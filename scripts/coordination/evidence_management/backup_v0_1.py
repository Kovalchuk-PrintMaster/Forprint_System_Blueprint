"""ForPrint Evidence Vault A02: separate-mount backup and isolated restore proof.

Technical separation is checked (mount/device), physical independence is NOT
proven by software. Never authorizes CF10/Worker or claims disaster recovery.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from datetime import datetime, timezone

from scripts.coordination.evidence_management import vault_v0_1 as v

SCHEMA='forprint_evidence_a02_snapshot_v0_1'
NAME=re.compile(r'[a-z0-9][a-z0-9-]{3,90}\Z')
SHA=re.compile(r'[0-9a-f]{64}\Z')
CONFIRM_BACKUP='CREATE_FORPRINT_EVIDENCE_A02_SNAPSHOT'
CONFIRM_RESTORE='RESTORE_TEST_FORPRINT_EVIDENCE_A02'
RESTORE_PARENT=Path('/srv/software_development/forprint-project/forprint_system_blueprint/tmp')

class BackupBlocked(RuntimeError):pass

def guard(c, fn, *args, **kwargs):
    try:return fn(*args,**kwargs)
    except (v.VaultBlocked, OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        raise BackupBlocked(c+':'+str(e)[:160]) from e

def reg(path:Path, maximum:int=30_000_000)->bytes:
    return guard('UNSAFE_OR_MISSING_SOURCE',v.read_regular,path,max_size=maximum,require_private=True)

def require_absolute(path:Path)->None:
    if not path.is_absolute() or '..' in path.parts:raise BackupBlocked('ABSOLUTE_PATH_REQUIRED')
    guard('SYMLINK_PATH',v.check_no_symlinks,path)

def under(child:Path,parent:Path)->bool:
    return child==parent or parent in child.parents

def validate_backup_mount_only(target:Path,source:Path,*,strict:bool=True)->dict:
    """Restore verification can operate after total loss of the source Vault."""
    require_absolute(target)
    require_absolute(source)
    if target==Path('/') or under(source,target) or any(under(target,x) for x in (
       source,Path('/srv/software_development/forprint-project'),
       Path('/srv/software_development/forprint-worker-runtime'),
       Path('/srv/software_development/forprint-releases'),
       Path('/tmp'),Path('/var/tmp'))):
        raise BackupBlocked('BACKUP_TARGET_IN_PRIMARY_OR_TRANSIENT_TREE')
    if not target.is_dir():raise BackupBlocked('BACKUP_TARGET_NOT_EXISTING_DIRECTORY')
    st=target.stat()
    if st.st_mode & 0o077 or st.st_uid!=(0 if strict else os.geteuid()):
        raise BackupBlocked('BACKUP_ROOT_MUST_BE_PRIVATE_AND_OPERATOR_OWNED')
    if strict and (os.geteuid()!=0 or os.uname().nodename.split('.')[0]!='s01'):
        raise BackupBlocked('ROOT_OPERATOR_S01_REQUIRED')
    cur=target
    while cur!=Path('/'):
        if os.path.ismount(cur):break
        cur=cur.parent
    if cur==Path('/'):
        raise BackupBlocked('BACKUP_MOUNTPOINT_NOT_VERIFIED')
    return {'mountpoint':str(cur),'backup_dev':st.st_dev,
            'physical_independence_verified':False,'offhost_copy_verified':False}

def validate_target(target:Path,source:Path,*,strict:bool=True)->dict:
    observed=validate_backup_mount_only(target,source,strict=strict)
    guard('SOURCE_VAULT_INVALID',v.validate_root,source,strict=strict)
    source_dev=source.stat().st_dev
    if source_dev==observed['backup_dev']:
        raise BackupBlocked('BACKUP_TARGET_SAME_FILESYSTEM_AS_VAULT')
    return {**observed,'source_dev':source_dev,'separate_filesystem_verified':True}

def collect(root:Path,*,strict:bool=True)->dict[str,bytes]:
    guard('SOURCE_VAULT_INVALID',v.validate_root,root,strict=strict)
    manifests=root/'manifests'/'by-id'
    ids=sorted(p.stem for p in manifests.iterdir())
    if not ids:raise BackupBlocked('NO_REGISTERED_EVIDENCE')
    paths={'vault.json':root/'vault.json'}
    objects=set()
    for eid in ids:
        if not v.ID_RE.fullmatch(eid):raise BackupBlocked('INVALID_MANIFEST_ID')
        guard('EVIDENCE_VERIFY_FAILED',v.verify_registered,root,eid,strict=strict)
        m=root/'manifests'/'by-id'/(eid+'.json')
        e=root/'journal'/'events'/(eid+'.json')
        data=json.loads(reg(m,100_000)); sha=data['artifact_sha256']
        objects.add('objects/sha256/'+sha[:2]+'/'+sha)
        paths['manifests/by-id/'+eid+'.json']=m
        paths['journal/events/'+eid+'.json']=e
    for rel in objects:paths[rel]=root/rel
    # No silent omission of unexpected files, partial registrations, or stray objects.
    present=set()
    for dirpath,dirnames,filenames in os.walk(root,followlinks=False):
        for dn in dirnames:
            dp=Path(dirpath)/dn
            if dp.is_symlink():raise BackupBlocked('VAULT_SYMLINK_DIRECTORY')
        for fn in filenames:
            path=Path(dirpath)/fn
            if path.is_symlink():raise BackupBlocked('VAULT_SYMLINK_FILE')
            rel=path.relative_to(root).as_posix()
            if rel!='.register.lock':present.add(rel)
    if present!=set(paths):
        raise BackupBlocked('VAULT_EXTRA_OR_MISSING_FILES:'+','.join(sorted(present^set(paths))[:5]))
    return {rel:reg(p,100_000 if 'manifests/' in rel or 'journal/' in rel else 30_000_000)
            for rel,p in sorted(paths.items())}

def snapshot_id()->str:
    return 'a02-'+datetime.now(timezone.utc).strftime('%Y%m%dt%H%M%S%f')+'z'

def write_new(path:Path,raw:bytes)->None:
    guard('BACKUP_CREATE_FAILED',v.atomic_new,path,raw)

def private_parents(top:Path, child:Path)->None:
    # mkdir(parents=True) does not apply mode=0700 to intermediate levels.
    if not under(child,top):raise BackupBlocked('DIRECTORY_OUTSIDE_TARGET')
    path=top
    for part in child.relative_to(top).parts:
        path=path/part
        if path.exists():
            if path.is_symlink() or not path.is_dir() or stat.S_IMODE(path.stat().st_mode)!=0o700:
                raise BackupBlocked('BACKUP_DIRECTORY_NOT_PRIVATE')
        else:path.mkdir(mode=0o700)

def snapshot(root:Path,target:Path,*,confirm:str,strict:bool=True,identifier:str|None=None)->dict:
    if confirm!=CONFIRM_BACKUP:raise BackupBlocked('EXPLICIT_BACKUP_CONFIRMATION_REQUIRED')
    sep=validate_target(target,root,strict=strict)
    sid=identifier or snapshot_id()
    if not NAME.fullmatch(sid):raise BackupBlocked('SNAPSHOT_ID_INVALID')
    with v.vault_lock(root):
        entries=collect(root,strict=strict)
        # Confirm no unexpected prior data in the target pilot surface.
        for path in (target/'snapshots',target/'staging'):
            if path.is_symlink():raise BackupBlocked('BACKUP_SYMLINK_DIR')
            if not path.exists():path.mkdir(mode=0o700)
            if not path.is_dir() or stat.S_IMODE(path.stat().st_mode)!=0o700:
                raise BackupBlocked('BACKUP_DIRECTORY_MODE_DRIFT')
        stage=target/'staging'/sid
        done=target/'snapshots'/sid
        if stage.exists() or done.exists():raise BackupBlocked('SNAPSHOT_ALREADY_EXISTS')
        stage.mkdir(mode=0o700)
        for rel,data in entries.items():
            p=stage/'payload'/rel
            private_parents(stage,p.parent)
            write_new(p,data)
        manifest={'schema_version':SCHEMA,'snapshot_id':sid,
                  'source_kind':'FORPRINT_EVIDENCE_VAULT_A01',
                  'evidence_count':sum(x.startswith('manifests/by-id/') for x in entries),
                  'entries':{name:{'sha256':v.digest(data),'size_bytes':len(data)}
                             for name,data in sorted(entries.items())},
                  'authority_granted':False,'independent_failure_domain_proven':False,
                  'source_backup_verified':False,'signing_performed':False}
        data=v.encode(manifest)
        write_new(stage/'snapshot_manifest.json',data)
        # Re-read from the separate filesystem, verify before exposing as completed.
        verify_snapshot(stage, v.digest(data), expected_id=sid, strict=strict, staging=True)
        os.rename(stage,done)
        guard('BACKUP_FSYNC_FAILED',v.fsync_dir,target/'snapshots')
        return {'state':'SEPARATE_FILESYSTEM_SNAPSHOT_VERIFIED_NON_AUTHORIZING',
                'snapshot_id':sid,'manifest_sha256':v.digest(data),'snapshot_root':str(done),
                'evidence_count':manifest['evidence_count'],**sep,
                'authority_granted':False,'backup_disaster_recovery_proven':False}

def verify_snapshot(snapshot_root:Path,expected_sha:str,*,expected_id:str|None=None,strict:bool=True,staging:bool=False)->dict:
    require_absolute(snapshot_root)
    if not SHA.fullmatch(expected_sha):raise BackupBlocked('EXPECTED_MANIFEST_SHA256_REQUIRED')
    manifest_raw=reg(snapshot_root/'snapshot_manifest.json',100_000)
    if v.digest(manifest_raw)!=expected_sha:raise BackupBlocked('SNAPSHOT_MANIFEST_ANCHOR_MISMATCH')
    m=json.loads(manifest_raw)
    if m.get('schema_version')!=SCHEMA or m.get('authority_granted') is not False or m.get('independent_failure_domain_proven') is not False:
        raise BackupBlocked('SNAPSHOT_SCHEMA_OR_AUTHORITY_DRIFT')
    if not NAME.fullmatch(m.get('snapshot_id','')) or expected_id and m['snapshot_id']!=expected_id:
        raise BackupBlocked('SNAPSHOT_ID_DRIFT')
    entry=m.get('entries')
    if not isinstance(entry,dict) or 'vault.json' not in entry:raise BackupBlocked('MANIFEST_ENTRIES_MISSING')
    actual=set()
    for dp,dns,fns in os.walk(snapshot_root,followlinks=False):
        if any((Path(dp)/x).is_symlink() for x in dns):raise BackupBlocked('BACKUP_SYMLINK_DIRECTORY')
        for f in fns:
            p=Path(dp)/f
            if p.is_symlink():raise BackupBlocked('BACKUP_SYMLINK_FILE')
            actual.add(p.relative_to(snapshot_root).as_posix())
    expected={'snapshot_manifest.json'}|{'payload/'+x for x in entry}
    if actual!=expected:raise BackupBlocked('SNAPSHOT_FILE_SET_DRIFT')
    payload={}
    for rel,item in entry.items():
        if not isinstance(rel,str) or rel.startswith('/') or '..' in Path(rel).parts or '\\' in rel:
            raise BackupBlocked('MANIFEST_PATH_TRAVERSAL')
        if not isinstance(item,dict) or not SHA.fullmatch(item.get('sha256','')) or type(item.get('size_bytes')) is not int:
            raise BackupBlocked('SNAPSHOT_ITEM_SCHEMA_DRIFT')
        blob=reg(snapshot_root/'payload'/rel)
        if v.digest(blob)!=item['sha256'] or len(blob)!=item['size_bytes']:
            raise BackupBlocked('SNAPSHOT_PAYLOAD_DRIFT:'+rel)
        payload[rel]=blob
    ids=sorted(rel.split('/')[-1][:-5] for rel in payload if rel.startswith('manifests/by-id/') and rel.endswith('.json'))
    if not ids or m.get('evidence_count')!=len(ids):raise BackupBlocked('SNAPSHOT_COUNT_DRIFT')
    objects=set()
    for eid in ids:
        if not v.ID_RE.fullmatch(eid):raise BackupBlocked('SNAPSHOT_BAD_EVIDENCE_ID')
        mrel='manifests/by-id/'+eid+'.json'; erel='journal/events/'+eid+'.json'
        if erel not in payload:raise BackupBlocked('SNAPSHOT_JOURNAL_MISSING')
        item=json.loads(payload[mrel]); event=json.loads(payload[erel])
        sha=item.get('artifact_sha256')
        if not isinstance(sha,str) or not SHA.fullmatch(sha):raise BackupBlocked('SNAPSHOT_ARTIFACT_HASH_MISSING')
        orel='objects/sha256/'+sha[:2]+'/'+sha
        objects.add(orel)
        if orel not in payload or v.digest(payload[orel])!=sha:raise BackupBlocked('SNAPSHOT_OBJECT_NOT_BOUND')
        if item.get('authority_granted') is not False or item.get('evidence_id')!=eid or item.get('size_bytes')!=len(payload[orel]):
            raise BackupBlocked('SNAPSHOT_EVIDENCE_MANIFEST_DRIFT')
        if event.get('event')!='REGISTER_NON_AUTHORIZING' or event.get('manifest_sha256')!=v.digest(payload[mrel]) or event.get('artifact_sha256')!=sha:
            raise BackupBlocked('SNAPSHOT_EVENT_BINDING_DRIFT')
        guard('SNAPSHOT_G2A_PROOF_INVALID',v.verify_g2a_report,payload[orel])
    expected_names={'vault.json'}|objects|{'journal/events/'+eid+'.json' for eid in ids}|{'manifests/by-id/'+eid+'.json' for eid in ids}
    if set(payload)!=expected_names:raise BackupBlocked('SNAPSHOT_UNEXPECTED_OR_MISSING_PROVENANCE_PATHS')
    marker=json.loads(payload['vault.json'])
    if marker.get('schema_version')!=v.MAGIC or marker.get('authority_granted') is not False:
        raise BackupBlocked('SNAPSHOT_VAULT_MARKER_DRIFT')
    return {'state':'SNAPSHOT_INTEGRITY_VERIFIED_NON_AUTHORIZING',
            'snapshot_id':m['snapshot_id'],'manifest_sha256':expected_sha,
            'evidence_count':len(ids),'authority_granted':False}

def restore_test(source:Path,target:Path,sid:str,expected_sha:str,restore_root:Path,*,confirm:str,strict:bool=True)->dict:
    if confirm!=CONFIRM_RESTORE:raise BackupBlocked('EXPLICIT_RESTORE_CONFIRMATION_REQUIRED')
    validate_backup_mount_only(target,source,strict=strict)
    if not NAME.fullmatch(sid):raise BackupBlocked('SNAPSHOT_ID_INVALID')
    snap=target/'snapshots'/sid
    check=verify_snapshot(snap,expected_sha,expected_id=sid,strict=strict)
    require_absolute(restore_root)
    if restore_root.parent!=RESTORE_PARENT or not restore_root.name.startswith('evidence_a02_restore_'):
        raise BackupBlocked('RESTORE_TARGET_MUST_BE_PROJECT_TEMP_CHILD')
    if any(under(restore_root,x) for x in (source,target)) or under(source,restore_root) or under(target,restore_root):
        raise BackupBlocked('RESTORE_ROOT_OVERLAPS_SOURCE_OR_BACKUP')
    if restore_root.exists() or not restore_root.parent.is_dir():raise BackupBlocked('RESTORE_MUST_CREATE_NEW_DIRECTORY')
    restore_root.mkdir(mode=0o700)
    payload=snap/'payload'
    m=json.loads(reg(snap/'snapshot_manifest.json',100_000))
    for rel in sorted(m['entries']):
        dst=restore_root/rel
        private_parents(restore_root,dst.parent)
        write_new(dst,reg(payload/rel))
    for rel in v.DIRS:
        private_parents(restore_root,restore_root/rel)
    write_new(restore_root/'.register.lock',b'')
    guard('RESTORE_SOURCE_LAYOUT_INVALID',v.validate_root,restore_root,strict=False)
    out=collect(restore_root,strict=False)
    for rel,data in out.items():
        if v.digest(data)!=m['entries'][rel]['sha256']:
            raise BackupBlocked('RESTORED_VAULT_DRIFT:'+rel)
    return {'state':'ISOLATED_RESTORE_TEST_PASS_NON_AUTHORIZING','snapshot_id':sid,
            'restore_root':str(restore_root),'manifest_sha256':expected_sha,
            'evidence_count':len([x for x in out if x.startswith('manifests/by-id/')]),
            'backup_disaster_recovery_proven':False,'authority_granted':False}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('inspect-source','check-target','snapshot','verify-snapshot','restore-test'))
    p.add_argument('--backup-root',type=Path)
    p.add_argument('--snapshot-id')
    p.add_argument('--manifest-sha256')
    p.add_argument('--restore-root',type=Path)
    p.add_argument('--confirm',default='')
    a=p.parse_args(argv)
    root=v.BASE
    try:
        if a.action=='inspect-source':
            data=collect(root)
            result={'state':'SOURCE_VAULT_VALID_NON_AUTHORIZING',
                    'evidence_count':sum(x.startswith('manifests/by-id/') for x in data),
                    'authority_granted':False,'backup_verified':False}
        else:
            if a.backup_root is None:raise BackupBlocked('BACKUP_ROOT_EXPLICIT_REQUIRED')
            if a.action=='check-target':result=validate_target(a.backup_root,root)
            elif a.action=='snapshot':result=snapshot(root,a.backup_root,confirm=a.confirm)
            else:
                if not a.snapshot_id or not a.manifest_sha256:raise BackupBlocked('SNAPSHOT_ID_AND_EXTERNAL_MANIFEST_SHA_REQUIRED')
                snap=a.backup_root/'snapshots'/a.snapshot_id
                if a.action=='verify-snapshot':
                    validate_backup_mount_only(a.backup_root,root)
                    result=verify_snapshot(snap,a.manifest_sha256,expected_id=a.snapshot_id)
                else:
                    if a.restore_root is None:raise BackupBlocked('RESTORE_ROOT_REQUIRED')
                    result=restore_test(root,a.backup_root,a.snapshot_id,a.manifest_sha256,
                                        a.restore_root,confirm=a.confirm)
        print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
        return 0
    except (BackupBlocked,OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print('FORPRINT_EVIDENCE_A02=BLOCKED:'+type(e).__name__+':'+str(e)[:260],file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
