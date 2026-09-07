---
name: chronoforge
description: Recreate videos longer than a generation model's clip limit using full-source evidence, story and continuity contracts, reference images, fixed-duration video jobs, layered QA and deterministic assembly. Use for source-led video remakes with Image2/Omni-style workflows without LoRA training.
---

# ChronoForge · v2

Reconstruct what the viewer understands, not just the objects visible in selected frames. Target reference-guided structural and semantic recreation; do not promise pixel, motion, face or original-audio identity.

## Working rules

- Analyze the full source before spending on references. Keep observations, inferences and unknowns separate.
- Freeze **versioned** editorial truth. Provider containers package the edit; they do not define source cuts. A later source audit creates a new version and invalidates affected downstream assets.
- Connect cause → visible action → reaction → consequence/payoff. Track character and prop states across cuts.
- Image2 generates references **before** L1 and human lock. Only paid **video** generation requires the locked reference pack.
- The routine creative human gate is reference lock. Paid-batch, out-of-budget retry and scope-change authorization are separate; a lock is not permission for unlimited charges.
- Preserve raw results and lineage. A technical pass is not semantic acceptance. Retake the earliest responsible layer.
- No LoRA or local GPU training is required by this workflow. Provider generation still incurs API charges; local FFmpeg work consumes compute.
- Never log keys or publish private source media, account details, task/result URLs or expanded reference data.

## Routing and references

Use the installed `watch` skill for source/frame evidence; read its instructions before invoking it. If unavailable, use ffprobe/FFmpeg plus direct frame inspection and disclose coverage/audio limitations. Watch does not automatically prove continuous visual or audio understanding.

Read these at their corresponding stage:

| Stage | Required reference |
|---|---|
| Source analysis and creative truth | [story-compiler.md](references/story-compiler.md) |
| Artifact registration, lock, revision and handoff | [reference-execution.md](references/reference-execution.md) |
| Before UpDrama calls | [provider-runtime.md](references/provider-runtime.md), [updrama-contract.md](references/updrama-contract.md) |
| Asset/video acceptance | [qa-contract.md](references/qa-contract.md) |
| Pilot, assembly and delivery | [delivery-and-canary.md](references/delivery-and-canary.md) |
| Restoring an incomplete prior run or learning from the original production | [v2-restoration-audit.md](references/v2-restoration-audit.md) |

Other creative skills may inform judgment when installed and relevant; they are not mandatory runtime dependencies or parallel orchestrators.

## 1. Initialize and audit the complete source

```bash
python3 scripts/init_run.py SOURCE_VIDEO --out RUN --provider-clip-seconds 10 --aspect-ratio 9:16
```

Probe/hash the source; inventory existing analysis before extracting again. Inspect a full-duration pass, then dense windows at causal actions, reactions, prop transitions and ambiguous cuts. Read every frame required by the chosen analysis pass. Record timestamps from the extraction manifest, not guessed filenames.

Write `source-evidence.json`: visible facts, editorial inference, uncertainty, evidence paths/time ranges, coverage, dialogue/music/effects and what audio was actually heard. If key actions remain uncertain, inspect their windows before designing them.

## 2. Explain the appeal and freeze creative truth

Answer: What is the opening hook? Why does the viewer keep watching? Which setup creates expectation, what escalates it, and how is it paid off? For every important action, explain the reason and the state it changes.

Compile story beats, observed shot boundaries, character roles/state tracks, prop lifecycles, audio intent and must-preserve/may-drift fields. Explicitly record approved adaptations such as removing a human helper: who now performs that helper's causal action? Do not silently call a rewritten action a source observation.

Version the story/timeline contracts. Maintain evidence → beat → reference role → container action → QA observation traceability. Use `validate_story.py` as a structural check, not proof of understanding.

## 3. Package the editorial timeline

Group adjacent complete action units into fixed-duration provider containers. Keep measured source cuts distinct from chosen local prompt cuts. Long source shots may span containers through `shot_segments`; preserve their editorial identity.

For `omni_flash-10s`, each paid request outputs 10 seconds. Choose retained intervals from the story, complete all actions before each trim point, and put only a stable hold in the discarded tail. The minimum count ceil(duration/10) is a capacity lower bound, not a universally sufficient topology.

Write timeline and execution plan. Validate with:

