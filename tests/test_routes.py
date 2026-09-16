"""Offline synthetic contracts, not evidence of real media/model quality."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch
import argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from routes import route, evidence_errors, required_qa
from compile_prompt import build, compile_job, check_boundary
import updrama_runtime as rt
import workflow as wf
from validate_plan import validate


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def fixture(root, mode):
    write(root / 'run.json', {'schema_version': '3.0.0', 'mode': mode, 'aspect_ratio': '9:16'})
    write(root / 'analysis/source-evidence.json', {'coverage': {'full_duration_reviewed': True}, 'observations': ['synthetic observation'], 'audio_review': 'synthetic silent fixture'})
    product = root / 'evidence/product'
    (product / 'images').mkdir(parents=True)
    (product / 'images/item.png').write_bytes(b'synthetic image fixture')
    write(product / 'product_manifest.json', {'extraction_audit': {'complete': True}, 'images': [{'local_path': 'images/item.png'}]})
    write(product / 'image_analysis.json', {'images': [{'local_path': 'images/item.png', 'analysis': {'observation': 'synthetic'}}]})
    brief = {k: ['synthetic'] for k in ['confirmed_identity', 'confirmed_selling_points', 'confirmed_use_cases', 'misuse_risks_to_avoid']}
    brief.update(state_change_contract={'required': False}, video_feasibility_plan={'protect_product_configuration': True})
    write(product / 'product_brief.json', brief)
    write(root / 'analysis/claim-ledger.json', {'claims': [{'id': 'K01', 'wording': 'shade', 'status': 'supported', 'evidence': ['synthetic source']}]})
    story = {'mode': mode, 'hook': {'beat_ids': ['B01']}, 'fidelity_boundary': 'synthetic',
        'beats': [{'id': 'B01', 'visible_action': 'ready product', 'must_preserve': ['SKU'], 'initial_condition': True, 'terminal': True, 'claim_ids': ['K01']}],
        'prop_tracks': [{'prop': 'product', 'states': ['ready'], 'configuration_lock': True}]}
    if mode == 'hybrid': story['adaptation_map'] = [{'source_beat': 'B01', 'target_beat': 'B01', 'reason': 'synthetic adaptation'}]
    write(root / 'analysis/story-truth.json', story)
    refs = [{'id': 'SB01', 'role': 'storyboard', 'controls': 'scene sequence', 'must_not_control': 'product shape'},
        {'id': 'P01', 'role': 'product_identity', 'controls': 'SKU shape', 'must_not_control': 'background'}]
    job = {'id': 'C01', 'model': 'omni_flash-10s', 'purpose': 'establish scene', 'generated_seconds': 10, 'retain_seconds': 10,
        'references': refs, 'actions': [{'local_range': [0, 9], 'beat_ids': ['B01'], 'instruction': 'Show verified ready product.'}],
        'audio': {'policy': 'post_voiceover'}, 'protect_configuration': True}
    plan = {'schema_version': 3, 'mode': mode, 'story_file': '../analysis/story-truth.json', 'jobs': [job]}
    write(root / 'manifests/execution-plan.json', plan)
    shot = {'id': 'S01', 'editorial_range': [0, 10]}
    if mode != 'product_video':
        shot['source_range'] = [0, 10]
    timeline = {'mode': mode, 'editorial_duration': 10, 'source_duration': 10, 'provider_clip_seconds': 10,
        'editorial_shots': [shot], 'containers': [{'id': 'C01', 'editorial_range': [0, 10], 'provider_duration': 10, 'retain_duration': 10,
        'shot_segments': [{'shot_id': 'S01', 'editorial_range': [0, 10]}]}]}
    write(root / 'manifests/timeline.json', timeline)
    return plan, story


class Routes(unittest.TestCase):
    def test_hybrid_precedes_individual_routes(self):
        self.assertEqual(route('source.mp4', 'https://example.com/product'), 'hybrid')
        self.assertEqual(route('source.mp4'), 'recreation')
        self.assertEqual(route(None, 'https://example.com/product'), 'product_video')
        with self.assertRaises(ValueError): route()
        with self.assertRaises(ValueError): route('https://example.com/video')

    def test_product_initialization_never_probes_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'run'
            p = subprocess.run([sys.executable, str(ROOT / 'scripts/init_run.py'), 'https://example.com/product', '--duration', '30', '--out', str(out)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertFalse((out / 'source.json').exists())
            self.assertFalse((out / 'analysis/source-evidence.json').exists())
            self.assertFalse(json.loads((out / 'run.json').read_text())['use_watch'])

    def test_all_three_routes_compile_to_provider_schema(self):
        for mode in ['recreation', 'product_video', 'hybrid']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); fixture(root, mode)
                request, proof = build(root, root / 'manifests/execution-plan.json', 'C01')
                self.assertFalse(rt.validate(request))
                self.assertEqual(set(request), {'model', 'prompt', 'params'})
                self.assertEqual(proof['mode'], mode)
                self.assertIn('Image 2 (product_identity)', request['prompt'])
                self.assertNotIn('touchscreen', request['prompt'])

    def test_missing_analysis_and_unresolved_claim_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); fixture(root, 'product_video')
            write(root / 'analysis/claim-ledger.json', {'claims': [{'id': 'K01', 'status': 'unresolved', 'evidence': ['conflict']}]})
            with self.assertRaisesRegex(ValueError, 'unresolved'):
                build(root, root / 'manifests/execution-plan.json', 'C01')
            write(root / 'evidence/product/image_analysis.json', {'images': []})
            self.assertTrue(evidence_errors(root, 'product_video'))

    def test_supporting_detail_does_not_need_invented_cause(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); plan, story = fixture(root, 'product_video')
            story['beats'].append({'id': 'B02', 'kind': 'detail', 'visible_action': 'fabric close-up', 'must_preserve': ['fabric'], 'supports': ['B01'], 'editorial_purpose': 'show texture'})
            plan['jobs'][0]['actions'][0]['beat_ids'].append('B02')
            write(root / 'analysis/story-truth.json', story)
            write(root / 'manifests/execution-plan.json', plan)
            build(root, root / 'manifests/execution-plan.json', 'C01')

    def test_short_independent_container_and_first_last_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan, story = fixture(Path(tmp), 'product_video')
            j = plan['jobs'][0]; j.update(model='omni-flash', generated_seconds=6, retain_seconds=6)
            j['actions'][0]['local_range'] = [0, 5]
            self.assertFalse(validate(plan, story))
            self.assertFalse(rt.validate(compile_job(j, story)))
            j.update(model='omni_flash-10s-fl', generated_seconds=10, retain_seconds=10, continuation_of='C00')
            with self.assertRaises(ValueError): compile_job(j, story)
            j['references'][0]['role'] = 'boundary_frame'; j['references'][1]['role'] = 'target_end_frame'
            prompt = compile_job(j, story)['prompt']
            self.assertIn('Image 2 (target_end_frame)', prompt)
            self.assertNotIn('Image 2 (product_identity)', prompt)
            j['actions'][0]['instruction'] = 'x' * 4100
            with self.assertRaisesRegex(ValueError, 'never truncate'): compile_job(j, story)

    def test_all_omni_models_require_lock_at_submit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); image = root / 'raw.png'; image.write_bytes(b'fixture')
            wf.register(root, 'RAW', image, 'source', 'raw', [])
            for model in rt.VIDEO_MODELS:
                params = {'images': ['artifact://RAW'], 'aspect_ratio': '9:16'}
                if model == 'omni-flash': params['duration'] = '4'
                request = root / 'req.json'; write(request, {'model': model, 'prompt': 'synthetic', 'params': params})
                args = argparse.Namespace(request=str(request), run_dir=str(root), job_id='job', confirm_paid='I_UNDERSTAND_THIS_IS_PAID', timeout=1)
                with patch.object(rt, 'call') as call:
                    with self.assertRaises(ValueError): rt.submit(args)
                    call.assert_not_called()

    def test_tt_schema_and_variable_omni_reject_bad_requests(self):
        image = {'model': 'tt-image-2.5', 'prompt': 'x', 'params': {'images': ['artifact://P'], 'aspect_ratio': '9:16', 'resolution': '2K'}}
        self.assertFalse(rt.validate(image))
        image['params']['images'] *= 17
        self.assertTrue(rt.validate(image))
        video = {'model': 'omni-flash', 'prompt': 'x', 'params': {'images': ['artifact://P'], 'aspect_ratio': '9:16', 'duration': '7'}}
        self.assertTrue(rt.validate(video))
        video['params']['duration'] = '6'; video['prompt'] = 'x' * 4001
        self.assertTrue(rt.validate(video))

    def test_route_qa_unknown_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); fixture(root, 'product_video')
            image = root / 'x.png'; image.write_bytes(b'fixture')
            wf.register(root, 'X', image, 'reference', 'identity', [])
            checks = {k: {'status': 'pass', 'evidence': 'synthetic'} for k in required_qa('product_video', 'reference')}
            report = {'asset_sha256': wf.sha(image), 'reviewer': 'test', 'technical_pass': True, 'decision': 'accepted', 'observations': ['synthetic'], 'checks': checks}
            path = root / 'qa.json'; write(path, report); wf.record_qa(root, 'X', path)
            checks['product_fidelity']['status'] = 'unknown'; write(path, report)
            with self.assertRaises(ValueError): wf.record_qa(root, 'X', path)

    def test_timeline_plan_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); plan, _ = fixture(root, 'product_video')
            plan['jobs'][0]['retain_seconds'] = 9
            write(root / 'manifests/execution-plan.json', plan)
            with self.assertRaisesRegex(ValueError, 'durations differ'):
                build(root, root / 'manifests/execution-plan.json', 'C01')

    def test_three_routes_thirty_second_editorial_coverage(self):
        for mode in ['recreation', 'product_video', 'hybrid']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); plan, story = fixture(root, mode)
                timeline = json.loads((root / 'manifests/timeline.json').read_text())
                timeline.update(editorial_duration=30, source_duration=30, editorial_shots=[], containers=[])
                original = copy.deepcopy(plan['jobs'][0]); plan['jobs'] = []
                for i in range(3):
                    job = copy.deepcopy(original); job['id'] = f'C{i+1:02d}'
                    bid, sid = f'B{i+1:02d}', f'S{i+1:02d}'
                    job['actions'][0]['beat_ids'] = [bid]; plan['jobs'].append(job)
                    if i:
                        story['beats'].append({'id': bid, 'kind': 'detail', 'visible_action': 'source-backed detail', 'must_preserve': ['SKU'], 'supports': ['B01'], 'editorial_purpose': 'support the film claim'})
                    span = [i*10, (i+1)*10]
                    shot = {'id': sid, 'editorial_range': span}
                    if mode != 'product_video': shot['source_range'] = span
                    timeline['editorial_shots'].append(shot)
                    timeline['containers'].append({'id': job['id'], 'editorial_range': span, 'provider_duration': 10, 'retain_duration': 10, 'shot_segments': [{'shot_id': sid, 'editorial_range': span}]})
                write(root / 'analysis/story-truth.json', story)
                write(root / 'manifests/timeline.json', timeline)
                write(root / 'manifests/execution-plan.json', plan)
                for job in plan['jobs']:
                    request, _ = build(root, root / 'manifests/execution-plan.json', job['id'])
                    self.assertFalse(rt.validate(request))

    def test_boundary_requires_l2_parent_and_true_frame_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); raw = root / 'raw.mp4'; raw.write_bytes(b'raw fixture')
            boundary = root / 'boundary.png'; boundary.write_bytes(b'frame fixture')
            wf.register(root, 'C00', raw, 'container', 'previous', [])
            wf.register(root, 'BND', boundary, 'reference', 'actual last frame', ['C00'])
            job = {'model': 'omni_flash-10s-fl', 'continuation_of': 'C00', 'references': [{'id': 'BND'}]}
            with self.assertRaisesRegex(ValueError, 'L2'): check_boundary(root, job)
            qa = {'asset_sha256': wf.sha(raw), 'reviewer': 'test', 'technical_pass': True, 'decision': 'accepted_with_warnings', 'observations': ['synthetic']}
            write(root / 'qa.json', qa); wf.record_qa(root, 'C00', root / 'qa.json')
            with self.assertRaisesRegex(ValueError, 'true last'): check_boundary(root, job)
            qa.update(asset_sha256=wf.sha(boundary), decision='accepted', boundary_of='C00', true_last_frame_verified=True)
            write(root / 'qa.json', qa); wf.record_qa(root, 'BND', root / 'qa.json')
            with self.assertRaisesRegex(ValueError, 'warning review'): check_boundary(root, job)
            qa['continuation_warning_review'] = 'Reviewed warning does not affect boundary state (synthetic)'
            write(root / 'qa.json', qa); wf.record_qa(root, 'BND', root / 'qa.json')
            check_boundary(root, job)

    def test_current_review_compile_hash_and_locks_before_paid_post(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); fixture(root, 'product_video')
            request, proof = build(root, root / 'manifests/execution-plan.json', 'C01')
            path = root / 'requests/C01.json'; write(path, request); write(path.with_suffix('.compile.json'), proof)
            args = argparse.Namespace(request=str(path), run_dir=str(root), job_id='C01-v1', confirm_paid='I_UNDERSTAND_THIS_IS_PAID', timeout=1)
            write(root / 'provider/001/omni_flash-10s.json', {'synthetic': True})
            write(root / 'provider/contract-review.json', {'reviewer': 'test', 'reviewed_at': 'synthetic', 'models': ['omni_flash-10s'], 'snapshots': {'provider/001/omni_flash-10s.json': wf.sha(root / 'provider/001/omni_flash-10s.json')}})
            for aid in ['SB01', 'P01']:
                image = root / f'{aid}.png'; image.write_bytes(b'synthetic')
                wf.register(root, aid, image, 'reference', 'synthetic role', [])
                qa = {'asset_sha256': wf.sha(image), 'reviewer': 'test', 'technical_pass': True, 'decision': 'accepted', 'observations': ['synthetic'], 'checks': {k: {'status': 'pass', 'evidence': 'synthetic'} for k in required_qa('product_video', 'reference')}}
                write(root / f'{aid}.qa.json', qa); wf.record_qa(root, aid, root / f'{aid}.qa.json')
            wf.lock(root, ['SB01', 'P01'], 'synthetic test, not real user consent')
            with patch.object(rt, 'call', return_value={'code': 200, 'data': {'task_id': 123}}) as call, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(rt.submit(args), 0)
                self.assertEqual(rt.submit(args), 0)
                self.assertEqual(call.call_count, 1)
                story = json.loads((root / 'analysis/story-truth.json').read_text()); story['hook'] = 'changed'
                write(root / 'analysis/story-truth.json', story)
                with self.assertRaisesRegex(ValueError, 'stale'): rt.submit(args)
                self.assertEqual(call.call_count, 1)

    def test_reject_unrelated_continuation_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); plan, story = fixture(root, 'product_video')
            job = plan['jobs'][0]
            job.update(model='omni_flash-10s-fl', continuation_of='UNRELATED')
            job['references'][0]['role'] = 'boundary_frame'
            job['references'][1]['role'] = 'target_end_frame'
            write(root / 'manifests/execution-plan.json', plan)
            with self.assertRaisesRegex(ValueError, 'immediately preceding'):
                build(root, root / 'manifests/execution-plan.json', 'C01')

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_v3_three_route_initialization_and_registered_assembly(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); source = folder / 'synthetic.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=96x160:r=24:d=10', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(source)], check=True)
            for mode in ['recreation', 'product_video', 'hybrid']:
                root = folder / mode
                args = [str(source)] if mode != 'product_video' else []
                if mode != 'recreation': args += ['--product-url', 'https://example.com/product', '--duration', '10']
                p = subprocess.run([sys.executable, str(ROOT / 'scripts/init_run.py'), *args, '--out', str(root)], capture_output=True, text=True)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(json.loads((root / 'run.json').read_text())['mode'], mode)
                fixture(root, mode)
                raw = root / 'raw.mp4'; shutil.copyfile(source, raw)
                wf.register(root, 'C01', raw, 'container', 'synthetic test only', [])
                qa = {'asset_sha256': wf.sha(raw), 'reviewer': 'test', 'technical_pass': True, 'decision': 'accepted', 'observations': ['synthetic fixture; never deliver'], 'checks': {k: {'status': 'pass', 'evidence': 'synthetic fixture'} for k in required_qa(mode, 'container')}}
                write(root / 'qa.json', qa); wf.record_qa(root, 'C01', root / 'qa.json')
                manifest = {'schema_version': 3, 'run_dir': '.', 'output': 'master.mp4', 'size': [96, 160], 'fps': 24, 'audio_policy': 'silent', 'containers': [{'id': 'C01', 'file': 'raw.mp4', 'sha256': wf.sha(raw), 'qa_decision': 'accepted', 'retain_seconds': 10}]}
                write(root / 'assembly.json', manifest)
                cmd = [sys.executable, str(ROOT / 'scripts/assemble.py'), str(root / 'assembly.json')]
                p = subprocess.run(cmd, capture_output=True, text=True)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(sum(json.loads((root / 'master.assembly.json').read_text())['frame_budgets']), 240)
                manifest['output'] = 'wrong.mp4'; manifest['containers'][0]['retain_seconds'] = 9
                write(root / 'assembly.json', manifest)
                p = subprocess.run(cmd, capture_output=True, text=True)
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('order/trim', p.stderr)


if __name__ == '__main__':
    unittest.main()
