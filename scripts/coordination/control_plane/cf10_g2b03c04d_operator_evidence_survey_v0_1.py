"""CF10 G2b-03C/04D: independent operator evidence survey, NON-AUTHORIZING.

Read-only schedule, ledger DAC/ACL/mount and process observations plus an
operator proof-intake template. They are NOT full writer enrollment, runtime
proof, independent signature verification, or authority. The existing 04C
report is authenticated with its externally recorded digest and exact path.
No /etc trust payloads, signed decision or private keys are read.
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

SCHEMA='cf10_g2b03c04d_operator_evidence_survey_v0_1'
DEPLOYMENT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
SELF_REL='scripts/coordination/control_plane/cf10_g2b03c04d_operator_evidence_survey_v0_1.py'
PRIOR_REL=Path('tmp/cf10_g2b03c04c_readback_20261028T143251400854Z/report.json')
PRIOR_SHA='9bbd7691d5e030b2b7e0991f5658a71c1933ec2b32e61653f4a92aed000a1860'
PRIOR_HEAD='0c6dfc9fe8ce614739b162a118b0802fc573a4bf'
PRIOR_B_REPORT=Path('tmp/cf10_g2b03c04b_coverage_20261028T141615684389Z/report.json')
PRIOR_B_SHA='0e786e2b98a2e632f4393150e3e8473c6062d00f6f491b7cb46fcdb2fa7c9ba2'
SHA40=re.compile(r'[0-9a-f]{40}\Z')
SHA64=re.compile(r'[0-9a-f]{64}\Z')
NEXT='G2B03C04E_INDEPENDENT_OPERATOR_PROOF_SUBMISSION_AND_VERIFIER_ACCEPTANCE_DESIGN'
SCHEDULE_PATHS=(Path('/etc/systemd/system'),Path('/etc/cron.d'),Path('/etc/crontab'))
OUT_OF_SCOPE=('forprint-google-drive-backup','forprint-website-preview')
NEEDLES=(b'governed_worker_cycle',b'execution_attempt_ledger',b'execution_attempts',b'forprint_system_blueprint',b'cf10')
MAX_FILES=2000
MAX_SINGLE=65536
MAX_TOTAL=4_000_000

class SurveyBlocked(RuntimeError):pass

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()


def load_predecessor(root:Path, path:Path, digest:str)->dict:
    """Authenticated 04C report and manifest; no alternate operator input allowed."""
    if path!=root/PRIOR_REL or digest!=PRIOR_SHA:
        raise SurveyBlocked('04C_EVIDENCE_PATH_OR_EXTERNALLY_RECORDED_SHA_MISMATCH')
    from scripts.coordination.control_plane import cf10_g2b03c04c_coverage_evidence_readback_v0_1 as old
    raw=old.private_read(path)
    if sha(raw)!=digest:raise SurveyBlocked('04C_REPORT_HASH_DRIFT')
    sums=old.private_read(path.parent/'SHA256SUMS',maximum=100000).decode('ascii')
    names={}
    for line in sums.splitlines():
        d,sep,name=line.partition('  ')
        if not sep or not SHA64.fullmatch(d) or name not in ('report.json','summary.txt') or name in names:
            raise SurveyBlocked('04C_MANIFEST_INVALID')
        names[name]=d
    if set(names)!={'report.json','summary.txt'} or names['report.json']!=digest:
        raise SurveyBlocked('04C_MANIFEST_PATHS_OR_HASH_DRIFT')
    if sha(old.private_read(path.parent/'summary.txt'))!=names['summary.txt']:
        raise SurveyBlocked('04C_SUMMARY_HASH_DRIFT')
    try:doc=json.loads(raw)
    except (ValueError,UnicodeError) as exc:raise SurveyBlocked('04C_INVALID_JSON') from exc
    if not isinstance(doc,dict):raise SurveyBlocked('04C_NOT_OBJECT')
    return doc


def validate_prior(doc:dict, requirements:tuple)->list[str]:
    errors=[]
    if (doc.get('schema_version')!='cf10_g2b03c04c_evidence_readback_v0_1' or
        doc.get('source_head')!=PRIOR_HEAD or
        doc.get('status')!='INDEPENDENT_EVIDENCE_READBACK_READY_FOR_OPERATOR_PROOFS_NON_AUTHORIZING' or
        doc.get('blockers')!=[] or doc.get('proofs_submitted')!=0 or
        doc.get('proofs_attested')!=0 or doc.get('authority_granted') is not False or
        doc.get('independent_dynamic_coverage_verified') is not False or
        doc.get('launch_allowed') is not False):
        errors.append('FROZEN_04C_PREDECESSOR_NOT_VERIFIED')
    rows=doc.get('operator_proof_intake')
    if (not isinstance(rows,list) or len(rows)!=len(requirements) or
        [r.get('id') if isinstance(r,dict) else None for r in rows]!=[r[0] for r in requirements] or
        any(not isinstance(row,dict) or row.get('state')!='NOT_SUBMITTED' or
                row.get('operator_evidence_required')!=requirements[i][1] or
                row.get('independent_evidence_id') is not None or
                row.get('evidence_sha256') is not None or
                row.get('review_authority')!='NOT_VERIFIED' for i,row in enumerate(rows))):
        errors.append('04C_OPERATOR_PROOF_MATRIX_DRIFT')
    return errors


def survey_schedule(paths:tuple[Path,...]=SCHEDULE_PATHS)->dict:
    """Bounded, no-follow, read-only schedule reference candidates; not exhaustiveness.

    Scope is deliberately narrow to prevent scanning unrelated operating data.
    Never read any file in /etc/forprint or a signed authority directory.
    """
    matches=[]; findings=[]; counts={'files_read':0,'links_skipped':0,'bytes_read':0,'out_of_scope_skipped':0}
    roots=[]
    for target in paths:
        if not target.is_absolute() or '..' in target.parts or any(p.is_symlink() for p in (target,*target.parents)):
            findings.append('UNSAFE_SCHEDULE_ROOT:'+str(target));continue
        if not target.exists():findings.append('SCHEDULE_ROOT_MISSING:'+str(target));continue
        if target.is_file(): roots.append(target)
        elif target.is_dir():
            # One level of systemd service directories (incl *.wants), no symbolic traversal.
            try:
                children=sorted(target.iterdir(),key=lambda p:p.name)
                roots.extend(children)
            except OSError:findings.append('SCHEDULE_ROOT_UNREADABLE:'+str(target))
        else:findings.append('SCHEDULE_ROOT_NOT_REGULAR:'+str(target))
    walk=[]
    for path in roots:
        try:
            st=path.lstat()
        except OSError:findings.append('SCHEDULE_ENTRY_UNREADABLE');continue
        if stat.S_ISLNK(st.st_mode):counts['links_skipped']+=1;continue
        if stat.S_ISDIR(st.st_mode):
            try: walk.extend(sorted(path.iterdir(),key=lambda p:p.name))
            except OSError:findings.append('SCHEDULE_CHILDREN_UNREADABLE:'+str(path))
        elif stat.S_ISREG(st.st_mode):walk.append(path)
    for path in sorted(walk,key=str):
        if any(key in path.name.lower() for key in OUT_OF_SCOPE):
            counts['out_of_scope_skipped']+=1;continue
        if counts['files_read']>=MAX_FILES or counts['bytes_read']>=MAX_TOTAL:
            findings.append('SCHEDULE_SURVEY_LIMIT_REACHED');break
        try:
            st=path.lstat()
            if stat.S_ISLNK(st.st_mode):counts['links_skipped']+=1;continue
            if not stat.S_ISREG(st.st_mode) or st.st_size>MAX_SINGLE or st.st_size<0:
                findings.append('SCHEDULE_FILE_UNINSPECTED:'+str(path));continue
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
            try:
                current=os.fstat(fd)
                if (current.st_dev,current.st_ino,current.st_size)!=(st.st_dev,st.st_ino,st.st_size):
                    raise OSError('schedule race')
                raw=os.read(fd,MAX_SINGLE+1)
                after=os.fstat(fd)
                if (len(raw)!=st.st_size or (current.st_mtime_ns,current.st_size)!=(after.st_mtime_ns,after.st_size)):
                    raise OSError('schedule changed')
            finally:os.close(fd)
            counts['files_read']+=1;counts['bytes_read']+=len(raw)
            lower=raw.lower()
            terms=[n.decode('ascii') for n in NEEDLES if n in lower]
            if terms:
                matches.append({'path':str(path),'sha256':sha(raw),'matching_tokens':terms,
                                'classification':'SCHEDULE_REFERENCE_CANDIDATE_NOT_WRITER_ENROLLMENT'})
        except OSError:findings.append('SCHEDULE_FILE_READ_FAILED:'+str(path))
    if counts['bytes_read']>=MAX_TOTAL and 'SCHEDULE_SURVEY_LIMIT_REACHED' not in findings:
        findings.append('SCHEDULE_SURVEY_LIMIT_REACHED')
    return {'schema_version':'cf10_schedule_reference_observation_v0_1',
            'scope':[str(x) for x in paths], 'counts':counts,
            'matches':matches,'findings':sorted(set(findings)),
            'full_scheduler_scope_proven':False,'remote_or_manual_writers_proven':False,
            'out_of_scope_services_excluded':list(OUT_OF_SCOPE),'external_authority_payloads_read':False}


def classify(*,prior:dict,head:str,requirements:tuple,schedule:dict,live:dict,source_ok:bool)->dict:
    errors=validate_prior(prior,requirements)
    if not SHA40.fullmatch(head) or source_ok is not True:errors.append('CURRENT_SOURCE_PUBLICATION_UNVERIFIED')
    if (not isinstance(schedule,dict) or schedule.get('full_scheduler_scope_proven') is not False or
        schedule.get('remote_or_manual_writers_proven') is not False or
        schedule.get('external_authority_payloads_read') is not False or
        not isinstance(schedule.get('matches'),list) or not isinstance(schedule.get('findings'),list)):
        errors.append('SCHEDULE_SURVEY_SEMANTICS_UNSAFE')
    if (not isinstance(live,dict) or live.get('processes',{}).get('state')!='OBSERVED' or
        live.get('processes',{}).get('unreadable_count')!=0 or
        live.get('processes',{}).get('absence_of_processes_proven') is not False or
        live.get('ledger',{}).get('state')!='DIRECTORY' or
        live.get('mount',{}).get('state')!='OBSERVED' or
        live.get('mount',{}).get('network_or_fuse_surface') is not False):
        errors.append('LOCAL_RUNTIME_OBSERVATION_UNRELIABLE')
    # Capture only observational facts. This is NOT an independently signed verdict.
    template={'schema_version':'cf10_g2b03c04d_operator_proof_intake_template_v0_1',
              'source_head':head,'predecessor_report_sha256':PRIOR_SHA,
              'purpose':'INDEPENDENT_OPERATOR_TO_SUBMIT_EXTERNAL_EVIDENCE_NOT_SELF_APPROVAL',
              'requirements':[{'id':item[0],'required_evidence':item[1],
                   'state':'NOT_SUBMITTED','evidence_reference':None,'evidence_sha256':None,
                   'independent_verifier_reference':None,'review_state':'NOT_VERIFIED'} for item in requirements],
              'submitted_count':0,'accepted_count':0,'authority_granted':False}
    return {'schema_version':SCHEMA,
        'status':'OPERATOR_EVIDENCE_SURVEY_CAPTURED_WITH_GAPS_NON_AUTHORIZING' if not errors else 'BLOCKED_NON_AUTHORIZING',
        'blockers':sorted(set(errors)),'source_head':head,'prior_head':PRIOR_HEAD,
        'prior_report_sha256':PRIOR_SHA,'schedule_survey':schedule,'runtime_snapshot':live,
        'proof_rows':len(requirements),'proofs_submitted':0,'proofs_attested':0,
        'proof_template':template,'full_writer_set_proven':False,
        'all_writer_processes_enrolled':False,'writer_drain_restart_verified':False,
        'independent_dynamic_coverage_verified':False,'signature_cryptographically_verified':False,
        'signed_renewal_performed':False,'runtime_binding_authorized':False,
        'make_launch_quarantine_removed':False,'launch_allowed':False,'ledger_append_allowed':False,
        'ledger_mutated':False,'worker_launched':False,'authority_granted':False,'next_boundary':NEXT}


def collect(root:Path,head:str,*,prior_report:Path,prior_sha:str)->dict:
    from scripts.coordination.control_plane import cf10_g2b03c04c_coverage_evidence_readback_v0_1 as old
    from scripts.coordination.control_plane import cf10_g2b03c04b_dynamic_coverage_proof_contract_v0_1 as proof
    from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inv
    from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_1 as runtime
    if root!=DEPLOYMENT or root.is_symlink() or not SHA40.fullmatch(head):
        raise SurveyBlocked('ROOT_OR_HEAD_UNPINNED')
    before=inv.exact_published_file(root,head,SELF_REL)
    prior=load_predecessor(root,prior_report,prior_sha)
    # Re-run exact 04C validation, including its live 04B observation.
    fresh=old.review(root,head,report=root/PRIOR_B_REPORT,report_sha=PRIOR_B_SHA)
    if fresh.get('status')!='INDEPENDENT_EVIDENCE_READBACK_READY_FOR_OPERATOR_PROOFS_NON_AUTHORIZING' or fresh.get('blockers')!=[]:
        raise SurveyBlocked('FRESH_04C_PREDECESSOR_BLOCKED')
    schedule=survey_schedule()
    canonical=root/runtime.CANONICAL_REL
    live={'processes':runtime.scan_proc(), 'ledger':runtime.path_status(canonical),
          'mount':runtime.mount_status(canonical),'acl':runtime.acl_status(canonical)}
    if inv.exact_published_file(root,head,SELF_REL)!=before or runtime.git(root,'rev-parse','HEAD')!=head:
        raise SurveyBlocked('SOURCE_CHANGED_DURING_SURVEY')
    return classify(prior=prior,head=head,requirements=proof.PROOF_REQUIREMENTS,
                    schedule=schedule,live=live,source_ok=True)


def write_new(folder:Path,name:str,raw:bytes)->None:
    fd=os.open(folder/name,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())


def save(root:Path,result:dict)->tuple[Path,str]:
    scratch=root/'tmp'
    if not scratch.is_dir() or any(p.is_symlink() for p in (scratch,*scratch.parents)):
        raise SurveyBlocked('PROJECT_TMP_UNSAFE')
    out=scratch/('cf10_g2b03c04d_survey_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(mode=0o700)
    def encode(doc):return (json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
    report=result.copy();report.pop('proof_template')
    report['proof_template_sha256']=sha(encode(result['proof_template']))
    data={'report.json':encode(report),'schedule_evidence.json':encode(result['schedule_survey']),
          'operator_proof_intake_template.json':encode(result['proof_template']),
          'summary.txt':('CF10_G2B03C04D_STATUS='+result['status']+'\n'+
               ''.join('BLOCKER='+e+'\n' for e in result['blockers'])+
               'PROOF_ROWS='+str(result['proof_rows'])+'\nPROOFS_ATTESTED=0\n'+
               'DYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\n'+
               'WORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false\n').encode()}
    data['SHA256SUMS']=''.join(sha(value)+'  '+name+'\n' for name,value in sorted(data.items())).encode()
    for name,value in sorted(data.items()):write_new(out,name,value)
    return out,sha(data['report.json'])


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--expected-head',required=True)
    p.add_argument('--frozen-04c-report',required=True,type=Path)
    p.add_argument('--frozen-04c-sha256',required=True)
    args=p.parse_args(argv)
    try:
        root=args.root.absolute()
        result=collect(root,args.expected_head,prior_report=args.frozen_04c_report,prior_sha=args.frozen_04c_sha256)
        out,digest=save(root,result)
        print('CF10_G2B03C04D_STATUS='+result['status'])
        print('SCHEDULE_REFERENCES='+str(len(result['schedule_survey']['matches'])))
        print('SCHEDULE_FILES_READ='+str(result['schedule_survey']['counts']['files_read']))
        print('OBSERVED_RECOGNIZED_PROCESSES='+str(len(result['runtime_snapshot']['processes'].get('observed',[]))))
        print('PROOF_ROWS='+str(result['proof_rows']))
        print('PROOFS_ATTESTED=0')
        for e in result['blockers']:print('BLOCKER='+e)
        print('REPORT_DIR='+str(out));print('REPORT_SHA256='+digest)
        print('DYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        return 2 if result['blockers'] else 0
    except (SurveyBlocked,OSError,ValueError,RuntimeError) as exc:
        print('CF10_G2B03C04D_STATUS=BLOCKED_NON_AUTHORIZING',file=sys.stderr)
        print('BLOCKER='+type(exc).__name__+':'+str(exc)[:180],file=sys.stderr)
        print('AUTHORITY_GRANTED=false',file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
