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
import subprocess

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


class OfflineProbeFailure(ValueError):
    """Allowlisted metadata only; never pass CLI output or environment to parent."""
    CODES={'EXEC_OSERROR','TIMEOUT','NONZERO_EXIT','OUTPUT_TYPE','OUTPUT_OVERSIZE',
           'OUTPUT_NUL','OUTPUT_ENCODING','VERSION_NOT_OBSERVED','PROBE_INTERNAL'}
    def __init__(self,code,*,return_code=None,os_errno=None,stdout=b'',stderr=b''):
        assert code in self.CODES
        if type(return_code) is not int or not -255<=return_code<=255:return_code=None
        if type(os_errno) is not int or not 1<=os_errno<=4095:os_errno=None
        b1=stdout if type(stdout) is bytes else b''
        b2=stderr if type(stderr) is bytes else b''
        # Hash only the first 4KiB, keep capped sizes; no raw stderr or tokens.
        self.record={'failure_code':code,'return_code':return_code,
           'os_errno':os_errno,'stdout_bytes':min(len(b1),65535),
           'stderr_bytes':min(len(b2),65535),
           'stdout_sha256':hashlib.sha256(b1[:4096]).hexdigest(),
           'stderr_sha256':hashlib.sha256(b2[:4096]).hexdigest()}
        super().__init__(code)

def offline_version_probe(*, runner=subprocess.run):
    """Non-authorizing offline executable smoke in worker cgroup.

    The child inherits a scrubbed environment from AE's anchor, but passes an
    even narrower env to the real CLI. This is NOT a provider authentication
    or inference check and deliberately cannot take arbitrary arguments.
    """
    env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent','XDG_CONFIG_HOME':'/nonexistent',
         'LANG':'C','LC_ALL':'C','GIT_TERMINAL_PROMPT':'0','NO_COLOR':'1'}
    if any(k in env for k in ('COPILOT_GITHUB_TOKEN','GH_TOKEN','GITHUB_TOKEN',
                              'OPENAI_API_KEY','ANTHROPIC_API_KEY',
                              'COPILOT_PROVIDER_API_KEY')):
        raise ValueError('secret env')
    cmd=['/usr/local/bin/forprint-copilot-1.0.107','--version']
    try:
        cp=runner(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE,cwd='/',env=env,timeout=18,check=False)
    except subprocess.TimeoutExpired as e:
        raise OfflineProbeFailure('TIMEOUT',stdout=e.stdout,stderr=e.stderr) from None
    except OSError as e:
        raise OfflineProbeFailure('EXEC_OSERROR',os_errno=e.errno) from None
    if (type(cp.stdout) is not bytes or type(cp.stderr) is not bytes
            or type(cp.returncode) is not int):
        raise OfflineProbeFailure('OUTPUT_TYPE')
    out,err=cp.stdout,cp.stderr
    if cp.returncode!=0:
        raise OfflineProbeFailure('NONZERO_EXIT',return_code=cp.returncode,
                                  stdout=out,stderr=err)
    if len(out)>4096 or len(err)>4096:
        raise OfflineProbeFailure('OUTPUT_OVERSIZE',stdout=out,stderr=err)
    if b'\x00' in out+err:
        raise OfflineProbeFailure('OUTPUT_NUL',stdout=out,stderr=err)
    try:text=(out+b'\n'+err).decode('utf-8','strict')
    except UnicodeDecodeError:
        raise OfflineProbeFailure('OUTPUT_ENCODING',stdout=out,stderr=err) from None
    if '1.0.107' not in text:
        raise OfflineProbeFailure('VERSION_NOT_OBSERVED',stdout=out,stderr=err)
    return {'exit_code':0,'stdout_sha256':hashlib.sha256(cp.stdout).hexdigest(),
       'stderr_sha256':hashlib.sha256(cp.stderr).hexdigest(),
       'stdout_bytes':len(cp.stdout),'stderr_bytes':len(cp.stderr),
       'version_1_0_107_observed':True,'argv_mode':'PINNED_COPILOT_VERSION_ONLY',
       'credentials_passed':False,'provider_inference':False}


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
            legacy={'schema':VERSION,'phase':'RELEASE_ONE_DISPOSABLE',
                       'unit':unit,'nonce':nonce,'task_id':task}
            offline={**legacy,'offline_copilot_version':True}
            if frame!=legacy and frame!=offline:
                return 74
            if frame==offline:
                try:probe=offline_version_probe()
                except OfflineProbeFailure as exc:
                    send(sock,{'schema':VERSION,'phase':'COPILOT_OFFLINE_VERSION_HOLD',
                        'unit':unit,'nonce_sha256':hashlib.sha256(nonce.encode()).hexdigest(),
                        **exc.record})
                    return 77
                except (ValueError,TypeError,UnicodeError):
                    exc=OfflineProbeFailure('PROBE_INTERNAL')
                    send(sock,{'schema':VERSION,'phase':'COPILOT_OFFLINE_VERSION_HOLD',
                        'unit':unit,'nonce_sha256':hashlib.sha256(nonce.encode()).hexdigest(),
                        **exc.record})
                    return 77
                send(sock,{'schema':VERSION,'phase':'COPILOT_OFFLINE_VERSION_PROOF',
                    'unit':unit,'nonce_sha256':hashlib.sha256(nonce.encode()).hexdigest(),
                    **probe})
                ack=recv(sock)
                if ack!={'schema':VERSION,'phase':'OFFLINE_PROOF_ACCEPTED',
                          'unit':unit,'nonce_sha256':hashlib.sha256(nonce.encode()).hexdigest()}:
                    return 78
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
