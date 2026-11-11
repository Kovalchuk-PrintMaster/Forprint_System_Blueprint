#!/usr/bin/env python3
"""Standalone, no-repo-import, disposable Copilot --version compatibility probe.

NO provider auth, prompts, task, tools, HTTP, proxy, or provider credentials.
Never logs command output; only bounded SHA/length/returncode metadata.
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

BIN='/usr/local/bin/forprint-copilot-1.0.107'
EXPECTED_VERSION='1.0.107'
FRAME_CAP=2048


def frame(sock,obj):
    data=(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
    if len(data)>FRAME_CAP:raise ValueError('FRAME_CAP')
    sock.sendall(data)

def recv(sock):
    buf=b''
    while not buf.endswith(b'\n'):
        part=sock.recv(256)
        if not part or len(buf)+len(part)>FRAME_CAP:raise ValueError('FRAME_RECEIVE')
        buf+=part
    return json.loads(buf.decode('ascii','strict'))

def prohibited_family(family):
    try:
        sock=socket.socket(family,socket.SOCK_STREAM)
    except OSError as exc:return exc.errno
    else:
        sock.close()
        return 0

def credential_denial(path):
    try:
        with open(path,'rb') as f:f.read(16)
    except OSError as exc:return exc.errno
    return 0

def offline_version(*,binary=BIN,home:Path):
    env={
        'PATH':'/usr/bin:/bin', 'HOME':str(home),
        'XDG_CONFIG_HOME':str(home/'config'),
        'XDG_CACHE_HOME':str(home/'cache'),
        'XDG_DATA_HOME':str(home/'data'),
        'LANG':'C','LC_ALL':'C','TERM':'dumb','NO_COLOR':'1',
        'CI':'true','GIT_CONFIG_NOSYSTEM':'1',
    }
    try:
        cp=subprocess.run([binary,'--version'],cwd=home,env=env,
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            timeout=20,check=False)
        out,err=cp.stdout,cp.stderr
        # Never export unbounded tool output or possible provider data.
        if len(out)>4096 or len(err)>4096:
            raise ValueError('CLI_OUTPUT_OVERSIZE')
        found=bool(re.search(r'(?<![0-9])1\.0\.107(?![0-9])',out.decode('utf8','replace')))
        return {'result_status':'PASS_OFFLINE_VERSION' if cp.returncode==0 and found else 'HOLD_VERSION',
            'exit_code':cp.returncode,'version_found':found,
            'stdout_sha256':hashlib.sha256(out).hexdigest(),
            'stderr_sha256':hashlib.sha256(err).hexdigest(),
            'stdout_length':len(out),'stderr_length':len(err)}
    except (OSError,subprocess.TimeoutExpired,ValueError):
        return {'result_status':'HOLD_OFFLINE_PROCESS',
            'exit_code':-1,'version_found':False,
            'stdout_sha256':hashlib.sha256(b'').hexdigest(),
            'stderr_sha256':hashlib.sha256(b'').hexdigest(),
            'stdout_length':0,'stderr_length':0}

def main(args):
    if len(args)!=5:return 72
    bridge,unit,home,fake=args[1:]
    if not re.fullmatch(r'forprint-cf10-batchi-[a-f0-9]{16}\.service',unit):return 73
    base=Path('/run')/unit.removesuffix('.service')
    if (bridge!=str(base/'bridge.sock') or home!=str(base/'home') or
        fake!=str(base/'fake_credential.txt')):return 74
    sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    try:
        sock.settimeout(32)
        sock.connect(bridge)
        frame(sock,{'schema':'cf10_batch_i_offline_cli_begin_v0_1','unit':unit,
                    'uid':os.getuid(),'gid':os.getgid()})
        if recv(sock)!={'command':'RUN_OFFLINE_VERSION_ONLY'}:return 75
        obs=offline_version(home=Path(home))
        obs.update(schema='cf10_batch_i_offline_cli_result_v0_1',
            uid=os.getuid(),gid=os.getgid(),
            ipv4_denied_errno=prohibited_family(socket.AF_INET),
            ipv6_denied_errno=prohibited_family(socket.AF_INET6),
            fake_credential_errno=credential_denial(fake),
            client_pid=os.getpid(),binary_command='PINNED_COPILOT_VERSION_ONLY')
        frame(sock,obs)
        if recv(sock)!={'command':'ACK_OBSERVATION'}:return 76
        return 0 if obs['result_status']=='PASS_OFFLINE_VERSION' else 77
    except (OSError,ValueError,UnicodeError):return 78
    finally:sock.close()
if __name__=='__main__':raise SystemExit(main(sys.argv))
