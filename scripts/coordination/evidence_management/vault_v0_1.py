"""ForPrint local Evidence Vault A01 — non-authorizing G2a proof pilot.

No authority transfer, Worker operations, Git writes, deletion, migration, or external services.
A root operator explicitly initializes and registers one externally supplied G2a report.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from zipfile import ZipFile, BadZipFile
from io import BytesIO

BASE = Path('/srv/software_development/forprint-evidence-store')
MAGIC = 'forprint_evidence_vault_v0_1'
EVIDENCE_SCHEMA = 'forprint_evidence_manifest_v0_1'
REPORT_SCHEMA = 'cf10_g2a_stable_release_roots_review_v0_1'
SOURCE_HEAD = 'f37abe98045afa8a28f158a017fc3114e1d26499'
PIN = {
    'gate': ('3d90143a240439d33833463d38ab0fb3497eac8f', '06a7b4eeb757254c0f098be393780f950a266407'),
    'writer': ('d5d1495c0a1ab25367c146b0f5379b015e03dd85', 'e098c6dc8c15192d33b3c0560830b2bb37a0f338'),
}
ID_RE = re.compile(r'[a-z0-9](?:[a-z0-9-]{0,94}[a-z0-9])?\Z')
MAX_SOURCE = 30_000_000
MAX_MEMBER = 2_000_000
MAX_TOTAL_UNCOMPRESSED = 5_000_000
DIRS = ('intake', 'objects', 'objects/sha256', 'manifests', 'manifests/by-id', 'journal', 'journal/events', 'catalog', 'quarantine')

class VaultBlocked(RuntimeError):
    pass


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def encode(x: object) -> bytes:
    return (json.dumps(x, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def check_no_symlinks(path: Path) -> None:
    if not path.is_absolute() or '..' in path.parts:
        raise VaultBlocked('ABSOLUTE_CANONICAL_PATH_REQUIRED')
    for part in (path, *path.parents):
        if part.is_symlink():
            raise VaultBlocked('SYMLINK_PATH_REJECTED')


def require_root_s01() -> None:
    if os.geteuid() != 0 or os.uname().nodename.split('.')[0] != 's01':
        raise VaultBlocked('ROOT_OPERATOR_ON_S01_REQUIRED')


def check_parent_security(root: Path) -> None:
    if root != BASE:
        raise VaultBlocked('VAULT_PATH_NOT_APPROVED')
    check_no_symlinks(root)
    for part in (root.parent, *list(root.parent.parents)):
        st = part.stat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != 0 or (st.st_mode & 0o022):
            raise VaultBlocked('VAULT_PARENT_NOT_ROOT_CONTROLLED')


def must_dir(path: Path, *, strict_owner: bool) -> None:
    check_no_symlinks(path)
    st = path.lstat()
    if not stat.S_ISDIR(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o700:
        raise VaultBlocked('VAULT_DIRECTORY_MODE_DRIFT:' + path.name)
    if strict_owner and st.st_uid != 0:
        raise VaultBlocked('VAULT_DIRECTORY_OWNER_DRIFT:' + path.name)


def init(root: Path = BASE, *, confirmed: bool = False, strict: bool = True) -> str:
    if not confirmed:
        raise VaultBlocked('INIT_OPERATOR_CONFIRMATION_REQUIRED')
    if strict:
        require_root_s01()
        check_parent_security(root)
    else:
        check_no_symlinks(root)
    if root.exists():
        must_dir(root, strict_owner=strict)
        if (root / 'vault.json').exists():
            validate_root(root, strict=strict)
            return 'ALREADY_INITIALIZED_NON_AUTHORIZING'
        if any(root.iterdir()):
            raise VaultBlocked('UNRECOGNIZED_NONEMPTY_VAULT_ROOT')
    else:
        root.mkdir(mode=0o700)
    for rel in DIRS:
        p = root / rel
        if p.exists():
            must_dir(p, strict_owner=strict)
        else:
            p.mkdir(mode=0o700)
    atomic_new(root/'vault.json', encode({
        'schema_version': MAGIC, 'storage_class': 'LOCAL_ROOT_CONTROLLED',
        'authority_granted': False, 'automatic_deletion': False,
        'backup_verified': False, 'external_replica_verified': False,
        'bootstrap_status': 'PILOT_NO_PRODUCTION_AUTHORITY',
    }))
    atomic_new(root/'.register.lock', b'')
    validate_root(root, strict=strict)
    return 'INITIALIZED_NON_AUTHORIZING'


def validate_root(root: Path = BASE, *, strict: bool = True) -> None:
    if strict:
        check_parent_security(root)
    must_dir(root, strict_owner=strict)
    for rel in DIRS:
        must_dir(root / rel, strict_owner=strict)
    marker = read_regular(root/'vault.json', max_size=10000, require_private=True)
    obj = json.loads(marker)
    if obj.get('schema_version') != MAGIC or obj.get('authority_granted') is not False:
        raise VaultBlocked('VAULT_MARKER_DRIFT')
    read_regular(root/'.register.lock', max_size=10000, require_private=True)


def read_regular(path: Path, *, max_size: int = MAX_SOURCE, require_private: bool = False) -> bytes:
    check_no_symlinks(path)
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_size > max_size:
        raise VaultBlocked('SOURCE_NOT_SMALL_REGULAR_FILE')
    if st.st_mode & 0o022:
        raise VaultBlocked('SOURCE_WRITABLE_BY_OTHERS')
    if require_private and (stat.S_IMODE(st.st_mode) & 0o077):
        raise VaultBlocked('VAULT_FILE_NOT_PRIVATE')
    if require_private and st.st_nlink != 1:
        raise VaultBlocked('VAULT_HARDLINK_REJECTED')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        fs = os.fstat(fd)
        if (fs.st_dev,fs.st_ino,fs.st_size)!=(st.st_dev,st.st_ino,st.st_size):
            raise VaultBlocked('FILE_RACE_DETECTED')
        data = b''
        while len(data) <= max_size:
            part = os.read(fd, min(65536, max_size + 1 - len(data)))
            if not part: break
            data += part
        if len(data)>max_size:
            raise VaultBlocked('SOURCE_OVERSIZE')
        return data
    finally:
        os.close(fd)


def fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os,'O_DIRECTORY',0))
    try: os.fsync(fd)
    finally: os.close(fd)


def atomic_new(path: Path, raw: bytes) -> None:
    check_no_symlinks(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        # Do not silently erase ambiguous evidence; partial writes require review.
        raise
    fsync_dir(path.parent)


def verify_g2a_report(raw: bytes) -> dict:
    try:
        with ZipFile(BytesIO(raw)) as z:
            infos = z.infolist()
            names = [i.filename for i in infos]
            if len(names)!=3 or set(names)!={'SHA256SUMS','summary.txt','report.json'} or len(set(names))!=3:
                raise VaultBlocked('G2A_ZIP_MEMBER_SET_DRIFT')
            if any(i.file_size > MAX_MEMBER for i in infos) or sum(i.file_size for i in infos)>MAX_TOTAL_UNCOMPRESSED:
                raise VaultBlocked('G2A_ZIP_UNCOMPRESSED_LIMIT')
            if z.testzip() is not None:
                raise VaultBlocked('G2A_ZIP_CRC_FAIL')
            summary=z.read('summary.txt'); report=z.read('report.json'); sums=z.read('SHA256SUMS').decode('ascii')
    except (BadZipFile, ValueError, UnicodeError, OSError) as exc:
        raise VaultBlocked('G2A_ZIP_PARSE_FAILED') from exc
    expected=''.join(digest(data)+'  '+name+'\n' for name,data in sorted({'report.json':report,'summary.txt':summary}.items()))
    if sums!=expected:
        raise VaultBlocked('G2A_INTERNAL_SHA256SUMS_DRIFT')
    try: doc=json.loads(report)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise VaultBlocked('G2A_REPORT_JSON_INVALID') from exc
    if doc.get('schema_version') != REPORT_SCHEMA or doc.get('state')!='STABLE_RELEASES_READY_FOR_INDEPENDENT_REBIND_NON_AUTHORIZING':
        raise VaultBlocked('G2A_STATE_OR_SCHEMA_UNEXPECTED')
    checks=doc.get('checks')
    if not isinstance(checks,dict) or any(checks.get(n,{}).get('status')!='PASS' for n in ('canonical','gate','writer')):
        raise VaultBlocked('G2A_CHECKS_NOT_ALL_PASS')
    canonical=checks['canonical']
    if canonical.get('canonical_head')!=SOURCE_HEAD or canonical.get('remote_verified') is not True or canonical.get('pinned_git_objects_verified') is not True or canonical.get('pinned_git_objects_missing')!=[]:
        raise VaultBlocked('G2A_CANONICAL_PROVENANCE_DRIFT')
    for kind,(head,blob) in PIN.items():
        if checks[kind].get('head')!=head or checks[kind].get('source_blob_oid')!=blob:
            raise VaultBlocked('G2A_PINNED_RELEASE_DRIFT:'+kind)
    for key in ('authority_granted','root_signed_activation_renewed', 'make_launch_gate_unquarantined','worker_launched','historical_technical_coverage_evidence_migrated','historical_gate_coverage_binding_reauthorized'):
        if doc.get(key) is not False:
            raise VaultBlocked('G2A_AUTHORITY_FLAG_NOT_FALSE:'+key)
    if 'CF10_G2A_STATUS=STABLE_RELEASES_READY_FOR_INDEPENDENT_REBIND_NON_AUTHORIZING' not in summary.decode('utf-8','strict'):
        raise VaultBlocked('G2A_SUMMARY_MISMATCH')
    return {'source_head': SOURCE_HEAD,'evidence_kind':'CF10_G2A_STABLE_RELEASE_REVIEW',
            'gate_head':PIN['gate'][0], 'writer_head':PIN['writer'][0],
            'historical_coverage_rebound':False, 'authorizing':False}


def propose(source: Path) -> dict:
    raw=read_regular(source)
    metadata=verify_g2a_report(raw)
    return {'status':'SOURCE_TECHNICALLY_VERIFIED_NON_AUTHORIZING',
            'sha256':digest(raw),'size_bytes':len(raw),**metadata,
            'vault_mutated':False, 'history_migrated':False,'backup_verified':False}


def object_path(root: Path, sha: str) -> Path:
    if not re.fullmatch('[0-9a-f]{64}',sha): raise VaultBlocked('OBJECT_SHA_INVALID')
    return root/'objects'/'sha256'/sha[:2]/sha


def manifest_path(root: Path, evidence_id: str) -> Path:
    if not ID_RE.fullmatch(evidence_id): raise VaultBlocked('EVIDENCE_ID_INVALID')
    return root/'manifests'/'by-id'/(evidence_id+'.json')


def event_path(root: Path, evidence_id: str) -> Path:
    if not ID_RE.fullmatch(evidence_id): raise VaultBlocked('EVIDENCE_ID_INVALID')
    return root/'journal'/'events'/(evidence_id+'.json')


@contextmanager
def vault_lock(root: Path):
    with (root/'.register.lock').open('rb') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try: yield
        finally: fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def verify_registered(root: Path, evidence_id: str, *, strict: bool = True) -> dict:
    validate_root(root, strict=strict)
    mbytes=read_regular(manifest_path(root,evidence_id),max_size=100_000,require_private=True)
    m=json.loads(mbytes)
    if m.get('schema_version')!=EVIDENCE_SCHEMA or m.get('evidence_id')!=evidence_id or m.get('authority_granted') is not False:
        raise VaultBlocked('MANIFEST_SCHEMA_OR_ID_DRIFT')
    sha=m.get('artifact_sha256')
    source=object_path(root,sha)
    blob=read_regular(source,require_private=True)
    if digest(blob)!=sha or len(blob)!=m.get('size_bytes'):
        raise VaultBlocked('OBJECT_HASH_OR_SIZE_MISMATCH')
    detail=verify_g2a_report(blob)
    if m.get('source_head')!=detail['source_head'] or m.get('evidence_type')!=detail['evidence_kind']:
        raise VaultBlocked('MANIFEST_PROVENANCE_DRIFT')
    ev=json.loads(read_regular(event_path(root,evidence_id),max_size=100_000,require_private=True))
    if ev.get('manifest_sha256')!=digest(mbytes) or ev.get('artifact_sha256')!=sha or ev.get('event')!='REGISTER_NON_AUTHORIZING':
        raise VaultBlocked('JOURNAL_LINK_DRIFT')
    return {'state':'VERIFIED_REGISTERED_NON_AUTHORIZING','evidence_id':evidence_id,'sha256':sha,
            'source_head':m['source_head'],'authority_granted':False,'object_size_bytes':len(blob)}


def register(root: Path, source: Path, evidence_id: str, *, confirmed: bool=False, strict: bool=True) -> dict:
    if not confirmed: raise VaultBlocked('REGISTER_OPERATOR_CONFIRMATION_REQUIRED')
    if strict: require_root_s01()
    validate_root(root,strict=strict)
    target=manifest_path(root,evidence_id)
    ev=event_path(root,evidence_id)
    with vault_lock(root):
        raw=read_regular(source)
        detail=verify_g2a_report(raw)
        sha=digest(raw)
        obj=object_path(root,sha)
        if target.exists() or ev.exists():
            if not target.exists() or not ev.exists():
                raise VaultBlocked('INCOMPLETE_EXISTING_REGISTRATION_REVIEW_REQUIRED')
            existing=verify_registered(root,evidence_id,strict=strict)
            if existing['sha256']!=sha:
                raise VaultBlocked('EVIDENCE_ID_ALREADY_BOUND_TO_OTHER_BYTES')
            return {**existing,'state':'ALREADY_REGISTERED_NON_AUTHORIZING'}
        if obj.parent.exists():
            must_dir(obj.parent,strict_owner=strict)
        else:
            obj.parent.mkdir(mode=0o700)
            fsync_dir(obj.parent.parent)
        if obj.exists():
            existing=read_regular(obj,require_private=True)
            if digest(existing)!=sha:
                raise VaultBlocked('EXISTING_OBJECT_HASH_DRIFT')
        else:
            atomic_new(obj,raw)
        m={
            'schema_version':EVIDENCE_SCHEMA,'evidence_id':evidence_id,
            'artifact_sha256':sha,'size_bytes':len(raw),'evidence_type':detail['evidence_kind'],
            'source_head':detail['source_head'],
            'origin_basename':source.name, 'owner_module':'forprint_system_blueprint',
            'scope':'CF10_G2B_INPUT_CANDIDATE','lifecycle_state':'REGISTERED_NON_AUTHORIZING',
            'trust_class':'TECHNICAL_INTEGRITY_CHECKED_NOT_INDEPENDENTLY_ACCEPTED',
            'retention_policy':'WHILE_REFERENCED_OR_UNTIL_EXPLICIT_DISPOSITION',
            'registered_utc':datetime.now(timezone.utc).isoformat(),
            'authority_granted':False,'signed_activation_renewed':False,
            'backup_verified':False, 'deletion_authorized':False,
        }
        mbytes=encode(m)
        atomic_new(target,mbytes)
        event={'event':'REGISTER_NON_AUTHORIZING','evidence_id':evidence_id,
               'artifact_sha256':sha,'manifest_sha256':digest(mbytes),'authority_granted':False}
        atomic_new(ev,encode(event))
        return {**verify_registered(root,evidence_id,strict=strict),'state':'REGISTERED_NON_AUTHORIZING'}


def retrieve(root: Path,evidence_id:str,destination:Path,*,confirmed:bool=False,strict:bool=True) -> dict:
    if not confirmed:raise VaultBlocked('EXPLICIT_RETRIEVAL_CONFIRMATION_REQUIRED')
    if strict:require_root_s01()
    state=verify_registered(root,evidence_id,strict=strict)
    if not destination.is_absolute() or root in destination.parents or destination==root:
        raise VaultBlocked('RETRIEVAL_DESTINATION_UNSAFE')
    check_no_symlinks(destination)
    if not destination.parent.is_dir() or destination.exists():
        raise VaultBlocked('RETRIEVAL_DESTINATION_NOT_NEW_FILE')
    data=read_regular(object_path(root,state['sha256']),require_private=True)
    atomic_new(destination,data)
    return {'state':'EXPORTED_NON_AUTHORIZING','destination':str(destination),'sha256':digest(data), 'authority_granted':False}


def inspect(root: Path, *, strict: bool = True) -> dict:
    if not root.exists():
        return {'state':'NOT_INITIALIZED_NON_AUTHORIZING','vault_initialized':False,'authority_granted':False}
    validate_root(root,strict=strict)
    manifests=list((root/'manifests'/'by-id').glob('*.json'))
    events=list((root/'journal'/'events').glob('*.json'))
    return {'state':'INITIALIZED_NON_AUTHORIZING','vault_initialized':True,
            'registered_manifest_count':len(manifests),'journal_event_count':len(events),
            'authority_granted':False,'backup_verified':False,'cleanup_supported':False}


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('inspect','init','propose','register','verify','retrieve'))
    p.add_argument('--source',type=Path)
    p.add_argument('--evidence-id')
    p.add_argument('--destination',type=Path)
    p.add_argument('--confirm')
    a=p.parse_args(argv)
    try:
        if a.action=='inspect': result=inspect(BASE)
        elif a.action=='init': result={'state':init(confirmed=a.confirm=='INIT_FORPRINT_EVIDENCE_VAULT_V01')}
        elif a.action=='propose':
            if a.source is None: raise VaultBlocked('SOURCE_REQUIRED')
            result=propose(a.source)
        elif a.action=='register':
            if a.source is None or not a.evidence_id:raise VaultBlocked('SOURCE_AND_EVIDENCE_ID_REQUIRED')
            result=register(BASE,a.source,a.evidence_id,confirmed=a.confirm=='REGISTER_FORPRINT_G2A_EVIDENCE_V01')
        elif a.action=='verify':
            if not a.evidence_id:raise VaultBlocked('EVIDENCE_ID_REQUIRED')
            result=verify_registered(BASE,a.evidence_id)
        else:
            if not a.evidence_id or a.destination is None:raise VaultBlocked('EVIDENCE_ID_AND_DESTINATION_REQUIRED')
            result=retrieve(BASE,a.evidence_id,a.destination,confirmed=a.confirm=='EXPORT_FORPRINT_EVIDENCE_V01')
        print(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2))
        return 0
    except (VaultBlocked,OSError,ValueError,json.JSONDecodeError) as exc:
        print('FORPRINT_EVIDENCE_VAULT=BLOCKED:'+type(exc).__name__+':'+str(exc)[:200],file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
