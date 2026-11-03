"""CF10 r045: bounded Task70 owner-pilot admission evidence; never grants launch.

This is a separate single-owner profile, not an alias for independent signed
release and not an alternate way around the legacy Make/systemd quarantine.
All production observations are read-only, with no tmp/ dependency, claim,
PAM prompt, systemd lifecycle change or ledger append.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any, Mapping

PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUNTIME = Path('/srv/software_development/forprint-worker-runtime')
WORKER = 'worker-01'
SCHEMA = 'cf10_r045_bounded_owner_pilot_admission_v0_1'
ATTEMPT = re.compile(r'cf10-u180j-a[0-9]{3,}\Z')
TASK = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}\Z')
UNIT = re.compile(r'forprint-cf10-worker-[0-9a-f]{24}\.service\Z')
FACT_KEYS = frozenset({
    'design_verified','published_source','owner_source_sealed','task70_verified',
    'fresh_attempt','canonical_cycle_ready','frozen_input_verified',
    'writer_protocol_enforced','root_state_verified','claim_unconsumed',
    'ledger_unstarted','systemd_worker_quiescent',
    'legacy_release_unchanged','make_quarantined','backend_live_disabled',
})
MISSING_RELEASE_PROOFS = (
    'INDEPENDENT_BOUND_PILOT_RELEASE_REVIEW',
    'SYSTEMD_DISPOSABLE_GATED_END_TO_END_AND_RECOVERY_PROOF',
    'TMP_UNAVAILABLE_RECOVERY_IN_DISPOSABLE_ISOLATION',
    'EXPLICIT_ONE_ATTEMPT_OPERATOR_CUTOVER_DECISION',
)


def classify(*, task: str, attempt: str, facts: Mapping[str, bool],
             details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Pure classification. Even all-true facts are NEVER launch authority."""
    failures = []
    if not isinstance(task, str) or TASK.fullmatch(task) is None:
        failures.append('TASK_ID_INVALID')
    if not isinstance(attempt, str) or ATTEMPT.fullmatch(attempt) is None:
        failures.append('NEW_CF10_U180J_ATTEMPT_ID_REQUIRED')
    if not isinstance(facts, Mapping) or set(facts) != FACT_KEYS:
        failures.append('INCOMPLETE_READ_ONLY_FACTS')
        facts = {}
    for key in sorted(FACT_KEYS):
        if facts.get(key) is not True:
            failures.append('PRECONDITION_' + key.upper())
    ready = not failures
    return {
        'schema_version': SCHEMA,
        'profile': 'SINGLE_OWNER_BOUNDED_TASK70_CANDIDATE',
        'task_prompt_id': task,
        'attempt_id': attempt,
        'status': ('PRECLAIM_EVIDENCE_CANDIDATE_NON_AUTHORIZING' if ready
                   else 'BLOCKED_PRECLAIM_EVIDENCE_NON_AUTHORIZING'),
        'preclaim_evidence_complete': ready,
        'blockers': sorted(set(failures)),
        'observations': dict(details or {}),
        'remaining_release_proofs': list(MISSING_RELEASE_PROOFS),
        'legacy_independent_release': 'UNCHANGED_NOT_SATISFIED_BY_OWNER_PILOT',
        'owner_pam_authenticated': False,
        'operator_claim_consumed': False,
        'admission_authorized': False,
        'launch_allowed': False,
        'production_cutover': False,
        'worker_launched': False,
        'automatic_retry': False,
        'automatic_acceptance': False,
        'automatic_publication': False,
        'next_action': ('SEPARATE_PILOT_CUTOVER_REVIEW_REQUIRED' if ready
                        else 'REPAIR_OR_PREPARE_EXACT_TASK70_ATTEMPT_WITHOUT_LAUNCH'),
    }


