"""CF-10 G2b-03A: read-only candidate successor provenance verifier.

This checks immutable historical coverage and the fixed prospective external
location; it never copies, signs, verifies current deployment coverage, executes
pinned Gate/Writer verifiers, or grants runtime/ledger/Worker authority.
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

from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inv
from scripts.coordination.control_plane import cf10_g2b02_binding_plan_v0_1 as plan

SCHEMA = 'cf10_g2b03_successor_provenance_v0_1'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
MAX_COVERAGE = inv.MAX_COVERAGE
CANDIDATE = inv.STABLE_COVERAGE
NEXT = 'G2B03B_INDEPENDENT_DYNAMIC_COVERAGE_VERIFIER_AND_RUNTIME_BINDING_REVIEW'

class EvidenceBlocked(RuntimeError):
    pass


def reject_symlinks(path: Path) -> None:
    if not path.is_absolute() or '..' in path.parts:
        raise EvidenceBlocked('ABSOLUTE_CANONICAL_PATH_REQUIRED')
    for part in (path, *path.parents):
        if part.is_symlink():
            raise EvidenceBlocked('SYMLINK_IN_EVIDENCE_PATH:' + str(part))


def read_candidate(path: Path, *, strict_owner: bool = True) -> bytes:
    """Exact approved external path; one bounded, nofollow, root-controlled read."""
    if path != CANDIDATE:
        raise EvidenceBlocked('CANDIDATE_PATH_NOT_APPROVED')
    reject_symlinks(path)
    if not path.exists():
        raise EvidenceBlocked('CANDIDATE_ABSENT')
    if not path.parent.is_dir():
        raise EvidenceBlocked('CANDIDATE_PARENT_NOT_DIRECTORY')
    for part in (path.parent, *tuple(path.parent.parents)):
        st = part.stat()
        if not stat.S_ISDIR(st.st_mode) or (st.st_mode & 0o022):
            raise EvidenceBlocked('CANDIDATE_PARENT_WRITABLE_BY_OTHERS:' + str(part))
        if strict_owner and st.st_uid != 0:
            raise EvidenceBlocked('CANDIDATE_PARENT_NOT_ROOT_OWNED:' + str(part))
    st = path.lstat()
    if (not stat.S_ISREG(st.st_mode) or st.st_size > MAX_COVERAGE or
            st.st_size == 0 or stat.S_IMODE(st.st_mode) != 0o600 or st.st_nlink != 1 or
            (strict_owner and st.st_uid != 0)):
        raise EvidenceBlocked('CANDIDATE_FILE_KIND_MODE_OWNER_OR_SIZE_UNSAFE')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        cur = os.fstat(fd)
        if (st.st_ino, st.st_dev, st.st_size) != (cur.st_ino, cur.st_dev, cur.st_size):
            raise EvidenceBlocked('CANDIDATE_RACE_DETECTED')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(MAX_COVERAGE + 1)
    finally:
        os.close(fd)
    if len(data) > MAX_COVERAGE or len(data) != st.st_size:
        raise EvidenceBlocked('CANDIDATE_SIZE_DRIFT')
    return data


def candidate_probe(path: Path = CANDIDATE, *, strict_owner: bool = True) -> dict:
    """Cannot emit PASS if immutable SHA and schema/profile/pins are not proven."""
    if path != CANDIDATE:
        return {'status': 'BLOCKED', 'reason': 'CANDIDATE_PATH_NOT_APPROVED'}
    try:
        reject_symlinks(path)
        if not path.exists():
            return {'status': 'MISSING', 'reason': 'ROOT_CONTROLLED_EXTERNAL_EVIDENCE_NOT_PROVISIONED'}
        raw = read_candidate(path, strict_owner=strict_owner)
        actual = hashlib.sha256(raw).hexdigest()
        if actual != inv.EXPECTED_COVERAGE_SHA256:
            return {'status': 'BLOCKED', 'reason': 'EXTERNAL_EVIDENCE_SHA256_MISMATCH', 'actual_sha256': actual}
        original_probe = inv.coverage_probe(path, 'successor_candidate')
        if original_probe['status'] != 'PASS':
            return {'status': 'BLOCKED', 'reason': 'EXTERNAL_EVIDENCE_PROFILE_NOT_VERIFIED',
                    'detail': original_probe['detail']}
        return {'status': 'PASS', 'reason': 'EXACT_ROOT_CONTROLLED_COVERAGE_BYTES_AND_PINS',
                'sha256': actual, 'path': str(path), 'authority_granted': False}
    except (OSError, ValueError, TypeError, EvidenceBlocked) as exc:
        return {'status': 'BLOCKED', 'reason': type(exc).__name__ + ':' + str(exc)[:180]}


def evaluate(*, prior_plan: dict, provenance: dict, history: dict) -> dict:
    """Combine independently observed facts; no authorization on any outcome."""
    blockers = []
    if prior_plan.get('status') != 'SUCCESSOR_GATE_DESIGN_REVIEW_REQUIRED_NON_AUTHORIZING' or prior_plan.get('blockers') != []:
        blockers.append('PREREQUISITE_G2B02_PLAN_NOT_VALID')
    if history.get('status') != 'PASS' or history.get('sha256') != inv.EXPECTED_COVERAGE_SHA256:
        blockers.append('HISTORICAL_COVERAGE_UNVERIFIED')
    status = provenance.get('status')
    if status == 'BLOCKED':
        blockers.append('EXTERNAL_CANDIDATE_CONFLICT')
    if status not in ('PASS','MISSING','BLOCKED'):
        blockers.append('EXTERNAL_CANDIDATE_STATE_INVALID')
    if status == 'PASS' and provenance.get('sha256') != history.get('sha256'):
        blockers.append('EXTERNAL_AND_ORIGINAL_SHA_MISMATCH')
    state = ('BLOCKED_NON_AUTHORIZING' if blockers else
             'EXTERNAL_CANDIDATE_MISSING_NON_AUTHORIZING' if status == 'MISSING' else
             'PROVENANCE_CANDIDATE_VERIFIED_NON_AUTHORIZING')
    return {'schema_version': SCHEMA, 'state': state, 'blockers': sorted(set(blockers)),
            'original_coverage_sha256': inv.EXPECTED_COVERAGE_SHA256,
            'original_historical_check': history, 'external_candidate_check': provenance,
            'g2b02_planning_state': prior_plan.get('status'),
            'successor_dynamic_coverage_verified': False,
            'independent_gate_verifier_accepted': False,
            'signed_operator_approval_verified': False,
            'external_evidence_rebound': False,
            'historical_evidence_copied': False,
            'independent_gate_or_writer_executed': False,
            'worker_launched': False, 'ledger_mutated': False,
            'authority_granted': False, 'backup_state': 'PENDING_EXTERNAL_INTEGRATION',
            'next_boundary': NEXT}


def audit(root: Path, expected: str, historical: Path) -> dict:
    inv_doc = inv.review(root, expected, historical, verify_vault=True)
    source_checks = plan.independent_sources(root, expected)
    prior = plan.plan_from_observations(inv_doc, source_checks)
    orig = next((x for x in inv_doc['checks'] if x['id'] == 'historical_coverage'), {})
    hist = {'status': orig.get('status', 'MISSING'), 'sha256': orig.get('sha256'),
            'detail': orig.get('detail', 'UNKNOWN')}
    return evaluate(prior_plan=prior, provenance=candidate_probe(), history=hist)


def write_report(root: Path, doc: dict) -> Path:
    scratch = root/'tmp'
    reject_symlinks(scratch)
    if not scratch.is_dir():
        raise EvidenceBlocked('PROJECT_SCRATCH_UNAVAILABLE')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = scratch/('cf10_g2b03a_provenance_'+stamp)
    out.mkdir(mode=0o700)
    report = (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False)+'\n').encode()
    summary = (f'CF10_G2B03A_STATUS={doc["state"]}\n'
        f'EXTERNAL_CANDIDATE={doc["external_candidate_check"]["status"]}\n'
        'DYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\n'
        'WORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false\n'
        'EVIDENCE_VAULT_BACKUP=PENDING_EXTERNAL_INTEGRATION\n').encode()
    contents = {'report.json': report, 'summary.txt': summary}
    contents['SHA256SUMS'] = ''.join(hashlib.sha256(v).hexdigest()+'  '+k+'\n' for k,v in sorted(contents.items())).encode()
    for name, raw in sorted(contents.items()):
        path = out/name
        fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0), 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
    return out


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--expected-head',required=True)
    p.add_argument('--historical-coverage',type=Path)
    p.add_argument('--no-report',action='store_true')
    args=p.parse_args(argv)
    root=args.root.absolute()
    historical=args.historical_coverage or root/inv.HISTORICAL_COVERAGE_REL
    if not SHA40.fullmatch(args.expected_head) or not historical.is_absolute():
        print('CF10_G2B03A=BLOCKED:ABSOLUTE_HISTORICAL_PATH_AND_SHA40_REQUIRED',file=sys.stderr)
        return 2
    try:
        result=audit(root,args.expected_head,historical)
        print('CF10_G2B03A_STATUS='+result['state'])
        print('HISTORICAL_COVERAGE='+result['original_historical_check']['status'])
        print('EXTERNAL_CANDIDATE='+result['external_candidate_check']['status']+':'+result['external_candidate_check']['reason'])
        for reason in result['blockers']:print('BLOCKER='+reason)
        if not args.no_report:
            dest=write_report(root,result)
            print('REPORT_DIR='+str(dest))
            print('REPORT_SHA256='+hashlib.sha256((dest/'report.json').read_bytes()).hexdigest())
        print('DYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        print('EVIDENCE_VAULT_BACKUP=PENDING_EXTERNAL_INTEGRATION')
        return 2 if result['blockers'] else 0
    except (OSError,ValueError,EvidenceBlocked) as exc:
        print('CF10_G2B03A=BLOCKED:'+type(exc).__name__+':'+str(exc)[:200],file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
