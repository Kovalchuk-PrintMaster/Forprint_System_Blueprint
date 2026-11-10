"""R135: real local socket framing, but root/cgroup/lease are test doubles.

These tests DO NOT attest production root authority, G1-G5, or kernel cancel.
"""
from __future__ import annotations

import json
import os
import socket
import threading
import time
from copy import deepcopy
from pathlib import Path

import pytest

from tests.coordination.control_plane.worker_runtime.test_cf10_r134_ipc_preclaim_crosswalk_v0_1 import source_pair
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r135_ipc_session_fence_v0_1 as r135,
    cf10_r127_mcp_stdio_ipc_proxy_v0_1 as proxy,
    cf10_r126_root_external_revoke_v0_1 as revoke,
    cf10_r129_canonical_lifecycle_convergence_v0_1 as r129,
)

LEASE = Path('/run/forprint-cf10-r125-0123456789abcdef/lease.json')


def setup_bound(monkeypatch):
    inv, c = source_pair()
    lease = {'revoked': False, 'calls': 0, 'revoke_calls': 0}
    monkeypatch.setattr(r135.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(r135, '_peer_kernel', lambda conn:(34293, 996, 992))
    monkeypatch.setattr(r135, '_proc_cgroup', lambda pid:'0::/system.slice/'+
        r135.bind.unit_for(c['attempt_id'], c['source_head']))
    def inspect(path, **kwargs):
        assert path == LEASE
        assert kwargs == {'attempt':c['attempt_id'],'epoch':c['epoch'],
                          'source_head':c['source_head'],'capsule_id':r129.CAPSULE}
        lease['calls'] += 1
        return {'revoked':lease['revoked']}
    def do_revoke(path, **kwargs):
        assert path == LEASE
        assert kwargs['attempt']==c['attempt_id']
        if lease['revoked']:
            raise revoke.ExternalRevokeHold('ALREADY_REVOKED')
        lease['revoke_calls'] += 1
        lease['revoked'] = True
    monkeypatch.setattr(revoke, 'inspect_lease', inspect)
    monkeypatch.setattr(revoke, 'revoke_lease', do_revoke)
    return inv, c, lease


def args(inv,c):
    return dict(invocation=inv,candidate=c,expected_attempt=c['attempt_id'],
                expected_epoch=c['epoch'],expected_head=c['source_head'],
                lease_path=LEASE,timeout_seconds=2)


def frame(obj):
    return proxy.encode(obj)


def messages():
    return [
      {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18',
         'capabilities':{},'clientInfo':{'name':'ForPrint','version':'1'}}},
      {'jsonrpc':'2.0','method':'notifications/initialized'},
      {'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}},
      {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'run_repo_head','arguments':{}}},
    ]


def response(msg):
    method=msg['method']
    result = ({'protocolVersion':'2025-06-18','capabilities':{}} if method=='initialize'
        else {'tools':[{'name':'run_repo_head', 'description':'read-only'}]} if method=='tools/list'
        else {'isError':False,'structuredContent':{'return_code':0,'timed_out':False,
            'outcome':'completed','authority':{'worker':False},'evidence_digest':'a'*64}})
    return frame({'jsonrpc':'2.0','id':msg['id'],'result':result})


def run_sockets(monkeypatch, *, external_revoke=False, corrupt_call=False, mutate=None):
    inv,c,lease=setup_bound(monkeypatch)
    cp, cs = socket.socketpair()
    bp, bs = socket.socketpair()
    received=[]; results=[]; backend_errors=[]
    for s in (cp,cs,bp,bs):s.settimeout(3)
    def backend():
        try:
            rdr=bs.makefile('rb')
            for i in range(4):
                req=proxy.decode(rdr.readline());received.append(req['method'])
                if i == 1:continue
                if i == 3 and external_revoke:
                    # This is a *fixture* external lease change while MCP works.
                    lease['revoked'] = True
                    time.sleep(0.2)
                else:
                    bs.sendall(response(req))
        except Exception as exc:
            backend_errors.append(str(exc))
    def controller():
        try:results.append(r135.handle_session(client=cs,trusted_mcp=bp,**args(inv,c)))
        except Exception as exc:results.append(exc)
    tb=threading.Thread(target=backend,daemon=True)
    tc=threading.Thread(target=controller,daemon=True)
    tb.start();tc.start()
    client_responses=[]
    try:
        for i,m in enumerate(messages()):
            if i==3 and corrupt_call:
                m['params']['name']='run_validation_suite'
            if mutate is not None and i==3:mutate(m)
            cp.sendall(frame(m))
            if i!=1 and not (i==3 and (external_revoke or corrupt_call)):
                raw=b''
                while not raw.endswith(b'\n'):
                    raw+=cp.recv(8192)
                client_responses.append(proxy.decode(raw))
        tc.join(timeout=3);tb.join(timeout=3)
        return received,client_responses,results,lease,backend_errors
    finally:
        for s in (cp,cs,bp,bs):s.close()