def _task70(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Resolve one exact Task70 from canonical queue and index, not a name guess."""
    from scripts.coordination.control_plane import cf10_training_dispatch as training
    queue = training._load_yaml(root / training.TRAINING_QUEUE, 'CF10 training queue')
    rows = queue.get('tasks')
    if not isinstance(rows, list) or queue.get('work_id') != 'u180j' or queue.get('step_id') != 'CF-10':
        return [], ['TRAINING_QUEUE_CONTRACT_INVALID']
    matches = [item for item in rows if isinstance(item, dict) and
               type(item.get('order')) is int and item['order'] == 70]
    if len(matches) != 1 or not isinstance(matches[0].get('task_id'), str):
        return [], ['TASK70_REQUIRES_ONE_CANONICAL_QUEUE_BINDING']
    training_ref = matches[0]['task_id']
    index = training._load_yaml(root / training.WORKER_TASK_INDEX, 'Worker Task index')
    entries = index.get('tasks')
    if not isinstance(entries, list):
        return [], ['WORKER_TASK_INDEX_INVALID']
    candidates = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get('work_id') != 'u180j':
            continue
        name = entry.get('task_id')
        if not isinstance(name, str) or TASK.fullmatch(name) is None:
            continue
        try:
            bound = training.resolve_training_task(root=root, task_prompt_id=name)
        except Exception:
            continue  # unrelated invalid tasks cannot supply Task70 authority
        if (type(bound.get('training_order')) is int and bound['training_order'] == 70 and
                bound.get('training_task_id') == training_ref):
            candidates.append({
                'task_prompt_id': bound['task_prompt_id'],
                'training_order': 70,
                'training_task_id': training_ref,
                'work_front_id': bound['work_front_id'],
                'task_ref': bound['task_ref'],
            })
    if len(candidates) != 1:
        return candidates, ['TASK70_INDEX_AND_QUEUE_REBIND_FAILED']
    return candidates, []


def inventory(root: Path) -> dict[str, Any]:
    """Read only canonical Task70 discovery, without attempt creation."""
    try:
        root = root.resolve(strict=True)
        if root != PROJECT:
            raise ValueError('NON_CANONICAL_ROOT')
        tasks, blockers = _task70(root)
    except Exception:
        tasks, blockers = [], ['TASK70_CANONICAL_INVENTORY_UNAVAILABLE']
    return {
        'schema_version': SCHEMA, 'mode': 'inventory',
        'status': 'TASK70_IDENTIFIED_NON_AUTHORIZING' if not blockers else 'BLOCKED_NON_AUTHORIZING',
        'tasks': tasks, 'blockers': blockers,
        'launch_allowed': False, 'admission_authorized': False,
        'next_action': 'SELECT_FRESH_ATTEMPT_AND_RUN_READ_ONLY_INSPECT',
    }


def _claim_unconsumed(attempt: str) -> tuple[bool, str]:
    """Check exactly this owner claim in an existing root-owned directory."""
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    fd = once.open_root_owned_state_dir()
    try:
        name = 'owner_attempt_' + hashlib.sha256((WORKER + '\0' + attempt).encode()).hexdigest() + '.json'
        try:
            st = os.stat(name, dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            return True, 'NOT_CONSUMED'
        return False, ('ALREADY_CONSUMED' if stat.S_ISREG(st.st_mode) else 'UNSAFE_CLAIM_ENTRY')
    finally:
        os.close(fd)


def _systemd_quiescent() -> tuple[bool, str]:
    """Fail closed on command errors or ambiguous CF10 service observations."""
    cp = subprocess.run([
        '/usr/bin/systemctl', 'list-units', '--no-pager', '--no-legend', '--plain',
        '--all', '--type=service', 'forprint-cf10-worker-*.service',
    ], capture_output=True, text=True, check=False, timeout=20,
        env={'PATH': '/usr/bin:/bin', 'LANG': 'C'})
    if cp.returncode != 0:
        return False, 'SYSTEMD_READBACK_UNAVAILABLE'
    for line in cp.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.split(maxsplit=4)
        if len(fields) < 4 or UNIT.fullmatch(fields[0]) is None:
            return False, 'SYSTEMD_UNIT_LIST_AMBIGUOUS'
        if fields[2] != 'inactive' or fields[3] not in ('dead', 'exited'):
            return False, 'SYSTEMD_CF10_UNIT_NOT_QUIESCENT'
    return True, 'NO_ACTIVE_CF10_WORKER_UNITS_OBSERVED'


def collect(root: Path, task: str, attempt: str) -> dict[str, Any]:
    """Re-use canonical source/ledger/owner checks; never synthesize proof."""
    facts: dict[str, bool] = {k: False for k in FACT_KEYS}
    details: dict[str, str] = {}
    if root.resolve() != PROJECT or not isinstance(task, str) or TASK.fullmatch(task) is None or \
            not isinstance(attempt, str) or ATTEMPT.fullmatch(attempt) is None:
        return classify(task=task, attempt=attempt, facts=facts,
                        details={'identity': 'BLOCKED_CANONICAL_ROOT_OR_IDS'})

    from scripts.coordination.control_plane import cf10_single_owner_pilot_review_v0_1 as design
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_owner_pam_launch_v0_1 as owner
    from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as modern
    from scripts.coordination.control_plane import cf10_training_dispatch as training
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
    from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer

    try:
        report = design.inspect(root)
        facts['design_verified'] = report.get('status') == 'OWNER_SELECTED_DESIGN_RELEASE_BLOCKED' and not report.get('blockers')
        # r042 independently captured the historic legacy-release bytes.
        # Neither a changed tracked file nor a new local override is accepted.
        legacy = root / 'scripts/coordination/control_plane/cf10_s01_release_gate_candidate_v0_1.py'
        expected = 'f8d6cb94079233d04a7b5f92b6418cd6393485d8565a44338f2fcf210eac0eec'
        facts['legacy_release_unchanged'] = (facts['design_verified'] and
            legacy.is_file() and not legacy.is_symlink() and
            hashlib.sha256(legacy.read_bytes()).hexdigest() == expected)
        details['design'] = report.get('status', 'UNKNOWN')
    except Exception:
        details['design'] = 'UNVERIFIABLE'
    try:
        console.source_guard(root)
        facts['published_source'] = True
        details['published_source'] = 'EXACT_REMOTE_HEAD_AND_CRITICAL_SOURCE'
    except Exception:
        details['published_source'] = 'BLOCKED'
    try:
        owner._assert_live_source(root)
        facts['owner_source_sealed'] = True
    except Exception:
        details['owner_source_sealed'] = 'BLOCKED'
    try:
        bound = training.resolve_training_task(root=root, task_prompt_id=task)
        candidates, problems = _task70(root)
        facts['task70_verified'] = (not problems and len(candidates) == 1 and
                                    candidates[0]['task_prompt_id'] == task and
                                    type(bound.get('training_order')) is int and bound['training_order'] == 70)
        details['task70'] = 'EXACT_QUEUE_ORDER_70' if facts['task70_verified'] else 'NOT_EXACT_TASK70'
    except Exception:
        details['task70'] = 'UNVERIFIABLE'
    try:
        attempt_root = RUNTIME / 'forprint_system_blueprint' / WORKER / attempt
        facts['fresh_attempt'] = attempt_root.is_dir() and not attempt_root.is_symlink()
        facts['canonical_cycle_ready'] = bool(facts['fresh_attempt']) and (
            cycle.status(root=root, runtime_root=RUNTIME, task_prompt_id=task,
                         attempt_id=attempt, worker_id=WORKER).get('state') == 'READY_FOR_WORKER_LAUNCH')
        owner._cycle_preclaim(root, RUNTIME, task, attempt)
        facts['frozen_input_verified'] = True
        details['cycle'] = 'EXACT_READY_SOURCE_FROZEN'
    except Exception:
        details['cycle'] = 'NOT_READY_OR_SOURCE_DRIFT'
    try:
        facts['writer_protocol_enforced'] = bool(writer.load_enforced_protocol(required=True))
    except Exception:
        details['writer'] = 'ENFORCED_PROTOCOL_NOT_VERIFIED'
    try:
        fd = once.open_root_owned_state_dir()
        os.close(fd)
        facts['root_state_verified'] = True
        ok, state = _claim_unconsumed(attempt)
        facts['claim_unconsumed'] = ok
        details['claim'] = state
    except Exception:
        details['claim'] = 'ROOT_STATE_UNAVAILABLE_OR_UNTRUSTED'
    try:
        contract = ledger.load_contract(root)
        store = ledger.store_root(root, contract, None)
        facts['ledger_unstarted'] = len(ledger.records_for_attempt(store, attempt)) == 0
        details['ledger'] = 'NO_ATTEMPT_RECORDS' if facts['ledger_unstarted'] else 'EXISTING_HISTORY_NO_RETRY'
    except Exception:
        details['ledger'] = 'LEDGER_REVIEW_UNAVAILABLE'
    try:
        ok, state = _systemd_quiescent()
        facts['systemd_worker_quiescent'] = ok
        details['systemd'] = state
    except Exception:
        details['systemd'] = 'READBACK_UNAVAILABLE'
    # Preserve the source-controlled quarantine. A changed gate is not a grant.
    try:
        make = (root / 'Makefile').read_text(encoding='utf-8')
        make_gate = ('cf10-s01-runtime-launch-preflight:\n'
            '\t@echo "CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND"; exit 2')
        facts['make_quarantined'] = (make_gate in make and
            'governed-worker-cycle-advance: cf10-s01-runtime-launch-preflight' in make)
        backend_file = root / 'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py'
        facts['backend_live_disabled'] = (modern.backend.LIVE_CUTOVER_ENABLED is False and
            backend_file.is_file() and not backend_file.is_symlink() and
            b'LIVE_CUTOVER_ENABLED=False' in backend_file.read_bytes())
    except Exception:
        details['release'] = 'SOURCE_RELEASE_FENCE_UNVERIFIED'
    return classify(task=task, attempt=attempt, facts=facts, details=details)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=('inventory', 'inspect', 'launch-preflight'))
    ap.add_argument('--root', type=Path, default=Path('.'))
    ap.add_argument('--task-prompt-id', default='')
    ap.add_argument('--attempt-id', default='')
    args = ap.parse_args(argv)
    try:
        if args.action == 'inventory':
            result = inventory(args.root)
        else:
            result = collect(args.root, args.task_prompt_id, args.attempt_id)
    except Exception:
        result = classify(task=args.task_prompt_id, attempt=args.attempt_id,
                          facts={}, details={'error': 'UNEXPECTED_READ_ONLY_FAILURE'})
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    # The CLI can never authorize the launch path, even after all preclaim facts.
    if args.action == 'launch-preflight':
        return 2
    return 0 if not result.get('blockers') else 2


if __name__ == '__main__':
    raise SystemExit(main())
