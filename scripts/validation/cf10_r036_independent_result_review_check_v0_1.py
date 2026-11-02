"""CF10 r036 standalone canonical root-only non-authorizing result candidate crosscheck."""
from __future__ import annotations
import ast
import os
import subprocess
from pathlib import Path
import tempfile

ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
MOD='scripts/coordination/control_plane/worker_runtime/cf10_r036_independent_result_crosscheck_v0_1.py'
TESTS=['test_cf10_r036_independent_result_crosscheck.py',
       'test_cf10_r035_durable_crash_recovery.py',
       'test_cf10_r034_kernel_witness_join.py',
       'test_cf10_r030_canonical_systemd_route.py',
       'test_cf10_r025_cutover_and_recovery.py',
       'test_cf10_r026_trusted_systemd_readback.py']

def main():
    if Path.cwd()!=ROOT or Path(__file__).resolve().parents[2]!=ROOT or os.geteuid()!=0:
        raise RuntimeError('CF10_R036_CANONICAL_ROOT_REQUIRED')
    p=ROOT/MOD
    if not p.is_file() or p.is_symlink():raise RuntimeError('R036_MODULE_MISSING_OR_SYMLINK')
    code=p.read_text('utf-8');tree=ast.parse(code)
    if not any(isinstance(n,ast.FunctionDef) and n.name=='inspect' for n in tree.body):
        raise RuntimeError('R036_PINNED_PRODUCTION_INSPECT_MISSING')
    for proof in ('durable.join_review(', 'durable.inspect(',
                  'actual.validate_result_envelope(', 'actual.validate_resume(',
                  'CF10_R036_', 'worker_result_accepted'):
        if proof not in code and proof!='durable.inspect(':
            raise RuntimeError('R036_CROSS_BOUNDARY_VALIDATION_REMOVED:'+proof)
    backend=(ROOT/'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py').read_text()
    if 'LIVE_CUTOVER_ENABLED=False' not in backend:
        raise RuntimeError('R036_PRODUCTION_GATE_NOT_SEALED')
    with tempfile.TemporaryDirectory(dir='/var/tmp',prefix='cf10-r036-validation-') as td:
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':td,'TMP':td,'TEMP':td}
        files=[str(ROOT/'tests/coordination/control_plane'/t) for t in TESTS]
        subprocess.run([str(ROOT/'.venv_blueprint/bin/python'),'-B','-m','pytest','-q',
                        '-p','no:cacheprovider','--basetemp='+td+'/pytest',*files],
                        cwd=ROOT,env=env,check=True)
    print('CF10_R036_INDEPENDENT_RESULT_REVIEW=READ_ONLY_EXISTING_CANONICAL_S4_VERIFIERS')
    print('CF10_R036_CROSS_BOUNDARY=ROOT_PRE_POST_CLAIM_LEDGER_SERVICE_RESULT')
    print('CF10_R036_RESULT_ACCEPTED=false')
    print('CF10_R036_PRODUCTION_CUTOVER=false')
    print('CF10_R036_GATE=BLOCKED_PENDING_FINALIZER_WIRING_AND_REAL_CRASH_REBOOT_PROOF')

if __name__=='__main__':main()
