# Whole-film prompt and reference compiler

execution-plan.json uses schema_version=3, mode, story_file and jobs. Each job defines id, model, purpose, generated_seconds, retain_seconds, completion_deadline, aspect_ratio, references, actions, invariants, allowed_changes, protect_configuration, audio, forbidden and end_state.

References are ordered objects: {id, role, controls, must_not_control}. Actions are {local_range: [start,end], beat_ids: [ID], instruction}. Purpose explains this container's role in the whole film; not every container repeats a hook or CTA.

## Model/reference matrix

| Task | Model | References in order |
|---|---|---|
| Product independent scene | omni_flash-10s | storyboard, product_identity; optional operation only for evidenced non-protected motion |
| Recreation independent scene | omni_flash-10s | minimal character/environment/hero_prop/storyboard/state references (1–7) |
| Hybrid independent scene | omni_flash-10s | adapted storyboard, product_identity; optional source composition with exclusions |
| Continuous scene, any route | omni_flash-10s-fl | boundary_frame, target_end_frame, exactly two |
| Deliberately shorter independent scene | omni-flash | up to 3 role-selected images; 4/6/8/10 seconds |

Continuation sets continuation_of to the registered parent container. Extract its true last frame after L2; register it as a reference depending on that container. Boundary L1 QA includes boundary_of, true_last_frame_verified=true, plus continuation_warning_review if parent acceptance has warnings. Lock boundary and target together. Product identity is already baked into endpoints; never append a third identity image. New editorial scenes are independent jobs.

continuation_of must identify the immediately preceding plan job's asset_id (or id if omitted). A true-last-frame continuation requires the preceding generated clip to be fully retained. If the parent is trimmed, its discarded final frame is not the visible seam: use a new-scene cut or revise the endpoint/retention plan rather than silently propagating an unseen state. V3 assembly checks ordered asset IDs and retained durations against the frozen plan.

## Image references

All new image requests default to tt-image-2.5 with registered source/prior-reference artifact IDs, aspect_ratio, resolution=2K, version=sunburst, quality=high, background=opaque. Scene frames use 9:16; reference grids may use the planned grid ratio. Inspect actual saved dimensions.

Canonical source photos govern product shape; identity grids supplement them. End frames also reference the accepted start frame. Endpoint invariants include selected SKU, wardrobe, scene and contact geometry. Storyboards are grids; endpoints are single undivided photos. Record provider, params, hash, role and exclusions. Do not regenerate correct old references solely to change provider.

## Prompt compilation

Compile from a single frozen whole-film plan: specification → numbered image roles → purpose → invariants/allowed changes → timed actions → audio → product-specific prohibitions → deadline/end state. Never inject an unconditional same-room/camera rule, irrelevant device bans, or “image 2 is the identity” across modes.

audio.policy is native, ambient, silent, or post_voiceover. Native requires language and exact complete text. Check actual speech duration, especially non-English. Specify native speech once; assign complete lines in the whole-film script. Post_voiceover requests environmental sound without speech/music; mix separately after generation.

All generated visuals are text-free. Compile white labels/captions from a separate edit-time text plan; exact claims and display intervals are reviewed in L3. Typography changes invalidate postproduction/L3, not paid footage.

Prompts above 4,000 characters fail. Shorten complete redundant clauses in the plan; preserve beats, references, SKU, contact constraints and exact audio. No substring truncation. The .compile.json sidecar records dependencies; provider payload stays exactly model/prompt/params. Changed story/timeline/evidence requires recompile and affected-reference review.

## Executable sample

See tests/test_routes.py for synthetic three-route contract fixtures. They are test evidence only and must never be used as real review or user approval.
