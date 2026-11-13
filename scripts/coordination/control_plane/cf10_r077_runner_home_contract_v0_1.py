"""CF10 R077: read-only dedicated provider HOME and systemd sandbox contract.

Does not create cache, change permissions, launch Worker, claim or attest CLI auth.
The systemd StateDirectory property grants precisely the runner's existing home
write access despite ProtectSystem=strict; no global /var/lib allowlisting.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import pwd
import stat
import subprocess
import uuid

HOME=Path('/var/lib/forprint-runner')
RUNNER='forprint-runner'
UID=996
GID=992
DIRECTORY='forprint-runner'
MODE=0o700

class HomeBlocked(RuntimeError): pass

def deny(code):raise HomeBlocked('CF10_R077_'+code)

def inspect_home(home:Path,*,uid:int,gid:int,account_home:str)->dict:
    """Pure read-only filesystem observation; fixture path permitted to tests only."""
    p=Path(home)
    if not p.is_absolute() or str(p)!=account_home or '..' in p.parts:
        deny('HOME_PATH_NOT_BOUND_TO_ACCOUNT')
    for ancestor in (p.parent.parent,p.parent,p):
        if ancestor.is_symlink():deny('HOME_SYMLINK_ANCESTOR')
        try:s=ancestor.lstat()
        except FileNotFoundError:deny('HOME_PARENT_MISSING')
        if not stat.S_ISDIR(s.st_mode):deny('HOME_PARENT_NOT_DIRECTORY')
    s=p.lstat()
    if s.st_uid!=uid or s.st_gid!=gid or stat.S_IMODE(s.st_mode)!=MODE:
        deny('RUNNER_HOME_UID_GID_OR_MODE')
    cache=p/'.cache'
    if cache.is_symlink():deny('CACHE_SYMLINK')
    if cache.exists():
        st=cache.lstat()
        if (not stat.S_ISDIR(st.st_mode) or st.st_uid!=uid or st.st_gid!=gid
                or (stat.S_IMODE(st.st_mode) & 0o077)):
            deny('CACHE_UNSAFE_EXISTING_INODE')
        state='EXISTS_PRIVATE'
    else:state='MISSING_ALLOWED_STATE_DIRECTORY_WILL_ENABLE_CREATE'
    return {'status':'RUNNER_HOME_INODE_VERIFIED_NON_AUTHORIZING',
            'runner_home':str(p),'uid':uid,'gid':gid,'mode':'0700',
            'cache_state':state,'home_write_test_performed':False,
            'worker_launched':False,'claim_consumed':False}

def assert_runner_home()->dict:
    if os.geteuid()!=0:deny('ROOT_READ_ONLY_INSPECTION_REQUIRED')
    acct=pwd.getpwnam(RUNNER)
    if (acct.pw_uid!=UID or acct.pw_gid!=GID or acct.pw_dir!=str(HOME)
            or acct.pw_shell!='/usr/sbin/nologin'):
        deny('RUNNER_ACCOUNT_BOUNDARY_DRIFT')
    # Do not permit symlink pivots from /var. Protect /var/lib parent identity.
    for path in (Path('/var'),Path('/var/lib')):
        if path.is_symlink():deny('RUNNER_PARENT_SYMLINK')
        s=path.lstat()
        if (not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or
                stat.S_IMODE(s.st_mode)&0o022):
            deny('RUNNER_PARENT_UNTRUSTED')
    return inspect_home(HOME,uid=UID,gid=GID,account_home=acct.pw_dir)

def assert_systemd_properties(props:dict, workspace:str|None=None,
                              logs:str|None=None)->bool:
    """No broad RW path; state-directory exception is exactly the runner HOME."""
    wanted={'User':RUNNER,'Group':RUNNER,'ProtectSystem':'strict',
            'ProtectHome':'yes','PrivateTmp':'yes',
            'StateDirectory':DIRECTORY,'StateDirectoryMode':'0700'}
    if not isinstance(props,dict) or any(props.get(k)!=v for k,v in wanted.items()):
        deny('SANDBOX_STATE_DIRECTORY_CONTRACT_DRIFT')
    if workspace is not None or logs is not None:
        if not workspace or not logs or not isinstance(workspace,str) or not isinstance(logs,str):
            deny('SCOPED_WRITABLE_PATHS_REQUIRED')
        if props.get('ReadWritePaths')!=workspace+' '+logs:
            deny('EXTRA_WRITABLE_PATHS_PROHIBITED')
        if '/var/lib' in props['ReadWritePaths']:
            deny('BROAD_GLOBAL_WRITE_PATH_PROHIBITED')
    return True

# Runs only a disposable mount-namespace check, NOT Copilot and NOT a Worker.
# The child creates the exact cache directory if absent, tests it, and removes
# only its own random probe file. It never writes a source/receipt/ledger file.
PROBE_CHILD = r'''import os,stat,sys,uuid
from pathlib import Path
p=Path('/var/lib/forprint-runner')
if os.geteuid()!=996 or os.getegid()!=992:sys.exit(81)
if os.environ.get('HOME')!=str(p):sys.exit(82)
st=p.lstat()
if not stat.S_ISDIR(st.st_mode) or st.st_uid!=996 or st.st_gid!=992 or stat.S_IMODE(st.st_mode)!=0o700:sys.exit(83)
c=p/'.cache'
if c.is_symlink():sys.exit(84)
try:c.mkdir(mode=0o700)
except FileExistsError:pass
st=c.lstat()
if not stat.S_ISDIR(st.st_mode) or st.st_uid!=996 or st.st_gid!=992 or stat.S_IMODE(st.st_mode)&0o077:sys.exit(85)
fd=os.open(c,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
name='.cf10-r077-'+uuid.uuid4().hex
try:
 f=os.open(name,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600,dir_fd=fd)
 try:os.write(f,b'R077_SANDBOX_PROBE')
 finally:os.close(f)
 os.unlink(name,dir_fd=fd)
finally:os.close(fd)
print('CF10_R077_EFFECTIVE_HOME_CACHE_WRITE=PASS')
'''

def disposable_sandbox_probe()->dict:
    if os.geteuid()!=0 or not os.isatty(0) or not os.isatty(1):
        deny('ROOT_INTERACTIVE_TTY_REQUIRED_FOR_PROBE')
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
    assert_runner_home()
    assert_systemd_properties(bound.EXPECTED_PROPERTIES)
    name='forprint-cf10-homeprobe-'+uuid.uuid4().hex[:16]
    props={**bound.EXPECTED_PROPERTIES,
           'WorkingDirectory':str(HOME),
           'Environment':'HOME='+str(HOME),
           'Type':'exec','Restart':'no','RuntimeMaxSec':'25s'}
    argv=['/usr/bin/systemd-run','--wait','--pipe','--collect','--quiet',
          '--unit='+name,'--description=ForPrint CF10 R077 disposable HOME probe',
          *['--property='+key+'='+value for key,value in sorted(props.items())],
          '--','/usr/bin/python3','-I','-B','-c',PROBE_CHILD]
    try:
        cp=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
               stderr=subprocess.PIPE,timeout=40,check=False,
               env={'PATH':'/usr/bin:/bin','LANG':'C'})
    except (OSError,subprocess.SubprocessError) as exc:
        deny('PROBE_UNAVAILABLE_'+type(exc).__name__)
    if cp.returncode!=0 or cp.stdout.count(b'CF10_R077_EFFECTIVE_HOME_CACHE_WRITE=PASS')!=1:
        deny('EFFECTIVE_SANDBOX_PROBE_BLOCKED_RC_'+str(cp.returncode))
    return {'status':'PASS_DISPOSABLE_SYSTEMD_HOME_CACHE_WRITE_NON_AUTHORIZING',
            'cache_path':str(HOME/'.cache'),'runner_uid':UID,'runner_gid':GID,
            'worker_launched':False,'owner_claim_consumed':False,
            'runner_home_modified_only_for_private_cache':True,
            'automatic_retry':False,'no_production_cutover':True}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode',choices=['inspect','probe'],required=True)
    ap.add_argument('--confirm',default='')
    args=ap.parse_args(argv)
    if args.mode=='probe':
        if args.confirm!='PROBE_CF10_R077_DISPOSABLE_HOME_NO_WORKER':
            deny('EXPLICIT_PROBE_CONFIRMATION_REQUIRED')
        print(json.dumps(disposable_sandbox_probe(),sort_keys=True,indent=2))
        return 0
    report=assert_runner_home()
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
    assert_systemd_properties(bound.EXPECTED_PROPERTIES)
    print(json.dumps({**report,'systemd_state_directory':'forprint-runner',
          'systemd_state_directory_mode':'0700','protect_system':'strict',
          'global_live_cutover':False,'effective_mount_probe_performed':False},
          sort_keys=True,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
