"""Offline, mock-bounded safety tests for canonical pre-worker invocation rehearsal."""
from __future__ import annotations

import inspect
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

from scripts.coordination import control_plane as control_plane_pkg
from scripts.coordination.control_plane import cf10_invocation_rehearsal_v0_1 as rehearsal
from scripts.coordination.control_plane import cf10_prelaunch_audit_v0_2 as audit

ATTEMPT = 'cf10-u180j-a049'
TASK = 'cf10-project-change-impact-and-freshness-control-v0-1'


class RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = Path(self.dir.name) / 'repo'
        self.root.mkdir()
        self.runtime = Path(self.dir.name) / 'runtime'
        self.attempt = self.runtime / 'forprint_system_blueprint/worker-01' / ATTEMPT

    def prepare(self):
        for rel in rehearsal.EXPECTED_FILES:
            p = self.attempt / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('test fixture\n')
        ws = self.attempt / 'workspace/repo'
        ws.mkdir(parents=True)
        return ws

    def mocks(self, *, builder_exception=None, mutate=None):
        cycle = types.ModuleType('scripts.coordination.control_plane.governed_worker_cycle')
        for name in ('_assert_frozen_source_state_current',
                     '_load_verified_original_handoff_manifest'):
            setattr(cycle, name, MagicMock())
        cycle._load_yaml = MagicMock(side_effect=lambda path, label: {'label': label})
        cycle._resolve_stage4c_trusted_transport = MagicMock(return_value='LEGACY')
        cycle._resolve_b3_trusted_readback = MagicMock(return_value=None)
        cycle._project_native_started_record = MagicMock(return_value=(
            {'attempt_stage': 'STARTED', 'result_state': 'PENDING'}, {'task': 'safe'}))
        cycle._validated_project_native_governed_worker_context = MagicMock(return_value={'context': 'safe'})
        cycle.launch_cycle = MagicMock(side_effect=AssertionError('FORBIDDEN_LAUNCH'))
        cycle.launch_authorized_worker_cycle = MagicMock(side_effect=AssertionError('FORBIDDEN_LAUNCH'))
        inv = types.ModuleType('scripts.coordination.control_plane.worker_runtime.invocation_adapter')
        sha = 'a' * 64
        plan = {
            'attempt_id': ATTEMPT,
            'command_representation': 'ARGV_NO_SHELL',
            'workspace_repo': str(self.attempt / 'workspace/repo'),
            'prompt_sha256': sha, 'argv_sha256': 'b' * 64,
            'invocation_sha256': 'c' * 64,
            'prompt': 'SECRET_PROMPT_TEST_SENTINEL',
            'argv': ['provider', '-p', 'SECRET_PROMPT_TEST_SENTINEL'],
            'effects': dict.fromkeys((
                'filesystem_write_performed', 'worker_process_started',
                'attempt_ledger_appended', 'candidate_promoted',
                'commit_performed', 'push_performed'), False),
            'authority': {'adapter_grants_authority': False},
        }
        if mutate:
            mutate(plan)
        inv.build_launch_invocation = MagicMock(side_effect=builder_exception) if builder_exception else MagicMock(return_value=plan)
        inv.build_invocation_evidence = MagicMock(side_effect=lambda candidate: {
            **{key: candidate[key] for key in ('attempt_id','command_representation','prompt_sha256','argv_sha256','invocation_sha256')},
            'serialization_boundary': {'prompt_text_serialized':False, 'full_argv_serialized':False},
        })
        return cycle, inv

    def run_mocks(self, **kwargs):
        cycle, inv = self.mocks(**kwargs)
        worker_pkg = types.ModuleType('scripts.coordination.control_plane.worker_runtime')
        worker_pkg.__path__ = []
        worker_pkg.invocation_adapter = inv
        with patch.dict(sys.modules, {
            'scripts.coordination.control_plane.governed_worker_cycle': cycle,
            'scripts.coordination.control_plane.worker_runtime': worker_pkg,
            'scripts.coordination.control_plane.worker_runtime.invocation_adapter': inv,
        }), patch.object(
            control_plane_pkg, 'governed_worker_cycle', cycle, create=True
        ), patch.object(
            control_plane_pkg, 'worker_runtime', worker_pkg, create=True
        ):
            result = rehearsal.inspect(self.root, self.runtime, TASK, ATTEMPT)
        return result, cycle, inv

    def test_no_attempt_is_not_testable(self):
        p = rehearsal.inspect(self.root, self.runtime, TASK, ATTEMPT)
        self.assertEqual(p['status'], 'NOT_YET_TESTABLE')

    def test_missing_dispatch_is_not_testable(self):
        self.prepare()
        (self.attempt / rehearsal.EXPECTED_FILES[-1]).unlink()
        self.assertEqual(rehearsal.inspect(self.root, self.runtime, TASK, ATTEMPT)['status'], 'NOT_YET_TESTABLE')

    def test_missing_manifest_is_not_testable(self):
        self.prepare()
        (self.attempt / 'manifest.yaml').unlink()
        self.assertEqual(rehearsal.inspect(self.root, self.runtime, TASK, ATTEMPT)['status'], 'NOT_YET_TESTABLE')

    def test_symlink_input_blocks(self):
        self.prepare()
        path = self.attempt / 'manifest.yaml'
        path.unlink()
        path.symlink_to(self.root)
        self.assertEqual(rehearsal.inspect(self.root, self.runtime, TASK, ATTEMPT)['status'], 'BLOCKED')

    def test_symlink_ancestor_blocks(self):
        self.prepare()
        inputdir = self.attempt / 'input'
        replacement = self.attempt / 'input_real'
        inputdir.rename(replacement)
        inputdir.symlink_to(replacement, target_is_directory=True)
        self.assertEqual(rehearsal.inspect(self.root,self.runtime,TASK,ATTEMPT)['status'], 'BLOCKED')

    def test_runtime_secret_error_is_redacted(self):
        reason = rehearsal.safe_reason(RuntimeError('runtime token=abc123'))
        self.assertNotIn('abc123', reason)

    def test_invalid_attempt_blocks(self):
        self.assertEqual(rehearsal.inspect(self.root, self.runtime, TASK, 'bad/../a049')['status'], 'BLOCKED')

    def test_invalid_worker_blocks(self):
        self.assertEqual(rehearsal.inspect(self.root, self.runtime, TASK, ATTEMPT, worker_id='../bad')['status'], 'BLOCKED')

    def test_success_uses_actual_builders_and_returns_only_hashes(self):
        self.prepare()
        result, cycle, inv = self.run_mocks()
        self.assertEqual(result['status'], 'PASS')
        self.assertIn('invocation_sha256='+'c'*64, result['detail'])
        self.assertNotIn('SECRET_PROMPT_TEST_SENTINEL', str(result))
        inv.build_launch_invocation.assert_called_once()
        inv.build_invocation_evidence.assert_called_once()
        cycle._load_verified_original_handoff_manifest.assert_called_once()
        cycle._resolve_stage4c_trusted_transport.assert_called_once()
        cycle._resolve_b3_trusted_readback.assert_called_once()
        cycle.launch_cycle.assert_not_called()
        cycle.launch_authorized_worker_cycle.assert_not_called()

    def test_cached_package_attributes_do_not_escape_mocks(self):
        self.prepare()
        stale_cycle = types.ModuleType('stale_cycle')
        stale_cycle._load_yaml = MagicMock(side_effect=AssertionError('STALE_CYCLE_USED'))
        stale_worker = types.ModuleType('stale_worker')
        with patch.object(control_plane_pkg, 'governed_worker_cycle', stale_cycle,
                          create=True), patch.object(control_plane_pkg, 'worker_runtime',
                                                     stale_worker, create=True):
            result, cycle, inv = self.run_mocks()
        self.assertEqual(result['status'], 'PASS')
        cycle._load_yaml.assert_called()
        inv.build_launch_invocation.assert_called_once()

    def test_canonical_prior_accept_error_blocks(self):
        self.prepare()
        result, _, _ = self.run_mocks(
            builder_exception=RuntimeError('frozen capsule zero-delta ACCEPT evidence digest drift:terminal_sha256'))
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('frozen capsule', result['detail'])

    def test_unknown_provider_error_does_not_expose_text(self):
        self.prepare()
        result, _, _ = self.run_mocks(builder_exception=RuntimeError('secret_token=abc123'))
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertNotIn('abc123', str(result))
        self.assertIn('DETAIL_WITHHELD', result['detail'])

    def test_effect_claiming_worker_started_blocks(self):
        self.prepare()
        result, _, _ = self.run_mocks(mutate=lambda p:p['effects'].__setitem__('worker_process_started', True))
        self.assertEqual(result['status'], 'BLOCKED')

    def test_effect_claiming_ledger_append_blocks(self):
        self.prepare()
        result, _, _ = self.run_mocks(mutate=lambda p:p['effects'].__setitem__('attempt_ledger_appended', True))
        self.assertEqual(result['status'], 'BLOCKED')

    def test_malformed_hash_blocks(self):
        self.prepare()
        result, _, _ = self.run_mocks(mutate=lambda p:p.__setitem__('invocation_sha256', 'bad'))
        self.assertEqual(result['status'], 'BLOCKED')

    def test_generated_report_does_not_modify_attempt(self):
        self.prepare()
        before = sorted((str(p.relative_to(self.attempt)), p.read_bytes())
                        for p in self.attempt.rglob('*') if p.is_file())
        self.run_mocks()
        after = sorted((str(p.relative_to(self.attempt)), p.read_bytes())
                       for p in self.attempt.rglob('*') if p.is_file())
        self.assertEqual(before, after)

    def test_no_launch_methods_called_in_module(self):
        source = inspect.getsource(rehearsal.inspect)
        self.assertNotIn('cycle.launch_cycle(', source)
        self.assertNotIn('cycle.launch_authorized_worker_cycle(', source)
        self.assertNotIn('append_ledger(', source)
        self.assertIn('inv.build_launch_invocation(', source)

    def test_audit_integrates_rehearsal_in_standard_command(self):
        source = inspect.getsource(audit.inspect)
        self.assertIn('rehearsal.inspect(root, runtime, task, attempt_id)',source)
        self.assertIn("add('operator_renewal', 'REVIEW'", source)


if __name__ == '__main__':
    unittest.main()
