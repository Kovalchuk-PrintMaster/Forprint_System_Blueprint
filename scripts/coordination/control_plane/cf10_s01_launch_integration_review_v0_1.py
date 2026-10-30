"""CF-10 S01: project-native *non-authorizing* launch-integration review.

Reuses canonical activation/release/rebind/corridor components. Produces a single
bounded, actionable report. It NEVER executes claim, spawn, ledger append,
operator signature, trust provisioning, Git mutation, or Make quarantine change.
A read-only report can NEVER serve as live launch authority.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

SCHEMA = 'cf10_s01_launch_integration_review_v0_1'
SOURCE_FILES = (
    'Makefile',
    'scripts/coordination/control_plane/governed_worker_cycle.py',
    'scripts/coordination/control_plane/cf10_s01_release_gate_candidate_v0_1.py',
    'scripts/coordination/control_plane/cf10_s01_runtime_rebind_v0_2.py',
    'scripts/coordination/control_plane/cf10_s01_controlled_launch_corridor_v0_1.py',
    'scripts/coordination/control_plane/cf10_s01_root_controlled_single_use_v0_2.py',
    'scripts/coordination/execution_attempt_writer_activation_v0_1.py',
    'scripts/coordination/execution_attempt_writer_lock_v0_1.py',
    'scripts/coordination/execution_attempt_ledger_v0_1.py',
    'scripts/coordination/control_plane/cf10_authorization_lifecycle_v0_1.py',
)
GUARDED_ENTRYPOINTS = ('launch_cycle', 'launch_authorized_worker_cycle')
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
ID_RE = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,159}\Z')


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(['git', *args], cwd=root, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=20).stdout


def status_only(report: object, name: str) -> dict[str, Any]:
    """Bound reported fields. Never export /etc payload, nonce or signature."""
    if not isinstance(report, dict):
        return {'name': name, 'status': 'UNAVAILABLE', 'blockers': ['INVALID_RESULT']}
    raw_blockers = report.get('blockers', [])
    safe_blockers = []
    if isinstance(raw_blockers, list):
        for value in raw_blockers[:30]:
            if isinstance(value, str):
                # Only a bounded blocker code may leave this review tool;
                # never copy arbitrary exception text, paths or secrets.
                if re.fullmatch(r'[A-Z][A-Z0-9_]{2,80}(?::[A-Za-z0-9_]{1,65})?', value):
                    safe_blockers.append(value)
                else:
                    safe_blockers.append('CANONICAL_CHECK_BLOCKED')
    return {'name': name, 'status': str(report.get('status', 'UNKNOWN'))[:100],
            'blockers': safe_blockers,
            'candidate_preconditions_pass': report.get('candidate_preconditions_pass') is True,
            'predicate_pass': report.get('predicate_pass') is True}


def source_inventory(root: Path) -> dict[str, Any]:
    head = git(root, 'rev-parse', 'HEAD').decode('ascii').strip()
    if not SHA40.fullmatch(head):
        raise ValueError('INVALID_GIT_HEAD')
    files = []
    drift = []
    for rel in SOURCE_FILES:
        published = git(root, 'show', f'{head}:{rel}')
        path = root / rel
        if path.is_symlink() or not path.is_file():
            raise ValueError('SOURCE_MISSING_OR_SYMLINK:' + rel)
        actual = path.read_bytes()
        match = actual == published
        files.append({'path': rel, 'published_sha256': sha(published),
                      'worktree_matches_head': match})
        if not match:
            drift.append(rel)
    return {'head': head, 'files': files, 'critical_source_drift': drift}


def inspect_barriers(worker_source: str, make_source: str) -> dict[str, Any]:
    """AST/static positive clues are necessary, never sufficient to launch."""
    code = ast.parse(worker_source)
    fn = {node.name: node for node in code.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    guard = fn.get('require_bounded_s01_launch_authority')
    hard_block = False
    if guard is not None:
        hard_block = any(isinstance(node, ast.Raise) for node in ast.walk(guard))
    entrypoints = {}
    for name in GUARDED_ENTRYPOINTS:
        node = fn.get(name)
        if node is None:
            entrypoints[name] = 'MISSING'
        else:
            statements = [x for x in node.body if not isinstance(x, ast.Expr) or not isinstance(x.value, ast.Constant) or not isinstance(x.value.value, str)]
            first = statements[0] if statements else None
            called = (isinstance(first, ast.Expr) and isinstance(first.value, ast.Call) and
                      isinstance(first.value.func, ast.Name) and
                      first.value.func.id == 'require_bounded_s01_launch_authority')
            entrypoints[name] = 'FIRST_ACTION_GUARD' if called else 'FIRST_ACTION_NOT_PROVEN_GUARDED'
    quarantine = ('cf10-s01-runtime-launch-preflight:' in make_source and
                  'CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND' in make_source)
    return {'direct_python_hard_blocked': hard_block,
            'python_entrypoints': entrypoints,
            'make_quarantine_present': quarantine,
            'source_level_bypass_absence_proven': False,
            'live_launch_allowed': False}


def canonical_reviews(root: Path, *, worker: str, task: str, attempt: str,
                      loader=None) -> list[dict[str, Any]]:
    if loader is not None:
        return [status_only(loader(name), name) for name in ('activation', 'release', 'rebind', 'corridor')]
    out = []
    specs = (
        ('activation', 'scripts.coordination.execution_attempt_writer_activation_v0_1',
         'evaluate', {'stage': 'verify'}),
        ('release', 'scripts.coordination.control_plane.cf10_s01_release_gate_candidate_v0_1',
         'evaluate', {'mode': 'inspect'}),
        ('rebind', 'scripts.coordination.control_plane.cf10_s01_runtime_rebind_v0_2',
         'evaluate', {'worker_id': worker, 'task_prompt_id': task, 'attempt_id': attempt}),
        ('corridor', 'scripts.coordination.control_plane.cf10_s01_controlled_launch_corridor_v0_1',
         'evaluate', {'worker_id': worker, 'task_prompt_id': task, 'attempt_id': attempt}),
    )
    import importlib
    for name, modname, funcname, params in specs:
        try:
            mod = importlib.import_module(modname)
            result = getattr(mod, funcname)(root, **params)
            out.append(status_only(result, name))
        except Exception:
            out.append({'name': name, 'status': 'UNAVAILABLE', 'blockers': ['CANONICAL_EVALUATOR_FAILED']})
    return out


def plan(*, barrier: dict, inventory: dict, checks: list[dict], exact_scope: bool) -> dict:
    blockers = []
    if inventory['critical_source_drift']:
        blockers.append('CRITICAL_WORKTREE_SOURCE_DRIFT')
    if not all(x == 'FIRST_ACTION_GUARD' for x in barrier['python_entrypoints'].values()):
        blockers.append('DIRECT_PYTHON_GUARD_REVIEW_REQUIRED')
    if barrier['direct_python_hard_blocked']:
        blockers.append('DIRECT_PYTHON_LAUNCH_QUARANTINED_BY_DESIGN')
    if barrier['make_quarantine_present']:
        blockers.append('LIVE_MAKE_QUARANTINE_RETAINED')
    else:
        blockers.append('LIVE_MAKE_QUARANTINE_ABSENT_REQUIRES_REVIEW')
    if not exact_scope:
        blockers.append('EXACT_WORKER_TASK_ATTEMPT_NOT_SUPPLIED')
    for row in checks:
        if row['name'] == 'activation' and row['status'] != 'PASS':
            blockers.append('INDEPENDENT_ACTIVATION_NOT_VERIFIED')
        if row['name'] == 'release' and row.get('candidate_preconditions_pass') is not True:
            blockers.append('INDEPENDENT_RELEASE_NOT_VERIFIED')
        if row['name'] == 'rebind' and row.get('predicate_pass') is not True:
            blockers.append('PILOT_SCOPE_AND_EIGHT_PROOFS_NOT_VERIFIED')
    if 'CRITICAL_WORKTREE_SOURCE_DRIFT' in blockers:
        next_action = 'RESTORE_OR_INDEPENDENTLY_REVIEW_CRITICAL_SOURCE_DRIFT_BEFORE_INTEGRATION'
    elif barrier['direct_python_hard_blocked'] or barrier['make_quarantine_present']:
        next_action = 'IMPLEMENT_AND_INDEPENDENTLY_REVIEW_SINGLE_GUARDED_LAUNCH_CORRIDOR_BEFORE_RENEWING_SIGNATURES'
    elif 'EXACT_WORKER_TASK_ATTEMPT_NOT_SUPPLIED' in blockers:
        next_action = 'SELECT_CANONICAL_NEXT_TASK_AND_NEW_ATTEMPT_IN_OPERATOR_REVIEW'
    else:
        next_action = 'INDEPENDENT_RUNTIME_CUTOVER_AND_SIGNATURE_REVIEW_REQUIRED'
    return {'status': 'BLOCKED_NON_AUTHORIZING', 'blockers': sorted(set(blockers)),
            'next_action': next_action, 'evidence_automatically_attested': False,
            'signature_renewal_performed': False, 'source_published_by_review': False,
            'authority_granted': False, 'launch_allowed': False,
            'worker_launched': False, 'canonical_ledger_modified': False,
            'single_use_claim_consumed': False}


def evaluate(root: Path, *, worker: str = '', task: str = '', attempt: str = '', loader=None) -> dict:
    root = root.resolve(strict=True)
    exact_scope = (worker == 'worker-01' and bool(ID_RE.fullmatch(task)) and
                   attempt.startswith('cf10-') and bool(ID_RE.fullmatch(attempt)))
    inventory = source_inventory(root)
    source = (root / 'scripts/coordination/control_plane/governed_worker_cycle.py').read_text('utf-8')
    make = (root / 'Makefile').read_text('utf-8')
    barriers = inspect_barriers(source, make)
    # Guard source and Git HEAD stability after external canonical reads.
    canonical = canonical_reviews(root, worker=worker, task=task, attempt=attempt, loader=loader)
    head_end = git(root, 'rev-parse', 'HEAD').decode('ascii').strip()
    if head_end != inventory['head']:
        raise ValueError('SOURCE_HEAD_CHANGED_DURING_INSPECTION')
    outcome = plan(barrier=barriers, inventory=inventory, checks=canonical, exact_scope=exact_scope)
    return {'schema_version': SCHEMA, 'source_head': inventory['head'],
            'worker_id': worker or None, 'task_prompt_id': task or None,
            'attempt_id': attempt or None, 'source': inventory, 'barriers': barriers,
            'canonical_checks': canonical, 'outcome': outcome,
            'next_sequence': ['REVIEW_AND_PUBLISH_GUARDED_LIVE_CORRIDOR',
                              'INDEPENDENT_PROOF_AND_SOURCE_FRESHNESS_ACCEPTANCE',
                              'RENEW_WRITER_AND_PILOT_SIGNED_DECISIONS_AFTER_FINAL_HEAD',
                              'ONE_GOVERNED_WORKER_ATTEMPT_AND_CLOSEOUT'],
            'no_external_authority_payloads_exported': True}


def write_report(root: Path, report: dict) -> Path:
    base = root / 'tmp/cf10_s01_launch_integration_review'
    if (root / 'tmp').is_symlink() or base.is_symlink():
        raise ValueError('REPORT_DIRECTORY_UNSAFE')
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    if base.stat().st_mode & 0o077:
        raise ValueError('REPORT_DIRECTORY_NOT_PRIVATE')
    body = (json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode()
    key = sha(body)[:20]
    dest = base / ('review_' + key + '.json')
    if dest.exists():
        if dest.is_symlink() or dest.read_bytes() != body:
            raise ValueError('REPORT_EXISTS_WITH_DIFFERENT_BYTES')
    else:
        fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        with os.fdopen(fd, 'wb') as out:
            out.write(body)
    return dest


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('status','report','launch-preflight'))
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--worker-id', default='')
    p.add_argument('--task-prompt-id', default='')
    p.add_argument('--attempt-id', default='')
    args = p.parse_args(argv)
    try:
        report = evaluate(args.root, worker=args.worker_id, task=args.task_prompt_id, attempt=args.attempt_id)
        if args.mode == 'report':
            report['report_file'] = str(write_report(args.root, report))
        print(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2))
        print('CF10_S01_INTEGRATION=BLOCKED_NON_AUTHORIZING')
        print('WORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        return 2 if args.mode == 'launch-preflight' else 0
    except Exception as exc:
        print('CF10_S01_INTEGRATION=BLOCKED_EVALUATION_ERROR:' + type(exc).__name__, file=sys.stderr)
        print('WORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
