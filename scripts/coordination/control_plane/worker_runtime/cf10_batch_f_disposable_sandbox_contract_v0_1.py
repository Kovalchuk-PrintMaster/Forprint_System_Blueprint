"""CF10 Batch F: executable AF_UNIX-only *lab* sandbox profile, never Copilot admission.

The profile deliberately blocks TCP including provider inference. It proves no
live G1/G2/G3 production gate and is NOT passed to R030.run_once. The only
runtime consumer is a separate disposable test unit under /run, without a claim.
"""
from __future__ import annotations
import hashlib
import json
import re
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as r013

SCHEMA='cf10_batch_f_disposable_sandbox_contract_v0_1'
STATE='CANDIDATE_AF_UNIX_ONLY_DISPOSABLE_NO_COPILOT_INFERENCE'
GATES=('G1_INFERENCE_TRANSPORT_UNSOLVED','G2_REAL_CREDENTIAL_SCOPE_UNPROVEN',
       'G3_REAL_COPILOT_PROCESS_NOT_SANDBOXED','G4_PRODUCTION_BROKER_NOT_WIRED',
       'G5_KERNEL_TERMINAL_UNPROVEN')

class SandboxHold(RuntimeError): pass

def deny(code): raise SandboxHold('CF10_BATCH_F_HOLD_'+code)

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()

def disposable_plan(*, unit:str, canary_file:str, lab_dir:str)->dict:
    if type(unit) is not str or not re.fullmatch(r'forprint-cf10-batchf-[0-9a-f]{16}\.service',unit):
        deny('UNIT')
    if type(lab_dir) is not str or lab_dir != '/run/'+unit.removesuffix('.service'):
        deny('RUN_SCOPE')
    if canary_file != lab_dir+'/fake_provider_credential.txt':
        deny('CANARY_SCOPE')
    base=dict(r013.EXPECTED_PROPERTIES)
    if base['User']!=r013.RUNNER or base['Group']!=r013.RUNNER or base['KillMode']!='control-group':
        deny('R013_BASE_CHANGED')
    # A disposable lab must never manage the persistent runner StateDirectory.
    base.pop('StateDirectory',None)
    base.pop('StateDirectoryMode',None)
    base.update({'PrivateNetwork':'yes','RestrictAddressFamilies':'AF_UNIX',
                 'IPAddressDeny':'any',
                 'InaccessiblePaths':'/var/lib/forprint-runner '+canary_file,
                 'Environment':'HOME=/nonexistent',
                 'WorkingDirectory':'/','RuntimeMaxSec':'60s',
                 'Restart':'no','Type':'exec','ExitType':'cgroup',
                 'StandardOutput':'null','StandardError':'null'})
    for k,v in {'NoNewPrivileges':'yes','ProtectSystem':'strict',
                'ProtectHome':'yes','ProtectControlGroups':'yes',
                'PrivateDevices':'yes','RestrictNamespaces':'yes',
                'CapabilityBoundingSet':'','AmbientCapabilities':'',
                'Delegate':'no'}.items():
        if base.get(k)!=v: deny('ISOLATION_BASE_CHANGED_'+k)
    return {'schema':SCHEMA,'state':STATE,'unit':unit,'properties':base,
            'profile_sha256':digest(base),
            'model_inference_possible':False,'provider_credentials_used':False,
            'copilot_executed':False,'root_broker_live':False,
            'kernel_terminal_proven':False,'g1_g5_closed':False,
            'live_admission':False,'claim_consumed':False,
            'open_gates':list(GATES)}

def source_check():
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_systemd_launcher_v0_1 as launcher,
        cf10_batch_e_runtime_cutover_contract_v0_1 as r_e)
    if launcher.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_GATE_ON')
    e=r_e.source_check()
    if e.get('live_worker_authorized') is not False or len(e.get('open_gates',[]))!=5:
        deny('BATCH_E_GATES')
    unit='forprint-cf10-batchf-'+'1'*16+'.service'
    plan=disposable_plan(unit=unit,lab_dir='/run/'+unit[:-8],
        canary_file='/run/'+unit[:-8]+'/fake_provider_credential.txt')
    return {'schema':SCHEMA,'source_checked':True,
            'profile_sha256':plan['profile_sha256'],
            'authority':False,'open_gates':list(GATES)}

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['source-check'],required=True)
    p.parse_args(argv)
    try:
        d=source_check()
        print('CF10_BATCH_F_SOURCE=PASS_EXACT_DISPOSABLE_SANDBOX_PROFILE')
        print('CF10_BATCH_F_PROFILE_SHA256='+d['profile_sha256'])
        print('CF10_BATCH_F_G1_G5=OPEN_NO_COPILOT_ADMISSION')
        return 0
    except (SandboxHold,ImportError,KeyError,TypeError,ValueError) as exc:
        print(str(exc) if isinstance(exc,SandboxHold) else 'CF10_BATCH_F_HOLD_'+type(exc).__name__)
        return 3
if __name__=='__main__': raise SystemExit(main())
