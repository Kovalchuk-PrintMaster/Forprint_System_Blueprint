"""CF-10 independent, read-only cross-boundary Worker Result candidate check.

Uses canonical root-owned r035 pre/terminal receipts + existing strict S4
result validators. Does not modify a ledger, retry, accept, promote, release,
mark a production attempt quiescent or grant operator/Worker authority.

Inputs such as origin/context/ledger require *canonical upstream provenance*;
this is a second bounded cross-check, not a replacement for finalizer checks.
"""
from __future__ import annotations
import os
from collections.abc import Mapping
from pathlib import Path
import re
import stat
from typing import Callable
import yaml

from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as recovery
from scripts.coordination.control_plane.worker_runtime import cf10_r035_durable_witness_boundary_v0_1 as durable

RUNTIME=Path('/srv/software_development/forprint-worker-runtime')
BLUEPRINT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
HEX64=re.compile(r'[a-f0-9]{64}\Z')

class CrosscheckBlocked(RuntimeError):pass

def deny(reason):raise CrosscheckBlocked('CF10_R036_'+reason)

class _NoDuplicateSafeLoader(yaml.SafeLoader):pass

def _construct_mapping(loader,node):
    mapping={}
    for key_node,value_node in node.value:
        key=loader.construct_object(key_node,deep=True)
        if not isinstance(key,str) or key in mapping:deny('RESULT_DUPLICATE_OR_NONSTRING_KEY')
        mapping[key]=loader.construct_object(value_node,deep=True)
    return mapping

_NoDuplicateSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,_construct_mapping)

def _file(path:Path,root:Path)->dict:
    """Read a bounded on-disk result; caller cannot supply an in-memory Worker claim."""
    p=Path(path)
    if p!=root/'result'/'worker_result.yaml' or not root.is_absolute() or '..' in root.parts:
        deny('RESULT_PATH_SCOPE')
    # No symlink components below attempt; no missing/nonregular/aliased file.
    for parent in (root,root/'result'):
        if parent.is_symlink() or not parent.is_dir():deny('RESULT_PARENT')
    try:
        fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    except FileNotFoundError:deny('RESULT_MISSING')
    try:
        s=os.fstat(fd)
        if (not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_nlink!=1
                or s.st_size==0 or s.st_size>524288 or stat.S_IMODE(s.st_mode)&0o022):
            deny('RESULT_INODE_OR_PERMISSIONS')
        raw=os.read(fd,524289)
    finally:os.close(fd)
    if len(raw)>524288:deny('RESULT_OVERSIZE')
    try:result=yaml.load(raw.decode('utf-8','strict'),Loader=_NoDuplicateSafeLoader)
    except (yaml.YAMLError,UnicodeError,ValueError,TypeError) as e:
        deny('RESULT_PARSE_'+type(e).__name__)
    if not isinstance(result,dict):deny('RESULT_NOT_MAPPING')
    return result

def _validate_identity(result:dict,identity:recovery.ReadbackIdentity,baseline:str,
                       origin:dict,context:dict):
    if result.get('attempt_id')!=identity.attempt_id:deny('RESULT_ATTEMPT_MISMATCH')
    if result.get('status') not in ('PASS','COMPLETED'):deny('RESULT_NOT_SUCCESS')
    if result.get('handoff_manifest_sha256')!=identity.handoff_sha256:deny('RESULT_HANDOFF_MISMATCH')
    if not isinstance(origin,dict) or origin.get('handoff_manifest_sha256')!=identity.handoff_sha256:
        deny('ORIGIN_BINDING')
    if not isinstance(context,dict) or context.get('handoff_manifest_sha256')!=identity.handoff_sha256:
        deny('GOVERNED_CONTEXT_BINDING')
    if not isinstance(baseline,str) or not HEX64.fullmatch(baseline):deny('BASELINE_HASH')

