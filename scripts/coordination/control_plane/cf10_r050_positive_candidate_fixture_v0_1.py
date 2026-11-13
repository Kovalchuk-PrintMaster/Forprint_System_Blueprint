"""CF10 r050: positive canonical result candidate over fsynced disposable receipts.

Root-only /var/tmp fixture. Real canonical Handoff+S4 validators and r035/r036
are used, but source/output, cgroup sample and service state are synthetic.
Not a real Worker, systemd terminal witness, production quiescence, release,
full E2E, proof issuer, canonical ledger mutation, or operator ACCEPT.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
import yaml

SCHEMA = 'cf10_r050_positive_disposable_candidate_v0_1'
ATT = 'cf10-r050-fixture-a050'
HEAD = 'a' * 40
HAND = 'b' * 64
BASE = 'c' * 64
INV = 'd' * 32


class FixtureBlocked(RuntimeError):
    pass


def run(*, root: Path, variant: str = 'positive') -> dict:
    if variant not in ('positive', 'missing_terminal', 'drifted_result'):
        raise FixtureBlocked('UNKNOWN_FIXTURE_VARIANT')
    if os.geteuid() != 0 or not Path(root).is_dir() or Path(root).is_symlink():
        raise FixtureBlocked('ROOT_AND_SOURCE_REQUIRED')
    from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipts
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
    from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as recovery
    from scripts.coordination.control_plane.worker_runtime import cf10_r035_durable_witness_boundary_v0_1 as durable
    from scripts.coordination.control_plane.worker_runtime import cf10_r036_independent_result_crosscheck_v0_1 as independent
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as witness
    from scripts.coordination.control_plane.worker_runtime import worker_result_return as transport
    from scripts.coordination import assistant_handoff_v2_result_v0_1 as envelope

    unit = binding.unit_for(ATT, HEAD)
    with tempfile.TemporaryDirectory(prefix='cf10-r035-fixture-r050-', dir='/var/tmp') as dir_name:
        tmp = Path(dir_name)
        store = tmp / 'receipts'
        store.mkdir(mode=0o700)
        receipts.claim(private_store=store, attempt_id=ATT, head=HEAD, handoff_sha256=HAND)
        receipts.append_observation(private_store=store, attempt_id=ATT,
                                    expected_head=HEAD, event='LAUNCH_REQUESTED')
        spec = binding.BoundedInput('cf10-r050-disposable-only', ATT, HEAD, HAND, BASE,
                '/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/'
                + ATT + '/workspace/repo',
                '/srv/software_development/forprint-worker-runtime', ('/usr/bin/true',), 60)
        identity = recovery.identity_from_source(attempt_id=ATT, head=HEAD, handoff_sha256=HAND)
        attempt = tmp / ATT
        attempt.mkdir(mode=0o700)
        (attempt / 'logs').mkdir(mode=0o700)
        cursor = {'roadmap_sync': 'IN_SYNC', 'roadmap_status_sha256': 'e' * 64}
        origin = {'handoff_manifest_sha256': HAND, 'source_state_fingerprint': 'f' * 64,
                  'lifecycle_roadmap_cursor': cursor}
        context = {'schema_version': 'forprint_governed_worker_context_projection_v0_1',
                   'handoff_manifest_sha256': HAND, 'handoff_source_state_fingerprint': 'f' * 64,
                   'lifecycle_roadmap_cursor': cursor}
        result = {
            'schema_version': 'forprint_assistant_handoff_v2_result_v0_1',
            'handoff_manifest_sha256': HAND, 'attempt_id': ATT, 'status': 'PASS',
            'changed_paths': ['Makefile'],
            'validation_evidence': [{'name': 'r050-fixture-only', 'result': 'PASS'}],
            'self_repair_attempts': [], 'resume_coordinates': {
                'attempt_id': ATT, 'handoff_manifest_sha256': HAND,
                'source_state_fingerprint': 'f' * 64, 'lifecycle_roadmap_cursor': cursor},
            'unresolved_findings': [],
        }
        stdout = attempt / 'logs' / 'stdout.log'
        stdout.write_text(transport.FRAME_BEGIN + '\n' + yaml.safe_dump(result)
                          + '\n' + transport.FRAME_END + '\n', encoding='utf-8')
        materialized = transport.materialize_worker_result(
            root=root, attempt_root=attempt, stdout_path=stdout,
            origin_manifest=origin, expected_attempt_id=ATT, governed_worker_context=context)
        if materialized.get('validation_passed') is not True:
            raise FixtureBlocked('CANONICAL_MATERIALIZATION_NOT_VALIDATED')
        try:
            transport.materialize_worker_result(
                root=root, attempt_root=attempt, stdout_path=stdout,
                origin_manifest=origin, expected_attempt_id=ATT, governed_worker_context=context)
        except transport.WorkerResultReturnError:
            create_only_replay_blocked = True
        else:
            raise FixtureBlocked('WORKER_RESULT_OVERWRITE_WAS_ALLOWED')
        summary = receipts.observe(private_store=store, attempt_id=ATT, expected_head=HEAD)
        ledger = [dict(attempt_id=ATT, attempt_stage='STARTED', result_state='PENDING',
                       recorded_at='2026-11-03T10:00:00Z')]
        # Synthetic root-observed service. NOT a real systemd verification.
        service = dict(unit=unit, attempt_id=ATT, source_head=HEAD,
                       load_state='not-found', active_state='inactive', main_pid=0,
                       control_group='', user='', group='', kill_mode='',
                       provenance='ROOT_SYSTEMCTL_SHOW_READBACK')
        sample = tmp / 'synthetic-cgroup.events'
        sample.write_bytes(b'populated 1\n')
        arm = witness.KernelWitness(unit, INV, os.open(sample, os.O_RDONLY))
        try:
            durable.record_pre(spec=spec, unit=unit, witness=arm,
                               store=store, fixture=True)
        finally:
            arm.close()
        if variant != 'missing_terminal':
            durable.record_terminal(spec=spec, unit=unit, store=store, fixture=True,
                    outcome={'systemd_unit': unit, 'systemd_invocation_id': INV,
                             'return_code': 0, 'outcome': 'completed',
                             'quiescence_observation':
                             'PINNED_KERNEL_1_TO_0_RETAINED_SYSTEMD_NON_AUTHORIZING',
                             'worker_result_accepted': False, 'automatic_retry': False})
        if variant == 'drifted_result':
            materialized_file = attempt / 'result' / 'worker_result.yaml'
            result['handoff_manifest_sha256'] = '9' * 64
            materialized_file.write_text(yaml.safe_dump(result), encoding='utf-8')
            materialized_file.chmod(0o600)
        def canonical_envelope(doc, bound):
            return envelope.validate_result_envelope(doc, bound, root=root)
        def canonical_resume(doc, bound, bound_context):
            projected = transport._s4_resume_origin(
                governed_worker_context=bound_context, origin_manifest=bound)
            return transport.validate_resume(doc, projected)
        opts = dict(identity=identity, baseline_sha256=BASE, attempt_root=attempt,
                    origin_manifest=origin, governed_worker_context=context,
                    receipt_summary=summary, ledger_rows=ledger, service=service,
                    claim_path_occupied=True, envelope_validator=canonical_envelope,
                    resume_validator=canonical_resume, store=store, fixture=True)
        try:
            examined = independent._assess(**opts)
            candidate = examined.get('status') == 'VERIFIED_RESULT_CANDIDATE_PENDING_CANONICAL_LEDGER_FINALIZER'
            if variant == 'positive':
                if not candidate or examined.get('existing_verifier_checked') is not True:
                    raise FixtureBlocked('POSITIVE_INDEPENDENT_CANDIDATE_MISSING')
                verdict = 'PASS_POSITIVE_DISPOSABLE_CANDIDATE_NON_AUTHORIZING'
            elif variant == 'missing_terminal':
                if examined.get('status') != 'BLOCKED_TERMINAL_NOT_DURABLE':
                    raise FixtureBlocked('MISSING_TERMINAL_DID_NOT_FAIL_CLOSED')
                verdict = 'PASS_NEGATIVE_TERMINAL_ABSENCE_BLOCKED'
            else:
                raise FixtureBlocked('NEGATIVE_DRIFT_WAS_ACCEPTED')
        except independent.CrosscheckBlocked:
            if variant != 'drifted_result':
                raise
            examined = {'status': 'BLOCKED_INVALID_RESULT_CROSS_BOUNDARY'}
            verdict = 'PASS_NEGATIVE_RESULT_DRIFT_BLOCKED'
        if variant == 'missing_terminal':
            if examined.get('status') != 'BLOCKED_TERMINAL_NOT_DURABLE':
                raise FixtureBlocked('MISSING_TERMINAL_DID_NOT_FAIL_CLOSED')
            verdict = 'PASS_NEGATIVE_TERMINAL_ABSENCE_BLOCKED'
        return {
            'schema_version': SCHEMA, 'status': verdict, 'variant': variant,
            'crosscheck_status': examined['status'],
            'actual_result_materializer_used': True,
            'real_envelope_and_resume_validators_used': True,
            'immutable_fixture_pre_record_present': True,
            'immutable_fixture_terminal_record_present': variant != 'missing_terminal',
            'create_only_result_replay_blocked': create_only_replay_blocked,
            'real_worker_process_started': False,
            'real_systemd_terminal_witness_observed': False,
            'actual_worker_end_to_end_proven': False,
            'production_quiescence_proven': False,
            'canonical_ledger_modified': False,
            'root_pilot_proof_issued': False,
            'worker_result_accepted': False,
            'automatic_retry': False, 'launch_allowed': False,
            'production_cutover': False,
            'disposable_fixture_auto_cleaned': True,
        }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path('.'))
    ap.add_argument('--variant', choices=('positive', 'missing_terminal', 'drifted_result'),
                    default='positive')
    ns = ap.parse_args(argv)
    try:
        result = run(root=ns.root.resolve(strict=True), variant=ns.variant)
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(json.dumps({'schema_version': SCHEMA, 'status': 'BLOCKED_DISPOSABLE_FIXTURE',
                          'reason': type(exc).__name__, 'production_cutover': False}))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
