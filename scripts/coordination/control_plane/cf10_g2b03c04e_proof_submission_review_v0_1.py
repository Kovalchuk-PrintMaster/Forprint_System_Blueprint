"""CF10 G2b-03C/04E: operator proof submission *integrity* intake.

Authenticates frozen 04D survey and its five-file manifest, optionally reads a
single private, pin-hashed, explicitly supplied proof index under project tmp,
and checks only submitted evidence file hashes. This DOES NOT decide whether
proofs are true, independent, signed, complete, current beyond the stated HEAD,
or adequate for Writer enrollment, drain/restart, runtime authorization or launch.
No /etc authority payloads, secrets, gates, Writer, ledger or external services.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

SCHEMA = 'cf10_g2b03c04e_proof_submission_integrity_review_v0_1'
INDEX_SCHEMA = 'cf10_g2b03c04e_proof_submission_index_v0_1'
DEPLOYMENT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
SELF_REL = 'scripts/coordination/control_plane/cf10_g2b03c04e_proof_submission_review_v0_1.py'
FOUR_D_REL = Path('tmp/cf10_g2b03c04d_survey_20261028T150642485450Z/report.json')
FOUR_D_SHA = 'a13ad684607d00615265b091c5bb97943ed50ed296faeffe0d576df5b632cbb7'
FOUR_D_HEAD = 'de0113cb4f04fe25276d8a804a2f4ef045cef102'
INDEX_REL = Path('tmp/cf10_g2b03c04e_submissions_v01/index.json')
INDEX_ROOT_REL = Path('tmp/cf10_g2b03c04e_submissions_v01')
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
SHA64 = re.compile(r'[0-9a-f]{64}\Z')
REQ_FILES = ('report.json', 'schedule_evidence.json', 'operator_proof_intake_template.json', 'summary.txt')
NEXT = 'G2B03C04F_INDEPENDENT_EXTERNAL_PROOF_CONTENT_AND_ATTESTATION_VERIFICATION'

class IntakeBlocked(RuntimeError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_read(path: Path, *, max_size: int = 2_000_000, allow_empty: bool = False) -> bytes:
    """Root-owned private single-link regular file, no-follow, bounded and race checked."""
    if not path.is_absolute() or '..' in path.parts or any(p.is_symlink() for p in (path,*path.parents)):
        raise IntakeBlocked('UNSAFE_OR_SYMLINK_EVIDENCE_PATH')
    parent = path.parent.lstat()
    if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0 or stat.S_IMODE(parent.st_mode) & 0o077:
        raise IntakeBlocked('EVIDENCE_PARENT_NOT_ROOT_PRIVATE')
    st = path.lstat()
    if (not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or stat.S_IMODE(st.st_mode) != 0o600
            or st.st_nlink != 1 or st.st_size > max_size or (st.st_size == 0 and not allow_empty)):
        raise IntakeBlocked('EVIDENCE_FILE_NOT_PRIVATE_REGULAR_BOUNDED')
    fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        if (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns) != (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns):
            raise IntakeBlocked('EVIDENCE_RACED_BEFORE_READ')
        parts=[]; read=0
        while read <= max_size:
            chunk=os.read(fd,min(65536,max_size+1-read))
            if not chunk: break
            parts.append(chunk);read+=len(chunk)
        after=os.fstat(fd)
        if read != st.st_size or read > max_size or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns) != (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
            raise IntakeBlocked('EVIDENCE_CHANGED_DURING_READ')
        return b''.join(parts)
    finally:
        os.close(fd)


def decode_json(raw:bytes, label:str)->dict:
    try: out=json.loads(raw)
    except (ValueError,UnicodeError) as exc: raise IntakeBlocked(label+'_JSON_UNREADABLE') from exc
    if not isinstance(out,dict): raise IntakeBlocked(label+'_JSON_NOT_OBJECT')
    return out


def frozen_04d(root:Path,report:Path,expected_sha:str)->tuple[dict,dict]:
    """Verify all four immutable 04D artifacts against the pinned survey."""
    if report != root/FOUR_D_REL or expected_sha != FOUR_D_SHA:
        raise IntakeBlocked('04D_PATH_OR_EXTERNAL_DIGEST_DRIFT')
    folder=report.parent
    if folder.is_symlink() or not folder.is_dir():raise IntakeBlocked('04D_REPORT_DIR_UNSAFE')
    manifest=safe_read(folder/'SHA256SUMS',max_size=100000).decode('ascii')
    hashes={}
    for line in manifest.splitlines():
        h,sep,name=line.partition('  ')
        if not sep or not SHA64.fullmatch(h) or name not in REQ_FILES or name in hashes:
            raise IntakeBlocked('04D_SHA256SUMS_INVALID')
        hashes[name]=h
    if set(hashes)!=set(REQ_FILES) or hashes['report.json'] != expected_sha:
        raise IntakeBlocked('04D_SHA256SUMS_PIN_OR_FILESET_DRIFT')
    decoded={}
    for name in REQ_FILES:
        raw=safe_read(folder/name)
        if sha(raw)!=hashes[name]:raise IntakeBlocked('04D_FILE_HASH_DRIFT:'+name)
        if name.endswith('.json'):decoded[name]=decode_json(raw,name)
    doc=decoded['report.json']; template=decoded['operator_proof_intake_template.json']; schedule=decoded['schedule_evidence.json']
    if (doc.get('schema_version')!='cf10_g2b03c04d_operator_evidence_survey_v0_1'
            or doc.get('source_head')!=FOUR_D_HEAD
            or doc.get('status')!='OPERATOR_EVIDENCE_SURVEY_CAPTURED_WITH_GAPS_NON_AUTHORIZING'
            or doc.get('blockers')!=[] or doc.get('proof_rows')!=8
            or doc.get('proofs_attested')!=0 or doc.get('proofs_submitted')!=0
            or doc.get('authority_granted') is not False
            or doc.get('independent_dynamic_coverage_verified') is not False
            or doc.get('launch_allowed') is not False
            or doc.get('proof_template_sha256')!=hashes['operator_proof_intake_template.json']
            or schedule != doc.get('schedule_survey')):
        raise IntakeBlocked('04D_SURVEY_SEMANTICS_DRIFT')
    rows=template.get('requirements')
    if (template.get('schema_version')!='cf10_g2b03c04d_operator_proof_intake_template_v0_1'
            or template.get('source_head')!=FOUR_D_HEAD or template.get('predecessor_report_sha256')!=doc.get('prior_report_sha256')
            or template.get('submitted_count')!=0 or template.get('accepted_count')!=0
            or template.get('authority_granted') is not False
            or not isinstance(rows,list) or len(rows)!=8):
        raise IntakeBlocked('04D_TEMPLATE_SEMANTICS_DRIFT')
    from scripts.coordination.control_plane.cf10_g2b03c04b_dynamic_coverage_proof_contract_v0_1 import PROOF_REQUIREMENTS
    expected_ids=[x[0] for x in PROOF_REQUIREMENTS]
    if ([r.get('id') if isinstance(r,dict) else None for r in rows]!=expected_ids or
        any(not isinstance(r,dict) or r.get('required_evidence')!=PROOF_REQUIREMENTS[i][1]
            or r.get('state')!='NOT_SUBMITTED' or r.get('evidence_reference') is not None
            or r.get('evidence_sha256') is not None or r.get('independent_verifier_reference') is not None
            or r.get('review_state')!='NOT_VERIFIED' for i,r in enumerate(rows))):
        raise IntakeBlocked('04D_PROOF_MATRIX_DRIFT')
    return doc,template


def safe_relative(value:str)->Path:
    if not isinstance(value,str) or len(value)>240 or not value.startswith('evidence/') or '\\' in value or '\x00' in value:
        raise IntakeBlocked('SUBMISSION_REL_PATH_INVALID')
    p=PurePosixPath(value)
    if (p.is_absolute() or any(x in ('','.', '..') for x in value.split('/')) or len(p.parts)<2 or p.suffix not in ('.json','.txt','.yaml')):
        raise IntakeBlocked('SUBMISSION_REL_PATH_INVALID')
    return Path(*p.parts)


def check_index(index:dict, *, head:str, known_ids:list[str])->list[dict]:
    if set(index)!={'schema_version','source_head','frozen_04d_sha256','submissions'}:
        raise IntakeBlocked('SUBMISSION_SCHEMA_FIELDS_INVALID')
    if (index['schema_version']!=INDEX_SCHEMA or index['source_head']!=head or
            index['frozen_04d_sha256']!=FOUR_D_SHA or not isinstance(index['submissions'],list) or
            len(index['submissions'])>8):
        raise IntakeBlocked('SUBMISSION_HEAD_SCHEMA_OR_LIMIT_DRIFT')
    used_ids=set();used_paths=set()
    for row in index['submissions']:
        if (not isinstance(row,dict) or set(row)!={'requirement_id','artifact_rel','sha256','submitter_ref'}
            or row['requirement_id'] not in known_ids or row['requirement_id'] in used_ids
            or not isinstance(row['sha256'],str) or not SHA64.fullmatch(row['sha256'])
            or not isinstance(row['submitter_ref'],str) or not (1<=len(row['submitter_ref'])<=160)):
            raise IntakeBlocked('SUBMISSION_ROW_INVALID_OR_DUPLICATE')
        rel=safe_relative(row['artifact_rel'])
        if rel in used_paths:raise IntakeBlocked('SUBMISSION_DUPLICATE_ARTIFACT')
        used_ids.add(row['requirement_id']);used_paths.add(rel)
    return index['submissions']


def optional_submission(root:Path,*,head:str,known_ids:list[str],index_path:Path|None,index_sha:str|None)->tuple[list[dict],str]:
    if index_path is None and index_sha is None:return [],'NOT_PROVIDED'
    if index_path is None or not isinstance(index_sha,str) or not SHA64.fullmatch(index_sha):
        raise IntakeBlocked('SUBMISSION_PATH_AND_EXTERNAL_SHA_REQUIRED_TOGETHER')
    if index_path != root/INDEX_REL:
        raise IntakeBlocked('SUBMISSION_INDEX_NOT_PROJECT_PINNED_PATH')
    raw=safe_read(index_path,max_size=100000)
    if sha(raw)!=index_sha:raise IntakeBlocked('SUBMISSION_INDEX_PIN_HASH_MISMATCH')
    entries=check_index(decode_json(raw,'SUBMISSION_INDEX'),head=head,known_ids=known_ids)
    accepted=[]
    for row in entries:
        artifact=root/INDEX_ROOT_REL/safe_relative(row['artifact_rel'])
        raw_e=safe_read(artifact,max_size=2_000_000)
        if sha(raw_e)!=row['sha256']:raise IntakeBlocked('SUBMISSION_ARTIFACT_SHA256_MISMATCH:'+row['requirement_id'])
        accepted.append({'requirement_id':row['requirement_id'],'artifact_rel':row['artifact_rel'],
                         'evidence_sha256':row['sha256'], 'submitter_ref':row['submitter_ref'],
                         'integrity':'SHA256_MATCH_ONLY_NOT_ATTESTED'})
    return accepted,'INDEX_AND_ARTIFACT_BYTES_MATCH_UNVERIFIED_CONTENT'


def classify(*,prior:dict,template:dict,head:str,self_published:bool,submissions:list[dict],submission_state:str)->dict:
    blockers=[]
    if not SHA40.fullmatch(head) or self_published is not True:blockers.append('SOURCE_HEAD_NOT_EXACT_PUBLISHED')
    if (prior.get('source_head')!=FOUR_D_HEAD or prior.get('status')!='OPERATOR_EVIDENCE_SURVEY_CAPTURED_WITH_GAPS_NON_AUTHORIZING'
            or prior.get('authority_granted') is not False or prior.get('independent_dynamic_coverage_verified') is not False):
        blockers.append('FROZEN_04D_PREDECESSOR_NOT_VALID')
    rows=template.get('requirements',[])
    if not isinstance(rows,list) or len(rows)!=8:blockers.append('FROZEN_PROOF_MATRIX_INCOMPLETE')
    ids=[r['id'] for r in rows] if isinstance(rows,list) and all(isinstance(r,dict) and 'id' in r for r in rows) else []
    if len(set(ids))!=8:blockers.append('DUPLICATE_PROOF_ID')
    record={r['requirement_id']:r for r in submissions}
    if len(record)!=len(submissions) or any(x not in ids for x in record):blockers.append('SUBMISSION_SET_INVALID')
    matrix=[{'id':r['id'],'required_evidence':r['required_evidence'],
             'intake_state':'HASH_VERIFIED_CONTENT_UNREVIEWED' if r['id'] in record else 'NOT_SUBMITTED',
             'evidence_sha256':record[r['id']]['evidence_sha256'] if r['id'] in record else None,
             'evidence_reference':record[r['id']]['artifact_rel'] if r['id'] in record else None,
             'independent_verifier':'NOT_VERIFIED','attested':False} for r in rows] if len(ids)==8 else []
    state=('BLOCKED_NON_AUTHORIZING' if blockers else
           'OPERATOR_PROOF_INTAKE_INTEGRITY_REVIEW_NON_AUTHORIZING' if record else
           'OPERATOR_PROOF_INTAKE_READY_AWAITING_EXTERNAL_SUBMISSIONS_NON_AUTHORIZING')
    return {'schema_version':SCHEMA,'status':state,'blockers':sorted(set(blockers)),
        'source_head':head,'frozen_04d_head':FOUR_D_HEAD,'frozen_04d_sha256':FOUR_D_SHA,
        'submission_state':submission_state,'submission_integrity_count':len(record),
        'requirement_count':len(matrix),'matrix':matrix,
        'content_and_authenticity_independently_verified':False,
        'proofs_attested':0,'dynamic_coverage_verified':False,'complete_writer_set_proven':False,
        'all_writer_processes_enrolled':False,'drain_restart_verified':False,
        'signed_operator_decision_verified':False,'signature_cryptographically_verified':False,
        'runtime_binding_authorized':False,'make_quarantine_removed':False,
        'launch_allowed':False,'ledger_append_allowed':False,'ledger_mutated':False,
        'worker_launched':False,'authority_granted':False,'next_boundary':NEXT}


def review(root:Path,head:str,report:Path,report_sha:str,index_path:Path|None=None,index_sha:str|None=None)->dict:
    from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inv
    from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_1 as runtime
    if root!=DEPLOYMENT or root.is_symlink() or not SHA40.fullmatch(head):
        raise IntakeBlocked('CANONICAL_DEPLOYMENT_OR_HEAD_INVALID')
    before=inv.exact_published_file(root,head,SELF_REL)
    prior,template=frozen_04d(root,report,report_sha)
    evidence,state=optional_submission(root,head=head,known_ids=[x['id'] for x in template['requirements']],index_path=index_path,index_sha=index_sha)
    if inv.exact_published_file(root,head,SELF_REL)!=before or runtime.git(root,'rev-parse','HEAD')!=head:
        raise IntakeBlocked('CANONICAL_HEAD_OR_SOURCE_CHANGED_DURING_INTAKE')
    return classify(prior=prior,template=template,head=head,self_published=True,submissions=evidence,submission_state=state)


def save(root:Path,doc:dict)->tuple[Path,str]:
    scratch=root/'tmp'
    if not scratch.is_dir() or any(p.is_symlink() for p in (scratch,*scratch.parents)):
        raise IntakeBlocked('PROJECT_TMP_UNSAFE')
    output=scratch/('cf10_g2b03c04e_intake_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(mode=0o700)
    encoded=lambda x:(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
    template={'schema_version':INDEX_SCHEMA,'source_head':doc['source_head'],
              'frozen_04d_sha256':FOUR_D_SHA,'submissions':[]}
    report=encoded(doc)
    contents={'report.json':report,
              'submission_index_template.json':encoded(template),
              'summary.txt':('CF10_G2B03C04E_STATUS='+doc['status']+'\n'+
                ''.join('BLOCKER='+s+'\n' for s in doc['blockers'])+
                'SUBMISSION_INTEGRITY_COUNT='+str(doc['submission_integrity_count'])+'\n'+
                'PROOFS_ATTESTED=0\nDYNAMIC_COVERAGE_VERIFIED=false\n'
                'WORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false\n').encode()}
    contents['SHA256SUMS']=''.join(sha(blob)+'  '+name+'\n' for name,blob in sorted(contents.items())).encode()
    for name,blob in sorted(contents.items()):
        fd=os.open(output/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(blob);stream.flush();os.fsync(stream.fileno())
    return output,sha(report)


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--frozen-04d-report',type=Path,required=True)
    parser.add_argument('--frozen-04d-sha256',required=True)
    parser.add_argument('--submission-index',type=Path)
    parser.add_argument('--submission-sha256')
    args=parser.parse_args(argv)
    try:
        root=args.root.absolute()
        doc=review(root,args.expected_head,args.frozen_04d_report,args.frozen_04d_sha256,args.submission_index,args.submission_sha256)
        folder,digest=save(root,doc)
        print('CF10_G2B03C04E_STATUS='+doc['status'])
        print('SUBMISSION_INTEGRITY_COUNT='+str(doc['submission_integrity_count']))
        print('PROOF_REQUIREMENTS='+str(doc['requirement_count']))
        print('PROOFS_ATTESTED=0')
        print('REPORT_DIR='+str(folder));print('REPORT_SHA256='+digest)
        print('DYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        return 2 if doc['blockers'] else 0
    except (IntakeBlocked,ValueError,OSError,RuntimeError) as exc:
        print('CF10_G2B03C04E_STATUS=BLOCKED_NON_AUTHORIZING',file=sys.stderr)
        print('BLOCKER='+type(exc).__name__+':'+str(exc)[:180],file=sys.stderr)
        print('AUTHORITY_GRANTED=false',file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
