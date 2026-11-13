#!/usr/bin/env python3
"""AH: one nonce-bound physical worker executes pinned Copilot --version offline.

This is a delegated-leaf test of the *actual CLI binary*, not authenticated
inference. It reuses AG's canonical Dispatcher API decision-preview -> nonce,
and AE's validated root/runner IPC, cgroup transition and systemd terminal.
No token, CLI config, external network, production worker claim, durable worker
ledger, automatic retry, or new launcher. G1-G5 deliberately remain OPEN.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
from collections.abc import Mapping

SCHEMA='cf10_ah_pinned_copilot_offline_join_v0_1'
PROBE='cf10_ad_disposable_worker_child_v0_1'
GATES=['G1','G2','G3','G4','G5']
UNIT=re.compile(r'forprint-cf10-batchad-[0-9a-f]{16}\.service\Z')
SHA64=re.compile(r'[0-9a-f]{64}\Z')
PIN='985f0e1b1b3e734bc996324651307a076ae3deae21e3fa9f9af917983ce309c4'

class OfflineHold(ValueError):pass

def deny(why):raise OfflineHold('CF10_AH_HOLD_'+why)

def verify_probe(proof:Mapping,*,unit:str,nonce:str)->dict:
    """Bound lab evidence from the trusted child; never an independent exec pin.

    Root prechecks the immutable executable by R115. Child runs only --version
    with a fixed secret-free env; provider auth and network remain disabled.
    """
    keys={'schema','phase','unit','nonce_sha256','exit_code','stdout_sha256',
          'stderr_sha256','stdout_bytes','stderr_bytes','version_1_0_107_observed',
          'argv_mode','credentials_passed','provider_inference'}
    if not isinstance(proof,Mapping) or set(proof)!=keys:deny('PROOF_SHAPE')
    if (type(unit) is not str or UNIT.fullmatch(unit) is None or
        type(nonce) is not str or SHA64.fullmatch(nonce) is None):deny('EXPECTATION_SCOPE')
    if (proof['schema']!=PROBE or proof['phase']!='COPILOT_OFFLINE_VERSION_PROOF' or
        proof['unit']!=unit or proof['nonce_sha256']!=hashlib.sha256(nonce.encode('ascii')).hexdigest()):
        deny('PROOF_BINDING')
    if (proof['argv_mode']!='PINNED_COPILOT_VERSION_ONLY' or
        type(proof['exit_code']) is not int or proof['exit_code']!=0 or
        proof['version_1_0_107_observed'] is not True or
        proof['credentials_passed'] is not False or proof['provider_inference'] is not False):
        deny('PROVIDER_OR_AUTH_DRIFT')
    for k in ('stdout_sha256','stderr_sha256'):
        if type(proof[k]) is not str or SHA64.fullmatch(proof[k]) is None:deny('OUTPUT_HASH')
    for k in ('stdout_bytes','stderr_bytes'):
        if type(proof[k]) is not int or proof[k]<0 or proof[k]>4096:deny('OUTPUT_SIZE')
    if proof['stdout_bytes']+proof['stderr_bytes']==0:deny('MISSING_VERSION_OUTPUT')
    return {'schema':SCHEMA,'offline_cli_verified':True,'binary_sha256_expected':PIN,
            'argv_mode':'PINNED_COPILOT_VERSION_ONLY',
            'version_1_0_107_observed':True,'stdout_sha256':proof['stdout_sha256'],
            'stderr_sha256':proof['stderr_sha256'],
            'exit_code':0,'worker_subprocess_probe':True,
            'independent_exec_inode_proven':False,'provider_inference':False,
            'credentials_used':False,'external_egress':False,'gates_open':list(GATES)}


def verify_failure(frame:Mapping,*,unit:str,nonce:str)->dict:
    """Exact allowlisted offline failure; no CLI stdout/stderr or auth material."""
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_ad_disposable_worker_child_v0_1 as child)
    keys={'schema','phase','unit','nonce_sha256','failure_code','return_code','os_errno',
          'stdout_bytes','stderr_bytes','stdout_sha256','stderr_sha256'}
    if not isinstance(frame,Mapping) or set(frame)!=keys:deny('FAILURE_SCHEMA')
    if (not isinstance(unit,str) or UNIT.fullmatch(unit) is None or
        type(nonce) is not str or SHA64.fullmatch(nonce) is None or
        frame['schema']!=PROBE or frame['phase']!='COPILOT_OFFLINE_VERSION_HOLD' or
        frame['unit']!=unit or frame['nonce_sha256']!=hashlib.sha256(nonce.encode()).hexdigest()):
        deny('FAILURE_BINDING')
    if type(frame['failure_code']) is not str or frame['failure_code'] not in child.OfflineProbeFailure.CODES:
        deny('FAILURE_CODE')
    code=frame['return_code'];errno=frame['os_errno']
    if code is not None and (type(code) is not int or not -255<=code<=255):deny('FAILURE_RETURN')
    if errno is not None and (type(errno) is not int or not 1<=errno<=4095):deny('FAILURE_ERRNO')
    for key in ('stdout_bytes','stderr_bytes'):
        if type(frame[key]) is not int or not 0<=frame[key]<=65535:deny('FAILURE_BYTES')
    for key in ('stdout_sha256','stderr_sha256'):
        if type(frame[key]) is not str or SHA64.fullmatch(frame[key]) is None:deny('FAILURE_HASH')
    # Null fields are allowed, but mode-specific data cannot impersonate success.
    if frame['failure_code']=='NONZERO_EXIT' and (code is None or code==0):deny('FAILURE_EXIT_MISSING')
    if frame['failure_code']=='EXEC_OSERROR' and errno is None:deny('FAILURE_ERRNO_MISSING')
    return {'schema':SCHEMA,'offline_cli_verified':False,'failure_code':frame['failure_code'],
      'return_code':code,'os_errno':errno,
      'stdout_bytes':frame['stdout_bytes'],'stderr_bytes':frame['stderr_bytes'],
      'stdout_sha256':frame['stdout_sha256'],'stderr_sha256':frame['stderr_sha256'],
      'no_output_content_exposed':True,'credentials_used':False,'provider_inference':False,
      'failure_is_not_terminal_success':True}

def attest(*,preview:Mapping,physical:Mapping,joined:Mapping)->dict:
    if not isinstance(preview,Mapping) or not isinstance(physical,Mapping) or not isinstance(joined,Mapping):
        deny('JOIN_INPUT')
    off=physical.get('copilot_offline')
    if (not isinstance(off,Mapping) or off.get('schema')!=SCHEMA or
        off.get('offline_cli_verified') is not True or
        off.get('version_1_0_107_observed') is not True or
        off.get('independent_exec_inode_proven') is not False or
        off.get('credentials_used') is not False or off.get('external_egress') is not False or
        off.get('provider_inference') is not False or off.get('gates_open')!=GATES):
        deny('OFFLINE_PROOF_ABSENT')
    if (joined.get('status')!='PASS_CANONICAL_DISPATCHER_NONCE_BOUND_TO_PHYSICAL_TERMINAL' or
        joined.get('real_kernel_leaf_1_to_0') is not True or
        joined.get('nonce_binding_verified_against_child_digest') is not True or
        joined.get('physical_unit')!=physical.get('unit') or
        joined.get('physical_invocation_id')!=physical.get('kernel',{}).get('invocation_id') or
        joined.get('physical_result_sha256')!=physical.get('result',{}).get('synthetic_result_digest') or
        joined.get('gates_open')!=GATES or
        joined.get('canonical_worker_claim_consumed') is not False or
        joined.get('real_copilot_inference') is not False):
        deny('CANONICAL_PHYSICAL_JOIN')
    if (physical.get('status')!='PASS_DISPOSABLE_DELEGATED_WORKER_IPC_KERNEL_TERMINAL' or
        physical.get('runtime_cleanup')!='PASS_DISPOSABLE_ONLY' or
        physical.get('stage')!='STOPPED_AND_TERMINAL_VERIFIED' or
        physical.get('kernel',{}).get('transition')!='1_TO_0' or
        physical.get('kernel',{}).get('samples')!=['1','0'] or
        physical.get('poststop',{}).get('active')!='inactive' or
        preview.get('ack_from_independent_assistant') is not False or
        preview.get('production_owner_auth') is not False):
        deny('PHYSICAL_OR_PREVIEW')
    result={'schema':SCHEMA,'status':'PASS_CANONICAL_NONCE_BOUND_PINNED_COPILOT_OFFLINE_KERNEL_TERMINAL',
      'unit':joined['physical_unit'],'invocation_id':joined['physical_invocation_id'],
      'decision_preview_sha256':joined['preview_identity_sha256'],
      'nonce_commitment_sha256':joined['nonce_commitment_sha256'],
      'synthetic_result_sha256':joined['physical_result_sha256'],
      'version_stdout_sha256':off['stdout_sha256'],
      'version_stderr_sha256':off['stderr_sha256'],
      'offline_binary_version_observed':True,'copilot_subprocess_spawned_by_cgroup_worker':True,
      'copilot_exec_inode_independently_proven':False,
      'kernel_leaf_1_to_0_proven':True,'retained_systemd_stop_verified':True,
      'canonical_dispatcher_apis_exercised':True,'independent_ack_or_owner_auth':False,
      'copilot_inference_executed':False,'provider_authenticated':False,
      'root_provider_egress_used':False,'production_dispatcher_claim_consumed':False,
      'production_result_accepted':False,'worker_ledger_written':False,
      'automatic_retry':False,'gates_open':list(GATES)}
    result['report_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return result


def source_check()->dict:
    from scripts.coordination.control_plane.worker_runtime import (
       cf10_ae_delegated_kernel_rehearsal_v0_1 as ae,
       cf10_ag_bound_dispatcher_worker_v0_1 as ag,
       cf10_systemd_launcher_v0_1 as backend,
       cf10_r115_preclaim_executable_profile_v0_1 as r115)
    if backend.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_SWITCH_OPEN')
    if r115.COPILOT_PILOT_SHA256!=PIN:deny('R115_BINARY_PIN_DRIFT')
    if ag.source_check().get('status')!='PASS_CANONICAL_APIS_AND_AE_BOUND_NONCE_SOURCE':deny('AG_API')
    if ae.source_check().get('live_worker') is not False:deny('AE_SOURCE')
    return {'schema':SCHEMA,'status':'PASS_OFFLINE_COPILOT_NON_AUTHORIZING_SOURCE',
            'real_binary_exec':False,'gates_open':list(GATES)}


def run_once()->dict:
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    source_check()
    from scripts.coordination.control_plane.worker_runtime import (
       cf10_ag_bound_dispatcher_worker_v0_1 as ag,
       cf10_ae_delegated_kernel_rehearsal_v0_1 as ae,
       cf10_r115_preclaim_executable_profile_v0_1 as r115)
    from scripts.coordination.control_plane import cf10_training_dispatch as training
    # Root metadata, expected size, O_NOFOLLOW FD and SHA are verified before
    # any disposable systemd process is created or attempt preview evaluated.
    r115.assert_pinned_binary()
    scratch=ag._scratch_dir()
    report={'schema':SCHEMA,'status':'CF10_AH_HOLD_BEFORE_START',
            'stage':'ROOT_PINNED_BINARY_VERIFIED','gates_open':list(GATES),
            'production_claim_consumed':False,'credentials_used':False,
            'provider_inference':False,'automatic_retry':False}
    physical_seen={}
    class AEProxy:
        def run_once(self,**kwargs):
            row=ae.run_once(**kwargs)
            physical_seen['status']=row.get('status')
            physical_seen['stage']=row.get('stage')
            physical_seen['runtime_cleanup']=row.get('runtime_cleanup')
            physical_seen['error_kind']=row.get('error',{}).get('kind')
            # AE reports only validated codes, numeric errno/exit status and hashes.
            if isinstance(row.get('copilot_offline_diagnostic'),dict):
                physical_seen['copilot_offline_diagnostic']=row['copilot_offline_diagnostic']
            return row
    try:
        attempt='cf10-u180j-a'+str(100000000+secrets.randbelow(900000000))
        data=ag.run_with_apis(training=training,ae=AEProxy(),root=ag.ROOT,
             scratch=scratch,attempt_id=attempt,offline_copilot_probe=True)
        joined=attest(**data)
        report['status']=joined['status'];report['stage']='PHYSICAL_PINNED_COPILOT_OFFLINE_TERMINAL'
        report['joined']=joined
    except BaseException as exc:
        report['status']=str(exc) if isinstance(exc,OfflineHold) else 'CF10_AH_HOLD_'+type(exc).__name__
        report['stage']='REVIEW_REQUIRED'
        report['physical_diagnostic']=physical_seen
    finally:
        try:ag._clean_scratch(scratch);report['scratch_cleanup']='PASS_DISPOSABLE_ONLY'
        except BaseException:
            report['scratch_cleanup']='HOLD_QUARANTINE'
            report['status']='CF10_AH_HOLD_SCRATCH_CLEANUP'
    return report


def main(argv=None)->int:
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('source-check','run-once'),required=True)
    args=p.parse_args(argv)
    try:result=source_check() if args.mode=='source-check' else run_once()
    except BaseException as exc:
        result={'schema':SCHEMA,'status':str(exc) if isinstance(exc,OfflineHold)
                 else 'CF10_AH_HOLD_'+type(exc).__name__,'gates_open':list(GATES)}
    print(json.dumps(result,sort_keys=True,separators=(',',':'),ensure_ascii=True))
    return 0 if result['status'].startswith('PASS_') else 3

if __name__=='__main__':raise SystemExit(main())
