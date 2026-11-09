"""CF10 R125: non-authorizing, fail-closed single-use lab MCP IPC session gate.

This module is deliberately NOT a production broker or a Worker launcher.
Owner/PAM, claim, canonical ledger and release authority are not implemented
here. One disposable fixture can forward one registered read-only Git HEAD call.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import socket
import stat
import struct

MAX_FRAME = 65536
LEASE_MAX = 4096
PROTO = '2025-06-18'
ATTEMPT = 'cf10-r121-disposable-no-worker'  # Exact R121 wrapper attempt binding.
CAPABILITY = 'run_repo_head'
META_METHODS = ('initialize', 'notifications/initialized', 'tools/list')

class BoundaryHold(RuntimeError):
    pass

def deny(s: str):
    raise BoundaryHold('CF10_R125_HOLD_'+s)

def unique(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj: deny('JSON_DUPLICATE_KEY')
        obj[k] = v
    return obj

def parse(raw: bytes) -> dict:
    if type(raw) is not bytes or not 2 <= len(raw) <= MAX_FRAME or not raw.endswith(b'\n') or raw.count(b'\n') != 1:
        deny('FRAME_SIZE')
    try:
        o=json.loads(raw.decode('utf8','strict'), object_pairs_hook=unique)
    except (ValueError, UnicodeError, TypeError):
        deny('FRAME_JSON')
    if type(o) is not dict: deny('FRAME_OBJECT')
    return o

def encode(obj: dict) -> bytes:
    if type(obj) is not dict: deny('ENCODE_OBJECT')
    blob=(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('ascii')
    if len(blob)>MAX_FRAME: deny('ENCODE_SIZE')
    return blob

def recvline(sock: socket.socket) -> bytes:
    b=bytearray()
    while len(b) < MAX_FRAME:
        c=sock.recv(1)
        if not c: deny('CLIENT_EOF')
        b+=c
        if c==b'\n': return bytes(b)
    deny('FRAME_OVERSIZE')

def verify_peer(sock, uid:int, gid:int):
    if not (type(uid) is int and type(gid) is int and uid>0 and gid>0): deny('PEER_PARAMS')
    raw=sock.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,struct.calcsize('3i'))
    pid,u,g=struct.unpack('3i',raw)
    if not (pid>0 and u==uid and g==gid): deny('PEER_MISMATCH')
    return {'uid':u,'gid':g,'verified':True}

def validate_metadata(raw:bytes,phase:int,seen:set):
    if type(phase) is not int or phase not in (0,1,2): deny('META_PHASE')
    v=parse(raw)
    if v.get('jsonrpc')!='2.0' or v.get('method')!=META_METHODS[phase]: deny('META_METHOD')
    fields={'jsonrpc','method'} if phase==1 else {'jsonrpc','id','method','params'}
    if set(v)!=fields: deny('META_FIELDS')
    if phase==1: return v
    if type(v['id']) is not str or not re.fullmatch('[0-9a-f]{32}',v['id']) or v['id'] in seen: deny('META_ID')
    seen.add(v['id'])
    if type(v['params']) is not dict: deny('META_PARAMS')
    if phase==0:
        p=v['params']
        if set(p)!={'protocolVersion','capabilities','clientInfo'}: deny('INIT_KEYS')
        if p['protocolVersion']!=PROTO or p['capabilities']!={}: deny('INIT_PROTOCOL')
        if p['clientInfo']!={'name':'ForPrintR125BoundedLab','version':'0.1.0'}: deny('CLIENT_ID')
    elif v['params']!={}: deny('LIST_PARAMS')
    return v

def validate_readonly_call(raw:bytes,seen:set) -> dict:
    v=parse(raw)
    if set(v)!={'jsonrpc','id','method','params'} or v.get('jsonrpc')!='2.0' or v.get('method')!='tools/call': deny('CALL_METHOD')
    if type(v['id']) is not str or not re.fullmatch('[0-9a-f]{32}',v['id']) or v['id'] in seen: deny('CALL_ID')
    if v.get('params')!={'name':CAPABILITY,'arguments':{}}: deny('CALL_CAPABILITY_OR_ARGUMENTS')
    seen.add(v['id'])
    return v

def check_response(resp:dict,request_id:str):
    if type(resp) is not dict or resp.get('jsonrpc')!='2.0' or resp.get('id')!=request_id or 'error' in resp: deny('RESPONSE_IDENTITY')
    result=resp.get('result')
    if type(result) is not dict or result.get('isError', False) is not False: deny('TOOL_REJECTED')
    structured=result.get('structuredContent')
    if type(structured) is not dict: deny('TOOL_RESULT_MISSING')
    if structured.get('return_code') != 0 or structured.get('timed_out') is not False or structured.get('outcome')!='completed':
        # The canonical launcher uses COMPLETED or SUCCESS depending on build;
        # fail closed rather than assuming either means success.
        deny('TOOL_RESULT_OUTCOME')
    authority=structured.get('authority')
    if type(authority) is not dict or not authority or any(type(x) is not bool or x for x in authority.values()): deny('TOOL_AUTHORITY')
    if type(structured.get('evidence_digest')) is not str or not re.fullmatch('[0-9a-f]{64}',structured['evidence_digest']): deny('TOOL_EVIDENCE')
    return {'read_only_call_completed':True,'result_evidence_sha256':structured['evidence_digest'],'authority_widened':False}

def secure_lease(path:Path,*,attempt:str,epoch:str,source_head:str,capsule_id:str,revoked:bool):
    """Check exact root-owned disposable record from trusted side, no model input."""
    if not isinstance(path, Path) or not path.is_absolute() or not re.fullmatch(r'/run/forprint-cf10-r125-[0-9a-f]{16}/lease.json',str(path)): deny('LEASE_PATH')
    try:
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
        try:
            st=os.fstat(fd)
            if not (stat.S_ISREG(st.st_mode) and st.st_uid==0 and st.st_gid==0 and stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1 and st.st_size<=LEASE_MAX): deny('LEASE_OWNER_MODE')
            raw=os.read(fd,LEASE_MAX+1)
        finally: os.close(fd)
    except OSError: deny('LEASE_UNREADABLE')
    if len(raw)>LEASE_MAX: deny('LEASE_SIZE')
    try: obj=json.loads(raw.decode('utf8'),object_pairs_hook=unique)
    except (ValueError,UnicodeError): deny('LEASE_JSON')
    if type(obj) is not dict or set(obj)!={'schema','attempt_id','epoch','source_head','capsule_id','revoked'}: deny('LEASE_KEYS')
    if (obj['schema']!='cf10_r125_disposable_lease_v0_1' or obj['attempt_id']!=attempt or obj['epoch']!=epoch or
        obj['source_head']!=source_head or obj['capsule_id']!=capsule_id or type(obj['revoked']) is not bool or obj['revoked']!=revoked): deny('LEASE_BINDING_OR_REVOKED')
    return True

def write_lease(path:Path,*,attempt:str,epoch:str,source_head:str,capsule_id:str,revoked:bool,replace:bool=False):
    """Root lab writer only: O_EXCL initial, replace via private same-dir rename."""
    if os.geteuid()!=0: deny('LEASE_ROOT_WRITER')
    obj={'schema':'cf10_r125_disposable_lease_v0_1','attempt_id':attempt,'epoch':epoch,'source_head':source_head,'capsule_id':capsule_id,'revoked':revoked}
    data=encode(obj)
    if not replace:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try: os.write(fd,data);os.fsync(fd)
        finally: os.close(fd)
    else:
        # Caller MUST have checked the original root-owned lease before revoke.
        other=path.with_name('lease-replace.json')
        fd=os.open(other,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try: os.write(fd,data);os.fsync(fd)
        finally: os.close(fd)
        os.replace(other,path)
        d=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(d)
        finally:os.close(d)

def relay_once(conn, child_stdin, child_reader, *, rpc, lease:Path, source_head:str,capsule_id:str):
    """Three metadata frames, one real read-only call, then root-side revocation.

    After the first successful tools/call the same client sends a second request:
    it MUST be rejected locally, before forwarding anything to the MCP child.
    This is lab exhaustion/replay proof, NOT external operator revocation.
    """
    seen=set(); epoch='r125-fixture-epoch-1'; phase_count=0
    for phase in (0,1,2):
        secure_lease(lease,attempt=ATTEMPT,epoch=epoch,source_head=source_head,capsule_id=capsule_id,revoked=False)
        raw=recvline(conn);req=validate_metadata(raw,phase,seen)
        child_stdin.write(raw);child_stdin.flush();phase_count+=1
        if phase in (0,2):
            response=child_reader.read()
            if phase==0:rpc.validate_init(response,req['id'])
            else:rpc.validate_tools(response,req['id'])
            conn.sendall(encode(response))
    secure_lease(lease,attempt=ATTEMPT,epoch=epoch,source_head=source_head,capsule_id=capsule_id,revoked=False)
    req=validate_readonly_call(recvline(conn),seen)
    child_stdin.write(encode(req));child_stdin.flush();phase_count+=1
    response=child_reader.read(timeout=20)
    summary=check_response(response,req['id'])
    conn.sendall(encode(response))
    # Disable access to even this read-only capability for the same attempt.
    secure_lease(lease,attempt=ATTEMPT,epoch=epoch,source_head=source_head,capsule_id=capsule_id,revoked=False)
    write_lease(lease,attempt=ATTEMPT,epoch=epoch,source_head=source_head,capsule_id=capsule_id,revoked=True,replace=True)
    secure_lease(lease,attempt=ATTEMPT,epoch=epoch,source_head=source_head,capsule_id=capsule_id,revoked=True)
    again=recvline(conn)
    # Never forward a fifth request regardless of content.
    conn.sendall(encode({'jsonrpc':'2.0','id':parse(again).get('id'),'error':{'code':-32001,'message':'CF10_SESSION_REVOKED'}}))
    return {'metadata_frames':3,'read_only_tool_calls_forwarded':1,'post_revoke_forwarded':0,
            'replay_rejected':True,'fixture_lease_revoked':True,'rpc_frames_forwarded':phase_count,**summary}
