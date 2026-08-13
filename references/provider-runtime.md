# Provider runtime reference

## Contents

1. Runtime invariants
2. UpDrama profile
3. Paid-job state machine
4. Ambiguous submission recovery
5. Security

## Runtime invariants

- Keep creative manifests immutable after reference lock.
- Compile provider requests into separate runtime artifacts.
- Hash requests and input assets.
- Serialize paid creates with a single-writer lock.
- Append and fsync `submit_intent` before POST.
- Record task ID only after validating the current response contract.
- Never automatically retry timeouts or connection loss after a paid POST.
- Poll with a bounded interval and preserve all terminal results.

## UpDrama profile

Refresh authenticated guide and model detail before each paid batch. At the time this skill was authored, the observed contract was:

- media create: `POST https://api.lk888.ai/v1/media/generate`
- discovery and status base: `https://api.lk888.ai/api`
- preferred task status: `GET /v1/skills/task-status?task_id=...`
- create request: top-level `model`, `prompt`, `params`
- create success: `code == 200` and numeric `data.task_id`
- terminal: `is_final == true`
- success: `state == "success"` plus nonempty `result_url`

Treat this as a profile to verify, not an eternal guarantee. Static exported examples may drift.

Useful model roles:

- `gpt-image-2`: reference-image reconstruction; current details determine limits and accepted sizes.
- `omni_flash-10s`: fixed 10-second 720p reference video; current details determine image count and aspect ratios.

## Paid-job state machine

```text
planned
  → submit_intent_written
  → submitting
  → task_known → pending/running → success|failed
  ↘ submission_rejected
  ↘ unknown_submission
  ↘ contract_anomaly
```

Recommended ledger record fields:

```json
{
  "record_type":"submit_intent",
  "job_id":"stable-derived-id",
  "operator_job_id":"human-readable-id",
  "model":"model-name",
  "request_sha256":"...",
  "input_hashes":[],
  "state":"submitting",
  "recorded_at":"ISO-8601"
}
```

Do not put prompts or secret headers in the ledger when hashes suffice.

## Ambiguous submission recovery

When the POST may have reached the provider but no valid response was received:

1. Mark `unknown_submission` and prohibit automatic retry.
2. Stop same-model paid creates unless isolation is provable.
3. Reconcile using provider usage/task history and submission time.
4. Auto-adopt only when exactly one unmatched task can be proven and no concurrent same-model create occurred.
5. Otherwise require human/provider support resolution.

If the provider later supports idempotency keys or request-hash lookup, prefer those and update the adapter.

## Security

- Read keys only from provider-specific environment variables.
- Never echo, serialize, screenshot, or include keys in final responses.
- Validate URLs before download.
- Keep source frames local unless their submission is explicitly authorized.
- Resolve local source images to in-memory data URLs when supported; do not write expanded base64 requests to disk.
- Remove recognizable people and source watermarks from generated reference assets when the task permits.
- Confirm rights to reproduce the source and likenesses when use is not obviously authorized.

