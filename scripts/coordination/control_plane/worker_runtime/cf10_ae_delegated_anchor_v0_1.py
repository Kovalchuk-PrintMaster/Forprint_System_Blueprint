"""Disposable AE systemd-main anchor, NOT a Worker or canonical launcher.

Keeps the containing systemd unit populated until a separate delegated leaf
Worker cgroup reaches 0, verified by the root controller. No provider/tools,
secrets, real network, direct ledger, or production activation.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

SCHEMA = 'cf10_ae_delegated_anchor_v0_1'
UNIT = re.compile(r'forprint-cf10-batchad-[0-9a-f]{16}\.service\Z')
SHA64 = re.compile(r'[0-9a-f]{64}\Z')
TASK = 'cf10-verification-tier-self-hardening-v0-1'


def encode(record: dict) -> bytes:
    raw = (json.dumps(record, sort_keys=True, separators=(',', ':'), ensure_ascii=True)+'\n').encode('ascii')
    if len(raw)>2048:raise ValueError('frame too large')
    return raw


def unique(pairs):
    ret={}
    for key,val in pairs:
        if key in ret:raise ValueError('duplicate field')
        ret[key]=val
    return ret


def recv(sock:socket.socket)->dict:
    raw=bytearray()
    while len(raw)<2048:
        part=sock.recv(1)
        if not part:raise ValueError('unexpected eof')
        raw.extend(part)
        if part==b'\n':
            return json.loads(raw.decode('ascii','strict'), object_pairs_hook=unique)
    raise ValueError('oversize')


def send(sock:socket.socket,record:dict)->None:
    sock.sendall(encode(record))


def sanitized_env()->dict[str,str]:
    return {'PATH':'/usr/bin:/bin','HOME':'/nonexistent','LANG':'C','LC_ALL':'C',
            'PYTHONDONTWRITEBYTECODE':'1','GIT_TERMINAL_PROMPT':'0'}


def validate_args(argv:list[str])->tuple[str,str,str,str,str,str]:
    if len(argv)!=7:raise ValueError('argv length')
    unit,anchor_path,worker_path,childfile,nonce,task=argv[1:]
    root='/run/'+unit.removesuffix('.service')
    if (not UNIT.fullmatch(unit) or anchor_path!=root+'/anchor.sock' or
        worker_path!=root+'/control.sock' or childfile!=root+'/child.py' or
        not SHA64.fullmatch(nonce) or task!=TASK):raise ValueError('argv values')
    if (os.getuid(),os.getgid(),os.geteuid())!=(996,992,996):raise ValueError('runner identity')
    return unit,anchor_path,worker_path,childfile,nonce,task


def run(argv:list[str])->int:
    try:
        unit,anchor_path,worker_path,childfile,nonce,task=validate_args(argv)
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
            sock.settimeout(40)
            sock.connect(anchor_path)
            send(sock,{'schema':SCHEMA,'event':'ANCHOR_HELD','unit':unit,
                'nonce_sha256':hashlib.sha256(nonce.encode()).hexdigest()})
            if recv(sock)!={'schema':SCHEMA,'event':'SPAWN_ONE','unit':unit,'nonce':nonce}:
                return 77
            cmd=['/usr/bin/python3','-I','-B',childfile,unit,worker_path,nonce,task]
            with subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL,env=sanitized_env(),cwd='/',close_fds=True) as proc:
                send(sock,{'schema':SCHEMA,'event':'WORKER_SPAWNED','unit':unit,'pid':proc.pid})
                if recv(sock)!={'schema':SCHEMA,'event':'FINALIZE_AFTER_PINNED_ZERO',
                                 'unit':unit,'pid':proc.pid}:
                    return 78
                try:status=proc.wait(timeout=8)
                except subprocess.TimeoutExpired:return 79
                send(sock,{'schema':SCHEMA,'event':'WORKER_REAPED','unit':unit,
                           'pid':proc.pid,'exit_code':status})
                return 0 if status==0 else 80
    except (OSError,ValueError,TypeError,UnicodeError):
        return 81

if __name__=='__main__':raise SystemExit(run(sys.argv))
