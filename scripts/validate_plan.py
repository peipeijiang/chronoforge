#!/usr/bin/env python3
"""Check beat coverage and ordered reference roles, not visual truth."""
import argparse
import json
import math
import pathlib


def validate(plan, story):
    errors = []
    required = {b['id'] for b in story['beats'] if b.get('must_preserve')}
    covered = set()
    jobs = plan.get('jobs', [])
    ids = [j['id'] for j in jobs]
    if not jobs or len(ids) != len(set(ids)):
        errors.append('jobs must have unique IDs and be nonempty')
    for job in jobs:
        label = job['id']
        refs = job.get('references', [])
        if not 1 <= len(refs) <= 7 or any(not r.get('role') or not r.get('id') for r in refs):
            errors.append(label + ': need 1-7 ordered role-labelled references')
        keep = float(job['retain_seconds'])
        generated = float(job['generated_seconds'])
        if not math.isfinite(keep) or not 0 < keep <= generated or generated != 10:
            errors.append(label + ': invalid Omni duration/trim')
        cursor = 0.0
        for action in job.get('actions', []):
            start, end = map(float, action['local_range'])
            if not all(map(math.isfinite, (start, end))) or not 0 <= start < end <= keep or start < cursor:
                errors.append(label + ': action out of order or outside retained range')
            cursor = end
            if not action.get('instruction') or not action.get('beat_ids'):
                errors.append(label + ': action needs instruction and beat IDs')
            for bid in action.get('beat_ids', []):
                if bid not in required:
                    errors.append(label + ': unknown/unrequired beat ' + bid)
                covered.add(bid)
        if job.get('qa'):
            qa = job['qa']
            if qa.get('decision') not in ('accepted', 'accepted_with_warnings'):
                errors.append(label + ': QA not accepted')
            observations = qa.get('observations', [])
            observed = {o.get('beat_id') for o in observations if o.get('verdict') == 'pass'
                        and o.get('evidence') and isinstance(o.get('time'), (int, float))
                        and 0 <= o['time'] < keep}
            expected = {b for a in job['actions'] for b in a['beat_ids']}
            if expected - observed:
                errors.append(label + ': missing timestamped QA for ' + ','.join(sorted(expected - observed)))
    if required - covered:
        errors.append('uncovered source beats: ' + ','.join(sorted(required - covered)))
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan'); p.add_argument('--require-qa', action='store_true')
    p.add_argument('--qa-dir', help='separate JOB_ID.json reports; never mutate a frozen plan to attach QA')
    a = p.parse_args()
    path = pathlib.Path(a.plan)
    plan = json.loads(path.read_text())
    if a.qa_dir:
        for job in plan['jobs']:
            name = job['id']
            if pathlib.Path(name).name != name:
                raise ValueError('job IDs used as QA filenames must be plain names')
            report = pathlib.Path(a.qa_dir) / (name + '.json')
            job['qa'] = json.loads(report.read_text()) if report.exists() else None
    story = json.loads((path.parent / plan['story_file']).read_text())
    errors = validate(plan, story)
    if a.require_qa and any(not j.get('qa') for j in plan['jobs']):
        errors.append('every job needs reviewed L2 QA')
    print(json.dumps({'status': 'fail' if errors else 'pass', 'errors': errors}))
    return 2 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
