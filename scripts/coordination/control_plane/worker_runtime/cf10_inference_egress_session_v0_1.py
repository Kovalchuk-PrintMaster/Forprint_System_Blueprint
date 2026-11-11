#!/usr/bin/env python3
"""CF10 V: executable bounded *lab* inference-egress IPC session.

This is an egress protocol boundary, deliberately separate from R140 (MCP).
One synthetic fixture destination is accepted; NO TCP upstream, provider
inference, auth material, Worker, claim, root service, or production egress.
Immutable explicit binding is required even for a fixture request. Unknown
fields and attempts to supply secrets are rejected before any socket action.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import socket
import struct
from collections.abc import Mapping

SCHEMA = 'cf10_v_inference_egress_session_v0_1'
REQUEST = 'cf10_v_inference_egress_request_v0_1'
REPLY = 'cf10_v_inference_egress_decision_v0_1'
FIXTURE = 'fixture.forprint.invalid:443'
MAX_FRAME = 2048
PIN = '985f0e1b1b3e734bc996324651307a076ae3deae21e3fa9f9af917983ce309c4'
OPEN_GATES = ('G1','G2','G3','G4','G5')
ATTEMPT = re.compile(r'cf10-[a-zA-Z0-9_-]{3,80}-a[0-9]{3,5}\Z')
SHA40 = re.compile('[0-9a-f]{40}\\Z')
SHA64 = re.compile('[0-9a-f]{64}\\Z')
UNIT = re.compile(r'forprint-cf10-worker-[0-9a-f]{24}\.service\Z')

class EgressHold(ValueError): pass

def deny(reason): raise EgressHold('CF10_V_EGRESS_HOLD_'+reason)
def digest(doc):
    return hashlib.sha256(json.dumps(doc,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest()

def _sha(value,length=64):
    if type(value) is not str or (SHA40 if length==40 else SHA64).fullmatch(value) is None: deny('SHA')
    return value

def _no_unknown(obj,fields,reason):
    if not isinstance(obj,Mapping) or set(obj)!=set(fields):deny(reason+'_SHAPE')
    return obj

def build_session(*, attachment:Mapping, root_binding:Mapping, expected_unit:str, expected_invocation_id:str)->dict:
    """Candidate from O's inert attachment, not independently issued authority."""
    _no_unknown(attachment,{'schema','attempt_id','source_head','frozen_preclaim_sha256',
        'crosswalk_sha256','provider_selection_sha256','provider_id','root_ipc_adapter',
        'egress_route','approved_hosts','open_gates','source_only','authority',
        'live_worker_authorized','inference_enabled','credentials_delegated',
        'external_egress_enabled','dispatcher_integrated','terminal_proven',
        'provider_native_sandbox_counts_as_isolation',
        'kernel_fixture_counts_as_live_worker_proof','automatic_retry',
        'git_mutation_authorized_by_contract','candidate_sha256'},'ATTACHMENT')
    if attachment['schema']!='cf10_root_egress_attachment_candidate_v0_1':deny('ATTACHMENT_SCHEMA')
    check={k:v for k,v in attachment.items() if k!='candidate_sha256'}
    if _sha(attachment['candidate_sha256'])!=digest(check):deny('ATTACHMENT_HASH')
    if (attachment['provider_id']!='github_copilot_cli' or
        attachment['root_ipc_adapter']!='R140_EXISTING_ROOT_IPC' or
        attachment['egress_route']!='J_LOOPBACK_TO_UNIX_CONNECT_CANDIDATE' or
        attachment['approved_hosts']!=[] or attachment['open_gates']!=[
            'G1_REAL_PROVIDER_EGRESS_NOT_ATTESTED','G2_PROVIDER_AUTH_DELEGATION_NOT_ATTESTED',
            'G3_REAL_COPILOT_INFERENCE_NOT_ATTESTED',
            'G4_CANONICAL_DISPATCHER_EGRESS_ATTACHMENT_NOT_ATTESTED',
            'G5_REAL_WORKER_KERNEL_TERMINAL_NOT_ATTESTED']):deny('ATTACHMENT_PRECONDITIONS')
    for k in ('source_only','provider_native_sandbox_counts_as_isolation','kernel_fixture_counts_as_live_worker_proof',
              'live_worker_authorized','inference_enabled','credentials_delegated','external_egress_enabled',
              'dispatcher_integrated','terminal_proven','automatic_retry','git_mutation_authorized_by_contract'):
        required=(k=='source_only')
        if attachment[k] is not required:deny('ATTACHMENT_AUTHORITY_'+k)
    if attachment['authority'] is not False:deny('ATTACHMENT_AUTHORITY')
    attempt=attachment['attempt_id']
    if type(attempt) is not str or ATTEMPT.fullmatch(attempt) is None:deny('ATTEMPT')
    head=_sha(attachment['source_head'],40)
    for field in ('frozen_preclaim_sha256','crosswalk_sha256','provider_selection_sha256'):_sha(attachment[field])
    _no_unknown(root_binding,{'unit','attempt_id','source_head','frozen_preclaim_sha256',
                             'invocation_id','copilot_binary_sha256','root_ipc_role'},'ROOT_BINDING')
    if (type(expected_unit) is not str or UNIT.fullmatch(expected_unit) is None or
        type(expected_invocation_id) is not str or re.fullmatch('[0-9a-f]{32}',expected_invocation_id) is None):
        deny('INDEPENDENT_KERNEL_EXPECTATIONS')
    if (root_binding['unit'] != expected_unit or root_binding['invocation_id'] != expected_invocation_id or
        type(root_binding['unit']) is not str or UNIT.fullmatch(root_binding['unit']) is None or
        root_binding['attempt_id']!=attempt or root_binding['source_head']!=head or
        root_binding['frozen_preclaim_sha256']!=attachment['frozen_preclaim_sha256'] or
        root_binding['root_ipc_role']!='MCP_ONLY_NOT_PROVIDER_EGRESS' or
        _sha(root_binding['copilot_binary_sha256'])!=PIN or
        type(root_binding['invocation_id']) is not str or
        re.fullmatch('[0-9a-f]{32}',root_binding['invocation_id']) is None):deny('ROOT_BINDING_IDENTITY')
    doc={'schema':SCHEMA,'attempt_id':attempt,'source_head':head,
        'provider_id':'github_copilot_cli','attachment_sha256':attachment['candidate_sha256'],
        'unit':root_binding['unit'],'invocation_id':root_binding['invocation_id'],
        'root_mcp_broker_role':'MCP_ONLY_NOT_PROVIDER_EGRESS',
        'inference_egress_role':'SEPARATE_DISPOSABLE_FIXTURE_ONLY',
        'fixture_destination':FIXTURE,'root_upstream_network_enabled':False,
        'real_provider_destinations_allowed':[], 'provider_auth_delegated':False,
        'worker_claim_consumed':False,'gates_open':list(OPEN_GATES),
        'live_dispatch_authorized':False,'real_inference_authorized':False,
        'automatic_retry':False}
    doc['session_sha256']=digest(doc)
    return doc