def test_fixture_real_unix_sockets_exact_one_readonly_call_and_root_revoke(monkeypatch):
    received, replies, results, lease, errors = run_sockets(monkeypatch)
    assert not errors
    assert received == list(proxy.METHODS)
    assert [x['id'] for x in replies] == [1,2,3]
    assert len(results)==1 and isinstance(results[0], dict)
    assert results[0]['state']=='DISPOSABLE_IPC_ONE_READ_ONLY_CALL_REVOKED_REVIEW_ONLY'
    assert results[0]['root_verified_peer'] is True  # only fixture peer injected
    assert results[0]['inflight_kernel_cancellation_proven'] is False
    assert all(results[0][x] is False for x in ('worker_result_accepted','terminal_ledger_written',
         'g1_g5_closed','live_worker_authorized','automatic_retry'))
    assert lease['revoked'] and lease['revoke_calls']==1 and lease['calls']>=7


def test_fixture_external_revoke_midtool_suppresses_result_and_requires_quarantine(monkeypatch):
    received, replies, results, lease, errors=run_sockets(monkeypatch,external_revoke=True)
    assert received==list(proxy.METHODS)
    assert len(replies)==2
    assert len(results)==1 and isinstance(results[0], r135.SessionHold)
    assert results[0].in_flight and results[0].quarantine_required
    assert not results[0].terminal_success and not results[0].automatic_retry
    assert lease['revoke_calls']==0


def test_fixture_widened_tool_denied_before_backend(monkeypatch):
    received, replies, results, lease, errors=run_sockets(monkeypatch,corrupt_call=True)
    assert received==list(proxy.METHODS[:3])
    assert len(replies)==2
    assert isinstance(results[0],r135.SessionHold)
    assert 'PROTOCOL_DENIED' in str(results[0])
    assert lease['revoke_calls']==0


@pytest.mark.parametrize('field,new', [('attempt','cf10-else-a000'),('epoch','wrong'),
    ('head','f'*40),('lease',Path('/tmp/forged/lease.json'))])
def test_binding_identity_drift_denied_before_socket(monkeypatch,field,new):
    inv,c,lease=setup_bound(monkeypatch)
    client, other=socket.socketpair()
    try:
        inputs=args(inv,c)
        key={'attempt':'expected_attempt','epoch':'expected_epoch','head':'expected_head','lease':'lease_path'}[field]
        inputs[key]=new
        with pytest.raises(r135.SessionHold):
            r135.verify_binding(**{k:v for k,v in inputs.items() if k not in ('timeout_seconds',)})
    finally:client.close();other.close()


def test_root_required_before_source_claim(monkeypatch):
    inv,c=source_pair()
    monkeypatch.setattr(r135.os,'geteuid',lambda:996)
    with pytest.raises(r135.SessionHold,match='ROOT_REQUIRED'):
        r135.verify_binding(invocation=inv,candidate=c,expected_attempt=c['attempt_id'],
            expected_epoch=c['epoch'],expected_head=c['source_head'],lease_path=LEASE)


@pytest.mark.parametrize('creds',[(1,996,992),(99,0,0),(99,996,0),(99,995,992)])
def test_peer_identity_denied(monkeypatch,creds):
    client,peer=socket.socketpair()
    try:
        monkeypatch.setattr(r135,'_peer_kernel',lambda s:creds)
        monkeypatch.setattr(r135,'_proc_cgroup',lambda pid:'0::/system.slice/'+
            'forprint-cf10-worker-'+'a'*24+'.service')
        with pytest.raises(r135.SessionHold, match='PEER_UID_GID'):
            r135.verify_peer(client,unit='forprint-cf10-worker-'+'a'*24+'.service')
    finally:client.close();peer.close()


