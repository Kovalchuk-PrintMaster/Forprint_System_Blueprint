"""CF10 r025: conservative post-crash join for a canonical attempted service.

This is read-only, NEVER recovery authority. No systemd start/stop, credentials,
ledger append, claim creation, retry, or production release. Inputs are verified
by caller from independent root-only receipt store, canonical ledger contract,
and trusted kernel/systemd observation (never worker-provided output).
"""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import os
import re
import stat

from scripts.coordination.control_plane import cf10_receipt_ledger_join_review_v0_1 as ledger_join
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as supervisor

SHA40=re.compile(r'[0-9a-f]{40}\Z')
HEX64=re.compile(r'[0-9a-f]{64}\Z')
ATTEMPT=supervisor.ATTEMPT

class RecoveryBlocked(ValueError):pass

def deny(reason): raise RecoveryBlocked('CF10_R025_'+reason)

@dataclass(frozen=True)
class ReadbackIdentity:
    attempt_id:str
    head:str
    handoff_sha256:str
    runtime_root:str
    unit:str

    def validate(self):
        if not isinstance(self.attempt_id,str) or not ATTEMPT.fullmatch(self.attempt_id):deny('ATTEMPT')
        if not isinstance(self.head,str) or not SHA40.fullmatch(self.head):deny('HEAD')
        if not isinstance(self.handoff_sha256,str) or not HEX64.fullmatch(self.handoff_sha256):deny('HANDOFF')
        if self.runtime_root!='/srv/software_development/forprint-worker-runtime':deny('RUNTIME_ROOT')
        if self.unit!=supervisor.unit_for(self.attempt_id,self.head):deny('UNIT_BINDING')
        return True


def _trusted_service(identity:ReadbackIdentity, observation:Mapping|None):
    if observation is None:return {'status':'UNKNOWN','service_checked':False}
    if not isinstance(observation,Mapping):deny('SERVICE_TYPE')
    wanted={'unit','attempt_id','source_head','load_state','active_state',
            'main_pid','control_group','user','group','kill_mode','provenance'}
    if set(observation)!=wanted:deny('SERVICE_FIELDS')
    if (observation['unit']!=identity.unit or observation['attempt_id']!=identity.attempt_id
        or observation['source_head']!=identity.head or observation['provenance']!='ROOT_SYSTEMCTL_SHOW_READBACK'):
        deny('SERVICE_BINDING')
    if observation['load_state'] not in ('loaded','not-found','masked') or observation['active_state'] not in ('active','activating','deactivating','inactive','failed'):
        deny('SERVICE_STATE')
    if type(observation['main_pid']) is not int or observation['main_pid']<0:deny('SERVICE_PID')
    if observation['user'] not in ('forprint-runner','') or observation['group'] not in ('forprint-runner',''):
        deny('SERVICE_USER')
    if observation['kill_mode'] not in ('control-group',''):deny('SERVICE_KILL_MODE')
    group='/system.slice/'+identity.unit
    if observation['active_state'] in ('active','activating','deactivating'):
        if (observation['load_state']!='loaded' or observation['main_pid']<=1
            or observation['control_group']!=group or observation['user']!='forprint-runner'
            or observation['group']!='forprint-runner' or observation['kill_mode']!='control-group'):
            deny('ACTIVE_UNIT_NOT_PROVEN')
        return {'status':'PROCESS_MAY_BE_ACTIVE','service_checked':True}
    if observation['main_pid'] not in (0,) or observation['control_group'] not in ('',group):
        # MainPID gone != whole cgroup quiescent. Ambiguous service state.
        return {'status':'UNKNOWN','service_checked':True}
    return {'status':'NOT_ACTIVE_UNVERIFIED_CGROUP','service_checked':True}


