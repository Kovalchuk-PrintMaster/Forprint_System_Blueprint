"""CF10 r026 canonical check: non-mutating tests and real systemctl readback."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as recovery
from scripts.coordination.control_plane import cf10_r026_trusted_systemd_readback_v0_1 as rootobs

PROJECT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
HEAD='3734cb3c60b57d284264d05082e756c05481ea5e'

def check():
    if os.geteuid()!=0 or Path.cwd()!=PROJECT:
        raise SystemExit('CF10_R026_BLOCKED_ROOT_CANONICAL_REQUIRED')
    current=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    # Expected during install (before commit) only. After commit, checks remain
    # usable on a later HEAD; identity of the synthetic probe is historical.
    if not len(current)==40 or any(ch not in '0123456789abcdef' for ch in current):
        raise SystemExit('CF10_R026_BLOCKED_INVALID_HEAD')
    from scripts.coordination.control_plane.cf10_r025_canonical_seam_v0_1 import inspect_committed
    seam=inspect_committed(PROJECT,current)
    if not seam['legacy_popen_present'] or seam['worker_cutover_authorized']:
        raise SystemExit('CF10_R026_BLOCKED_SEAM_DRIFT')
    tests=PROJECT/'tests/coordination/control_plane'
    names=[
     'test_cf10_r013_cross_boundaries.py','test_cf10_r015_receipt_store.py',
     'test_cf10_r016_cross_boundary.py','test_cf10_r016_recovery_reconciliation.py',
     'test_cf10_r022_durable_readonly_boundary.py','test_cf10_supervisor_binding_candidate_v0_1.py',
     'test_cf10_untrusted_worktree_delta_v0_1.py','test_cf10_r023_guarded_transaction.py',
     'test_cf10_r024_systemd_receipt_join.py','test_cf10_r025_cutover_and_recovery.py',
     'test_cf10_r026_trusted_systemd_readback.py']
    paths=[tests/n for n in names]
    if not all(p.is_file() and not p.is_symlink() for p in paths):
        raise SystemExit('CF10_R026_BLOCKED_TEST_SOURCES')
    with tempfile.TemporaryDirectory(prefix='cf10-r026-tests-',dir='/var/tmp') as d:
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=d,TMP=d,TEMP=d)
        subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','--basetemp='+d+'/pytest',
                        *map(str,paths)],cwd=PROJECT,env=env,check=True)
    ident=recovery.identity_from_source(attempt_id='cf10-r026probe-abcdef123456-a026',
                                        head=HEAD,handoff_sha256='0'*64)
    if not (rootobs.CGROUP_ROOT==Path('/sys/fs/cgroup/system.slice')):
        raise SystemExit('CF10_R026_BLOCKED_CGROUP_LOCATION')
    # Real server systemctl readback of a synthetic NOT-PRODUCTION unit; none is started.
    observation=rootobs.collect(ident)
    if observation['systemctl']['load_state']!='not-found':
        raise SystemExit('CF10_R026_BLOCKED_PROBE_UNIT_COLLISION')
    print('CF10_R026_SYSTEMCTL_READBACK=PASS_ROOT_SIDE_NONMUTATING')
    print('CF10_R026_PROBE_UNIT='+ident.unit)
    print('CF10_R026_PRODUCTION_LAUNCH=false')
    print('CF10_R026_AUTOMATIC_RETRY=false')
    print('CF10_R026_RELEASE_GATE=BLOCKED_PENDING_LIVE_LAUNCH_AND_REBOOT_PROOF')

if __name__=='__main__':check()
