"""r028 completion contract check. No systemd mutation and no worker launch."""
from __future__ import annotations
import os,subprocess,sys,tempfile
from pathlib import Path

ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')

def run():
    if os.geteuid()!=0 or Path.cwd()!=ROOT:
        raise SystemExit('CF10_R028_BLOCKED_CANONICAL_ROOT_REQUIRED')
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    if launcher.LIVE_CUTOVER_ENABLED is not False:
        raise SystemExit('CF10_R028_BLOCKED_UNEXPECTED_PRODUCTION_CUTOVER')
    test=ROOT/'tests/coordination/control_plane/test_cf10_r028_systemd_terminal_bridge.py'
    if not test.is_file() or test.is_symlink():
        raise SystemExit('CF10_R028_BLOCKED_TEST_ABSENT')
    with tempfile.TemporaryDirectory(prefix='cf10-r028-test-',dir='/var/tmp') as td:
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':td,'TEMP':td,'TMP':td}
        cmd=[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',
             '--basetemp='+td+'/pytest',str(test)]
        subprocess.run(cmd,cwd=ROOT,env=env,check=True)
    subprocess.run(['make','cf10-r027-launcher-modernization-check'],cwd=ROOT,env=env,check=True)
    print('CF10_R028_TERMINAL_BRIDGE=19_PASS_NON_AUTHORIZING')
    print('CF10_R028_PRODUCTION_CUTOVER=false')
    print('CF10_R028_RELEASE_GATE=BLOCKED_PENDING_CANONICAL_RESULT_WIRING_AND_REAL_COMPLETION_READBACK')

if __name__=='__main__':run()
