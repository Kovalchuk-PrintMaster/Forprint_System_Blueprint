"""CF10 r037 canonical finalizer cross-boundary preterminal gate, non-authorizing."""
from __future__ import annotations
import ast
import os
from pathlib import Path
import subprocess
import tempfile

ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
SEAM='scripts/coordination/control_plane/governed_worker_cycle.py'
MODULE='scripts/coordination/control_plane/cf10_r037_finalizer_boundary_v0_1.py'
TESTS=[
 'test_cf10_r037_finalizer_boundary.py',
 'test_cf10_r036_independent_result_crosscheck.py',
 'test_cf10_r035_durable_crash_recovery.py',
 'test_cf10_r034_kernel_witness_join.py',
 'test_cf10_r030_canonical_systemd_route.py',
 'test_cf10_r025_cutover_and_recovery.py',
 'test_cf10_r026_trusted_systemd_readback.py',
]

def main():
    if Path.cwd()!=ROOT or Path(__file__).resolve().parents[2]!=ROOT or os.geteuid()!=0:
        raise RuntimeError('CF10_R037_ROOT_REQUIRED')
    source=(ROOT/SEAM).read_text('utf-8')
    guard=(ROOT/MODULE).read_text('utf-8')
    route=(ROOT/'scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py').read_text('utf-8')
    tree=ast.parse(source)
    ast.parse(guard)
    if 'LIVE_CUTOVER_ENABLED=False' not in (ROOT/'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py').read_text('utf-8'):
        raise RuntimeError('CF10_R037_PRODUCTION_SEAL_REMOVED')
    if source.count('R037_INDEPENDENT_RESULT_GUARD:')!=1:
        raise RuntimeError('CF10_R037_FINALIZER_GUARD_MISSING_OR_DUPLICATED')
    if source.index('R037_INDEPENDENT_RESULT_GUARD:')>=source.index('finalize_cf10_workspace_result_artifact('):
        raise RuntimeError('CF10_R037_GUARD_TOO_LATE')
    if "if not terminal_already_present:\n            from scripts.coordination.control_plane import cf10_r037_finalizer_boundary_v0_1" not in source:
        raise RuntimeError('CF10_R037_REPLAY_IDEMPOTENCE_DRIFT')
    if route.index('durable.record_terminal(spec=spec,unit=unit,outcome=outcome)')>=route.index('_retire_after_durable_terminal(unit)',route.index('durable.record_terminal(spec=spec,unit=unit,outcome=outcome)')):
        raise RuntimeError('CF10_R037_PREMATURE_SYSTEMD_STOP')
    for literal in ('recovery.read_root_claim(', 'trusted.collect(', 'crosscheck.inspect(',
                    "deny('LIVE_CGROUP_NOT_TERMINAL')", "'worker_result_accepted':False"):
        if literal not in guard:
            raise RuntimeError('CF10_R037_CRITICAL_PROOF_REMOVED:'+literal)
    with tempfile.TemporaryDirectory(dir='/var/tmp',prefix='cf10-r037-validation-') as td:
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':td,'TMP':td,'TEMP':td}
        files=[str(ROOT/'tests/coordination/control_plane'/t) for t in TESTS]
        subprocess.run([str(ROOT/'.venv_blueprint/bin/python'),'-B','-m','pytest','-q',
            '-p','no:cacheprovider','--basetemp='+td+'/pytest',*files],
            cwd=ROOT,env=env,check=True)
    print('CF10_R037_FINALIZER_GATE=INDEPENDENT_CROSS_BOUNDARY_BEFORE_TERMINAL_LEDGER')
    print('CF10_R037_REPLAY=IMMUTABLE_TERMINAL_NO_REFINALIZATION')
    print('CF10_R037_TESTS=201_PASS_NON_AUTHORIZING')
    print('CF10_R037_WORKER_RESULT_ACCEPTED=false')
    print('CF10_R037_PRODUCTION_CUTOVER=false')

if __name__=='__main__':main()
