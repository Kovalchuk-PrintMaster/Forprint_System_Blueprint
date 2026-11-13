"""Single-use disposable tool-worker isolation probe. No provider, no credentials.

The network probe ONLY attempts socket creation, never any outbound connect.
It reports to one local AF_UNIX root listener; server independently checks
SO_PEERCRED and /proc pid cgroup. No journal/console secret contents.
"""
import errno
import json
import os
import re
import socket
import sys
import time

def main(argv):
    if len(argv)!=4:return 71
    sock_path,canary,unit=argv[1:]
    if not re.fullmatch(r'forprint-cf10-batchf-[a-f0-9]{16}\.service',unit):return 72
    home='/run/'+unit[:-8]
    if sock_path != home+'/bridge.sock' or canary != home+'/fake_provider_credential.txt':
        return 73
    def attempt_family(family):
        try:
            s=socket.socket(family,socket.SOCK_STREAM)
        except OSError as exc:
            return {'denied':True,'errno':int(exc.errno or 0)}
        else:
            s.close()
            return {'denied':False,'errno':0}
    def attempt_canary():
        try:
            with open(canary,'rb') as f:f.read(1)
        except OSError as exc:
            return {'denied':True,'errno':int(exc.errno or 0)}
        return {'denied':False,'errno':0}
    payload={'schema':'cf10_batch_f_disposable_worker_observation_v0_1',
             'ipv4':attempt_family(socket.AF_INET),
             'ipv6':attempt_family(socket.AF_INET6),
             'fake_credential':attempt_canary(),
             'uid':os.getuid(),'gid':os.getgid()}
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(15)
        s.connect(sock_path)
        wire=(json.dumps(payload,separators=(',',':'),sort_keys=True)+'\n').encode('ascii')
        if len(wire)>2048:return 74
        s.sendall(wire)
        if s.recv(8)!=b'RECEIVED':return 75
    # Keep the cgroup populated until the root observer explicitly stops unit.
    while True:time.sleep(1)
if __name__=='__main__':raise SystemExit(main(sys.argv))
