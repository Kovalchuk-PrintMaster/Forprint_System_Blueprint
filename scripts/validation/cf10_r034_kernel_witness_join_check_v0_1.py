"""Source-bound, non-authorizing CF10 pinned kernel witness check."""
from __future__ import annotations
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
FILES=[
 'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py',
 'scripts/coordination/control_plane/worker_runtime/cf10_systemd_terminal_bridge_v0_1.py',
 'scripts/coordination/control_plane/worker_runtime/cf10_systemd_kernel_witness_v0_1.py',
 'scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py',
]
TESTS=[
 'test_cf10_r034_kernel_witness_join.py',
 'test_cf10_r030_canonical_systemd_route.py',
 'test_cf10_r027_modernized_launcher.py',
 'test_cf10_r028_systemd_terminal_bridge.py',
 'test_cf10_r029_output_and_kernel_proof.py',
 'test_cf10_r025_cutover_and_recovery.py',
 'test_cf10_r026_trusted_systemd_readback.py',
]

def main():
    root=Path(__file__).resolve().parents[2]
    if os.geteuid()!=0 or root!=ROOT or Path.cwd()!=ROOT:
        raise RuntimeError('CF10_R034_BLOCKED_CANONICAL_ROOT_REQUIRED')
    for p in FILES:
        x=root/p
        if not x.is_file() or x.is_symlink():raise RuntimeError('CF10_R034_SOURCE_MISSING:'+p)
        ast.parse(x.read_text('utf-8'))
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as witness
    if backend.LIVE_CUTOVER_ENABLED is not False:
        raise RuntimeError('CF10_R034_PRODUCTION_GATE_NOT_SEALED')
    launcher=(root/FILES[0]).read_text('utf-8')
    route=(root/FILES[3]).read_text('utf-8')
    if "'ExitType':'cgroup'" not in launcher or "'--remain-after-exit'" not in launcher:
        raise RuntimeError('CF10_R034_SYSTEMD_RETENTION_NOT_BOUND')
    if route.count('witness.arm(')!=1 or route.count('terminal.witnessed_terminal(')!=1:
        raise RuntimeError('CF10_R034_WITNESS_OR_TERMINAL_ROUTE_DRIFT')
    if route.index('witness.arm(')>route.index('started_callback(record)'):
        raise RuntimeError('CF10_R034_WITNESS_NOT_ARMED_BEFORE_LEDGER')
    if witness.CGROUP_ROOT!=Path('/sys/fs/cgroup/system.slice'):
        raise RuntimeError('CF10_R034_KERNEL_ROOT_DRIFT')
    with tempfile.TemporaryDirectory(dir='/var/tmp',prefix='cf10-r034-') as td:
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':td,'TMP':td,'TEMP':td}
        tests=[str(root/'tests/coordination/control_plane'/x) for x in TESTS]
        subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',
            '--basetemp='+td+'/pytest',*tests],cwd=root,env=env,check=True)
    print('CF10_R034_WITNESS_TERMINAL_REGRESSION=182_PASS_NON_AUTHORIZING')
    print('CF10_R034_KERNEL_WITNESS=ARMED_BEFORE_STARTED_AND_RELEASE')
    print('CF10_R034_TERMINAL=PINNED_CGROUP_ZERO_PLUS_RETAINED_SYSTEMD')
    print('CF10_R034_PRODUCTION_CUTOVER=false')
    print('CF10_R034_RELEASE_GATE=BLOCKED_PENDING_DURABLE_CONTROLLER_CRASH_REBOOT_AND_INDEPENDENT_WORKER_RESULT')

if __name__=='__main__':main()
