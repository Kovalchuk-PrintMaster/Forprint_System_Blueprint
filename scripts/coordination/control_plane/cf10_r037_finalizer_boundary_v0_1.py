"""Root-only, read-only gate immediately before CF10 canonical terminal finalization.

Connects genuine canonical frozen evidence, root claim and systemd/kernel
readback to the existing r036 independent candidate checker. Never accepts,
retries, appends ledger, changes systemd, or grants production launch authority.
"""
from __future__ import annotations
import os
from pathlib import Path
from collections.abc import Mapping

from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as recovery
from scripts.coordination.control_plane import cf10_r026_trusted_systemd_readback_v0_1 as trusted
from scripts.coordination.control_plane.worker_runtime import cf10_r035_durable_witness_boundary_v0_1 as durable
from scripts.coordination.control_plane.worker_runtime import cf10_r036_independent_result_crosscheck_v0_1 as crosscheck

ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUNTIME=Path('/srv/software_development/forprint-worker-runtime')
EXPECTED='VERIFIED_RESULT_CANDIDATE_PENDING_CANONICAL_LEDGER_FINALIZER'

class FinalizerBoundaryBlocked(RuntimeError): pass

def deny(reason):
    raise FinalizerBoundaryBlocked('CF10_R037_FINALIZER_'+reason)

def review(*,canonical:Path,attempt:Path,attempt_id:str,
           source_state:Mapping,baseline:Mapping,origin_manifest:dict,
           governed_context:dict,ledger_rows:list[dict])->dict:
    """Production-pinned review; all I/O is read-only, and acceptance is impossible.

    Inputs originate in canonical advance_cycle only after existing source,
    Handoff, baseline and ledger validation. We independently re-bind every
    stable identifier before fetching privileged root/systemd observations.
    """
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    if canonical!=ROOT or canonical.is_symlink():deny('SOURCE_ROOT')
    if (not isinstance(attempt_id,str) or
        attempt!=RUNTIME/'forprint_system_blueprint'/'worker-01'/attempt_id or
        attempt.is_symlink() or not attempt.is_dir()):deny('ATTEMPT_ROOT')
    if not isinstance(source_state,Mapping) or not isinstance(baseline,Mapping):
        deny('SOURCE_AND_BASELINE')
    head=source_state.get('git_head')
    manifest_hash=origin_manifest.get('handoff_manifest_sha256') if isinstance(origin_manifest,dict) else None
    baseline_hash=baseline.get('baseline_fingerprint_sha256')
    if not isinstance(governed_context,dict) or governed_context.get('handoff_manifest_sha256')!=manifest_hash:
        deny('HANDOFF_CONTEXT_DRIFT')
    try:
        identity=recovery.identity_from_source(attempt_id=attempt_id,head=head,
                                               handoff_sha256=manifest_hash)
    except (ValueError,TypeError,KeyError) as exc:
        deny('IDENTITY_'+type(exc).__name__)
    if (not isinstance(ledger_rows,list) or len(ledger_rows)!=1 or
            ledger_rows[0].get('attempt_id')!=attempt_id or
            ledger_rows[0].get('attempt_stage')!='STARTED' or
            ledger_rows[0].get('result_state')!='PENDING'):
        deny('STARTED_PENDING_REQUIRED')
    # Receipt is root-owned and occupied claims are never interpreted as free.
    try:
        receipt,occupied=recovery.read_root_claim(
            private_store=durable.STORE,identity=identity,blueprint_root=canonical)
    except (OSError,ValueError,TypeError) as exc:
        deny('ROOT_CLAIM_'+type(exc).__name__)
    if not occupied or receipt is None:deny('CLAIM_NOT_VERIFIABLE')
    try:
        observation=trusted.collect(identity)
    except (OSError,ValueError,RuntimeError,TypeError) as exc:
        deny('TRUSTED_READBACK_'+type(exc).__name__)
    # A current kernel report of potentially running processes is never a
    # candidate, even if an old immutable terminal proof exists.
    if observation['kernel']['cgroup_state'] in ('POPULATED','INACTIVE_BUT_POPULATED'):
        deny('LIVE_CGROUP_NOT_TERMINAL')
    if observation['kernel']['cgroup_state'] not in (
            'EMPTY_AT_SAMPLE','REMOVED_NOT_PROOF','UNKNOWN_NO_EVENTS','UNKNOWN_NO_CONTROL_GROUP'):
        deny('KERNEL_STATE_UNKNOWN')
    try:
        result=crosscheck.inspect(identity=identity,baseline_sha256=baseline_hash,
            attempt_root=attempt,origin_manifest=origin_manifest,
            governed_worker_context=governed_context,receipt_summary=receipt,
            ledger_rows=ledger_rows,service=observation['systemctl'],
            claim_path_occupied=occupied)
    except (OSError,ValueError,RuntimeError,TypeError,KeyError) as exc:
        deny('CROSS_BOUNDARY_'+type(exc).__name__)
    if (result.get('status')!=EXPECTED or result.get('existing_verifier_checked') is not True or
            result.get('worker_result_accepted') is not False or
            result.get('automatic_retry') is not False or
            result.get('release_allowed') is not False or
            not result.get('pre_record_sha256') or not result.get('terminal_record_sha256')):
        deny('CANDIDATE_NOT_VERIFIED')
    return {'status':EXPECTED,'attempt_id':attempt_id,
            'pre_record_sha256':result['pre_record_sha256'],
            'terminal_record_sha256':result['terminal_record_sha256'],
            'worker_result_accepted':False,'automatic_retry':False,
            'release_allowed':False,'read_only':True}
