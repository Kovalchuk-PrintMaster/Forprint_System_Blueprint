"""CF-10 r024 disposable systemd service fixture. Non-authorizing, not a Worker launcher.

This file never touches production attempts. The only systemd mutation is a uniquely
named transient fixture unit, created after an explicit confirmation and stopped
in a finally block. Fail closed on unresolved process teardown.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import pwd
import grp
import re
import secrets
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone

PINNED_HEAD = 'e99aedbed976e8f809db471ee06888f304df0965'
RUNNER = 'forprint-runner'
UID = 996
GID = 992
PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
UNIT_RE = re.compile(r'^forprint-cf10-r024-fixture-[0-9a-f]{12}\.service$')
CGROUP = Path('/sys/fs/cgroup')

class FixtureBlocked(RuntimeError):
    pass


def require(cond, message):
    if not cond:
        raise FixtureBlocked(message)


def cmd(argv, *, timeout=15, check=True):
    cp = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout, check=False)
    if check and cp.returncode != 0:
        raise FixtureBlocked('COMMAND_FAILED: ' + ' '.join(argv[:2]) + f' rc={cp.returncode} ' + cp.stderr[-320:])
    return cp


def pinned_preflight(*, repo=PROJECT):
    require(os.geteuid() == 0, 'ROOT_REQUIRED_FOR_FIXTURE')
    require(repo.is_dir() and (repo/'.git').exists(), 'PROJECT_ROOT_MISSING')
    require(cmd(['git', '-C', str(repo), 'rev-parse', 'HEAD']).stdout.strip() == PINNED_HEAD, 'HEAD_DRIFT')
    account = pwd.getpwnam(RUNNER)
    group = grp.getgrnam(RUNNER)
    require(account.pw_uid == UID and account.pw_gid == GID and group.gr_gid == GID, 'RUNNER_IDENTITY_DRIFT')
    require(account.pw_shell.endswith('/nologin'), 'RUNNER_SHELL_DRIFT')
    require(account.pw_dir == '/var/lib/forprint-runner', 'RUNNER_HOME_DRIFT')
    require(Path('/run').is_dir(), 'RUN_NOT_MOUNTED')
    require((CGROUP/'cgroup.controllers').exists(), 'CGROUP_V2_REQUIRED')
    require(shutil.which('systemctl') and shutil.which('systemd-run'), 'SYSTEMD_TOOLS_MISSING')
    require(Path('/run/systemd/system').is_dir(), 'SYSTEMD_NOT_BOOTED')
    require(Path('/usr/bin/python3').is_file(), 'PYTHON_UNAVAILABLE')
    return {'head': PINNED_HEAD, 'uid': UID, 'gid': GID, 'systemd_booted': True, 'cgroup2': True,
            'authorization_issued': False, 'worker_started': False}


def show_unit(unit):
    require(bool(UNIT_RE.fullmatch(unit)), 'INVALID_UNIT_NAME')
    cp = cmd(['systemctl','show',unit,'--no-pager','--property=LoadState','--property=ActiveState',
              '--property=SubState','--property=MainPID','--property=ControlGroup',
              '--property=User','--property=Group','--property=KillMode',
              '--property=Delegate','--property=NoNewPrivileges','--property=ProtectControlGroups'],check=False)
    require(cp.returncode == 0, 'SYSTEMCTL_SHOW_FAILED')
    out = {}
    for line in cp.stdout.splitlines():
        if '=' in line:
            k,v=line.split('=',1)
            out[k] = v
    return out


def proc_identity(pid):
    require(isinstance(pid,int) and pid > 0, 'INVALID_PID')
    stat_path=Path(f'/proc/{pid}/stat')
    status_path=Path(f'/proc/{pid}/status')
    cg_path=Path(f'/proc/{pid}/cgroup')
    try:
        raw=stat_path.read_text()
        parts=raw[raw.rfind(')')+2:].split()
        state=parts[0]
        starttime=int(parts[19])
        ids={}
        for line in status_path.read_text().splitlines():
            if line.startswith(('Uid:', 'Gid:')):
                k,rest=line.split(':',1)
                ids[k]=int(rest.split()[0])
        cgroups=[line.strip() for line in cg_path.read_text().splitlines() if line.startswith('0::')]
        require(len(cgroups)==1, 'CGROUP_NOT_UNIFIED')
        return {'pid':pid,'state':state,'starttime':starttime,'uid':ids['Uid'],'gid':ids['Gid'],
                'cgroup':cgroups[0][3:]}
    except (FileNotFoundError, ProcessLookupError):
        return None


def same_process_alive(proof):
    current = proc_identity(int(proof['pid']))
    return bool(current and current['starttime']==proof['starttime'] and current['state']!='Z')


def bounded_json(path, *, max_bytes=2048):
    require(path.is_file() and not path.is_symlink(), 'PROBE_REPORT_MISSING')
    require(path.stat().st_size <= max_bytes, 'PROBE_REPORT_OVERSIZE')
    data=json.loads(path.read_text())
    require(isinstance(data,dict) and isinstance(data.get('pid'),int), 'PROBE_REPORT_INVALID')
    return data


def validate_membership(proof, control_group):
    require(control_group.startswith('/system.slice/forprint-cf10-r024-fixture-') and control_group.endswith('.service'),
            'UNEXPECTED_CGROUP')
    require(proof and proof['uid']==UID and proof['gid']==GID, 'RUNNER_UID_NOT_PROVEN')
    require(proof['cgroup']==control_group or proof['cgroup'].startswith(control_group+'/'), 'ESCAPED_CGROUP')
    return True


def wait_for_files(paths, timeout=14):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        if all(p.is_file() for p in paths):
            return
        time.sleep(.2)
    raise FixtureBlocked('FIXTURE_PROCESS_REPORT_TIMEOUT')


def stop_and_check(unit, proofs, expected_group):
    # Never stop a unit without exact prefix and nonce.
    require(bool(UNIT_RE.fullmatch(unit)), 'INVALID_UNIT_NAME')
    stop=cmd(['systemctl','stop',unit], timeout=18,check=False)
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        if not any(same_process_alive(p) for p in proofs):
            break
        time.sleep(.25)
    live=[p['pid'] for p in proofs if same_process_alive(p)]
    state=show_unit(unit)
    cpath=CGROUP / expected_group.lstrip('/') if expected_group and expected_group.startswith('/') else None
    populated = None
    if cpath and cpath.is_file():
        raise FixtureBlocked('CGROUP_PATH_NOT_DIRECTORY')
    if cpath and cpath.is_dir():
        event=cpath/'cgroup.events'
        if event.exists():
            for line in event.read_text().splitlines():
                if line.startswith('populated '): populated=line.split()[1]
    require(not live, 'CHILD_PROCESS_SURVIVED_STOP:' + repr(live))
    require(state.get('ActiveState') in ('inactive','failed') or state.get('LoadState')=='not-found',
            'TRANSIENT_UNIT_STILL_ACTIVE')
    require(populated in ('0',None), 'CGROUP_STILL_POPULATED')
    return {'unit_stopped':stop.returncode==0, 'all_sampled_pids_gone':True,
            'cgroup_empty_or_removed':True, 'after_state':state.get('ActiveState','unknown')}



def run_fixture(probe_path, *, repo=PROJECT):
    pinned_preflight(repo=repo)
    source = Path(probe_path)
    expected = repo / 'scripts/validation/cf10_r024_probe_v0_1.py'
    require(source == expected and source.is_file() and not source.is_symlink(), 'PROBE_CANONICAL_PATH_REQUIRED')
    require(hashlib.sha256(source.read_bytes()).hexdigest() == '18f326f242244e05969524ab8ef8829db4c005f5c5ce92eaa7ff228a9f9667c7',
            'PROBE_SOURCE_DRIFT')
    nonce=secrets.token_hex(6)
    unit='forprint-cf10-r024-fixture-'+nonce+'.service'
    basedir=Path('/run') / ('forprint-cf10-r024-fixture-'+nonce)
    require(not basedir.exists(), 'FIXTURE_PATH_COLLISION')
    require(show_unit(unit).get('LoadState','not-found')=='not-found', 'FIXTURE_UNIT_COLLISION')
    # NOTE service test runs exactly one bounded program; NOT the Worker launcher.
    basedir.mkdir(mode=0o755)
    io=basedir/'runner_io'; io.mkdir(mode=0o700)
    os.chown(io,UID,GID)
    target=basedir/'probe.py'
    target.write_bytes(Path(probe_path).read_bytes())
    target.chmod(0o644)
    require(target.stat().st_uid==0, 'TEST_SOURCE_NOT_ROOT_OWNED')
    parent_file=io/'parent.json'; child_file=io/'child.json'
    properties=[
        'User='+RUNNER,'Group='+RUNNER,'KillMode=control-group',
        'Delegate=no','NoNewPrivileges=yes','ProtectControlGroups=yes',
        'ProtectSystem=strict','ProtectHome=yes','PrivateTmp=yes',
        'PrivateDevices=yes','RestrictNamespaces=yes','RestrictSUIDSGID=yes',
        'CapabilityBoundingSet=','AmbientCapabilities=',
        'TasksMax=16','TimeoutStopSec=4s','SendSIGKILL=yes',
        'UMask=0077','ReadWritePaths='+str(io),
    ]
    args=['systemd-run','--unit='+unit,'--description=ForPrint CF10 disposable quiescence fixture']
    args.extend(['--property='+p for p in properties])
    args.extend(['/usr/bin/python3',str(target),str(parent_file),str(child_file)])
    receipt={'schema':'cf10_systemd_disposable_supervisor_gate_r024',
             'head':PINNED_HEAD,'unit':unit,'operator_approval_for_live_worker':False,
             'live_worker_launched':False, 'attempt_mutated':False,
             'status':'BLOCKED_PENDING_FIXTURE', 'timestamp_utc':datetime.now(timezone.utc).isoformat()}
    attempted=False; teardown_ok=False; proofs=[]; control_group=''
    try:
        attempted=True
        cp=cmd(args,timeout=20)
        receipt['start_rc']=cp.returncode
        wait_for_files([parent_file,child_file])
        parent=bounded_json(parent_file); child=bounded_json(child_file)
        require(parent['pid']!=child['pid'], 'FORK_NOT_OBSERVED')
        require(parent.get('uid')==UID and child.get('uid')==UID, 'UID_DRIFT_PROBE')
        require(child.get('sid')==child.get('pid'), 'SETSID_NOT_PROVEN')
        state=show_unit(unit)
        control_group=state.get('ControlGroup','')
        require(state.get('ActiveState')=='active', 'UNIT_NOT_ACTIVE')
        require(state.get('MainPID')==str(parent['pid']), 'MAIN_PID_UNBOUND')
        require(state.get('User')==RUNNER and state.get('Group')==RUNNER, 'UNIT_IDENTITY_UNBOUND')
        require(state.get('KillMode')=='control-group', 'UNIT_KILL_MODE_WRONG')
        require(state.get('Delegate')=='no','UNIT_DELEGATION_ENABLED')
        require(state.get('NoNewPrivileges')=='yes','UNIT_NNP_DISABLED')
        require(state.get('ProtectControlGroups')=='yes','UNIT_CGROUP_ACCESS_UNPROTECTED')
        for p in (parent,child):
            proof=proc_identity(p['pid']); validate_membership(proof,control_group)
            proofs.append(proof)
        receipt.update({'parent_pid':parent['pid'],'child_pid':child['pid'],
                        'runner_uid_proven':True,'setsid_child_contained':True,
                        'systemd_properties_verified':True,'control_group':control_group,
                        'fixture_started':True})
    except Exception as e:
        receipt['error']=type(e).__name__+': '+str(e)[:280]
    finally:
        if attempted:
            try:
                if not control_group:
                    before_stop=show_unit(unit)
                    control_group=before_stop.get('ControlGroup','')
                teardown=stop_and_check(unit,proofs,control_group)
                receipt['teardown']=teardown
                teardown_ok=(teardown['unit_stopped'] and teardown['all_sampled_pids_gone'] and teardown['cgroup_empty_or_removed']
                             and (bool(proofs) or not control_group))
            except Exception as e:
                receipt['teardown_error']=type(e).__name__+': '+str(e)[:280]
        else:
            receipt['teardown']={'unit_was_not_attempted':True}
            teardown_ok=True
        # Do NOT delete possibly running fixture scripts when teardown is uncertain.
        if teardown_ok:
            shutil.rmtree(basedir)
            receipt['test_directory_removed']=True
        else:
            receipt['test_directory_removed']=False
            receipt['manual_review_required']=True
    if receipt.get('systemd_properties_verified') and receipt.get('setsid_child_contained') and teardown_ok:
        receipt['status']='PASS_DISPOSABLE_ONLY_NON_AUTHORIZING'
    else:
        receipt['status']='BLOCKED_DISPOSABLE_FIXTURE'
    receipt['process_quiescence_proven_for_production']=False
    receipt['production_promotion_allowed']=False
    return receipt
