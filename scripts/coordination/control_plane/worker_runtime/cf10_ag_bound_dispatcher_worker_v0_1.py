#!/usr/bin/env python3
"""AG: actual canonical Dispatcher API dry-decision -> nonce-bound AE disposable Worker.

Uses the real CF09/CF10 preparation/ACK validator/explicit-decision APIs and
AE's already proven physical delegated Worker systemd lifecycle. The ACK is
an *automatic exact echo* FOR A DISPOSABLE REHEARSAL ONLY, NOT a human or
independent assistant approval. The decision is never passed to a production
launcher, PAM owner claim, durable ledger, or actual live provider.

No tokens, network, production claims, canonical attempt ledger append, or
production release. Existing canonical implementations are reused verbatim.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
from collections.abc import Mapping

SCHEMA='cf10_ag_disposable_dispatcher_bound_worker_v0_1'
TASK='cf10-verification-tier-self-hardening-v0-1'
GATES=['G1','G2','G3','G4','G5']
ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUN=Path('/run')
FINGERPRINT='9e17680295581ff07bc2ae913a96fdc4cf86c88be60078ba03d1866ab3d9792d'
UNIT=re.compile(r'forprint-cf10-batchad-[a-f0-9]{16}\.service\Z')
ATTEMPT=re.compile(r'cf10-u180j-a[0-9]{9}\Z')
SHA64=re.compile(r'[0-9a-f]{64}\Z')

class AGHold(RuntimeError):pass

def deny(why):raise AGHold('CF10_AG_HOLD_'+why)

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest()

def _map(obj,fields=None):
    if not isinstance(obj,Mapping):deny('NOT_MAPPING')
    if fields is not None and set(obj)!=set(fields):deny('SCHEMA_DRIFT')
    return obj

def _safe_preview(*,prepared,ack,ready,decision,attempt_id,source_fingerprint):
    """Treat exact echoed ACK and synthetic explicit decision as review-only."""
    for record in (prepared,ack,ready,decision):_map(record)
    if type(attempt_id) is not str or not ATTEMPT.fullmatch(attempt_id):deny('ATTEMPT')
    if type(source_fingerprint) is not str or not SHA64.fullmatch(source_fingerprint):deny('FINGERPRINT')
    if (prepared.get('state')!='AWAITING_ASSISTANT_ACK' or
        prepared.get('assistant_ack_validated') is not False or
        prepared.get('task_prompt_id')!=TASK or prepared.get('worker_id')!= 'worker-01' or
        prepared.get('attempt_id')!=attempt_id):deny('PREPARED')
    auth=_map(prepared.get('authority'))
    if any(auth.get(k) is not False for k in (
         'execution_authority_granted','dispatch_authority_granted',
         'worker_dispatch_performed','external_dispatch_allowed','release_allowed',
         'push_allowed','merge_allowed')):deny('PREPARED_AUTHORITY')
    if (ack.get('freshness_ack',{}).get('attempt_id')!=attempt_id or
        ack.get('freshness_ack',{}).get('source_state_fingerprint')!=source_fingerprint or
        ack.get('freshness_ack',{}).get('worker_id')!='worker-01' or
        ack.get('authority_ack',{}).get('authority_widening') is not False or
        ack.get('launch_mode')!='TASK_EXECUTION'):deny('ACK_BOUNDARY')
    if (ready.get('state')!='READY_FOR_EXPLICIT_DISPATCH' or
        ready.get('assistant_ack_validated') is not True or
        ready.get('task_prompt_id')!=TASK or ready.get('attempt_id')!=attempt_id):deny('READY')
    rb=_map(decision.get('binding'))
    if (decision.get('decision')!='ALLOW_EXACT_CF10_TRAINING_WORKER_LAUNCH' or
        decision.get('assistant_ack_validated') is not True or
        decision.get('explicit_dispatch_decision_recorded') is not True or
        decision.get('worker_process_launch_allowed') is not True or
        rb.get('attempt_id')!=attempt_id or rb.get('worker_id')!='worker-01' or
        rb.get('task_prompt_id')!=TASK or rb.get('source_state_fingerprint')!=source_fingerprint or
        rb.get('runtime_provider')!='github_copilot_cli' or rb.get('runtime_model')!='auto'):
        deny('EXPLICIT_DECISION_PREVIEW')
    if any(decision.get(k) is not False for k in (
        'external_dispatch_allowed','release_allowed','push_allowed','merge_allowed',
        'foreign_repository_write_allowed','automatic_accept_allowed','grants_broad_dispatch_authority')):
        deny('DECISION_ESCALATION')
    ctx=rb.get('governed_worker_context_sha256')
    if type(ctx) is not str or not SHA64.fullmatch(ctx) or ctx!=ready.get('governed_worker_context_sha256'):
        deny('GOVERNED_CONTEXT')
    if (type(decision.get('decision_id')) is not str or
        not SHA64.fullmatch(decision['decision_id']) or
        decision['decision_id']!=digest(dict(rb))):
        deny('DECISION_ID_NOT_MATCHING_CANONICAL_BINDING')
    identity=digest({'attempt_id':attempt_id,'task':TASK,'context_sha256':ctx,
                     'source_fingerprint':source_fingerprint,'decision_id':decision.get('decision_id')})
    return {'state':'CANONICAL_API_DECISION_PREVIEW_ONLY','task_id':TASK,'work_id':'u180j',
            'attempt_id_digest':hashlib.sha256(attempt_id.encode()).hexdigest(),
            'preview_identity_sha256':identity,'governed_context_sha256':ctx,
            'exact_generated_ack_checked':True,'ack_from_independent_assistant':False,
            'production_owner_auth':False,'claim_consumed':False,'canonical_worker_released':False,
            'can_launch_only_disposable_ae_after_review':True}

def disposable_nonce(preview_sha256:str,salt_hex:str)->str:
    """Synthetic-only derivation binds a fresh AE nonce to the exact decision.

    Salt is NOT an auth secret. It is emitted in evidence so the binding can be
    independently recomputed. AE validates/executes this nonce as a real byte
    input to its unchanged root IPC, anchor, and synthetic child protocol.
    """
    if (type(preview_sha256) is not str or SHA64.fullmatch(preview_sha256) is None or
            type(salt_hex) is not str or SHA64.fullmatch(salt_hex) is None):
        deny('DISPOSABLE_NONCE_INPUT')
    return hashlib.sha256(b'CF10_AG_DISPOSABLE_DECISION_NONCE_V1\0'+
                          bytes.fromhex(preview_sha256)+bytes.fromhex(salt_hex)).hexdigest()


def join(*,preview,physical,salt_hex:str)->dict:
    """Strict causal join: canonical decision -> nonce -> physical child digest.

    Not a production authorization. Kernel proof is accepted only from AE's
    root-verified physical result, not from a caller-provided 'success' flag.
    """
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_ad_disposable_worker_child_v0_1 as child)
    a=_map(preview);p=_map(physical)
    if (a.get('state')!='CANONICAL_API_DECISION_PREVIEW_ONLY' or
        a.get('exact_generated_ack_checked') is not True or
        a.get('ack_from_independent_assistant') is not False or
        a.get('claim_consumed') is not False or
        a.get('canonical_worker_released') is not False or
        a.get('task_id')!=TASK or
        type(a.get('preview_identity_sha256')) is not str or
        SHA64.fullmatch(a['preview_identity_sha256']) is None):
        deny('PREVIEW_NOT_BOUNDED')
    nonce=disposable_nonce(a['preview_identity_sha256'],salt_hex)
    commitment=hashlib.sha256(nonce.encode('ascii')).hexdigest()
    # AE root controller reports the EXACT nonce used in systemd/Worker IPC.
    nonce_row=p.get('nonce_binding')
    if (not isinstance(nonce_row,Mapping) or
        set(nonce_row)!={'disposable_external_nonce_used','nonce_sha256'} or
        nonce_row.get('disposable_external_nonce_used') is not True or
        nonce_row.get('nonce_sha256')!=commitment):
        deny('DISPATCH_DECISION_NOT_BOUND_TO_WORKER_NONCE')
    term=_map(p.get('terminal'));kernel=_map(p.get('kernel'))
    if (p.get('schema')!='cf10_ae_physical_delegated_leaf_v0_1' or
        p.get('status')!='PASS_DISPOSABLE_DELEGATED_WORKER_IPC_KERNEL_TERMINAL' or
        p.get('stage')!='STOPPED_AND_TERMINAL_VERIFIED' or
        p.get('gates_open')!=GATES or
        p.get('canonical_binding',{}).get('task_id')!=TASK or
        p.get('canonical_binding',{}).get('production_dispatch_performed') is not False or
        p.get('canonical_binding',{}).get('worker_claim_consumed') is not False or
        p.get('runtime_cleanup')!='PASS_DISPOSABLE_ONLY'):
        deny('PHYSICAL_STATUS')
    if (not isinstance(p.get('unit'),str) or UNIT.fullmatch(p['unit']) is None or
        term.get('unit')!=p['unit'] or
        term.get('canonical_task_binding')!=TASK or
        term.get('worker_result_verified_by_root') is not True or
        term.get('kernel_leaf_transition')!='1_TO_0' or
        term.get('parent_anchor_held_until_kernel_zero') is not True or
        term.get('retained_systemd') is not True or
        term.get('stopped_readback') is not True or
        term.get('worker_pid')!=p.get('worker_pid') or
        term.get('anchor_pid')!=p.get('anchor',{}).get('pid') or
        term.get('held_invocation_id')!=p.get('anchor',{}).get('invocation_id') or
        any(term.get(x) is not False for x in ('production_claim_consumed',
             'production_ledger_written','production_result_acceptance','canonical_dispatcher_release',
             'provider_inference','provider_credentials','external_egress'))):
        deny('TERMINAL_EVIDENCE')
    if (kernel.get('observation')!='PINNED_DELEGATED_LEAF_FD' or
        kernel.get('samples')!=['1','0'] or
        kernel.get('transition')!='1_TO_0' or
        kernel.get('parent_anchor_populated')!='1' or
        kernel.get('invocation_id')!=term.get('held_invocation_id') or
        kernel.get('unit')!=p.get('unit') or
        kernel.get('leaf_name')!='cf10-actual-worker'):
        deny('KERNEL_EVIDENCE')
    expected_result=child.worker_digest(TASK,nonce)
    result=_map(p.get('result'))
    if (p.get('poststop',{}).get('active')!='inactive' or
        p.get('poststop',{}).get('main_pid')!='0' or
        p.get('poststop',{}).get('result')!='success' or
        result.get('result_verified_by_root') is not True or
        result.get('model_inference_executed') is not False or
        result.get('worker_result_accepted') is not False or
        result.get('canonical_result_ledger_written') is not False or
        result.get('synthetic_result_digest')!=expected_result or
        term.get('result_sha256')!=expected_result):
        deny('CHILD_RESULT_NOT_BOUND_TO_DECISION')
    response={'schema':SCHEMA,
       'status':'PASS_CANONICAL_DISPATCHER_NONCE_BOUND_TO_PHYSICAL_TERMINAL',
       'canonical_api_prepare_ack_validate_explicit_preview':True,
       'synthetic_ack_not_owner_authorization':True,
       'physical_worker_ipc_result_verified':True,
       'real_kernel_leaf_1_to_0':True,'retained_systemd_stop_verified':True,
       'task_id':TASK,'work_id':'u180j',
       'preview_identity_sha256':a['preview_identity_sha256'],
       'lab_salt_hex':salt_hex, 'nonce_commitment_sha256':commitment,
       'nonce_binding_verified_against_child_digest':True,
       'physical_result_sha256':expected_result,
       'physical_invocation_id':term['held_invocation_id'],
       'physical_unit':p['unit'],'gates_open':list(GATES),
       'canonical_production_dispatch_performed':False,'canonical_worker_claim_consumed':False,
       'production_result_accepted':False,'live_worker':False,'real_copilot_inference':False,
       'provider_credentials_used':False,'external_provider_egress':False,
       'automatic_retry':False}
    response['join_sha256']=digest(response)
    return response

def _scratch_dir()->Path:
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    p=RUN/('forprint-cf10-ag-'+secrets.token_hex(12))
    if p.exists() or p.is_symlink():deny('RUN_COLLISION')
    p.mkdir(mode=0o700)
    st=p.lstat()
    if p.is_symlink() or not stat.S_ISDIR(st.st_mode) or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=0o700:
        deny('RUN_PERMISSIONS')
    return p

def _clean_scratch(p:Path)->None:
    if (not isinstance(p,Path) or p.parent!=RUN or not p.name.startswith('forprint-cf10-ag-') or
        p.is_symlink() or not p.is_dir() or p.lstat().st_uid!=0 or
        stat.S_IMODE(p.lstat().st_mode)!=0o700):deny('SCRATCH_SCOPE')
    shutil.rmtree(p)


def _phase(label:str,action,**kwargs):
    """Expose only failed phase and exception *kind*, never private contents."""
    try:return action(**kwargs)
    except AGHold:raise
    except BaseException as exc:deny(label+'_'+type(exc).__name__)

def run_with_apis(*,training,ae,root:Path,scratch:Path,attempt_id:str,
                  source_fingerprint:str=FINGERPRINT, offline_copilot_probe:bool=False)->dict:
    """Injected APIs facilitate offline tests, not a production entrypoint."""
    if type(offline_copilot_probe) is not bool:deny('OFFLINE_PROBE_TYPE')
    if not ATTEMPT.fullmatch(attempt_id) or scratch.is_symlink() or not scratch.is_dir():deny('RUN_INPUT')
    ledger=scratch/'empty-ledger';ledger.mkdir(mode=0o700)
    workspace=scratch/'forprint_system_blueprint'/'worker-01'/attempt_id/'workspace'/'repo'
    workspace.mkdir(parents=True,mode=0o700)
    prepared=_phase('PREPARE',training.prepare_training_pre_dispatch,
         root=root,task_prompt_id=TASK,worker_id='worker-01',
         attempt_id=attempt_id,blueprint_ai_trial_ready=False,
         ledger_store_override=ledger)
    ack=_phase('BUILD_ACK',training.build_training_canonical_ack,
         root=root,prepared_execution=prepared,
         source_state_fingerprint=source_fingerprint,
         worker_id='worker-01',attempt_id=attempt_id)
    # Automatic exact echo is a *disposable test input*. It is NOT evidence of
    # an actual independent assistant ACK or owner authorization.
    ready=_phase('VALIDATE_ACK',training.validate_training_assistant_ack,
         root=root,prepared_execution=prepared,
         assistant_ack=copy.deepcopy(ack),expected_ack=ack)
    decision=_phase('EXPLICIT_PREVIEW',training.authorize_training_explicit_dispatch,
         root=root,ready_execution=ready,worker_id='worker-01',attempt_id=attempt_id,
         source_state_fingerprint=source_fingerprint,workspace_repo=workspace,
         runtime_provider='github_copilot_cli',runtime_model='auto',
         ledger_store_override=ledger)
    preview=_safe_preview(prepared=prepared,ack=ack,ready=ready,decision=decision,
         attempt_id=attempt_id,source_fingerprint=source_fingerprint)
    # No production launcher can receive decision. AE independently resolves
    # canonical TASK and launches exactly ONE separate disposable systemd unit.
    salt_hex=secrets.token_hex(32)
    nonce=disposable_nonce(preview['preview_identity_sha256'],salt_hex)
    physical=_phase('PHYSICAL_AE',ae.run_once,disposable_nonce=nonce,
                   **({'offline_copilot_probe':True} if offline_copilot_probe else {}))
    if physical.get('status')!='PASS_DISPOSABLE_DELEGATED_WORKER_IPC_KERNEL_TERMINAL':
        stage=physical.get('stage','UNKNOWN')
        if type(stage) is not str or not re.fullmatch(r'[A-Z0-9_]{1,80}',stage):stage='UNKNOWN'
        deny('PHYSICAL_'+stage)
    return {'preview':preview,'physical':physical,
            'joined':join(preview=preview,physical=physical,salt_hex=salt_hex)}

def source_check():
    from scripts.coordination.control_plane import cf10_training_dispatch as training
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_ae_delegated_kernel_rehearsal_v0_1 as ae,
        cf10_systemd_launcher_v0_1 as backend)
    for method in ('resolve_training_task','prepare_training_pre_dispatch',
                   'build_training_canonical_ack','validate_training_assistant_ack',
                   'authorize_training_explicit_dispatch'):
        if not callable(getattr(training,method,None)):deny('DISPATCHER_METHOD_'+method)
    if backend.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_CUTOVER_OPEN')
    if (not callable(getattr(ae,'run_once',None)) or
        not callable(getattr(ae,'disposable_nonce_for_run',None))):
        deny('AE_NONCE_BINDING_SEAM_ABSENT')
    if ae.source_check()['live_worker'] is not False:deny('AE_AUTHORITY')
    return {'schema':SCHEMA,'status':'PASS_CANONICAL_APIS_AND_AE_BOUND_NONCE_SOURCE',
      'production_dispatch':False,'provider_inference':False,'gates_open':list(GATES)}

def run_once():
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    source_check()
    from scripts.coordination.control_plane import cf10_training_dispatch as training
    from scripts.coordination.control_plane.worker_runtime import cf10_ae_delegated_kernel_rehearsal_v0_1 as ae
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
    if backend.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_CUTOVER')
    attempt='cf10-u180j-a'+str(100000000+secrets.randbelow(900000000))
    scratch=_scratch_dir()
    report={'schema':SCHEMA,'status':'CF10_AG_HOLD_BEFORE_DISPATCH',
       'stage':'PREPARING_CANONICAL_DISPOSABLE_PREVIEW','gates_open':list(GATES),
       'canonical_claim_consumed':False,'automatic_retry':False}
    try:
        data=run_with_apis(training=training,ae=ae,root=ROOT,scratch=scratch,
                          attempt_id=attempt)
        report.update(data)
        report['status']=data['joined']['status']
        report['stage']='CANONICAL_DRY_DECISION_JOINED_TO_REAL_DELEGATED_TERMINAL'
    except BaseException as exc:
        report['status']=str(exc) if isinstance(exc,AGHold) else 'CF10_AG_HOLD_'+type(exc).__name__
        report['error_kind']=type(exc).__name__
    finally:
        try:
            _clean_scratch(scratch)
            report['scratch_cleanup']='PASS_DISPOSABLE_ONLY'
        except BaseException:
            report['scratch_cleanup']='HOLD_DISPOSABLE_SCRATCH_REMAINS'
            report['status']='CF10_AG_HOLD_SCRATCH_CLEANUP'
    # Avoid outputting raw prepared ACK, context, decision or any secret-shaped fields.
    return report

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=('source-check','run-once'),required=True)
    a=p.parse_args(argv)
    try:r=source_check() if a.mode=='source-check' else run_once()
    except BaseException as exc:
        r={'schema':SCHEMA,'status':str(exc) if isinstance(exc,AGHold) else 'CF10_AG_HOLD_'+type(exc).__name__,
           'gates_open':list(GATES)}
    print(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=True))
    return 0 if r['status'].startswith('PASS_') else 3
if __name__=='__main__':raise SystemExit(main())
