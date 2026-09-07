from __future__ import annotations
import argparse
import contextlib
import copy
import io
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import workflow as wf
import updrama_runtime as runtime
from assemble import frame_budgets
from validate_plan import validate as validate_plan


class RunFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.image = self.root / 'source.png'
        self.image.write_bytes(b'fixture image bytes; no real media claim')
        wf.register(self.root, 'E01', self.image, 'source', 'source', [])
        self.request = {'model': 'gpt-image-2', 'prompt': 'reference only',
                        'params': {'images': ['artifact://E01'], 'size': '1088x1920', 'quality': 'high'}}
        self.request_path = self.root / 'request.json'
        wf.write(self.request_path, self.request)
        self.args = argparse.Namespace(request=str(self.request_path), run_dir=str(self.root),
            job_id='G01-v1', confirm_paid='I_UNDERSTAND_THIS_IS_PAID', timeout=1)

    def tearDown(self):
        self.temp.cleanup()

    def submit(self, args=None):
        with contextlib.redirect_stdout(io.StringIO()):
            return runtime.submit(args or self.args)

    def reference(self):
        wf.register(self.root, 'G01', self.image, 'reference', 'identity only', ['E01'])
        report = self.root / 'qa.json'
        wf.write(report, {'asset_sha256': wf.sha(self.image), 'reviewer': 'test-fixture',
            'technical_pass': True, 'decision': 'accepted', 'observations': ['synthetic fixture only']})
        wf.record_qa(self.root, 'G01', report)
        return {'model': 'omni_flash-10s', 'prompt': 'test',
                'params': {'images': ['artifact://G01'], 'aspect_ratio': '9:16'}}

    def test_image_creation_does_not_require_reference_lock(self):
        with patch.object(runtime, 'call', return_value={'code': 200, 'data': {'task_id': 123}}):
            self.assertEqual(self.submit(), 0)

    def test_repeated_known_job_never_posts_twice(self):
        with patch.object(runtime, 'call', return_value={'code': 200, 'data': {'task_id': 123}}) as call:
            self.submit(); self.submit()
            self.assertEqual(call.call_count, 1)
        # Persistence also works with only the on-disk ledger, not process state.
        self.assertEqual(runtime.ledger(self.root)[-1]['task_id'], '123')

    def test_modified_request_cannot_reuse_operator_id(self):
        with patch.object(runtime, 'call', return_value={'code': 200, 'data': {'task_id': 123}}) as call:
            self.submit()
            self.request['prompt'] = 'different'; wf.write(self.request_path, self.request)
            with self.assertRaises(ValueError): self.submit()
            self.assertEqual(call.call_count, 1)

    def test_ambiguous_submission_blocks_new_job_in_lane(self):
        for failure in (TimeoutError(), json.JSONDecodeError('bad', 'x', 0)):
            with self.subTest(type=type(failure).__name__):
                # A new root is not used to bypass a live task; this is an isolated mock fixture.
                (self.root / 'media-jobs.jsonl').unlink(missing_ok=True)
                with patch.object(runtime, 'call', side_effect=failure) as call:
                    self.assertEqual(self.submit(), 3)
                    other = copy.copy(self.args); other.job_id = 'G02-v1'
                    with self.assertRaises(RuntimeError): self.submit(other)
                    self.assertEqual(call.call_count, 1)

    def test_crash_after_intent_blocks_lane(self):
        runtime.append(self.root, {'record_type': 'submit_intent', 'job_id': 'interrupted',
                                  'model': 'gpt-image-2'})
        with patch.object(runtime, 'call') as call:
            with self.assertRaises(RuntimeError): self.submit()
            call.assert_not_called()

    def test_wrong_create_envelope_is_not_retryable(self):
        with patch.object(runtime, 'call', return_value={'id': 'other-api-profile'}) as call:
            with self.assertRaises(RuntimeError): self.submit()
            with self.assertRaises(RuntimeError): self.submit()
            self.assertEqual(call.call_count, 1)

    def test_video_lock_and_reference_hash_enforced(self):
        request = self.reference()
        with self.assertRaises(ValueError): wf.resolve(request, self.root, True)
        wf.lock(self.root, ['G01'], 'synthetic test approval, not real consent')
        self.assertTrue(wf.resolve(request, self.root, True)['params']['images'][0].startswith('data:image/'))
        self.image.write_bytes(b'changed')
        with self.assertRaises(ValueError): wf.resolve(request, self.root, True)

    def test_source_frame_cannot_be_locked_as_generated_reference(self):
        with self.assertRaises(ValueError): wf.lock(self.root, ['E01'], 'test')

    def test_invalidation_propagates_and_preserves_files(self):
        self.reference()
        video = self.root / 'raw.mp4'; video.write_bytes(b'raw')
        master = self.root / 'master.mp4'; master.write_bytes(b'master')
        wf.register(self.root, 'C01', video, 'container', 'scene', ['G01'])
        wf.register(self.root, 'M01', master, 'master', 'delivery', ['C01'])
        self.assertEqual(wf.invalidate(self.root, 'E01', 'changed interpretation'), ['C01', 'E01', 'G01', 'M01'])
        self.assertTrue(master.exists())
        with self.assertRaises(ValueError): wf.current(self.root, wf.registry(self.root), 'M01')

    def test_qa_for_other_bytes_rejected(self):
        report = self.root / 'qa.json'; wf.write(report, {'asset_sha256': 'wrong'})
        with self.assertRaises(ValueError): wf.record_qa(self.root, 'E01', report)

    def test_status_requires_consistent_lowercase_terminal_fields(self):
        args = argparse.Namespace(run_dir=str(self.root), task_id='123')
        for value in ({'state': 'SUCCESS', 'is_final': True},
                      {'state': 'success', 'is_final': False},
                      {'state': 'success', 'is_final': True, 'result_url': ''}):
            with patch.object(runtime, 'call', return_value=value):
                with self.assertRaises(RuntimeError): runtime.status(args)

    def test_preflight_does_not_pass_error_response(self):
        with patch.object(runtime, 'call', return_value={'code': 401, 'error': 'unauthorized'}):
            with self.assertRaises(RuntimeError): runtime.preflight(self.args)

    def test_collect_original_bytes_without_cdn_credentials(self):
        args = argparse.Namespace(run_dir=str(self.root), task_id='123',
                                  output=str(self.root / 'raw.mp4'), wait_seconds=0)
        response = {'state': 'success', 'is_final': True, 'result_url': 'https://example.com/output.mp4'}
        with patch.object(runtime, 'call', return_value=response), \
             patch.object(runtime.urllib.request, 'urlopen', return_value=io.BytesIO(b'original-result')) as get, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runtime.collect(args), 0)
            self.assertEqual(get.call_args.args, ('https://example.com/output.mp4',))
        self.assertEqual((self.root / 'raw.mp4').read_bytes(), b'original-result')
        row = runtime.ledger(self.root)[-1]
        self.assertEqual(row['sha256'], wf.sha(self.root / 'raw.mp4'))
        self.assertEqual(row['qa'], 'pending')
        with self.assertRaises(ValueError): runtime.collect(args)

    def test_collect_pending_yields_without_paid_post(self):
        args = argparse.Namespace(run_dir=str(self.root), task_id='123',
                                  output=str(self.root / 'raw.mp4'), wait_seconds=0)
        with patch.object(runtime, 'call', return_value={'state': 'running', 'is_final': False}) as call, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runtime.collect(args), 5)
            self.assertEqual(call.call_args.args[0], 'GET')
        self.assertFalse((self.root / 'raw.mp4').exists())

    def test_reconcile_known_task_preserves_original_provenance(self):
        runtime.append(self.root, {'record_type': 'submit_intent', 'job_id': 'unknown', 'model': 'gpt-image-2'})
        args = argparse.Namespace(run_dir=str(self.root), job_id='unknown', task_id='123', evidence='synthetic support evidence')
        self.assertEqual(runtime.reconcile(args), 0)
        args.task_id = '456'
        with self.assertRaises(ValueError): runtime.reconcile(args)


