"""Disposable CF10 AD synthetic worker. Never imports/launches a provider.

Read-only detached process. All inputs are one-time parent-provided fixed values.
No shell, tools, network, source repo mutations, provider credentials, or ledger.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import socket
import sys

VERSION='cf10_ad_disposable_worker_child_v0_1'
UNIT=re.compile(r'forprint-cf10-batchad-[a-f0-9]{16}\.service\Z')
SHA64=re.compile(r'[a-f0-9]{64}\Z')
TASK='cf10-verification-tier-self-hardening-v0-1'

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')

def send(sock,obj):
    data=canonical(obj)+b'\n'
    if len(data)>2048:raise ValueError('frame oversize')
    sock.sendall(data)

def recv(sock):
    data=bytearray()
    while len(data)<2048:
        chunk=sock.recv(1)
        if not chunk:raise ValueError('eof')
        data.extend(chunk)
        if chunk==b'\n':
            return json.loads(bytes(data).decode('ascii'),object_pairs_hook=unique)
    raise ValueError('frame oversize')

def unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('duplicate key')
        result[k]=v
    return result

def worker_digest(task,nonce):
    return hashlib.sha256(('CF10_AD_SYNTHETIC_RESULT\0'+task+'\0'+nonce).encode('ascii')).hexdigest()

def main(argv):
    if len(argv)!=5:return 71
    unit,socket_path,nonce,task=argv[1:]
    if (UNIT.fullmatch(unit) is None or
            socket_path!='/run/'+unit.removesuffix('.service')+'/control.sock' or
            SHA64.fullmatch(nonce) is None or task!=TASK):return 72
    if (os.getuid(),os.getgid(),os.geteuid())!=(996,992,996):return 73
    try:
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
            sock.settimeout(35)
            sock.connect(socket_path)
            send(sock,{'schema':VERSION,'phase':'HELD','unit':unit,
                       'task_id':task,'nonce_sha256':hashlib.sha256(nonce.encode()).hexdigest()})
            frame=recv(sock)
            if frame!={'schema':VERSION,'phase':'RELEASE_ONE_DISPOSABLE',
                       'unit':unit,'nonce':nonce,'task_id':task}:
                return 74
            send(sock,{'schema':VERSION,'phase':'RESULT','unit':unit,'task_id':task,
                       'result_kind':'SYNTHETIC_READONLY_NON_AI',
                       'result_sha256':worker_digest(task,nonce)})
            verdict=recv(sock)
            if verdict!={'schema':VERSION,'phase':'RESULT_RECEIVED','unit':unit,
                         'result_sha256':worker_digest(task,nonce)}:
                return 75
            return 0
    except (OSError,ValueError,UnicodeError,TypeError):return 76

if __name__=='__main__':raise SystemExit(main(sys.argv))
