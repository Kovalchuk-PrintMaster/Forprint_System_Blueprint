"""Y doctor: metadata-only, never read credentials or launch Worker."""
from pathlib import Path
from unittest.mock import patch
import os
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_first_worker_operator_doctor_v0_1 as d
from scripts.coordination.control_plane.worker_runtime import cf10_first_worker_critical_path_v0_1 as y


def test_no_handle_is_unconfigured():
    row=d.inspect_auth_handle(None)
    assert row['source']=='UNCONFIGURED'
    assert row['material_read'] is False

@pytest.mark.parametrize('path',["/tmp/cf10/token","/srv/software_development/forprint-project/forprint_system_blueprint/x","relative", "/root/../etc/forprint/token"])
def test_forbidden_handle_paths(path):
    with pytest.raises(d.DoctorHold):d.inspect_auth_handle(Path(path))

def _mock_handle(monkeypatch, mode=0o600):
    import stat as statlib
    from types import SimpleNamespace
    path=Path('/var/lib/forprint-credentials/y-test-token')
    def fake_lstat(self):
        if self==path:
            return SimpleNamespace(st_mode=statlib.S_IFREG | mode,st_uid=0,st_gid=0,
                                   st_nlink=1,st_size=50)
        if self==path.parent:
            return SimpleNamespace(st_mode=statlib.S_IFDIR | 0o700,st_uid=0)
        raise FileNotFoundError()
    monkeypatch.setattr(Path,'lstat',fake_lstat)
    monkeypatch.setattr(Path,'is_symlink',lambda self:False)
    return path

def test_private_handle_metadata_only(monkeypatch):
    path=_mock_handle(monkeypatch)
    result=d.inspect_auth_handle(path)
    assert result['source']=='ROOT_EXTERNAL_HANDLE_REVIEW_ONLY'
    assert result['material_read'] is False
    assert not any('/var/lib' in str(value) for value in result.values())

def test_insecure_handle_denied(monkeypatch):
    path=_mock_handle(monkeypatch,0o644)
    with pytest.raises(d.DoctorHold):d.inspect_auth_handle(path)

def test_doctor_review_fails_if_inherited_env():
    with pytest.raises(d.DoctorHold):d.report(source_head='d9911cb24f03ee443cad6adea945dcab826b8293',
      binary={'pinned':True,'binary_sha256':y.BIN_SHA},auth=d.inspect_auth_handle(None),
      token_environment_names=['GH_TOKEN'])

def test_clean_doctor_reports_unproven():
    result=d.report(source_head='d9911cb24f03ee443cad6adea945dcab826b8293',
      binary={'pinned':True,'binary_sha256':y.BIN_SHA},auth=d.inspect_auth_handle(None))
    assert result['result']=='PASS_PRELIVE_CRITICAL_PATH_REVIEW'
    assert result['gates_open'] is True
    assert result['auth_proven'] is False and result['no_live_dispatch'] is True

@pytest.mark.parametrize('name',['GH_TOKEN','GITHUB_TOKEN','COPILOT_GITHUB_TOKEN','OPENAI_API_KEY'])
def test_env_key_never_authorizes(name):
    with pytest.raises(d.DoctorHold):d.report(source_head='d9911cb24f03ee443cad6adea945dcab826b8293',
      binary={'pinned':True,'binary_sha256':y.BIN_SHA},auth=d.inspect_auth_handle(None),
      token_environment_names=[name])

def test_unexpected_binary_blocked():
    with pytest.raises(d.DoctorHold):d.report(source_head='d9911cb24f03ee443cad6adea945dcab826b8293',
      binary={'pinned':False,'binary_sha256':y.BIN_SHA},auth=d.inspect_auth_handle(None))
