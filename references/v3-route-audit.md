# Three-route audit — 2026-09-16

## Scope and outcome

Recreation, product_video and hybrid pass the local contract and assembly tests. This is not an assertion that a provider accepted live requests or that generated media passed visual QA. No paid task was submitted in this audit.

## Issues corrected

- Route hybrid before either individual input; product-only initialization never probes video or requires source evidence.
- Keep source time separate from editorial time; original product stories cannot invent source timecodes.
- Author one full film before provider packing; supporting shots require editorial purpose, not fabricated causality.
- Map product claims to evidence; unresolved claims and unsafe state transitions block compilation.
- Select references by route and purpose; continuation accepts exactly the prior container's reviewed last frame and the target endpoint.
- Require continuation to follow the immediately preceding planned asset, with full parent retention so the visible seam matches the boundary.
- Compile complete, bounded prompts with explicit reference roles and audio; reject arbitrary truncation and stale dependencies.
- Preserve reviewed model snapshots, reference locks, serial paid intent logging, deduplication and ambiguous-submit blocking.
- Apply common L1/L2/L3 layers with route-specific evidence checks; unknown is never accepted as a pass.
- Assemble only current registered L2-accepted bytes, in frozen plan order and with frozen retained durations.

## Verification

`python3 -m unittest discover -s tests -v`: 41 tests pass with FFmpeg/FFprobe installed. Tests cover all three route initializations, 30-second whole-film compilation, reference/claim/QA failures, continuation lineage, stale requests, mocked paid POST deduplication, v2 compatibility and real synthetic-media frame-exact assembly. Fixtures are synthetic and never constitute actual evidence or user approval.

## Remaining execution gates

At each real run, inspect current provider capabilities and product/source evidence; obtain applicable paid authorization and the user's reference lock. Actual generated images, raw videos and the final master still require L1/L2/L3 review. Optional buyer/trend research may be unavailable and must be labelled accordingly. White text, voiceover and music require explicit postproduction; the bundled assembly tool does not silently add them.

The external product-ugc-pipeline skill is not modified. Chronoforge consumes its acquisition/cognition workflow and keeps its own model routing and paid-execution policy.
