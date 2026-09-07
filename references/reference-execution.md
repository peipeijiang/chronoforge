# Artifact lifecycle and operational handoff

The original production used local evidence frames, Image2 outputs, a user-locked pack, ordered per-container references, generated videos and layered QA. Use the same structure in a portable run, without copying the original approval or private URLs.

## Register versioned assets

Copy source evidence into the run first. Register source frames and frozen contracts (story, timeline and execution plan), then references with their source/contract dependencies.

```bash
python3 scripts/workflow.py --run-dir RUN register E01 RUN/evidence/E01.jpg --kind source --role "source composition"
python3 scripts/workflow.py --run-dir RUN register STORY-v1 RUN/analysis/story-truth.json --kind contract --role "story truth"
python3 scripts/workflow.py --run-dir RUN register G01-v1 RUN/media/references/G01.png \
  --kind reference --role "environment only" --depends-on E01 STORY-v1
```

Use `artifact://E01` for Image2 input and `artifact://G01-v1` for video input. Requests preserve exact array order; describe what each slot controls and must not control. G01-v1 is an **ID**, not a filesystem URI. HTTP/data URL examples are accepted in planned schema checks, but ready paid submission requires registered local artifacts so the actual bytes and lock are verifiable.

Do not overwrite a registered file or reuse its ID. Register a new version. Dependencies form a graph; references, containers and masters must include their actual upstream contracts and assets. Missing dependency declarations cannot be discovered by the script.

## QA and human lock

After inspecting generated image bytes, write a reviewer report:

```json
{
  "asset_sha256": "REPLACE_WITH_ACTUAL_SHA256",
  "reviewer": "agent or human reviewer identity",
  "technical_pass": true,
  "decision": "accepted_with_warnings",
  "observations": [
    {"evidence": "inspected full image", "finding": "Identity and prop state match the plan"}
  ],
  "warnings": ["Disclose any allowed deviation here"]
}
```

The report is an illustrative schema, **not pre-approved evidence**. Accepted means the reviewer actually inspected it. Semantic checks and warnings must be specific to that asset.

```bash
python3 scripts/workflow.py --run-dir RUN qa G01-v1 RUN/qa/G01-v1.json
python3 scripts/workflow.py --run-dir RUN lock G01-v1 G02-v1 G03-v1 \
  --approval "Actual user reference-lock confirmation and its provenance"
```

Lock the full accepted pack, not just a single container's subset. Lock approval is a routine creative gate, separate from authorization for paid jobs. The tool records supplied approval; it cannot verify who consented. Never invent it.

## Coverage, video QA and assembly

Maintain an execution plan like [the sanitized case](../assets/cat-coffee-v3/execution-plan.json). Every required story beat must reach a local action before the retained trim point. A prompt schedule is generated staging, not measured source timing.

```bash
python3 scripts/validate_plan.py RUN/manifests/execution-plan.json
python3 scripts/media_qa.py RUN/media/containers/C01.raw.mp4 --out RUN/qa/C01-evidence
```

Read the extracted frames and record timestamped findings for **each required beat**, plus order, cause/reaction, object state and warnings. Listen separately when audio matters. Save separate `QA_DIR/C01.json` etc. reports with `decision` and `observations` entries containing `beat_id`, `time`, `verdict` = pass/fail and `evidence`. Run `validate_plan.py PLAN --qa-dir QA_DIR --require-qa`. Do not edit the frozen plan to add QA; that would change its hash and invalidate dependent assets. The optional embedded `qa` field is for unregistered illustrative plans only.

Register the raw container with references, story, timeline and plan as dependencies. Attach its hash-bound L2 report via `workflow.py qa`. Before assembly, run `workflow.py check` for selected container IDs, then use their hashes and decisions in the assembly manifest. A hand-edited assembly decision alone is not sufficient evidence.

After assembly, sample evidence with `media_qa.py MASTER --out QA_DIR --seams ...` using actual seam timestamps. Do L3 technical and semantic review; the helper never auto-accepts a video. Register the master with its container/contract dependencies and attach the actual L3 decision.

## Re-audit and targeted restoration

```bash
python3 scripts/workflow.py --run-dir RUN invalidate STORY-v1 \
  --reason "New evidence changes a required causal action"
```

This marks that artifact and all declared downstream dependents stale without deleting their bytes. Runtime hash checks also refuse silently changed files. Reuse an old asset only after explicit review against the new story; register a new version/dependency relationship, run L1 and lock again when the accepted reference pack changes.

Classify fixes by their earliest responsible layer. Preserve a retake log: failed evidence, changed variable, approved attempt, old/new fingerprints and outcome. Provider failure without rendered media is not a creative topology test.
