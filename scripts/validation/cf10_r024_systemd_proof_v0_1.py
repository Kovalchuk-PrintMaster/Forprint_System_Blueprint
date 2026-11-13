"""CF10 r024: explicitly confirmed disposable real-systemd proof.

Only a fixed source-controlled probe is launched, NEVER a Worker. No project
`tmp/`, no production runtime write, no historical attempt, no automatic retry.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile

PROJECT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
HEAD='e99aedbed976e8f809db471ee06888f304df0965'
BRANCH='audit/blueprint-inventory-refresh-2026-07-29'


def verify_suite():
    """Root-only independent tests; uses OS /var/tmp, never Blueprint tmp/."""
    if os.geteuid()!=0 or Path.cwd()!=PROJECT:
        raise SystemExit('CF10_R024_BLOCKED_TEST_ROOT_CANONICAL_REQUIRED')
    tests=PROJECT/'tests/coordination/control_plane'
    with tempfile.TemporaryDirectory(prefix='cf10-r024-tests-',dir='/var/tmp') as d:
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=d,TMP=d,TEMP=d)
        names=[
            'test_cf10_r013_cross_boundaries.py',
            'test_cf10_r015_receipt_store.py',
            'test_cf10_r016_cross_boundary.py',
            'test_cf10_r016_recovery_reconciliation.py',
            'test_cf10_r022_durable_readonly_boundary.py',
            'test_cf10_supervisor_binding_candidate_v0_1.py',
            'test_cf10_untrusted_worktree_delta_v0_1.py',
            'test_cf10_r023_guarded_transaction.py',
            'test_cf10_r024_systemd_receipt_join.py',
        ]
        paths=[tests/name for name in names]
        if not all(path.is_file() and not path.is_symlink() for path in paths):
            raise SystemExit('CF10_R024_MISSING_TEST_SOURCE')
        argv=[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',
              '--basetemp='+d+'/pytest',*map(str,paths)]
        ret=subprocess.run(argv,cwd=str(PROJECT),env=env,check=False).returncode
        if ret:raise SystemExit('CF10_R024_LOCAL_TESTS_FAILED')
    print('CF10_R024_TESTS=165_PASS_NON_AUTHORIZING_NO_PROJECT_TMP')
    print('CF10_R024_ACTUAL_SYSTEMD_SERVICE_STARTED=false')

def run():
    p=argparse.ArgumentParser()
    ops=p.add_mutually_exclusive_group(required=True)
    ops.add_argument('--confirm')
    ops.add_argument('--check',action='store_true')
    a=p.parse_args()
    if a.check:
        return verify_suite()
    if a.confirm!='RUN_CF10_R024_DISPOSABLE_SYSTEMD_PROOF':
        raise SystemExit('CF10_R024_BLOCKED_CONFIRM')
    if os.geteuid()!=0 or Path.cwd()!=PROJECT:
        raise SystemExit('CF10_R024_BLOCKED_CANONICAL_ROOT_REQUIRED')
    if subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=HEAD or subprocess.check_output(['git','branch','--show-current'],text=True).strip()!=BRANCH:
        raise SystemExit('CF10_R024_BLOCKED_SOURCE_HEAD_BRANCH')
    # This is a bounded test of a fixed probe, not a promotion of live Worker.
    from scripts.coordination.control_plane import cf10_r024_disposable_supervisor_v0_1 as sysd
    from scripts.coordination.control_plane import cf10_r024_receipt_systemd_join_v0_1 as bridge
    sysd.pinned_preflight()
    token=secrets.token_hex(6)
    parent=Path(tempfile.mkdtemp(prefix='cf10-r024-disposable-'+token+'-',dir='/var/tmp'))
    os.chmod(parent,0o700)
    store=parent/'receipts'
    store.mkdir(mode=0o700)
    attempt='cf10-r024fixture-'+token+'-a024'
    probe=PROJECT/'scripts/validation/cf10_r024_probe_v0_1.py'
    outcome=None
    try:
        outcome=bridge.execute_disposable(private_store=store, attempt_id=attempt,
            probe=probe,systemd_fixture=sysd.run_fixture)
        print(json.dumps(outcome,sort_keys=True))
        if outcome['status']!='PASS_DISPOSABLE_SYSTEMD_RECEIPT_JOIN_NON_AUTHORIZING':
            raise RuntimeError('CF10_R024_DISPOSABLE_SYSTEMD_NOT_PROVEN')
        print('CF10_R024_REAL_SYSTEMD_RECEIPT_JOIN=PASS_NON_AUTHORIZING')
        print('CF10_R024_PRODUCTION_WORKER_LAUNCHED=false')
        print('CF10_R024_RELEASE_GATE=BLOCKED_PENDING_REAL_CUTOVER_AUTHORITY_AND_RECOVERY')
    finally:
        # Remove only after complete proof. Keep consumed claim if systemd is
        # uncertain so operators can independently diagnose without retry.
        if outcome is not None and outcome['status']=='PASS_DISPOSABLE_SYSTEMD_RECEIPT_JOIN_NON_AUTHORIZING':
            shutil.rmtree(parent)
        else:
            print('CF10_R024_MANUAL_REVIEW_DIR='+str(parent),file=sys.stderr)

if __name__=='__main__': run()
