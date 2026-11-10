#!/usr/bin/env python3
"""CF10 R138: canonical root-terminal / attempt-ledger cross-store review fence.

Invoked *after* R030's immutable R035 terminal receipt or after R133's
explicit quarantine. Every readback is done by existing root/ledger modules.
The output is an unprivileged review projection; no terminal ledger append,
Worker Result acceptance, release, retry, claim, systemd operation, or IPC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Mapping

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding

SCHEMA = 'cf10_r138_canonical_terminal_handoff_v0_1'
ROOT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RECEIPTS = Path('/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/control_plane/root_receipts')
SUCCESS = 'TERMINAL_RECORD_PRESENT_NEEDS_LEDGER_AND_INDEPENDENT_RESULT_VERIFIER'
CANCELLED = 'BLOCKED_CONTROLLER_INTERRUPTED_OR_TERMINAL_NOT_RECORDED'
KERNEL = 'PINNED_KERNEL_1_TO_0_RETAINED_SYSTEMD_NON_AUTHORIZING'
DIGEST = re.compile(r'[a-f0-9]{64}\Z')

class TerminalHandoffHold(RuntimeError):
    pass

def deny(code: str) -> None:
    raise TerminalHandoffHold('CF10_R138_HOLD_' + code)

def _sha(data: Mapping) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True).encode('ascii')).hexdigest()

def _spec(spec: binding.BoundedInput, unit: str) -> None:
    if os.geteuid() != 0:
        deny('ROOT_REQUIRED')
    if type(spec) is not binding.BoundedInput:
        deny('SPEC_TYPE')
    try:
        plan = binding.bind_plan(spec)
        binding.validate_plan(plan, spec)
    except (binding.BoundaryBlocked, ValueError, TypeError, KeyError):
        deny('SPEC_NOT_CANONICAL')
    if type(unit) is not str or unit != binding.unit_for(spec.attempt_id, spec.source_head):
        deny('UNIT_BINDING')
    if spec.runtime_root != '/srv/software_development/forprint-worker-runtime':
        deny('RUNTIME_ROOT')

def _outcome(unit: str, outcome: Mapping, *, cancelled: bool) -> str:
    if not isinstance(outcome, Mapping):
        deny('OUTCOME_TYPE')
    if outcome.get('worker_result_accepted') is not False or outcome.get('automatic_retry') is not False:
        deny('OUTCOME_FALSE_AUTHORITY')
    invocation = outcome.get('systemd_invocation_id')
    if type(invocation) is not str or not re.fullmatch('[a-f0-9]{32}', invocation):
        deny('INVOCATION')
    if cancelled:
        if (outcome.get('state') != 'CANCELLED_KERNEL_ZERO_REVIEW_REQUIRED' or
            outcome.get('unit') != unit or outcome.get('terminal_success') is not False or
            outcome.get('release_allowed') is not False or outcome.get('root_review_recorded') is not True):
            deny('CANCELLATION_OUTCOME_DRIFT')
    elif (outcome.get('systemd_unit') != unit or outcome.get('outcome') != 'completed' or
          type(outcome.get('return_code')) is not int or outcome['return_code'] != 0 or
          outcome.get('timed_out') is not False or outcome.get('release_allowed') is not False or
          outcome.get('quiescence_observation') != KERNEL):
        deny('SUCCESS_OUTCOME_DRIFT')
    return invocation

def _ledger_pending(spec: binding.BoundedInput) -> tuple[dict, str]:
    """Read one canonical STARTED/PENDING fact; never attempt terminal append.

    The historical ledger is a *fact store*, not root/kernel authority. Refuse
    duplicates, unsafe paths, invalid record hashes, or already terminal rows.
    """
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
    import yaml
    contract = ledger.load_contract(ROOT)
    store = ROOT / contract['storage']['default_root']
    if not store.is_dir() or store.is_symlink() or store.resolve() != store:
        deny('LEDGER_STORE_UNAVAILABLE')
    files = sorted(store.glob(spec.attempt_id + '__*.yaml'))
    if len(files) != 1:
        deny('LEDGER_NOT_EXACTLY_ONE_PENDING')
    path = files[0]
    if (path.is_symlink() or not path.is_file() or path.stat().st_size > 65536 or
        path.stat().st_nlink != 1 or not stat.S_ISREG(path.lstat().st_mode)):
        deny('LEDGER_FILE_UNSAFE')
    try:
        row = yaml.safe_load(path.read_text(encoding='utf8'))
    except (UnicodeError, ValueError, yaml.YAMLError, OSError):
        deny('LEDGER_CONTENT_UNREADABLE')
    if type(row) is not dict or ledger.validate_record_data(row, contract):
        deny('LEDGER_RECORD_CONTRACT')
    row_sha = ledger.record_digest(row)
    if path.name != f'{spec.attempt_id}__{row_sha[:12]}.yaml':
        deny('LEDGER_FILENAME_HASH')
    if (row.get('attempt_id') != spec.attempt_id or row.get('attempt_stage') != 'STARTED' or
            row.get('result_state') != 'PENDING' or row.get('validator_outcome') != 'NOT_RUN'):
        deny('LEDGER_ALREADY_TERMINAL_OR_UNBOUND')
    return row, row_sha

def _trusted_readback(*, spec: binding.BoundedInput, unit: str, invocation: str,
                      cancelled: bool) -> dict:
    """Authenticate immutable R035, R015 root receipts and R020 ledger join.

    No user-provided witness, lease dictionary or ledger-row mapping is accepted.
    Production locations are hard-pinned; no fixture override in this API.
    """
    from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as recovery
    from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipts
    from scripts.coordination.control_plane import cf10_receipt_ledger_join_review_v0_1 as r020
    from scripts.coordination.control_plane.worker_runtime import cf10_r035_durable_witness_boundary_v0_1 as r035
    identity = recovery.identity_from_source(attempt_id=spec.attempt_id,
                                              head=spec.source_head, handoff_sha256=spec.handoff_sha256)
    durable = r035.inspect(identity=identity, baseline_sha256=spec.baseline_sha256)
    want = CANCELLED if cancelled else SUCCESS
    if durable.get('state') != want or durable.get('worker_result_accepted') is not False or durable.get('automatic_retry') is not False:
        deny('DURABLE_ROOT_WITNESS_STATE')
    directory = r035._directory(RECEIPTS, spec.attempt_id, spec.source_head, spec.handoff_sha256)
    pre = r035._read(directory, r035.PRE)
    post = r035._read(directory, r035.POST)
    if pre is None or pre.get('invocation_id') != invocation or pre.get('unit') != unit:
        deny('DURABLE_INVOCATION_BINDING')
    if cancelled:
        if post is not None:
            deny('CANCELLATION_CANNOT_OVERWRITE_TERMINAL')
    else:
        if (post is None or post.get('invocation_id') != invocation or post.get('unit') != unit or
                post.get('pre_record_sha256') != pre.get('record_sha256') or
                post.get('quiescence_observation') != KERNEL):
            deny('DURABLE_TERMINAL_BINDING')
    receipt = receipts.observe(private_store=RECEIPTS, attempt_id=spec.attempt_id,
                               expected_head=spec.source_head)
    if (receipt.get('claim_consumed') is not True or receipt.get('root_receipt_chain_verified') is not True or
            receipt.get('automatic_retry') is not False or receipt.get('worker_result_accepted') is not False):
        deny('ROOT_RECEIPT_CHAIN')
    if cancelled:
        if type(receipt.get('event_count')) is not int or receipt['event_count'] < 2:
            deny('CANCELLATION_OBSERVATIONS_ABSENT')
        n = receipt['event_count']
        first = receipts._read_json(directory / f'event_{n-1:04d}.json')
        last = receipts._read_json(directory / f'event_{n:04d}.json')
        if (first.get('event') != 'QUIESCENCE_OBSERVED_CANDIDATE' or
                last.get('event') != 'REVIEW_REQUIRED' or
                last.get('previous_sha256') != first.get('receipt_sha256') or
                last.get('receipt_sha256') != receipt.get('last_digest')):
            deny('CANCELLATION_REVIEW_NOT_IN_CHAIN')
    row, row_sha = _ledger_pending(spec)
    joined = r020.reconcile(attempt_id=spec.attempt_id, source_head=spec.source_head,
                            handoff_sha256=spec.handoff_sha256,
                            receipt=receipt, ledger_rows=[row])
    if (joined.get('state') != 'BLOCKED_STARTED_PENDING_RECOVERY_REQUIRED' or
            joined.get('worker_result_accepted') is not False or
            joined.get('release_allowed') is not False):
        deny('LEDGER_ROOT_CROSS_STORE_DRIFT')
    return {'r035_pre_record_sha256': pre['record_sha256'],
            'r035_terminal_record_sha256': post['record_sha256'] if post else None,
            'r015_last_receipt_sha256': receipt['last_digest'],
            'ledger_started_sha256': row_sha}

def review_success(*, spec: binding.BoundedInput, unit: str, outcome: Mapping) -> dict:
    """Called only by canonical R030 after R035.record_terminal fsync."""
    _spec(spec, unit)
    invocation = _outcome(unit, outcome, cancelled=False)
    try:
        proof = _trusted_readback(spec=spec, unit=unit, invocation=invocation, cancelled=False)
    except TerminalHandoffHold:
        raise
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        deny('ROOT_LEDGER_READBACK_' + type(exc).__name__)
    if proof.get('r035_terminal_record_sha256') is None:
        deny('TERMINAL_RECEIPT_ABSENT')
    return _report(spec, unit, invocation, proof, cancelled=False)

def review_cancelled(*, spec: binding.BoundedInput, unit: str, outcome: Mapping) -> dict:
    """Called only by R030 after successful R133 kernel-zero quarantine."""
    _spec(spec, unit)
    invocation = _outcome(unit, outcome, cancelled=True)
    try:
        proof = _trusted_readback(spec=spec, unit=unit, invocation=invocation, cancelled=True)
    except TerminalHandoffHold:
        raise
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        deny('ROOT_LEDGER_READBACK_' + type(exc).__name__)
    if proof.get('r035_terminal_record_sha256') is not None:
        deny('CANCELLATION_TERMINAL_FORGERY')
    return _report(spec, unit, invocation, proof, cancelled=True)

def _report(spec, unit, invocation, proof, *, cancelled):
    expected = ('r035_pre_record_sha256', 'r015_last_receipt_sha256', 'ledger_started_sha256')
    if (type(proof) is not dict or any(type(proof.get(k)) is not str or
            not DIGEST.fullmatch(proof[k]) for k in expected) or
            (proof.get('r035_terminal_record_sha256') is not None and
             (type(proof['r035_terminal_record_sha256']) is not str or
              not DIGEST.fullmatch(proof['r035_terminal_record_sha256'])))):
        deny('PROOF_DIGEST_SHAPE')
    row = {'schema_version': SCHEMA, 'attempt_id':spec.attempt_id,
           'source_head':spec.source_head,'handoff_sha256':spec.handoff_sha256,
           'baseline_sha256':spec.baseline_sha256,'unit':unit,
           'systemd_invocation_id':invocation,
           'state': 'QUARANTINE_REVIEW_REQUIRED_NO_TERMINAL_LEDGER' if cancelled else
                    'ROOT_TERMINAL_READY_FOR_INDEPENDENT_RESULT_VERIFIER',
           **proof,
           'result_accepted':False,'terminal_ledger_written':False,
           'automatic_retry':False,'release_allowed':False,'launch_allowed':False,
           'production_cutover_authorized':False,
           'independent_worker_result_verified':False,
           'g1_g5_closed':False}
    row['report_sha256'] = _sha(row)
    return row

def main(argv=None) -> int:
    p=argparse.ArgumentParser(description='R138 source-only interface audit')
    p.add_argument('--mode',choices=['source-check'],required=True)
    p.parse_args(argv)
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launch
    if launch.LIVE_CUTOVER_ENABLED is not False:
        deny('LIVE_GATE_DRIFT')
    print('CF10_R138_CANONICAL_R030=ROOT_TERMINAL_AND_QUARANTINE_REVIEW_HOOKS')
    print('CF10_R138_LEDGER=STARTED_PENDING_FACT_ONLY_NO_TERMINAL_APPEND')
    print('CF10_R138_ROOT_READBACK=R035_R015_R020_READ_ONLY')
    print('CF10_R138_G1_G5=OPEN_NO_LIVE_ADMISSION')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
