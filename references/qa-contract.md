# Media QA contract

## Three-route checks (v3)

All routes use the same L1 reference / L2 raw container / L3 actual delivery master layers. Checks compare against the selected route's truth, not a universal source-video test.

| Route | L1 | L2 | L3 |
|---|---|---|---|
| recreation | source/adaptation identity, setting, prop state | required actions, order, reaction and continuity | whole-source setup/payoff and approved adaptations |
| product_video | actual SKU/structure/scale, planned original scene | valid use, supported claim/proof, invariant product | coherent whole ad, accurate speech/text and readable pacing |
| hybrid | product identity plus source-inspired target composition | adapted action correct for actual product | source-inspired story with truthful product integration |

V3 hash-bound reports include checks, each with status and actual evidence. Required common names: L1 identity, geometry, reference_roles; L2 beat_coverage, state_continuity, audio, trim_completion; L3 whole_story, seams, audio, text_readability. Product/hybrid add product_fidelity and claim_accuracy; recreation/hybrid add source_adaptation. An accepted report requires each applicable check to pass; not_applicable requires a reason. Static L1 cannot verify motion; an identity sheet may mark claim_accuracy not_applicable if it contains no claim. Unknown/failed checks cannot become accepted. Still describe the actual limitation in the observations.

L2 also reviews every internal cut and every required beat, with denser sampling for action. Audio must be listened to separately; an ASR transcript does not prove seamless mixing. Optional warnings must be disclosed, and continuation warnings explicitly reviewed before using a boundary. Product B-roll need not invent causal actions: judge its declared supporting purpose.

Before image generation, perform planned evidence/script review: unresolved product claims, source coverage, plausible actions, whole-film progression, reference roles, timing and audio/text. This complements rather than replaces L1. L3 tests communication, not predicted conversion or guaranteed sales performance.

Assembly followed by text/audio changes requires fresh L3 on the changed master. Check subtitle duration, approved claim wording, selected SKU, platform preview/safe-zone template when available and actual seam/audio behavior. Do not claim a fixed UI-safe rectangle works for every placement.

## Contents

1. L1 reference QA
2. L2 container QA
3. L3 master QA
4. Retake policy
5. Acceptance language

## L1 reference QA

Technical gates:

- decodable image;
- sufficient resolution and correct orientation;
- stable hash;
- no unexpected alpha/corruption;
- provider URL downloaded and matched to the intended task.

Semantic gates:

- correct character identity and separation;
- correct environment and object function;
- causal state is visually readable;
- no unwanted people, watermark, UI, or dangerous/graphic drift;
- role and `must_not_control` fields are explicit.

Stop for the human reference-lock gate after L1 technical and actual semantic review passes. Generating the image happens before this gate.

## L2 container QA

Technical gates:

- probe codec, duration, dimensions, frame rate, audio;
- full decode;
- unintended black/freeze/silence checks, with declared intentional holds excluded;
- stable source file and hash.

Semantic gates:

- sample at least twice per second for dense action or around every internal cut;
- check every required beat exists and occurs in order;
- check start/end state against adjacent containers;
- check character identity, anatomy, and prop ownership;
- inspect audio meaning and A/V synchronization;
- confirm all action in a trimmed container finishes before its trim point;
- note generated text, unsafe drift, explicit content, or background mismatch.

Presence is insufficient. “Mask appears” fails when the odor cause is absent or comes from the wrong object.

## L3 master QA

Technical gates:

- normalized dimensions, CFR, pixel format, audio rate/channels;
- full decode;
- exact container order;
- sample both sides of every provider seam;
- check all trim boundaries and internal cuts;
- check black/freeze/silence with thresholds appropriate to the media;
- verify video/audio duration and disclose frame quantization delta;
- hash the final master.

Semantic gates:

- read a full-master contact sheet, then targeted dense frames;
- re-evaluate the hook and every setup/payoff pair;
- ensure no container boundary breaks a causal chain;
- compare story truth, not only shot nouns;
- state a fidelity boundary and all warnings.

## Retake policy

Map failures to the earliest responsible layer:

- wrong reference meaning → regenerate/relock L1;
- provider ignored a correct reference or action → L2 controlled retry;
- trim, seam, codec, or audio assembly error → fix L3 without paid generation.

Change one field per controlled retry. Record baseline, diagnosis, changed field, cost, and result. Do not retry a paid task merely because a score is low; connect the retry to a visible contract failure.

## Acceptance language

Use decisions such as:

- `pass`
- `pass_with_minor_drift`
- `pass_with_disclosed_warning`
- `fail_reference_layer`
- `fail_container_semantics`
- `fail_assembly`
- `superseded_narrative_fail`

Never use “pixel-perfect clone” for a reference-only video model. Prefer “reference-locked structural and semantic reenactment.”

## Machine-readable v2 handoff

Keep the detailed layer-specific decision above as the reason. Map eligible assets to `accepted` or `accepted_with_warnings` (otherwise `rejected`) for `workflow.py qa`; bind each report to `asset_sha256`, reviewer and actual observations. Never map a technical-only pass to accepted.

`media_qa.py` supplies probe/decode and timestamped frames, with semantic review explicitly pending. Write separate container QA reports with per-beat timestamps and evidence, then run `validate_plan.py PLAN --qa-dir QA_DIR --require-qa`. Do not mutate the frozen plan when adding review results. Also check the required beat order manually: the plan validator does not watch the media.

After a new story/reference version, check the dependency registry before reusing any prior QA. Register all actual upstream dependencies; missing edges cannot be inferred by a file checker. The assembled master always needs a fresh L3 review.
