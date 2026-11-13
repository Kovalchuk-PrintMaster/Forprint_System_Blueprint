"""CF-10 canonical systemd route (sealed) integration acceptance tests.

No process launch, no claim, no ledger write. Tests only. Non-authorizing.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile

TESTS=(
 'test_cf10_r025_cutover_and_recovery.py',
 'test_cf10_r027_modernized_launcher.py',
 'test_cf10_r028_systemd_terminal_bridge.py',
 'test_cf10_r029_output_and_kernel_proof.py',
 'test_cf10_r030_canonical_systemd_route.py',
)

def check():
    repo=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
    if os.geteuid()!=0 or Path.cwd()!=repo:
        raise SystemExit('CF10_R030_BLOCKED_CANONICAL_ROOT_REQUIRED')
    from scripts.coordination.control_plane import cf10_r025_canonical_seam_v0_1 as seam
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
    paths={p:(repo/p).read_bytes() for p in seam.CRITICAL}
    result=seam.review_source_shapes(paths)
    if result.get('launch_mode')!='SEALED_CANONICAL_SYSTEMD' or backend.LIVE_CUTOVER_ENABLED is not False:
        raise SystemExit('CF10_R030_BLOCKED_ROUTE_NOT_SEALED')
    tests=[repo/'tests/coordination/control_plane'/n for n in TESTS]
    if not all(p.is_file() and not p.is_symlink() for p in tests):
        raise SystemExit('CF10_R030_BLOCKED_TEST_SOURCES')
    with tempfile.TemporaryDirectory(dir='/var/tmp',prefix='cf10-r030-') as td:
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=td,TMP=td,TEMP=td)
        subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',
            '--basetemp='+td+'/pytest',*map(str,tests)],cwd=repo,env=env,check=True)
    print('CF10_R030_CANONICAL_ROUTE=SEALED_SYSTEMD_NO_POPEN_FALLBACK')
    print('CF10_R030_CUTOVER=NOT_RELEASED_NO_WORKER_LAUNCH')
    print('CF10_R030_RELEASE_GATE=BLOCKED_PENDING_REAL_GATE_AND_TERMINAL_KERNEL_PROOF')

if __name__=='__main__':check()
