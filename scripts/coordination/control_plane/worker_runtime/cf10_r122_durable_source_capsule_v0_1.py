#!/usr/bin/env python3
"""CF10 R122: root-owned, versioned *source-only* MCP runtime capsule.

Never invokes Copilot, MCP tools or Worker. No claim, release, ledger,
credentials, provider network, unit deployment or kernel-policy change.
R121 proved the *disposable* source capsule; this component safely publishes
and re-verifies its Git-object source bytes in durable state outside tmp/.
This artifact is non-authorizing; invocation_adapter and R118 gate are unchanged.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import shutil
import stat
import subprocess
import sys

PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
PINNED_HEAD = '12c668e0cc309bd1162154ae12f7281603cf7bfa'
PINNED_BRANCH = 'audit/blueprint-inventory-refresh-2026-07-29'
STORE = Path('/var/lib/forprint-cf10/runtime-capsules')
RUNNER = 'forprint-runner'
RUNNER_UID = 996
RUNNER_GID = 992
MCP = 'scripts/coordination/control_plane/worker_runtime/worker_validation_mcp.py'
SUITE = 'scripts/validation/run_validation_suite_v0_1.py'
SCHEMA = 'forprint_cf10_r122_durable_source_capsule_v0_1'
MAX_TREE_BYTES = 8_000_000
MAX_FILES = 9000
MAX_BLOB = 2_000_000
MAX_TOTAL = 96_000_000
SHA1 = re.compile(r'^[0-9a-f]{40}$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')
SCOPE = re.compile(r'^(?:scripts|coordination)/[A-Za-z0-9_./-]{1,220}$')
PREFIX = 'git-' + PINNED_HEAD[:12] + '-sha256-'
AUTHORITY = {
    'worker_authorized': False, 'claim_consumed': False,
    'production_activated': False, 'provider_network_enabled': False,
    'credential_access_granted': False, 'systemd_changed': False,
    'mcp_tool_call_executed': False, 'r118_preclaim_changed': False,
}

class Hold(RuntimeError):
    pass


def deny(code):
    raise Hold('CF10_R122_HOLD_' + code)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def canonical(doc):
    return json.dumps(doc, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode('utf8') + b'\n'


def approved_source(path):
    if not isinstance(path, str) or not SCOPE.fullmatch(path):
        return False
    if any(part in ('', '.', '..') for part in path.split('/')):
        return False
    if path.startswith('scripts/') and path.endswith('.py'):
        return True
    if path.startswith('coordination/') and path.endswith('.py'):
        return True
    if path.startswith('coordination/registry/') and path.endswith(('.json','.yml','.yaml')):
        return True
    return False


def parse_tree(data):
    if not isinstance(data, bytes) or not data or len(data) > MAX_TREE_BYTES or not data.endswith(b'\0'):
        deny('GIT_TREE_BYTES')
    records = []
    for line in data[:-1].split(b'\0'):
        try:
            header, path = line.split(b'\t', 1)
            mode, kind, oid = header.decode('ascii').split(' ')
        except (UnicodeError, ValueError):
            deny('GIT_TREE_RECORD')
        legal = {'100644':'blob', '100755':'blob', '120000':'blob', '040000':'tree', '160000':'commit'}
        if legal.get(mode) != kind or not SHA1.fullmatch(oid):
            deny('GIT_TREE_RECORD')
        # Non-selected Unicode filenames (e.g. Ukrainian .mhtml) are normal Git entries.
        if not path.isascii():
            continue
        rel = path.decode('ascii')
        if not approved_source(rel):
            continue
        if mode not in ('100644', '100755') or kind != 'blob':
            deny('SOURCE_NOT_REGULAR_BLOB')
        records.append((rel, oid))
        if len(records)>MAX_FILES: deny('FILE_BUDGET')
    paths=[r[0] for r in records]
    if len(paths) != len(set(paths)) or MCP not in paths or SUITE not in paths:
        deny('SOURCE_SET_INCOMPLETE')
    return sorted(records)


def git_command(root, *args, limit=MAX_TREE_BYTES):
    try:
        p=subprocess.run(['/usr/bin/git','-C',str(root),*args],
                         cwd=str(root), stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         env={'PATH':'/usr/bin:/bin','LANG':'C'},
                         timeout=20, check=False)
    except (OSError,subprocess.SubprocessError):
        deny('GIT_IO')
    if p.returncode or len(p.stdout)>limit:
        deny('GIT_COMMAND')
    return p.stdout


def preflight_git(root=PROJECT):
    if root.is_symlink() or not root.is_dir() or root.resolve()!=root:
        deny('PROJECT_ROOT')
    if git_command(root,'rev-parse','--show-toplevel',limit=256).strip()!=str(root).encode():
        deny('REPO_TOPLEVEL')
    if git_command(root,'rev-parse','HEAD',limit=100).strip()!=PINNED_HEAD.encode():
        deny('FROZEN_HEAD')
    if git_command(root,'symbolic-ref','--short','HEAD',limit=160).strip()!=PINNED_BRANCH.encode():
        deny('BRANCH')
    # Only index must be clean. Unrelated dirty worktree, including SUITE, is retained.
    if subprocess.run(['/usr/bin/git','-C',str(root),'diff','--cached','--quiet'],
                     cwd=str(root), stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                     timeout=15, check=False).returncode != 0:
        deny('STAGED_INDEX')
    return True


def tree_from_head(root=PROJECT):
    return parse_tree(git_command(root,'ls-tree','-r','-z',PINNED_HEAD,'--','scripts','coordination'))


def compile_manifest(records, fetch):
    files=[];total=0
    for name,oid in records:
        if not approved_source(name) or not SHA1.fullmatch(oid):deny('UNTRUSTED_RECORD')
        raw=fetch(oid)
        if type(raw) is not bytes or len(raw)>MAX_BLOB or git_blob(raw)!=oid:
            deny('SOURCE_BLOB_MISMATCH')
        total+=len(raw)
        if total>MAX_TOTAL:deny('SOURCE_BUDGET')
        files.append({'path':name,'git_sha1':oid,'sha256':digest(raw),'bytes':len(raw)})
    if [f['path'] for f in files]!=sorted({f['path'] for f in files}):
        deny('SOURCE_ORDER_DUPLICATE')
    manifest={'schema_version':SCHEMA,'git_head':PINNED_HEAD,'source_type':'EXACT_GIT_OBJECTS_ONLY',
              'file_count':len(files),'total_bytes':total,'mcp_relative_path':'source/'+MCP,
              'suite_relative_path':'source/'+SUITE,'files':files,'authority':dict(AUTHORITY),
              'state':'PUBLISHED_SOURCE_ONLY_NOT_ACTIVATED'}
    return manifest


def check_owned_path(path, *, owner=0, group=RUNNER_GID, directory=True, mode=0o750):
    st=path.lstat()
    if st.st_uid!=owner or st.st_gid!=group or stat.S_IMODE(st.st_mode)!=mode or (stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode)) is False:
        deny('PATH_OWNER_MODE')
    return st


def mkdir_exact(path, *, owner=0, group=RUNNER_GID, mode=0o750):
    if path.is_symlink():deny('STATE_SYMLINK')
    if path.exists():
        check_owned_path(path,owner=owner,group=group,mode=mode)
    else:
        try:path.mkdir(mode=mode)
        except FileExistsError:deny('STATE_RACE')
        os.chown(path,owner,group)
        path.chmod(mode)
        check_owned_path(path,owner=owner,group=group,mode=mode)


def ensure_store(store=STORE, *,owner=0, group=RUNNER_GID):
    if not store.is_absolute() or store == Path('/') or store.is_symlink():deny('STATE_STORE_ROOT')
    if store == STORE:
        # Never create or modify /var/lib; this must already be a trusted OS directory.
        check_owned_path(Path('/var/lib'),owner=0,group=0,mode=0o755)
        mkdir_exact(store.parent,owner=owner,group=group)
    elif not store.parent.is_dir():
        deny('TEST_PARENT_MISSING')
    mkdir_exact(store,owner=owner,group=group)
    return store


def write_exclusive(path, raw, mode, *, owner=0, group=RUNNER_GID):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    with os.fdopen(fd,'wb') as out:
        os.fchown(out.fileno(),owner,group)
        out.write(raw);out.flush();os.fsync(out.fileno())
    os.chmod(path,mode)


def stage_files(folder,records,fetch,manifest,*,owner=0,group=RUNNER_GID):
    folder.mkdir(mode=0o700)
    os.chown(folder,owner,group)
    src=folder/'source';src.mkdir(mode=0o700)
    os.chown(src,owner,group)
    expected={r['path']:r for r in manifest['files']}
    for rel,oid in records:
        data=fetch(oid)
        rec=expected[rel]
        if git_blob(data)!=oid or digest(data)!=rec['sha256'] or len(data)!=rec['bytes']:
            deny('RACE_BLOB_READ')
        path=src/rel
        path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        if path.exists() or path.is_symlink():deny('STAGE_COLLISION')
        write_exclusive(path,data,0o640,owner=owner,group=group)
    write_exclusive(folder/'MANIFEST.json',canonical(manifest),0o640,owner=owner,group=group)
    for parent, dirs, _ in os.walk(src):
        for d in dirs:
            dp=Path(parent)/d
            os.chown(dp,owner,group)
            dp.chmod(0o750)
    src.chmod(0o750)
    folder.chmod(0o750)
    return folder


def manifest_id(manifest):
    return PREFIX+digest(canonical(manifest))


def verify_capsule(capsule, *,store=STORE,owner=0,group=RUNNER_GID):
    # Prevent user-controlled external paths and symlink swaps through the store.
    if not capsule.is_absolute() or capsule.parent!=store or not capsule.name.startswith(PREFIX):
        deny('VERIFY_SCOPE')
    if store==STORE:
        check_owned_path(STORE.parent,owner=owner,group=group)
    check_owned_path(store,owner=owner,group=group)
    check_owned_path(capsule,owner=owner,group=group)
    manifest_path=capsule/'MANIFEST.json'
    check_owned_path(manifest_path,owner=owner,group=group,directory=False,mode=0o640)
    raw=manifest_path.read_bytes()
    if len(raw)>1_000_000:deny('MANIFEST_BUDGET')
    try:doc=json.loads(raw)
    except (UnicodeError,ValueError):deny('MANIFEST_JSON')
    if type(doc) is not dict or canonical(doc)!=raw or doc.get('schema_version')!=SCHEMA:
        deny('MANIFEST_CANONICAL')
    if manifest_id(doc)!=capsule.name or doc.get('git_head')!=PINNED_HEAD or doc.get('authority')!=AUTHORITY or doc.get('source_type')!='EXACT_GIT_OBJECTS_ONLY' or doc.get('state')!='PUBLISHED_SOURCE_ONLY_NOT_ACTIVATED':
        deny('MANIFEST_IDENTITY')
    if doc.get('mcp_relative_path')!='source/'+MCP or doc.get('suite_relative_path')!='source/'+SUITE:
        deny('MANIFEST_ENTRYPOINT')
    files=doc.get('files')
    if type(files) is not list or not files or len(files)>MAX_FILES or doc.get('file_count')!=len(files):
        deny('MANIFEST_FILES')
    src=capsule/'source';check_owned_path(src,owner=owner,group=group)
    actual=set();total=0
    for folder,dirs,names in os.walk(capsule,followlinks=False):
        for item in dirs:
            target=Path(folder)/item
            check_owned_path(target,owner=owner,group=group)
            actual.add(str(target.relative_to(capsule))+'/')
        for item in names:
            target=Path(folder)/item
            check_owned_path(target,owner=owner,group=group,directory=False,mode=0o640)
            actual.add(str(target.relative_to(capsule)))
    expected={'MANIFEST.json','source/'}
    previous=''
    for f in files:
        if type(f) is not dict or set(f)!={'path','git_sha1','sha256','bytes'}:
            deny('MANIFEST_RECORD')
        rel=f['path']
        if not approved_source(rel) or rel<=previous or not SHA1.fullmatch(f['git_sha1']) or not SHA256.fullmatch(f['sha256']) or type(f['bytes']) is not int or not 0<=f['bytes']<=MAX_BLOB:
            deny('MANIFEST_RECORD')
        previous=rel
        target=src/rel
        data=target.read_bytes()
        if digest(data)!=f['sha256'] or git_blob(data)!=f['git_sha1'] or len(data)!=f['bytes']:
            deny('CAPSULE_DIGEST')
        total+=len(data)
        if total>MAX_TOTAL:deny('CAPSULE_SIZE')
        expected.add('source/'+rel)
        for p in Path(rel).parents:
            if str(p)!='.':expected.add('source/'+str(p)+'/')
    if actual!=expected or doc.get('total_bytes')!=total:
        deny('CAPSULE_FILESET')
    return {'status':'PASS_NON_AUTHORIZING_DURABLE_SOURCE','git_head':PINNED_HEAD,
            'capsule_id':capsule.name,'source_files':len(files),'source_bytes':total,
            'runner_writable':False,'worker_authorized':False,'g1_g5_closed':False}


def publish(*,root=PROJECT,store=STORE,owner=0,group=RUNNER_GID,records=None,fetch=None):
    """Root-owned, locked atomic source publication; never activates runtime."""
    ensure_store(store,owner=owner,group=group)
    # Only root may open this lock; runner may read published source, not publish.
    lock=store/'.r122-publish.lock'
    fd=os.open(lock,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        st=os.fstat(fd)
        if st.st_uid!=owner or stat.S_IMODE(st.st_mode)!=0o600 or not stat.S_ISREG(st.st_mode):
            deny('STORE_LOCK_IDENTITY')
        fcntl.flock(fd,fcntl.LOCK_EX)
        if records is None:records=tree_from_head(root)
        if fetch is None:fetch=lambda oid:git_command(root,'cat-file','blob',oid,limit=MAX_BLOB)
        manifest=compile_manifest(records,fetch)
        target=store/manifest_id(manifest)
        if target.exists() or target.is_symlink():
            result=verify_capsule(target,store=store,owner=owner,group=group)
            return {**result,'action':'REUSED_VERIFIED'}
        staging=store/('.r122-stage-'+secrets.token_hex(12))
        try:
            stage_files(staging,records,fetch,manifest,owner=owner,group=group)
            if digest((staging/'MANIFEST.json').read_bytes())!=digest(canonical(manifest)):
                deny('STAGE_MANIFEST')
            # Exclusive root-owned store lock prevents a competing publisher.
            os.rename(staging,target)
            result=verify_capsule(target,store=store,owner=owner,group=group)
            dfd=os.open(store,os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
            try:os.fsync(dfd)
            finally:os.close(dfd)
            return {**result,'action':'PUBLISHED_NEW'}
        finally:
            if staging.exists():shutil.rmtree(staging)
    finally:
        os.close(fd)


def runner_import_check(capsule, *,python=PROJECT/'.venv_blueprint/bin/python',runner=RUNNER):
    try:who=pwd.getpwnam(runner)
    except KeyError:deny('RUNNER_NOT_FOUND')
    if who.pw_uid!=RUNNER_UID or who.pw_gid!=RUNNER_GID:
        deny('RUNNER_IDENTITY')
    if not python.is_file():deny('PYTHON_MISSING')
    cmd=[str(python),'-I','-B','-c',
         'import runpy,sys;runpy.run_path(sys.argv[1],run_name="_forprint_r122_import_only_")',
         str(capsule/'source'/MCP)]
    def drop():
        os.setgroups([]);os.setgid(who.pw_gid);os.setuid(who.pw_uid)
    try:
        p=subprocess.run(cmd,cwd=str(capsule/'source'),stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                        env={'HOME':'/nonexistent','PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},
                        preexec_fn=drop,timeout=35,check=False)
    except (OSError,subprocess.SubprocessError):deny('RUNNER_IMPORT_EXEC')
    if p.returncode!=0 or p.stdout:deny('RUNNER_IMPORT_FAILED')
    return 'PASS_IMMUTABLE_DURABLE_SOURCE_IMPORT_ONLY'


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('inspect','publish','verify'),required=True)
    p.add_argument('--capsule-id',default=os.environ.get('CF10_CAPSULE_ID'))
    a=p.parse_args(argv)
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    if a.mode=='inspect':
        preflight_git()
        records=tree_from_head()
        print('CF10_R122_SOURCE_HEAD='+PINNED_HEAD)
        print('CF10_R122_TRACKED_FILES='+str(len(records)))
        print('CF10_R122=PASS_SOURCE_INSPECT_NON_AUTHORIZING')
        return 0
    if a.mode=='publish':
        try:account=pwd.getpwnam(RUNNER)
        except KeyError:deny('RUNNER_NOT_FOUND')
        if account.pw_uid!=RUNNER_UID or account.pw_gid!=RUNNER_GID:deny('RUNNER_IDENTITY')
        preflight_git()
        result=publish()
        verify=verify_capsule(STORE/result['capsule_id'])
        imported=runner_import_check(STORE/result['capsule_id'])
        print('CF10_R122_CAPSULE_ACTION='+result['action'])
        print('CF10_R122_CAPSULE_ID='+result['capsule_id'])
        print('CF10_R122_CAPSULE_FILES='+str(result['source_files']))
        print('CF10_R122_CAPSULE_READBACK='+verify['status'])
        print('CF10_R122_RUNNER_IMPORT='+imported)
        print('CF10_R122=PASS_DURABLE_SOURCE_PUBLISHED_NON_AUTHORIZING')
    else:
        if not a.capsule_id or not re.fullmatch(re.escape(PREFIX)+r'[0-9a-f]{64}',a.capsule_id):
            deny('CAPSULE_ID')
        result=verify_capsule(STORE/a.capsule_id)
        print('CF10_R122_CAPSULE_READBACK='+result['status'])
        print('CF10_R122=PASS_DURABLE_SOURCE_VERIFIED_NON_AUTHORIZING')
    print('CF10_R122_G1_G5=OPEN_NO_LIVE_ADMISSION')
    print('CF10_R122_NO_SYSTEMD_NO_WORKER_NO_CLAIM_NO_CREDENTIALS=true')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (Hold, OSError, ValueError, KeyError) as exc:
        print('CF10_R122_HOLD='+str(exc) if isinstance(exc,Hold) else 'CF10_R122_HOLD_'+type(exc).__name__)
        print('CF10_R122_G1_G5=OPEN_NO_LIVE_ADMISSION')
        sys.exit(3)
