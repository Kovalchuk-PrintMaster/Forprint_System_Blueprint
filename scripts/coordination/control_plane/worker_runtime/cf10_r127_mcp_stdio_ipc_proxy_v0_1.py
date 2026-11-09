#!/usr/bin/env python3
"""CF10 R127: narrow, non-authorizing MCP STDIO-to-UDS bridge candidate.

NOT a Worker launcher or a root broker. This is a fixed read-only candidate
transport for a future reviewed Copilot cutover. It cannot grant a lease,
release, claim, or run commands. The R125/R126 root-side lease fence and
canonical independent Worker lifecycle remain mandatory. Current R115 rejects
this transport on the live path, by design.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import socket
import stat
import struct
import sys
from typing import BinaryIO

MAX_FRAME = 65536
CAPSULE = 'git-12c668e0cc30-sha256-5877e4f4e16fefecf16a6e50ea9e9a712d288c7e35fb726b05950226ab416de9'
SOCKET = re.compile(r'/run/forprint-cf10-r125-[a-f0-9]{16}/mcp\.sock\Z')
ID = re.compile(r'[A-Za-z0-9_.:-]{1,160}\Z')
EPOCH = re.compile(r'[A-Za-z0-9_.:-]{1,80}\Z')
SHA = re.compile(r'[a-f0-9]{40}\Z')
METHODS = ('initialize', 'notifications/initialized', 'tools/list', 'tools/call')
CAPABILITY = 'run_repo_head'

class IPCProxyHold(RuntimeError):
    pass

def deny(code: str):
    raise IPCProxyHold('CF10_R127_PROXY_HOLD_' + code)

def unique(pairs):
    doc = {}
    for k, v in pairs:
        if k in doc: deny('JSON_DUPLICATE_KEY')
        doc[k] = v
    return doc

def decode(frame: bytes) -> dict:
    if type(frame) is not bytes or not (2 <= len(frame) <= MAX_FRAME) or not frame.endswith(b'\n') or frame.count(b'\n') != 1:
        deny('FRAME_LENGTH')
    try: obj = json.loads(frame.decode('utf8', 'strict'), object_pairs_hook=unique)
    except (ValueError, UnicodeError, TypeError): deny('FRAME_JSON')
    if type(obj) is not dict: deny('FRAME_OBJECT')
    return obj

def encode(obj: dict) -> bytes:
    if type(obj) is not dict: deny('ENCODE_OBJECT')
    data = (json.dumps(obj, ensure_ascii=True, sort_keys=True, separators=(',', ':')) + '\n').encode('ascii')
    if len(data) > MAX_FRAME: deny('ENCODE_SIZE')
    return data

def read_frame(inp: BinaryIO) -> bytes:
    # Bounded read: no unbounded readline() on model-controlled stream.
    frame = inp.readline(MAX_FRAME + 1)
    if not frame: deny('EOF')
    if len(frame) > MAX_FRAME: deny('FRAME_OVERSIZE')
    decode(frame)
    return frame

def validate_identity(*, socket_path: Path, attempt: str, epoch: str, source_head: str, capsule_id: str):
    if (type(socket_path) is not Path and not isinstance(socket_path, Path)) or not socket_path.is_absolute() or not SOCKET.fullmatch(str(socket_path)):
        deny('SOCKET_PATH')
    if any(type(v) is not str for v in (attempt, epoch, source_head, capsule_id)):
        deny('IDENTITY_TYPE')
    if not ID.fullmatch(attempt) or not EPOCH.fullmatch(epoch) or not SHA.fullmatch(source_head) or capsule_id != CAPSULE:
        deny('IDENTITY_DRIFT')
    return True

def validate_request(req: dict, phase: int, seen: set):
    if type(req) is not dict or phase not in range(4): deny('REQUEST_SHAPE')
    method = METHODS[phase]
    if req.get('jsonrpc') != '2.0' or req.get('method') != method: deny('METHOD_ORDER')
    if phase == 1:
        if set(req) != {'jsonrpc', 'method'}: deny('NOTIFICATION_FIELDS')
        return None
    if set(req) != {'jsonrpc', 'id', 'method', 'params'}: deny('REQUEST_FIELDS')
    identity = req['id']
    if (type(identity) not in (str, int) or type(identity) is str and (not identity or len(identity) > 128)
        or type(identity) is int and not (0 <= identity <= 2**31 - 1)) or identity in seen:
        deny('REQUEST_ID')
    seen.add(identity)
    params = req['params']
    if type(params) is not dict: deny('PARAMS_OBJECT')
    if phase == 0:
        if set(params) != {'protocolVersion', 'capabilities', 'clientInfo'}: deny('INIT_FIELDS')
        if (type(params['protocolVersion']) is not str or len(params['protocolVersion']) > 32
            or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', params['protocolVersion'])): deny('INIT_PROTOCOL')
        if type(params['capabilities']) is not dict: deny('INIT_CAPABILITIES')
        client = params['clientInfo']
        if type(client) is not dict or set(client) != {'name', 'version'} or not all(type(client[x]) is str and 1 <= len(client[x]) <= 128 for x in client):
            deny('INIT_CLIENT')
    elif phase == 2:
        if params != {}: deny('LIST_PARAMS')
    elif params != {'name': CAPABILITY, 'arguments': {}}:
        deny('TOOL_DENIED')
    return identity

def validate_response(resp: dict, request_id, phase: int) -> dict:
    if (type(resp) is not dict or resp.get('jsonrpc') != '2.0' or resp.get('id') != request_id
        or 'error' in resp or type(resp.get('result')) is not dict):
        deny('RESPONSE_CORRUPT')
    result = resp['result']
    if phase == 2:
        tools = result.get('tools')
        if type(tools) is not list: deny('TOOLS_LIST')
        matches = [t for t in tools if type(t) is dict and t.get('name') == CAPABILITY]
        if len(matches) != 1: deny('TOOLS_ALLOWLIST')
        # The proxy exposes ONLY the fixed read-only capability. It does not
        # authorize execution; root broker must independently enforce the gate.
        resp = dict(resp); resp['result'] = {'tools': matches}
    elif phase == 3:
        if result.get('isError', False) is not False: deny('TOOL_ERROR')
        structured = result.get('structuredContent')
        if (type(structured) is not dict or structured.get('return_code') != 0
            or structured.get('timed_out') is not False or structured.get('outcome') != 'completed'):
            deny('TOOL_RESULT')
        authority = structured.get('authority')
        if type(authority) is not dict or not authority or any(type(value) is not bool or value for value in authority.values()):
            deny('AUTHORITY_WIDENED')
        if not (type(structured.get('evidence_digest')) is str and re.fullmatch('[a-f0-9]{64}', structured['evidence_digest'])):
            deny('EVIDENCE_DIGEST')
    return resp

def run_session(input_stream: BinaryIO, output_stream: BinaryIO, server: socket.socket) -> dict:
    """Four bounded protocol frames, one fixed read-only call, then EOF.

    The root broker *must* check R126 lease before each request, and must
    revoke/deny reuse. A proxy's own checks are never an authority source.
    """
    seen = set(); count = 0
    peer = server.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize('3i'))
    pid, uid, _ = struct.unpack('3i', peer)
    if pid <= 0 or uid != 0: deny('SERVER_NOT_ROOT')
    with server.makefile('rb', buffering=0) as reader:
        for phase in range(4):
            frame = read_frame(input_stream)
            req = decode(frame)
            request_id = validate_request(req, phase, seen)
            server.sendall(encode(req)); count += 1
            if phase == 1:
                continue  # MCP initialized notification has no response.
            response = validate_response(decode(read_frame(reader)), request_id, phase)
            output_stream.write(encode(response)); output_stream.flush()
    # Never forward any additional request, regardless of STDIN content.
    return {'frames_forwarded': count, 'read_only_calls_forwarded': 1,
            'extra_calls_allowed': False, 'authority_granted': False,
            'worker_launched': False}

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description='Source-only CF10 R127 STDIO IPC candidate, no Worker authority')
    p.add_argument('--socket', required=True)
    p.add_argument('--attempt-id', required=True)
    p.add_argument('--epoch', required=True)
    p.add_argument('--source-head', required=True)
    p.add_argument('--capsule-id', required=True)
    args = p.parse_args(argv)
    try:
        target = Path(args.socket)
        validate_identity(socket_path=target, attempt=args.attempt_id, epoch=args.epoch,
                          source_head=args.source_head, capsule_id=args.capsule_id)
        st = target.lstat()
        if not (stat.S_ISSOCK(st.st_mode) and st.st_uid == 0 and stat.S_IMODE(st.st_mode) == 0o660):
            deny('SOCKET_OWNER_MODE')
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(25)
        try:
            sock.connect(str(target))
            # Current live R115 refuses this path; this command is NOT a
            # production cutover, and has no access to root-owned lease.
            run_session(sys.stdin.buffer, sys.stdout.buffer, sock)
        finally:
            sock.close()
    except (IPCProxyHold, OSError, ValueError, KeyError, TypeError) as exc:
        code = str(exc) if isinstance(exc, IPCProxyHold) else 'CF10_R127_PROXY_HOLD_' + type(exc).__name__
        print(code, file=sys.stderr)
        return 3
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
