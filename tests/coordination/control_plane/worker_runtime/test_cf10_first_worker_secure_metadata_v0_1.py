"""CF10 AA: do not open credential files or follow attacker-owned ancestors."""
from __future__ import annotations
from pathlib import Path
import os
import tempfile
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_first_worker_secure_metadata_v0_1 as m
from scripts.coordination.control_plane.worker_runtime import cf10_first_worker_operator_doctor_v0_1 as doctor
from scripts.coordination.control_plane.worker_runtime import cf10_r115_preclaim_executable_profile_v0_1 as r115

ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')

@pytest.mark.parametrize('path',[
    'relative','/tmp/x','/var/tmp/x','/run/x','/dev/x','/proc/x','/sys/x',
    '/root/../etc/x','/root/./x','/root/x\n','/root/x\\name',
    '/srv/software_development/forprint-project/forprint_system_blueprint/secret',
])
def test_banned_scope(path):
    with pytest.raises(m.MetadataHold):m.inspect_credential_metadata(Path(path),project_root=ROOT)

def test_none_is_unconfigured():
    row=m.inspect_credential_metadata(None,project_root=ROOT)
    assert row['source']=='UNCONFIGURED' and row['material_read'] is False
    assert m.source_check()['g1_g5_open'] is True

@pytest.fixture
def root_handle():
    if os.geteuid()!=0:
        pytest.skip('root-only inode test')
    with tempfile.TemporaryDirectory(prefix='cf10-aa-',dir='/root') as base:
        root=Path(base);root.chmod(0o700)
        p=root/'token.bin';p.write_bytes(b'SYNTHETIC_NOT_A_REAL_TOKEN')
        p.chmod(0o600)
        yield root,p

def test_positive_metadata_only(root_handle,monkeypatch):
    _,p=root_handle
    orig=os.open
    def forbid_file_open(name,*args,**kwargs):
        if str(name).endswith('token.bin'):
            raise AssertionError('credential content opened')
        return orig(name,*args,**kwargs)
    monkeypatch.setattr(m.os,'open',forbid_file_open)
    result=m.inspect_credential_metadata(p,project_root=ROOT)
    assert result['root_owns_material'] is True
    assert result['material_read'] is False
    assert result['credential_exchange_attested'] is False
    assert '/root/' not in str(result)

def test_world_readable_file_denied(root_handle):
    _,p=root_handle;p.chmod(0o644)
    with pytest.raises(m.MetadataHold):m.inspect_credential_metadata(p,project_root=ROOT)

def test_parent_group_writable_denied(root_handle):
    root,p=root_handle;root.chmod(0o770)
    with pytest.raises(m.MetadataHold):m.inspect_credential_metadata(p,project_root=ROOT)

def test_parent_not_private_denied(root_handle):
    root,p=root_handle;root.chmod(0o755)
    with pytest.raises(m.MetadataHold):m.inspect_credential_metadata(p,project_root=ROOT)

def test_symlink_final_denied(root_handle):
    root,p=root_handle
    q=root/'redirect';q.symlink_to(p)
    with pytest.raises(m.MetadataHold):m.inspect_credential_metadata(q,project_root=ROOT)

def test_symlink_ancestor_denied(root_handle):
    root,p=root_handle
    q=root/'symlink_parent';q.symlink_to(root,target_is_directory=True)
    with pytest.raises(m.MetadataHold):m.inspect_credential_metadata(q/'token.bin',project_root=ROOT)

def test_hardlink_denied(root_handle):
    root,p=root_handle
    q=root/'hardlink';os.link(p,q)
    with pytest.raises(m.MetadataHold):m.inspect_credential_metadata(q,project_root=ROOT)

def test_empty_file_denied(root_handle):
    _,p=root_handle;p.write_bytes(b'')
    with pytest.raises(m.MetadataHold):m.inspect_credential_metadata(p,project_root=ROOT)

def test_directory_as_handle_denied(root_handle):
    root,_=root_handle
    with pytest.raises(m.MetadataHold):m.inspect_credential_metadata(root,project_root=ROOT)

def test_binary_routes_to_canonical_r115(monkeypatch):
    called=[]
    monkeypatch.setattr(r115,'assert_pinned_binary',lambda:called.append(True))
    record=doctor.inspect_binary()
    assert called==[True] and record['binary_sha256']==r115.COPILOT_PILOT_SHA256
    assert record['executable_invoked'] is False

def test_binary_path_override_is_denied():
    with pytest.raises(doctor.DoctorHold):doctor.inspect_binary(Path('/usr/bin/true'))

def test_r115_failure_is_mapped_to_hold(monkeypatch):
    def bad():raise r115.R115PreclaimBlocked('test')
    monkeypatch.setattr(r115,'assert_pinned_binary',bad)
    with pytest.raises(doctor.DoctorHold):doctor.inspect_binary()

def test_empty_token_variable_detected_as_present():
    # Regression contract: explicit presence, even empty, cannot silently pass.
    import inspect
    text=inspect.getsource(doctor.main)
    assert 'if n in os.environ' in text
    assert 'if os.environ.get(n)' not in text
