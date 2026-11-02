"""Disposable unprivileged service probe only. NEVER imports Blueprint/Worker code."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def emit(path):
    p=Path(path)
    data={'pid':os.getpid(),'ppid':os.getppid(),'uid':os.getuid(),
          'gid':os.getgid(),'sid':os.getsid(0)}
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as f:
        json.dump(data,f)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--child':
        emit(sys.argv[2]);time.sleep(90)
    elif len(sys.argv)==3:
        proc=subprocess.Popen([sys.executable,__file__,'--child',sys.argv[2]],
                              start_new_session=True,stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=True)
        emit(sys.argv[1]);time.sleep(90)
    else:
        raise SystemExit(2)
