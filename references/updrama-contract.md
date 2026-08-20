# UpDrama runtime contract

This document captures the UpDrama API contract as observed during the skill's development. Provider contracts drift over time; always run `preflight` before paid work and validate request schemas against the authenticated guide.

## Base URL and routing

At the time of authoring:
- Media create: `POST https://api.lk888.ai/v1/media/generate`
- Task status: `GET https://api.lk888.ai/v1/media/task-status?taskId={task_id}`
- Discovery and model detail: `GET https://api.lk888.ai/v1/skills/guide`

The guide returns provider-controlled model names, display labels, default parameters, allowed fields, and current pricing. Do not assume static examples override the authenticated guide.

## gpt-image-2 allowed fields

Model: `gpt-image-2`

Request schema (allowed keys only):
```json
{
  "model": "gpt-image-2",
  "prompt": "string (required)",
  "params": {
    "images": ["url", "url", ...],
    "size": "1088x1920" | "1920x1088" | ...,
    "quality": "high" | "standard"
  }
}
```

**Prohibited fields** (rejected or ignored):
- `seed`, `random_seed`
- `negative_prompt`
- `num_outputs`, `n`
- `notify_url`, `webhook_url`
- `source_video`, `init_image`

Timeout: 300 seconds per create request. If the server does not respond within 300 seconds, treat it as a connection loss, not a task failure; do NOT automatically retry.

## omni_flash-10s allowed fields

Model: `omni_flash-10s`

Request schema (allowed keys only):
```json
{
  "model": "omni_flash-10s",
  "prompt": "string (required)",
  "params": {
    "images": ["url", "url", ...],
    "aspect_ratio": "9:16" | "16:9"
  }
}
```

**Prohibited fields** (rejected or ignored):
- `seed`, `random_seed`
- `negative_prompt`
- `duration` (fixed at 10 seconds)
- `source_video`, `init_video`
- `start_frame`, `end_frame`
- `motion_strength`, `motion_bucket_id`
- `notify_url`, `webhook_url`

Timeout: 600 seconds per status poll. The model generates approximately 10 seconds of video; polling should continue until `is_final` becomes true or an error state is reached.

## Terminal state contract

The status response includes:
```json
{
  "code": 200,
  "message": "...",
  "data": {
    "task_id": "string",
    "state": "PENDING" | "PROCESSING" | "SUCCESS" | "FAILED" | ...,
    "is_final": boolean,
    "result_url": "https://..." | null,
    ...
  }
}
```

**Terminal conditions:**
- `code != 200`: API error; do not retry without manual review.
- `data.is_final == true`: task reached a final state (success or failure).
- `data.state == "SUCCESS" && data.result_url != null`: download and hash the result.
- `data.state == "FAILED"`: task failed; analyze the message and decide whether to retry with a different prompt or reference.

**Ambiguous submission** (connection loss after POST but before task ID):
1. Append `unknown_submission` to the job ledger.
2. Query usage/task history by model, narrow `created_at` window, and normalized input hashes.
3. Auto-adopt only if exactly one unmatched task can be proven and no concurrent same-model create occurred.
4. Otherwise require human or provider support resolution before attempting a second submission.

See [provider-runtime.md](provider-runtime.md) for the general ambiguous-submission recovery protocol.

## Dynamic preflight

Before each paid batch:
1. Run `python3 scripts/updrama_runtime.py preflight` to fetch and display the current guide, model detail, and allowed fields.
2. Compare the returned schema against the request manifests. If new required fields appear or existing fields are removed, mark all pending requests as `stale` and regenerate them against the new contract.
3. Capture a redacted snapshot (remove `balance`, `pricing`, and credential echoes) and freeze it with the request batch for reproducibility.

If the guide is unreachable or returns an error, do NOT proceed with paid submission.

## Security

- Read `UPDRAMA_API_KEY` only from the environment variable.
- Never echo, serialize, screenshot, or include the key in final responses or manifests.
- Validate all `result_url` values before download.
- Do not write expanded base64 `data:` URIs to disk; resolve local source images to in-memory data URLs when supported.
- Remove recognizable people and source watermarks from generated reference assets when the task permits.