class PlanTests(unittest.TestCase):
    def setUp(self):
        case = ROOT / 'assets/cat-coffee-v3'
        self.story = wf.read(case / 'story-truth.json')
        self.plan = wf.read(case / 'execution-plan.json')

    def test_case_beat_coverage(self):
        self.assertEqual(validate_plan(self.plan, self.story), [])

    def test_missing_cause_beat_fails(self):
        self.plan['jobs'][0]['actions'].pop(0)
        self.assertTrue(any('B01' in x for x in validate_plan(self.plan, self.story)))

    def test_action_after_trim_fails(self):
        self.plan['jobs'][3]['actions'][-1]['local_range'][1] = 9
        self.assertTrue(validate_plan(self.plan, self.story))

    def test_nominal_qa_without_observations_fails(self):
        self.plan['jobs'][0]['qa'] = {'decision': 'accepted', 'observations': []}
        self.assertTrue(validate_plan(self.plan, self.story))

    def test_actual_prompts_match_plan_reference_order(self):
        for job in self.plan['jobs']:
            request = wf.read(ROOT / 'assets/cat-coffee-v3' / (job['id'] + '.json'))
            self.assertEqual(request['params']['images'], ['artifact://' + r['id'] for r in job['references']])
            self.assertEqual(runtime.validate(request), [])

    def test_cumulative_frame_rounding(self):
        self.assertEqual(frame_budgets([10, 7, 10, 6.111723], 60), [600, 420, 600, 367])
        self.assertEqual(sum(frame_budgets([.101, .101, .101], 60)), 19)
        with self.assertRaises(ValueError): frame_budgets([float('nan')], 60)

    def test_separate_qa_reports_preserve_frozen_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            wf.write(root / 'plan.json', self.plan)
            wf.write(root / 'story-truth.json', self.story)
            original = wf.sha(root / 'plan.json')
            for job in self.plan['jobs']:
                wf.write(root / 'qa' / (job['id'] + '.json'), {'decision': 'accepted',
                    'observations': [{'beat_id': bid, 'time': action['local_range'][0],
                                      'verdict': 'pass', 'evidence': 'synthetic review fixture'}
                                     for action in job['actions'] for bid in action['beat_ids']]})
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_plan.py'),
                str(root / 'plan.json'), '--qa-dir', str(root / 'qa'), '--require-qa'], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(wf.sha(root / 'plan.json'), original)


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg not installed')
class MediaIntegration(unittest.TestCase):
    def test_four_containers_exact_frames_and_qa_pending(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder); source = root / 'synthetic.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=96x160:r=30:d=10',
                '-f', 'lavfi', '-i', 'sine=frequency=440:duration=10', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-shortest', str(source)], check=True)
            manifest = {'output': 'master.mp4', 'size': [96, 160], 'fps': 60, 'containers': [
                {'id': f'C{i}', 'file': source.name, 'sha256': wf.sha(source),
                 'qa_decision': 'synthetic_test', 'retain_seconds': t}
                for i, t in enumerate([10, 7, 10, 6.111723])]}
            wf.write(root / 'assembly.json', manifest)
            cmd = [sys.executable, str(ROOT / 'scripts/assemble.py'), str(root / 'assembly.json')]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = wf.read(root / 'master.assembly.json')
            self.assertEqual(sum(report['frame_budgets']), 1987)
            self.assertLess(abs(report['quantization_delta']), 1/60)
            self.assertTrue(report['synthetic_test'])
            self.assertEqual(report['status'], 'assembled_semantic_qa_pending')
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            qa = subprocess.run([sys.executable, str(ROOT / 'scripts/media_qa.py'), str(source),
                '--out', str(root / 'qa'), '--interval', '5', '--seams', '3'], capture_output=True, text=True)
            self.assertEqual(qa.returncode, 0, qa.stderr)
            evidence = wf.read(root / 'qa/evidence.json')
            self.assertEqual(evidence['semantic_decision'], 'pending')
            self.assertTrue(any(f['time'] == 3 for f in evidence['frames']))
            self.assertTrue(all(not f['reviewed'] for f in evidence['frames']))


if __name__ == '__main__':
    unittest.main()