def _unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:deny('DUPLICATE_JSON_KEY')
        result[k]=v
    return result

def read_frame(raw:bytes)->dict:
    if type(raw) is not bytes or not 2<=len(raw)<=MAX_FRAME or raw.count(b'\n')!=1 or not raw.endswith(b'\n') or b'\0' in raw:
        deny('FRAME_BOUNDS')
    try:obj=json.loads(raw.decode('ascii','strict'),object_pairs_hook=_unique)
    except (UnicodeError,ValueError,TypeError):deny('FRAME_JSON')
    _no_unknown(obj,{'schema','attempt_id','session_sha256','method','target','mode'},'FRAME')
    if any(type(x) is not str for x in obj.values()):deny('FRAME_VALUE_TYPE')
    return obj

def request(session:Mapping,target:str=FIXTURE):
    return {'schema':REQUEST,'attempt_id':session['attempt_id'],
      'session_sha256':session['session_sha256'],'method':'CONNECT',
      'target':target,'mode':'SYNTHETIC_FIXTURE_ONLY'}

def decide(session:Mapping,frame:bytes)->dict:
    if not isinstance(session,Mapping) or session.get('schema')!=SCHEMA:deny('SESSION')
    _sha(session.get('session_sha256'))
    if digest({k:v for k,v in session.items() if k!='session_sha256'})!=session['session_sha256']:deny('SESSION_HASH')
    obj=read_frame(frame)
    if (obj['schema']!=REQUEST or obj['attempt_id']!=session['attempt_id'] or
        obj['session_sha256']!=session['session_sha256'] or obj['method']!='CONNECT' or
        obj['mode']!='SYNTHETIC_FIXTURE_ONLY'):deny('REQUEST_BINDING')
    target=obj['target']
    if not 1<=len(target)<=255 or any(ord(c)<33 or ord(c)>126 for c in target):deny('TARGET_ENCODING')
    verdict='ALLOW_SYNTHETIC_FIXTURE_NO_UPSTREAM' if target==FIXTURE else 'DENY_NO_UPSTREAM'
    return {'schema':REPLY,'session_sha256':session['session_sha256'],
        'result':verdict,'real_upstream_attempted':False,
        'credential_seen':False,'provider_inference':False,
        'live_worker_authorized':False,'g1_g5_open':True}

