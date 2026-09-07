#!/usr/bin/env python3
"""Local artifact provenance and reference gate; never calls a provider.

QA decisions are supplied by a reviewer, not inferred from file existence.
Keep each run under one creative writer; paid creates have their own lock.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import mimetypes
import pathlib
import datetime as dt


def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(pathlib.Path(path).read_text())


def write(path, data):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


def registry(root):
    path = pathlib.Path(root) / 'manifests/artifacts.json'
    return read(path) if path.exists() else {'schema_version': 2, 'assets': {}, 'locks': []}


def current(root, data, aid, trail=()):
    if aid in trail:
        raise ValueError('dependency cycle: ' + aid)
    asset = data['assets'][aid]
    if asset['status'] in ('stale', 'rejected'):
        raise ValueError('unusable asset: ' + aid)
    if sha(pathlib.Path(root) / asset['file']) != asset['sha256']:
        raise ValueError('changed bytes: ' + aid)
    for dep, expected in asset.get('dependencies', {}).items():
        parent = current(root, data, dep, trail + (aid,))
        if parent['sha256'] != expected:
            raise ValueError('changed dependency: ' + dep)
    return asset


def register(root, aid, file, kind, role, dependencies):
    root = pathlib.Path(root).resolve()
    data = registry(root)
    if aid in data['assets']:
        raise ValueError('use a new versioned asset ID; never overwrite: ' + aid)
    path = pathlib.Path(file).resolve()
    # Files stay within their run so a portable registry cannot read arbitrary paths.
    relative = str(path.relative_to(root))
    parents = {x: current(root, data, x)['sha256'] for x in dependencies}
    data['assets'][aid] = {'file': relative, 'kind': kind, 'role': role,
        'sha256': sha(path), 'status': 'pending', 'dependencies': parents}
    write(root / 'manifests/artifacts.json', data)


def record_qa(root, aid, report_file):
    data = registry(root)
    asset = current(root, data, aid)
    report = read(report_file)
    if report.get('asset_sha256') != asset['sha256']:
        raise ValueError('QA is not bound to current asset bytes')
    if report.get('decision') not in ('accepted', 'accepted_with_warnings', 'rejected'):
        raise ValueError('explicit reviewer decision required')
    if not report.get('reviewer') or not report.get('observations'):
        raise ValueError('reviewer and actual observations required')
    if report['decision'].startswith('accepted') and report.get('technical_pass') is not True:
        raise ValueError('technical pass required, separately from semantic decision')
    asset['qa'] = report
    asset['status'] = 'rejected' if report['decision'] == 'rejected' else 'accepted'
    write(pathlib.Path(root) / 'manifests/artifacts.json', data)


def lock(root, ids, approval):
    if not approval.strip() or not ids or len(set(ids)) != len(ids):
        raise ValueError('unique assets and actual human approval record required')
    data = registry(root)
    hashes = {}
    for aid in ids:
        asset = current(root, data, aid)
        if asset['kind'] != 'reference' or asset['status'] != 'accepted' or not asset['role']:
            raise ValueError('only L1-accepted role-labelled references may be locked: ' + aid)
        hashes[aid] = asset['sha256']
    data['locks'].append({'assets': hashes, 'approval': approval,
        'recorded_at': dt.datetime.now(dt.timezone.utc).isoformat()})
    write(pathlib.Path(root) / 'manifests/artifacts.json', data)


def resolve(request, root, require_lock=False):
    data = registry(root)
    result = copy.deepcopy(request)
    images = result['params']['images']
    locked = data['locks'][-1]['assets'] if data['locks'] else {}
    for i, image in enumerate(images):
        if not image.startswith('artifact://'):
            raise ValueError('ready submission requires registered artifact:// IDs')
        aid = image[len('artifact://'):]
        asset = current(root, data, aid)
        if require_lock and (asset['kind'] != 'reference' or asset['status'] != 'accepted'
                             or locked.get(aid) != asset['sha256']):
            raise ValueError('reference is not in the current human lock: ' + aid)
        if not require_lock and asset['kind'] not in ('source', 'reference'):
            raise ValueError('Image2 input must be source evidence or a reference')
        if not require_lock and asset['kind'] == 'reference' and asset['status'] != 'accepted':
            raise ValueError('review a generated reference before using it for another image: ' + aid)
        path = pathlib.Path(root) / asset['file']
        mime = mimetypes.guess_type(path.name)[0]
        if mime not in ('image/png', 'image/jpeg', 'image/webp'):
            raise ValueError('unsupported reference image type')
        images[i] = 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode()
    return result


def invalidate(root, aid, reason):
    data = registry(root)
    if aid not in data['assets'] or not reason.strip():
        raise ValueError('known asset and reason required')
    affected = {aid}
    while True:
        extra = {key for key, a in data['assets'].items()
                 if set(a.get('dependencies', {})) & affected} - affected
        if not extra:
            break
        affected |= extra
    for key in affected:
        data['assets'][key]['status'] = 'stale'
        data['assets'][key]['invalidation_reason'] = reason
    write(pathlib.Path(root) / 'manifests/artifacts.json', data)
    return sorted(affected)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir', required=True)
    sub = p.add_subparsers(dest='command', required=True)
    x = sub.add_parser('register'); x.add_argument('id'); x.add_argument('file')
    x.add_argument('--kind', choices=['source', 'reference', 'container', 'master', 'contract'], required=True)
    x.add_argument('--role', required=True); x.add_argument('--depends-on', nargs='*', default=[])
    x = sub.add_parser('qa'); x.add_argument('id'); x.add_argument('report')
    x = sub.add_parser('lock'); x.add_argument('ids', nargs='+'); x.add_argument('--approval', required=True)
    x = sub.add_parser('invalidate'); x.add_argument('id'); x.add_argument('--reason', required=True)
    x = sub.add_parser('check'); x.add_argument('ids', nargs='+')
    a = p.parse_args()
    if a.command == 'register': register(a.run_dir, a.id, a.file, a.kind, a.role, a.depends_on)
    elif a.command == 'qa': record_qa(a.run_dir, a.id, a.report)
    elif a.command == 'lock': lock(a.run_dir, a.ids, a.approval)
    elif a.command == 'invalidate': print(json.dumps(invalidate(a.run_dir, a.id, a.reason)))
    else:
        data = registry(a.run_dir)
        for aid in a.ids: current(a.run_dir, data, aid)
    print(json.dumps({'status': 'pass', 'operation': a.command}))


if __name__ == '__main__':
    main()
