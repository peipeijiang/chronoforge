---
name: chronoforge
description: Analyze and recreate long source videos as causally faithful generative productions using source-video evidence, reference-image generation, fixed-duration video models, deterministic trimming/assembly, resumable paid-job ledgers, and layered media QA. Use when Codex must replicate, remake, reenact, extend, localize, or reconstruct a video longer than one generation-model clip; preserve story progression, causal actions, character/scene continuity, prop state, timing, audio intent, and editorial structure; or orchestrate Watch/Image2/Omni/FFmpeg-style workflows without LoRA training.
---

# ChronoForge

Compile a source video into evidence, story truth, visual references, generation containers, and a verified master. Treat fidelity as a testable contract, not a prompt adjective.

## Non-negotiable invariants

1. Analyze the full source before designing references or prompts.
2. Preserve editorial shots and story beats as the immutable timeline truth. Treat provider clip lengths as packaging only.
3. Record causal chains explicitly: cause → visible action → reaction → consequence/payoff.
4. Trace every story-bearing prop and character state across shots.
5. Claim structural/semantic reenactment unless the provider genuinely supports motion or pixel identity.
6. Use one routine human gate: lock the accepted reference pack before paid video generation.
7. Never expose API keys, write them into requests, or print them in logs.
8. Write a submit intent before every paid POST. Serialize creates. Never blindly retry an ambiguous paid submission.
9. Retake the earliest responsible layer and change one variable per controlled retry.
10. Do not mark a technically valid master as faithful when its story causality is wrong.

## Route the work

- Use an installed source-video analysis skill such as `watch` when available. Follow its frame-reading requirements completely.
- Use a configured reference-image provider when available; otherwise prepare requests without submitting.
- Use a configured fixed-duration video provider when available; otherwise prepare container requests without submitting.
- Use `ffprobe` and `ffmpeg` for deterministic inspection, trimming, normalization, assembly, and technical QA.
- Read [references/story-compiler.md](references/story-compiler.md) before analyzing a narrative, comedy, tutorial, transformation, or process video.
- Read [references/provider-runtime.md](references/provider-runtime.md) before any paid API submission or when using UpDrama Image2/Omni.
- Read [references/qa-contract.md](references/qa-contract.md) before accepting assets, containers, or a master.

## Initialize a run

Run:

```bash
python3 scripts/init_run.py SOURCE_VIDEO --out RUN_DIR \
  --provider-clip-seconds 10 --aspect-ratio 9:16
```

This creates manifests and directories only. It never submits paid work.

Copy and adapt [assets/timeline.example.json](assets/timeline.example.json) and [assets/assembly.example.json](assets/assembly.example.json) when building the first manifests.

Use the run directory as the only creative/runtime ledger for that replication. Preserve source hashes and accepted artifact hashes.

## Stage 1: extract source evidence

1. Probe duration, dimensions, frame rate, codecs, and audio.
2. Analyze the entire source at scene level.
3. Run focused dense passes around every cut, reaction, hidden action, prop transition, and container trim boundary.
4. Read every extracted frame required by the analysis tool. Do not infer unseen action from filenames.
5. Distinguish:
   - `visible_fact`: directly shown.
   - `editorial_inference`: strongly implied by ordering or reaction.
   - `unknown`: unresolved.
6. Note dialogue, music, effects, silence, rhythm, and audio-dependent jokes.

Write `analysis/source-evidence.json` and `analysis/story-truth.json` using the schemas in [references/story-compiler.md](references/story-compiler.md).

Validate the compiled story:

```bash
python3 scripts/validate_story.py RUN_DIR/analysis/story-truth.json
```

## Stage 2: compile story truth

Before writing a shot plan, answer:

- What is the hook and why does it attract attention?
- What does each character want or represent?
- Why does every important action occur?
- Which reaction makes an invisible cause legible?
- What information must the viewer remember for the payoff?
- Which object or state carries continuity across a cut?

Build:

- an immutable editorial shot list;
- a beat-level causal graph;
- character state tracks;
- prop lifecycle tracks;
- setup/payoff links;
- must-preserve and may-drift fields;
- a fidelity boundary and rights/safety check.

Fail the analysis if an important action is listed without a cause, reaction, consequence, or declared ambiguity.

## Stage 3: design generation topology

Keep editorial truth separate from provider containers.

1. Group adjacent source beats into semantic containers no longer than the provider clip duration.
2. Prefer boundaries at hard source cuts or complete action units.
3. For a short final container, require all action to finish before the retained trim point and hold a stable end state afterward.
4. Do not equal-bin by default. Optimize for causal completeness and continuity.
5. Assign each container `shot_segments` so a source shot longer than the provider limit may span containers without changing editorial truth.
6. Validate the timeline:

```bash
python3 scripts/validate_timeline.py RUN_DIR/manifests/timeline.json
```

Split only the specific container whose same boundary failure repeats in a baseline and one controlled same-topology retry. Record increased generated seconds and cost before splitting.

## Stage 4: build and lock references

Design references around control roles, not quantity.

- Global references: environment, character identities, hero props.
- Beat references: causal setups, reactions, interaction geometry, important object states.
- Cleanup references: remove watermarks, background people, UI, and irrelevant text while preserving evidence.

For sensitive or gross-out actions, preserve narrative implication without unnecessary graphic detail. Never invent a literal action when the source only implies it editorially.

Assign each accepted image a role and `must_not_control` list. Prefer 3–6 focused references per video container; never exceed provider limits. Hash the accepted pack and stop for the human reference-lock gate. Do not submit video until the user accepts it.

## Stage 5: compile provider prompts

For each provider container, write:

1. output duration, orientation, style, and audio intent;
2. ordered reference roles;
3. a timestamped action timeline;
4. explicit hard cuts when needed;
5. causal constraints and state continuity;
6. the completion deadline for trimmed containers;
7. global and shot-specific exclusions;
8. a precise statement of what is not literally shown.

Use explicit language such as “odor comes only from the tent, never from the machine” when confusing the source would reverse the story.

## Stage 6: execute safely

Before submission:

- refresh provider guide/model detail;
- validate current request schemas;
- resolve references to stable URLs or allowed in-memory data URLs;
- confirm authorization for the exact paid batch;
- ensure there is no unresolved `unknown_submission` for the same model lane.

Use the provider adapter pattern in [references/provider-runtime.md](references/provider-runtime.md). Never assume static examples override authenticated runtime detail.

Poll by terminal fields, not localized display strings. Download results, hash them, and preserve the original provider output before any transformation.

## Stage 7: three-layer QA

Apply the full contract in [references/qa-contract.md](references/qa-contract.md):

- L1 reference assets;
- L2 raw provider containers;
- L3 assembled master.

At every layer run deterministic technical checks and timestamped semantic checks. At L2, require both the presence and ordering of causal beats. At L3, sample all provider seams, internal cuts, trim boundaries, and setup/payoff links.

Never trigger a paid retake for an assembly-only error.

## Stage 8: assemble and deliver

Normalize geometry, frame rate, pixel format, audio rate, and channel count. Trim containers to their declared retained durations. Concatenate in timeline order.

At constant frame rate, encode an integer number of frames and disclose the resulting quantization delta from the editorial duration.

Deliver:

- the final master;
- contact sheet or preview;
- reference-pack manifest;
- provider request manifests;
- append-only job ledger;
- per-container L2 QA;
- final L3 QA;
- disclosed warnings and fidelity boundary.

If a new story audit invalidates an old master, mark it superseded instead of leaving it as a delivery candidate.
