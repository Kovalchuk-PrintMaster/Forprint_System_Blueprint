"""CF-10 G2b-01: read-only, non-authorizing Gate/Writer evidence inventory.

Bounded named-file inspection only. Never invokes pinned verifier/Worker, writes signed
state, edits provenance, copies historical evidence, or accepts a rebind.
Optional review output is create-only, ignored, scratch-local and NOT acceptance proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

from scripts.coordination.control_plane import cf10_stable_release_roots_v0_1 as g2
from scripts.coordination.evidence_management import vault_v0_1 as vault

SCHEMA = 'cf10_g2b01_evidence_inventory_v0_1'
BRANCH = g2.BRANCH
ORIGIN = g2.ORIGIN
EXPECTED_COVERAGE_SHA256 = '15bb96b3fdb87186d8337dfa17391bfd5a5a951e2faae34c8c671734d4027b71'
HISTORICAL_COVERAGE_REL = 'tmp/cf10_gate_rollover_7odYLfVr/tmp/cf10_writer_coverage_gate3d90143_170494.json'
STABLE_COVERAGE = g2.BASE/'evidence'/'cf10_writer_coverage_gate3d90143_170494.json'
SIGNED_DECISION = Path('/etc/forprint/execution_attempt_writer_activation/signed_decision_v0_1.json')
EVIDENCE_ID = 'cf10-g2a-stable-releases-f37abe98-20261028'
MAX_COVERAGE = 1_000_000
SHA40 = re.compile(r'[a-f0-9]{40}\Z')

class ReviewBlocked(RuntimeError): pass

def row(name: str, status: str, detail: str, **extras: Any) -> dict[str, Any]:
    return {'id': name, 'status': status, 'detail': detail, **extras}

def git_read(repo: Path, *args: str) -> str:
    try:
        p = subprocess.run(['git', *args], cwd=repo, capture_output=True,
                           text=True, timeout=25, check=False)
    except (OSError, subprocess.SubprocessError) as e:
        raise ReviewBlocked('GIT_READ_UNAVAILABLE:' + args[0]) from e
    if p.returncode:
        raise ReviewBlocked('GIT_READ_FAILED:' + args[0] + ':RC=' + str(p.returncode))
    return p.stdout.strip()

def regular_private_or_stable(path: Path, max_size: int, *, require_root: bool = False) -> bytes:
    if not path.is_absolute() or '..' in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ReviewBlocked('UNSAFE_PATH_OR_SYMLINK')
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_size > max_size or (st.st_mode & 0o022):
        raise ReviewBlocked('FILE_KIND_SIZE_OR_MODE_UNSAFE')
    if require_root and st.st_uid != 0:
        raise ReviewBlocked('FILE_NOT_ROOT_OWNED')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        actual = os.fstat(fd)
        if (actual.st_dev,actual.st_ino,actual.st_size)!=(st.st_dev,st.st_ino,st.st_size):
            raise ReviewBlocked('FILE_RACE_DETECTED')
        data = bytearray()
        while len(data) <= max_size:
            part = os.read(fd, min(65536, max_size + 1 - len(data)))
            if not part: break
            data.extend(part)
        if len(data)>max_size: raise ReviewBlocked('FILE_TOO_LARGE')
        return bytes(data)
    finally:
        os.close(fd)

def coverage_probe(path: Path, name: str) -> dict[str, Any]:
    if not path.exists() and not path.is_symlink():
        return row(name, 'MISSING', 'EXPECTED_PATH_ABSENT_NOT_REBOUND', path=str(path))
    try:
        raw = regular_private_or_stable(path, MAX_COVERAGE)
        actual = hashlib.sha256(raw).hexdigest()
        if actual != EXPECTED_COVERAGE_SHA256:
            return row(name, 'BLOCKED', 'COVERAGE_SHA256_DRIFT', path=str(path), actual_sha256=actual)
        data = json.loads(raw)
        if not isinstance(data,dict) or data.get('schema_version') != 'forprint_execution_attempt_writer_deployment_evidence_v0_2':
            return row(name, 'BLOCKED', 'COVERAGE_SCHEMA_DRIFT', path=str(path), actual_sha256=actual)
        if data.get('status') != 'READY_FOR_INDEPENDENT_REVIEW' or data.get('technical_blockers') != []:
            return row(name, 'BLOCKED', 'COVERAGE_TECHNICAL_STATE_DRIFT', path=str(path), actual_sha256=actual)
        for kind in ('gate','writer'):
            node = data.get(kind+'_publication',{})
            pin = g2.RELEASES[kind]
            if not isinstance(node,dict) or (node.get('remote'),node.get('ref'),node.get('commit')) != (ORIGIN,pin['ref'],pin['head']):
                return row(name, 'BLOCKED', 'COVERAGE_PUBLICATION_PIN_DRIFT:'+kind, path=str(path), actual_sha256=actual)
        return row(name, 'PASS', 'HISTORICAL_SHA_AND_PIN_PROFILE_MATCH_NON_AUTHORIZING', path=str(path), sha256=actual)
    except (ReviewBlocked,OSError,ValueError,UnicodeError) as e:
        return row(name, 'BLOCKED', type(e).__name__+':'+str(e)[:150], path=str(path))

def signer_probe(path: Path) -> dict[str, Any]:
    # Never disclose/read the signed payload or evaluate an Ed25519 signature here.
    if not path.exists() and not path.is_symlink():
        return row('external_signed_decision', 'MISSING', 'NOT_PRESENT_OR_NOT_ACCESSIBLE', path=str(path))
    try:
        if any(p.is_symlink() for p in (path,*path.parents)):
            raise ReviewBlocked('SYMLINK_IN_SIGNED_DECISION_PATH')
        parent=path.parent.stat(); st=path.lstat()
        if (parent.st_uid!=0 or parent.st_mode & 0o022 or st.st_uid!=0 or
            not stat.S_ISREG(st.st_mode) or st.st_mode & 0o022 or st.st_size>1_048_576):
            raise ReviewBlocked('SIGNED_DECISION_METADATA_UNSAFE')
        return row('external_signed_decision','REVIEW',
                   'ROOT_CONTROLLED_METADATA_OBSERVED_SIGNATURE_AND_NEW_HEAD_NOT_VERIFIED',
                   path=str(path),size_bytes=st.st_size)
    except (OSError, ReviewBlocked) as e:
        return row('external_signed_decision','BLOCKED',type(e).__name__+':'+str(e)[:130],path=str(path))

def exact_published_file(root: Path, expected: str, rel: str) -> str:
    if (root/rel).is_symlink(): raise ReviewBlocked('SOURCE_SYMLINK:'+rel)
    raw=regular_private_or_stable(root/rel,2_000_000)
    committed=subprocess.run(['git','show',expected+':'+rel],cwd=root,capture_output=True,timeout=20,check=False)
    if committed.returncode != 0: raise ReviewBlocked('PUBLISHED_FILE_MISSING:'+rel)
    if raw!=committed.stdout: raise ReviewBlocked('SOURCE_BYTES_NOT_PUBLISHED:'+rel)
    return raw.decode('utf-8','strict')

def canonical_probe(root: Path, expected: str) -> tuple[dict[str,Any],dict[str,str]]:
    texts:dict[str,str]={}
    try:
        if not SHA40.fullmatch(expected) or not root.is_absolute() or root.is_symlink():
            raise ReviewBlocked('ROOT_OR_EXPECTED_SHA_INVALID')
        if git_read(root,'rev-parse','--show-toplevel')!=str(root):raise ReviewBlocked('NOT_CANONICAL_GIT_TOP')
        if git_read(root,'rev-parse','HEAD')!=expected: raise ReviewBlocked('EXPECTED_HEAD_DRIFT')
        if git_read(root,'branch','--show-current')!=BRANCH:raise ReviewBlocked('CANONICAL_BRANCH_DRIFT')
        if git_read(root,'remote','get-url','origin')!=ORIGIN:raise ReviewBlocked('CANONICAL_ORIGIN_DRIFT')
        if git_read(root,'diff','--cached','--name-only'):raise ReviewBlocked('STAGED_INDEX_DIRTY')
        for rel in ('Makefile',
                    'scripts/coordination/control_plane/s01_writer_runtime_binding_v0_1.py',
                    'scripts/coordination/control_plane/s01_writer_runtime_binding_v0_2.py',
                    'scripts/coordination/control_plane/cf10_stable_release_roots_v0_1.py',
                    'scripts/coordination/evidence_management/vault_v0_1.py'):
            texts[rel]=exact_published_file(root,expected,rel)
        return row('canonical','PASS','HEAD_BRANCH_ORIGIN_SOURCE_BYTES_VERIFIED',head=expected),texts
    except (OSError,ReviewBlocked,UnicodeError,ValueError,subprocess.SubprocessError) as e:
        return row('canonical','BLOCKED',type(e).__name__+':'+str(e)[:160]),{}

def make_boundary_probe(texts: dict[str,str]) -> list[dict[str,Any]]:
    if not texts:
        return [row('make_launch_boundary','BLOCKED','CANONICAL_SOURCE_NOT_VERIFIED'),
                row('legacy_coverage_path_dependency','REVIEW','UNREADABLE_CANONICAL_SOURCE')]
    make=texts['Makefile']
    v1=texts['scripts/coordination/control_plane/s01_writer_runtime_binding_v0_1.py']
    v2=texts['scripts/coordination/control_plane/s01_writer_runtime_binding_v0_2.py']
    pins=(str(g2.stable_path('gate')),str(g2.stable_path('writer')),str(STABLE_COVERAGE))
    if (any(p not in make for p in pins) or make.count('CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND')!=2
        or 'governed-worker-cycle-launch: cf10-s01-runtime-launch-preflight' not in make):
        quarantine=row('make_launch_boundary','BLOCKED','MAKE_STABLE_PATH_OR_QUARANTINE_DRIFT')
    else:
        quarantine=row('make_launch_boundary','PASS','STABLE_PATHS_QUARANTINED_NO_EXECUTION_AUTHORITY')
    old="coverage_path.parent.resolve() != (gate_root / \"tmp\").resolve()"
    legacy=('COVERAGE_EVIDENCE_NOT_FROM_GATE_TMP' in v1 and 'gate_root / "tmp"' in v1 and
            'from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_1 as inventory' in v2)
    return [quarantine,row('legacy_coverage_path_dependency','REVIEW' if legacy else 'BLOCKED',
                            'V01_REQUIRES_GATE_ROOT_TMP_G2B02_REVIEW_REQUIRED' if legacy else
                            'KNOWN_LEGACY_BINDING_NOT_FOUND_REVIEW_SOURCE_DIFF')]

def release_probe(kind: str) -> dict[str,Any]:
    path=g2.stable_path(kind)
    inspected=g2.inspect_release(path,kind)
    return row('stable_'+kind, inspected['status'],inspected.get('reason','UNSPECIFIED'),
               path=str(path),head=g2.RELEASES[kind]['head'])

def vault_probe() -> dict[str, Any]:
    try:
        result=vault.verify_registered(vault.BASE,EVIDENCE_ID)
        if result.get('state')!='VERIFIED_REGISTERED_NON_AUTHORIZING':
            raise ReviewBlocked('VAULT_UNEXPECTED_STATE')
        return row('g2a_vault_registration','PASS','G2A_RELEASE_REPORT_REGISTERED_NOT_COVERAGE_REBIND',
                   evidence_id=EVIDENCE_ID,sha256=result['sha256'])
    except (OSError,vault.VaultBlocked,ReviewBlocked,ValueError) as e:
        return row('g2a_vault_registration','BLOCKED',type(e).__name__+':'+str(e)[:130],evidence_id=EVIDENCE_ID)

def review(root: Path, expected: str, historical: Path, *, verify_vault: bool=True,
           signer: Path=SIGNED_DECISION) -> dict[str, Any]:
    canonical,texts=canonical_probe(root,expected)
    checks=[canonical,*make_boundary_probe(texts),release_probe('gate'),release_probe('writer'),
            coverage_probe(historical,'historical_coverage'),coverage_probe(STABLE_COVERAGE,'stable_coverage_target'),
            signer_probe(signer)]
    if verify_vault: checks.append(vault_probe())
    blocked=[r['id'] for r in checks if r['status']=='BLOCKED']
    missing=[r['id'] for r in checks if r['status']=='MISSING']
    state='BLOCKED_NON_AUTHORIZING' if blocked else 'INVENTORY_REVIEW_REQUIRED_NON_AUTHORIZING'
    return {'schema_version':SCHEMA,'status':state,'expected_head':expected,
            'checks':checks,'blocked':blocked,'missing':missing,
            'coverage_evidence_rebound':False,'new_signed_head_authorized':False,
            'independent_coverage_verifier_executed':False,'historical_evidence_copied':False,
            'external_signed_payload_read':False,'vault_mutated':False,'worker_launched':False,
            'ledger_mutated':False,'authority_granted':False,
            'backup_state':'PENDING_EXTERNAL_INTEGRATION',
            'next_boundary':'G2B02_INDEPENDENT_COVERAGE_PROVENANCE_AND_BINDING_REVIEW'}

def save_scratch(root: Path, doc: dict[str,Any]) -> Path:
    scratch=root/'tmp'
    if scratch.is_symlink() or not scratch.is_dir(): raise ReviewBlocked('PROJECT_SCRATCH_MISSING_OR_UNSAFE')
    if any(p.is_symlink() for p in (scratch,*scratch.parents)):raise ReviewBlocked('SCRATCH_ANCESTOR_SYMLINK')
    dest=scratch/('cf10_g2b01_inventory_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dest.mkdir(mode=0o700)
    report=(json.dumps(doc,indent=2,ensure_ascii=False,sort_keys=True)+'\n').encode()
    summary=('CF10_G2B01_STATUS='+doc['status']+'\n'+
             '\n'.join(f"{r['id']}={r['status']}:{r['detail']}" for r in doc['checks'])+'\n'+
             'AUTHORITY_GRANTED=false\nWORKER_LAUNCHED=false\nEVIDENCE_VAULT_BACKUP=PENDING_EXTERNAL_INTEGRATION\nBACKUP_VERIFIED=false\n').encode()
    data={'report.json':report,'summary.txt':summary}
    data['SHA256SUMS']=''.join(hashlib.sha256(raw).hexdigest()+'  '+name+'\n' for name,raw in sorted(data.items())).encode()
    for name,raw in sorted(data.items()):
        path=dest/name
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return dest

def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--expected-head',required=True)
    p.add_argument('--historical-coverage',type=Path)
    p.add_argument('--no-vault',action='store_true',help='Diagnostic only: reports Vault as not checked')
    p.add_argument('--no-report',action='store_true')
    a=p.parse_args(argv)
    root=a.root.absolute()
    historical=a.historical_coverage or (root/HISTORICAL_COVERAGE_REL)
    if not historical.is_absolute():
        print('CF10_G2B01=BLOCKED:HISTORICAL_COVERAGE_MUST_BE_ABSOLUTE',file=sys.stderr);return 2
    doc=review(root,a.expected_head,historical,verify_vault=not a.no_vault)
    for r in doc['checks']:
        print(f"{r['id'].upper()}={r['status']}:{r['detail']}")
    print('CF10_G2B01_STATUS='+doc['status'])
    if not a.no_report:
        try:
            dest=save_scratch(root,doc)
            print('REPORT_DIR='+str(dest))
            print('REPORT_SHA256='+hashlib.sha256((dest/'report.json').read_bytes()).hexdigest())
        except (OSError,ReviewBlocked) as e:
            print('CF10_G2B01=BLOCKED:REPORT:'+str(e)[:190],file=sys.stderr);return 2
    print('WORKER_LAUNCHED=false\nSIGNED_RENEWAL_PERFORMED=false\nAUTHORITY_GRANTED=false')
    print('EVIDENCE_VAULT_BACKUP=PENDING_EXTERNAL_INTEGRATION\nBACKUP_VERIFIED=false')
    print('WARNING: Evidence Vault off-host backup and independent restore remain pending.')
    return 2 if doc['blocked'] else 0

if __name__=='__main__':raise SystemExit(main())
