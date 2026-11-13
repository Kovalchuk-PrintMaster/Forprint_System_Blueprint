"""CF10 Large Batch H: real loopback CONNECT/TLS transport through a Unix broker.

Disposable, NO provider, tokens, live Worker, R030 launch, production broker,
PAM, owner claim, external egress, or G1-G5 authorization. The test certificate
and body are public synthetic fixture data, not provider credentials.
"""
from __future__ import annotations
import hashlib
import ipaddress
import json
import re
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as r013
from scripts.coordination.control_plane.worker_runtime import cf10_batch_g_inference_bridge_contract_v0_1 as g

SCHEMA='cf10_batch_h_loopback_tls_transport_contract_v0_1'
REQUEST_SCHEMA='cf10_batch_h_connect_v0_1'
ALLOW='fixture.forprint.invalid:443'
REJECT='unauthorized.invalid:443'
BODY=b'CF10_BATCH_H_PUBLIC_TLS_CONNECT_FIXTURE_V1\n'
BODY_SHA256=hashlib.sha256(BODY).hexdigest()
OPEN_GATES=('G1_LIVE_PROVIDER_NETWORK_NOT_ATTESTED',
            'G2_PROVIDER_AUTH_NOT_DELEGATED',
            'G3_REAL_COPILOT_NOT_EXECUTED',
            'G4_R030_ROOT_BROKER_NOT_ATTACHED',
            'G5_KERNEL_PINNED_1_TO_0_UNPROVEN')

class TransportHold(RuntimeError): pass

def deny(msg): raise TransportHold('CF10_BATCH_H_HOLD_'+msg)

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest()

def request_id(unit):
    if type(unit) is not str or not re.fullmatch(r'forprint-cf10-batchh-[0-9a-f]{16}\.service',unit):deny('UNIT_SCOPE')
    return hashlib.sha256(('cf10-batch-h|'+unit).encode('ascii')).hexdigest()[:24]

def connect_request(unit, target):
    return {'schema':REQUEST_SCHEMA,'request_id':request_id(unit),'target':target,
            'attempt_mode':'DISPOSABLE_TLS_FIXTURE_ONLY'}

def broker_decide(request,unit):
    if type(request) is not dict or set(request)!=set(connect_request(unit,ALLOW)) or \
       any(type(v) is not str for v in request.values()):deny('REQUEST_SHAPE')
    if request['schema']!=REQUEST_SCHEMA or request['request_id']!=request_id(unit) or \
       request['attempt_mode']!='DISPOSABLE_TLS_FIXTURE_ONLY':deny('REQUEST_BINDING')
    if request['target']==REJECT:return {'status':'DENY_CONNECT','request_id':request_id(unit)}
    if request['target']!=ALLOW:deny('UNEXPECTED_TARGET')
    return {'status':'ALLOW_FIXTURE_TLS','request_id':request_id(unit)}

def expected_https_body():return BODY

def plan(*,unit,lab_dir,private_file):
    request_id(unit)
    if type(lab_dir) is not str or lab_dir!='/run/'+unit.removesuffix('.service'):deny('LAB_SCOPE')
    if private_file!=lab_dir+'/fake_credential.txt':deny('PRIVATE_FILE_SCOPE')
    p=dict(r013.EXPECTED_PROPERTIES)
    required={'User':'forprint-runner','Group':'forprint-runner','KillMode':'control-group',
              'NoNewPrivileges':'yes','ProtectSystem':'strict','ProtectHome':'yes',
              'ProtectControlGroups':'yes','PrivateDevices':'yes','RestrictNamespaces':'yes',
              'CapabilityBoundingSet':'','AmbientCapabilities':'','Delegate':'no'}
    for key,val in required.items():
        if p.get(key)!=val:deny('R013_BASE_DRIFT_'+key)
    p.pop('StateDirectory',None);p.pop('StateDirectoryMode',None)
    p.update({'PrivateNetwork':'yes',
              'RestrictAddressFamilies':'AF_UNIX AF_INET AF_INET6',
              'IPAddressDeny':'any','IPAddressAllow':'localhost',
              'InaccessiblePaths':'/var/lib/forprint-runner '+private_file,
              'Environment':'HOME=/nonexistent','WorkingDirectory':'/',
              'RuntimeMaxSec':'75s','Restart':'no','Type':'exec','ExitType':'cgroup',
              'StandardOutput':'null','StandardError':'null'})
    return {'schema':SCHEMA,'unit':unit,'properties':p,'profile_sha256':digest(p),
            'external_network_used':False,'live_admission':False,
            'provider_credentials_used':False,'copilot_executed':False,
            'worker_claim_consumed':False,'production_broker_used':False,
            'kernel_terminal_proven':False,'open_gates':list(OPEN_GATES)}

def effective_network_set(raw):
    if type(raw) is not str or not raw.strip():return None
    if raw.strip()=='localhost':return {'127.0.0.0/8','::1/128'}
    try:
        items=raw.split()
        if len(items)!=2 or len(set(items))!=2:return None
        return {str(ipaddress.ip_network(x,strict=True)) for x in items}
    except ValueError:return None

def source_check():
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    if launcher.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_GATE_ENABLED')
    prior=g.source_check()
    if prior.get('authority') is not False:deny('G_PREDECESSOR_AUTHORITY_DRIFT')
    u='forprint-cf10-batchh-'+'a'*16+'.service'
    path='/run/'+u.removesuffix('.service')
    candidate=plan(unit=u,lab_dir=path,private_file=path+'/fake_credential.txt')
    if candidate['live_admission'] is not False or len(candidate['open_gates'])!=5:deny('GATES_DRIFT')
    if broker_decide(connect_request(u,REJECT),u)['status']!='DENY_CONNECT':deny('DENIAL_DRIFT')
    if broker_decide(connect_request(u,ALLOW),u)['status']!='ALLOW_FIXTURE_TLS':deny('ALLOWLIST_DRIFT')
    if effective_network_set('127.0.0.0/8 ::1/128')!={'127.0.0.0/8','::1/128'}:deny('NETWORK_POLICY')
    return {'schema':SCHEMA,'authority':False,'open_gates':list(OPEN_GATES),
            'profile_sha256':candidate['profile_sha256']}

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['source-check'],required=True);p.parse_args(argv)
    try:
        r=source_check()
        print('CF10_BATCH_H_SOURCE=PASS_LOOPBACK_TLS_CONNECT_DISPOSABLE_ONLY')
        print('CF10_BATCH_H_PROFILE_SHA256='+r['profile_sha256'])
        print('CF10_BATCH_H_G1_G5=OPEN_NO_LIVE_COPILOT_OR_EGRESS')
        return 0
    except (TransportHold,ValueError,TypeError,KeyError,ImportError) as exc:
        print(str(exc) if isinstance(exc,TransportHold) else 'CF10_BATCH_H_HOLD_'+type(exc).__name__)
        return 3
if __name__=='__main__':raise SystemExit(main())
