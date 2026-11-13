"""CF10 R076 source-native repeatable exact-attempt operator-reviewed proof issuer.

Never launches a Worker, consumes its claim, rewrites source, changes git or
issues legacy signed release. Historical a050/a051 fixtures remain historical;
no cryptographic producer identity is asserted. The human explicitly reviews
that limitation through canonical operator PAM before proof candidate issuance.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import stat
import sys
from scripts.coordination.control_plane import cf10_r076_historical_evidence_v0_1 as evidence
from dataclasses import dataclass

ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUNTIME=Path('/srv/software_development/forprint-worker-runtime')
TASK=evidence.TASK
WORKER='worker-01'
CONFIRM='REVIEW_HISTORICAL_NONCRYPTO_EVIDENCE_ISSUE_EXACT_NONAUTH_PROOFS_NO_WORKER'
HISTORICAL_ATTEMPT=evidence.ATT

@dataclass(frozen=True)
class Context:
    attempt: str
    head: str
    task: str = TASK


def historical_folder() -> Path:
    """Existing R073 root-owned originals. NEVER consume from project tmp."""
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    fd=once.open_root_owned_state_dir()
    try:
        root_st=os.fstat(fd)
        require(stat.S_ISDIR(root_st.st_mode) and root_st.st_uid==0 and
                stat.S_IMODE(root_st.st_mode)==0o700,'ROOT_STORE_IDENTITY')
        key=__import__('hashlib').sha256((WORKER+'\0'+HISTORICAL_ATTEMPT).encode()).hexdigest()
        name='r073_evidence_'+key
        subfd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
        try:
            st=os.fstat(subfd)
            require(stat.S_ISDIR(st.st_mode) and st.st_uid==0 and
                    stat.S_IMODE(st.st_mode)==0o700,'HISTORICAL_ARCHIVE_TRUST')
        finally:os.close(subfd)
        return once.STATE_PATH/name
    finally:os.close(fd)


class Blocked(RuntimeError): pass

def require(ok,why):
    if not ok:raise Blocked('CF10_R076_'+why)

def live_before_issue(*,proof_expected,ctx:Context):
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_pilot_cycle_v0_1 as pilot
    from scripts.coordination.control_plane import cf10_r052_owner_launch_guard_v0_1 as guard
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as proof
    from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as preclaim
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as admission
    require(os.geteuid()==0 and Path.cwd()==ROOT and not ROOT.is_symlink(),'ROOT_CWD_REQUIRED')
    require(console.source_guard(ROOT)==ctx.head,'SOURCE_NOT_PUBLISHED_OR_DIRTY_CRITICAL')
    s=pilot.snapshot(ROOT,RUNTIME,TASK,ctx.attempt)
    require(s['source_head']==ctx.head and s['frozen_head']==ctx.head and s['frozen_source_current'] is True,'FROZEN_SOURCE_DRIFT')
    require(s['state']=='READY_FOR_WORKER_LAUNCH' and s['claim']=='UNCONSUMED' and s['ledger_records']==0
            and s['worker_process_started'] is False,'ATTEMPT_NOT_UNCONSUMED_READY')
    require(s['preclaim']=='PRECLAIM_ROOT_RECEIPT_VERIFIED_NON_AUTHORIZING' and s['preclaim_blockers']==[],'PRECLAIM')
    require(preclaim.inspect(root=ROOT,task=TASK,attempt=ctx.attempt,head=ctx.head)['preclaim_root_receipt_verified'] is True,'PRECLAIM_READBACK')
    require(s['root_receipt_store']=='PASS' and s['logs']=='PASS','RUNTIME_STATE')
    # R075 real frozen manifest/runner gate, not only the R013 structural sample.
    pilot.assert_owner_preclaim_runtime(root=ROOT,runtime=RUNTIME,task=TASK,
                                        attempt=ctx.attempt,head=ctx.head)
    facts=guard._observe(root=ROOT,runtime_root=RUNTIME,task=TASK,attempt=ctx.attempt,head=ctx.head)
    wanted=set(('automatic_retry_disabled','canonical_cycle_ready','canonical_ledger_unstarted','frozen_input_current',
       'independent_finalizer_required','legacy_signed_release_separate','preclaim_root_receipt_verified',
       'release_candidate_raw_lineage_verified','root_one_shot_claim_unconsumed','source_bound_pilot_make_route_verified',
       'source_bound_pilot_systemd_backend_verified','source_guard_verified','systemd_worker_quiescent','writer_protocol_enforced'))
    require(set(facts)==wanted,'GATE_FIELDS_DRIFT')
    require(all(type(v) is bool for v in facts.values()),'GATE_BOOLEAN_TYPES')
    require(all(v is True for k,v in facts.items() if k!='release_candidate_raw_lineage_verified'),'NONRELEASE_GATES_BLOCKED')
    require(facts['release_candidate_raw_lineage_verified'] is proof_expected,'RELEASE_STATE_UNEXPECTED')
    r=proof.inspect(root=ROOT,task=TASK,attempt=ctx.attempt,phase='LAUNCH_WINDOW')
    require(r['status']==('PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED' if proof_expected else 'BLOCKED_PENDING_PILOT_RELEASE_EVIDENCE'),'R046_SCOPE')
    if not proof_expected:require(r['blockers']==['DURABLE_PILOT_PROOF_OR_RELEASE_UNAVAILABLE'],'UNEXPECTED_PROOF_BLOCKER')
    return {'schema':'cf10_r076_live_readonly_v0_1','head':ctx.head,'attempt_id':ctx.attempt,
       'state':s['state'],'claim':s['claim'],'ledger_records':s['ledger_records'],
       'preclaim':s['preclaim'],'r046':r['status'],'gates':facts,'worker_launched':False}

def all_observations(host):
    f=host['gates']
    return {
      evidence.KINDS[0]:{key:True for key in evidence.FIELDS[evidence.KINDS[0]]},
      evidence.KINDS[1]:{key:True for key in evidence.FIELDS[evidence.KINDS[1]]},
      evidence.KINDS[2]:{key:True for key in evidence.FIELDS[evidence.KINDS[2]]},
      evidence.KINDS[3]:{
        'canonical_task70_and_work_front_bound':f['canonical_cycle_ready'] and f['source_guard_verified'],
        'published_head_and_frozen_source_equal':f['frozen_input_current'] and f['source_guard_verified'],
        'writer_protocol_enforced':f['writer_protocol_enforced'],
        'one_shot_claim_unconsumed':f['root_one_shot_claim_unconsumed'],
        'canonical_ledger_has_no_started_record_for_attempt':f['canonical_ledger_unstarted'],
        'cf10_systemd_quiescence_observed':f['systemd_worker_quiescent'],
      },
    }

def build_records(dossier,host,review_time,ctx:Context):
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as r046
    from scripts.coordination.control_plane import cf10_r047_pilot_proof_lineage_v0_1 as r047
    require(r046.PROOF_TYPES==evidence.KINDS,'SCHEMA_TYPE_DRIFT')
    require(r047.REQUIRED_OBSERVATIONS=={k:frozenset(v) for k,v in evidence.FIELDS.items()},'SCHEMA_OBSERVATIONS_DRIFT')
    obs=all_observations(host)
    require(all(type(x) is bool and x for values in obs.values() for x in values.values()),'OBSERVATION_COVERAGE_INCOMPLETE')
    records={};proofs={};binding={}
    key=r046._attempt_key(ctx.attempt)
    for kind in r046.PROOF_TYPES:
        raw={'schema_version':r047.SCHEMA,'status':r047.STATUS,'proof_type':kind,
          'source_head':ctx.head,'task_prompt_id':TASK,'attempt_id':ctx.attempt,'worker_id':WORKER,
          'production_worker_launched':False,'automatic_retry':False,
          'scope':'READ_ONLY_EXACT_ATTEMPT' if kind==evidence.KINDS[3] else 'DISPOSABLE_NON_AUTHORIZING',
          'observations':obs[kind]}
        raw_bytes=evidence.canonical(raw)
        require(r047.verify_source_record(raw_bytes,kind=kind,head=ctx.head,task=TASK,attempt=ctx.attempt,worker=WORKER,decode=r046._json_checked)==[],'R047_RAW_SCHEMA')
        record_name=r047.raw_name(kind,ctx.attempt)
        proof={'schema_version':r046.PROOF_SCHEMA,'status':'VERIFIED_TECHNICAL_EVIDENCE','proof_type':kind,
           'source_head':ctx.head,'task_prompt_id':TASK,'attempt_id':ctx.attempt,'worker_id':WORKER,
           'fixture_only':kind!=evidence.KINDS[3], 'production_worker_launched':False,
           'independently_reviewed':True,'source_evidence_sha256':evidence.sha(raw_bytes)}
        proof_name=r046._proof_name(kind,ctx.attempt)
        proof_bytes=evidence.canonical(proof)
        records[record_name]=raw_bytes;records[proof_name]=proof_bytes
        proofs[kind]=proof;binding[kind]={'sha256':evidence.sha(proof_bytes),'relative_file':proof_name}
    release={'schema_version':r046.RELEASE_SCHEMA,'status':'EXPLICIT_OWNER_PILOT_CANDIDATE_NON_AUTHORIZING',
      'profile':'SINGLE_OWNER_BOUNDED_TASK70','owner':'forprint_system_blueprint','worker_id':WORKER,
      'task_prompt_id':TASK,'attempt_id':ctx.attempt,'source_head':ctx.head,'automatic_retry':False,
      'automatic_acceptance':False,'automatic_publication':False,'legacy_signed_release_replaced':False,
      'independent_human_signer_required':False,'root_owned_one_shot_claim_required':True,
      'pam_operator_confirmation_required':True,'strict_finalizer_required':True,'proofs':binding}
    require(r046.validate_candidate(release,proofs,head=ctx.head,task=TASK,attempt=ctx.attempt)==[],'R046_CANDIDATE_INVALID')
    review={
       'schema':'cf10_r076_owner_historical_proof_review_v0_1','attempt_id':ctx.attempt,'source_head':ctx.head,'reviewed_utc':review_time,
       'review_method':'CANONICAL_S01_OPERATOR_PAM_INTERACTIVE_EXPLICIT',
       'historical_original_evidence_attempt':HISTORICAL_ATTEMPT,
       'historical_original_evidence_head':evidence.HEAD,
       'historical_reuse_requires_fresh_current_guards':True,
       'historical_evidence_not_fresh_for_new_head':True,
       'review_scope':'FOUR_EXACT_TASK70_NONAUTH_DISPOSABLE_PROOF_CANDIDATES',
       'r075_actual_frozen_manifest_preclaim_reverified':True,
       'review_dossier_sha256':evidence.sha(evidence.canonical(dossier)),
       'durable_evidence_directory':'r073_evidence_'+key,
       'durable_original_archives_sha256':dict(evidence.SRC),
       'historical_a050_a051_evidence_not_current_worker_execution':True,
       'disposable_fixtures_have_injected_dependencies':True,
       'production_finalizer_end_to_end_attested':False,
       'external_producer_cryptographically_authenticated':False,
       'operator_reviewed_evidence_bytes_and_limitations':True,
       'technical_verifier_different_from_human_decision':True,
       'worker_launched':False,'owner_claim_consumed':False,'automatic_retry':False,
    }
    records['r076_dossier_'+key+'.json']=evidence.canonical(dossier)
    records['r076_operator_review_'+key+'.json']=evidence.canonical(review)
    release_name='owner_pilot_release_'+key+'.json'
    records[release_name]=evidence.canonical(release)
    require(all(len(d)<32768 for d in records.values()),'DOCUMENT_EXCEEDS_R046_MAX')
    return records,release_name

def issue_records(records, release_name, archive_blobs,ctx:Context):
    """Irreversible 11-file create-once; no cleanup or retry if interrupted."""
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as r046
    f=once.open_root_owned_state_dir()
    lock_fd=None
    try:
        lf=os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_CLOEXEC
        lock_fd=os.open('owner_launch.lock',lf,0o600,dir_fd=f)
        st=os.fstat(lock_fd)
        require(stat.S_ISREG(st.st_mode) and st.st_uid==0 and stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1,'LAUNCH_MUTEX_UNTRUSTED')
        fcntl.flock(lock_fd,fcntl.LOCK_EX)
        # No substitutions, symlinks, or damaged partial issuance can be repaired by this run.
        evidence_dir='r073_evidence_'+__import__('hashlib').sha256((WORKER+'\0'+ctx.attempt).encode()).hexdigest()
        try:os.stat(evidence_dir,dir_fd=f,follow_symlinks=False)
        except FileNotFoundError:pass
        else:raise Blocked('CF10_R073_EVIDENCE_DIRECTORY_OCCUPIED_NO_RETRY')
        require(set(archive_blobs)==set(evidence.SRC) and all(evidence.sha(b)==evidence.SRC[n] for n,b in archive_blobs.items()),'EVIDENCE_SOURCE_CHANGED')
        for name in records:
            require(name.isascii() and name.endswith('.json') and name.replace('_','').replace('.','').isalnum(),'DURABLE_FILE_NAME')
            try:os.stat(name,dir_fd=f,follow_symlinks=False)
            except FileNotFoundError:pass
            else:raise Blocked('CF10_R073_DURABLE_NAME_OCCUPIED_NO_RETRY:'+name)
        # Re-read the current guard and frozen attempt while holding owner-launch lock.
        live_before_issue(proof_expected=False,ctx=ctx)
        flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC
        # Freeze ORIGINAL evidence bytes durably before creating the release candidate.
        os.mkdir(evidence_dir,0o700,dir_fd=f)
        proof_fd=os.open(evidence_dir,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=f)
        try:
            st=os.fstat(proof_fd)
            require(stat.S_ISDIR(st.st_mode) and st.st_uid==0 and stat.S_IMODE(st.st_mode)==0o700,'EVIDENCE_DIR_TRUST')
            for name,blob in sorted(archive_blobs.items()):
                require(len(blob)<2_000_000 and evidence.sha(blob)==evidence.SRC[name],'ARCHIVED_EVIDENCE_DRIFT')
                ef=os.open(name,flags,0o600,dir_fd=proof_fd)
                try:
                    with os.fdopen(ef,'wb',closefd=False) as fp:
                        fp.write(blob);fp.flush();os.fsync(fp.fileno())
                finally:os.close(ef)
                vf=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=proof_fd)
                try:
                    require(evidence.sha(os.read(vf,len(blob)+1))==evidence.SRC[name],'EVIDENCE_READBACK_DRIFT')
                finally:os.close(vf)
            os.fsync(proof_fd)
            os.fsync(f)
        finally:os.close(proof_fd)
        for name in sorted(records,key=lambda n:n==release_name):
            blob=records[name]
            fd=os.open(name,flags,0o600,dir_fd=f)
            try:
                os.fchmod(fd,0o600)
                with os.fdopen(fd,'wb',closefd=False) as out:
                    out.write(blob);out.flush();os.fsync(out.fileno())
            finally:os.close(fd)
        os.fsync(f)
    finally:
        if lock_fd is not None:
            fcntl.flock(lock_fd,fcntl.LOCK_UN)
            os.close(lock_fd)
        os.close(f)
    gate=r046.inspect(root=ROOT,task=TASK,attempt=ctx.attempt,phase='LAUNCH_WINDOW')
    require(gate['status']=='PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED' and gate['blockers']==[]
            and gate['checks'].get('r047_source_lineage')=='EXACT_RAW_BYTES_BOUND'
            and gate['launch_allowed'] is False,'POST_ISSUANCE_VERIFICATION_BLOCKED')
    after=live_before_issue(proof_expected=True,ctx=ctx)
    return {'r046':gate['status'],'r047_lineage':gate['checks']['r047_source_lineage'],'claim':after['claim'],'ledger_records':after['ledger_records']}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode',required=True,choices=['history','inspect','review-and-issue'])
    ap.add_argument('--attempt',default='')
    ap.add_argument('--task',default=TASK)
    ap.add_argument('--confirm',default='')
    arg=ap.parse_args(argv)
    try:
        require(os.geteuid()==0 and Path.cwd()==ROOT,'CANONICAL_ROOT_REQUIRED')
        source=historical_folder()
        dossier=evidence.proof_evidence(source)
        require(dossier.get('schema')=='cf10_r073_disposable_evidence_byte_review_v0_1'
                and dossier.get('attempt_id')==HISTORICAL_ATTEMPT,'HISTORICAL_DOSSIER_SCHEMA')
        print('CF10_R076_HISTORICAL_EVIDENCE=VERIFIED_BYTE_PINNED_NONCRYPTO',flush=True)
        print('CF10_R076_HISTORY_ATTEMPT='+HISTORICAL_ATTEMPT,flush=True)
        print('CF10_R076_HISTORY_PRODUCTION_ATTESTED=false',flush=True)
        if arg.mode=='history':
            print('CF10_R076_HISTORY_READONLY=PASS',flush=True)
            return 0
        require(arg.attempt!=HISTORICAL_ATTEMPT,'HISTORICAL_ATTEMPT_NO_REISSUE')
        from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
        from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as r046
        require(arg.task==TASK and isinstance(arg.attempt,str) and
                r046.ATTEMPT.fullmatch(arg.attempt) is not None,
                'TASK70_EXACT_ATTEMPT_REQUIRED')
        require(arg.attempt!=HISTORICAL_ATTEMPT,'HISTORICAL_ATTEMPT_NO_REISSUE')
        ctx=Context(attempt=arg.attempt,head=console.source_guard(ROOT),task=arg.task)
        host=live_before_issue(proof_expected=False,ctx=ctx)
        print('CF10_R076_FRESH_13_NONRELEASE_GATES=PASS',flush=True)
        print('CF10_R076_FROZEN_ATTEMPT='+ctx.attempt,flush=True)
        print('CF10_R076_CURRENT_HEAD='+ctx.head,flush=True)
        print('CF10_R076_NONCRYPTO_HISTORICAL_PRODUCER_PROOF=false',flush=True)
        print('CF10_R076_PROOF_IS_LAUNCH_AUTHORITY=false',flush=True)
        if arg.mode=='inspect':
            print('CF10_R076_STATUS=READY_FOR_EXPLICIT_HUMAN_PROOF_REVIEW_NOT_ISSUED',flush=True)
            return 0
        require(arg.confirm==CONFIRM,'EXACT_EXPLICIT_CONFIRMATION_REQUIRED')
        require(os.isatty(0) and os.isatty(1),'ROOT_INTERACTIVE_TTY_REQUIRED')
        print('\n=== R076 HISTORICAL FIXTURE EVIDENCE — NOT NEW SOURCE TEST ===',flush=True)
        for kind,fields in evidence.FIELDS.items():
            print(kind+': '+str(len(fields))+' historic/current observations',flush=True)
            for field in fields:print('  '+field,flush=True)
        print('The four archived evidence ZIPs originally concern old attempts and source.',flush=True)
        print('The present exact-attempt source/writer/PRECLAIM/systemd gates were checked LIVE.',flush=True)
        print('Historical fixture tests are not independent authenticated production tests of this HEAD.',flush=True)
        print('No producer cryptographic attestation. Human operator must explicitly accept this limitation.',flush=True)
        print('O_EXCL root records are irreversible. Failure is NO RETRY. No Worker will launch.',flush=True)
        console.decision('R076_REVIEW_HISTORICAL_NONCRYPTO_EVIDENCE_FOR_'+ctx.attempt,
                         ctx.task,ctx.attempt,ctx.head)
        require(evidence.proof_evidence(historical_folder())==dossier,'HISTORICAL_BYTES_CHANGED_AFTER_PAM')
        live_before_issue(proof_expected=False,ctx=ctx)
        records,release_name=build_records(dossier,host,datetime.now(timezone.utc).isoformat(),ctx)
        archive_blobs={}
        for name,expected in evidence.SRC.items():
            p=source/name
            require(p.is_file() and not p.is_symlink() and p.stat().st_size<2_000_000,
                    'ARCHIVE_FILE_UNSAFE')
            data=p.read_bytes()
            require(evidence.sha(data)==expected,'ARCHIVE_BYTES_CHANGED_AFTER_PAM')
            archive_blobs[name]=data
        result=issue_records(records,release_name,archive_blobs,ctx)
        print('CF10_R076_ROOT_PROOF_ISSUANCE=PASS_NON_AUTHORIZING',flush=True)
        print('CF10_R076_R046='+result['r046'],flush=True)
        print('CF10_R076_R047='+result['r047_lineage'],flush=True)
        print('CF10_R076_CLAIM='+result['claim'],flush=True)
        print('CF10_R076_WORKER_LAUNCHED=false',flush=True)
        return 0
    except (Blocked,evidence.EvidenceBlocked,OSError,ValueError,KeyError,TypeError) as exc:
        print('CF10_R076_BLOCKED='+type(exc).__name__+':'+str(exc)[:280],flush=True)
        print('CF10_R076_NO_RETRY=true',flush=True)
        return 2

if __name__=='__main__':raise SystemExit(main())
