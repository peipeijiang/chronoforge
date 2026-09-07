#!/usr/bin/env python3
"""Full decode + timestamped frame evidence. Semantic judgment stays pending."""
import argparse
import json
import math
import pathlib
import subprocess
from workflow import sha, write


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                     '-show_format', '-of', 'json', str(path)], text=True))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('media'); p.add_argument('--out', required=True)
    p.add_argument('--interval', type=float, default=0.5)
    p.add_argument('--seams', type=float, nargs='*', default=[])
    a = p.parse_args()
    if not math.isfinite(a.interval) or a.interval <= 0:
        raise ValueError('interval must be positive')
    source = pathlib.Path(a.media).resolve(); out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    metadata = probe(source)
    duration = float(metadata['format']['duration'])
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(source), '-f', 'null', '-'], check=True)
    times = {round(i * a.interval, 6) for i in range(math.ceil(duration / a.interval))}
    for seam in a.seams:
        times.update(round(t, 6) for t in (seam - .1, seam, seam + .1) if 0 <= t < duration)
    frames = []
    for index, timestamp in enumerate(sorted(times)):
        dest = out / f'frame-{index:04d}.jpg'
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(source), '-ss', str(timestamp),
                        '-frames:v', '1', '-q:v', '3', '-n', str(dest)], check=True)
        if not dest.exists():
            raise RuntimeError('missing frame at ' + str(timestamp))
        frames.append({'file': dest.name, 'time': timestamp, 'sha256': sha(dest), 'reviewed': False})
    report = {'asset_sha256': sha(source), 'probe': metadata, 'full_decode_pass': True,
              'semantic_decision': 'pending', 'frames': frames,
              'audio_review': 'pending; frame extraction does not listen to audio'}
    write(out / 'evidence.json', report)
    print(json.dumps({'evidence': str(out / 'evidence.json'), 'semantic_decision': 'pending'}))


if __name__ == '__main__':
    main()
