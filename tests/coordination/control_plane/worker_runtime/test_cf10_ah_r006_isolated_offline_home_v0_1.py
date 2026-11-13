"""AH r006: disposable Copilot HOME is narrow, root-managed, and removed."""
from __future__ import annotations
import os,stat,hashlib,subprocess,shutil
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_child_v0_1 as child
from scripts.coordination.control_plane.worker_runtime import cf10_ae_delegated_anchor_v0_1 as anchor
from scripts.coordination.control_plane.worker_runtime import cf10_ae_delegated_kernel_rehearsal_v0_1 as ae
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
UNIT='forprint-cf10-batchad-'+'a'*16+'.service'
HOME='/run/'+UNIT.removesuffix('.service')+'/offline-home'

def test_fixed_no_secrets_no_shell_and_no_egress():
    env=anchor.sanitized_env(unit=UNIT)
    assert env['CF10_DISPOSABLE_HOME']==HOME
    assert not {'GITHUB_TOKEN','GH_TOKEN','COPILOT_GITHUB_TOKEN','OPENAI_API_KEY','ANTHROPIC_API_KEY'} & set(env)
    assert launcher.LIVE_CUTOVER_ENABLED is False
    assert 'LIVE_CUTOVER_ENABLED=True' not in Path(ae.__file__).read_text()

@pytest.mark.parametrize('bad',["other.service",'forprint-cf10-worker-'+'a'*24+'.service','forprint-cf10-batchad-a.service;cat'])
def test_anchor_rejects_unsafe_unit(bad):
    with pytest.raises(ValueError):anchor.sanitized_env(unit=bad)

def test_legacy_anchor_env_unchanged():
    env=anchor.sanitized_env()
    assert env['HOME']=='/nonexistent'
    assert 'CF10_DISPOSABLE_HOME' not in env

def test_no_home_legacy_probe_unchanged(monkeypatch):
    monkeypatch.delenv('CF10_DISPOSABLE_HOME',raising=False)
    seen={}
    def runner(*args,**kw):
        seen.update(kw)
        return SimpleNamespace(returncode=0,stdout=b'Copilot 1.0.107',stderr=b'')
    result=child.offline_version_probe(runner=runner)
    assert result['version_1_0_107_observed'] is True
    assert seen['env']['HOME']=='/nonexistent'
    assert 'COPILOT_HOME' not in seen['env']
    assert 'GH_TOKEN' not in seen['env']

@pytest.mark.parametrize('home',['/tmp/evil','/root/.copilot','/run/forprint-cf10-worker-'+('a'*24)+'/offline-home',HOME+'/../else'])
def test_invalid_home_path_is_rejected(monkeypatch,home):
    monkeypatch.setenv('CF10_DISPOSABLE_HOME',home)
    with pytest.raises(child.OfflineProbeFailure) as ex:
        child.offline_version_probe(runner=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('must not exec')))
    assert ex.value.record['failure_code']=='PROBE_INTERNAL'

def test_missing_exact_home_is_failure_not_success(monkeypatch):
    monkeypatch.setenv('CF10_DISPOSABLE_HOME',HOME)
    with pytest.raises(child.OfflineProbeFailure) as ex:
        child.offline_version_probe(runner=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('must not exec')))
    assert ex.value.record['failure_code'] in {'EXEC_OSERROR','PROBE_INTERNAL'}

def test_exact_home_env_does_not_inherit_tokens(tmp_path,monkeypatch):
    class S:
        st_mode=stat.S_IFDIR|0o700
        st_uid=996
        st_gid=992
    class P:
        st_mode=stat.S_IFDIR|0o750
        st_uid=0
        st_gid=992
    actual_lstat=child.os.lstat
    def lstat(path):
        if str(path)==HOME:return S()
        if str(path)==os.path.dirname(HOME):return P()
        return actual_lstat(path)
    monkeypatch.setattr(child.os,'lstat',lstat)
    monkeypatch.setenv('CF10_DISPOSABLE_HOME',HOME)
    monkeypatch.setenv('GH_TOKEN','FAKE_SENSITIVE_TOKEN_FOR_TEST')
    seen={}
    def runner(args,**kw):
        seen.update({'args':args,'env':kw['env']})
        return SimpleNamespace(returncode=0,stdout=b'copilot 1.0.107',stderr=b'')
    assert child.offline_version_probe(runner=runner)['version_1_0_107_observed'] is True
    assert seen['args']==['/usr/local/bin/forprint-copilot-1.0.107','--version']
    assert seen['env']['HOME']==HOME
    assert seen['env']['COPILOT_HOME']==HOME+'/.copilot'
    assert seen['env']['XDG_CACHE_HOME']==HOME+'/.cache'
    assert seen['env']['XDG_DATA_HOME']==HOME+'/.local/share'
    assert 'GH_TOKEN' not in seen['env']
    assert 'FAKE_SENSITIVE_TOKEN_FOR_TEST' not in str(seen)

def test_scoped_home_provision_and_fd_safe_cleanup(tmp_path,monkeypatch):
    if os.geteuid()!=0:pytest.skip('requires root to chown runner 996')
    oldroot=ae.RUN_ROOT
    root=tmp_path
    monkeypatch.setattr(ae,'RUN_ROOT',root)
    path=root/UNIT.removesuffix('.service')
    path.mkdir(mode=0o750)
    os.chown(path,0,992)
    os.chmod(path,0o750)
    try:
        home=ae.provision_offline_home(path)
        assert stat.S_IMODE(home.stat().st_mode)==0o700
        assert (home.stat().st_uid,home.stat().st_gid)==(996,992)
        (home/'fake-cache').mkdir()
        (home/'fake-cache'/'test.txt').write_text('test')
        (home/'fake-link').symlink_to(tmp_path/'outside')
        (path/'anchor.py').write_text('x')
        (path/'child.py').write_text('x')
        (path/'anchor.sock').write_text('x')
        (path/'control.sock').write_text('x')
        ae.cleanup_run(path)
        assert not path.exists()
    finally:
        monkeypatch.setattr(ae,'RUN_ROOT',oldroot)

def test_provision_rejects_other_namespace(tmp_path,monkeypatch):
    monkeypatch.setattr(ae,'RUN_ROOT',tmp_path)
    bad=tmp_path/'wrong-name';bad.mkdir()
    with pytest.raises(ae.AEHold):ae.provision_offline_home(bad)

def test_home_cleanup_must_never_follow_fake_home_symlink(tmp_path,monkeypatch):
    monkeypatch.setattr(ae,'RUN_ROOT',tmp_path)
    p=tmp_path/UNIT.removesuffix('.service');p.mkdir()
    (p/'offline-home').symlink_to(tmp_path)
    for n in ('anchor.py','child.py','anchor.sock','control.sock'):(p/n).write_text('x')
    with pytest.raises(ae.AEHold):ae.cleanup_run(p)
    assert tmp_path.is_dir()

def test_only_offline_mode_adds_write_path():
    source=Path(ae.__file__).read_text()
    assert "if offline_home is not None:" in source
    assert "props.append('ReadWritePaths='+str(offline_home))" in source
    assert "props.append('PrivateTmp=yes')" in source
    assert "'ProtectSystem=strict'" in source
    assert "'PrivateNetwork=yes'" in source
    assert "'IPAddressDeny=any'" in source
    assert "'RestrictAddressFamilies=AF_UNIX'" in source
