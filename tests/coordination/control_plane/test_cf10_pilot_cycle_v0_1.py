"""Pure decision-table and boundary regression tests for the R068 operator cycle."""
from pathlib import Path
import importlib.util
import unittest
from unittest.mock import patch

SOURCE = (Path(__file__).resolve().parents[3] /
          'scripts/coordination/control_plane/cf10_pilot_cycle_v0_1.py')
spec = importlib.util.spec_from_file_location('cf10_pilot_cycle_under_test', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PilotCycleDecisionTests(unittest.TestCase):
    def row(self, **kw):
        base = {'frozen_source_current': True, 'state': 'READY_FOR_WORKER_LAUNCH',
                'claim': 'UNCONSUMED', 'ledger_records': 0,
                'root_receipt_store': 'PASS', 'logs': 'PASS',
                'preclaim': 'PRECLAIM_ROOT_RECEIPT_VERIFIED_NON_AUTHORIZING',
                'proof': 'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED',
                'proof_lineage': 'EXACT_RAW_BYTES_BOUND', 'proof_blockers': [],
                'worker_process_started': False, 'worker_process_finished': False}
        base.update(kw)
        return base

    def test_a052_readiness_is_not_authority(self):
        self.assertEqual(mod.classify(self.row(), launch_once=False),
                         'READY_CONFIRM_LAUNCH_ONCE')
        self.assertEqual(mod.classify(self.row(), launch_once=True),
                         'EXPLICIT_CANONICAL_PAM_LAUNCH')

    def test_claim_consumed_no_retry_even_when_cycle_ready(self):
        for flag in (False, True):
            self.assertEqual(mod.classify(self.row(claim='CONSUMED_NO_RETRY'),launch_once=flag),
                             'OWNER_CLAIM_CONSUMED_NO_RETRY')

    def test_no_start_with_inconsistent_ledger(self):
        self.assertEqual(mod.classify(self.row(ledger_records=1),launch_once=True),
                         'LEDGER_ALREADY_HAS_RECORDS_INSPECT_NO_RETRY')
        self.assertEqual(mod.classify(self.row(ledger_records=None),launch_once=True),
                         'CANONICAL_LEDGER_UNAVAILABLE')

    def test_frozen_source_is_immutable(self):
        self.assertTrue(mod.classify(self.row(frozen_source_current=False),launch_once=True)
                        .startswith('FROZEN_SOURCE_HEAD_MISMATCH'))

    def test_no_implicit_root_provision(self):
        self.assertEqual(mod.classify(self.row(root_receipt_store='ABSENT'),launch_once=True),
                         'RUNTIME_PRECLAIM_PROVISION_REQUIRED')

    def test_missing_logs_provision_before_preclaim(self):
        self.assertEqual(mod.classify(self.row(logs='LOG_DIRECTORY_MISSING'),launch_once=True),
                         'RUNTIME_PRECLAIM_PROVISION_REQUIRED')

    def test_no_proof_fabrication(self):
        self.assertEqual(mod.classify(self.row(proof='BLOCKED_PILOT_PROOF'),launch_once=True),
                         'INDEPENDENT_ROOT_PROOF_REVIEW_REQUIRED')
        self.assertEqual(mod.classify(self.row(proof_lineage=None),launch_once=True),
                         'INDEPENDENT_ROOT_PROOF_REVIEW_REQUIRED')

    def test_preclaim_cannot_be_assumed(self):
        self.assertEqual(mod.classify(self.row(preclaim='BLOCKED'),launch_once=True),
                         'PRECLAIM_INSPECTION_REQUIRED')

    def test_ack_dispatch_transitions_are_explicit(self):
        self.assertEqual(mod.classify(self.row(state='AWAITING_ASSISTANT_ACK')),
                         'AWAITING_ASSISTANT_ACK')
        self.assertEqual(mod.classify(self.row(state='READY_FOR_EXPLICIT_DISPATCH')),
                         'READY_FOR_EXPLICIT_DISPATCH')

    def test_postworker_resume_requires_started_and_ledger(self):
        row = self.row(state='VALIDATE_CANDIDATE', claim='CONSUMED_NO_RETRY',
                       worker_process_started=True, ledger_records=1)
        self.assertEqual(mod.classify(row), 'EXISTING_S3_POSTWORKER_RESUME')
        row['ledger_records'] = 0
        self.assertEqual(mod.classify(row), 'POSTWORKER_PROVENANCE_UNAVAILABLE_NO_RETRY')

    def test_observe_worker_is_never_relaunched(self):
        self.assertEqual(mod.classify(self.row(state='OBSERVE_WORKER',claim='CONSUMED_NO_RETRY')),
                         'WAIT_FOR_WORKER_RESULT_NO_RELAUNCH')

    def test_disallow_unlisted_make_targets(self):
        with self.assertRaisesRegex(mod.PilotBlocked, 'NONCANONICAL_MAKE_TARGET'):
            mod._run_make(Path('/not-needed'), mod.RUNTIME, mod.TASK,
                          'cf10-u180j-a053', 'cf10-retry-claim')

    def test_selector_is_exact(self):
        mod.validate_selector(mod.PROJECT, mod.RUNTIME, mod.TASK, 'cf10-u180j-a053')
        with self.assertRaisesRegex(mod.PilotBlocked, 'EXACT_TASK70_ATTEMPT_REQUIRED'):
            mod.validate_selector(mod.PROJECT, mod.RUNTIME, mod.TASK, '../bad')

    def test_owner_preclaim_rejects_unprovisioned_store(self):
        with (patch.object(mod, '_head', return_value='a'*40),
              patch.object(mod, 'frozen_head', return_value='a'*40),
              patch.object(mod, '_root_store_health', return_value='ROOT_RECEIPT_STORE_MISSING_OR_UNSAFE'),
              patch.object(mod, '_logs_health', return_value='PASS'),
              patch.object(mod, '_assert_static_argv_boundary') as static):
            with self.assertRaisesRegex(mod.PilotBlocked, 'STORE_NOT_PROVISIONED'):
                mod.assert_owner_preclaim_runtime(root=mod.PROJECT, runtime=mod.RUNTIME,
                    task=mod.TASK, attempt='cf10-u180j-a053', head='a'*40)
            static.assert_not_called()

    def test_owner_preclaim_rejects_missing_logs_before_claim(self):
        with (patch.object(mod, '_head', return_value='a'*40),
              patch.object(mod, 'frozen_head', return_value='a'*40),
              patch.object(mod, '_root_store_health', return_value='PASS'),
              patch.object(mod, '_logs_health', return_value='LOG_DIRECTORY_MISSING'),
              patch.object(mod, '_assert_static_argv_boundary') as static):
            with self.assertRaisesRegex(mod.PilotBlocked, 'LOGS_NOT_READY_BEFORE_CLAIM'):
                mod.assert_owner_preclaim_runtime(root=mod.PROJECT, runtime=mod.RUNTIME,
                    task=mod.TASK, attempt='cf10-u180j-a053', head='a'*40)
            static.assert_not_called()

    def test_owner_preclaim_rejects_frozen_head_drift(self):
        with (patch.object(mod, '_head', return_value='a'*40),
              patch.object(mod, 'frozen_head', return_value='b'*40),
              patch.object(mod, '_root_store_health') as root_check):
            with self.assertRaisesRegex(mod.PilotBlocked, 'FROZEN_HEAD_SOURCE_CHANGED'):
                mod.assert_owner_preclaim_runtime(root=mod.PROJECT, runtime=mod.RUNTIME,
                    task=mod.TASK, attempt='cf10-u180j-a053', head='a'*40)
            root_check.assert_not_called()

    def test_owner_preclaim_checks_pinned_r013(self):
        with (patch.object(mod, '_head', return_value='a'*40),
              patch.object(mod, 'frozen_head', return_value='a'*40),
              patch.object(mod, '_root_store_health', return_value='PASS'),
              patch.object(mod, '_logs_health', return_value='PASS'),
              patch.object(mod, '_assert_static_argv_boundary') as static,
              patch.object(mod, '_assert_actual_frozen_invocation') as actual):
            mod.assert_owner_preclaim_runtime(root=mod.PROJECT, runtime=mod.RUNTIME,
                task=mod.TASK, attempt='cf10-u180j-a053', head='a'*40)
            static.assert_called_once()
            actual.assert_called_once_with(mod.PROJECT, mod.RUNTIME, mod.TASK,
                                          'cf10-u180j-a053', 'a'*40)

    def test_proof_gate_blocks_without_make_mutation(self):
        example=self.row(proof='BLOCKED_PROOF')
        with (patch.object(mod.os,'geteuid',return_value=0),
              patch.object(mod.os,'isatty',return_value=True),
              patch.object(mod, 'snapshot', return_value=example),
              patch.object(mod, '_run_make') as make):
            # Patch the actual canonical module object, not only sys.modules:
            # `from package import module` may use the package's cached attribute.
            from scripts.coordination.control_plane import (
                cf10_owner_operator_console_v0_1 as console,
            )
            example['source_head'] = 'a'*40
            with patch.object(console, 'source_guard', return_value='a'*40) as guard:
                result=mod.advance(mod.PROJECT,mod.RUNTIME,mod.TASK,
                                   'cf10-u180j-a053',launch_once=True)
            guard.assert_called_once_with(mod.PROJECT)
            self.assertEqual(result['status'],'PAUSED')
            self.assertEqual(result['next_action'],'INDEPENDENT_ROOT_PROOF_REVIEW_REQUIRED')
            make.assert_not_called()

    def test_no_shell_in_make_invocation(self):
        fake = type('CP', (), {'returncode': 0})()
        with patch.object(mod.subprocess,'run',return_value=fake) as run:
            mod._run_make(mod.PROJECT, mod.RUNTIME, mod.TASK,
                          'cf10-u180j-a053','cf10-resume')
        command, = run.call_args.args
        self.assertEqual(command, ['make', '-s', 'cf10-resume'])
        self.assertNotIn('shell', run.call_args.kwargs)



class PilotActualInvocationTests(unittest.TestCase):
    """The production preclaim uses real canonical provider-plan APIs, never a fixture argv."""

    def _exercise(self, *, started_errors=None, invocation_error=None, bind_error=None):
        from scripts.coordination.control_plane import governed_worker_cycle as cycle
        from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
        from scripts.coordination.control_plane.worker_runtime import invocation_adapter as adapter
        from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
        from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
        from unittest.mock import Mock
        attempt='cf10-u180j-a053'
        head='a'*40
        frozen={'git_head':head}
        prepared={'handoff_manifest_sha256':'c'*64}
        decision={'binding':{'attempt_id':attempt}}
        plan={'attempt_id':attempt, 'argv':['/usr/bin/true','-p','prompt\nline'],
              'workspace_repo':str(mod.RUNTIME/'forprint_system_blueprint'/mod.WORKER/attempt/'workspace/repo'),
              'paths':{'stdout':'stdout','stderr':'stderr'},'timeout_seconds':60}
        inp=[frozen,prepared,decision,{'baseline_fingerprint_sha256':'b'*64}]
        loader=Mock(side_effect=inp)
        build=Mock(return_value=plan, side_effect=invocation_error)
        binding=Mock(return_value=('pinned-spec', 'pinned-plan'), side_effect=bind_error)
        validate=Mock(return_value=started_errors or [])
        with (patch.object(mod,'_head',return_value=head),
              patch.object(mod,'frozen_head',return_value=head),
              patch.object(cycle,'_load_yaml',loader),
              patch.object(cycle,'_assert_frozen_source_state_current'),
              patch.object(cycle,'_load_verified_original_handoff_manifest'),
              patch.object(cycle,'_resolve_stage4c_trusted_transport',return_value='transport'),
              patch.object(cycle,'_resolve_b3_trusted_readback',return_value=None),
              patch.object(cycle,'_project_native_started_record',return_value=({'attempt_id':attempt},'ctx')),
              patch.object(cycle,'_validated_project_native_governed_worker_context',return_value={'safe':True}),
              patch.object(cycle,'_b2_find_launch_mapping',return_value={'argv':plan['argv']}),
              patch.object(adapter,'build_launch_invocation',build),
              patch.object(ledger,'load_contract',return_value='contract'),
              patch.object(ledger,'validate_record_data',validate),
              patch.object(route,'bind_contract',binding),
              patch.object(backend,'assert_frozen_manifest_preclaim',return_value={'claim_consumed':False}) as gate):
            if invocation_error or bind_error or started_errors:
                with self.assertRaises(mod.PilotBlocked):
                    mod._assert_actual_frozen_invocation(mod.PROJECT,mod.RUNTIME,mod.TASK,attempt,head)
            else:
                mod._assert_actual_frozen_invocation(mod.PROJECT,mod.RUNTIME,mod.TASK,attempt,head)
            return build,binding,loader,validate

    def test_exact_frozen_context_reaches_real_builder_and_systemd_contract(self):
        builder,binding,loader,validate=self._exercise()
        self.assertEqual(loader.call_count,4)
        self.assertEqual(builder.call_count,1)
        kw=builder.call_args.kwargs
        self.assertEqual(kw['attempt_root'],mod.RUNTIME/'forprint_system_blueprint'/mod.WORKER/'cf10-u180j-a053')
        self.assertEqual(kw['result_transport'],'transport')
        self.assertEqual(binding.call_count,1)
        self.assertEqual(binding.call_args.kwargs['source_head'],'a'*40)
        validate.assert_called_once()

    def test_provider_failure_blocks_before_claim_without_leaking_prompt(self):
        build,binding,_,_=self._exercise(invocation_error=RuntimeError('SECRET-PROMPT'))
        build.assert_called_once();binding.assert_not_called()

    def test_ledger_schema_blocks_before_binding(self):
        _,binding,_,_=self._exercise(started_errors=['INVALID'])
        binding.assert_not_called()

    def test_backend_contract_failure_blocks_before_claim(self):
        _,binding,_,_=self._exercise(bind_error=RuntimeError('SECRET-ARGV'))
        binding.assert_called_once()


    def test_actual_plan_failure_prevents_preclaim_issue_make(self):
        from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
        snapshot={'source_head':'a'*40, 'frozen_source_current':True,
                  'state':'READY_FOR_WORKER_LAUNCH','claim':'UNCONSUMED',
                  'ledger_records':0, 'root_receipt_store':'PASS','logs':'PASS',
                  'preclaim':'BLOCKED_PRECLAIM_ROOT_RECEIPT','proof':'UNKNOWN'}
        with (patch.object(mod.os,'geteuid',return_value=0),
              patch.object(mod.os,'isatty',return_value=True),
              patch.object(mod,'snapshot',return_value=snapshot),
              patch.object(mod,'_preclaim_absent',return_value=True),
              patch.object(mod,'_assert_static_argv_boundary'),
              patch.object(mod,'_assert_actual_frozen_invocation',side_effect=mod.PilotBlocked('BAD_ACTUAL_ARGV')),
              patch.object(mod,'_run_make') as make,
              patch.object(console,'source_guard',return_value='a'*40)):
            with self.assertRaisesRegex(mod.PilotBlocked,'BAD_ACTUAL_ARGV'):
                mod.advance(mod.PROJECT,mod.RUNTIME,mod.TASK,
                            'cf10-u180j-a053',launch_once=False)
        make.assert_not_called()

if __name__ == '__main__':
    unittest.main()
