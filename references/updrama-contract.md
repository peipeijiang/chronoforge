# UpDrama adapter profile

This is the profile observed in the original August 2026 run, not a claim that today's service has been revalidated. Before a paid batch, fetch authenticated guide/model details and review their bodies. If they disagree with this profile, stop and adapt/test the parser first. A successful HTTP GET or a snapshot hash alone does not validate a contract.

| Operation | Observed endpoint / shape |
|---|---|
| Guide | GET `https://api.lk888.ai/api/v1/skills/guide` |
| Image2 detail | GET `https://api.lk888.ai/api/v1/skills/models/gpt-image-2` |
| Omni detail | GET `https://api.lk888.ai/api/v1/skills/models/omni_flash-10s` |
| Create | POST `https://api.lk888.ai/v1/media/generate` |
| Create response | `{"code":200,"data":{"task_id":123456}}` |
| Status | GET `https://api.lk888.ai/api/v1/skills/task-status?task_id=123456` |
| Status response | Bare object with lowercase `state`, boolean `is_final`, and `result_url` |

The original pasted media documentation also described `/v1/media/status` and an `id/status` create response. Those are a **different documented interface**, not aliases to silently mix into this observed adapter. Do not invent `/v1/media/task-status?taskId=` or uppercase states.

The adapter supports these recreation-specific requests:

| Model | params | Reference policy |
|---|---|---|
| `gpt-image-2` | `images`, `size`, optional `quality` = auto/high/medium/low | 1–14 source frames or previous images; no reference lock needed to create them |
| `omni_flash-10s` | `images`, `aspect_ratio` = 9:16/16:9 | 1–7 L1-accepted, human-locked references; fixed 10 seconds |

The recreation adapter intentionally requires references even if the service offers text-only generation. It does not implement webhooks; that is an adapter limitation, not a claim the service prohibits them. Image dimensions and service limits must be checked against the fetched detail. Model branding in a reseller description is not proof of upstream model identity.

`preflight --run-dir RUN` saves response bodies under `provider/` and reports `fetched_review_required`. Inspect allowed parameters, response envelopes, limits and supported reference transport before proceeding. Keep snapshots local; they may include account-specific information.

`validate REQUEST` checks a **planned** request, including unresolved `artifact://ID` references. `validate REQUEST --ready --run-dir RUN` additionally resolves local bytes, checks dependency freshness and enforces the video reference lock. Submission always runs the ready gate. JSON/data URLs are resolved in memory; never save credential headers or base64-expanded requests to Git.

Use `UPDRAMA_API_KEY` from the environment. Do not echo its value or publish account records. A local confirmation phrase records operator intent; it does not manufacture user authorization or enforce a monetary budget.
