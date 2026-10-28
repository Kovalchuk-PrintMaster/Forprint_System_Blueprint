"""CF10 G2b-03C/03B: independent B3 regression replay and binding design review.

Executes only existing exact-published synthetic pytest fixtures, not a Worker,
launch preflight, historical Gate/Writer activation, signing or ledger mutation.
A regression PASS is not independent production attestation or authorization.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SCHEMA = 'cf10_g2b03c03b_binding_design_review_v0_1'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
SHA64 = re.compile(r'[0-9a-f]{64}\Z')
NEXT = 'G2B03C03C_VERSIONED_RUNTIME_BINDING_SOURCE_CANDIDATE'
TESTS = (
    'tests/coordination/control_plane/test_cf10_b3_readback_selector_p0p1_v0_1.py',
    'tests/coordination/control_plane/test_cf10_b3_p2_trusted_readback_invocation_v0_1.py',
)
SOURCE_DEPS = (
    'scripts/coordination/control_plane/governed_worker_cycle.py',
    'scripts/coordination/control_plane/validation_evidence_readback_selection_v0_1.py',
    'scripts/coordination/control_plane/worker_runtime/invocation_adapter.py',
    'scripts/coordination/control_plane/cf10_training_dispatch.py',
    'scripts/coordination/control_plane/cf10_g2b03c03a_writer_delta_v0_1.py',
    'scripts/coordination/control_plane/cf10_g2b03c02_successor_gate_v0_1.py',
    'scripts/coordination/control_plane/cf10_g2b03c03b_binding_design_v0_1.py',
    'Makefile',
)
SOURCE_SET = TESTS + SOURCE_DEPS
REQUIRED_BINDING = (
    'current_canonical_head_and_published_source_bytes',
    'exact_root_owned_external_coverage_path_sha256_schema_and_release_pins',
    'versioned_runtime_binding_without_legacy_gate_root_tmp_dependency',
    'current_s01_process_dac_mount_and_writer_enrollment_independent_proof',
    'B3_P0_ACK_dispatch_digest_policy_and_prelaunch_fail_closed_readback',
    'separately_published_successor_gate_readback_and_writer_activation_verifier',
    'independent_signed_operator_decision_current_head_runtime_source_hashes_and_expiry',
    'quarantine_release_separate_explicit_operator_acceptance',
)

class DesignBlocked(RuntimeError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def classify(delta: dict, fixture: dict, published: dict, *, head: str) -> dict:
    """Never equate fixture PASS with independent runtime coverage/acceptance."""
    blockers = []
    if not SHA40.fullmatch(head) or delta.get('source_head') != head:
        blockers.append('CANONICAL_HEAD_OR_DELTA_BINDING_DRIFT')
    if (delta.get('status') != 'WRITER_DELTA_COMPATIBILITY_REVIEW_REQUIRED_NON_AUTHORIZING'
            or delta.get('blockers') != [] or delta.get('authority_granted') is not False
            or delta.get('b3_behavior_independently_verified') is not False):
        blockers.append('PRIOR_DELTA_REVIEW_UNVERIFIED')
    dr = delta.get('delta_review', {})
    if (dr.get('classification') != 'B3_INSERTION_ONLY_COMPATIBILITY_REVIEW_REQUIRED'
            or dr.get('recognized_b3_augmentation') is not True or len(dr.get('hunks', [])) != 3):
        blockers.append('B3_DELTA_PROFILE_UNEXPECTED')
    if set(published) != set(SOURCE_SET) or any(not SHA64.fullmatch(v) for v in published.values()):
        blockers.append('EXACT_PUBLISHED_TEST_AND_SOURCE_SET_NOT_VERIFIED')
    if (fixture.get('status') != 'PASS' or fixture.get('returncode') != 0
            or tuple(fixture.get('test_paths', ())) != TESTS or
            not isinstance(fixture.get('passed_count'), int) or fixture['passed_count'] < 20
            or not SHA64.fullmatch(fixture.get('stdout_sha256',''))
            or not SHA64.fullmatch(fixture.get('stderr_sha256',''))):
        blockers.append('B3_FOCUSED_REGRESSION_NOT_PROVEN')
    return {
        'schema_version': SCHEMA,
        'status': ('B3_REGRESSION_PASS_BINDING_DESIGN_REVIEW_REQUIRED_NON_AUTHORIZING'
                   if not blockers else 'BLOCKED_NON_AUTHORIZING'),
        'blockers': sorted(set(blockers)),
        'expected_head': head,
        'source_set_sha256': published,
        'preceding_writer_delta': delta.get('delta_review', {}),
        'focused_synthetic_regression': fixture,
        'required_versioned_binding': list(REQUIRED_BINDING),
        'proposed_module': 's01_writer_runtime_binding_v0_3.py',
        'legacy_gate_and_runtime_versions_mutated': False,
        'signed_approval_payload_read': False,
        'b3_synthetic_regression_passed': not blockers,
        'b3_behavior_independently_attested': False,
        'current_runtime_writer_enrollment_verified': False,
        'dynamic_coverage_verified': False,
        'successor_binding_implemented': False,
        'signed_renewal_performed': False,
        'writer_gate_unquarantined': False,
        'ledger_mutated': False,
        'worker_launched': False,
        'authority_granted': False,
        'next_boundary': NEXT,
    }


def published_set(root: Path, head: str) -> dict[str,str]:
    from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inv
    digests = {}
    for rel in SOURCE_SET:
        content = inv.exact_published_file(root, head, rel)
        digests[rel] = sha(content.encode('utf-8'))
    return digests


def create_output(root: Path) -> Path:
    scratch = root/'tmp'
    if scratch.is_symlink() or not scratch.is_dir() or any(p.is_symlink() for p in (scratch,*scratch.parents)):
        raise DesignBlocked('PROJECT_TMP_UNSAFE')
    folder = scratch/('cf10_g2b03c03b_review_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(mode=0o700)
    return folder


def write_create_only(out: Path, name: str, content: bytes) -> None:
    fd = os.open(out/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(content); stream.flush(); os.fsync(stream.fileno())


def run_fixtures(root: Path, out: Path, *, python: str = sys.executable, timeout: int = 180) -> dict:
    # The fixed published suite uses only synthetic tmp_path, monkeypatch and
    # in-process invocation planning; never asks Worker to launch.
    temp = out/'fixture_workspace'
    temp.mkdir(mode=0o700)
    env = dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
               PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONPATH=str(root), PYTEST_ADDOPTS='')
    cmd = [python, '-B', '-m', 'pytest', '-c', '/dev/null', '--noconftest',
           '-q', '-p', 'no:cacheprovider', '--tb=short',
           '--basetemp=' + str(temp), *TESTS]
    try:
        proc = subprocess.run(cmd,cwd=root,env=env,capture_output=True,
                              check=False,timeout=timeout)
        output, error, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        output, error, code = (exc.stdout or b''), (exc.stderr or b''), 124
    # Complete logs belong only in root-owned create-only project scratch.
    write_create_only(out,'fixture_stdout.txt',output[:2_000_000])
    write_create_only(out,'fixture_stderr.txt',error[:2_000_000])
    count = re.search(rb'\b(\d+) passed\b',output)
    passed = int(count.group(1)) if count else 0
    return {'status': 'PASS' if code == 0 and passed >= 20 else 'BLOCKED',
            'returncode': code,'passed_count': passed, 'test_paths':list(TESTS),
            'stdout_sha256':sha(output),'stderr_sha256':sha(error),
            'stdout_bytes':len(output),'stderr_bytes':len(error),
            'logs_truncated':len(output)>2_000_000 or len(error)>2_000_000,
            'worker_execution_started':False}


def save_report(out: Path, doc: dict) -> str:
    data=(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
    summary=(
        'CF10_G2B03C03B_STATUS='+doc['status']+'\n'
        + ''.join('BLOCKER='+b+'\n' for b in doc['blockers'])
        + 'B3_REGRESSION_PASSED='+str(doc['focused_synthetic_regression']['passed_count'])+'\n'
        + 'B3_BEHAVIOR_INDEPENDENTLY_ATTESTED=false\nDYNAMIC_COVERAGE_VERIFIED=false\n'
        + 'SIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false\n'
    ).encode('utf-8')
    write_create_only(out,'report.json',data)
    write_create_only(out,'summary.txt',summary)
    records=[]
    for name in ('report.json','summary.txt','fixture_stdout.txt','fixture_stderr.txt'):
        records.append(sha((out/name).read_bytes())+'  '+name+'\n')
    write_create_only(out,'SHA256SUMS',''.join(records).encode())
    return sha(data)


def audit(root: Path, head: str, out: Path, *, fixture_runner=run_fixtures) -> dict:
    from scripts.coordination.control_plane import cf10_g2b03c03a_writer_delta_v0_1 as delta
    if not SHA40.fullmatch(head):
        raise DesignBlocked('EXPECTED_HEAD_INVALID')
    prior=delta.audit(root,head)
    if prior.get('status')!='WRITER_DELTA_COMPATIBILITY_REVIEW_REQUIRED_NON_AUTHORIZING':
        raise DesignBlocked('PRIOR_WRITER_DELTA_NOT_READY')
    stamps=published_set(root,head)
    fixture=fixture_runner(root,out)
    # Fail on any publication drift between test execution and final classification.
    if published_set(root,head)!=stamps:
        raise DesignBlocked('PUBLISHED_SOURCE_CHANGED_DURING_FIXTURE')
    return classify(prior,fixture,stamps,head=head)


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--expected-head',required=True)
    args=p.parse_args(argv)
    try:
        root=args.root.absolute()
        if not SHA40.fullmatch(args.expected_head):
            raise DesignBlocked('EXPECTED_HEAD_INVALID')
        out=create_output(root)
        doc=audit(root,args.expected_head,out)
        digest=save_report(out,doc)
        print('CF10_G2B03C03B_STATUS='+doc['status'])
        print('B3_REGRESSION_PASSED='+str(doc['focused_synthetic_regression']['passed_count']))
        for b in doc['blockers']:print('BLOCKER='+b)
        print('REPORT_DIR='+str(out))
        print('REPORT_SHA256='+digest)
        print('B3_BEHAVIOR_INDEPENDENTLY_ATTESTED=false\nDYNAMIC_COVERAGE_VERIFIED=false\n'
              'SIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        return 2 if doc['blockers'] else 0
    except (DesignBlocked,OSError,RuntimeError,ValueError,subprocess.SubprocessError) as exc:
        print('CF10_G2B03C03B_STATUS=BLOCKED_NON_AUTHORIZING',file=sys.stderr)
        print('BLOCKER='+type(exc).__name__+':'+str(exc)[:160],file=sys.stderr)
        print('AUTHORITY_GRANTED=false',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
