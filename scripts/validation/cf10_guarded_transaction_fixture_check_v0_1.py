"""Canonical CLI for r023 isolated, non-authorizing CF10 transaction checks.

Never accesses a real Worker attempt or production root receipt store. It does
not call systemd or Git mutating commands. Uses disposable OS fixture storage,
not Blueprint tmp/. Needs root for the r022 root-owned receipt tests.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TESTS = (
    'test_cf10_r013_cross_boundaries.py',
    'test_cf10_r015_receipt_store.py',
    'test_cf10_r016_cross_boundary.py',
    'test_cf10_r016_recovery_reconciliation.py',
    'test_cf10_r022_durable_readonly_boundary.py',
    'test_cf10_supervisor_binding_candidate_v0_1.py',
    'test_cf10_untrusted_worktree_delta_v0_1.py',
    'test_cf10_r023_guarded_transaction.py',
)

def main() -> int:
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--no-project-tmp', action='store_true', required=True)
    args=p.parse_args()
    if not args.no_project_tmp: raise SystemExit('CF10_R023_TMP_GUARD_REQUIRED')
    if os.geteuid()!=0: raise SystemExit('CF10_R023_BLOCKED_ROOT_REQUIRED_FOR_RECEIPT_TESTS')
    paths=[ROOT/'tests/coordination/control_plane'/t for t in TESTS]
    if not all(t.is_file() for t in paths):
        raise SystemExit('CF10_R023_BLOCKED_TEST_SOURCE_MISSING')
    with tempfile.TemporaryDirectory(prefix='cf10-r023-os-fixtures-', dir='/var/tmp') as d:
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=d, TMP=d,TEMP=d)
        # Isolated root has NO Blueprint tmp/ directory. Only OS /var/tmp
        # disposable fixtures are allowed; no actual production replay claim.
        args=[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',
              '--basetemp='+d+'/pytest',*map(str,paths)]
        rc=subprocess.call(args,cwd=str(ROOT),env=env)
    if rc: raise SystemExit('CF10_R023_FIXTURE_TESTS_FAILED')
    print('CF10_R023_NO_PROJECT_TMP_FIXTURE=PASS_NON_AUTHORIZING')
    print('CF10_R023_PRODUCTION_LAUNCH=false')
    print('CF10_R023_RELEASE_GATE=BLOCKED_PENDING_REAL_SYSTEMD_CUTOVER_AND_RECOVERY_PROOF')
    return 0

if __name__=='__main__': raise SystemExit(main())