def decide(*,identity:ReadbackIdentity, receipt_summary:Mapping|None,
           ledger_rows:list[dict], service:Mapping|None,
           claim_path_occupied:bool)->dict:
    """Review-only projection. Receipt/ledger/service MUST be independently proven.

    claim_path_occupied comes from trusted root-side O_NOFOLLOW inspection; if
    path exists but receipt cannot be read, it is quarantined, not unclaimed.
    """
    if not isinstance(identity,ReadbackIdentity):deny('IDENTITY')
    identity.validate()
    if type(claim_path_occupied) is not bool:deny('CLAIM_FLAG')
    obs=_trusted_service(identity,service)
    if claim_path_occupied and receipt_summary is None:
        state='QUARANTINE_OCCUPIED_MISSING_OR_CORRUPT_CLAIM'
        cross=None
    else:
        if receipt_summary is not None and not claim_path_occupied:deny('RECEIPT_WITHOUT_CLAIM_PATH')
        try:
            cross=ledger_join.reconcile(attempt_id=identity.attempt_id,
                source_head=identity.head,handoff_sha256=identity.handoff_sha256,
                receipt=receipt_summary,ledger_rows=ledger_rows)
        except (ValueError,TypeError,KeyError) as exc:
            deny('LEDGER_RECEIPT_BINDING:'+type(exc).__name__)
        state=cross['state']
        if obs['status']=='PROCESS_MAY_BE_ACTIVE' and not claim_path_occupied:
            state='QUARANTINE_ORPHAN_SERVICE_NO_ROOT_CLAIM'
        elif obs['status']=='PROCESS_MAY_BE_ACTIVE':
            state='BLOCKED_SYSTEMD_MAY_BE_ACTIVE_REQUIRES_OPERATOR_RECONCILIATION'
        elif obs['status']=='UNKNOWN' and claim_path_occupied:
            state='BLOCKED_CGROUP_OR_SERVICE_UNKNOWN'
        elif state=='UNCLAIMED_NO_LEDGER_FACT_REVIEW_ONLY' and obs['status']=='UNKNOWN':
            state='UNKNOWN_NO_TRUSTED_SYSTEMD_READBACK'
    return {'schema_version':'cf10_r025_postcrash_recovery_review_v0_1',
        'attempt_id':identity.attempt_id,'source_head':identity.head,'unit':identity.unit,
        'state':state,'receipt_ledger_state':cross['state'] if cross else None,
        'service_state':obs['status'],'claim_path_occupied':claim_path_occupied,
        'service_checked':obs['service_checked'],'automatic_retry':False,
        'launch_allowed':False,'stop_allowed':False,'operator_authority_granted':False,
        'worker_result_accepted':False,'release_allowed':False,
        'production_quiescence_proven':False,'manual_review_required':True}


def identity_from_source(*,attempt_id,head,handoff_sha256):
    identity=ReadbackIdentity(attempt_id,head,handoff_sha256,
        '/srv/software_development/forprint-worker-runtime',supervisor.unit_for(attempt_id,head))
    identity.validate()
    return identity


def read_root_claim(*, private_store:Path, identity:ReadbackIdentity,
                    blueprint_root:Path, disposable_fixture:bool=False)->tuple[dict|None,bool]:
    """Read-only receipt adapter. Never infer FREE from an occupied inode.

    Production stores require exact approved durable location and 0700 root mode.
    The only alternative is a disposable isolated fixture outside Blueprint/runtime.
    """
    from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipt
    from scripts.coordination.control_plane import blueprint_durable_storage_v0_1 as paths
    identity.validate()
    private_store=Path(private_store)
    if disposable_fixture:
        parent=private_store.parent
        if (not private_store.is_absolute() or not parent.name.startswith('cf10-r025-fixture-') or not str(parent).startswith(('/var/tmp/','/tmp/'))
            or private_store.name!='receipts' or private_store.is_symlink()
            or parent.is_symlink() or parent.resolve()!=parent):
            deny('DISPOSABLE_SCOPE')
    else:
        paths.require_existing_private_store(private_store,blueprint_root=blueprint_root)
    receipt._check_private_root_dir(private_store)
    claim=private_store/identity.attempt_id
    if claim.is_symlink():
        return (None,True)
    try:st=claim.lstat()
    except FileNotFoundError:return (None,False)
    if not stat.S_ISDIR(st.st_mode) or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=0o700:
        return (None,True)
    try:
        summary=receipt.observe(private_store=private_store,
            attempt_id=identity.attempt_id,expected_head=identity.head)
    except (OSError,ValueError,KeyError,TypeError):
        return (None,True)
    return summary,True
