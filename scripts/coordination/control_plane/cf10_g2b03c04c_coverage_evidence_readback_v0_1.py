"""CF10 G2b-03C/04C: non-authorizing independent 04B evidence readback.

Cross-check frozen 04B report against currently published evidence and live scan.
Creates a missing-proof operator intake matrix, NOT independent dynamic coverage,
writer enrollment, signature verification, acceptance, or launch permission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

SCHEMA = 'cf10_g2b03c04c_evidence_readback_v0_1'
DEPLOYMENT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
PRIOR_REPORT_REL = Path('tmp/cf10_g2b03c04b_coverage_20261028T141615684389Z/report.json')
PRIOR_SHA256 = '0e786e2b98a2e632f4393150e3e8473c6062d00f6f491b7cb46fcdb2fa7c9ba2'
PRIOR_HEAD = '0c07e3ab83f9dd838a9bf19eb6e25f708f812028'
B3_REL = Path('tmp/cf10_g2b03c03b_review_20261028T135332890726Z/report.json')
B3_SHA256 = '74d069eae81fea583375fede6d320b3ba23fbc337b73b03b788236a2e3dc3a3b'
SELF_REL = 'scripts/coordination/control_plane/cf10_g2b03c04c_coverage_evidence_readback_v0_1.py'
NEXT = 'G2B03C04D_OPERATOR_SOURCE_COVERAGE_AND_ENROLLMENT_EVIDENCE_COLLECTION'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
SHA64 = re.compile(r'[0-9a-f]{64}\Z')

class EvidenceReadbackBlocked(RuntimeError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def private_read(path: Path, *, maximum: int = 2_000_000, allow_empty: bool = False) -> bytes:
    """One bounded nofollow read. Report and its directory must be root-private."""
    if not path.is_absolute() or '..' in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise EvidenceReadbackBlocked('REPORT_PATH_NONCANONICAL_OR_SYMLINK')
    parent = path.parent
    st_dir = parent.lstat()
    if not stat.S_ISDIR(st_dir.st_mode) or st_dir.st_uid != 0 or st_dir.st_mode & 0o077:
        raise EvidenceReadbackBlocked('REPORT_DIRECTORY_NOT_ROOT_PRIVATE')
    st = path.lstat()
    if (not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or stat.S_IMODE(st.st_mode) != 0o600
            or st.st_nlink != 1 or st.st_size > maximum or (st.st_size == 0 and not allow_empty)):
        raise EvidenceReadbackBlocked('REPORT_NOT_PRIVATE_REGULAR_OR_BOUNDED')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        cur = os.fstat(fd)
        if (st.st_dev, st.st_ino, st.st_size) != (cur.st_dev, cur.st_ino, cur.st_size):
            raise EvidenceReadbackBlocked('REPORT_RACE')
        raw = bytearray()
        while len(raw) <= maximum:
            chunk = os.read(fd, min(65536,maximum+1-len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        final = os.fstat(fd)
        if (len(raw) != st.st_size or len(raw) > maximum or
            (cur.st_dev,cur.st_ino,cur.st_size,cur.st_mtime_ns) !=
            (final.st_dev,final.st_ino,final.st_size,final.st_mtime_ns)):
            raise EvidenceReadbackBlocked('REPORT_CHANGED_OR_OVERSIZE')
        return bytes(raw)
    finally:
        os.close(fd)


def load_prior(root: Path, path: Path, expected_sha: str) -> dict:
    if path != root / PRIOR_REPORT_REL or expected_sha != PRIOR_SHA256:
        raise EvidenceReadbackBlocked('04B_REPORT_PATH_OR_PIN_MISMATCH')
    raw = private_read(path)
    if sha(raw) != expected_sha:
        raise EvidenceReadbackBlocked('04B_REPORT_DIGEST_MISMATCH')
    sums = private_read(path.parent/'SHA256SUMS', maximum=100_000).decode('ascii')
    expected = {'report.json','summary.txt'}
    entries = {}
    for line in sums.splitlines():
        digest, sep, name = line.partition('  ')
        if not sep or not SHA64.fullmatch(digest) or name not in expected or name in entries:
            raise EvidenceReadbackBlocked('04B_SHA256SUMS_INVALID')
        entries[name] = digest
    if set(entries) != expected or entries['report.json'] != expected_sha:
        raise EvidenceReadbackBlocked('04B_MANIFEST_SET_OR_PIN_MISMATCH')
    if sha(private_read(path.parent/'summary.txt')) != entries['summary.txt']:
        raise EvidenceReadbackBlocked('04B_SUMMARY_INTEGRITY_FAILED')
    try:
        doc = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise EvidenceReadbackBlocked('04B_REPORT_JSON_INVALID') from exc
    if not isinstance(doc,dict):
        raise EvidenceReadbackBlocked('04B_REPORT_SCHEMA_INVALID')
    return doc


def classify(*, archived:dict, fresh:dict, head:str, self_published:bool,
             proof_requirements:tuple | None=None) -> dict:
    if proof_requirements is None:
        from scripts.coordination.control_plane import cf10_g2b03c04b_dynamic_coverage_proof_contract_v0_1 as proof
        proof_requirements = proof.PROOF_REQUIREMENTS
    blockers=[]
    findings=[]
    if not SHA40.fullmatch(head) or not SHA40.fullmatch(archived.get('source_head','')) or archived.get('source_head') != PRIOR_HEAD:
        blockers.append('PRIOR_HEAD_NOT_PINNED')
    if self_published is not True:
        blockers.append('SELF_SOURCE_NOT_PUBLISHED')
    for tag, record in (('ARCHIVED',archived),('FRESH',fresh)):
        if (record.get('status') != 'DYNAMIC_COVERAGE_PROOF_CONTRACT_MAPPED_NON_AUTHORIZING'
            or record.get('blockers') != [] or record.get('authority_granted') is not False
            or record.get('independent_dynamic_coverage_verified') is not False
            or record.get('signature_verified') is not False or record.get('launch_allowed') is not False
            or record.get('proof_requirements_satisfied') != 0):
            blockers.append(tag+'_04B_PROOF_CONTRACT_INVALID')
        rows=record.get('proof_requirements')
        expected=[x[0] for x in proof_requirements]
        if (not isinstance(rows,list) or len(rows)!=len(expected) or
            [r.get('id') if isinstance(r,dict) else None for r in rows] != expected or
            any(not isinstance(r,dict) or r.get('status')!='NOT_ATTESTED'
                or r.get('required_evidence') != proof_requirements[i][1] for i,r in enumerate(rows))):
            blockers.append(tag+'_REQUIREMENTS_MISMATCH')
    archived_static=archived.get('static_inventory',{})
    fresh_static=fresh.get('static_inventory',{})
    if (not isinstance(archived_static,dict) or not isinstance(fresh_static,dict) or
        archived_static != fresh_static or archived_static.get('full_writer_set_proven') is not False):
        blockers.append('STATIC_SOURCE_OR_CANDIDATE_DRIFT')
    archived_proc=archived.get('process_observation',{})
    fresh_proc=fresh.get('process_observation',{})
    if (not isinstance(archived_proc,dict) or not isinstance(fresh_proc,dict) or
        archived_proc.get('scan_is_complete_dynamic_attestation') is not False or
        fresh_proc.get('scan_is_complete_dynamic_attestation') is not False or
        archived_proc.get('absence_of_writers_proven') is not False or
        fresh_proc.get('absence_of_writers_proven') is not False or
        fresh_proc.get('unreadable_count') != 0):
        blockers.append('PROCESS_OBSERVATION_SEMANTICS_INVALID')
    if archived_proc.get('observed_recognized_count') != fresh_proc.get('observed_recognized_count'):
        findings.append('PROCESS_COUNT_CHANGED_SINCE_04B_REQUIRES_OPERATOR_REVIEW')
    if archived.get('findings') != fresh.get('findings'):
        findings.append('EXTERNAL_EVIDENCE_METADATA_FINDINGS_CHANGED')
    intake=[{'id':key,'state':'NOT_SUBMITTED','operator_evidence_required':description,
             'independent_evidence_id':None,'evidence_sha256':None,
             'review_authority':'NOT_VERIFIED'} for key,description in proof_requirements]
    status = 'BLOCKED_NON_AUTHORIZING' if blockers else 'INDEPENDENT_EVIDENCE_READBACK_READY_FOR_OPERATOR_PROOFS_NON_AUTHORIZING'
    return {
        'schema_version': SCHEMA,'status':status,'blockers':sorted(set(blockers)),
        'findings':sorted(set(findings)),'source_head':head,
        'frozen_04b_head':PRIOR_HEAD,'frozen_04b_report_sha256':PRIOR_SHA256,
        'frozen_static_candidate_count':len(archived_static.get('candidates',[])) if isinstance(archived_static.get('candidates'),list) else None,
        'archived_recognized_processes':archived_proc.get('observed_recognized_count'),
        'fresh_recognized_processes':fresh_proc.get('observed_recognized_count'),
        'static_source_revalidated':not blockers,
        'operator_proof_intake':intake,'proofs_submitted':0,'proofs_attested':0,
        'operator_proof_status':'AWAITING_EXTERNAL_INDEPENDENT_EVIDENCE',
        'independent_dynamic_coverage_verified':False,
        'complete_writer_entrypoint_set_verified':False,
        'writer_process_enrollment_verified':False,
        'writer_restart_or_drain_verified':False,
        'signed_current_head_verified':False,
        'signature_cryptographically_verified':False,
        'runtime_binding_authorized':False,'writer_gate_unquarantined':False,
        'launch_allowed':False,'ledger_append_allowed':False,
        'worker_launched':False,'ledger_mutated':False,'authority_granted':False,
        'next_boundary':NEXT,
    }


def review(root:Path,head:str,*,report:Path,report_sha:str)->dict:
    from scripts.coordination.control_plane import cf10_g2b03c04b_dynamic_coverage_proof_contract_v0_1 as proof
    from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inventory
    from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_1 as runtime
    if root != DEPLOYMENT or root.is_symlink() or not SHA40.fullmatch(head):
        raise EvidenceReadbackBlocked('CANONICAL_ROOT_OR_HEAD_INVALID')
    code = inventory.exact_published_file(root,head,SELF_REL)
    archived = load_prior(root,report,report_sha)
    fresh = proof.review(root,head,b3_report=root/B3_REL,b3_sha256=B3_SHA256)
    if inventory.exact_published_file(root,head,SELF_REL) != code or runtime.git(root,'rev-parse','HEAD') != head:
        raise EvidenceReadbackBlocked('CURRENT_PUBLICATION_CHANGED_DURING_READBACK')
    return classify(archived=archived,fresh=fresh,head=head,self_published=True)


def save(root:Path,doc:dict)->tuple[Path,str]:
    scratch=root/'tmp'
    if not scratch.is_dir() or any(p.is_symlink() for p in (scratch,*scratch.parents)):
        raise EvidenceReadbackBlocked('PROJECT_TMP_UNSAFE')
    out=scratch/('cf10_g2b03c04c_readback_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(mode=0o700)
    data=(json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
    summary=('CF10_G2B03C04C_STATUS='+doc['status']+'\n'+
            ''.join('BLOCKER='+b+'\n' for b in doc['blockers'])+
            ''.join('FINDING='+f+'\n' for f in doc['findings'])+
            'PROOFS_ATTESTED=0\nDYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\n'+
            'WORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false\n').encode()
    parts={'report.json':data,'summary.txt':summary}
    parts['SHA256SUMS']=''.join(sha(raw)+'  '+name+'\n' for name,raw in sorted(parts.items())).encode()
    for name,raw in sorted(parts.items()):
        fd=os.open(out/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return out,sha(data)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--expected-head',required=True)
    p.add_argument('--frozen-report',required=True,type=Path)
    p.add_argument('--frozen-sha256',required=True)
    args=p.parse_args(argv)
    try:
        root=args.root.absolute()
        doc=review(root,args.expected_head,report=args.frozen_report,report_sha=args.frozen_sha256)
        folder,digest=save(root,doc)
        print('CF10_G2B03C04C_STATUS='+doc['status'])
        print('FROZEN_STATIC_APPEND_CANDIDATES='+str(doc['frozen_static_candidate_count']))
        print('FRESH_RECOGNIZED_PROCESSES='+str(doc['fresh_recognized_processes']))
        print('PROOF_REQUIREMENTS='+str(len(doc['operator_proof_intake'])))
        print('PROOFS_ATTESTED=0')
        for item in doc['findings']:print('FINDING='+item)
        for item in doc['blockers']:print('BLOCKER='+item)
        print('REPORT_DIR='+str(folder));print('REPORT_SHA256='+digest)
        print('DYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        return 2 if doc['blockers'] else 0
    except (EvidenceReadbackBlocked,OSError,ValueError,RuntimeError) as exc:
        print('CF10_G2B03C04C_STATUS=BLOCKED_NON_AUTHORIZING',file=sys.stderr)
        print('BLOCKER='+type(exc).__name__+':'+str(exc)[:190],file=sys.stderr)
        print('AUTHORITY_GRANTED=false',file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
