# Paid execution and recovery

Read [updrama-contract.md](updrama-contract.md) for the only maintained adapter profile, and [reference-execution.md](reference-execution.md) for artifact registration and lock commands.

## Before a paid batch

1. Confirm the user-authorized models, exact job IDs, count and retry allowance. Image authorization and reference-lock approval are different events.
2. Fetch and inspect the current guide/model snapshots. Local schema checks are only one part of this review.
3. Validate planned story/timeline/beat coverage; validate **ready** reference bytes immediately before submission.
4. Use one run directory and one creative writer for the project. The paid-create file lock serializes POSTs inside that run, not across arbitrary copies or machines.
5. Submit using a versioned operator ID, such as `C02-v3-attempt1`. Keep request manifests immutable after approval.

## Ledger behavior

The adapter writes and fsyncs `submit_intent` before POST. It records a known task ID, or an unresolved state. A process crash after intent is conservatively unresolved too.

- Repeating an existing job ID with the same resolved bytes returns its known task ID, without POST.
- Reusing that ID with different bytes is rejected.
- An intent with no known task or evidence-backed `confirmed_no_task` blocks other submissions in its model lane.
- HTTP errors, timeouts, invalid JSON and unexpected create envelopes are **not** safe reasons to replay POST.
- This is local duplicate protection, **not provider idempotency**. Do not evade it by using a fresh run directory.
- The adapter does not price jobs or track account-wide budgets. The agent must stay within the actual authorization.

## Unknown submission

Use read-only provider task/account tools or support evidence to identify whether a task was created. Matching only model/time/count is insufficient if another submission could match. Never infer a task from a guessed ID.

Once there is reliable evidence, record one of:

```bash
python3 scripts/updrama_runtime.py reconcile --run-dir RUN --job-id LEDGER_JOB_ID \
  --task-id 123456 --evidence "Provider task record identifies this submission"
python3 scripts/updrama_runtime.py reconcile --run-dir RUN --job-id LEDGER_JOB_ID \
  --no-task --evidence "Provider confirmed no task was created"
```

Use the hashed ledger job ID, not the human-readable operator ID, here. Reconciliation cannot discover the truth itself. Only record verified evidence. Even confirmed no-task recovery does not authorize a new charge: a new attempt needs an authorized, new operator job ID.

## Known task and original media

Poll `status TASK_ID --run-dir RUN` or use:

```bash
python3 scripts/updrama_runtime.py collect TASK_ID --run-dir RUN \
  --output RUN/media/containers/C01-v3.raw.mp4 --wait-seconds 40
```

`collect` polls in a short bounded window (individual network requests can add latency), yields `pending_resume_same_task` when unfinished, and can be resumed with the **same** task ID. It never submits. Terminal failure exits without retry. Success downloads original bytes without sending the API key to the result CDN, records SHA-256, and leaves QA pending. It refuses existing outputs and interrupted `.part` files. Inspect an interrupted download, then choose a new output path; never create another paid task to solve a download failure.

Decode/probe after collection: a nonempty file is not necessarily valid media. Preserve raw files before crop/trim/re-encode. Keep result URLs and ledger private; publish only sanitized examples.

## Retake classification

| Observation | Response |
|---|---|
| No rendered media / overload / refund | Provider failure, not evidence of a bad creative topology; request scoped retry approval |
| Reference defines wrong setting, prop or causal state | Repair that reference, L1, new human lock; invalidate dependents |
| Render exists, wrong motion/cut/beat order | Controlled prompt retake of the affected container |
| Same boundary fails in baseline and one controlled retake | Consider splitting only that container; disclose new cost and seam |
| Valid media, wrong trim/codec/audio mix | Local assembly repair; no paid video retake |
| New source interpretation contradicts old acceptance | New story version, dependency invalidation, targeted regeneration |

One approved single retry means one new submission, not a retry-until-success loop.
