#!/usr/bin/env python3
"""CF-10 X: executable disposable HTTP CONNECT <-> W-session <-> TLS fixture join.

Existing W owns the root session and SO_PEERCRED authority.  This module
ADAPTS W's exact session into a bounded byte tunnel; it neither creates a
second MCP broker nor enables production egress or accepts provider credentials.
The *only* upstream is a root-supplied local TLS fixture at 127.0.0.1.  The
production upstream / provider auth boundary remains explicitly CLOSED.
"""
from __future__ import annotations
import json
import os
import re
import select
import socket
import struct
import time
from typing import Mapping
from scripts.coordination.control_plane.worker_runtime import cf10_inference_egress_session_v0_1 as w

SCHEMA='cf10_x_bound_transport_join_v0_1'
MAX_HEAD=4096
MAX_WIRE=65536
MAX_LIFE=12.0
OPEN_GATES=('G1','G2','G3','G4','G5')

class JoinHold(RuntimeError):pass

def deny(reason):raise JoinHold('CF10_X_HOLD_'+reason)

def recv_until(s:socket.socket,delimiter:bytes,limit:int)->bytes:
    if not isinstance(s,socket.socket) or type(delimiter) is not bytes or delimiter not in (b'\n',b'\r\n\r\n'):
        deny('INPUT')
    data=bytearray()
    while not data.endswith(delimiter):
        if len(data)>=limit:deny('SIZE')
        try:part=s.recv(1)
        except (OSError,TimeoutError):deny('TIMEOUT')
        if not part:deny('EARLY_EOF')
        data+=part
    return bytes(data)

def parse_connect(data:bytes)->str:
    """No HTTP proxy auth, arbitrary headers, request bodies, or absolute URIs."""
    if type(data) is not bytes or not 16<=len(data)<=MAX_HEAD or not data.endswith(b'\r\n\r\n'):
        deny('HTTP_FRAME')
    try:lines=data[:-4].decode('ascii','strict').split('\r\n')
    except UnicodeError:deny('HTTP_ENCODING')
    if not lines or len(lines)>2:deny('HTTP_HEADERS')
    cols=lines[0].split(' ')
    if len(cols)!=3 or cols[0]!='CONNECT' or cols[2] not in ('HTTP/1.0','HTTP/1.1'):
        deny('HTTP_METHOD')
    target=cols[1]
    if target!=w.FIXTURE and (not 1<=len(target)<=255 or any(ord(x)<33 or ord(x)>126 for x in target)):
        deny('HTTP_TARGET')
    if '/' in target or '@' in target or '\\' in target or ':' not in target:deny('HTTP_TARGET_SYNTAX')
    if len(lines)==2 and lines[1]!=f'Host: {target}':deny('HTTP_HEADER_POLICY')
    return target

def response_code(code:int)->bytes:
    if code==200:return b'HTTP/1.1 200 Connection Established\r\n\r\n'
    if code==403:return b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n'
    deny('HTTP_STATUS')

def bounded_relay(one:socket.socket,two:socket,*,cap:int=MAX_WIRE,seconds:float=MAX_LIFE)->int:
    if not (isinstance(one,socket.socket) and isinstance(two,socket.socket) and type(cap) is int and 1<=cap<=MAX_WIRE and 0<seconds<=MAX_LIFE):deny('RELAY_PARAMS')
    pairs={one:two,two:one};live={one,two};bytes_total=0;deadline=time.monotonic()+seconds
    while live:
        left=deadline-time.monotonic()
        if left<=0:deny('RELAY_DEADLINE')
        try:ready,_,_=select.select(tuple(live),[],[],min(left,0.25))
        except (OSError,ValueError):deny('RELAY_SELECT')
        for src in ready:
            try:data=src.recv(min(4096,cap-bytes_total+1))
            except OSError:deny('RELAY_READ')
            if not data:
                live.remove(src)
                try:pairs[src].shutdown(socket.SHUT_WR)
                except OSError:pass
                continue
            bytes_total+=len(data)
            if bytes_total>cap:deny('RELAY_OVERFLOW')
            try:pairs[src].sendall(data)
            except OSError:deny('RELAY_WRITE')
    return bytes_total

def root_serve_one(conn:socket.socket,session:Mapping,*,runner_uid:int,runner_gid:int,fixture_port:int)->dict:
    """Root-owned W decision + one localhost fixture TLS tunnel (NO egress)."""
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    if type(fixture_port) is not int or not 1<=fixture_port<=65535:deny('FIXTURE_PORT')
    peer=w.peer_cred(conn,uid=runner_uid,gid=runner_gid)
    conn.settimeout(8)
    raw=recv_until(conn,b'\n',w.MAX_FRAME)
    verdict=w.decide(session,raw)
    if verdict['real_upstream_attempted'] is not False or verdict['g1_g5_open'] is not True:
        deny('W_AUTHORITY_DRIFT')
    conn.sendall(w.frame(verdict))
    if verdict['result']=='DENY_NO_UPSTREAM':
        return {'schema':SCHEMA,'decision':'DENY_NO_UPSTREAM','kernel_peer_checked':True,
                'peer_uid':peer['uid'],'peer_gid':peer['gid'],'tls_fixture_bytes':0,
                'real_upstream':False,'credentials':False,'live_worker':False,'gates_open':list(OPEN_GATES)}
    if verdict['result']!='ALLOW_SYNTHETIC_FIXTURE_NO_UPSTREAM':deny('W_DECISION')
    # No hostname or public address reaches socket.connect.  Loopback ONLY.
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as upstream:
        upstream.settimeout(6)
        upstream.connect(('127.0.0.1',fixture_port))
        total=bounded_relay(conn,upstream)
    return {'schema':SCHEMA,'decision':'ALLOW_SYNTHETIC_FIXTURE_NO_UPSTREAM',
            'kernel_peer_checked':True,'peer_uid':peer['uid'],'peer_gid':peer['gid'],
            'tls_fixture_bytes':total,'real_upstream':False,'credentials':False,
            'live_worker':False,'gates_open':list(OPEN_GATES)}

