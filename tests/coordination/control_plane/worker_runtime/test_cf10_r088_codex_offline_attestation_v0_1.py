"""R088 offline Codex inventory/probe policy: pure fixtures, no real CLI/systemd."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_r088_codex_offline_attestation_v0_1 as m

UNIT='forprint-cf10-codexprobe-'+'a'*16


def test_fixed_allowlist_and_no_live_authority():
    assert m.CANDIDATES == (Path('/usr/local/bin/codex'),Path('/usr/bin/codex'))
    result=m.inspect_candidates()
    assert result['provider_registry_ready'] is False
    assert result['executable_verified_for_worker'] is False
    assert result['cli_version_executed'] is False
    assert result['worker_launched'] is False
    assert result['live_dispatch_enabled'] is False
    assert result['automatic_retry'] is False
    assert result['provider_auth_verified'] is False


def test_missing_paths_become_inventory_not_exception(monkeypatch):
    monkeypatch.setattr(m,'_candidate_state',lambda path:'NOT_INSTALLED')
    result=m.inspect_candidates()
    assert result['status']=='CODEX_CLI_NOT_INSTALLED_IN_ALLOWED_PATHS'
    assert result['selected_executable'] is None


def test_one_exact_binary_discovered_without_auth(monkeypatch):
    monkeypatch.setattr(m,'_candidate_state',lambda p:'EXACT_ROOT_OWNED_BINARY_CANDIDATE' if p==m.CANDIDATES[0] else 'NOT_INSTALLED')
    result=m.inspect_candidates()
    assert result['selected_executable']==str(m.CANDIDATES[0])
    assert result['status'].startswith('ONE_ROOT_OWNED')
    assert result['provider_auth_verified'] is False


@pytest.mark.parametrize('status',[
    'SYMLINK_NEEDS_INDEPENDENT_PROVENANCE','UNTRUSTED_EXECUTABLE_PARENT',
    'EXECUTABLE_OWNERSHIP_OR_MODE_UNTRUSTED','NOT_REGULAR_EXECUTABLE',
    'DIRECTORY_MISSING',
])
def test_untrusted_or_missing_directory_never_selected(monkeypatch,status):
    monkeypatch.setattr(m,'_candidate_state',lambda p:status if p==m.CANDIDATES[0] else 'NOT_INSTALLED')
    assert m.inspect_candidates()['selected_executable'] is None


def test_two_root_binaries_are_ambiguous(monkeypatch):
    monkeypatch.setattr(m,'_candidate_state',lambda p:'EXACT_ROOT_OWNED_BINARY_CANDIDATE')
    assert m.inspect_candidates()['selected_executable'] is None


def test_non_allowlisted_path_rejected():
    with pytest.raises(m.CodexOfflineBlocked,match='NOT_ALLOWLISTED'):
        m._candidate_state(Path('/tmp/not-trusted/codex'))


def test_symlink_cannot_claim_binary(monkeypatch):
    monkeypatch.setattr(m,'CANDIDATES',(Path('/usr/bin/codex'),))
    monkeypatch.setattr(Path,'lstat',lambda p: SimpleNamespace(st_mode=(stat.S_IFLNK|0o777) if p==Path('/usr/bin/codex') else (stat.S_IFDIR|0o755),st_uid=0))
    assert m._candidate_state(Path('/usr/bin/codex'))=='SYMLINK_NEEDS_INDEPENDENT_PROVENANCE'


def test_not_root_owned_parent_denied(monkeypatch):
    monkeypatch.setattr(m,'CANDIDATES',(Path('/usr/bin/codex'),))
    monkeypatch.setattr(Path,'lstat',lambda p: SimpleNamespace(st_mode=stat.S_IFDIR|0o777,st_uid=1000))
    assert m._candidate_state(Path('/usr/bin/codex'))=='UNTRUSTED_EXECUTABLE_PARENT'


def test_sandbox_properties_exact_private_codex_home():
    p=m.probe_properties(UNIT)
    assert p['User']=='forprint-runner'
    assert p['ProtectSystem']=='strict'
    assert p['ProtectHome']=='yes'
    assert p['NoNewPrivileges']=='yes'
    assert p['StateDirectoryMode']=='0700'
    assert p['RuntimeDirectoryMode']=='0700'
    assert p['RuntimeDirectory']==UNIT
    assert p['IPAddressDeny']=='any'
    assert p['Restart']=='no'
    assert p['Environment']=='HOME=/var/lib/forprint-runner CODEX_HOME=/run/'+UNIT
    assert 'ReadWritePaths' not in p


@pytest.mark.parametrize('unit',['','forprint-cf10-worker-'+'b'*16,
    'forprint-cf10-codexprobe-TOOLONG','forprint-cf10-codexprobe-'+'A'*16,
    'forprint-cf10-codexprobe-'+'a'*17])
def test_invalid_unit_fails_closed(unit):
    with pytest.raises(m.CodexOfflineBlocked): m.probe_properties(unit)


def test_probe_argv_is_only_version(monkeypatch):
    from scripts.coordination.control_plane import cf10_r077_runner_home_contract_v0_1 as home
    validated=Mock(return_value=True)
    monkeypatch.setattr(home,'assert_systemd_properties',validated)
    argv=m.build_version_argv(Path('/usr/bin/codex'),m.probe_properties(UNIT),UNIT)
    assert argv[-3:]==['--','/usr/bin/codex','--version']
    assert '-p' not in argv and 'exec' not in argv
    assert '--property=IPAddressDeny=any' in argv
    assert '--property=RuntimeDirectoryMode=0700' in argv
    assert '--property=Restart=no' in argv
    assert '--property=User=forprint-runner' in argv
    assert not any('ReadWritePaths' in x for x in argv)
    validated.assert_called_once()


@pytest.mark.parametrize('field,value',[
    ('IPAddressDeny','none'),('User','root'),('ProtectHome','no'),
    ('ProtectSystem','full'),('Restart','always'),('RuntimeDirectoryMode','0777'),
    ('WorkingDirectory','/root'),('Environment','HOME=/root'),
])
def test_probe_property_drift_fails_before_subprocess(monkeypatch,field,value):
    p=m.probe_properties(UNIT);p[field]=value
    with pytest.raises(m.CodexOfflineBlocked,match='SANDBOX_DRIFT'):
        m.build_version_argv(Path('/usr/bin/codex'),p,UNIT)


def test_probe_command_rejects_not_pinned_executable():
    with pytest.raises(m.CodexOfflineBlocked,match='SANDBOX_DRIFT'):
        m.build_version_argv(Path('/opt/arbitrary/codex'),m.probe_properties(UNIT),UNIT)


def test_version_output_redacted_only():
    raw=b'codex-cli 1.2.3 secret-any-string\n'
    data=m._safe_version_output(raw,b'',0)
    assert data['version_stdout_sha256']==hashlib.sha256(raw).hexdigest()
    assert raw.decode().strip() not in repr(data)


@pytest.mark.parametrize('out,err,rc',[(b'',b'',0),(b'hello',b'',1),(b'a'*8193,b'',0),(b'hello',b'b'*8193,0)])
def test_version_output_failure_and_caps(out,err,rc):
    with pytest.raises(m.CodexOfflineBlocked):m._safe_version_output(out,err,rc)


def test_no_confirm_denies_even_before_inventory(monkeypatch):
    inventory=Mock(side_effect=AssertionError('must never inspect'))
    monkeypatch.setattr(m,'inspect_candidates',inventory)
    monkeypatch.delenv('CF10_CONFIRM_CODEX_VERSION_PROBE',raising=False)
    assert m.main(['--mode','probe'])==2
    inventory.assert_not_called()


def test_probe_nonroot_denies_before_any_executable_check(monkeypatch):
    monkeypatch.setattr(m.os,'geteuid',lambda:1000)
    inventory=Mock(side_effect=AssertionError('must never inspect'))
    monkeypatch.setattr(m,'inspect_candidates',inventory)
    with pytest.raises(m.CodexOfflineBlocked,match='ROOT_INTERACTIVE'):
        m.probe_version()
    inventory.assert_not_called()


def test_no_cli_probe_fails_before_systemd(monkeypatch):
    monkeypatch.setattr(m,'PROJECT',Path.cwd())
    monkeypatch.setattr(m.os,'geteuid',lambda:0)
    monkeypatch.setattr(m.os,'isatty',lambda fd:True)
    monkeypatch.setattr(m,'inspect_candidates',lambda:{'selected_executable':None})
    proc=Mock(side_effect=AssertionError('no systemd'))
    monkeypatch.setattr(m.subprocess,'run',proc)
    with pytest.raises(m.CodexOfflineBlocked,match='EXECUTABLE_NOT_ATTESTABLE'):
        m.probe_version()
    proc.assert_not_called()


def test_mocked_explicit_probe_has_fixed_argv_and_sanitized_env(monkeypatch):
    monkeypatch.setattr(m,'PROJECT',Path.cwd())
    monkeypatch.setattr(m.os,'geteuid',lambda:0)
    monkeypatch.setattr(m.os,'isatty',lambda fd:True)
    monkeypatch.setattr(m,'inspect_candidates',lambda:{'selected_executable':'/usr/bin/codex'})
    monkeypatch.setattr(m,'_source_and_home',lambda:None)
    monkeypatch.setattr(m.uuid,'uuid4',lambda:SimpleNamespace(hex='a'*32))
    from scripts.coordination.control_plane import cf10_r077_runner_home_contract_v0_1 as home
    monkeypatch.setattr(home,'assert_systemd_properties',lambda props:True)
    run=Mock(return_value=SimpleNamespace(returncode=0,stdout=b'codex-cli 1.0\n',stderr=b''))
    monkeypatch.setattr(m.subprocess,'run',run)
    result=m.probe_version()
    assert result['status'].startswith('OFFLINE_DISPOSABLE')
    assert not result['provider_registry_ready']
    assert not result['auth_tested']
    assert not result['worker_launched']
    args=run.call_args.args[0]
    assert args[-3:]==['--','/usr/bin/codex','--version']
    assert run.call_args.kwargs['input']==b''
    assert run.call_args.kwargs['env']=={'PATH':'/usr/bin:/bin','LANG':'C'}
    assert run.call_args.kwargs['timeout']==45
