"""CF10 G2b-03C/03A: compare current governed Worker cycle with pinned Writer.

Observational compatibility evidence only. An insertion-only B3 delta is never an
approval of those additions, a runtime binding, an attestation, or an authority.
Historical Git and release files are read, never modified. No signing or launch.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

SCHEMA = 'cf10_g2b03c03a_writer_delta_review_v0_1'
REL = 'scripts/coordination/control_plane/governed_worker_cycle.py'
SHA40 = re.compile(r'[a-f0-9]{40}\Z')
NEXT = 'G2B03C03B_VERSIONED_RUNTIME_BINDING_DESIGN_REVIEW'

class DeltaBlocked(RuntimeError):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def compare_published_sources(current: bytes, pinned: bytes) -> dict:
    """Conservatively classify *only* the known three insertion sites.

    This does not establish B3 functional correctness: even a recognized delta
    requires independent test/provenance and operator review before attestation.
    """
    try:
        a, b = pinned.decode('utf-8', 'strict').splitlines(keepends=True), current.decode('utf-8', 'strict').splitlines(keepends=True)
    except UnicodeError as exc:
        raise DeltaBlocked('WRITER_SOURCE_NON_UTF8') from exc
    opcodes = difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes()
    changes = []
    for tag, i, j, k, l in opcodes:
        if tag == 'equal':
            continue
        snippet = ''.join(b[k:l])
        changes.append({'kind':tag, 'old_lines':j-i, 'new_lines':l-k, 'added_sha256':digest(snippet.encode()),
                        'new_start_line':k+1, 'text':snippet})
    if not changes:
        return {'classification':'EXACT_PINNED_BYTES', 'hunks':[], 'recognized_b3_augmentation':False}
    recognized = (len(changes) == 3 and all(x['kind']=='insert' for x in changes)
                  and '# CF10_B3_P2_INDEPENDENT_PRELAUNCH_READBACK_V0_1_START' in changes[0]['text']
                  and '# CF10_B3_P2_INDEPENDENT_PRELAUNCH_READBACK_V0_1_END' in changes[0]['text']
                  and 'def _resolve_b3_trusted_readback(' in changes[0]['text']
                  and 'training.readback.verify_frozen_selection(' in changes[0]['text']
                  and 'trusted_readback_selection = _resolve_b3_trusted_readback(' in changes[1]['text']
                  and 'expected_attempt_id=attempt_id,' in changes[1]['text']
                  and '"validation_readback_selection": trusted_readback_selection,' in changes[2]['text']
                  and 45 <= changes[0]['new_lines'] <= 70
                  and 5 <= changes[1]['new_lines'] <= 15
                  and changes[2]['new_lines'] == 1)
    classification = 'B3_INSERTION_ONLY_COMPATIBILITY_REVIEW_REQUIRED' if recognized else 'UNEXPECTED_WRITER_DELTA_BLOCKED'
    # No source text exported (only line positions and hashes).
    for c in changes:
        del c['text']
    return {'classification':classification,'recognized_b3_augmentation':recognized,'hunks':changes,
            'new_total_lines':len(b),'pinned_total_lines':len(a)}


def classify(live: dict, delta: dict, *, head: str, current_sha: str, pinned_sha: str) -> dict:
    blockers = []
    findings = []
    if not SHA40.fullmatch(head) or live.get('source_head') != head:
        blockers.append('CURRENT_HEAD_NOT_VERIFIED')
    if live.get('status') != 'LIVE_OBSERVATION_REVIEW_REQUIRED_NON_AUTHORIZING' or live.get('blockers') != []:
        blockers.append('G2B03C02_LIVE_GATE_NOT_READY_FOR_REVIEW')
    if live.get('authority_granted') is not False or live.get('dynamic_coverage_verified') is not False:
        blockers.append('PRIOR_FALSE_AUTHORITY_CLAIM')
    runtime = live.get('observed_s01_runtime', {})
    tracked = runtime.get('tracked_writers')
    compared = runtime.get('writer_source_comparison')
    if not isinstance(tracked,list) or not isinstance(compared,dict) or set(tracked) != set(compared):
        blockers.append('TRACKED_WRITER_INVENTORY_UNVERIFIED')
    elif set(rel for rel,eq in compared.items() if eq is False) != {REL} or any(x is None for x in compared.values()):
        blockers.append('WRITER_DIFF_SCOPE_NOT_EXACTLY_GOVERNED_CYCLE')
    if not isinstance(delta,dict) or delta.get('classification') != 'B3_INSERTION_ONLY_COMPATIBILITY_REVIEW_REQUIRED':
        blockers.append('WRITER_DELTA_NOT_RECOGNIZED_AS_B3_ONLY')
    else:
        findings.append('B3_ADDED_PRELAUNCH_BEHAVIOR_REQUIRES_INDEPENDENT_REVIEW')
    if not re.fullmatch(r'[a-f0-9]{64}',current_sha) or not re.fullmatch(r'[a-f0-9]{64}',pinned_sha):
        blockers.append('SOURCE_DIGEST_NOT_VERIFIED')
    status = 'WRITER_DELTA_COMPATIBILITY_REVIEW_REQUIRED_NON_AUTHORIZING' if not blockers else 'BLOCKED_NON_AUTHORIZING'
    return {
        'schema_version':SCHEMA,'status':status,'blockers':sorted(set(blockers)),
        'findings':sorted(set(findings)), 'source_head':head,'tracked_writer':REL,
        'current_published_sha256':current_sha,'historical_pinned_sha256':pinned_sha,
        'delta_review':delta,
        'operator_acceptance':'NOT_PERFORMED',
        'b3_behavior_independently_verified':False,
        'current_runtime_coverage_verified':False,
        'successor_versioned_binding_implemented':False,
        'independent_attestation_verified':False,
        'signed_decision_read_or_renewed':False,
        'writer_gate_unquarantined':False,
        'worker_launched':False,'ledger_mutated':False,
        'authority_granted':False,'next_boundary':NEXT,
    }


def audit(root: Path, head: str) -> dict:
    from scripts.coordination.control_plane import cf10_g2b03c02_successor_gate_v0_1 as gate
    from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inv
    from scripts.coordination.control_plane import cf10_stable_release_roots_v0_1 as releases
    if not SHA40.fullmatch(head):
        raise DeltaBlocked('EXPECTED_HEAD_INVALID')
    live = gate.audit(root,head)
    current = inv.exact_published_file(root,head,REL).encode('utf-8')
    pinned_commit = releases.RELEASES['writer']['head']
    pinned = releases.git(root,'show',pinned_commit+':'+REL)
    release_root = releases.stable_path('writer')
    release_file = releases.safe_file(release_root/REL)
    if pinned != release_file:
        raise DeltaBlocked('PINNED_RELEASE_SOURCE_NOT_EQUAL_GIT')
    compared = compare_published_sources(current,pinned)
    return classify(live,compared,head=head,current_sha=digest(current),pinned_sha=digest(pinned))


def write_report(root: Path, result: dict) -> tuple[Path,str]:
    scratch=root/'tmp'
    if (scratch.is_symlink() or not scratch.is_dir() or any(p.is_symlink() for p in (scratch,*scratch.parents))):
        raise DeltaBlocked('PROJECT_TMP_UNSAFE')
    folder=scratch/('cf10_g2b03c03a_delta_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(mode=0o700)
    report=(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
    summary=('CF10_G2B03C03A_STATUS='+result['status']+'\n'
             + ''.join('BLOCKER='+b+'\n' for b in result['blockers'])
             + ''.join('FINDING='+b+'\n' for b in result['findings'])
             + 'DYNAMIC_COVERAGE_VERIFIED=false\nAUTHORITY_GRANTED=false\nWORKER_LAUNCHED=false\n').encode()
    files={'report.json':report,'summary.txt':summary}
    files['SHA256SUMS']=''.join(digest(raw)+'  '+name+'\n' for name,raw in sorted(files.items())).encode()
    for name,raw in sorted(files.items()):
        fd=os.open(folder/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return folder,digest(report)


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--expected-head',required=True)
    p.add_argument('--no-report',action='store_true')
    args=p.parse_args(argv)
    try:
        result=audit(args.root.absolute(),args.expected_head)
        print('CF10_G2B03C03A_STATUS='+result['status'])
        print('DELTA_CLASSIFICATION='+result['delta_review'].get('classification','UNKNOWN'))
        for msg in result['blockers']:print('BLOCKER='+msg)
        for msg in result['findings']:print('FINDING='+msg)
        if not args.no_report:
            folder,sha=write_report(args.root.absolute(),result)
            print('REPORT_DIR='+str(folder))
            print('REPORT_SHA256='+sha)
        print('B3_BEHAVIOR_INDEPENDENTLY_VERIFIED=false\nDYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        return 2 if result['blockers'] else 0
    except (DeltaBlocked,OSError,ValueError,RuntimeError) as exc:
        print('CF10_G2B03C03A_STATUS=BLOCKED_NON_AUTHORIZING',file=sys.stderr)
        print('BLOCKER='+str(exc)[:180],file=sys.stderr)
        print('AUTHORITY_GRANTED=false',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
