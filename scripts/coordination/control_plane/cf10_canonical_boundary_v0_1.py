"""CF10 canonical-boundary candidate, intentionally NON-AUTHORIZING.

This candidate composes the tested r010 snapshot, r013 binding / process observation,
and root-scoped lifecycle evidence. There is NO method here to start a worker,
consume authority, mint an ACK, approve a delta or promote an output.

The actual production systemd supervisor + durable claim reconciliation must be
separately reviewed and connected to the canonical dispatcher before cutover.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import os
import re
import stat
from typing import Mapping

from scripts.coordination.control_plane.workspace import cf10_untrusted_worktree_delta_v0_1 as delta
from scripts.coordination.control_plane import cf10_trusted_baseline_binding_v0_1 as binding
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as supervisor

class BoundaryError(ValueError):
    pass

_HEAD=re.compile(r"[a-f0-9]{40}\Z")
_SHA=re.compile(r"[a-f0-9]{64}\Z")
_TASK=re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{4,127}\Z")
_ATTEMPT=re.compile(r"cf10-[A-Za-z0-9_-]{3,80}-a[0-9]{3,5}\Z")


def _block(tag):
    raise BoundaryError('CF10_R015_'+tag)


def canonical_digest(value: Mapping) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True, separators=(',',':'),ensure_ascii=False).encode('utf8')).hexdigest()


def validate_scope(*, task: str, attempt: str, head: str, handoff: str, worktree: str, runtime_root: str):
    if not isinstance(task,str) or not _TASK.fullmatch(task): _block('TASK')
    if not isinstance(attempt,str) or not _ATTEMPT.fullmatch(attempt): _block('ATTEMPT')
    if not isinstance(head,str) or not _HEAD.fullmatch(head): _block('HEAD')
    if not isinstance(handoff,str) or not _SHA.fullmatch(handoff): _block('HANDOFF')
    if not isinstance(worktree,str) or not worktree.startswith('/') or '..' in Path(worktree).parts: _block('WORKTREE')
    if not isinstance(runtime_root,str) or not runtime_root.startswith('/') or '..' in Path(runtime_root).parts: _block('RUNTIME')
    expected=Path(runtime_root)/'forprint_system_blueprint'/'worker-01'/attempt/'workspace'/'repo'
    if Path(worktree)!=expected: _block('WORKTREE_SCOPE')


def capture_bound_baseline(*, task: str, attempt: str, head: str, handoff: str, worktree: str, runtime_root: str) -> dict:
    """Capture candidate snapshot. Caller must keep it OUTSIDE the worker's reachable tree.

    Returns a complete, content-bound record; does not persist it or grant authority.
    """
    validate_scope(task=task,attempt=attempt,head=head,handoff=handoff,worktree=worktree,runtime_root=runtime_root)
    snap=delta.snapshot_tree(worktree)
    spec=supervisor.BoundedInput(task,attempt,head,handoff,snap['content_sha256'],worktree,runtime_root,('/usr/bin/python3','-V'),60)
    # Canonical plan validation is non-authorizing, but proves structure and scoping.
    supervisor.validate_plan(supervisor.bind_plan(spec),spec)
    row={'schema_version':'cf10_r015_bound_baseline_v0_1','task_prompt_id':task,
         'attempt_id':attempt,'source_head':head,'handoff_sha256':handoff,
         'workspace_repo':worktree,'runtime_root':runtime_root,
         'snapshot':snap,'operator_authority_granted':False}
    row['content_sha256']=canonical_digest(row)
    return row


def verify_bound_baseline(row: Mapping, *, task: str, attempt: str, head: str, handoff: str, worktree: str, runtime_root: str) -> dict:
    validate_scope(task=task,attempt=attempt,head=head,handoff=handoff,worktree=worktree,runtime_root=runtime_root)
    if not isinstance(row,dict) or row.get('schema_version')!='cf10_r015_bound_baseline_v0_1': _block('BASELINE_SCHEMA')
    body=dict(row); digest=body.pop('content_sha256',None)
    if digest!=canonical_digest(body): _block('BASELINE_DIGEST')
    for k,v in [('task_prompt_id',task),('attempt_id',attempt),('source_head',head),('handoff_sha256',handoff),('workspace_repo',worktree),('runtime_root',runtime_root)]:
        if body.get(k)!=v: _block('BASELINE_BINDING_'+k.upper())
    if body.get('operator_authority_granted') is not False: _block('BASELINE_AUTHORITY')
    snap=body.get('snapshot')
    if not isinstance(snap,dict): _block('BASELINE_SNAPSHOT')
    from scripts.coordination.control_plane.workspace.cf10_untrusted_worktree_delta_v0_1 import SCHEMA
    if snap.get('schema_version')!=SCHEMA: _block('BASELINE_SNAPSHOT_SCHEMA')
    payload=dict(snap); sh=payload.pop('content_sha256',None)
    if sh!=canonical_digest(payload) or payload.get('git_metadata_consulted') is not False: _block('BASELINE_SNAPSHOT_DIGEST')
    return snap


def evaluate_candidate_delta(*, baseline: Mapping, task: str, attempt: str, head: str,
                             handoff: str, worktree: str, runtime_root: str,
                             supervisor_observation: Mapping|None) -> dict:
    """ALWAYS non-authorizing: observation != kernel-backed production receipt."""
    before=verify_bound_baseline(baseline,task=task,attempt=attempt,head=head,handoff=handoff,
                                 worktree=worktree,runtime_root=runtime_root)
    if not isinstance(supervisor_observation,Mapping): _block('SUPERVISOR_OBSERVATION_MISSING')
    if supervisor_observation.get('attempt_id')!=attempt or supervisor_observation.get('source_head')!=head:
        _block('SUPERVISOR_BINDING_MISMATCH')
    if supervisor_observation.get('production_quiescence_proven') is not False:
        _block('UNTRUSTED_PRODUCTION_QUISCENCE_CLAIM')
    # Safe preview reads worker bytes but cannot assert quiescence and cannot approve them.
    # IMPORTANT: no compare_snapshots(..., process_quiescence_proven=True) here.
    after=delta.snapshot_tree(worktree)
    return {'schema_version':'cf10_r015_candidate_delta_v0_1',
            'attempt_id':attempt,'source_head':head,'handoff_sha256':handoff,
            'pre_sha256':before['content_sha256'], 'post_sha256':after['content_sha256'],
            'candidate_files_changed':before['files']!=after['files'],
            'snapshot_metadata_independent_of_git':True,
            'process_quiescence_proven':False,'result_verification_allowed':False,
            'worker_result_accepted':False,'commit_allowed':False,
            'release_allowed':False,'automatic_retry':False,
            'status':'BLOCKED_PENDING_ROOT_CONTROLLED_QUIESCENCE_RECEIPT'}


def validate_readonly_attempt(*, expected: Path, attempt: Path) -> None:
    """Prevents accidentally directing tests toward an actual attempt."""
    if expected.resolve() != attempt.resolve() or not str(attempt).startswith('/tmp/'):
        _block('FIXTURE_ONLY')
