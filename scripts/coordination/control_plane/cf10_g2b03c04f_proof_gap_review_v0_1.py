"""CF-10 G2b/04F read-only, non-authorizing evidence-gap review.

Verify the pinned 04D->04E reports and source HEAD, then create a finite
operator-facing evidence request matrix. SHA matches are integrity, NOT an
independent claim of coverage, authenticity, signature or launch authority.
Never reads external /etc trust payloads; never modifies Gate/Writer/ledger.
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
import subprocess
import sys

SCHEMA = 'cf10_g2b03c04f_proof_gap_review_v0_1'
REPO = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
FOUR_E_SCHEMA = 'cf10_g2b03c04e_proof_submission_integrity_review_v0_1'
FOUR_D_SCHEMA = 'cf10_g2b03c04d_operator_evidence_survey_v0_1'
FOUR_E_SOURCE = 'scripts/coordination/control_plane/cf10_g2b03c04e_proof_submission_review_v0_1.py'
FOUR_B_SOURCE = 'scripts/coordination/control_plane/cf10_g2b03c04b_dynamic_coverage_proof_contract_v0_1.py'
SHA40 = re.compile(r'[a-f0-9]{40}\Z')
SHA64 = re.compile(r'[a-f0-9]{64}\Z')
TIMESTAMP = re.compile(r'cf10_g2b03c04([de])_(survey|intake)_[0-9]{8}T[0-9]{6,12}Z\Z')
PROOFS = (
 ('COMPLETE_CURRENT_WRITER_ENTRYPOINTS','Inventory current source, dynamic imports and indirect callbacks'),
 ('ALL_WRITER_PROCESSES_ENROLLED','Map running AND short-lived Writer processes to mandatory enrollment'),
 ('RUNNING_WRITER_RESTART_OR_DRAIN','Independently observe freeze-boundary drain/restart'),
 ('SCHEDULED_MANUAL_REMOTE_WRITERS','Cover systemd/timers/cron/Make/CLI/containers/SSH/remote/mounts'),
 ('CANONICAL_LOCK_AND_LEDGER_EXCLUSIVITY','Verify DAC/ACL/mount and canonical ledger lock for every write route'),
 ('INDEPENDENT_DYNAMIC_PROOF','Independently published verifier and dynamic observations'),
 ('SIGNED_COVERAGE_APPROVAL','Cryptographically verify HEAD/source/coverage/nonce/expiry/review binding'),
 ('RUNTIME_BINDING_AND_QUARANTINE_ACCEPTANCE','Separate operator acceptance of v0.3+ binding and Make unquarantine'),
)

class ReviewBlocked(RuntimeError):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ReviewBlocked(reason)


def read_private(path:Path,*,limit:int=2_000_000)->bytes:
    require(path.is_absolute() and '..' not in path.parts,'REPORT_PATH_INVALID')
    require(not path.is_symlink() and not path.parent.is_symlink(),'REPORT_SYMLINK')
    pst=path.parent.stat()
    require(stat.S_ISDIR(pst.st_mode) and pst.st_uid==0 and not (stat.S_IMODE(pst.st_mode)&0o077),
            'REPORT_PARENT_NOT_ROOT_PRIVATE')
    st=path.lstat()
    require(stat.S_ISREG(st.st_mode) and st.st_uid==0 and stat.S_IMODE(st.st_mode)==0o600 and
            st.st_nlink==1 and 0<st.st_size<=limit,'REPORT_FILE_METADATA_UNSAFE')
    fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
    try:
        a=os.fstat(fd)
        require((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns),
                'REPORT_CHANGED_BEFORE_READ')
        data=os.read(fd,limit+1)
        b=os.fstat(fd)
        require(len(data)==st.st_size and len(data)<=limit and
                (b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns)==(a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns),
                'REPORT_CHANGED_DURING_READ')
        return data
    finally:
        os.close(fd)


def json_object(data:bytes)->dict:
    try:
        out=json.loads(data)
    except (UnicodeError,ValueError) as e:
        raise ReviewBlocked('REPORT_JSON_INVALID') from e
    require(isinstance(out,dict),'REPORT_NOT_OBJECT')
    return out


def verify_artifacts(root:Path,kind:str,report:Path,pin:str)->dict:
    require(kind in ('04D','04E') and SHA64.fullmatch(pin) is not None,'BAD_EVIDENCE_PIN')
    expected_name='cf10_g2b03c'+kind.lower()+'_' + ('survey' if kind=='04D' else 'intake')
    require(report.parent.parent==root/'tmp' and report.name=='report.json' and
            report.parent.name.startswith(expected_name+'_') and TIMESTAMP.fullmatch(report.parent.name) is not None and
            not (root/'tmp').is_symlink(),
            'REPORT_LOCATOR_UNEXPECTED')
    manifest=read_private(report.parent/'SHA256SUMS',limit=32_768).decode('ascii')
    hashes={}
    for line in manifest.splitlines():
        h,sep,name=line.partition('  ')
        require(bool(sep) and SHA64.fullmatch(h) is not None and name not in hashes,'SHA256SUMS_MALFORMED')
        hashes[name]=h
    expected={'report.json','summary.txt','schedule_evidence.json','operator_proof_intake_template.json'} if kind=='04D' else {'report.json','summary.txt','submission_index_template.json'}
    require(set(hashes)==expected and hashes['report.json']==pin,'SHA256SUMS_PIN_OR_FILESET_MISMATCH')
    data={}
    for filename in sorted(expected):
        blob=read_private(report.parent/filename)
        require(digest(blob)==hashes[filename],'ARTIFACT_HASH_DRIFT:'+filename)
        if filename.endswith('.json'):
            data[filename]=json_object(blob)
    return data


def classify(d:dict,e:dict,*,head:str,d_pin:str,e_pin:str,exact_sources:dict[str,str],predecessor_head:str|None=None)->dict:
    """Pure fail-closed verification of *frozen report claims*, never authority."""
    require(SHA40.fullmatch(head) is not None,'BAD_HEAD')
    predecessor_head=predecessor_head or head
    require(SHA40.fullmatch(predecessor_head) is not None,'BAD_PREDECESSOR_HEAD')
    require(d.get('schema_version')==FOUR_D_SCHEMA and d.get('source_head')==predecessor_head and
            d.get('status')=='OPERATOR_EVIDENCE_SURVEY_CAPTURED_WITH_GAPS_NON_AUTHORIZING' and
            d.get('proof_rows')==8 and d.get('proofs_attested')==0 and d.get('proofs_submitted')==0 and
            d.get('blockers')==[] and d.get('authority_granted') is False and
            d.get('independent_dynamic_coverage_verified') is False and d.get('launch_allowed') is False,
            '04D_REPORT_CLAIMS_DRIFT')
    require(e.get('schema_version')==FOUR_E_SCHEMA and e.get('source_head')==predecessor_head and
            e.get('frozen_04d_sha256')==d_pin and e.get('frozen_04d_head')==predecessor_head and
            e.get('status') in ('OPERATOR_PROOF_INTAKE_READY_AWAITING_EXTERNAL_SUBMISSIONS_NON_AUTHORIZING',
                                'OPERATOR_PROOF_INTAKE_INTEGRITY_REVIEW_NON_AUTHORIZING') and
            e.get('proofs_attested')==0 and e.get('blockers',[])==[] and
            e.get('authority_granted') is False and e.get('launch_allowed') is False and
            e.get('dynamic_coverage_verified') is False and
            e.get('content_and_authenticity_independently_verified') is False and
            e.get('signed_operator_decision_verified') is False and
            e.get('signature_cryptographically_verified') is False and
            e.get('worker_launched') is False and e.get('make_quarantine_removed') is False,
            '04E_REPORT_CLAIMS_DRIFT')
    matrix=e.get('matrix')
    require(isinstance(matrix,list) and len(matrix)==len(PROOFS) and e.get('requirement_count')==len(PROOFS),
            '04E_MATRIX_LENGTH_INVALID')
    expected_ids=[x[0] for x in PROOFS]
    require([row.get('id') if isinstance(row,dict) else None for row in matrix]==expected_ids,
            '04E_MATRIX_IDS_DRIFT')
    result=[]
    for row,(ident,requirement) in zip(matrix,PROOFS):
        require(row.get('attested') is False and row.get('independent_verifier')=='NOT_VERIFIED',
                '04E_MATRIX_ASSERTS_UNVERIFIED_ATTESTATION')
        state=row.get('intake_state')
        require(state in ('NOT_SUBMITTED','HASH_VERIFIED_CONTENT_UNREVIEWED'),'04E_MATRIX_STATE_INVALID')
        if state=='NOT_SUBMITTED':
            require(row.get('evidence_sha256') is None and row.get('evidence_reference') is None,
                    '04E_UNSUBMITTED_ROW_CONTAINS_PROOF')
        else:
            require(isinstance(row.get('evidence_sha256'),str) and
                    SHA64.fullmatch(row['evidence_sha256']) is not None and
                    isinstance(row.get('evidence_reference'),str) and row['evidence_reference'].startswith('evidence/'),
                    '04E_SUBMISSION_ROW_METADATA_INVALID')
        result.append({'requirement_id':ident,'required_review':requirement,
                       'integrity_state':state,'independent_attestation':'NOT_VERIFIED',
                       'evidence_reference':row.get('evidence_reference'),
                       'evidence_sha256':row.get('evidence_sha256'),
                       'operator_next_action':('SUBMIT_INDEPENDENT_EVIDENCE' if state=='NOT_SUBMITTED'
                                               else 'INDEPENDENT_CONTENT_AND_AUTHENTICITY_REVIEW')})
    count=sum(x['integrity_state']!='NOT_SUBMITTED' for x in result)
    require(e.get('submission_integrity_count')==count,'04E_SUBMISSION_COUNT_DRIFT')
    require(set(exact_sources)=={FOUR_E_SOURCE,FOUR_B_SOURCE} and all(SHA64.fullmatch(x) for x in exact_sources.values()),
            'PUBLISHED_SOURCE_PIN_INCOMPLETE')
    stale = predecessor_head != head
    blockers=['INDEPENDENT_EXTERNAL_PROOF_CONTENT_AND_AUTHORITY_REQUIRED']
    if stale: blockers.append('CURRENT_HEAD_DIFFERS_FROM_FROZEN_EVIDENCE_HEAD')
    return {'schema_version':SCHEMA,
            'status':('04F_HISTORICAL_PROVENANCE_ONLY_CURRENT_HEAD_REVIEW_REQUIRED_NON_AUTHORIZING' if stale else
                      '04F_EVIDENCE_GAPS_RECORDED_INDEPENDENT_ATTESTATION_REQUIRED_NON_AUTHORIZING'),
            'source_head':head,'frozen_predecessor_head':predecessor_head,
            'frozen_04d_sha256':d_pin,'frozen_04e_sha256':e_pin,
            'canonical_source_sha256':exact_sources,
            'evidence_integrity_submitted':count,'proof_requirements':len(result),'proofs_attested':0,
            'proof_matrix':result,'full_writer_set_proven':False,
            'short_lived_and_remote_writers_verified':False,'content_authenticity_independently_attested':False,
            'signature_cryptographically_verified':False,'runtime_binding_authorized':False,
            'make_quarantine_removed':False,'dynamic_coverage_verified':False,'ledger_append_allowed':False,
            'worker_launched':False,'authority_granted':False,'launch_allowed':False,
            'blockers':blockers,'source_freshness_reconciled':not stale,
            'next_boundary':'04F_INDEPENDENT_OPERATOR_PROOFS_AND_SIGNED_RENEWAL_REQUIRED'}


def git(root:Path,*args:str)->bytes:
    cp=subprocess.run(['git','-C',str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                      timeout=15,check=False)
    require(cp.returncode==0,'GIT_QUERY_FAILED')
    return cp.stdout


def run_review(root:Path,head:str,d_path:Path,d_sha:str,e_path:Path,e_sha:str,predecessor_head:str|None=None)->dict:
    require(root==REPO and not root.is_symlink() and SHA40.fullmatch(head) is not None,'CANONICAL_ROOT_OR_HEAD_INVALID')
    require(git(root,'rev-parse','HEAD').decode().strip()==head,'HEAD_CHANGED')
    # Verify source is from the committed HEAD, not from the potentially dirty worktree.
    sources={}
    for p in (FOUR_E_SOURCE,FOUR_B_SOURCE):
        committed=git(root,'show',head+':'+p)
        require(len(committed)<150_000 and committed,'SOURCE_NOT_BOUNDED')
        sources[p]=digest(committed)
    d=verify_artifacts(root,'04D',d_path,d_sha)['report.json']
    e=verify_artifacts(root,'04E',e_path,e_sha)['report.json']
    out=classify(d,e,head=head,d_pin=d_sha,e_pin=e_sha,exact_sources=sources,predecessor_head=predecessor_head)
    require(git(root,'rev-parse','HEAD').decode().strip()==head,'HEAD_CHANGED_DURING_REVIEW')
    return out


def save(root:Path,doc:dict)->tuple[Path,str]:
    scratch=root/'tmp'
    require(scratch.is_dir() and not scratch.is_symlink(),'PROJECT_TMP_UNSAFE')
    dest=scratch/('cf10_g2b03c04f_review_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dest.mkdir(mode=0o700)
    report=(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
    summary=('CF10_04F_STATUS='+doc['status']+'\nPROOF_ROWS=8\nPROOFS_ATTESTED=0\n'
             'DYNAMIC_COVERAGE_VERIFIED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false\n').encode()
    contents={'report.json':report,'summary.txt':summary}
    contents['SHA256SUMS']=''.join(digest(data)+'  '+name+'\n' for name,data in sorted(contents.items())).encode()
    for name,data in sorted(contents.items()):
        fd=os.open(dest/name,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
    return dest,digest(report)


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--expected-head',required=True)
    p.add_argument('--predecessor-head',default=None)
    p.add_argument('--frozen-04d-report',type=Path,required=True)
    p.add_argument('--frozen-04d-sha256',required=True)
    p.add_argument('--frozen-04e-report',type=Path,required=True)
    p.add_argument('--frozen-04e-sha256',required=True)
    args=p.parse_args(argv)
    try:
        doc=run_review(args.root.absolute(),args.expected_head,args.frozen_04d_report,
                       args.frozen_04d_sha256,args.frozen_04e_report,args.frozen_04e_sha256,args.predecessor_head)
        dest,h=save(args.root.absolute(),doc)
        print('CF10_04F_STATUS='+doc['status'])
        print('PROOF_SUBMISSIONS_INTEGRITY='+str(doc['evidence_integrity_submitted']))
        print('PROOFS_ATTESTED=0\nDYNAMIC_COVERAGE_VERIFIED=false\nAUTHORITY_GRANTED=false\nWORKER_LAUNCHED=false')
        print('REPORT_DIR='+str(dest)+'\nREPORT_SHA256='+h)
        return 0
    except (ReviewBlocked,ValueError,OSError,subprocess.TimeoutExpired) as exc:
        print('CF10_04F_STATUS=BLOCKED_NON_AUTHORIZING\nBLOCKER='+type(exc).__name__+':'+str(exc)[:160],file=sys.stderr)
        print('AUTHORITY_GRANTED=false\nWORKER_LAUNCHED=false',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
