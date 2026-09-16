# UpDrama adapter profile

The checked-in profile is an adapter contract, not a live availability claim. Before each paid batch fetch and inspect guide and model snapshots. If actual capabilities differ, stop and adapt/test the parser; HTTP success alone is not contract approval.

| Operation | Maintained interface |
|---|---|
| Guide | GET https://api.lk888.ai/api/v1/skills/guide |
| Model details | GET https://api.lk888.ai/api/v1/skills/models/MODEL |
| Create | POST https://api.lk888.ai/v1/media/generate |
| Create response | code=200, data.task_id numeric |
| Status | GET https://api.lk888.ai/api/v1/skills/task-status?task_id=ID |
| Status response | lowercase state, boolean is_final, HTTPS result_url on success |

Do not silently mix in /v1/media/status envelopes from another adapter. Reconcile mismatches before production.

| Model | Params | References |
|---|---|---|
| tt-image-2.5 (default), tt-image-2 (scoped fallback) | images, aspect_ratio, resolution, version, quality, background | 1–16 registered image artifacts; new output precedes L1/lock |
| omni_flash-10s | images, aspect_ratio | 1–7 locked references, fixed 10s |
| omni_flash-10s-fl | images, aspect_ratio | 2 locked references for v3: actual preceding boundary then target endpoint, fixed 10s |
| omni-flash | images, aspect_ratio, duration, enhance_prompt; optional enable_upsample | 1–3 locked references, 4/6/8/10s |
| gpt-image-2 | historical size/quality request schema only | Legacy v2 compatibility; prohibited for new v3 calls |

Model names are reseller route identifiers, not proof of upstream identity. TT defaults: resolution=2K, version=sunburst, quality=high, background=opaque. Check fetched details before use. All Omni prompts are at most 4,000 characters.

preflight stores private guide/model response snapshots. After ACTUAL review write provider/contract-review.json:
```json
{
  "reviewer": "actual reviewer",
  "reviewed_at": "actual ISO timestamp",
  "models": ["tt-image-2.5", "omni_flash-10s"],
  "snapshots": {
    "provider/ACTUAL_TIMESTAMP/guide.json": "actual SHA256",
    "provider/ACTUAL_TIMESTAMP/tt-image-2.5.json": "actual SHA256",
    "provider/ACTUAL_TIMESTAMP/omni_flash-10s.json": "actual SHA256"
  }
}
```
This example is not approval. Refresh review each batch. V3 ready_policy checks the selected model, timestamp/identity presence and snapshot hashes; the agent reviews allowed params, transport, pricing/channel state and actual batch authorization. The runtime is not an account-wide budget manager.

validate REQUEST accepts planned artifact IDs. --ready resolves bytes and checks fresh plan/dependencies and current human lock for ALL Omni routes. submit repeats these gates. Expanded image data only exists in memory. Use UPDRAMA_API_KEY or LK888_API_KEY from environment; never log values. No LaoZhang route or VEO fallback is implemented.
