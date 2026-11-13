"""CF10 X negative/positive tests. No external network or provider credentials."""
from __future__ import annotations
import os
from pathlib import Path
import socket
import threading
from unittest import mock
import pytest
from scripts.coordination.control_plane.worker_runtime import (
 cf10_egress_transport_join_v0_1 as x,
 cf10_inference_egress_session_v0_1 as w,
 cf10_root_egress_attachment_contract_v0_1 as o,
)

HOST='fixture.forprint.invalid:443'

def make_session():
    a=o.plan_attachment(**o.test_vector())
    r={'unit':'forprint-cf10-worker-'+'a'*24+'.service',
       'attempt_id':a['attempt_id'],'source_head':a['source_head'],
       'frozen_preclaim_sha256':a['frozen_preclaim_sha256'],
       'invocation_id':'b'*32,'copilot_binary_sha256':w.PIN,
       'root_ipc_role':'MCP_ONLY_NOT_PROVIDER_EGRESS'}
    return w.build_session(attachment=a,root_binding=r,
        expected_unit=r['unit'],expected_invocation_id=r['invocation_id'])

@pytest.mark.parametrize('version',('HTTP/1.0','HTTP/1.1'))
@pytest.mark.parametrize('hostheader',(False,True))
def test_connect_valid_minimal(version,hostheader):
    data=(f'CONNECT {HOST} {version}\r\n'+(f'Host: {HOST}\r\n' if hostheader else '')+'\r\n').encode()
    assert x.parse_connect(data)==HOST

@pytest.mark.parametrize('body',[
    b'GET / HTTP/1.1\r\n\r\n',
    b'CONNECT fixture.forprint.invalid:443 HTTP/2.0\r\n\r\n',
    b'CONNECT fixture.forprint.invalid:443 HTTP/1.1\r\nHost: other:443\r\n\r\n',
    b'CONNECT fixture.forprint.invalid:443 HTTP/1.1\r\nAuthorization: secret\r\n\r\n',
    b'CONNECT fixture.forprint.invalid:443 HTTP/1.1\r\nProxy-Authorization: Basic aA==\r\n\r\n',
    b'CONNECT fixture.forprint.invalid:443 HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n',
    b'CONNECT fixture.forprint.invalid:443 HTTP/1.1\r\nHost: fixture.forprint.invalid:443\r\nCookie: x\r\n\r\n',
    b'CONNECT fixture.forprint.invalid:443 HTTP/1.1\r\nHost: fixture.forprint.invalid:443\r\nHost: fixture.forprint.invalid:443\r\n\r\n',
    b'CONNECT fixture.forprint.invalid:443 HTTP/1.1\n\n',
    b'CONNECT fixture.forprint.invalid:443 HTTP/1.1\r\n\x00\r\n\r\n',
    b'CONNECT fixture.forprint.invalid:443 HTTP/1.1\r\n',
    b'',b'AA',
    b'CONNECT fixture.forprint.invalid:443 HTTP/1.1\r\nX-Test: something\r\n\r\n',
    b'CONNECT  fixture.forprint.invalid:443 HTTP/1.1\r\n\r\n',
    b'connect fixture.forprint.invalid:443 HTTP/1.1\r\n\r\n',
    b'CONNECT http://fixture.forprint.invalid:443 HTTP/1.1\r\n\r\n',
    b'CONNECT fixture.forprint.invalid:443 HTTP/1.1\r\nHost: other:443\r\n\r\n',
])
def test_http_smuggling_and_extra_headers_denied(body):
    with pytest.raises(x.JoinHold):x.parse_connect(body)

def test_non_allowlisted_target_is_rejected_by_W_not_parse():
    s=make_session()
    target=x.parse_connect(b'CONNECT api.github.com:443 HTTP/1.1\r\n\r\n')
    assert w.decide(s,w.frame(w.request(s,target)))['result']=='DENY_NO_UPSTREAM'

@pytest.mark.parametrize('p',[None,0,65536,-1,'443',True])
def test_root_fixture_port_invalid(p):
    a,b=socket.socketpair()
    try:
        with pytest.raises(x.JoinHold):x.root_serve_one(a,make_session(),runner_uid=os.getuid(),runner_gid=os.getgid(),fixture_port=p)
    finally:a.close();b.close()

