"""CF10 Batch G -- disposable UDS-mediated *fixture* inference round trip.

No model/provider API, no tokens, no live Worker admission. This lab exercises
one trusted host-side broker decision across the proven Batch F sandbox.
"""
from __future__ import annotations
import hashlib
import json
import re
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as r013
from scripts.coordination.control_plane.worker_runtime import cf10_batch_f_disposable_sandbox_contract_v0_1 as batch_f

SCHEMA='cf10_batch_g_inference_bridge_contract_v0_1'
CLIENT_SCHEMA='cf10_batch_g_disposable_inference_request_v0_1'
RESPONSE_SCHEMA='cf10_batch_g_disposable_inference_response_v0_1'
STATUS='FIXTURE_TRANSPORT_ONLY_NO_COPILOT_AUTHORITY'
OPEN_GATES=('G1_REAL_INFERENCE_PATH_NOT_ATTESTED',
            'G2_PROVIDER_CREDENTIALS_NOT_SCOPED',
            'G3_REAL_COPILOT_PROCESS_NOT_PINNED',
            'G4_CANONICAL_BROKER_NOT_IN_LIVE_LIFECYCLE',
            'G5_KERNEL_TERMINAL_1_TO_0_UNPROVEN')
PAYLOAD_SHA=hashlib.sha256(b'CF10_BATCH_G_PUBLIC_DISPOSABLE_FIXTURE').hexdigest()
MAX_FRAME=1024

class BridgeHold(RuntimeError):pass

def deny(code):raise BridgeHold('CF10_BATCH_G_HOLD_'+code)

def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest()

def request_id(unit):
    if type(unit) is not str or not re.fullmatch(r'forprint-cf10-batchg-[0-9a-f]{16}\.service',unit):deny('UNIT')
    return hashlib.sha256(('cf10-batch-g|'+unit).encode('ascii')).hexdigest()[:24]

def fixture_request(unit, route='fixture.inference'):
    return {'schema':CLIENT_SCHEMA,'request_id':request_id(unit),
            'route':route,'payload_sha256':PAYLOAD_SHA}

def fixture_reply(unit):
    return {'schema':RESPONSE_SCHEMA,'status':'OK_FIXTURE_ONLY',
            'request_id':request_id(unit),
            'response_sha256':hashlib.sha256(('fixture-response|'+request_id(unit)).encode('ascii')).hexdigest()}

def broker_decide(message, unit):
    """Fixed allowlist. NEVER forwards to the network or launches any commands."""
    if type(message) is not dict or set(message)!=set(fixture_request(unit)):
        deny('REQUEST_KEYS')
    if any(type(message[k]) is not str for k in message):deny('REQUEST_TYPES')
    if message['schema']!=CLIENT_SCHEMA or message['request_id']!=request_id(unit) or \
       message['payload_sha256']!=PAYLOAD_SHA:deny('REQUEST_BINDING')
    if message['route']!='fixture.inference':
        return {'schema':RESPONSE_SCHEMA,'status':'DENIED_ROUTE','request_id':request_id(unit)}
    return fixture_reply(unit)

def validate_positive_reply(payload,unit):
    if type(payload) is not dict or payload!=fixture_reply(unit):deny('RESPONSE_BINDING')
    return True

def plan(*,unit,lab_dir,private_file):
    request_id(unit)
    if type(lab_dir) is not str or lab_dir != '/run/'+unit.removesuffix('.service'):
        deny('LAB_SCOPE')
    if private_file!=lab_dir+'/fake_credential.txt':deny('FILE_SCOPE')
    p=dict(r013.EXPECTED_PROPERTIES)
    for key,val in {'User':'forprint-runner','Group':'forprint-runner',
                    'KillMode':'control-group','NoNewPrivileges':'yes',
                    'ProtectSystem':'strict','ProtectHome':'yes',
                    'ProtectControlGroups':'yes','PrivateDevices':'yes',
                    'RestrictNamespaces':'yes','CapabilityBoundingSet':'',
                    'AmbientCapabilities':'','Delegate':'no'}.items():
        if p.get(key)!=val:deny('R013_BASE_CHANGED_'+key)
    p.pop('StateDirectory',None);p.pop('StateDirectoryMode',None)
    p.update({'PrivateNetwork':'yes','RestrictAddressFamilies':'AF_UNIX',
              'IPAddressDeny':'any','InaccessiblePaths':'/var/lib/forprint-runner '+private_file,
              'Environment':'HOME=/nonexistent','WorkingDirectory':'/',
              'RuntimeMaxSec':'60s','Restart':'no','Type':'exec','ExitType':'cgroup',
              'StandardOutput':'null','StandardError':'null'})
    return {'schema':SCHEMA,'status':STATUS,'unit':unit,'properties':p,
            'profile_sha256':digest(p),'local_fixture_only':True,
            'copilot_executed':False,'provider_credentials_used':False,
            'real_network_egress':False,'worker_claim_consumed':False,
            'kernel_terminal_proven':False,'production_root_broker_used':False,
            'live_admission':False,'g1_g5_closed':False,'open_gates':list(OPEN_GATES)}

def source_check():
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    if launcher.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_GATE_ON')
    f=batch_f.source_check()
    if f.get('authority') is not False or len(f.get('open_gates',()))!=5:
        deny('PREDECESSOR_GATES')
    u='forprint-cf10-batchg-'+'1'*16+'.service'
    obj=plan(unit=u,lab_dir='/run/'+u.removesuffix('.service'),
             private_file='/run/'+u.removesuffix('.service')+'/fake_credential.txt')
    if obj['live_admission'] is not False or len(obj['open_gates'])!=5:deny('GATES_DRIFT')
    if broker_decide(fixture_request(u),u)!=fixture_reply(u):deny('LOCAL_ROUTE_DRIFT')
    if broker_decide(fixture_request(u,'external.anywhere'),u)['status']!='DENIED_ROUTE':
        deny('DENY_ROUTE_DRIFT')
    return {'schema':SCHEMA,'status':STATUS,'profile_sha256':obj['profile_sha256'],
            'local_fixture_only':True,'authority':False,'open_gates':list(OPEN_GATES)}

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--mode',required=True,choices=['source-check']);p.parse_args(argv)
    try:
        report=source_check()
        print('CF10_BATCH_G_SOURCE=PASS_BOUNDED_DISPOSABLE_INFERENCE_FIXTURE')
        print('CF10_BATCH_G_PROFILE_SHA256='+report['profile_sha256'])
        print('CF10_BATCH_G_G1_G5=OPEN_NO_COPILOT_OR_NETWORK_ADMISSION')
        return 0
    except (BridgeHold,KeyError,ValueError,TypeError,ImportError) as exc:
        print(str(exc) if isinstance(exc,BridgeHold) else 'CF10_BATCH_G_HOLD_'+type(exc).__name__)
        return 3
if __name__=='__main__':raise SystemExit(main())
