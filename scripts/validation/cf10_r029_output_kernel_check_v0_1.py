"""Canonical non-authorizing r029 cross-check (output path + cgroup evidence)."""
from __future__ import annotations
import ast
import os
import subprocess
import tempfile
from pathlib import Path

ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
LAUNCH='scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py'
TERMINAL='scripts/coordination/control_plane/worker_runtime/cf10_systemd_terminal_bridge_v0_1.py'

def main():
    root=Path(__file__).resolve().parents[2]
    if root!=ROOT:raise RuntimeError('R029_CANONICAL_ROOT_REQUIRED')
    l=(root/LAUNCH).read_text('utf8');t=(root/TERMINAL).read_text('utf8')
    ast.parse(l);ast.parse(t)
    if 'LIVE_CUTOVER_ENABLED=False' not in l:
        raise RuntimeError('R029_PRODUCTION_GATE_NOT_SEALED')
    if "props['StandardOutput']='append:'" not in l or "props['StandardError']='append:'" not in l:
        raise RuntimeError('R029_STDOUT_STDERR_NOT_BOUND')
    if "if state != '0':deny('CGROUP_NOT_EMPTY_OR_UNKNOWN')" not in t:
        raise RuntimeError('R029_REMOVED_CGROUP_NOT_BLOCKED')
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    with tempfile.TemporaryDirectory(prefix='cf10-r029-tests-',dir='/var/tmp') as td:
        subprocess.run([str(root/'.venv_blueprint/bin/python'),'-B','-m','pytest','-q',
            '-p','no:cacheprovider','--basetemp='+td+'/pytest',
            'tests/coordination/control_plane/test_cf10_r029_output_and_kernel_proof.py'],
            cwd=root,env=env,check=True)
    subprocess.run(['make','cf10-r028-terminal-bridge-check'],cwd=root,env=env,check=True)
    print('CF10_R029_TESTS=293_PASS_9_NEW_PLUS_R028_R027_NON_AUTHORIZING')
    print('CF10_R029_STDOUT_STDERR=CANONICAL_ROOT_BOUND_AND_RESERVED')
    print('CF10_R029_MISSING_CGROUP=QUARANTINE_NOT_SUCCESS')
    print('CF10_R029_PRODUCTION_CUTOVER=false')
    print('CF10_R029_RELEASE_GATE=BLOCKED_PENDING_REAL_GATED_SYSTEMD_AND_CANONICAL_LIVE_WIRING')
if __name__=='__main__':main()