@pytest.mark.parametrize('path',('/tmp/sock','/run/forprint-cf10-x-abc/egress.sock',
    '/run/forprint-cf10-x-abcdef/../egress.sock','/run/forprint-cf10-x-abcdef/egress.sock/..',
    '/run/forprint-cf10-x-abcdef/mcp.sock','/run/forprint-cf10-x-abcdef/egress.sock\0',
    '/run/forprint-cf10-x-abcdef/egress.sock;echo'))
def test_root_socket_scope(path):
    a,b=socket.socketpair()
    try:
        with pytest.raises(x.JoinHold,match='ROOT_UNIX_SCOPE'):x.worker_proxy_one(a,path,make_session())
    finally:a.close();b.close()

@pytest.mark.parametrize('status',[201,404,500,True,'200'])
def test_bad_http_status_denied(status):
    with pytest.raises(x.JoinHold):x.response_code(status)

def test_w_fixture_session_hash_mutation_denied():
    s=make_session();s['session_sha256']='0'*64
    with pytest.raises(w.EgressHold):w.decide(s,w.frame(w.request(s)))

def test_root_peeruid_mismatch_denied():
    a,b=socket.socketpair()
    try:
        with pytest.raises(w.EgressHold):x.root_serve_one(a,make_session(),runner_uid=os.getuid()+1,
                          runner_gid=os.getgid(),fixture_port=443)
    finally:a.close();b.close()

def test_root_requires_root(monkeypatch):
    a,b=socket.socketpair()
    try:
        monkeypatch.setattr(x.os,'geteuid',lambda:996)
        with pytest.raises(x.JoinHold,match='ROOT_REQUIRED'):x.root_serve_one(a,make_session(),
                        runner_uid=996,runner_gid=992,fixture_port=443)
    finally:a.close();b.close()

def test_source_closed_gates_only():
    result=x.source_check()
    assert result['gates_open']==['G1','G2','G3','G4','G5']
    assert result['w_reused'] is True
    assert result['no_provider_credential_handoff'] is True
    assert result['no_real_provider_egress'] is True


def test_relay_bidirectional_with_real_sockets():
    left_in,left=socket.socketpair();right,right_out=socket.socketpair()
    output=[]
    def relay():
        try:output.append(x.bounded_relay(left,right,seconds=3))
        except Exception as e:output.append(e)
    thread=threading.Thread(target=relay,daemon=True);thread.start()
    left_in.sendall(b'HELLO')
    assert right_out.recv(5)==b'HELLO'
    right_out.sendall(b'WORLD')
    assert left_in.recv(5)==b'WORLD'
    left_in.shutdown(socket.SHUT_WR);right_out.shutdown(socket.SHUT_WR)
    thread.join(timeout=4)
    try:assert output==[10]
    finally:
        for s in (left_in,left,right,right_out):s.close()


def test_cap_overflow_never_succeeds():
    left_in,left=socket.socketpair();right,right_out=socket.socketpair()
    outcomes=[]
    def relay():
        try:x.bounded_relay(left,right,cap=2,seconds=2)
        except BaseException as e:outcomes.append(str(e))
    t=threading.Thread(target=relay,daemon=True);t.start()
    left_in.sendall(b'ABCD')
    t.join(timeout=3)
    try:assert any('RELAY_OVERFLOW' in s for s in outcomes)
    finally:
        for s in (left_in,left,right,right_out):s.close()


def test_http_reponse_no_credentials():
    assert b'Authorization' not in x.response_code(200)
    assert b'Set-Cookie' not in x.response_code(403)


def test_code_does_not_open_real_provider_or_raise_authority():
    code=Path(x.__file__).read_text()
    assert "upstream.connect(('127.0.0.1',fixture_port))" in code
    for forbidden in ('systemd-run','git push','COPILOT_GITHUB_TOKEN=',
                      'subprocess.Popen','LIVE_CUTOVER_ENABLED=True','/etc/sudoers.d'):
        assert forbidden not in code
