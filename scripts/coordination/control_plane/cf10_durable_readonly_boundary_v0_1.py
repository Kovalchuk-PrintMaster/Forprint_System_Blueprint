"""CF-10 permanent-storage read-only facade, non-authorizing.

Only trusted Blueprint source imports this facade; it never spawns a process,
opens a credential, issues a claim, or accepts a Worker Result. No tmp/ path
may be used for canonical state. Existing review primitives retain disposable
fixture support but must not be used as a production activation API.
"""
from __future__ import annotations
from pathlib import Path
import re
from typing import Mapping

from scripts.coordination.control_plane import blueprint_durable_storage_v0_1 as storage
from scripts.coordination.control_plane import cf10_receipt_ledger_join_review_v0_1 as join

HEAD = re.compile(r"[a-f0-9]{40}\Z")
HASH = re.compile(r"[a-f0-9]{64}\Z")
ATTEMPT = re.compile(r"cf10-[A-Za-z0-9_-]{3,80}-a[0-9]{3,5}\Z")

class DurableBoundaryBlocked(ValueError):
    pass

def _deny(reason: str):
    raise DurableBoundaryBlocked("CF10_R022_"+reason)

def _root() -> Path:
    # Installed in Git-controlled Blueprint (never import from ZIP staging).
    here = Path(__file__).resolve()
    return here.parents[3]

def validate_durable_scope(*, attempt_id: str, source_head: str,
                           handoff_sha256: str, runtime_root: str,
                           workspace_repo: str, receipt_store: str) -> dict:
    if not isinstance(attempt_id,str) or not ATTEMPT.fullmatch(attempt_id): _deny('ATTEMPT')
    if not isinstance(source_head,str) or not HEAD.fullmatch(source_head): _deny('HEAD')
    if not isinstance(handoff_sha256,str) or not HASH.fullmatch(handoff_sha256): _deny('HANDOFF')
    root=_root()
    try:
        runtime=storage.require_runtime_root(runtime_root,blueprint_root=root)
        repo=storage.require_worker_workspace(workspace_repo,blueprint_root=root,attempt_id=attempt_id)
        store=storage.require_root_receipt_store(receipt_store,blueprint_root=root)
    except (storage.StorageBoundaryBlocked, TypeError, ValueError) as exc:
        _deny('UNAPPROVED_OR_TEMP_STORAGE')
    return {'schema_version':'cf10_r022_durable_scope_v0_1',
            'attempt_id':attempt_id,'source_head':source_head,
            'handoff_sha256':handoff_sha256,'runtime_root':str(runtime),
            'workspace_repo':str(repo),'receipt_store':str(store),
            'status':'PASS_NON_AUTHORIZING_DURABLE_SCOPE',
            'claim_issued':False,'worker_launched':False,
            'worker_result_accepted':False,'release_allowed':False}

def review_ledger_only(*, scope: Mapping, receipt: Mapping | None,
                       ledger_rows: list, supervisor_observation: Mapping | None = None) -> dict:
    if not isinstance(scope,dict) or scope.get('schema_version')!='cf10_r022_durable_scope_v0_1':
        _deny('SCOPE')
    bound=validate_durable_scope(attempt_id=scope['attempt_id'],source_head=scope['source_head'],
        handoff_sha256=scope['handoff_sha256'],runtime_root=scope['runtime_root'],
        workspace_repo=scope['workspace_repo'],receipt_store=scope['receipt_store'])
    if bound != scope: _deny('SCOPE_TAMPER')
    projection=join.reconcile(attempt_id=scope['attempt_id'],source_head=scope['source_head'],
         handoff_sha256=scope['handoff_sha256'],receipt=receipt,ledger_rows=ledger_rows,
         supervisor_observation=supervisor_observation)
    return {**projection,'durable_storage_scope_verified':True,
            'worker_launched':False,'release_allowed':False,
            'production_cutover_completed':False}
