#!/usr/bin/env python3
"""Hash-checked, frame-budgeted assembly. Does not decide semantic acceptance."""
from __future__ import annotations
import argparse
import json
import math
import pathlib
import subprocess
import tempfile
from media_qa import probe
from workflow import sha, write


def run(cmd):
    subprocess.run(cmd, check=True)


def frame_budgets(durations, fps):
    """Round cumulative boundaries, not every clip independently."""
    cursor, prior, result = 0.0, 0, []
    for duration in durations:
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError('retained durations must be finite and positive')
        cursor += duration
        boundary = math.ceil(cursor * fps - 1e-9)
        result.append(boundary - prior)
        prior = boundary
    if any(n <= 0 for n in result):
        raise ValueError('a segment is shorter than the frame budget')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest')
    a = p.parse_args()
    path = pathlib.Path(a.manifest).resolve()
    data = json.loads(path.read_text()); base = path.parent
    output = (base / data['output']).resolve()
    if output.exists():
        raise ValueError('refusing to overwrite master; use a new version')
    width, height = data.get('size', [720, 1280])
    fps = data.get('fps', 60); rate = data.get('sample_rate', 44100)
    if any(type(n) is not int or n <= 0 for n in (width, height, fps, rate)) or width % 2 or height % 2:
        raise ValueError('positive integer geometry/fps/rate and even geometry required')
    audio = data.get('audio_policy', 'generated')
    if audio not in ('generated', 'silent'):
        raise ValueError('assembler supports generated or silent; source-audio reuse needs a separate verified mix')
    clips = data['containers']
    if not clips or len({c['id'] for c in clips}) != len(clips):
        raise ValueError('nonempty unique container IDs required')
    durations = [float(c['retain_seconds']) for c in clips]
    budgets = frame_budgets(durations, fps)
    target = sum(durations)
    sources = []
    for c, keep in zip(clips, durations):
        source = (base / c['file']).resolve()
        metadata = probe(source)
        video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
        if float(video.get('duration', metadata['format']['duration'])) + 1 / fps < keep:
            raise ValueError('container too short: ' + c['id'])
        if audio == 'generated' and not any(s['codec_type'] == 'audio' for s in metadata['streams']):
            raise ValueError('generated-audio policy requires an audio stream: ' + c['id'])
        if c.get('sha256') != sha(source):
            raise ValueError('input hash missing or changed: ' + c['id'])
        if c.get('qa_decision') not in ('accepted', 'accepted_with_warnings', 'synthetic_test'):
            raise ValueError('input QA decision missing: ' + c['id'])
        sources.append(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    scratch = pathlib.Path(tempfile.mkdtemp(prefix='chronoforge-assembly-', dir=output.parent))
    normalized = []
    for i, (source, keep, frames) in enumerate(zip(sources, durations, budgets)):
        dest = scratch / f'{i:03d}.mp4'
        # Only a sub-frame rounding pad is permitted after validated retained action.
        vf = (f'scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},'
              f'fps={fps},trim=duration={keep},setpts=PTS-STARTPTS,'
              f'tpad=stop_mode=clone:stop_duration={1/fps},trim=end_frame={frames},setpts=N/({fps}*TB)')
        cmd = ['ffmpeg', '-v', 'error', '-n', '-i', str(source), '-map', '0:v:0', '-vf', vf,
               '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', str(fps), '-video_track_timescale', str(fps*1000)]
        if audio == 'generated':
            cmd += ['-map', '0:a:0', '-af', f'aresample={rate},atrim=duration={keep},asetpts=PTS-STARTPTS,apad,atrim=duration={frames/fps}',
                    '-c:a', 'aac', '-ar', str(rate), '-ac', '2']
        else:
            cmd += ['-an']
        run(cmd + [str(dest)])
        normalized.append(dest)
    cmd = ['ffmpeg', '-v', 'error', '-n']
    for source in normalized:
        cmd += ['-i', str(source)]
    has_audio = audio == 'generated'
    labels = ''.join(f'[{i}:v]' + (f'[{i}:a]' if has_audio else '') for i in range(len(clips)))
    graph = labels + f'concat=n={len(clips)}:v=1:a={int(has_audio)}[v]' + ('[a0];[a0]atrim=duration=' + str(target) + '[a]' if has_audio else '')
    cmd += ['-filter_complex', graph, '-map', '[v]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-r', str(fps), '-video_track_timescale', str(fps*1000), '-frames:v', str(sum(budgets))]
    if has_audio:
        cmd += ['-map', '[a]', '-c:a', 'aac', '-ar', str(rate), '-ac', '2']
    cmd += ['-movflags', '+faststart', str(output)]
    run(cmd)
    result = probe(output)
    stream = next(s for s in result['streams'] if s['codec_type'] == 'video')
    if int(stream['nb_frames']) != sum(budgets):
        raise RuntimeError('encoded frame count mismatch; do not deliver')
    run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(output), '-f', 'null', '-'])
    report = {'status': 'assembled_semantic_qa_pending', 'output': str(output), 'sha256': sha(output),
              'editorial_duration': target, 'frame_budgets': budgets, 'encoded': result,
              'quantization_delta': sum(budgets) / fps - target,
              'synthetic_test': any(c.get('qa_decision') == 'synthetic_test' for c in clips),
              'normalized_inputs': str(scratch)}
    write(output.with_suffix('.assembly.json'), report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
