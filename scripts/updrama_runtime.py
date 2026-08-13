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
    if any(not isinstance(x, str) or not x.startswith(("https://", "http://", "data:image/")) for x in images):
        errors.append("images must be stable URLs or image data URLs")
    if request.get("model") == "gpt-image-2":
        if set(params) - {"images", "size", "quality"}:
            errors.append("unexpected Image2 params")
        if not 1 <= len(images) <= 14:
            errors.append("Image2 requires 1-14 images")
        if not params.get("size"):
            errors.append("Image2 size is required")
    if request.get("model") == "omni_flash-10s":
        if set(params) - {"images", "aspect_ratio"}:
            errors.append("unexpected Omni params")
        if not 1 <= len(images) <= 7:
            errors.append("Omni requires 1-7 images")
        if params.get("aspect_ratio") not in {"9:16", "16:9"}:
            errors.append("invalid Omni aspect ratio")
    return errors


def preflight(_: argparse.Namespace) -> int:
    rows = []
    for path in ("/v1/skills/guide", "/v1/skills/models/gpt-image-2", "/v1/skills/models/omni_flash-10s"):
        value = call("GET", SKILLS_BASE + path)
        rows.append({"path": path, "sha256": digest(value)})
    print(json.dumps({"status": "pass", "snapshots": rows, "secret_logged": False}))
    return 0


def check(args: argparse.Namespace) -> int:
    errors = validate(load(args.request))
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
    request_hash = digest(request)
    job_id = hashlib.sha256((args.job_id + ":" + request_hash).encode()).hexdigest()[:24]
    lock = run_dir / ".paid-create.lock"
    lock.touch(exist_ok=True)
    with lock.open("r+") as lease:
        fcntl.flock(lease, fcntl.LOCK_EX)
        append(run_dir, {"record_type":"submit_intent","job_id":job_id,"operator_job_id":args.job_id,"model":request["model"],"request_sha256":request_hash,"state":"submitting"})
        try:
            value = call("POST", MEDIA_BASE + "/v1/media/generate", request, args.timeout)
        except urllib.error.HTTPError as exc:
            append(run_dir, {"record_type":"submission_result","job_id":job_id,"state":"submission_rejected","http_status":exc.code})
            raise
        except (TimeoutError, urllib.error.URLError, ConnectionError) as exc:
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
    value = call("GET", url)
    state = value.get("state")
    final = value.get("is_final") is True
    result = value.get("result_url") if final and state == "success" else None
    append(run_dir, {"record_type":"status_observation","task_id":str(args.task_id),"state":state,"is_final":final,"result_url":result})
    print(json.dumps({"task_id":str(args.task_id),"state":state,"is_final":final,"result_url":result,"error":value.get("error", "")}, ensure_ascii=False))
    return 4 if state == "failed" else 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    x = sub.add_parser("preflight"); x.set_defaults(func=preflight)
    x = sub.add_parser("validate"); x.add_argument("request"); x.set_defaults(func=check)
    x = sub.add_parser("submit"); x.add_argument("request"); x.add_argument("--run-dir", required=True); x.add_argument("--job-id", required=True); x.add_argument("--confirm-paid", required=True); x.add_argument("--timeout", type=int, default=180); x.set_defaults(func=submit)
    x = sub.add_parser("status"); x.add_argument("task_id"); x.add_argument("--run-dir", required=True); x.set_defaults(func=status)
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

