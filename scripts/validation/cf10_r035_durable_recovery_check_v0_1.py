"""CF10 r035 source-bound non-authorizing durable controller recovery gate."""
from __future__ import annotations
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
C='scripts/coordination/control_plane/'
B=C+'worker_runtime/'
FILES=[C+'cf10_r030_canonical_systemd_route_v0_1.py',
 B+'cf10_r035_durable_witness_boundary_v0_1.py',
 B+'cf10_systemd_kernel_witness_v0_1.py',
 B+'cf10_systemd_terminal_bridge_v0_1.py',
 B+'cf10_systemd_launcher_v0_1.py']
TESTS=['test_cf10_r035_durable_crash_recovery.py',
       'test_cf10_r034_kernel_witness_join.py',
       'test_cf10_r030_canonical_systemd_route.py',
       'test_cf10_r025_cutover_and_recovery.py',
       'test_cf10_r026_trusted_systemd_readback.py']

def main():
    root=Path(__file__).resolve().parents[2]
    if root!=ROOT or Path.cwd()!=ROOT or os.geteuid()!=0:
        raise RuntimeError('CF10_R035_CANONICAL_ROOT_REQUIRED')
    for p in FILES:
        path=root/p
        if not path.is_file() or path.is_symlink():
            raise RuntimeError('CF10_R035_SOURCE_MISSING:'+p)
        ast.parse(path.read_text('utf-8'))
    route=(root/FILES[0]).read_text('utf-8')
    backend=(root/FILES[-1]).read_text('utf-8')
    if 'LIVE_CUTOVER_ENABLED=False' not in backend or '--remain-after-exit' not in backend:
        raise RuntimeError('CF10_R035_LIVE_GATE_OR_SYSTEMD_RETENTION_DRIFT')
    if route.count('durable.record_pre(')!=1 or route.count('durable.record_terminal(')!=1:
        raise RuntimeError('CF10_R035_DURABLE_ROUTE_COUNT')
    if not (route.index('witness.arm(')<route.index('durable.record_pre(')<route.index('started_callback(record)')):
        raise RuntimeError('CF10_R035_PRE_RECORD_NOT_BEFORE_STARTED')
    if not route.index('terminal.witnessed_terminal(')<route.index('durable.record_terminal('):
        raise RuntimeError('CF10_R035_TERMINAL_NOT_RECORDED')
    with tempfile.TemporaryDirectory(dir='/var/tmp',prefix='cf10-r035-validation-') as td:
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':td,'TMP':td,'TEMP':td}
        paths=[str(root/'tests/coordination/control_plane'/x) for x in TESTS]
        subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',
                        '--basetemp='+td+'/pytest',*paths],cwd=root,env=env,check=True)
    print('CF10_R035_DURABLE_BOUNDARY=PRE_START_AND_POST_TERMINAL_ROOT_0600_FSYNC_OEXCL')
    print('CF10_R035_CRASH_REBOOT_REVIEW=FAIL_CLOSED_NO_AUTO_RETRY')
    print('CF10_R035_INDEPENDENT_WORKER_RESULT=NOT_YET_ACCEPTED')
    print('CF10_R035_PRODUCTION_CUTOVER=false')
    print('CF10_R035_RELEASE_GATE=BLOCKED_PENDING_INDEPENDENT_RESULT_AND_RECOVERY_RELEASE_REVIEW')

if __name__=='__main__':main()
