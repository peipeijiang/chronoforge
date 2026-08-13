#!/usr/bin/env python3
"""Normalize, trim and assemble ChronoForge containers with FFmpeg."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import subprocess


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("manifest", help="JSON with output and ordered containers")
    args = p.parse_args()
    manifest_path = pathlib.Path(args.manifest).resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    output = (base / data["output"]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    normalized = output.parent / "normalized"
    normalized.mkdir(exist_ok=True)
    width, height = data.get("size", [720, 1280])
    fps = int(data.get("fps", 60))
    sample_rate = int(data.get("sample_rate", 44100))
    inputs: list[pathlib.Path] = []
    target = 0.0
    for i, c in enumerate(data["containers"]):
        source = (base / c["file"]).resolve()
        keep = float(c["retain_seconds"])
        target += keep
        dest = normalized / f"{i:03d}-{c.get('id', i)}.mp4"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(source),"-t",str(keep),
             "-vf",f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={fps},setpts=PTS-STARTPTS",
             "-af",f"aresample={sample_rate},atrim=duration={keep},asetpts=PTS-STARTPTS",
             "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-r",str(fps),"-video_track_timescale",str(fps*1000),
             "-c:a","aac","-b:a","192k","-ar",str(sample_rate),"-ac","2","-movflags","+faststart",str(dest)])
        inputs.append(dest)
    filter_inputs = "".join(f"[{i}:v][{i}:a]" for i in range(len(inputs)))
    frames = math.ceil(target * fps)
    cmd = ["ffmpeg","-hide_banner","-loglevel","error","-y"]
    for item in inputs:
        cmd += ["-i", str(item)]
    graph = f"{filter_inputs}concat=n={len(inputs)}:v=1:a=1[v0][a0];[v0]select='lt(n,{frames})',setpts=N/({fps}*TB)[v];[a0]atrim=duration={target},asetpts=PTS-STARTPTS[a]"
    cmd += ["-filter_complex",graph,"-map","[v]","-map","[a]","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-r",str(fps),"-video_track_timescale",str(fps*1000),"-c:a","aac","-b:a","192k","-ar",str(sample_rate),"-ac","2","-movflags","+faststart",str(output)]
    run(cmd)
    probe = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=index,codec_name,width,height,r_frame_rate,time_base,duration,nb_frames,sample_rate,channels","-of","json",str(output)], text=True))
    print(json.dumps({"status":"assembled","output":str(output),"editorial_duration":target,"encoded":probe}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