```bash
python3 scripts/validate_timeline.py RUN/manifests/timeline.json
python3 scripts/validate_plan.py RUN/manifests/execution-plan.json
```

The sanitized 33.111723-second [case plan](assets/cat-coffee-v3/execution-plan.json) uses four jobs retaining 10 + 7 + 10 + 6.111723 seconds. Its generated action timings are not measured source cut times and must not be imposed on a new video.

## 4. Generate, inspect and lock references

Plan global identity/environment/hero-prop references and additional beat/state/contact references only where they provide control. Each ordered slot has a role and exclusions; do not let a style/identity image override the action or setting.

Register source frames and contracts. Write `gpt-image-2` requests using `artifact://ID` source or prior-reference inputs, size and quality. Run the planned dry-run, fetch/review provider details, obtain exact image-batch authorization, and submit. Download/hash originals, inspect them at L1, and only then show the recommended pack for human lock.

A reuse/retire/new reference table is required when revising a prior pack. Do not regenerate good assets merely to equalize count or dimensions; do not reuse a visually attractive asset whose state contradicts the story.

Record actual L1 findings, roles, hashes and user approval through `workflow.py`. The reference-execution guide supplies commands. Never copy approval from an example or earlier incompatible version.

## 5. Compile executable prompts and pass the ready gate

Each prompt states model duration/aspect/style/audio, ordered reference roles, local action windows, cuts, actor/contact geometry, cause and state constraints, trim deadline, hold and exclusions. State what is implied rather than literally shown.

Cross-check the prompt against the execution plan; planned local cuts cannot overwrite evidence. Check required beats across the whole movie, not only within the pilot.

```bash
python3 scripts/updrama_runtime.py preflight --run-dir RUN
python3 scripts/updrama_runtime.py validate REQUEST --ready --run-dir RUN
```

Inspect saved preflight bodies. `fetched_review_required` is not automatic contract approval. Ready validation resolves reference bytes in memory and enforces the current human lock for Omni. Before submitting, verify actual paid authorization and unresolved ledger state.

## 6. Generate and preserve each container

Use an optional risk-based pilot within the authorized batch; reuse a passing, current pilot in the master. Its acceptance does not certify unrelated story sections.

```bash
python3 scripts/updrama_runtime.py submit REQUEST --run-dir RUN --job-id C01-v1-attempt1 --confirm-paid I_UNDERSTAND_THIS_IS_PAID
python3 scripts/updrama_runtime.py collect TASK_ID --run-dir RUN --output RUN/media/containers/C01-v1.raw.mp4 --wait-seconds 40
```

Creates are serialized per run. Known jobs resume without another POST; unknown submissions block the model lane pending evidence-backed reconciliation. A failed download is not a reason to regenerate video. Record task provenance and raw media hashes before transformation.

## 7. Inspect L2 and repair the responsible layer

Run full decode/probe and collect timestamped evidence with `media_qa.py`. Inspect every required beat, action order, cause/reaction, character/prop state, anatomy, contact, internal cut and retained deadline; listen separately for audio. Dense sampling supplements rather than replaces necessary playback.

Record per-beat L2 observations and warnings in separate `QA_DIR/C01.json` etc. reports, then validate with `validate_plan.py PLAN --qa-dir QA_DIR --require-qa`. Never mutate a frozen plan just to attach QA. Register accepted containers with **all** actual reference/contract dependencies. No helper infers semantic pass from file existence.

Distinguish provider/no-result failures from rendered creative failures. A controlled rendered retake changes one identified variable. Consider a costed topology split only after repeated evidence of the same boundary problem. Pure assembly errors stay local.

## 8. Assemble, review the master and deliver

Check selected registered containers for freshness. Build the assembly manifest with raw-file hashes, L2 decisions, retained seconds and the delivery contract. Run `assemble.py`; it refuses overwritten masters and validates cumulative frame budgets and full decode.

L3 compares the whole movie with current story truth: setup/payoff, transitions, trim completion, framing and audio—not merely codec/duration. Sample actual timeline seams with `media_qa.py --seams ...`. Quantify CFR duration delta and disclose allowed visual deviations.

Deliver the current master plus private provenance/QA package. Do not deliver synthetic test output or stale/superseded candidates. If re-audit changes the story, invalidate declared dependents through `workflow.py invalidate`, preserve prior files, and rebuild only the affected layers.