def worker_proxy_one(http:socket.socket,root_socket:str,session:Mapping,*,root_uid:int=0)->dict:
    """Worker-side HTTP proxy translates CONNECT to W; no provider tokens."""
    if (type(root_uid) is not int or root_uid!=0 or not isinstance(root_socket,str) or
        re.fullmatch(r'/run/forprint-cf10-x-[A-Za-z0-9_]{6,24}/egress\.sock',root_socket) is None):
        deny('ROOT_UNIX_SCOPE')
    http.settimeout(8)
    target=parse_connect(recv_until(http,b'\r\n\r\n',MAX_HEAD))
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as up:
        up.settimeout(8)
        up.connect(root_socket)
        raw=up.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,struct.calcsize('3i'))
        pid,uid,gid=struct.unpack('3i',raw)
        if pid<2 or uid!=root_uid:deny('ROOT_PEER')
        up.sendall(w.frame(w.request(session,target)))
        rawreply=recv_until(up,b'\n',w.MAX_FRAME)
        try: result=json.loads(rawreply.decode('ascii','strict'),object_pairs_hook=w._unique)
        except (UnicodeError,ValueError,TypeError):deny('ROOT_REPLY_JSON')
        expected=w.decide(session,w.frame(w.request(session,target)))
        if not isinstance(result,dict) or result!=expected or set(result)!={
             'schema','session_sha256','result','real_upstream_attempted','credential_seen',
             'provider_inference','live_worker_authorized','g1_g5_open'}:
            deny('ROOT_REPLY_UNBOUND')
        if result['result']=='DENY_NO_UPSTREAM':
            http.sendall(response_code(403))
            return {'schema':SCHEMA,'decision':'DENY_NO_UPSTREAM','root_peer_uid':uid,
                    'fixture_tls_bytes':0,'external_provider_egress':False,'gates_open':list(OPEN_GATES)}
        if result['result']!='ALLOW_SYNTHETIC_FIXTURE_NO_UPSTREAM':deny('ROOT_REPLY_ACTION')
        http.sendall(response_code(200))
        total=bounded_relay(http,up)
        return {'schema':SCHEMA,'decision':'ALLOW_SYNTHETIC_FIXTURE_NO_UPSTREAM',
                'root_peer_uid':uid,'fixture_tls_bytes':total,
                'external_provider_egress':False,'gates_open':list(OPEN_GATES)}

def source_check()->dict:
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_systemd_launcher_v0_1 as launcher,
        cf10_root_egress_attachment_contract_v0_1 as o)
    if launcher.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_SWITCH_DRIFT')
    attach=o.plan_attachment(**o.test_vector())
    rb={'unit':'forprint-cf10-worker-'+'a'*24+'.service',
        'attempt_id':attach['attempt_id'],'source_head':attach['source_head'],
        'frozen_preclaim_sha256':attach['frozen_preclaim_sha256'],
        'invocation_id':'b'*32,'copilot_binary_sha256':w.PIN,
        'root_ipc_role':'MCP_ONLY_NOT_PROVIDER_EGRESS'}
    session=w.build_session(attachment=attach,root_binding=rb,
                expected_unit=rb['unit'],expected_invocation_id=rb['invocation_id'])
    if w.decide(session,w.frame(w.request(session)))['result']!='ALLOW_SYNTHETIC_FIXTURE_NO_UPSTREAM':
        deny('W_SOURCE_DRIFT')
    if w.decide(session,w.frame(w.request(session,'api.github.com:443')))['result']!='DENY_NO_UPSTREAM':
        deny('REAL_HOST_POLICY')
    return {'schema':SCHEMA,'session_sha256':session['session_sha256'],
            'w_reused':True,'r140_unchanged':True,'no_real_provider_egress':True,
            'no_provider_credential_handoff':True,'live_worker':False,
            'canonical_dispatcher_attached':False,'gates_open':list(OPEN_GATES)}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=('source-check',),required=True);p.parse_args()
    try:
        result=source_check()
        print('CF10_X_SOURCE=PASS_BOUND_TLS_FIXTURE_TRANSPORT_NO_AUTHORITY')
        print('CF10_X_SESSION_SHA256='+result['session_sha256'])
        print('CF10_X_G1_G5=OPEN')
    except (JoinHold,w.EgressHold,AssertionError,ImportError,ValueError,TypeError,KeyError):
        print('CF10_X_SOURCE=HOLD')
        raise SystemExit(3)
