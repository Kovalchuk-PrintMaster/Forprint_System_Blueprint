"""CF10 G2b-03C/04B: read-only independent dynamic Writer coverage PROOF CONTRACT.

Reuses 04A preflight, publication and secure metadata checks. Adds a bounded
published-source AST candidate map and a fresh /proc observation. Neither is
complete enrollment, drain/restart, cryptographic attestation, or authority.
External /etc authority payloads are NEVER opened, read, parsed, or signed.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

SCHEMA = 'cf10_g2b03c04b_dynamic_coverage_proof_contract_v0_1'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
SHA64 = re.compile(r'[0-9a-f]{64}\Z')
DEPLOYMENT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
SELF_REL = 'scripts/coordination/control_plane/cf10_g2b03c04b_dynamic_coverage_proof_contract_v0_1.py'
B3_REPORT_REL = 'tmp/cf10_g2b03c03b_review_20261028T135332890726Z/report.json'
B3_SHA256 = '74d069eae81fea583375fede6d320b3ba23fbc337b73b03b788236a2e3dc3a3b'
NEXT = 'G2B03C04C_INDEPENDENT_DYNAMIC_WRITER_COVERAGE_VERIFIER_AND_ATTESTATION_REVIEW'
MAX_NODES = 60000
MAX_CANDIDATES = 250
TRUST_FILES = ('trust_root_v0_1.json','writer_coverage_v0_1.json','signed_decision_v0_1.json','protocol_candidate_v0_1.yaml')

PROOF_REQUIREMENTS = (
    ('COMPLETE_CURRENT_WRITER_ENTRYPOINTS', 'independent source/entrypoint inventory, dynamic imports and indirect callbacks'),
    ('ALL_WRITER_PROCESSES_ENROLLED', 'enumeration of running and short-lived writers with enrollment mapping'),
    ('RUNNING_WRITER_RESTART_OR_DRAIN', 'operator-verified process drain/restart evidence bound to a freeze boundary'),
    ('SCHEDULED_MANUAL_REMOTE_WRITERS', 'systemd, timers, Make/CLI, containers, other hosts, mounts and SSH write paths'),
    ('CANONICAL_LOCK_AND_LEDGER_EXCLUSIVITY', 'DAC, ACL, mount and writer-lock enforcement across every writer path'),
    ('INDEPENDENT_DYNAMIC_PROOF', 'separately published successor verifier and independently checked observations'),
    ('SIGNED_COVERAGE_APPROVAL', 'signed current HEAD, source digests, coverage digest, nonce, expiry and review reference'),
    ('RUNTIME_BINDING_AND_QUARANTINE_ACCEPTANCE', 'separate signed v0.3+ binding, explicit operator release of Make quarantine'),
)

class ProofContractBlocked(RuntimeError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def static_append_candidates(sources: dict[str,str]) -> dict:
    """Conservative AST call candidates, NEVER exhaustive or writer-authoritative."""
    if not isinstance(sources,dict) or not sources:
        raise ProofContractBlocked('STATIC_SOURCES_MISSING')
    items=[]
    hashes={}
    for rel, text in sorted(sources.items()):
        if not isinstance(rel,str) or not rel.startswith('scripts/coordination/') or not isinstance(text,str):
            raise ProofContractBlocked('STATIC_SOURCE_UNEXPECTED')
        raw=text.encode('utf-8')
        if len(raw)>2_000_000:
            raise ProofContractBlocked('STATIC_SOURCE_OVERSIZE')
        hashes[rel]=sha(raw)
        try:
            tree=ast.parse(text, filename=rel)
        except (SyntaxError,UnicodeError,RecursionError) as exc:
            raise ProofContractBlocked('STATIC_PARSE_FAILED:'+rel) from exc
        nodes=list(ast.walk(tree))
        if len(nodes)>MAX_NODES:
            raise ProofContractBlocked('STATIC_AST_LIMIT:'+rel)
        for node in nodes:
            if not isinstance(node,ast.Call):
                continue
            fn=node.func
            if (isinstance(fn,ast.Attribute) and fn.attr=='append_record') or (isinstance(fn,ast.Name) and fn.id=='append_record'):
                items.append({'file':rel,'line':node.lineno,'classification':'STATIC_APPEND_CALL_CANDIDATE_NOT_AUTHORITY'})
                if len(items)>MAX_CANDIDATES:
                    raise ProofContractBlocked('STATIC_CANDIDATE_LIMIT')
    return {'scan_method':'AST_BOUNDED_NON_EXHAUSTIVE', 'source_sha256':hashes,
            'candidates':sorted(items,key=lambda x:(x['file'],x['line'])),
            'dynamic_imports_and_callbacks_proven':False,
            'full_writer_set_proven':False}


def classify(*, prior:dict, head:str, process:dict, static:dict, tracked:tuple[str,...],
             self_published:bool) -> dict:
    """Pure classifier: PASS is approval of the PROOF CONTRACT, not coverage."""
    blockers=[]
    findings=[]
    if not SHA40.fullmatch(head) or prior.get('canonical_head')!=head:
        blockers.append('SOURCE_HEAD_NOT_BOUND')
    if (prior.get('status')!='ATTESTATION_BOUNDARY_GAPS_RECORDED_NON_AUTHORIZING'
        or prior.get('blockers')!=[] or prior.get('authority_granted') is not False
        or prior.get('independent_dynamic_coverage_verified') is not False
        or prior.get('signature_cryptographically_verified') is not False
        or prior.get('launch_allowed') is not False):
        blockers.append('G2B03C04A_METADATA_BOUNDARY_NOT_VERIFIED')
    if self_published is not True:
        blockers.append('PROOF_SOURCE_NOT_EXACT_PUBLISHED')
    external=prior.get('external_authority_metadata_only',{})
    files=external.get('files',{}) if isinstance(external,dict) else {}
    expected=set(TRUST_FILES)
    if not isinstance(files,dict) or set(files)!=expected:
        blockers.append('EXTERNAL_TRUST_INVENTORY_DRIFT')
    else:
        for name in sorted(files):
            state=files[name].get('status') if isinstance(files[name],dict) else 'UNSAFE'
            if state=='MISSING':
                findings.append('EXTERNAL_EVIDENCE_MISSING:'+name)
            elif state!='METADATA_PRESENT_NON_ATTESTING':
                blockers.append('EXTERNAL_FILE_UNSAFE_OR_UNKNOWN:'+name)
    if (external.get('external_file_content_read') is not False or
        external.get('signature_verified') is not False or
        external.get('coverage_attested') is not False):
        blockers.append('FALSE_EXTERNAL_AUTHORITY_CLAIM')
    if (not isinstance(process,dict) or process.get('state')!='OBSERVED'
        or process.get('unreadable_count')!=0 or not isinstance(process.get('observed'),list)
        or process.get('absence_of_processes_proven') is not False):
        blockers.append('PROCESS_SNAPSHOT_NOT_RELIABLE_FOR_OBSERVATION')
    if (not isinstance(static,dict) or static.get('scan_method')!='AST_BOUNDED_NON_EXHAUSTIVE'
        or not isinstance(static.get('candidates'),list) or not isinstance(static.get('source_sha256'),dict)
        or set(static.get('source_sha256',{}))!=set(tracked)
        or any(not isinstance(d,str) or not SHA64.fullmatch(d) for d in static.get('source_sha256',{}).values())
        or static.get('full_writer_set_proven') is not False
        or static.get('dynamic_imports_and_callbacks_proven') is not False):
        blockers.append('STATIC_CANDIDATE_SOURCE_PROFILE_INVALID')
    # Even an empty /proc list cannot prove no writers: always require independent proof.
    rows=[{'id':k,'status':'NOT_ATTESTED','required_evidence':v} for k,v in PROOF_REQUIREMENTS]
    state=('BLOCKED_NON_AUTHORIZING' if blockers else
           'DYNAMIC_COVERAGE_PROOF_CONTRACT_MAPPED_NON_AUTHORIZING')
    return {'schema_version':SCHEMA,'status':state,'blockers':sorted(set(blockers)),
            'findings':sorted(set(findings)),'source_head':head,
            'source_attestation':'EXACT_PUBLISHED_BYTES_VERIFIED' if self_published else 'NOT_VERIFIED',
            'predecessor_state':prior.get('status'),'external_trust_metadata_only':external,
            'static_inventory':static,'process_observation':{
                'state':process.get('state') if isinstance(process,dict) else 'UNAVAILABLE',
                'observed_recognized_count':len(process.get('observed',[])) if isinstance(process,dict) and isinstance(process.get('observed'),list) else None,
                'unreadable_count':process.get('unreadable_count') if isinstance(process,dict) else None,
                'all_writers_enrolled_proven':False,
                'absence_of_writers_proven':False,
                'scan_is_complete_dynamic_attestation':False},
            'proof_requirements':rows,'proof_requirements_satisfied':0,
            'independent_dynamic_coverage_verified':False,
            'external_signature_read':False,'signature_verified':False,
            'all_writer_entrypoints_verified':False,'all_writer_processes_enrolled':False,
            'running_writer_drain_or_restart_verified':False,
            'successor_gate_independently_accepted':False,
            'runtime_binding_authorized':False,'make_quarantine_removed':False,
            'launch_allowed':False,'ledger_append_allowed':False,
            'worker_launched':False,'ledger_mutated':False,
            'authority_granted':False,'next_boundary':NEXT}


def review(root:Path,head:str,*,b3_report:Path,b3_sha256:str)->dict:
    from scripts.coordination.control_plane import cf10_g2b03c04a_attestation_boundary_v0_1 as previous
    from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inventory
    from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_1 as runtime
    if root!=DEPLOYMENT or root.is_symlink() or not SHA40.fullmatch(head):
        raise ProofContractBlocked('DEPLOYMENT_OR_HEAD_NOT_PINNED')
    if b3_report!=root/B3_REPORT_REL or b3_sha256!=B3_SHA256:
        raise ProofContractBlocked('B3_REPORT_PIN_MISMATCH')
    published=inventory.exact_published_file(root,head,SELF_REL)
    if 'launch_allowed' not in published or 'NOT_ATTESTED' not in published:
        raise ProofContractBlocked('PUBLISHED_PROOF_SOURCE_ANCHORS_UNVERIFIED')
    prior=previous.review(root,head,b3_report=b3_report,b3_sha256=b3_sha256)
    texts={rel:inventory.exact_published_file(root,head,rel) for rel in runtime.TRACKED_WRITERS}
    static=static_append_candidates(texts)
    process=runtime.scan_proc()  # observed PIDs and known labels only, no argv exported.
    # Re-verify publication and the canonical HEAD after observational calls.
    if inventory.exact_published_file(root,head,SELF_REL)!=published or runtime.git(root,'rev-parse','HEAD')!=head:
        raise ProofContractBlocked('SOURCE_CHANGED_DURING_OBSERVATION')
    return classify(prior=prior,head=head,process=process,static=static,
                    tracked=tuple(runtime.TRACKED_WRITERS),self_published=True)


def save_report(root:Path, doc:dict)->tuple[Path,str]:
    scratch=root/'tmp'
    if not scratch.is_dir() or any(x.is_symlink() for x in (scratch,*scratch.parents)):
        raise ProofContractBlocked('PROJECT_TMP_UNSAFE')
    out=scratch/('cf10_g2b03c04b_coverage_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(mode=0o700)
    report=(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    summary=('CF10_G2B03C04B_STATUS='+doc['status']+'\n'+
        ''.join('BLOCKER='+s+'\n' for s in doc['blockers'])+
        ''.join('FINDING='+s+'\n' for s in doc['findings'])+
        'PROOF_REQUIREMENTS_SATISFIED=0\nDYNAMIC_COVERAGE_VERIFIED=false\n'+
        'SIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false\n').encode()
    files={'report.json':report,'summary.txt':summary}
    files['SHA256SUMS']=''.join(sha(data)+'  '+name+'\n' for name,data in sorted(files.items())).encode()
    for name,data in sorted(files.items()):
        fd=os.open(out/name,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
    return out,sha(report)


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--expected-head',required=True)
    p.add_argument('--b3-report',required=True,type=Path)
    p.add_argument('--b3-sha256',required=True)
    args=p.parse_args(argv)
    try:
        doc=review(args.root.absolute(),args.expected_head,b3_report=args.b3_report,b3_sha256=args.b3_sha256)
        out,digest=save_report(args.root.absolute(),doc)
        print('CF10_G2B03C04B_STATUS='+doc['status'])
        print('STATIC_APPEND_CANDIDATES='+str(len(doc['static_inventory']['candidates'])))
        print('OBSERVED_RECOGNIZED_PROCESSES='+str(doc['process_observation']['observed_recognized_count']))
        print('PROOF_REQUIREMENTS_SATISFIED=0')
        for finding in doc['findings']: print('FINDING='+finding)
        for blocker in doc['blockers']: print('BLOCKER='+blocker)
        print('REPORT_DIR='+str(out));print('REPORT_SHA256='+digest)
        print('DYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        return 2 if doc['blockers'] else 0
    except (ProofContractBlocked,OSError,ValueError,RuntimeError) as exc:
        print('CF10_G2B03C04B_STATUS=BLOCKED_NON_AUTHORIZING',file=sys.stderr)
        print('BLOCKER='+type(exc).__name__+':'+str(exc)[:180],file=sys.stderr)
        print('AUTHORITY_GRANTED=false',file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
