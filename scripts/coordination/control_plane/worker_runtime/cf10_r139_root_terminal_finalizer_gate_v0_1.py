#!/usr/bin/env python3
"""CF10 R139: fail-closed root/kernel lineage required before terminal finalizer.

This is a READ-ONLY prerequisite for the pre-existing CF09/CF10 finalizer,
not a new ledger writer or a replacement Worker Result validator. It invokes
R138's audited root-only readback of R035+R015+R020 and compares the exact
immutable STARTED fact. It NEVER creates, accepts, or finalizes Worker Result.

The production live cutover remains sealed; this module has no launch path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
import os
from pathlib import Path
import re
from collections.abc import Mapping

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bind
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r138_canonical_terminal_handoff_v0_1 as r138,
)

SCHEMA = 'cf10_r139_pre_finalizer_root_lineage_v0_1'
ROOT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
READY = 'ROOT_TERMINAL_VERIFIED_RESULT_VALIDATION_REMAINS_IN_CANONICAL_FINALIZER'
HEX40 = re.compile(r'[a-f0-9]{40}\Z')
HEX64 = re.compile(r'[a-f0-9]{64}\Z')
INV = re.compile(r'[a-f0-9]{32}\Z')

class RootFinalizerHold(RuntimeError):
    pass


def deny(reason: str) -> None:
    raise RootFinalizerHold('CF10_R139_HOLD_' + reason)


@dataclass(frozen=True)
class FrozenTerminalFacts:
    attempt_id: str
    source_head: str
    handoff_sha256: str
    baseline_sha256: str


def review_pending_success(*, root: Path, attempt_id: str, source_head: str,
                           baseline_sha256: str, handoff_sha256: str,
                           started_record: Mapping, process_result: Mapping) -> dict:
    """Require authentic root PRE+POST/ledger readback before existing finalizer.

    This gate is only for an attempt whose latest ledger fact remains PENDING.
    Its caller independently validates the frozen source, result envelope and
    Worker delta; R139 does not claim to have performed those checks itself.
    """
    if os.geteuid() != 0:
        deny('ROOT_REQUIRED_FOR_TRUSTED_READBACK')
    if (not isinstance(root, Path) or root != ROOT or not ROOT.is_dir() or
            ROOT.is_symlink() or ROOT.resolve() != ROOT):
        deny('CANONICAL_ROOT_REQUIRED')
    if (type(attempt_id) is not str or not bind.ATTEMPT.fullmatch(attempt_id) or
            type(source_head) is not str or not HEX40.fullmatch(source_head) or
            type(baseline_sha256) is not str or not HEX64.fullmatch(baseline_sha256) or
            type(handoff_sha256) is not str or not HEX64.fullmatch(handoff_sha256)):
        deny('FROZEN_IDENTITY_OR_HASH')
    if type(started_record) is not dict:
        deny('LEDGER_ROW_TYPE')
    if (started_record.get('attempt_id') != attempt_id or
            started_record.get('attempt_stage') != 'STARTED' or
            started_record.get('result_state') != 'PENDING' or
            started_record.get('validator_outcome') != 'NOT_RUN'):
        deny('STARTED_PENDING_FACT_REQUIRED')
    if type(process_result) is not dict:
        deny('PROCESS_RESULT_TYPE')
    unit = bind.unit_for(attempt_id, source_head)
    # R138 verifies the literal R030 terminal outcome, including unit,
    # return_code=0, pinned-kernel result, zero authority and invocation ID.
    try:
        invocation = r138._outcome(unit, process_result, cancelled=False)
    except (r138.TerminalHandoffHold, ValueError, TypeError, KeyError):
        deny('CANONICAL_SYSTEMD_RESULT_REQUIRED')
    if type(invocation) is not str or not INV.fullmatch(invocation):
        deny('INVOCATION_ID')

    facts = FrozenTerminalFacts(attempt_id, source_head, handoff_sha256,
                                baseline_sha256)
    try:
        # Reuse R138's root-owned readback and one exact immutable ledger row;
        # no synthetic receipt/worker dictionary supplied by callers.
        proof = r138._trusted_readback(spec=facts, unit=unit,
                                        invocation=invocation, cancelled=False)
        # Execution Attempt Ledger record_digest() canonical serialization.
        # R138 has independently re-read and validated that canonical record.
        expected_row_sha = hashlib.sha256(json.dumps(
            started_record,sort_keys=True,separators=(',', ':'),
            ensure_ascii=False).encode('utf-8')).hexdigest()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        deny('INDEPENDENT_READBACK_' + type(exc).__name__)
    expected_keys = ('r035_pre_record_sha256', 'r035_terminal_record_sha256',
                     'r015_last_receipt_sha256', 'ledger_started_sha256')
    if (type(proof) is not dict or set(proof) != set(expected_keys) or
            any(type(proof.get(k)) is not str or not HEX64.fullmatch(proof[k])
                for k in expected_keys) or
            proof['ledger_started_sha256'] != expected_row_sha):
        deny('ROOT_LEDGER_CROSSSTORE_MISMATCH')
    return {
        'schema_version': SCHEMA,
        'state': READY,
        'attempt_id': attempt_id,
        'source_head': source_head,
        'systemd_unit': unit,
        'systemd_invocation_id': invocation,
        **proof,
        'root_terminal_attested_for_review': True,
        'independent_worker_result_verified': False,
        'terminal_ledger_written': False,
        'worker_result_accepted': False,
        'release_allowed': False,
        'automatic_retry': False,
        'g1_g5_closed': False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description='R139 source-only finalizer guard')
    p.add_argument('--mode', required=True, choices=['source-check'])
    p.parse_args(argv)
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    if launcher.LIVE_CUTOVER_ENABLED is not False:
        deny('LIVE_GATE_DRIFT')
    print('CF10_R139_FINALIZER=REQUIRES_ROOT_R035_R015_R020_BEFORE_TERMINAL_APPEND')
    print('CF10_R139_EXISTING_FINALIZER=UNCHANGED_NO_NEW_LEDGER_WRITER')
    print('CF10_R139_G1_G5=OPEN_NO_LIVE_ADMISSION')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
