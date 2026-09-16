#!/usr/bin/env python3
"""Initialize a ChronoForge run without invoking any paid service."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import math
from routes import route, DEFAULTS, qa_focus


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
    p.add_argument("source_video", nargs='?')
    p.add_argument('--product-url')
    p.add_argument('--duration', type=float, help='Editorial target; product mode requires this')
    p.add_argument("--out", required=True)
    p.add_argument("--provider-clip-seconds", type=float, default=10.0)
    p.add_argument("--aspect-ratio", choices=("9:16", "16:9"), default="9:16")
    args = p.parse_args()

    # Bare HTTP input is a candidate product link, verified by page inspection later.
    if args.source_video and args.source_video.startswith(('https://', 'http://')) and not args.product_url:
        args.product_url, args.source_video = args.source_video, None
    try:
        mode = route(args.source_video, args.product_url)
    except ValueError as e:
        raise SystemExit(str(e))
    source = pathlib.Path(args.source_video).expanduser().resolve() if args.source_video else None
    if source and not source.is_file():
        raise SystemExit(f"source video not found: {source}")
    if args.duration is not None and (not math.isfinite(args.duration) or args.duration <= 0):
        raise SystemExit('duration must be finite and positive')
    if mode == 'product_video' and args.duration is None:
        raise SystemExit('product mode needs --duration (ask for the intended length)')
    if not math.isfinite(args.provider_clip_seconds) or args.provider_clip_seconds <= 0:
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
    } if source else None
    duration = args.duration or float(source_record['probe']['format']['duration'])
    run = {
        "schema_version": "3.0.0",
        "mode": mode,
        "product_url": args.product_url,
        "input_verification": "pending_page_inspection" if args.product_url else "local_video",
        "use_watch": source is not None,
        "models": DEFAULTS,
        "qa_focus": qa_focus(mode),
        "status": "initialized",
        "created_at": now,
        "source_sha256": source_record["sha256"] if source_record else None,
        "provider_clip_seconds": args.provider_clip_seconds,
        "aspect_ratio": args.aspect_ratio,
        "paid_create_mode": "serial_single_writer",
        "blind_retry": False,
        "reference_lock_registry": "manifests/artifacts.json",
    }
    timeline = {
        "mode": mode,
        "editorial_duration": duration,
        "provider_clip_seconds": args.provider_clip_seconds,
        "editorial_shots": [],
        "containers": [],
    }
    if source_record:
        write_json(out / "source.json", source_record)
        timeline['source_duration'] = float(source_record['probe']['format']['duration'])
    write_json(out / "run.json", run)
    write_json(out / "manifests" / "timeline.json", timeline)
    write_json(out / "manifests" / "artifacts.json", {"schema_version": 2, "assets": {}, "locks": []})
    write_json(out / "manifests" / "execution-plan.json", {"schema_version": 3, "mode": mode, "story_file": "../analysis/story-truth.json", "jobs": []})
    if source:
        write_json(out / "analysis" / "source-evidence.json", {"coverage": {"full_duration_reviewed": False}, "observations": [], "audio_review": None})
    if args.product_url:
        (out / 'evidence/product').mkdir(parents=True)
        write_json(out / 'analysis/claim-ledger.json', {'claims': []})
    write_json(out / "analysis" / "story-truth.json", {"mode": mode, "hook": None, "characters": [], "beats": [], "prop_tracks": [], "fidelity_boundary": None})
    (out / "media-jobs.jsonl").write_text(json.dumps({
        "record_type": "ledger_header", "schema_version": "3.0.0",
        "contains_secrets": False, "paid_create_mode": "serial_single_writer",
        "blind_retry": False,
    }, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "initialized", "run_dir": str(out), "mode": mode, "use_watch": bool(source)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
