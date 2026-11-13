"""CF-10 G2b-03C/03C: successor s01 runtime binding SOURCE CANDIDATE.

Read-only inspect and permanently blocked launch-preflight. Reuses published
successor Gate observation, Writer delta classification, and existing B3
synthetic regression evidence. Never promotes historical evidence or authorizes
runtime/ledger/Worker activity. No signed decision or secret is read here.
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

SCHEMA = 'cf10_s01_writer_runtime_binding_v0_3_candidate'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
SHA64 = re.compile(r'[0-9a-f]{64}\Z')
PREDECESSOR_HEAD = '9c314020359da15ad93392422eeb42e405b5cbb0'
EXPECTED_REPORT_SHA = '74d069eae81fea583375fede6d320b3ba23fbc337b73b03b788236a2e3dc3a3b'
REPORT_NAME = 'cf10_g2b03c03b_review_20261028T135332890726Z'
FROZEN_B3_REPORT = 'tmp/' + REPORT_NAME + '/report.json'
EXCLUDED_TESTED_SOURCE_CHANGE = {'Makefile'}
SELF_REL = 'scripts/coordination/control_plane/s01_writer_runtime_binding_v0_3.py'
NEXT = 'G2B03C04_INDEPENDENT_DYNAMIC_COVERAGE_AND_SIGNED_AUTHORITY_DESIGN'
S01_PROFILE = 'B3_PLUS_S01_FAIL_CLOSED_SOURCE_HARDENING_REVIEW_REQUIRED'
S01_DELTA_STATUS = 'S01_WRITER_HARDENING_COMPATIBILITY_REVIEW_REQUIRED_NON_AUTHORIZING'
S01_LOCK_REL = 'scripts/coordination/execution_attempt_writer_lock_v0_1.py'
S01_LOCK_SHA256 = '90ef12604e855914d3d9bb7bc04abdfb0c7515e9ffa489108cef380054f36703'
S01_PINNED_LOCK_SHA256 = '2abf27ed691c5a51235aae9874b881a6ac2aaf62d9314e32c03aafda030b7372'

class BindingBlocked(RuntimeError):
    pass


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def safe_project_read(path: Path, *, max_bytes: int = 2_000_000, allow_empty: bool = False) -> bytes:
    """Non-symlink, private, bounded named-file snapshot under root-controlled tmp."""
    if not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents)):
        raise BindingBlocked('EVIDENCE_PATH_NOT_ABSOLUTE_OR_SYMLINK')
    st = path.lstat()
    if (not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or
            stat.S_IMODE(st.st_mode) != 0o600 or st.st_nlink != 1 or
            (st.st_size == 0 and not allow_empty) or st.st_size > max_bytes):
        raise BindingBlocked('EVIDENCE_FILE_KIND_OWNER_MODE_OR_SIZE_UNSAFE')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size) != (st.st_dev, st.st_ino, st.st_size):
            raise BindingBlocked('EVIDENCE_FILE_RACE')
        buf = bytearray()
        while len(buf) <= max_bytes:
            chunk = os.read(fd, min(65536, max_bytes + 1 - len(buf)))
            if not chunk:
                break
            buf.extend(chunk)
        if len(buf) > max_bytes or len(buf) != st.st_size:
            raise BindingBlocked('EVIDENCE_FILE_SIZE_DRIFT')
        after = os.fstat(fd)
        if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns) != (
                after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
            raise BindingBlocked('EVIDENCE_FILE_CHANGED_DURING_READ')
        return bytes(buf)
    finally:
        os.close(fd)


def load_b3_report(root: Path, report: Path, expected_sha: str) -> dict:
    """Existing G2b03C03B report is historical fixture evidence, not runtime authority."""
    expected = root / FROZEN_B3_REPORT
    historical = report == expected and expected_sha == EXPECTED_REPORT_SHA
    # New S01 reports are produced only by the existing project-native 03B
    # command after the updated sources are published; never reuse a stale
    # report from the earlier B3-only HEAD as fresh S01 regression evidence.
    project_tmp = root / 'tmp'
    current_candidate = (report.parent.parent == project_tmp
        and report.parent.name.startswith('cf10_g2b03c03b_review_')
        and report.name == 'report.json' and report != expected)
    if (not SHA64.fullmatch(expected_sha) or
            not (historical or current_candidate)):
        raise BindingBlocked('B3_REPORT_EXACT_PATH_OR_EXTERNAL_DIGEST_MISMATCH')
    folder = report.parent
    if (not project_tmp.is_dir() or project_tmp.is_symlink() or
            not folder.is_dir() or folder.is_symlink() or (folder.stat().st_mode & 0o077)):
        raise BindingBlocked('B3_REPORT_DIRECTORY_UNSAFE')
    if folder.stat().st_uid != 0:
        raise BindingBlocked('B3_REPORT_DIRECTORY_OWNER_UNSAFE')
    raw = safe_project_read(report)
    if digest(raw) != expected_sha:
        raise BindingBlocked('B3_REPORT_SHA256_MISMATCH')
    entries = safe_project_read(folder / 'SHA256SUMS', max_bytes=100_000).decode('ascii')
    allow = {'report.json','summary.txt','fixture_stdout.txt','fixture_stderr.txt'}
    rows = {}
    for line in entries.splitlines():
        d,sep,name = line.partition('  ')
        if not sep or not SHA64.fullmatch(d) or name not in allow or name in rows:
            raise BindingBlocked('B3_SHA256SUMS_FORMAT_UNSAFE')
        rows[name] = d
    if set(rows) != allow or rows['report.json'] != expected_sha:
        raise BindingBlocked('B3_SHA256SUMS_FILE_SET_DRIFT')
    for name, sha in rows.items():
        if digest(safe_project_read(folder/name, allow_empty=True)) != sha:
            raise BindingBlocked('B3_LOG_OR_REPORT_HASH_DRIFT:' + name)
    try:
        doc=json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise BindingBlocked('B3_REPORT_INVALID_JSON') from exc
    if not isinstance(doc,dict):
        raise BindingBlocked('B3_REPORT_NOT_OBJECT')
    return doc


def b3_source_revalidation(root: Path, head: str, report: dict) -> dict[str,str]:
    """B3-tested source set must remain byte-identical, except new Make target."""
    from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inv
    from scripts.coordination.control_plane import cf10_g2b03c03b_binding_design_v0_1 as design
    tested = report.get('source_set_sha256')
    if (not isinstance(tested, dict) or set(tested) != set(design.SOURCE_SET) or
            any(not isinstance(v,str) or not SHA64.fullmatch(v) for v in tested.values())):
        raise BindingBlocked('B3_TESTED_SOURCE_SET_INVALID')
    actual={}
    for rel, expected in tested.items():
        data=inv.exact_published_file(root,head,rel).encode('utf-8')
        actual[rel]=digest(data)
        if rel not in EXCLUDED_TESTED_SOURCE_CHANGE and actual[rel]!=expected:
            raise BindingBlocked('B3_TESTED_SOURCE_DRIFT:'+rel)
    inv.exact_published_file(root,head,SELF_REL)
    return actual


def classify(*, head: str, live: dict, delta: dict, b3: dict,
             source_match: dict[str,str], source_hashes: dict[str,str],
             mode: str) -> dict:
    blockers=[]
    if not SHA40.fullmatch(head):
        blockers.append('INVALID_HEAD')
    if (live.get('status') != 'LIVE_OBSERVATION_REVIEW_REQUIRED_NON_AUTHORIZING' or
            live.get('source_head') != head or live.get('blockers') != [] or
            live.get('authority_granted') is not False or live.get('dynamic_coverage_verified') is not False):
        blockers.append('SUCCESSOR_GATE_OBSERVATION_NOT_VERIFIED')
    s01 = delta.get('delta_review',{}).get('classification') == S01_PROFILE
    expected_delta = S01_DELTA_STATUS if s01 else 'WRITER_DELTA_COMPATIBILITY_REVIEW_REQUIRED_NON_AUTHORIZING'
    if (delta.get('status') != expected_delta
            or delta.get('source_head') != head or delta.get('blockers') != []
            or delta.get('authority_granted') is not False
            or (s01 and (delta.get('writer_lock_review',{}).get('status') !=
                         'KNOWN_FAIL_CLOSED_LOCK_POSTIMAGE_VERIFIED_NON_AUTHORIZING'
                         or delta['writer_lock_review'].get('current_sha256') != S01_LOCK_SHA256
                         or delta['writer_lock_review'].get('pinned_sha256') != S01_PINNED_LOCK_SHA256))
            or (not s01 and delta.get('delta_review',{}).get('classification') !=
                'B3_INSERTION_ONLY_COMPATIBILITY_REVIEW_REQUIRED')):
        blockers.append('B3_WRITER_DELTA_NOT_VERIFIED')
    expected_regression_head = head if s01 else PREDECESSOR_HEAD
    if (b3.get('status') != 'B3_REGRESSION_PASS_BINDING_DESIGN_REVIEW_REQUIRED_NON_AUTHORIZING'
            or b3.get('expected_head') != expected_regression_head
            or b3.get('blockers') != []
            or b3.get('b3_behavior_independently_attested') is not False
            or b3.get('authority_granted') is not False
            or (s01 and b3.get('source_compatibility_profile') != 'S01_FAIL_CLOSED')
            or b3.get('focused_synthetic_regression', {}).get('passed_count') != 62
            or b3.get('focused_synthetic_regression', {}).get('returncode') != 0):
        blockers.append('B3_REGRESSION_EVIDENCE_NOT_ACCEPTABLE')
    if (not isinstance(source_match, dict) or not isinstance(source_hashes, dict)
            or not source_match or not source_hashes
            or any(not isinstance(s,str) or not SHA64.fullmatch(s) for s in (*source_match.values(),*source_hashes.values()))):
        blockers.append('SOURCE_DIGEST_SET_INVALID')
    live_sources=live.get('observed_s01_runtime',{}).get('writer_source_comparison',{})
    diffs = {rel for rel, equal in live_sources.items() if equal is False} if isinstance(live_sources,dict) else set()
    expected_diffs = {'scripts/coordination/control_plane/governed_worker_cycle.py', S01_LOCK_REL} if s01 else {'scripts/coordination/control_plane/governed_worker_cycle.py'}
    if diffs != expected_diffs:
        blockers.append('WRITER_DELTA_SCOPE_CHANGED')
    if mode not in ('inspect','launch-preflight'):
        blockers.append('INVALID_MODE')
    state = ('BLOCKED_NON_AUTHORIZING' if blockers else
             'VERSIONED_BINDING_CANDIDATE_REVIEW_REQUIRED_NON_AUTHORIZING')
    # Launch-preflight intentionally cannot return a positive decision in v0.3.
    if mode == 'launch-preflight':
        blockers.append('INDEPENDENT_SIGNED_RUNTIME_AND_DYNAMIC_WRITER_COVERAGE_REQUIRED')
        blockers.append('MAKE_QUARANTINE_NOT_RELEASED')
        state='BLOCKED_NON_AUTHORIZING'
    return {
        'schema_version':SCHEMA,'mode':mode,'status':state,'blockers':sorted(set(blockers)),
        'source_head':head,'b3_predecessor_head':PREDECESSOR_HEAD,
        'b3_report_sha256':EXPECTED_REPORT_SHA,
        'b3_regression_passed_count':b3.get('focused_synthetic_regression',{}).get('passed_count'),
        'gate_observation_status':live.get('status'),
        'delta_classification':delta.get('delta_review',{}).get('classification'),
        'writer_delta_review_required':True,
        'source_hashes':source_hashes,'b3_source_current_hashes':source_match,
        'runtime_observation_current':not bool(blockers) and mode=='inspect',
        'legacy_gate_tmp_dependency_removed_in_candidate':True,
        'independent_signer_approval':'NOT_VERIFIED',
        'writer_enrollment_and_drain':'NOT_VERIFIED',
        'external_coverage_immutability':'VERIFIED_BY_PREDECESSOR',
        'independent_dynamic_coverage_verified':False,
        'independent_runtime_binding_attested':False,
        'launch_allowed':False,'ledger_append_allowed':False,
        'runtime_binding_authorized':False,'writer_gate_unquarantined':False,
        'signed_renewal_performed':False,'worker_launched':False,
        'authority_granted':False,'next_boundary':NEXT,
    }


def review(root: Path, head: str, *, report: Path, report_sha: str, mode: str) -> dict:
    from scripts.coordination.control_plane import cf10_g2b03c02_successor_gate_v0_1 as gate
    from scripts.coordination.control_plane import cf10_g2b03c03a_writer_delta_v0_1 as delta_lib
    from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inv
    from scripts.coordination.control_plane import cf10_stable_release_roots_v0_1 as releases
    from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_2 as legacy
    if not SHA40.fullmatch(head) or mode not in ('inspect','launch-preflight'):
        raise BindingBlocked('INVALID_HEAD_OR_MODE')
    if root.is_symlink() or str(root) != '/srv/software_development/forprint-project/forprint_system_blueprint':
        raise BindingBlocked('CANONICAL_DEPLOYMENT_ROOT_NOT_APPROVED')
    b3=load_b3_report(root,report,report_sha)
    current_set=b3_source_revalidation(root,head,b3)
    live=gate.audit(root,head)
    current=inv.exact_published_file(root,head,delta_lib.REL).encode('utf-8')
    pin=releases.RELEASES['writer']['head']
    pinned=releases.git(root,'show',pin+':'+delta_lib.REL)
    if pinned != releases.safe_file(releases.stable_path('writer')/delta_lib.REL):
        raise BindingBlocked('PINNED_WRITER_BYTES_MISMATCH')
    # Reuse the complete published-source audit; direct classify lacks the
    # separately verified strict Writer Lock evidence required by S01.
    delta=delta_lib.audit(root,head)
    signed_sources=legacy.signed_source_digests(root) # Hash-only; no signature or decision read.
    hash_set=dict(signed_sources)
    for rel in (SELF_REL,
                'scripts/coordination/control_plane/cf10_g2b03c02_successor_gate_v0_1.py',
                'scripts/coordination/control_plane/cf10_g2b03c03a_writer_delta_v0_1.py',
                'scripts/coordination/control_plane/cf10_g2b03c03b_binding_design_v0_1.py'):
        hash_set[rel]=digest(inv.exact_published_file(root,head,rel).encode('utf-8'))
    if legacy.digest((root/'Makefile').read_bytes()) != hash_set.get('Makefile'):
        raise BindingBlocked('MAKEFILE_CHANGED_DURING_EVIDENCE_REVIEW')
    return classify(head=head,live=live,delta=delta,b3=b3,source_match=current_set,
                    source_hashes=hash_set,mode=mode)


def save_report(root:Path, result:dict) -> tuple[Path,str]:
    scratch=root/'tmp'
    if scratch.is_symlink() or not scratch.is_dir() or any(p.is_symlink() for p in (scratch,*scratch.parents)):
        raise BindingBlocked('PROJECT_SCRATCH_UNSAFE')
    folder=scratch/('cf10_g2b03c03c_runtime_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(mode=0o700)
    report=(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+'\n').encode()
    summary=('CF10_G2B03C03C_STATUS='+result['status']+'\n'
             +''.join('BLOCKER='+x+'\n' for x in result['blockers'])
             +'LAUNCH_ALLOWED=false\nDYNAMIC_COVERAGE_VERIFIED=false\n'
             +'SIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false\n').encode()
    parts={'report.json':report,'summary.txt':summary}
    parts['SHA256SUMS']=''.join(digest(data)+'  '+name+'\n' for name,data in sorted(parts.items())).encode()
    for name,data in sorted(parts.items()):
        fd=os.open(folder/name,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    return folder,digest(report)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('inspect','launch-preflight'))
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--expected-head',required=True)
    p.add_argument('--b3-report',required=True,type=Path)
    p.add_argument('--b3-sha256',required=True)
    a=p.parse_args(argv)
    try:
        result=review(a.root.absolute(),a.expected_head,report=a.b3_report,report_sha=a.b3_sha256,mode=a.mode)
        folder,sha=save_report(a.root.absolute(),result)
        print('CF10_G2B03C03C_STATUS='+result['status'])
        print('B3_REGRESSION_PASSED='+str(result['b3_regression_passed_count']))
        for x in result['blockers']:print('BLOCKER='+x)
        print('REPORT_DIR='+str(folder));print('REPORT_SHA256='+sha)
        print('LAUNCH_ALLOWED=false\nDYNAMIC_COVERAGE_VERIFIED=false\n'
              'SIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        return 0 if result['status']=='VERSIONED_BINDING_CANDIDATE_REVIEW_REQUIRED_NON_AUTHORIZING' else 2
    except (BindingBlocked,OSError,ValueError,RuntimeError) as exc:
        print('CF10_G2B03C03C_STATUS=BLOCKED_NON_AUTHORIZING',file=sys.stderr)
        print('BLOCKER='+type(exc).__name__+':'+str(exc)[:180],file=sys.stderr)
        print('AUTHORITY_GRANTED=false',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
