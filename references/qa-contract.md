# Media QA contract

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

Stop for the human reference-lock gate after machine QA passes.

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

