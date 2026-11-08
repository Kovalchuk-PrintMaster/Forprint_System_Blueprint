"""R116 executable FD pin, offline-only. No Worker, systemd, credential or network."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import stat
import pytest

from scripts.coordination.control_plane.worker_runtime import cf10_systemd_gate_entry_v0_1 as gate
from scripts.coordination.control_plane.worker_runtime import cf10_r115_preclaim_executable_profile_v0_1 as preclaim


def write_binary(path:Path,data:bytes=b'fake ELF bytes') -> Path:
    path.write_bytes(data)
    path.chmod(0o700)
    return path


def check(path:Path,data:bytes):
    return gate._pinned_exec_fd(path,hashlib.sha256(data).hexdigest(),len(data),require_root_parents=False)


def test_pin_matches_exact_preclaim_and_is_not_authority():
    assert gate.PILOT_EXEC_PATH==preclaim.COPILOT_PILOT_PATH
    assert gate.PILOT_EXEC_SHA256==preclaim.COPILOT_PILOT_SHA256
    assert gate.PILOT_EXEC_BYTES==preclaim.COPILOT_PILOT_BYTES
    assert gate.PILOT_EXEC_PATH.is_absolute()
    assert gate.PILOT_EXEC_BYTES>200_000_000


def test_fd_is_verified_and_opened_without_executing(tmp_path):
    data=b'fixture fake binary without any executable invocation'
    path=write_binary(tmp_path/'fake',data)
    fd=check(path,data)
    try:
        assert os.fstat(fd).st_ino==path.stat().st_ino
        assert os.read(fd,len(data))==data
    finally:os.close(fd)


def test_missing_binary_fail_closed(tmp_path):
    with pytest.raises(gate.GateBlocked,match='PILOT_EXEC_UNAVAILABLE'):
        check(tmp_path/'missing',b'abc')


def test_hash_drift_fail_closed(tmp_path):
    path=write_binary(tmp_path/'exec',b'ABC')
    with pytest.raises(gate.GateBlocked,match='PILOT_EXEC_SHA256_MISMATCH'):
        check(path,b'ABD')


def test_same_hash_different_size_fail_closed(tmp_path):
    path=write_binary(tmp_path/'exec',b'ABCx')
    with pytest.raises(gate.GateBlocked,match='PILOT_EXEC_INODE_OR_MODE_DRIFT'):
        check(path,b'ABC')


def test_symlink_denied(tmp_path):
    a=write_binary(tmp_path/'file',b'ABC')
    l=tmp_path/'link';l.symlink_to(a)
    with pytest.raises(gate.GateBlocked,match='PILOT_EXEC_UNAVAILABLE'):
        check(l,b'ABC')


def test_world_writable_binary_denied(tmp_path):
    p=write_binary(tmp_path/'file',b'ABC');p.chmod(0o777)
    with pytest.raises(gate.GateBlocked,match='PILOT_EXEC_INODE_OR_MODE_DRIFT'):
        check(p,b'ABC')


def test_not_executable_denied(tmp_path):
    p=write_binary(tmp_path/'file',b'ABC');p.chmod(0o600)
    with pytest.raises(gate.GateBlocked,match='PILOT_EXEC_INODE_OR_MODE_DRIFT'):
        check(p,b'ABC')


def test_hardlink_denied(tmp_path):
    p=write_binary(tmp_path/'file',b'ABC');os.link(p,tmp_path/'second')
    with pytest.raises(gate.GateBlocked,match='PILOT_EXEC_INODE_OR_MODE_DRIFT'):
        check(p,b'ABC')


def test_fd_retains_verified_inode_when_path_is_replaced(tmp_path):
    p=write_binary(tmp_path/'file',b'GOOD')
    fd=check(p,b'GOOD')
    try:
        write_binary(tmp_path/'replacement',b'EVIL').replace(p)
        assert p.read_bytes()==b'EVIL'
        assert os.fstat(fd).st_nlink==0
        assert os.read(fd,4)==b'GOOD'
    finally:os.close(fd)


def test_executable_path_restriction_blocks_before_fd(monkeypatch):
    def never(*_args,**_kwargs):raise AssertionError('fd opened too early')
    monkeypatch.setattr(gate,'_pinned_exec_fd',never)
    with pytest.raises(gate.GateBlocked,match='PILOT_EXEC_PATH_NOT_FROZEN'):
        gate._exec_pinned_pilot(['/usr/bin/true'])


def test_actual_exec_is_fd_only_never_path(monkeypatch,tmp_path):
    p=write_binary(tmp_path/'fake',b'ORIGINAL')
    fd=check(p,b'ORIGINAL')
    monkeypatch.setattr(gate,'_pinned_exec_fd',lambda *_args,**_kwargs:fd)
    seen=[]
    def intercept(candidate,argv,env):
        seen.append((candidate,argv,env))
        assert isinstance(candidate,int) and candidate==fd
        assert os.fstat(candidate).st_size==8
        raise RuntimeError('intercepted_no_exec')
    monkeypatch.setattr(gate.os,'execve',intercept)
    monkeypatch.setattr(gate.os,'execv',lambda *_:pytest.fail('pathname exec fallback'))
    with pytest.raises(RuntimeError,match='intercepted_no_exec'):
        gate._exec_pinned_pilot([str(gate.PILOT_EXEC_PATH),'--version'])
    assert len(seen)==1
    with pytest.raises(OSError):os.fstat(fd)


def test_root_parent_scope_does_not_accept_fixture_paths(tmp_path):
    p=write_binary(tmp_path/'fixture',b'abc')
    with pytest.raises(gate.GateBlocked,match='PILOT_EXEC_SCOPE'):
        gate._pinned_exec_fd(p,hashlib.sha256(b'abc').hexdigest(),3)


def test_pin_spec_rejects_malformed_hash_before_open(tmp_path):
    p=write_binary(tmp_path/'file',b'abc')
    with pytest.raises(gate.GateBlocked,match='PIN_SPEC_INVALID'):
        gate._pinned_exec_fd(p,'short',3,require_root_parents=False)


def test_source_does_not_open_live_cutover():
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launch
    assert launch.LIVE_CUTOVER_ENABLED is False
