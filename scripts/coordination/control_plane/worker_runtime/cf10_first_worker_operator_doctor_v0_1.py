#!/usr/bin/env python3
"""CF10 Y: real, read-only s01 operator doctor for the first governed Worker.

No token contents or CLI prompts are ever read or executed. Credential metadata
presence does not imply usable authentication. Designed to run by Make/CLI from
canonical repository, never from tmp in production.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from scripts.coordination.control_plane.worker_runtime import cf10_first_worker_critical_path_v0_1 as critical

SCHEMA='cf10_first_worker_operator_doctor_v0_1'
BINARY=Path('/usr/local/bin/forprint-copilot-1.0.107')
ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
MAX_SIZE=250_000_000

class DoctorHold(ValueError):pass

def deny(reason):raise DoctorHold('CF10_Y_DOCTOR_HOLD_'+reason)

def _digest_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as source:
        for data in iter(lambda:source.read(1_048_576),b''):h.update(data)
    return h.hexdigest()

def inspect_binary(path:Path=BINARY)->dict:
    """lstat/readback, root-owned pinned exact binary; never invoke it."""
    path=Path(path)
    if not path.is_absolute() or path.is_symlink():deny('BINARY_PATH')
    try:st=path.lstat()
    except OSError:deny('BINARY_MISSING')
    if (not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or
        stat.S_IMODE(st.st_mode)!=0o755 or not 0<st.st_size<=MAX_SIZE):
        deny('BINARY_OWNER_MODE_SIZE')
    digest=_digest_file(path)
    if digest!=critical.BIN_SHA:deny('BINARY_PIN_DRIFT')
    after=path.lstat()
    if (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
        deny('BINARY_CHANGED_DURING_HASH')
    return {'binary_sha256':digest,'pinned':True,'root_owned':True,'mode':'0755',
            'executable_invoked':False}

def inspect_auth_handle(path:Path|None)->dict:
    """Metadata-only check of an optional, *already provisioned* root-only file.

    Strictly no reads. Never copies or logs path or content; not an auth proof.
    """
    if path is None:
        return {'source':'UNCONFIGURED','root_owns_material':False,
            'group_or_world_access':False,'material_read':False,
            'passed_to_cli_env':False,'passed_to_child_tools':False,
            'credential_exchange_attested':False}
    path=Path(path)
    if (not path.is_absolute() or len(str(path))>400 or
        '/tmp/' in str(path) or str(path).startswith('/tmp') or
        str(path).startswith(str(ROOT)) or '..' in path.parts):
        deny('HANDLE_PATH_SCOPE')
    try:st=path.lstat(); pst=path.parent.lstat()
    except OSError:deny('HANDLE_MISSING')
    if (not stat.S_ISREG(st.st_mode) or st.st_nlink!=1 or
        st.st_uid!=0 or st.st_gid!=0 or stat.S_IMODE(st.st_mode)!=0o600 or
        not 0<st.st_size<16384 or
        not stat.S_ISDIR(pst.st_mode) or pst.st_uid!=0 or
        (stat.S_IMODE(pst.st_mode)&0o077)!=0 or path.is_symlink()):
        deny('HANDLE_PERMISSIONS')
    return {'source':'ROOT_EXTERNAL_HANDLE_REVIEW_ONLY','root_owns_material':True,
            'group_or_world_access':False,'material_read':False,
            'passed_to_cli_env':False,'passed_to_child_tools':False,
            'credential_exchange_attested':False}

def report(*,source_head:str,binary:dict,auth:dict,token_environment_names:list[str]=None)->dict:
    if token_environment_names is None:token_environment_names=[]
    if not isinstance(token_environment_names,list) or not all(type(x) is str for x in token_environment_names):
        deny('AUTH_ENV_TYPE')
    if any(x not in critical.SECRET_KEYS for x in token_environment_names):deny('AUTH_ENV_UNKNOWN')
    if len(token_environment_names)!=len(set(token_environment_names)):deny('AUTH_ENV_DUPLICATE')
    if not isinstance(binary,dict) or binary.get('pinned') is not True or binary.get('binary_sha256')!=critical.BIN_SHA:
        deny('BINARY_NOT_PINNED')
    if token_environment_names:
        # Credentials in the operator environment must not enter test subprocesses.
        deny('AUTH_ENV_MUST_BE_SCRUBBED_BEFORE_CHILD')
    fixture=critical.fixture()
    fixture['source_head']=source_head
    fixture['credential']=auth
    doc=critical.plan(**fixture)
    if doc['all_gates_open'] is not True or doc['worker_launched'] is not False:deny('AUTHORITY_DRIFT')
    return {'schema':SCHEMA,'result':'PASS_PRELIVE_CRITICAL_PATH_REVIEW',
        'source_head':source_head,'binary_attested':True,
        'credential_handle_metadata_valid':auth['root_owns_material'],
        'credential_contents_read':False,'auth_proven':False,
        'provider_egress_proven':False,'real_model_response_proven':False,
        'canonical_worker_executed':False,'live_terminal_ledger_proven':False,
        'gates':doc['gates'],'gates_open':True,
        'next_front':'ROOT_SIDE_CREDENTIAL_NONEXPOSURE_AND_PROVIDER_EGRESS_PILOT',
        'operator_action':'NO_LIVE_LAUNCH_UNTIL_INDEPENDENT_AUTH_EGRESS_ATTESTATION',
        'no_live_dispatch':True,'no_automatic_retry':True,
        'review_sha256':doc['review_sha256']}

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['inspect'],required=True)
    args=parser.parse_args(argv)
    # Never print / parse credential contents. One optional already-provisioned path.
    # The harness must scrub token env names before calling this program.
    present=sorted(n for n in critical.SECRET_KEYS if os.environ.get(n))
    if present:
        print('CF10_Y_DOCTOR=HOLD_AUTH_ENV_PRESENT_VALUES_NOT_READ')
        return 3
    try:
        from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
        if launcher.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_SWITCH_OPEN')
        binary=inspect_binary()
        external=os.environ.get('CF10_Y_ROOT_CREDENTIAL_HANDLE')
        auth=inspect_auth_handle(Path(external) if external else None)
        # Git head is supplied only by trusted guarded installer; no task IDs or
        # prior claim state can be derived from this CLI alone.
        import subprocess
        cmd=subprocess.run(['/usr/bin/git','-C',str(ROOT),'rev-parse','HEAD'],
          stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL,
          timeout=10,check=False,env={'PATH':'/usr/bin:/bin','LANG':'C'})
        if cmd.returncode or not re.fullmatch(rb'[a-f0-9]{40}\n?',cmd.stdout):deny('HEAD_READ')
        row=report(source_head=cmd.stdout.decode().strip(),binary=binary,auth=auth)
    except (DoctorHold,critical.AdmissionHold,ValueError,KeyError,OSError,TimeoutError) as exc:
        print('CF10_Y_DOCTOR=HOLD_'+type(exc).__name__)
        return 3
    print(json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=True))
    return 0
if __name__=='__main__':raise SystemExit(main())
