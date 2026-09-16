#!/usr/bin/env python3
"""Compile one container from a whole-film plan; preserve complete required clauses."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from routes import evidence_errors, MODES, read
from validate_plan import validate as validate_plan
from workflow import registry, current


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compile_job(job, story):
    refs = job['references']
    model = job.get('model', 'omni_flash-10s')
    first_last = model == 'omni_flash-10s-fl'
    roles = [r['role'] for r in refs]
    if first_last and roles != ['boundary_frame', 'target_end_frame']:
        raise ValueError('continuation needs ordered boundary_frame, target_end_frame')
    if not first_last and 'boundary_frame' in roles:
        raise ValueError('boundary continuation requires omni_flash-10s-fl')
    if story.get('mode') in ('product_video', 'hybrid') and not first_last:
        if 'storyboard' not in roles or 'product_identity' not in roles:
            raise ValueError('product scene requires storyboard and product_identity')
    if job.get('protect_configuration') and 'operation' in roles:
        raise ValueError('protected ready-state route must omit operation reference')
    lines = [f"Generate {job['generated_seconds']:g} seconds, {job.get('aspect_ratio', '9:16')}."]
    for i, ref in enumerate(refs, 1):
        if not ref.get('controls') or not ref.get('must_not_control'):
            raise ValueError('each image needs controls and must_not_control')
        lines.append(f"Image {i} ({ref['role']}): controls {ref['controls']}; must not control {ref['must_not_control']}.")
    if first_last:
        lines.append('Image 1 is the actual first frame; image 2 is the target final frame. End on image 2.')
    else:
        lines.append('References are role guidance, not a forced endpoint pair. Render full-frame shots, never a grid.')
    lines.append('CONTAINER PURPOSE: ' + job['purpose'])
    lines.append('INVARIANTS: ' + json.dumps(job.get('invariants', {}), ensure_ascii=False))
    lines.append('ALLOWED CHANGES: ' + json.dumps(job.get('allowed_changes', []), ensure_ascii=False))
    if job.get('protect_configuration'):
        lines.append('Keep the verified ready-state topology and connections fixed throughout. No assembly, folding or invented transition.')
    for action in job['actions']:
        start, end = action['local_range']
        lines.append(f"{start:g}-{end:g}s [{','.join(action['beat_ids'])}]: {action['instruction']}")
    audio = job.get('audio', {'policy': 'silent'})
    if audio.get('policy') not in ('native', 'ambient', 'silent', 'post_voiceover'):
        raise ValueError('unknown audio policy')
    if audio['policy'] == 'native':
        if not audio.get('language') or not audio.get('text'):
            raise ValueError('native speech requires language and complete exact text')
        lines.append(f"AUDIO: {audio['language']}; speak exactly {audio['text']}. No additional speech.")
    else:
        lines.append('AUDIO: ' + ('environment sounds only, no speech or music' if audio['policy'] in ('ambient', 'post_voiceover') else 'silent, no speech or music'))
    lines.append('FORBIDDEN: ' + json.dumps(job.get('forbidden', []), ensure_ascii=False))
    lines.append('No readable writing, subtitles, feature labels, watermark or platform UI. Text is added in postproduction.')
    lines.append(f"Finish required actions by {job.get('completion_deadline', job['retain_seconds']):g}s. Remaining discarded tail is a stable hold. End state: {json.dumps(job.get('end_state', {}), ensure_ascii=False)}")
    prompt = '\n'.join(lines)
    # A storyboard cannot recover missing instructions caused by arbitrary truncation.
    if len(prompt) > 4000:
        raise ValueError(f'prompt is {len(prompt)} characters; shorten complete clauses in the plan, never truncate beats')
    params = {'images': ['artifact://' + r['id'] for r in refs], 'aspect_ratio': job.get('aspect_ratio', '9:16')}
    if model == 'omni-flash':
        params.update(duration=str(int(job['generated_seconds'])), enhance_prompt='false')
    return {'model': model, 'prompt': prompt, 'params': params}


def check_boundary(root, job):
    if job.get('model') != 'omni_flash-10s-fl':
        return
    data = registry(root)
    boundary = current(root, data, job['references'][0]['id'])
    parent_id = job.get('continuation_of')
    if not parent_id or parent_id not in boundary.get('dependencies', {}):
        raise ValueError('boundary must depend on the actual preceding registered container')
    parent = current(root, data, parent_id)
    if parent['kind'] != 'container' or parent['status'] != 'accepted':
        raise ValueError('preceding container must have reviewed L2 acceptance')
    proof = boundary.get('qa', {})
    if proof.get('boundary_of') != parent_id or proof.get('true_last_frame_verified') is not True:
        raise ValueError('boundary QA must identify its parent and verify the true last frame')
    if parent.get('qa', {}).get('decision') == 'accepted_with_warnings' and not proof.get('continuation_warning_review'):
        raise ValueError('explicit warning review required before propagating boundary')


def build(root, plan_path, job_id):
    root, plan_path = Path(root).resolve(), Path(plan_path).resolve()
    story_path = (plan_path.parent / read(plan_path)['story_file']).resolve()
    if not plan_path.is_relative_to(root) or not story_path.is_relative_to(root):
        raise ValueError('plan and story must be inside the run')
    plan, story = read(plan_path), read(story_path)
    mode = read(root / 'run.json')['mode']
    if mode not in MODES or plan.get('mode') != mode or story.get('mode') != mode:
        raise ValueError('run, plan and story modes must agree')
    errors = evidence_errors(root, mode) + validate_plan(plan, story)
    timeline_path = root / 'manifests/timeline.json'
    for script, target in [('validate_story.py', story_path), ('validate_timeline.py', timeline_path)]:
        result = subprocess.run([sys.executable, str(Path(__file__).parent / script), str(target)], capture_output=True, text=True)
        if result.returncode:
            errors.append(script + ': ' + result.stdout + result.stderr)
    timeline = read(timeline_path)
    if timeline.get('mode') != mode:
        errors.append('timeline mode differs from run')
    by_id = {c['id']: c for c in timeline.get('containers', [])}
    if list(by_id) != [j['id'] for j in plan['jobs']]:
        errors.append('timeline and execution plan container order/IDs differ')
    for index, j in enumerate(plan['jobs']):
        c = by_id.get(j['id'], {})
        if c.get('provider_duration') != j['generated_seconds'] or c.get('retain_duration') != j['retain_seconds']:
            errors.append('plan durations differ from editorial container ' + j['id'])
        if j.get('model') == 'omni_flash-10s-fl':
            prior = plan['jobs'][index - 1] if index else {}
            if not index or j.get('continuation_of') != prior.get('asset_id', prior.get('id')):
                errors.append('continuation must name the immediately preceding planned container asset')
            if prior.get('retain_seconds') != prior.get('generated_seconds'):
                errors.append('true-last-frame continuation cannot follow a trimmed parent; use an independent scene or revise the endpoint plan')
    if mode != 'recreation':
        brief = read(root / 'evidence/product/product_brief.json')
        protected = brief.get('video_feasibility_plan', {}).get('protect_product_configuration')
        if protected and any(j.get('protect_configuration') is not True for j in plan['jobs']):
            errors.append('job cannot lower the source-backed configuration protection')
        claims = {c['id']: c for c in read(root / 'analysis/claim-ledger.json')['claims']}
        for beat in story['beats']:
            for cid in beat.get('claim_ids', []):
                claim = claims.get(cid, {})
                if claim.get('status') != 'supported' and not (claim.get('status') == 'seller_claim' and claim.get('approved_wording')):
                    errors.append('beat uses unresolved or unqualified claim: ' + cid)
        if not any(b.get('claim_ids') for b in story['beats']):
            errors.append('product story must map its selling points to claim IDs')
    if mode == 'hybrid' and not story.get('adaptation_map'):
        errors.append('hybrid requires an explicit source-to-product adaptation map')
    if errors:
        raise ValueError('; '.join(errors))
    job = next(j for j in plan['jobs'] if j['id'] == job_id)
    check_boundary(root, job)
    request = compile_job(job, story)
    from updrama_runtime import validate
    if validate(request):
        raise ValueError('; '.join(validate(request)))
    deps = [plan_path, story_path, timeline_path, root / 'run.json']
    deps += [p for p in (root / 'analysis').glob('*.json') if p.name != 'prompt-history.json']
    deps += list((root / 'evidence/product').rglob('*.json')) if mode != 'recreation' else []
    return request, {'job_id': job_id, 'mode': mode,
        'dependencies': {str(p.relative_to(root)): fingerprint(p) for p in deps},
        'request_sha256': hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir', required=True); p.add_argument('--plan', required=True)
    p.add_argument('--job', required=True); p.add_argument('--output', required=True)
    a = p.parse_args()
    request, proof = build(a.run_dir, a.plan, a.job)
    path = Path(a.output)
    proof_path = path.with_suffix('.compile.json')
    if path.exists() or proof_path.exists():
        raise ValueError('use a new request version')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + '\n')
    proof_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'compiled', 'request': str(path), 'characters': len(request['prompt'])}))


if __name__ == '__main__':
    main()
