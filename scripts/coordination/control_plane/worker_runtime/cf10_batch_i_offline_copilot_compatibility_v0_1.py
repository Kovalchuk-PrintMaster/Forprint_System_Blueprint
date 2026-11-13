"""CF10 Batch I: exact pinned Copilot --version *disposable offline compatibility*.

Never authorizes a Worker. A successful offline CLI run proves only that the
pinned executable can start in one isolated systemd fixture. It proves NO
credentials, inference, tool restrictions, root-broker, or kernel 1->0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from scripts.coordination.control_plane.worker_runtime import cf10_r115_preclaim_executable_profile_v0_1 as r115

SCHEMA='cf10_batch_i_offline_copilot_compatibility_v0_1'
UNIT_RE=re.compile(r'forprint-cf10-batchi-[a-f0-9]{16}\.service\Z')
RUNNER_UID=996
RUNNER_GID=992

class OfflineHold(ValueError):pass

def deny(reason):raise OfflineHold('CF10_BATCH_I_'+reason)

def digest(raw):return hashlib.sha256(raw).hexdigest()

def source_check():
    if r115.COPILOT_PILOT_PATH!=Path('/usr/local/bin/forprint-copilot-1.0.107'):
        deny('PINNED_PATH_DRIFT')
    if r115.COPILOT_PILOT_SHA256!='985f0e1b1b3e734bc996324651307a076ae3deae21e3fa9f9af917983ce309c4':
        deny('PINNED_SHA_DRIFT')
    if r115.COPILOT_PILOT_BYTES!=205458240:deny('PINNED_LENGTH_DRIFT')
    return {'schema':SCHEMA,'source':'R115_CANONICAL_BINARY_PIN',
            'binary_sha256':r115.COPILOT_PILOT_SHA256,
            'executable_probe_argv':['--version'],
            'no_inference':True,'no_credentials':True,'no_claim':True,
            'no_live_admission':True,'no_kernel_1_to_0_attestation':True,
            'g1_g5_open':True}

def verify_pinned_binary():
    """One root-side readback; not an execfd/launch authorization mechanism."""
    source_check()
    if os.geteuid()!=0:deny('ROOT_ONLY')
    path=r115.COPILOT_PILOT_PATH
    for parent in (Path('/usr'),Path('/usr/local'),Path('/usr/local/bin')):
        st=parent.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid!=0 or st.st_mode & 0o022:
            deny('PINNED_PARENT_UNSAFE')
    try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    except OSError:deny('PINNED_MISSING_OR_LINKED')
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or st.st_nlink!=1 or \
           st.st_size!=r115.COPILOT_PILOT_BYTES or \
           stat.S_IMODE(st.st_mode)!=0o755:deny('PINNED_INODE_OR_MODE')
        h=hashlib.sha256()
        while True:
            data=os.read(fd,1024*1024)
            if not data:break
            h.update(data)
        if h.hexdigest()!=r115.COPILOT_PILOT_SHA256:deny('PINNED_SHA256')
        return {'binary_sha256':h.hexdigest(),'binary_size':st.st_size,
                'binary_mode':'0755','binary_owner':0}
    finally:os.close(fd)

def plan(*,unit,root):
    if type(unit) is not str or not UNIT_RE.fullmatch(unit):deny('UNIT_SCOPE')
    if type(root) is not str or root!='/run/'+unit.removesuffix('.service'):
        deny('DISPOSABLE_ROOT_SCOPE')
    props={
        'User':'forprint-runner',
        'Group':'forprint-runner',
        'KillMode':'control-group',
        'PrivateNetwork':'yes',
        'RestrictAddressFamilies':'AF_UNIX',
        'IPAddressDeny':'any',
        'InaccessiblePaths':'/var/lib/forprint-runner',
        'ProtectHome':'yes',
        'NoNewPrivileges':'yes',
        'ProtectSystem':'strict',
        'PrivateTmp':'yes',
        'ReadWritePaths':root,
        'UMask':'0077',
        'RuntimeMaxSec':'60',
    }
    return {'schema':SCHEMA,'unit':unit,'root':root,'properties':props,
            'profile_sha256':digest(json.dumps(props,sort_keys=True,separators=(',',':')).encode()),
            'only_argv':['--version'],'process_exec_profile':'DISPOSABLE_PYTHON_CHILD_CALLS_PINNED_COPILOT',
            'provider_auth_used':False,'copilot_version_invoked':False,
            'inference_called':False,'worker_claim_consumed':False,'live_admission':False,
            'g1_g5_open':True,'kernel_1_to_0_proven':False}

def review_observation(raw):
    fields={'schema','uid','gid','result_status','exit_code','version_found',
            'stdout_sha256','stderr_sha256','stdout_length','stderr_length',
            'ipv4_denied_errno','ipv6_denied_errno','fake_credential_errno',
            'client_pid','binary_command'}
    if type(raw) is not dict or set(raw)!=fields:deny('OBS_FIELDS')
    if raw['schema']!='cf10_batch_i_offline_cli_result_v0_1':deny('OBS_SCHEMA')
    if type(raw['uid']) is not int or raw['uid']!=RUNNER_UID or \
       type(raw['gid']) is not int or raw['gid']!=RUNNER_GID:deny('OBS_RUNNER')
    if raw['result_status']!='PASS_OFFLINE_VERSION' or raw['version_found'] is not True or \
       type(raw['exit_code']) is not int or raw['exit_code']!=0:deny('OBS_CLI_VERSION')
    if raw['binary_command']!='PINNED_COPILOT_VERSION_ONLY':deny('OBS_ARGV')
    for k in ('stdout_sha256','stderr_sha256'):
        if type(raw[k]) is not str or not re.fullmatch('[0-9a-f]{64}',raw[k]):deny('OBS_SHA')
    for k in ('stdout_length','stderr_length'):
        if type(raw[k]) is not int or not 0<=raw[k]<=4096:deny('OBS_SIZE')
    if type(raw['client_pid']) is not int or raw['client_pid']<=1:deny('OBS_CHILD_PID')
    for k in ('ipv4_denied_errno','ipv6_denied_errno'):
        if type(raw[k]) is not int or raw[k] not in (1,13,97):deny('OBS_IP_DENY')
    if type(raw['fake_credential_errno']) is not int or raw['fake_credential_errno'] not in (1,13):
        deny('OBS_CREDENTIAL_DENY')
    return {k:raw[k] for k in sorted(fields - {'schema'})}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['source-check'],required=True)
    p.parse_args(argv)
    print(json.dumps(source_check(),sort_keys=True,indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
