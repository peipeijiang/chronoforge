#!/usr/bin/env python3
"""Initialize a ChronoForge run without invoking any paid service."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def probe(path: pathlib.Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-of", "json", str(path),
    ]
    return json.loads(subprocess.check_output(cmd, text=True))


def write_json(path: pathlib.Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("source_video")
    p.add_argument("--out", required=True)
    p.add_argument("--provider-clip-seconds", type=float, default=10.0)
    p.add_argument("--aspect-ratio", choices=("9:16", "16:9"), default="9:16")
    args = p.parse_args()

    source = pathlib.Path(args.source_video).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"source video not found: {source}")
    if args.provider_clip_seconds <= 0:
        raise SystemExit("provider clip duration must be positive")

    out = pathlib.Path(args.out).expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"refusing non-empty run directory: {out}")
    for d in ("analysis", "evidence", "manifests", "requests/image", "requests/video", "media/references", "media/containers", "media/final", "qa"):
        (out / d).mkdir(parents=True, exist_ok=True)

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    source_record = {
        "path": str(source),
        "sha256": sha256(source),
        "probe": probe(source),
        "recorded_at": now,
    }
    run = {
        "schema_version": "1.0.0",
        "status": "initialized",
        "created_at": now,
        "source_sha256": source_record["sha256"],
        "provider_clip_seconds": args.provider_clip_seconds,
        "aspect_ratio": args.aspect_ratio,
        "paid_create_mode": "serial_single_writer",
        "blind_retry": False,
        "reference_lock": "pending",
    }
    timeline = {
        "source_duration": float(source_record["probe"]["format"]["duration"]),
        "provider_clip_seconds": args.provider_clip_seconds,
        "editorial_shots": [],
        "containers": [],
    }
    write_json(out / "source.json", source_record)
    write_json(out / "run.json", run)
    write_json(out / "manifests" / "timeline.json", timeline)
    write_json(out / "analysis" / "source-evidence.json", {"observations": []})
    write_json(out / "analysis" / "story-truth.json", {"hook": None, "characters": [], "beats": [], "prop_tracks": [], "fidelity_boundary": None})
    (out / "media-jobs.jsonl").write_text(json.dumps({
        "record_type": "ledger_header", "schema_version": "1.0.0",
        "contains_secrets": False, "paid_create_mode": "serial_single_writer",
        "blind_retry": False,
    }, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "initialized", "run_dir": str(out), "source_sha256": source_record["sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
