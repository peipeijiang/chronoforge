#!/usr/bin/env python3
"""Reject story manifests that list actions without narrative causality."""

from __future__ import annotations

import argparse
import json
import pathlib


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("story_truth")
    args = p.parse_args()
    data = json.loads(pathlib.Path(args.story_truth).read_text(encoding="utf-8"))
    errors: list[str] = []
    beats = data.get("beats", [])
    ids = [b.get("id") for b in beats]
    if not beats:
        errors.append("story must contain beats")
    if len(ids) != len(set(ids)) or any(not x for x in ids):
        errors.append("beat ids must be nonempty and unique")
    if not data.get("hook"):
        errors.append("story hook is required")
    if not data.get("fidelity_boundary"):
        errors.append("fidelity_boundary is required")
    for i, beat in enumerate(beats):
        label = beat.get("id") or f"beats[{i}]"
        if not beat.get("visible_action"):
            errors.append(f"{label}: visible_action is required")
        if not beat.get("must_preserve"):
            errors.append(f"{label}: must_preserve must be nonempty")
        initial = beat.get("initial_condition") is True
        terminal = beat.get("terminal") is True
        declared = bool(beat.get("ambiguity"))
        if not initial and beat.get("cause") is None and not declared:
            errors.append(f"{label}: missing cause; mark initial_condition or declare ambiguity")
        if not terminal and beat.get("consequence") is None and beat.get("payoff") is None and not declared:
            errors.append(f"{label}: missing consequence/payoff; mark terminal or declare ambiguity")
        for field in ("cause", "consequence", "payoff"):
            ref = beat.get(field)
            refs = ref if isinstance(ref, list) else [ref]
            for item in refs:
                if isinstance(item, str) and item.startswith("B") and item not in ids:
                    errors.append(f"{label}: {field} references unknown beat {item!r}")
    props = data.get("prop_tracks", [])
    for i, prop in enumerate(props):
        states = prop.get("states", [])
        if len(states) < 2:
            errors.append(f"prop_tracks[{i}] must contain at least two states")
    print(json.dumps({"status":"pass" if not errors else "fail","errors":errors}, ensure_ascii=False))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