def _assess(*,identity:recovery.ReadbackIdentity,baseline_sha256:str,
            attempt_root:Path,origin_manifest:dict,governed_worker_context:dict,
            receipt_summary:Mapping|None,ledger_rows:list[dict],service:Mapping|None,
            claim_path_occupied:bool,envelope_validator:Callable,resume_validator:Callable,
            store:Path=durable.STORE,fixture:bool=False)->dict:
    """Test seam is non-authorizing; real entrypoint pins genuine validators."""
    identity.validate()
    attempt_root=Path(attempt_root)
    if fixture:
        if (not attempt_root.is_absolute() or not str(attempt_root).startswith('/tmp/') and
                not str(attempt_root).startswith('/var/tmp/')):deny('FIXTURE_ROOT_SCOPE')
    elif attempt_root!=RUNTIME/'forprint_system_blueprint'/'worker-01'/identity.attempt_id:
        deny('CANONICAL_ATTEMPT_ROOT')
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    joint=durable.join_review(identity=identity,baseline_sha256=baseline_sha256,
        receipt_summary=receipt_summary,ledger_rows=ledger_rows,service=service,
        claim_path_occupied=claim_path_occupied,store=store,fixture=fixture)
    durable_state=joint
    base={'schema':'cf10_r036_independent_result_crosscheck_v0_1',
          'attempt_id':identity.attempt_id,'source_head':identity.head,'unit':identity.unit,
          'durable_state':durable_state['state'],
          'r025_state':joint['r025_state'],'r025_service_state':joint['r025_service_state'],
          'pre_record_sha256':durable_state['pre_record_sha256'],
          'terminal_record_sha256':durable_state['terminal_record_sha256'],
          'read_only':True,'automatic_retry':False,'worker_result_accepted':False,
          'production_quiescence_proven':False,'launch_allowed':False,
          'release_allowed':False,'candidate_promotion_allowed':False,
          'manual_review_required':True}
    if not durable_state['terminal_candidate_recorded']:
        return {**base,'status':'BLOCKED_TERMINAL_NOT_DURABLE','existing_verifier_checked':False}
    if (not claim_path_occupied or receipt_summary is None or not isinstance(ledger_rows,list)
            or len(ledger_rows)!=1 or ledger_rows[0].get('attempt_stage')!='STARTED'
            or ledger_rows[0].get('result_state')!='PENDING'
            or joint['r025_service_state']!='NOT_ACTIVE_UNVERIFIED_CGROUP'
            or joint['state']!='BLOCKED_TERMINAL_CANDIDATE_PENDING_INDEPENDENT_CROSS_BOUNDARY_VERIFICATION'):
        return {**base,'status':'BLOCKED_CLAIM_LEDGER_OR_SERVICE_UNVERIFIED',
                'existing_verifier_checked':False}
    result=_file(attempt_root/'result'/'worker_result.yaml',attempt_root)
    _validate_identity(result,identity,baseline_sha256,origin_manifest,governed_worker_context)
    try:
        envelope_errors=envelope_validator(result,origin_manifest)
        resume_errors=resume_validator(result,origin_manifest,governed_worker_context)
    except (Exception,) as exc:
        deny('CANONICAL_VALIDATOR_ERROR_'+type(exc).__name__)
    if not isinstance(envelope_errors,list) or not isinstance(resume_errors,list):
        deny('CANONICAL_VALIDATOR_RESULT_TYPE')
    if envelope_errors or resume_errors:
        return {**base,'status':'BLOCKED_CANONICAL_HANDOFF_OR_RESUME_VALIDATION',
                'existing_verifier_checked':True,'verification_error_count':len(envelope_errors)+len(resume_errors)}
    return {**base,'status':'VERIFIED_RESULT_CANDIDATE_PENDING_CANONICAL_LEDGER_FINALIZER',
            'existing_verifier_checked':True,'verification_error_count':0}

def inspect(*,identity:recovery.ReadbackIdentity,baseline_sha256:str,
            attempt_root:Path,origin_manifest:dict,governed_worker_context:dict,
            receipt_summary:Mapping|None,ledger_rows:list[dict],service:Mapping|None,
            claim_path_occupied:bool)->dict:
    """Root-only, production-pinned, read-only. NEVER accepts Worker Result."""
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    from scripts.coordination.control_plane.worker_runtime import worker_result_return as actual
    def envelope(result,origin):
        return actual.validate_result_envelope(result,origin,root=BLUEPRINT)
    def resume(result,origin,context):
        s4=actual._s4_resume_origin(governed_worker_context=context,origin_manifest=origin)
        return actual.validate_resume(result,s4)
    return _assess(identity=identity,baseline_sha256=baseline_sha256,
                   attempt_root=attempt_root,origin_manifest=origin_manifest,
                   governed_worker_context=governed_worker_context,
                   receipt_summary=receipt_summary,ledger_rows=ledger_rows,
                   service=service,claim_path_occupied=claim_path_occupied,
                   envelope_validator=envelope,resume_validator=resume)