def frame(obj):
    blob=(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('ascii')
    if len(blob)>MAX_FRAME:deny('ENCODE_OVERSIZE')
    return blob

def peer_cred(sock:socket.socket,*,uid:int,gid:int):
    if not isinstance(sock,socket.socket) or type(uid) is not int or type(gid) is not int:deny('PEER_ARGUMENT')
    try:data=sock.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,struct.calcsize('3i'))
    except OSError:deny('PEER_KERNEL_UNAVAILABLE')
    pid,u,g=struct.unpack('3i',data)
    if pid<2 or u!=uid or g!=gid:deny('PEER_IDENTITY')
    return {'pid':pid,'uid':u,'gid':g,'kernel_verified':True}

def serve_one(sock:socket.socket,session:Mapping,*,uid:int,gid:int):
    """A single real AF_UNIX session, no TCP or provider access."""
    peer=peer_cred(sock,uid=uid,gid=gid)
    sock.settimeout(3)
    b=bytearray()
    while len(b)<=MAX_FRAME:
        chunk=sock.recv(1)
        if not chunk:deny('PEER_EOF')
        b.extend(chunk)
        if chunk==b'\n':break
    if len(b)>MAX_FRAME:deny('PEER_OVERSIZE')
    verdict=decide(session,bytes(b))
    sock.sendall(frame(verdict))
    return {'kernel_peer_checked':True,'uid':peer['uid'],'gid':peer['gid'],
        'response':verdict,'upstream_network_used':False,
        'live_authority':False,'gates_open':list(OPEN_GATES)}

def source_check():
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_root_egress_attachment_contract_v0_1 as o,
        cf10_systemd_launcher_v0_1 as launcher)
    if launcher.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_SWITCH_OPEN')
    doc=o.plan_attachment(**o.test_vector())
    rb={'unit':'forprint-cf10-worker-'+'a'*24+'.service',
        'attempt_id':doc['attempt_id'],'source_head':doc['source_head'],
        'frozen_preclaim_sha256':doc['frozen_preclaim_sha256'],
        'invocation_id':'b'*32,'copilot_binary_sha256':PIN,
        'root_ipc_role':'MCP_ONLY_NOT_PROVIDER_EGRESS'}
    session=build_session(attachment=doc,root_binding=rb,
        expected_unit=rb['unit'],expected_invocation_id=rb['invocation_id'])
    assert decide(session,frame(request(session)))['result']=='ALLOW_SYNTHETIC_FIXTURE_NO_UPSTREAM'
    assert decide(session,frame(request(session,'api.github.com:443')))['result']=='DENY_NO_UPSTREAM'
    return session

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['source-check'],required=True);p.parse_args(argv)
    try:
        session=source_check()
        print('CF10_V_EGRESS=PASS_BOUND_PEER_IPC_FIXTURE_ONLY')
        print('CF10_V_EGRESS_SESSION_SHA256='+session['session_sha256'])
        print('CF10_V_EGRESS_GATES=OPEN_G1_G5_NO_UPSTREAM_OR_CREDENTIALS')
        return 0
    except (EgressHold,AssertionError,ImportError,AttributeError,ValueError,KeyError,TypeError):
        print('CF10_V_EGRESS=HOLD_SOURCE_CHECK')
        return 3
if __name__=='__main__':raise SystemExit(main())
