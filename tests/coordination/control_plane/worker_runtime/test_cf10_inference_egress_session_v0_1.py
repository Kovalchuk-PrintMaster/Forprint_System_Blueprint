"""V root-only inference-egress IPC seam: executable negative and identity coverage."""
from __future__ import annotations
from copy import deepcopy
import json
import os
import socket
import threading
import pytest
from scripts.coordination.control_plane.worker_runtime import (
    cf10_inference_egress_session_v0_1 as v,
    cf10_root_egress_attachment_contract_v0_1 as o,
)

def good():
    a=o.plan_attachment(**o.test_vector())
    root={'unit':'forprint-cf10-worker-'+'a'*24+'.service',
      'attempt_id':a['attempt_id'],'source_head':a['source_head'],
      'frozen_preclaim_sha256':a['frozen_preclaim_sha256'],
      'invocation_id':'b'*32,'copilot_binary_sha256':v.PIN,
      'root_ipc_role':'MCP_ONLY_NOT_PROVIDER_EGRESS'}
    return a,root

def session():
    a,r=good()
    return v.build_session(attachment=a,root_binding=r,expected_unit='forprint-cf10-worker-'+'a'*24+'.service', expected_invocation_id='b'*32)

def test_binding_stable_and_no_authority():
    x=session();assert x==session()
    assert x['root_mcp_broker_role']=='MCP_ONLY_NOT_PROVIDER_EGRESS'
    assert x['inference_egress_role']=='SEPARATE_DISPOSABLE_FIXTURE_ONLY'
    assert x['real_provider_destinations_allowed']==[]
    assert all(x[k] is False for k in ('root_upstream_network_enabled',
      'live_dispatch_authorized','real_inference_authorized','provider_auth_delegated',
      'automatic_retry','worker_claim_consumed'))
    assert x['gates_open']==['G1','G2','G3','G4','G5']

def test_one_fixture_no_external_host():
    s=session()
    ok=v.decide(s,v.frame(v.request(s)))
    assert ok['result']=='ALLOW_SYNTHETIC_FIXTURE_NO_UPSTREAM'
    assert ok['real_upstream_attempted'] is False
    assert ok['provider_inference'] is False
    assert v.decide(s,v.frame(v.request(s,'api.github.com:443')))['result']=='DENY_NO_UPSTREAM'

@pytest.mark.parametrize('bad',[
  'github.com:443','api.github.com:443','localhost:443',
  '127.0.0.1:443','[::1]:443','fixture.forprint.invalid:8443',
  'FIXTURE.FORPRINT.INVALID:443','fixture.forprint.invalid:443/path',
  'fixture.forprint.invalid:443@evil.test:443',
  'fixture.forprint.invalid:443\r','fixture.forprint.invalid:443\u00a0',
])
def test_destination_never_upstream(bad):
    s=session()
    try:r=v.decide(s,v.frame(v.request(s,bad)))
    except v.EgressHold:return
    assert r['result']=='DENY_NO_UPSTREAM'
    assert r['real_upstream_attempted'] is False

@pytest.mark.parametrize('key,val',[
 ('unit','forprint-cf10-worker-'+'b'*24+'.service'),
 ('invocation_id','a'*32),
 ('source_head','b'*40),
 ('frozen_preclaim_sha256','d'*64),
 ('copilot_binary_sha256','c'*64),
 ('attempt_id','cf10-other-a999'),
 ('root_ipc_role','ROOT_INFERENCE_BROKER'),
])
def test_root_binding_forgery_denied(key,val):
    a,r=good();r[key]=val
    with pytest.raises(v.EgressHold):v.build_session(attachment=a,root_binding=r,expected_unit='forprint-cf10-worker-'+'a'*24+'.service', expected_invocation_id='b'*32)

@pytest.mark.parametrize('field,val',[
 ('authority',True),('source_only',False),('approved_hosts',['api.github.com:443']),
 ('external_egress_enabled',True),('provider_id','other'),
 ('credentials_delegated',True),('automatic_retry',True),
])
def test_widened_attachment_even_if_rehashed_denied(field,val):
    a,r=good();a[field]=val;a['candidate_sha256']=v.digest({k:x for k,x in a.items() if k!='candidate_sha256'})
    with pytest.raises(v.EgressHold):v.build_session(attachment=a,root_binding=r,expected_unit='forprint-cf10-worker-'+'a'*24+'.service', expected_invocation_id='b'*32)

def test_attachment_unknown_key_denied():
    a,r=good();a['Authorization']='secret';a['candidate_sha256']=v.digest({k:x for k,x in a.items() if k!='candidate_sha256'})
    with pytest.raises(v.EgressHold):v.build_session(attachment=a,root_binding=r,expected_unit='forprint-cf10-worker-'+'a'*24+'.service', expected_invocation_id='b'*32)

@pytest.mark.parametrize('change',[
 {'attempt_id':'cf10-other-a999'}, {'session_sha256':'0'*64},
 {'schema':'wrong'}, {'method':'POST'}, {'mode':'PRODUCTION'},
 {'Authorization':'Bearer fake'}, {'token':'fake'}, {'headers':{}},
])
def test_ipc_request_mutation_denied(change):
    s=session();row=v.request(s);row.update(change)
    with pytest.raises(v.EgressHold):v.decide(s,v.frame(row))

@pytest.mark.parametrize('raw',[
 b'',b'{}',b'{}\n\n',b'\x00\n',b'[]\n',b'{"schema":1}\n',
 b'{"a":1,"a":2}\n', b'\xff\n',b'a'*3000+b'\n',
])
def test_invalid_frame_denied(raw):
    with pytest.raises(v.EgressHold):v.read_frame(raw)

def test_tampered_session_hash_denied():
    s=session();s['gates_open']=[]
    with pytest.raises(v.EgressHold):v.decide(s,v.frame(v.request(s)))

def test_socketpair_real_kernel_identity_and_one_fixture_roundtrip():
    s=session();a,b=socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM)
    got=[]
    def server():
        with a:got.append(v.serve_one(a,s,uid=os.getuid(),gid=os.getgid()))
    thread=threading.Thread(target=server);thread.start()
    with b:
        b.sendall(v.frame(v.request(s)))
        data=bytearray()
        while not data.endswith(b'\n'):data.extend(b.recv(512))
        reply=json.loads(data)
        assert reply['result']=='ALLOW_SYNTHETIC_FIXTURE_NO_UPSTREAM'
        assert reply['real_upstream_attempted'] is False
    thread.join(timeout=4)
    assert not thread.is_alive()
    assert got[0]['kernel_peer_checked'] is True
    assert got[0]['upstream_network_used'] is False


def test_socketpair_wrong_peer_uid_denied():
    a,b=socket.socketpair()
    try:
        with pytest.raises(v.EgressHold):v.peer_cred(a,uid=os.getuid()+10000,gid=os.getgid())
    finally:a.close();b.close()