def test_wrong_cgroup_fails_even_with_correct_uid(monkeypatch):
    client,peer=socket.socketpair()
    try:
        monkeypatch.setattr(r135,'_peer_kernel',lambda s:(99,996,992))
        monkeypatch.setattr(r135,'_proc_cgroup',lambda pid:'0::/system.slice/unrelated.service')
        with pytest.raises(r135.SessionHold,match='PEER_NOT_IN_CANONICAL_CGROUP'):
            r135.verify_peer(client,unit='forprint-cf10-worker-'+'a'*24+'.service')
    finally:client.close();peer.close()


def test_peer_cgroup_file_unavailable_fails_closed(monkeypatch):
    monkeypatch.setattr(r135.os,'open',lambda *a,**kw: (_ for _ in ()).throw(OSError('missing')))
    with pytest.raises(r135.SessionHold, match='PROC_CGROUP_UNAVAILABLE'):
        r135._proc_cgroup(123)


def test_external_lease_revoked_before_call_denied(monkeypatch):
    inv,c,lease=setup_bound(monkeypatch)
    identity=r135.verify_binding(invocation=inv,candidate=c,expected_attempt=c['attempt_id'],
        expected_epoch=c['epoch'],expected_head=c['source_head'],lease_path=LEASE)
    lease['revoked']=True
    with pytest.raises(r135.SessionHold,match='ROOT_LEASE_REVOKED_OR_DRIFT'):
        r135.check_lease(lease_path=LEASE,identity=identity)


def test_lease_readback_unavailable_denied(monkeypatch):
    inv,c,lease=setup_bound(monkeypatch)
    identity=r135.verify_binding(invocation=inv,candidate=c,expected_attempt=c['attempt_id'],
        expected_epoch=c['epoch'],expected_head=c['source_head'],lease_path=LEASE)
    monkeypatch.setattr(revoke,'inspect_lease',lambda *a,**k:(_ for _ in ()).throw(revoke.ExternalRevokeHold('x')))
    with pytest.raises(r135.SessionHold,match='ROOT_LEASE_UNAVAILABLE'):
        r135.check_lease(lease_path=LEASE,identity=identity)


@pytest.mark.parametrize('duration',[0,True,31,-1,'12'])
def test_session_budget_denied(duration):
    with pytest.raises(r135.SessionHold,match='SESSION_TIMEOUT'):
        r135.handle_session(client=None,trusted_mcp=None,invocation={},candidate={},
            expected_attempt='x',expected_epoch='x',expected_head='x',lease_path=LEASE,
            timeout_seconds=duration)


def test_frame_oversize_denied_and_never_accepted(monkeypatch):
    inv,c,lease=setup_bound(monkeypatch)
    identity=r135.verify_binding(invocation=inv,candidate=c,expected_attempt=c['attempt_id'],
        expected_epoch=c['epoch'],expected_head=c['source_head'],lease_path=LEASE)
    a,b=socket.socketpair()
    try:
        a.sendall(b'x'*(r135.MAX+4))
        with pytest.raises(r135.SessionHold,match='FRAME_OVERSIZE'):
            r135.FrameReader().read(b,lease=LEASE,identity=identity,deadline=time.monotonic()+1,in_flight=False)
    finally:a.close();b.close()


def test_source_no_independent_launcher_or_ledger():
    text=Path(r135.__file__).read_text('utf8')
    assert 'subprocess.Popen(' not in text
    assert 'systemd-run' not in text
    assert '.append_observation(' not in text
    assert 'LIVE_CUTOVER_ENABLED=True' not in text
    assert 'r126.inspect_lease(' in text
    assert 'r126.revoke_lease(' in text
    assert 'r134.verify_source_only(' in text
    assert 'r127_proxy.validate_request(' in text


def test_source_only_cli_state_no_authority(monkeypatch,capsys):
    monkeypatch.setattr(r129,'verify_pinned_seams',lambda root:None)
    assert r135.main(['--mode','source-check'])==0
    output=capsys.readouterr().out
    assert 'NO_LISTENER_NO_WORKER' in output
    assert 'G1_G5=OPEN_NO_LIVE_ADMISSION' in output
