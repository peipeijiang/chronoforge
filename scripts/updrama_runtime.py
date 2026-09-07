#!/usr/bin/env python3
"""Fail-closed UpDrama runtime for ChronoForge paid media jobs."""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import pathlib
import ssl
import urllib.error
import urllib.parse
import urllib.request
import time

from workflow import resolve, sha

MEDIA_BASE = "https://api.lk888.ai"
SKILLS_BASE = "https://api.lk888.ai/api"
ALLOWED_MODELS = {"gpt-image-2", "omni_flash-10s"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load(path: str) -> dict:
    value = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("request must be a JSON object")
    return value


def api_key() -> str:
    value = os.environ.get("UPDRAMA_API_KEY", "")
    if not value:
        raise RuntimeError("UPDRAMA_API_KEY is not set")
    return value


def context() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def call(method: str, url: str, body: dict | None = None, timeout: int = 120) -> dict:
    req = urllib.request.Request(
        url, data=canonical(body) if body is not None else None, method=method,
        headers={"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout, context=context()) as response:
        value = json.loads(response.read().decode())
    if not isinstance(value, dict):
        raise RuntimeError("provider returned non-object JSON")
    return value


def append(run_dir: pathlib.Path, value: dict) -> None:
    path = run_dir / "media-jobs.jsonl"
    with path.open("a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps({"recorded_at": now(), **value}, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
        fcntl.flock(f, fcntl.LOCK_UN)


def validate(request: dict) -> list[str]:
    errors: list[str] = []
    if set(request) - {"model", "prompt", "params"}:
        errors.append("only model, prompt and params are allowed at top level")
    if request.get("model") not in ALLOWED_MODELS:
        errors.append("model is not allow-listed")
    if not isinstance(request.get("prompt"), str) or not request["prompt"].strip():
        errors.append("prompt must be nonempty")
    params = request.get("params")
    if not isinstance(params, dict):
        return errors + ["params must be an object"]
    images = params.get("images", [])
    if not isinstance(images, list) or not images:
        errors.append("reference images must be a nonempty list")
        images = []
    if any(not isinstance(x, str) or not x.startswith(("https://", "http://", "data:image/", "artifact://")) for x in images):
        errors.append("images must be URLs, image data URLs or planned artifact:// IDs")
    if request.get("model") == "gpt-image-2":
        if set(params) - {"images", "size", "quality"}:
            errors.append("unexpected Image2 params")
        if not 1 <= len(images) <= 14:
            errors.append("Image2 requires 1-14 images")
        if not params.get("size"):
            errors.append("Image2 size is required")
        if params.get("quality", "auto") not in {"auto", "high", "medium", "low"}:
            errors.append("invalid Image2 quality")
    if request.get("model") == "omni_flash-10s":
        if set(params) - {"images", "aspect_ratio"}:
            errors.append("unexpected Omni params")
        if not 1 <= len(images) <= 7:
            errors.append("Omni requires 1-7 images")
        if params.get("aspect_ratio") not in {"9:16", "16:9"}:
            errors.append("invalid Omni aspect ratio")
    return errors


def preflight(args: argparse.Namespace) -> int:
    rows = []
    snapshot_dir = pathlib.Path(args.run_dir) / 'provider' / dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    for path in ("/v1/skills/guide", "/v1/skills/models/gpt-image-2", "/v1/skills/models/omni_flash-10s"):
        value = call("GET", SKILLS_BASE + path)
        if not value or value.get('error') or value.get('code', 200) != 200:
            raise RuntimeError('provider preflight error; do not submit')
        destination = snapshot_dir / (path.rsplit('/', 1)[-1] + '.json')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical(value))
        rows.append({"path": path, "file": str(destination), "sha256": digest(value)})
    print(json.dumps({"status": "fetched_review_required", "snapshots": rows, "secret_logged": False}))
    return 0


def check(args: argparse.Namespace) -> int:
    request = load(args.request)
    errors = validate(request)
    if not errors and args.ready:
        if not args.run_dir:
            raise ValueError('--ready needs --run-dir')
        errors = validate(resolve(request, args.run_dir, request['model'] == 'omni_flash-10s'))
    print(json.dumps({"status": "pass" if not errors else "fail", "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 2


def submit(args: argparse.Namespace) -> int:
    if args.confirm_paid != "I_UNDERSTAND_THIS_IS_PAID":
        raise RuntimeError("paid confirmation phrase mismatch")
    run_dir = pathlib.Path(args.run_dir).resolve()
    request = load(args.request)
    errors = validate(request)
    if errors:
        raise ValueError("; ".join(errors))
    request = resolve(request, run_dir, request['model'] == 'omni_flash-10s')
    request_hash = digest(request)
    job_id = hashlib.sha256((args.job_id + ":" + request_hash).encode()).hexdigest()[:24]
    lock = run_dir / ".paid-create.lock"
    lock.touch(exist_ok=True)
    with lock.open("r+") as lease:
        fcntl.flock(lease, fcntl.LOCK_EX)
        rows = ledger(run_dir)
        prior = [r for r in rows if r.get('operator_job_id') == args.job_id]
        if prior:
            if prior[0].get('request_sha256') != request_hash:
                raise ValueError('job ID already used with different bytes; use a versioned retake ID after approval')
            known = [r for r in rows if r.get('job_id') == job_id and r.get('state') == 'task_known']
            if known:
                print(json.dumps({'state': 'task_known', 'task_id': known[-1]['task_id'], 'reused': True}))
                return 0
            raise RuntimeError('job already attempted; reconcile it, never repeat its POST')
        intents = {r['job_id']: r for r in rows if r.get('record_type') == 'submit_intent'}
        closed = {r.get('job_id') for r in rows if r.get('state') in ('task_known', 'confirmed_no_task')}
        if any(r['model'] == request['model'] and jid not in closed for jid, r in intents.items()):
            raise RuntimeError('unresolved submission in this model lane; reconcile before another POST')
        append(run_dir, {"record_type":"submit_intent","job_id":job_id,"operator_job_id":args.job_id,"model":request["model"],"request_sha256":request_hash,"state":"submitting"})
        try:
            value = call("POST", MEDIA_BASE + "/v1/media/generate", request, args.timeout)
        except Exception as exc:
            # HTTP 5xx and invalid JSON can happen AFTER a task was accepted.
            # Even a rejection needs reconciliation under this conservative profile.
            append(run_dir, {"record_type":"submission_result","job_id":job_id,"state":"unknown_submission","error_class":type(exc).__name__,"retry_allowed":False})
            print(json.dumps({"job_id":job_id,"state":"unknown_submission","retry_allowed":False}))
            return 3
        task_id = (value.get("data") or {}).get("task_id") if isinstance(value.get("data"), dict) else None
        if value.get("code") != 200 or not str(task_id).isdigit():
            append(run_dir, {"record_type":"submission_result","job_id":job_id,"state":"contract_anomaly","response_sha256":digest(value)})
            raise RuntimeError("create response contract mismatch")
        append(run_dir, {"record_type":"submission_result","job_id":job_id,"model":request["model"],"state":"task_known","task_id":str(task_id)})
        print(json.dumps({"job_id":job_id,"state":"task_known","task_id":str(task_id)}))
    return 0


def status(args: argparse.Namespace) -> int:
    run_dir = pathlib.Path(args.run_dir).resolve()
    url = SKILLS_BASE + "/v1/skills/task-status?" + urllib.parse.urlencode({"task_id": args.task_id})
    value = call("GET", url, timeout=20)
    state = value.get("state")
    if state not in {'pending', 'running', 'success', 'failed'} or type(value.get('is_final')) is not bool:
        raise RuntimeError('status contract mismatch; keep task ID, never recreate task')
    final = value.get("is_final") is True
    if final != (state in {'success', 'failed'}):
        raise RuntimeError('inconsistent terminal status')
    result = value.get("result_url") if final and state == "success" else None
    if final and state == 'success' and (not isinstance(result, str) or not result.startswith('https://')):
        raise RuntimeError('success missing HTTPS result URL; retry GET, not POST')
    append(run_dir, {"record_type":"status_observation","task_id":str(args.task_id),"state":state,"is_final":final,"result_url":result})
    print(json.dumps({"task_id":str(args.task_id),"state":state,"is_final":final,"result_url":result,"error":value.get("error", "")}, ensure_ascii=False))
    return 4 if state == "failed" else 0


def ledger(run_dir):
    path = pathlib.Path(run_dir) / 'media-jobs.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def reconcile(args):
    root = pathlib.Path(args.run_dir)
    with (root / '.paid-create.lock').open('a+') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX)
        rows = [r for r in ledger(root) if r.get('job_id') == args.job_id]
        if not rows:
            raise ValueError('unknown ledger job ID')
        if any(r.get('state') in ('task_known', 'confirmed_no_task') for r in rows):
            raise ValueError('job already reconciled or known; do not replace its provenance')
        if not args.evidence.strip():
            raise ValueError('reconciliation evidence required')
        if args.task_id and not args.task_id.isdigit():
            raise ValueError('numeric task ID required by this observed profile')
        append(root, {'record_type': 'reconciliation', 'job_id': args.job_id,
                      'state': 'task_known' if args.task_id else 'confirmed_no_task',
                      'task_id': args.task_id, 'evidence': args.evidence})
    return 0


def collect(args):
    """Bounded polling and original-byte collection; no paid POST and no CDN bearer."""
    if not 0 <= args.wait_seconds <= 60:
        raise ValueError('wait-seconds must be 0-60; resume same task after yielding')
    root = pathlib.Path(args.run_dir).resolve()
    destination = pathlib.Path(args.output).resolve()
    destination.relative_to(root)
    if destination.exists() or destination.with_suffix(destination.suffix + '.part').exists():
        raise ValueError('refusing to overwrite media or interrupted download')
    deadline = time.monotonic() + args.wait_seconds
    while True:
        code = status(args)
        if code:
            return code
        row = [r for r in ledger(root) if r.get('record_type') == 'status_observation'
               and r.get('task_id') == str(args.task_id)][-1]
        if row.get('is_final'):
            break
        if time.monotonic() >= deadline:
            print(json.dumps({'state': 'pending_resume_same_task', 'task_id': args.task_id}))
            return 5
        time.sleep(min(4, max(0, deadline - time.monotonic())))
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + '.part')
    # Download only the known provider result. Never send the API credential to a CDN.
    with urllib.request.urlopen(row['result_url'], timeout=60, context=context()) as response, partial.open('xb') as out:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            out.write(block)
    if not partial.stat().st_size:
        raise RuntimeError('empty download; preserved .part for inspection')
    partial.rename(destination)
    append(root, {'record_type': 'download', 'task_id': args.task_id,
                  'file': str(destination.relative_to(root)), 'sha256': sha(destination),
                  'qa': 'pending'})
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    x = sub.add_parser("preflight"); x.add_argument('--run-dir', required=True); x.set_defaults(func=preflight)
    x = sub.add_parser("validate"); x.add_argument("request"); x.add_argument('--ready', action='store_true'); x.add_argument('--run-dir'); x.set_defaults(func=check)
    x = sub.add_parser("submit"); x.add_argument("request"); x.add_argument("--run-dir", required=True); x.add_argument("--job-id", required=True); x.add_argument("--confirm-paid", required=True); x.add_argument("--timeout", type=int, default=180); x.set_defaults(func=submit)
    x = sub.add_parser("status"); x.add_argument("task_id"); x.add_argument("--run-dir", required=True); x.set_defaults(func=status)
    x = sub.add_parser('collect'); x.add_argument('task_id'); x.add_argument('--run-dir', required=True); x.add_argument('--output', required=True); x.add_argument('--wait-seconds', type=float, default=40); x.set_defaults(func=collect)
    x = sub.add_parser('reconcile'); x.add_argument('--run-dir', required=True); x.add_argument('--job-id', required=True); x.add_argument('--evidence', required=True)
    group = x.add_mutually_exclusive_group(required=True); group.add_argument('--task-id'); group.add_argument('--no-task', action='store_true'); x.set_defaults(func=reconcile)
    return p


def main() -> int:
    try:
        args = parser().parse_args()
        return args.func(args)
    except Exception as exc:
        print(json.dumps({"status":"error","error_class":type(exc).__name__,"message":str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
