# Delivery specification, dry runs and pilots

V3 applies to all three routes. Use editorial_duration for the final film; source_duration exists only for source-bearing routes. Assembly manifests use schema_version=3, run_dir relative to the manifest, and ordered registered container IDs (job asset_id, or job id). Each actual input must match current registry L2 acceptance and the frozen plan's retained duration.

White text/labels and custom narration/music are a separate local postproduction pass. Preserve the clean master, save a new version, register the text/mix plan and new master dependencies, then perform L3 on the actual final output. Bundled assemble.py does not automatically burn text or mix external voiceover. Audio/text timing and safe placement need actual inspection; generated test fixtures are never delivery media.

Freeze a run-specific delivery contract: editorial duration, aspect ratio, output size/fps, framing policy, audio policy and tolerances. The historical vertical master used 720×1280, H.264/yuv420p, 60 fps, AAC 44.1 kHz stereo. These are an **example**, not universal requirements.

Reference images need compatible composition, not identical pixel dimensions. A historical Image2 image returned 945×1665 rather than the requested 1088×1920 and was accepted after inspecting framing. Decide geometry tolerance in L1; do not force unnecessary paid retries for a harmless size difference. Conversely, never crop away an important interaction just to meet dimensions.

## Two dry-run stages

1. **Planned:** source evidence, story truth, timeline, ordered role bundles and action schedules are complete. Uncreated reference IDs may remain `artifact://ID`. Validate story, timeline, execution plan and planned requests. Use synthetic media to test assembly if changing topology/delivery settings.
2. **Ready:** references actually exist, have current hashes, passed L1 and have human lock approval. Validate resolved requests, dependency freshness and authorization before video submission.

Image generation precedes image QA and lock. Do not require generated references to exist during the pre-image dry run, or require reference lock before generating Image2 assets.

## Pilot strategy

An optional risk-based pilot is part of the planned batch, not an extra mandatory video. Choose the segment that tests the actual risk (causal staging, interactions or an early trim deadline). If it passes and its dependencies remain current, reuse it in the final master and generate only the remaining jobs.

A successful final-segment pilot does not validate earlier story causality. A 33-second case using four containers may generate one pilot plus three remaining clips, not five clips. Reference count is determined by roles and missing states, not a universal three/five/eleven-image recipe.

## Audio

- **generated:** use generated audio, check seams and listen to the mix; never claim original-audio identity.
- **silent:** omit audio from the master.
- **source reuse:** only with appropriate rights and verified timing; requires a separately reviewed mix workflow, not implemented by the bundled assembler.

Changing a mix or making a silent version normally invalidates assembly/L3 only. Regenerate video only if the new audio requirement changes visible timing or action semantics. Do not impose blanket paid regeneration for an audio policy change.

## Assembly and QA

The assembler requires original input hashes and a reviewer decision in each container entry. Use `synthetic_test` only for test media; the output is flagged and cannot be delivered as a recreation. Generated audio requires an audio stream in every clip. The current framing implementation is center scale-and-crop; inspect its effect before accepting the master.

Integer CFR frames use **cumulative boundary rounding**. For 33.111723 seconds at 60 fps, the total is 1987 frames, 33.116667 encoded seconds, delta approximately +0.004944 seconds. Inspect frame budgets, output probe and full decode. The assembler preserves raw inputs and writes normalized intermediates in a unique directory; it refuses an existing master.

L3 must separately inspect all internal cuts, timeline-derived seams, trim boundaries and story payoff. Silence/black detection may help locate defects but must not reject intentional creative choices. No technical metric proves causal fidelity. A source frame sample is not evidence that audio was heard, nor that every unsampled action was seen.

## Delivery

Provide master/hash, source fingerprint, story and timeline versions, ordered locked references, request fingerprints, task provenance, L1/L2/L3 reports, assembly report and disclosed limitations. Deliver only the current non-stale candidate. Preserve rejected/superseded assets locally for audit. Do not publish keys, private media, task IDs, account detail or result URLs as example data.
