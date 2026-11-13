"""CF10 r025 read-only canonical seam and durable crash-recovery tests.

Only actual test fixtures create disposable root-owned receipts in /var/tmp.
No production process, launcher override, systemd mutation or canonical ledger edit.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile

PROJECT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
TESTS=(
 'test_cf10_r013_cross_boundaries.py',
 'test_cf10_r015_receipt_store.py',
 'test_cf10_r016_cross_boundary.py',
 'test_cf10_r016_recovery_reconciliation.py',
 'test_cf10_r022_durable_readonly_boundary.py',
 'test_cf10_supervisor_binding_candidate_v0_1.py',
 'test_cf10_untrusted_worktree_delta_v0_1.py',
 'test_cf10_r023_guarded_transaction.py',
 'test_cf10_r024_systemd_receipt_join.py',
 'test_cf10_r025_cutover_and_recovery.py',
)

def check(repo=PROJECT):
    if os.geteuid()!=0 or Path.cwd()!=repo:
        raise SystemExit('CF10_R025_BLOCKED_ROOT_CANONICAL_REQUIRED')
    from scripts.coordination.control_plane import cf10_r025_canonical_seam_v0_1 as seam
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    report=seam.inspect_committed(repo,head)
    if (report['launch_mode'] not in ('LEGACY_ROOT_INHERITED_POPEN','SEALED_CANONICAL_SYSTEMD')
            or report['worker_cutover_authorized']):
        raise SystemExit('CF10_R025_BLOCKED_UNVERIFIED_LAUNCH_SEAM')
    suite=repo/'tests/coordination/control_plane'
    paths=[suite/name for name in TESTS]
    if not all(p.is_file() and not p.is_symlink() for p in paths):
        raise SystemExit('CF10_R025_BLOCKED_TEST_SOURCE')
    with tempfile.TemporaryDirectory(prefix='cf10-r025-tests-',dir='/var/tmp') as d:
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=d,TMP=d,TEMP=d)
        cmd=[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',
             '--basetemp='+d+'/pytest',*map(str,paths)]
        rc=subprocess.run(cmd,cwd=repo,env=env,check=False).returncode
        if rc:
            raise SystemExit('CF10_R025_BLOCKED_TESTS_FAILED')
    print('CF10_R025_CANONICAL_SEAM=PASS_READ_ONLY_'+report['launch_mode'])
    print('CF10_R025_TESTS=223_PASS_NO_PROJECT_TMP')
    print('CF10_R025_PRODUCTION_CUTOVER=false')
    print('CF10_R025_REAL_SYSTEMD_SERVICE_STARTED=false')
    print('CF10_R025_RELEASE_GATE=BLOCKED_PENDING_LIVE_LAUNCH_WIRING_AND_REBOOT_PROOF')

if __name__=='__main__':check()
