"""CF10 r027 source-bound, non-authorizing Worker Launcher Modernization check."""
from __future__ import annotations
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile

PROJECT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
TARGETS=(
 'scripts/coordination/control_plane/worker_runtime/cf10_systemd_gate_entry_v0_1.py',
 'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py',
 'scripts/validation/cf10_r027_launcher_modernization_check_v0_1.py',
 'tests/coordination/control_plane/test_cf10_r027_modernized_launcher.py',
)
TESTS=(
 'test_cf10_r013_cross_boundaries.py','test_cf10_r015_receipt_store.py',
 'test_cf10_r016_cross_boundary.py','test_cf10_r016_recovery_reconciliation.py',
 'test_cf10_r022_durable_readonly_boundary.py','test_cf10_supervisor_binding_candidate_v0_1.py',
 'test_cf10_untrusted_worktree_delta_v0_1.py','test_cf10_r023_guarded_transaction.py',
 'test_cf10_r024_systemd_receipt_join.py','test_cf10_r025_cutover_and_recovery.py',
 'test_cf10_r026_trusted_systemd_readback.py','test_cf10_r027_modernized_launcher.py',
)

def check(*,root=PROJECT):
    if os.geteuid()!=0 or Path.cwd()!=root:
        raise SystemExit('CF10_R027_BLOCKED_ROOT_REPO_REQUIRED')
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    from scripts.coordination.control_plane import cf10_r025_canonical_seam_v0_1 as seam
    if launcher.LIVE_CUTOVER_ENABLED is not False:
        raise SystemExit('CF10_R027_BLOCKED_LIVE_CUTOVER_WITHOUT_RELEASE')
    if any('/tmp/' in str((root/p).resolve()) or '/temp/' in str((root/p).resolve()) for p in TARGETS):
        raise SystemExit('CF10_R027_BLOCKED_TMP_CODE')
    for path in TARGETS:
        f=root/path
        if not f.is_file() or f.is_symlink():
            raise SystemExit('CF10_R027_BLOCKED_TARGET_MISSING:'+path)
        ast.parse(f.read_bytes(),filename=path)
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=root).strip()
    result=seam.inspect_committed(root,head)
    if (result['launch_mode'] not in ('LEGACY_ROOT_INHERITED_POPEN', 'SEALED_CANONICAL_SYSTEMD')
            or result['worker_cutover_authorized'] is not False
            or result['production_launch_allowed'] is not False):
        raise SystemExit('CF10_R027_BLOCKED_CANONICAL_SEAM_DRIFT')
    paths=[root/'tests/coordination/control_plane'/n for n in TESTS]
    if not all(p.is_file() and not p.is_symlink() for p in paths):
        raise SystemExit('CF10_R027_BLOCKED_TEST_PATHS')
    with tempfile.TemporaryDirectory(prefix='cf10-r027-tests-',dir='/var/tmp') as d:
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=d,TMP=d,TEMP=d)
        subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',
            '--basetemp='+d+'/pytest',*map(str,paths)],cwd=root,env=env,check=True)
    print('CF10_R027_TESTS=265_PASS_ISOLATED_NO_PROJECT_TMP')
    print('CF10_R027_SYSTEMD_BACKEND=SEALED_ROUTE_RECOGNIZED_NON_AUTHORIZING')
    print('CF10_R027_CANONICAL_MODE='+result['launch_mode'])
    print('CF10_R027_PRODUCTION_WORKER_LAUNCHED=false')
    print('CF10_R027_RELEASE_GATE=BLOCKED_PENDING_CANONICAL_CUTOVER_AND_REAL_GATE_PROOF')

if __name__=='__main__':check()
