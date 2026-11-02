"""CF10 r035 root-only immutable witness boundaries and read-only crash projection.

A pinned cgroup FD CANNOT survive controller death or reboot. This records
what was actually established before STARTED/release and after retained
terminal observation. Absent/corrupt evidence is QUARANTINE, never success.
These receipts do not authorize a launch, retry, worker acceptance, or release.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Mapping

from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipts
from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as recovery
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as witness_lib

STORE=Path('/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/control_plane/root_receipts')
PRE='r035_witness_pre.json'
POST='r035_witness_terminal.json'
HASH=re.compile(r'[0-9a-f]{64}\Z')
INV=re.compile(r'[0-9a-f]{32}\Z')

class DurableBoundaryBlocked(RuntimeError):pass

def deny(reason):raise DurableBoundaryBlocked('CF10_R035_'+reason)

def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def canonical(body:dict)->bytes:
    return (json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('ascii')

def _seal(body:dict)->bytes:
    return canonical({**body,'record_sha256':digest(canonical(body))})

def _directory(store:Path,attempt_id:str,head:str,handoff:str,*,fixture:bool=False)->Path:
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    if not binding.ATTEMPT.fullmatch(attempt_id) or not binding.HEAD.fullmatch(head) or not HASH.fullmatch(handoff):
        deny('IDENTITY')
    store=Path(store)
    if fixture:
        if (not store.is_absolute() or not str(store).startswith(('/var/tmp/','/tmp/')) or not store.parent.name.startswith('cf10-r035-fixture-')
                or store.name!='receipts' or '..' in store.parts):deny('FIXTURE_SCOPE')
    elif store!=STORE:deny('PRODUCTION_STORE_PIN')
    try:
        receipts._check_private_root_dir(store)
        attempt=store/attempt_id
        receipts._check_private_root_dir(attempt)
        claim=receipts._read_json(attempt/'0000_claim.json')
        if (claim.get('attempt_id')!=attempt_id or claim.get('source_head')!=head
                or claim.get('handoff_sha256')!=handoff):deny('CLAIM_BINDING')
        receipts.observe(private_store=store,attempt_id=attempt_id,expected_head=head)
    except (OSError,ValueError,KeyError,TypeError,receipts.ReceiptBlocked) as exc:
        deny('ROOT_CLAIM_INVALID_'+type(exc).__name__)
    return attempt

def _create(directory:Path,name:str,data:bytes)->None:
    if name not in (PRE,POST) or len(data)>8192:deny('WRITE_SCOPE')
    dirfd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    fd=None
    try:
        fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=dirfd)
        with os.fdopen(fd,'wb',closefd=False) as f:
            f.write(data);f.flush();os.fsync(fd)
        os.fsync(dirfd)
    except FileExistsError:deny('IMMUTABLE_BOUNDARY_ALREADY_EXISTS_NO_RETRY')
    finally:
        if fd is not None:os.close(fd)
        os.close(dirfd)

def _read(directory:Path,name:str)->dict|None:
    dirfd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        try:fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=dirfd)
        except FileNotFoundError:return None
        try:
            st=os.fstat(fd)
            if (not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=0o600
                    or st.st_nlink!=1 or st.st_size>8192):deny('ROOT_RECORD_INODE')
            raw=os.read(fd,8193)
        finally:os.close(fd)
    finally:os.close(dirfd)
    try:doc=json.loads(raw)
    except (UnicodeError,ValueError):deny('ROOT_RECORD_JSON')
    if not isinstance(doc,dict) or 'record_sha256' not in doc:deny('ROOT_RECORD_SCHEMA')
    checksum=doc.pop('record_sha256')
    if not HASH.fullmatch(str(checksum)) or digest(canonical(doc))!=checksum or raw!=_seal(doc):
        deny('ROOT_RECORD_TAMPER')
    return {**doc,'record_sha256':checksum}

def _ident(spec:binding.BoundedInput,unit:str)->None:
    if not isinstance(spec,binding.BoundedInput):deny('SPEC_TYPE')
    if unit!=binding.unit_for(spec.attempt_id,spec.source_head):deny('UNIT_BINDING')
    if not HASH.fullmatch(spec.baseline_sha256) or not HASH.fullmatch(spec.handoff_sha256):deny('HASH_BINDING')

def record_pre(*,spec:binding.BoundedInput,unit:str,witness,store:Path=STORE,fixture:bool=False)->dict:
    """Must execute after FD arm, before canonical STARTED callback and release."""
    _ident(spec,unit)
    if (type(witness) is not witness_lib.KernelWitness or witness.closed
            or witness.unit!=unit or witness.armed_populated!='1'
            or not INV.fullmatch(witness.invocation_id)):
        deny('WITNESS_NOT_ARMED')
    directory=_directory(store,spec.attempt_id,spec.source_head,spec.handoff_sha256,fixture=fixture)
    body={'schema':'cf10_r035_immutable_witness_boundary_v0_1',
          'event':'ARMED_BEFORE_LEDGER_STARTED_AND_RELEASE',
          'attempt_id':spec.attempt_id,'source_head':spec.source_head,
          'handoff_sha256':spec.handoff_sha256,'baseline_sha256':spec.baseline_sha256,
          'unit':unit,'invocation_id':witness.invocation_id,
          'armed_populated':'1','worker_result_accepted':False,
          'production_quiescence_proven':False,'automatic_retry':False}
    _create(directory,PRE,_seal(body))
    return _read(directory,PRE)

def record_terminal(*,spec:binding.BoundedInput,unit:str,outcome:dict,
                    store:Path=STORE,fixture:bool=False)->dict:
    """After real terminal bridge, before returning outcome to Worker Result pipeline."""
    _ident(spec,unit)
    directory=_directory(store,spec.attempt_id,spec.source_head,spec.handoff_sha256,fixture=fixture)
    pre=_read(directory,PRE)
    if pre is None:deny('PRE_BOUNDARY_ABSENT')
    _validate_pre(pre,spec.attempt_id,spec.source_head,spec.handoff_sha256,spec.baseline_sha256,unit)
    if not isinstance(outcome,dict) or (outcome.get('systemd_unit')!=unit or
            outcome.get('systemd_invocation_id')!=pre['invocation_id'] or
            outcome.get('return_code')!=0 or outcome.get('outcome')!='completed' or
            outcome.get('quiescence_observation')!='PINNED_KERNEL_1_TO_0_RETAINED_SYSTEMD_NON_AUTHORIZING' or
            outcome.get('worker_result_accepted') is not False or
            outcome.get('automatic_retry') is not False):
        deny('TERMINAL_NOT_CANONICAL')
    body={'schema':'cf10_r035_immutable_witness_boundary_v0_1',
          'event':'TERMINAL_CANDIDATE_RECORDED_NOT_WORKER_ACCEPTED',
          'attempt_id':spec.attempt_id,'source_head':spec.source_head,
          'handoff_sha256':spec.handoff_sha256,'baseline_sha256':spec.baseline_sha256,
          'unit':unit,'invocation_id':pre['invocation_id'],'pre_record_sha256':pre['record_sha256'],
          'quiescence_observation':outcome['quiescence_observation'],
          'worker_result_accepted':False,'production_quiescence_proven':False,
          'automatic_retry':False}
    _create(directory,POST,_seal(body))
    return _read(directory,POST)

def _validate_pre(pre,attempt,head,handoff,baseline,unit):
    expected={'schema','event','attempt_id','source_head','handoff_sha256','baseline_sha256',
              'unit','invocation_id','armed_populated','worker_result_accepted',
              'production_quiescence_proven','automatic_retry','record_sha256'}
    if (set(pre)!=expected or pre['schema']!='cf10_r035_immutable_witness_boundary_v0_1'
       or pre['event']!='ARMED_BEFORE_LEDGER_STARTED_AND_RELEASE'
       or any(pre[k]!=v for k,v in [('attempt_id',attempt),('source_head',head),('handoff_sha256',handoff),
                                    ('baseline_sha256',baseline),('unit',unit),('armed_populated','1')])
       or not INV.fullmatch(str(pre['invocation_id']))
       or any(pre[k] is not False for k in ('worker_result_accepted','production_quiescence_proven','automatic_retry'))):
        deny('PRE_BOUNDARY_BINDING')

def inspect(*,identity:recovery.ReadbackIdentity,baseline_sha256:str,
            store:Path=STORE,fixture:bool=False)->dict:
    """Durable projection after crash/reboot; NEVER infers a process is gone."""
    identity.validate()
    if not isinstance(baseline_sha256,str) or not HASH.fullmatch(baseline_sha256):deny('BASELINE')
    directory=_directory(store,identity.attempt_id,identity.head,identity.handoff_sha256,fixture=fixture)
    pre=_read(directory,PRE)
    post=_read(directory,POST)
    if pre is None:
        if post is not None:deny('TERMINAL_WITHOUT_PRE')
        state='BLOCKED_NO_DURABLE_WITNESS_BOUNDARY'
    else:
        _validate_pre(pre,identity.attempt_id,identity.head,identity.handoff_sha256,baseline_sha256,identity.unit)
        if post is None:
            state='BLOCKED_CONTROLLER_INTERRUPTED_OR_TERMINAL_NOT_RECORDED'
        else:
            expected={'schema','event','attempt_id','source_head','handoff_sha256','baseline_sha256',
                      'unit','invocation_id','pre_record_sha256','quiescence_observation',
                      'worker_result_accepted','production_quiescence_proven','automatic_retry','record_sha256'}
            if (set(post)!=expected or post['schema']!='cf10_r035_immutable_witness_boundary_v0_1'
                or post['event']!='TERMINAL_CANDIDATE_RECORDED_NOT_WORKER_ACCEPTED'
                or any(post[k]!=v for k,v in [('attempt_id',identity.attempt_id),('source_head',identity.head),
                    ('handoff_sha256',identity.handoff_sha256),('baseline_sha256',baseline_sha256),
                    ('unit',identity.unit),('invocation_id',pre['invocation_id']),
                    ('pre_record_sha256',pre['record_sha256']),
                    ('quiescence_observation','PINNED_KERNEL_1_TO_0_RETAINED_SYSTEMD_NON_AUTHORIZING')])
                or any(post[k] is not False for k in ('worker_result_accepted','production_quiescence_proven','automatic_retry'))):
                deny('TERMINAL_BOUNDARY_BINDING')
            state='TERMINAL_RECORD_PRESENT_NEEDS_LEDGER_AND_INDEPENDENT_RESULT_VERIFIER'
    return {'schema':'cf10_r035_crash_reboot_durable_review_v0_1',
        'attempt_id':identity.attempt_id,'source_head':identity.head,'unit':identity.unit,
        'state':state,'witness_armed_recorded':pre is not None,
        'terminal_candidate_recorded':post is not None,
        'pre_record_sha256':pre['record_sha256'] if pre else None,
        'terminal_record_sha256':post['record_sha256'] if post else None,
        'root_owned_records_only':True,'read_only':True,'worker_result_accepted':False,
        'production_quiescence_proven':False,'automatic_retry':False,'launch_allowed':False,
        'release_allowed':False,'manual_review_required':True}

def join_review(*,identity:recovery.ReadbackIdentity,baseline_sha256:str,
                receipt_summary:Mapping|None,ledger_rows:list[dict],service:Mapping|None,
                claim_path_occupied:bool,store:Path=STORE,fixture:bool=False)->dict:
    """Conservatively join independent caller-verified r025 inputs; NO authority."""
    durable=inspect(identity=identity,baseline_sha256=baseline_sha256,store=store,fixture=fixture)
    prior=recovery.decide(identity=identity,receipt_summary=receipt_summary,
                          ledger_rows=ledger_rows,service=service,
                          claim_path_occupied=claim_path_occupied)
    if prior['service_state']=='PROCESS_MAY_BE_ACTIVE':
        result='BLOCKED_PROCESS_MAY_STILL_BE_RUNNING'
    elif not claim_path_occupied or receipt_summary is None:
        result='BLOCKED_CLAIM_OR_RECEIPT_UNCERTAIN'
    elif not durable['terminal_candidate_recorded']:
        result='BLOCKED_TERMINAL_UNPROVEN_AFTER_CRASH_OR_REBOOT'
    else:
        result='BLOCKED_TERMINAL_CANDIDATE_PENDING_INDEPENDENT_CROSS_BOUNDARY_VERIFICATION'
    return {**durable,'state':result,'r025_state':prior['state'],
            'r025_service_state':prior['service_state'],
            'worker_result_accepted':False,'production_quiescence_proven':False,
            'automatic_retry':False,'launch_allowed':False,'release_allowed':False,
            'manual_review_required':True}
