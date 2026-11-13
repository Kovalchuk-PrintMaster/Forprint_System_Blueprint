"""Disposable retained-unit terminal child. No task, credential or network."""
from __future__ import annotations
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

COPILOT='/usr/local/bin/forprint-copilot-1.0.107'
UNIT=re.compile(r'forprint-cf10-batchl-[0-9a-f]{16}\.service\Z')

def read_line(sock,cap=1024):
    data=b''
    while not data.endswith(b'\n'):
        b=sock.recv(1)
        if not b or len(data)>=cap:raise ValueError('PROTO')
        data+=b
    return json.loads(data)

def send(sock,record):
    raw=(json.dumps(record,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
    if len(raw)>1024:raise ValueError('OVERSIZE')
    sock.sendall(raw)

def run(argv):
    if len(argv)!=4:return 73
    unit,socket_path,home=argv[1:]
    if UNIT.fullmatch(unit) is None:return 74
    root='/run/'+unit.removesuffix('.service')
    if socket_path!=root+'/control.sock' or home!=root+'/home':return 75
    if os.getuid()!=996 or os.getgid()!=992 or os.geteuid()!=996:return 76
    if not Path(home).is_dir() or Path(home).is_symlink():return 77
    try:
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
            s.settimeout(20);s.connect(socket_path)
            send(s,{'type':'READY','unit':unit,'uid':os.getuid(),'gid':os.getgid()})
            msg=read_line(s)
            if msg!={'type':'RELEASE','unit':unit}:return 78
            env={'PATH':'/usr/bin:/bin','HOME':home,'COPILOT_HOME':home+'/.copilot',
                'XDG_CONFIG_HOME':home+'/config','XDG_CACHE_HOME':home+'/cache',
                'XDG_DATA_HOME':home+'/data','LANG':'C','LC_ALL':'C','TERM':'dumb',
                'CI':'true','GIT_CONFIG_NOSYSTEM':'1','NO_COLOR':'1'}
            try:
                cp=subprocess.run([COPILOT,'--version'],env=env,cwd=home,
                    stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                    timeout=18,check=False)
                out=cp.stdout[:4097];err=cp.stderr[:4097]
                if len(out)>4096 or len(err)>4096:return 81
                version=bool(re.search(r'(?<![0-9])1\.0\.107(?![0-9])',out.decode('utf8','replace')))
                ok=cp.returncode==0 and version
                code=cp.returncode
            except (OSError,subprocess.TimeoutExpired):
                ok=False;code=-1
            send(s,{'type':'FINISHED','unit':unit,'copilot_version_pass':ok,
                    'copilot_exit_code':code,'no_inference':True})
            return 0 if ok else 82
    except (OSError,ValueError,UnicodeError):return 83

if __name__=='__main__':raise SystemExit(run(sys.argv))
