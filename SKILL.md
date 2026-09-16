---
name: chronoforge
description: Create reference-guided multi-clip films from uploaded videos (recreation), product page links (original ads), or both (product-constrained adaptation), with evidence, whole-film stories, locked references, safe paid execution and layered QA.
---

# ChronoForge · v3

Route the input before analysis. Preserve evidence, versioned editorial intent and asset lineage through generation and assembly. Do not promise exact faces, pixels, motion or original audio.

## 1. Route and initialize

| Input | Route | Evidence and creative work |
|---|---|---|
| Uploaded/local video | recreation | Read/use watch; inspect the entire source, then reconstruct its story |
| Product page link | product_video | Read/use product-ugc-pipeline; collect complete evidence, author an original whole-film story |
| Product link + uploaded/local video | hybrid | Both evidence paths; product truth constrains the source-inspired adaptation |
| Neither, ambiguous input, multiple unclear targets | Ask one focused question | Never silently select a product or invent a source |

Test the combined case first. A bare link is a candidate product page: inspect it before confirming the route. A video-only page requires clarification/upload; it does not automatically invoke watch. Ancillary product-page video does not turn a product job into a remake. Competitor-link research does not invoke watch.

```bash
python3 scripts/init_run.py /path/source.mp4 --out RUN
python3 scripts/init_run.py --product-url 'https://shop.example/product' --duration 30 --out RUN
python3 scripts/init_run.py /path/source.mp4 --product-url 'https://shop.example/product' --duration 30 --out RUN
```

Read [route-workflows.md](references/route-workflows.md) for the selected route. Source-bearing routes also read [story-compiler.md](references/story-compiler.md). Session/region-sensitive product pages use ego-browser first through product-ugc-pipeline. Never bypass a login or challenge.

## 2. Freeze evidence and whole-film story

- Source routes retain full-duration media/timecode/visual/transcript/audio/uncertainty evidence. A frame sample does not prove audio was heard or an unseen action occurred.
- Product routes require the complete manifest image set, per-image vision, brief, selected SKU, claim ledger and source-backed operation/risk assessment. Reviews and competitor research are optional. Mark inferred buyer motivations as hypotheses.
- Codex authors one complete film before dividing it into jobs. Multiple creative variants are multiple films, never automatically successive chapters.
- Preserve cause/action/reaction/payoff where narrative requires it. Detail, establishing and montage beats instead declare supports and editorial_purpose; do not invent causal events.
- Version story, timeline and plan. Observed time stays in source_range; chosen edit time uses editorial_range. Product originals have no source timecodes. Explicitly record adaptations in source-bearing routes.

Run validate_story.py, validate_timeline.py and validate_plan.py on frozen contracts. These are structural checks, not semantic acceptance.

## 3. Generate, inspect and lock references

Read [prompt-and-reference-contract.md](references/prompt-and-reference-contract.md) and [reference-execution.md](references/reference-execution.md).

Default all image work to LK888/upDrama **tt-image-2.5**: identity, optional operation grid, storyboard and scene endpoints. **tt-image-2** is the only planned fallback, after a known terminal failure within authorized attempts. Unknown submissions require reconciliation before switching models. No LaoZhang image fallback or VEO default. Preserve historical gpt-image-2 assets; new v3 runs reject that legacy model.

Canonical source photos govern product identity; generated sheets are secondary guidance. Scene endpoints are single undivided photos; storyboard grids are role-labelled planning references. High-risk folding/assembly/connection routes generate the verified ready state; real footage or separately produced endpoint edits communicate omitted transitions.

Register assets with actual source/story dependencies, provider/request/hash and role/exclusions. Do L1 using built-in vision and media checks, then obtain the user's reference-pack lock. Images are generated BEFORE L1 and human lock. Reuse sound assets and revise only affected dependencies.

## 4. Compile each video request

```bash
python3 scripts/compile_prompt.py --run-dir RUN --plan RUN/manifests/execution-plan.json --job C01 --output RUN/requests/video/C01-v1.json
```

The compiler checks evidence, story, timeline, beat coverage and reference roles, writes a dependency fingerprint, and rejects overlong prompts rather than truncating required beats. The agent still reviews meaning.

- New/independent scenes: **omni_flash-10s**. Product routes normally use storyboard + product identity; recreation uses role-selected character/environment/prop/state references.
- Continuous shots: **omni_flash-10s-fl**, preceding accepted container's true last frame first, target end frame second. Register boundary provenance and L1, extend the human lock, then compile. Only accepted L2 can feed continuation; warnings need explicit continuation review.
- Deliberately variable 4/6/8/10-second jobs: **omni-flash**. Differently named routes are not interchangeable.

Do not force every C02 into continuation. New scene cuts use independent jobs. Do not send raw product photos alone as scene references. Never hardcode “image 2 is the product” across modes. Apply only relevant prohibitions and invariant camera/person/environment fields; planned cuts may change them. Generate text-free visuals; white labels/captions belong to postproduction.

## 5. Safe paid execution

Read [provider-runtime.md](references/provider-runtime.md) and [updrama-contract.md](references/updrama-contract.md). Refresh and inspect capabilities before each authorized batch; record reviewed snapshot hashes. V3 ready/submission checks enforce the reviewed model profile and current compiled video plan, then resolve actual reference bytes and human lock.

```bash
python3 scripts/updrama_runtime.py preflight --run-dir RUN
python3 scripts/updrama_runtime.py validate REQUEST --ready --run-dir RUN
python3 scripts/updrama_runtime.py submit REQUEST --run-dir RUN --job-id C01-v1-attempt1 --confirm-paid I_UNDERSTAND_THIS_IS_PAID
python3 scripts/updrama_runtime.py collect TASK_ID --run-dir RUN --output RUN/media/containers/C01-v1.raw.mp4 --wait-seconds 40
```

Preserve serial paid POSTs, fsynced submit intent, known-task reuse and unknown-submission lane blocking. Independent known jobs may be polled/downloaded concurrently. Continuation waits for prior L2/boundary approval. Do not import product-ugc's automatic POST retry, paid regeneration, provider substitution or concurrent-create behavior. A download failure resumes the same task. Reference lock and batch count/retry authorization remain distinct; reuse applicable user authorization, never manufacture it.

## 6. L2, assembly and L3

Read [qa-contract.md](references/qa-contract.md) and [delivery-and-canary.md](references/delivery-and-canary.md). All routes use L1/L2/L3 with route-specific checks. Record actual evidence and limits; unknown is not a pass. Unavailable built-in vision requires an explicitly working alternative and disclosure; never silently restore LaoZhang or MiniMax vision.

L2 inspects full decode, every required beat, motion/contact, internal cuts, product/character state, audio and completion before trim. Register accepted raw containers with every actual dependency. Retake the earliest responsible layer: evidence/reference, generated motion or local assembly.

V3 assembly manifests use schema_version 3 and run_dir; assemble.py checks current registered L2 acceptance and original hashes before trimming, normalization and concatenation. Inspect center-crop framing. Postproduction adds reviewed white text/voiceover/music to a new version, then full L3 checks the actual delivery master. Bundled assembly supports generated or silent audio; custom text/mix requires local FFmpeg/editing work, never claim it was automatically rendered.

Deliver the current master and private provenance/QA package. Preserve raw/rejected/superseded assets. Never publish private product/account data, expanded image payloads, keys or provider task/result URLs. Restore old runs using [v2-restoration-audit.md](references/v2-restoration-audit.md); v2 contracts remain compatible and must not be silently relabelled v3.

For verified coverage and remaining execution gates, see [v3-route-audit.md](references/v3-route-audit.md).
