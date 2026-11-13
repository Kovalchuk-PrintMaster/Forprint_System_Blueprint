"""G2b-02: bounded, read-only evidence-binding migration plan (NOT rebind).

Uses G2b-01's live read-only inventory, then inspects immutable published Git
blobs of the historically pinned Gate/Writer verifiers. Nothing is executed,
relocated, signed, copied, fetched, registered, or authorized by this review.
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

from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inventory
from scripts.coordination.control_plane import cf10_stable_release_roots_v0_1 as releases

SCHEMA='cf10_g2b02_binding_review_v0_1'
GATE_MODULE='scripts/coordination/execution_attempt_writer_coverage_v0_1.py'
WRITER_MODULE='scripts/coordination/execution_attempt_writer_activation_v0_1.py'
RUNTIME_V1='scripts/coordination/control_plane/s01_writer_runtime_binding_v0_1.py'
RUNTIME_V2='scripts/coordination/control_plane/s01_writer_runtime_binding_v0_2.py'
EXPECTED_HISTORICAL_SHA=inventory.EXPECTED_COVERAGE_SHA256
NEEDED=('canonical','make_launch_boundary','stable_gate','stable_writer','historical_coverage','g2a_vault_registration')

class ReviewBlocked(RuntimeError): pass

def verified_git_blob(root:Path,kind:str)->str:
    pin=releases.RELEASES[kind]
    src=pin['source']
    raw=releases.git(root,'show',pin['head']+':'+src)
    if releases.blob_oid(raw)!=pin['git_blob_oid']:
        raise ReviewBlocked('PINNED_BLOB_OID_DRIFT:'+kind)
    return raw.decode('utf-8','strict')

def gate_contract(source:str)->dict:
    tokens=('PLAN_MUST_BE_REGULAR_PROJECT_TMP_FILE',
            'expected_parent = (root / "tmp").resolve()',
            'file.parent.resolve() != expected_parent',
            'def verify_coverage(',
            'gate.validate_coverage(doc)')
    missing=[t for t in tokens if t not in source]
    if missing:
        return {'status':'BLOCKED','finding':'INDEPENDENT_GATE_ANCHORS_NOT_VERIFIED','missing':missing}
    return {'status':'PASS','finding':'PINNED_GATE_REQUIRES_GATE_TMP_DIRECT_CHILD','supports_stable_evidence_path':False,
            'pin_must_remain_unchanged':True}

def writer_contract(source:str)->dict:
    tokens=('def verify_signed_decision(', 'def validate_coverage(',
            'signed_decision_v0_1.json', 'writer_coverage_v0_1.json',
            "'external_approval'", 'coverage_sha256')
    missing=[t for t in tokens if t not in source]
    if missing:
        return {'status':'BLOCKED','finding':'INDEPENDENT_ACTIVATION_ANCHORS_NOT_VERIFIED','missing':missing}
    return {'status':'PASS','finding':'INDEPENDENT_SIGNED_COVERAGE_AND_ACTIVATION_REQUIRED',
            'reads_signed_payload':False,'signature_verified_by_this_plan':False}

def runtime_contract(root:Path,head:str)->dict:
    try:
        v1=inventory.exact_published_file(root,head,RUNTIME_V1)
        v2=inventory.exact_published_file(root,head,RUNTIME_V2)
    except (OSError,inventory.ReviewBlocked,UnicodeError,ValueError) as exc:
        return {'status':'BLOCKED','finding':'RUNTIME_SOURCE_NOT_VERIFIED:'+str(exc)[:140]}
    needs=('coverage_path.parent.resolve() != (gate_root / "tmp").resolve()' in v1
           and 'COVERAGE_EVIDENCE_NOT_FROM_GATE_TMP' in v1
           and 's01_writer_runtime_binding_v0_1 as inventory' in v2
           and 'SIGNED_RUNTIME_EXTENSION_MISSING' in v2)
    return {'status':'PASS' if needs else 'BLOCKED',
            'finding':'RUNTIME_V1_REQUIRES_GATE_TMP_V2_DEPENDS_ON_V1' if needs else 'RUNTIME_BINDING_CONTRACT_DRIFT',
            'supports_stable_evidence_path':False if needs else None}

def independent_sources(root:Path,head:str)->dict:
    try: gate=gate_contract(verified_git_blob(root,'gate'))
    except (OSError,UnicodeError,ValueError,releases.ReviewBlocked,ReviewBlocked) as exc:
        gate={'status':'BLOCKED','finding':'GATE_PIN_UNREADABLE:'+str(exc)[:130]}
    try: writer=writer_contract(verified_git_blob(root,'writer'))
    except (OSError,UnicodeError,ValueError,releases.ReviewBlocked,ReviewBlocked) as exc:
        writer={'status':'BLOCKED','finding':'WRITER_PIN_UNREADABLE:'+str(exc)[:130]}
    return {'gate_verifier':gate,'writer_activation':writer,'runtime_binding':runtime_contract(root,head)}

def plan_from_observations(audit:dict,source_checks:dict)->dict:
    checks={x['id']:x for x in audit['checks']}
    reasons=[]
    if audit['status']=='BLOCKED_NON_AUTHORIZING' or any(x.get('status')=='BLOCKED' for x in audit['checks']):
        reasons.append('G2B01_INVENTORY_CONFLICT')
    for key in NEEDED:
        if checks.get(key,{}).get('status')!='PASS':reasons.append('REQUIRED_G2B01_PASS_MISSING:'+key)
    if checks.get('stable_coverage_target',{}).get('status') not in ('MISSING','PASS'):
        reasons.append('STABLE_EVIDENCE_TARGET_UNEXPECTED')
    if checks.get('legacy_coverage_path_dependency',{}).get('status')!='REVIEW':
        reasons.append('LEGACY_BINDING_PROFILE_UNEXPECTED')
    if checks.get('external_signed_decision',{}).get('status')!='REVIEW':
        reasons.append('EXTERNAL_SIGNED_DECISION_REQUIRES_METADATA_REVIEW')
    for key,value in source_checks.items():
        if value.get('status')!='PASS': reasons.append('PINNED_OR_RUNTIME_SOURCE_UNVERIFIED:'+key)
    if audit.get('coverage_evidence_rebound') is not False or audit.get('new_signed_head_authorized') is not False:
        reasons.append('INVENTORY_UNEXPECTED_AUTHORITY_CLAIM')
    return {'schema_version':SCHEMA,
            'status':'BLOCKED_NON_AUTHORIZING' if reasons else 'SUCCESSOR_GATE_DESIGN_REVIEW_REQUIRED_NON_AUTHORIZING',
            'blockers':sorted(set(reasons)),
            'g2b01_status':audit['status'],
            'coverage_sha256':EXPECTED_HISTORICAL_SHA,
            'observed':{'historical_coverage':checks.get('historical_coverage'),
                        'stable_coverage_target':checks.get('stable_coverage_target'),
                        'external_signed_decision':checks.get('external_signed_decision'),
                        'pin_and_runtime_source_review':source_checks},
            'recommended_architecture':{
                'strategy':'NEW_INDEPENDENT_GATE_VERIFIER_RELEASE_REQUIRED',
                'reason':'Legacy pinned verifier and runtime binding both enforce gate_root/tmp; moving bytes alone cannot satisfy authority.',
                'immutable_original_gate_commit':releases.RELEASES['gate']['head'],
                'immutable_original_writer_commit':releases.RELEASES['writer']['head'],
                'new_coverage_store_candidate':str(inventory.STABLE_COVERAGE),
                'approved_binding':False,
                'constraints':[ 'preserve_original_historical_evidence_sha_and_path',
                 'do_not_patch_pinned_release_checkouts',
                 'propose_separately_published_successor_gate_verifier_for_immutable_external_evidence',
                 'separate_operator_review_of_external_evidence_source_provenance_and_dac',
                 'versioned_successor_s01_runtime_binding_no_legacy_tmp_condition',
                 'independent_coverage_verifier_readback_required',
                 'new_source_head_bound_independent_signed_operator_approval_required',
                 'separate_make_launch_gate_unquarantine_acceptance_required',
                 'no_automatic_deletion_or_rebind_of_old_proofs']},
            'signature_verified':False,'signature_payload_read':False,
            'independent_verifier_executed':False,'historical_evidence_copied':False,
            'vault_mutated':False,'git_mutated':False,'worker_launched':False,
            'signed_renewal_performed':False,'authority_granted':False,
            'backup_state':'PENDING_EXTERNAL_INTEGRATION',
            'next_boundary':'G2B03_INDEPENDENT_SUCCESSOR_VERIFIER_AND_OPERATOR_AUTHORITY_REVIEW'}

def safe_save(root:Path,doc:dict)->Path:
    scratch=root/'tmp'
    if scratch.is_symlink() or not scratch.is_dir() or any(p.is_symlink() for p in (scratch,*scratch.parents)):
        raise ReviewBlocked('PROJECT_SCRATCH_UNSAFE')
    out=scratch/('cf10_g2b02_plan_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(mode=0o700)
    report=(json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    summary=('CF10_G2B02_STATUS='+doc['status']+'\n'+
             '\n'.join('BLOCKER='+x for x in doc['blockers'])+'\n'+
             'GATE_SUCCESSOR_REQUIRED=true\nSIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\n'+
             'AUTHORITY_GRANTED=false\nEVIDENCE_VAULT_BACKUP=PENDING_EXTERNAL_INTEGRATION\n').encode('utf-8')
    files={'report.json':report,'summary.txt':summary}
    files['SHA256SUMS']=''.join(hashlib.sha256(raw).hexdigest()+'  '+name+'\n' for name,raw in sorted(files.items())).encode()
    for name,raw in sorted(files.items()):
        dest=out/name
        fd=os.open(dest,os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0),0o600)
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return out

def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--expected-head',required=True)
    p.add_argument('--historical-coverage',type=Path)
    p.add_argument('--no-report',action='store_true')
    a=p.parse_args(argv)
    root=a.root.absolute()
    hist=a.historical_coverage or (root/inventory.HISTORICAL_COVERAGE_REL)
    if not hist.is_absolute():
        print('CF10_G2B02=BLOCKED:HISTORICAL_PATH_ABSOLUTE_REQUIRED',file=sys.stderr);return 2
    audited=inventory.review(root,a.expected_head,hist,verify_vault=True)
    source_checks=independent_sources(root,a.expected_head)
    result=plan_from_observations(audited,source_checks)
    print('CF10_G2B02_STATUS='+result['status'])
    for k,s in source_checks.items():print('PIN_'+k.upper()+'='+s['status']+':'+s['finding'])
    for reason in result['blockers']:print('G2B02_BLOCKER='+reason)
    if not a.no_report:
        try:
            out=safe_save(root,result)
            print('REPORT_DIR='+str(out))
            print('REPORT_SHA256='+hashlib.sha256((out/'report.json').read_bytes()).hexdigest())
        except (ReviewBlocked,OSError) as e:
            print('CF10_G2B02=BLOCKED:REPORT:'+str(e)[:160],file=sys.stderr);return 2
    print('GATE_SUCCESSOR_REQUIRED=true\nHISTORICAL_EVIDENCE_COPIED=false\nSIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
    print('EVIDENCE_VAULT_BACKUP=PENDING_EXTERNAL_INTEGRATION')
    return 2 if result['blockers'] else 0

if __name__=='__main__':raise SystemExit(main())
