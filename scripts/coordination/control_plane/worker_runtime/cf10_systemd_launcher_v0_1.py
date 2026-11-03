"""CF10 modernized systemd Worker backend, intentionally NOT yet live-wired.

Transaction: owner/PAM claim (upstream) -> root receipt -> manifest -> held
systemd unit -> kernel/systemd observation -> canonical STARTED callback ->
root-only release marker -> worker exec. No Popen of Worker, no root Worker,
no automatic retry. Fail closed at every incomplete boundary.

The production entrypoint rejects live launches until a separately reviewed
canonical cutover. The executable core is tested with a disposable driver;
never grant authority through worker-provided args or environment variables.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import pwd
import grp
import secrets
import stat
import subprocess
import time
from collections.abc import Callable

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipts
from scripts.coordination.control_plane import blueprint_durable_storage_v0_1 as storage

RUNTIME=Path('/srv/software_development/forprint-worker-runtime')
BLUEPRINT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
GATES=RUNTIME/'forprint_system_blueprint/control_plane/launch_gates'
STORE=RUNTIME/'forprint_system_blueprint/control_plane/root_receipts'
ENTRY=BLUEPRINT/'scripts/coordination/control_plane/worker_runtime/cf10_systemd_gate_entry_v0_1.py'
SYSTEMD_RUN='/usr/bin/systemd-run'
SYSTEMCTL='/usr/bin/systemctl'
PYTHON='/usr/bin/python3'
LIVE_CUTOVER_ENABLED=False  # only flip by source-bound approval + complete release evidence

class SystemdLaunchBlocked(RuntimeError):pass

def deny(code:str):raise SystemdLaunchBlocked('CF10_LAUNCH_'+code)

def _sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def _json(data:dict)->bytes:return (json.dumps(data,sort_keys=True,separators=(',',':'))+'\n').encode()

def _root_directory(path:Path,mode:int):
    if path.is_symlink():deny('STATE_SYMLINK')
    try:st=path.lstat()
    except FileNotFoundError:deny('STATE_DIRECTORY_MISSING')
    if not stat.S_ISDIR(st.st_mode) or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=mode:
        deny('STATE_DIRECTORY_OWNER_MODE')

def _store_file(directory:Path,name:str,data:bytes,mode:int):
    if '/' in name or name in ('.','..') or not data or len(data)>16384:
        deny('FILE_SCOPE')
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC|os.O_NOFOLLOW
    fd=os.open(name,flags,mode,dir_fd=(dirfd:=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)))
    try:
        with os.fdopen(fd,'wb',closefd=False) as out:
            out.write(data);out.flush();os.fsync(out.fileno())
        os.fsync(dirfd)
    finally:
        os.close(fd);os.close(dirfd)

def _runner_account():
    account=pwd.getpwnam(bound.RUNNER)
    group=grp.getgrnam(bound.RUNNER)
    if account.pw_uid!=bound.UID or account.pw_gid!=bound.GID or group.gr_gid!=bound.GID or account.pw_shell!='/usr/sbin/nologin':
        deny('RUNNER_IDENTITY_DRIFT')
    return account

def _manifest(spec:bound.BoundedInput,unit:str,nonce:str,now:float)->bytes:
    return _json({'schema':'cf10_systemd_launch_manifest_v0_1',
        'attempt_id':spec.attempt_id,'source_head':spec.source_head,
        'argv':list(spec.argv), 'argv_sha256':_sha('\0'.join(spec.argv).encode()),
        'cwd':spec.workspace,'unit':unit,'gate_nonce':nonce,
        'expires_unix':now+120,'runner_uid':bound.UID,'runner_gid':bound.GID})

def build_command(spec:bound.BoundedInput,plan:dict,manifest:Path)->list[str]:
    bound.validate_plan(plan,spec)
    if manifest.parent!=GATES or not manifest.name.startswith('manifest-'):
        deny('GATE_SCOPE')
    # Runner sees only the authorized workspace; it never inherits root shell env.
    props={**bound.EXPECTED_PROPERTIES,
           'WorkingDirectory':spec.workspace,
           'ReadWritePaths':spec.workspace,
           'RuntimeMaxSec':str(spec.timeout_seconds+180)+'s',
           'Restart':'no','Type':'exec','ExitType':'cgroup'}
    # Bind stream destinations to the canonical attempt, never to caller strings.
    logs=RUNTIME/'forprint_system_blueprint'/'worker-01'/spec.attempt_id/'logs'
    props['StandardOutput']='append:'+str(logs/'stdout.log')
    props['StandardError']='append:'+str(logs/'stderr.log')
    props['ReadWritePaths']=spec.workspace+' '+str(logs)
    # Keep the gate within approved runtime, not the source repo's tmp/.
    return [SYSTEMD_RUN,'--no-block','--quiet','--remain-after-exit','--unit='+plan['identity']['unit'],
        '--description=ForPrint CF10 guarded Worker',
        *['--property='+k+'='+v for k,v in sorted(props.items())],
        '--',PYTHON,'-I','-B',str(ENTRY),str(manifest)]

def _show(unit:str,runner:Callable[[list[str]],subprocess.CompletedProcess]):
    properties=['Id','LoadState','ActiveState','MainPID','ControlGroup','User','Group','KillMode','Result','ExecMainStatus']
    result=runner([SYSTEMCTL,'show','--no-pager',*['--property='+p for p in properties],'--',unit])
    if result.returncode!=0:deny('SYSTEMCTL_SHOW_FAILED')
    try:lines=result.stdout.decode('utf8').splitlines();rows=dict(line.split('=',1) for line in lines)
    except (UnicodeError,ValueError):deny('SHOW_FORMAT')
    if len(rows)!=len(properties) or set(rows)!=set(properties):deny('SHOW_PROPERTIES')
    if rows['Id']!=unit:deny('SHOW_UNIT_MISMATCH')
    return rows

def _verify_held(unit:str,runner):
    vals=_show(unit,runner)
    if (vals['LoadState']!='loaded' or vals['ActiveState']!='active'
        or not vals['MainPID'].isdigit() or int(vals['MainPID'])<2
        or vals['ControlGroup']!='/system.slice/'+unit
        or vals['User']!=bound.RUNNER or vals['Group']!=bound.RUNNER
        or vals['KillMode']!='control-group'):
        deny('HELD_SYSTEMD_IDENTITY_NOT_PROVEN')
    return vals

def _stop(unit,runner):
    try:runner([SYSTEMCTL,'stop','--',unit])
    except Exception:pass

def _reserve_root_logs(spec:bound.BoundedInput)->None:
    """Reserve immutable root-owned stream inodes after claim, before systemd-run.

    Worker may write only via systemd-provisioned FDs. Reusing prior logs,
    links and non-root-controlled directory is prohibited. No tmp/ is used.
    """
    attempt=RUNTIME/'forprint_system_blueprint'/'worker-01'/spec.attempt_id
    directory=attempt/'logs'
    storage.require_persistent_path(directory,blueprint_root=BLUEPRINT)
    try:ds=directory.lstat()
    except FileNotFoundError:deny('LOG_DIRECTORY_MISSING')
    if (not stat.S_ISDIR(ds.st_mode) or ds.st_uid!=0 or
            stat.S_IMODE(ds.st_mode)&0o022 or directory.is_symlink()):
        deny('LOG_DIRECTORY_UNTRUSTED')
    # No hardlink or symlink endpoint can be redirected by the runner.
    for name in ('stdout.log','stderr.log'):
        path=directory/name
        if path.exists() or path.is_symlink():deny('LOG_ALREADY_PRESENT_NO_OVERWRITE')
    for name in ('stdout.log','stderr.log'):
        fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,
                   dir_fd=(dirfd:=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)))
        try:os.fsync(fd);os.fsync(dirfd)
        finally:os.close(fd);os.close(dirfd)

def _core(*,spec:bound.BoundedInput,plan:dict,started_callback:Callable[[dict],None],
          runner:Callable[[list[str]],subprocess.CompletedProcess],now:Callable[[],float]=time.time,
          sleep:Callable[[float],None]=time.sleep,root:Path=BLUEPRINT,gate_dir:Path=GATES,
          store:Path=STORE,require_real_roots=True):
    """Single-use transaction, test driver may replace driver/roots in isolated fixtures.

    The production entrypoint does NOT expose test injection to callers.
    """
    bound.validate_plan(plan,spec)
    if not callable(started_callback):deny('STARTED_CALLBACK_REQUIRED')
    if require_real_roots:
        if os.geteuid()!=0 or root!=BLUEPRINT or gate_dir!=GATES or store!=STORE:
            deny('ROOT_CANONICAL_SCOPE_REQUIRED')
        storage.require_runtime_root(spec.runtime_root,blueprint_root=root)
        storage.require_worker_workspace(spec.workspace,blueprint_root=root,attempt_id=spec.attempt_id)
        _runner_account()
        storage.require_root_receipt_store(store,blueprint_root=root)
        storage.require_persistent_path(gate_dir,blueprint_root=root)
        _root_directory(store,0o700)
        _root_directory(gate_dir,0o711)
        if not ENTRY.is_file() or ENTRY.is_symlink():deny('GATE_ENTRY_UNTRUSTED')
    else:
        # A disposable isolated scenario only. No attempts under production runtime.
        if gate_dir==GATES or store==STORE or not (gate_dir.is_relative_to(root) and store.is_relative_to(root)):
            deny('FIXTURE_ROOT_SCOPE')
        _root_directory(store,0o700);_root_directory(gate_dir,0o711)
    # Any occupied claim inode (including partial/corrupt) is permanently consumed.
    if (store/spec.attempt_id).exists() or (store/spec.attempt_id).is_symlink():
        deny('ALREADY_CONSUMED_NO_RETRY')
    unit=plan['identity']['unit']
    before=_show(unit,runner)
    if before['LoadState']!='not-found' or before['ActiveState'] not in ('inactive','failed'):
        deny('UNIT_ALREADY_EXISTS_OR_ACTIVE')
    # Irreversible O_EXCL claim precedes any service invocation.
    receipts.claim(private_store=store,attempt_id=spec.attempt_id,head=spec.source_head,
                   handoff_sha256=spec.handoff_sha256)
    receipts.append_observation(private_store=store,attempt_id=spec.attempt_id,
                   expected_head=spec.source_head,event='LAUNCH_REQUESTED')
    if require_real_roots:
        _reserve_root_logs(spec)
    nonce=secrets.token_hex(32)
    manifest=gate_dir/('manifest-'+nonce+'.json')
    raw=_manifest(spec,unit,nonce,now())
    _store_file(gate_dir,manifest.name,raw,0o644)
    command=build_command(spec,plan,GATES/manifest.name)
    # Only in disposable tests remap fixed gate path to the disposable equivalent.
    if gate_dir!=GATES:command[-1]=str(manifest)
    spawned=False
    try:
        cp=runner(command)
        if cp.returncode!=0:deny('SYSTEMD_RUN_FAILED')
        spawned=True
        # Wait for gate entry to be active; never assume systemd-run rc == Worker launch.
        for _ in range(30):
            try:observation=_verify_held(unit,runner);break
            except SystemdLaunchBlocked:
                sleep(.15)
        else:deny('HELD_SERVICE_NOT_VERIFIED')
        receipts.append_observation(private_store=store,attempt_id=spec.attempt_id,
                   expected_head=spec.source_head,event='SERVICE_OBSERVED')
        # Canonical ledger STARTED callback; release is strictly AFTER it returns.
        started_callback({'pid':int(observation['MainPID']), 'unit':unit,
                         'argv_sha256':plan['identity']['argv_sha256'],
                         'started_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
        _store_file(gate_dir,'release-'+nonce+'.json',
                   _json({'schema':'cf10_root_release_v0_1','manifest_sha256':_sha(raw)}),0o644)
        # The exec process is systemd-owned; return only as observation, not release.
        return {'state':'SYSTEMD_RELEASED_OBSERVE_WORKER', 'attempt_id':spec.attempt_id,
            'unit':unit,'pid':int(observation['MainPID']), 'source_head':spec.source_head,
            'process_started':True,'worker_result_accepted':False,'release_allowed':False,
            'automatic_retry':False,'systemd_launch':True}
    except BaseException:
        if spawned:_stop(unit,runner)  # failure to stop never permits retry
        try:receipts.append_observation(private_store=store,attempt_id=spec.attempt_id,
                    expected_head=spec.source_head,event='REVIEW_REQUIRED')
        except Exception:pass
        raise

def launch_after_owner_claim(*,spec:bound.BoundedInput,plan:dict,
                            started_callback:Callable[[dict],None])->dict:
    """Production API is sealed until a new source-controlled release decision.

    No environment flag, CLI argument or caller bool can lift this gate.
    """
    if LIVE_CUTOVER_ENABLED is not True:
        # CF10_SOURCE_BOUND_PILOT_BACKEND_BRANCH_VERIFIED
        # r053 is a dormant branch only.  Neither successful proof inspection
        # nor a caller-supplied value can reach _core through this branch.
        from scripts.coordination.control_plane import cf10_r052_owner_launch_guard_v0_1 as pilot_guard
        from scripts.coordination.control_plane import cf10_r053_dormant_pilot_bridge_v0_1 as dormant
        try:
            dormant.refuse_backend_launch(spec=spec, guard_module=pilot_guard)
        except dormant.PilotDormantBlocked:
            deny('PRODUCTION_CUTOVER_NOT_AUTHORIZED')
        deny('PRODUCTION_CUTOVER_NOT_AUTHORIZED')
    # The existing owner/PAM console and one-time claim remain compulsory.
    from scripts.coordination.control_plane import cf10_owner_pam_launch_v0_1 as owner
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    s=owner._SESSION.get()
    if (os.geteuid()!=0 or s is None or s.phase!='INNER_ENTERED'
            or s.attempt!=spec.attempt_id or s.task!=spec.task_prompt_id
            or s.head!=spec.source_head):
        deny('OWNER_PAM_CONTEXT_REQUIRED')
    folder=once.open_root_owned_state_dir()
    try:
        key=hashlib.sha256(('worker-01\0'+spec.attempt_id).encode()).hexdigest()
        fd=os.open('owner_attempt_'+key+'.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=folder)
        try:
            st=os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=0o600:
                deny('OWNER_CLAIM_INODE')
            doc=json.loads(os.read(fd,8192))
        finally:os.close(fd)
        if (doc.get('attempt_id')!=spec.attempt_id or doc.get('source_head')!=spec.source_head
                or doc.get('status')!='CONSUMED_BEFORE_SPAWN_NO_RETRY'):
            deny('OWNER_CLAIM_BINDING')
    finally:os.close(folder)
    def runner(args):
        return subprocess.run(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
             stderr=subprocess.PIPE,timeout=12,check=False,
             env={'PATH':'/usr/bin:/bin','LANG':'C'})
    return _core(spec=spec,plan=plan,started_callback=started_callback,runner=runner)
