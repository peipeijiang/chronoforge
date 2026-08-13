#!/usr/bin/env python3
"""Validate ChronoForge editorial truth and provider container coverage."""

from __future__ import annotations

import argparse
import json
import pathlib


EPS = 1e-6


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("timeline")
    args = p.parse_args()
    data = json.loads(pathlib.Path(args.timeline).read_text(encoding="utf-8"))
    errors: list[str] = []
    duration = float(data.get("source_duration", 0))
    limit = float(data.get("provider_clip_seconds", 0))
    shots = data.get("editorial_shots", [])
    containers = data.get("containers", [])

    if not shots:
        errors.append("editorial_shots must be nonempty")
    if not containers:
        errors.append("containers must be nonempty")

    def check_ranges(items: list[dict], label: str, end_target: float) -> None:
        cursor = 0.0
        for i, item in enumerate(items):
            try:
                start, end = map(float, item["source_range"])
            except Exception:
                errors.append(f"{label}[{i}] has invalid source_range")
                continue
            if end <= start:
                errors.append(f"{label}[{i}] end must be greater than start")
            if abs(start - cursor) > EPS:
                errors.append(f"{label}[{i}] starts at {start}, expected contiguous {cursor}")
            cursor = end
        if items and abs(cursor - end_target) > EPS:
            errors.append(f"{label} ends at {cursor}, expected {end_target}")

    if duration <= 0 or limit <= 0:
        errors.append("source_duration and provider_clip_seconds must be positive")
    check_ranges(shots, "editorial_shots", duration)
    check_ranges(containers, "containers", duration)

    shot_ranges = {x.get("id"): tuple(map(float, x.get("source_range", (0, 0)))) for x in shots}
    owned: dict[str, list[tuple[float, float]]] = {sid: [] for sid in shot_ranges}
    for i, c in enumerate(containers):
        provider_duration = float(c.get("provider_duration", 0))
        retain_duration = float(c.get("retain_duration", 0))
        deadline = float(c.get("completion_deadline", retain_duration))
        start, end = map(float, c.get("source_range", (0, 0)))
        if provider_duration > limit + EPS:
            errors.append(f"containers[{i}] provider_duration exceeds limit")
        if retain_duration > provider_duration + EPS:
            errors.append(f"containers[{i}] retain_duration exceeds provider duration")
        if abs(retain_duration - (end - start)) > EPS:
            errors.append(f"containers[{i}] retain_duration differs from source range")
        if deadline > retain_duration + EPS:
            errors.append(f"containers[{i}] completion_deadline exceeds trim point")
        for j, segment in enumerate(c.get("shot_segments", [])):
            sid = segment.get("shot_id")
            if sid not in shot_ranges:
                errors.append(f"containers[{i}].shot_segments[{j}] references unknown shot {sid!r}")
                continue
            try:
                seg_start, seg_end = map(float, segment["source_range"])
            except Exception:
                errors.append(f"containers[{i}].shot_segments[{j}] has invalid source_range")
                continue
            if seg_start < start - EPS or seg_end > end + EPS or seg_end <= seg_start:
                errors.append(f"containers[{i}].shot_segments[{j}] is outside its container or empty")
            shot_start, shot_end = shot_ranges[sid]
            if seg_start < shot_start - EPS or seg_end > shot_end + EPS:
                errors.append(f"containers[{i}].shot_segments[{j}] is outside source shot {sid!r}")
            owned[sid].append((seg_start, seg_end))
    for sid, expected in shot_ranges.items():
        segments = sorted(owned[sid])
        cursor = expected[0]
        for start, end in segments:
            if abs(start - cursor) > EPS:
                errors.append(f"editorial shot {sid!r} segment gap/overlap at {cursor} → {start}")
            cursor = end
        if not segments or abs(cursor - expected[1]) > EPS:
            errors.append(f"editorial shot {sid!r} segment coverage ends at {cursor}, expected {expected[1]}")

    print(json.dumps({"status": "pass" if not errors else "fail", "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
