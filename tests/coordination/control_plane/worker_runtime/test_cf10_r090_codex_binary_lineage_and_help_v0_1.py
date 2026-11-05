"""R090: synthetic filesystem receipts and mocked systemd; never run Codex."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r090_codex_binary_lineage_and_help_v0_1 as m,
    cf10_r089_codex_pinned_install_v0_1 as r089,
    cf10_r088_codex_offline_attestation_v0_1 as r088,
)

GOOD_HELP = ('Codex exec help\n'+'\n'.join(f'  {opt} <value>' for opt in m.HELP_FLAGS)+'\n').encode()


@pytest.fixture
def installed(monkeypatch, tmp_path):
    binary = tmp_path/'codex'
    binary.write_bytes(b'\x7fELF\x02\x01'+b'Q' * 1_100_000)
    binary.chmod(0o755)
    sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    receipts = tmp_path/'durable'
    receipts.mkdir(mode=0o700)
    receipt = receipts/'codex_r089_v0_166_0_install.json'
    monkeypatch.setattr(m, 'BINARY', binary)
    monkeypatch.setattr(m, 'RECEIPT_ROOT', receipts)
    monkeypatch.setattr(m, 'RECEIPT', receipt)
    monkeypatch.setattr(m, 'ROOT_UID', os.getuid())
    monkeypatch.setattr(m, 'ROOT_GID', os.getgid())
    monkeypatch.setattr(m, 'EXPECTED_BINARY_SHA_X86_64', sha)
    monkeypatch.setattr(m, '_check_install_head', lambda head: None)
    monkeypatch.setattr(r089, 'DESTINATION', binary)
    monkeypatch.setattr(r089, 'RECEIPT', receipt)
    asset = r089.selected_asset('x86_64')
    monkeypatch.setattr(r089, 'selected_asset', lambda: asset)
    body = r089._receipt_body(pinned=asset, binary_sha256=sha, source_head=m.HEAD_AT_INSTALL)
    receipt.write_text(json.dumps(body, sort_keys=True)+'\n', encoding='utf-8')
    receipt.chmod(0o600)
    monkeypatch.setattr(r088, 'inspect_candidates', lambda: {
        'status':'ONE_ROOT_OWNED_EXECUTABLE_CANDIDATE_NO_AUTH_ATTESTATION',
        'selected_executable':str(binary)})
    return binary, receipt, body


def test_attest_exact_installed_candidate_no_authority(installed):
    report = m.attest()
    assert report['status'].startswith('PINNED_CODEX_BINARY_AND_RECEIPT')
    assert report['binary_sha256'] == hashlib.sha256(installed[0].read_bytes()).hexdigest()
    assert report['provider_ready'] is False
    assert report['provider_auth_verified'] is False
    assert report['worker_launched'] is False
    assert report['claim_consumed'] is False
    assert report['cli_exec_help_probe_executed'] is False


def test_binary_changes_after_receipt_denied(installed):
    with installed[0].open('ab') as f: f.write(b'ATTACK')
    with pytest.raises(m.LineageBlocked, match='SHA_NOT_REVIEWED_PIN'):
        m.attest()


def test_receipt_extra_field_even_with_own_sha_denied(installed):
    binary, receipt, body = installed
    body['provider_ready'] = True
    receipt.write_text(json.dumps(body)+'\n')
    with pytest.raises(m.LineageBlocked, match='RECEIPT_NOT_EXACT'):
        m.attest()


def test_receipt_source_head_mutation_denied(installed):
    binary, receipt, body = installed
    body['source_head_at_install'] = 'f'*40
    receipt.write_text(json.dumps(body)+'\n')
    with pytest.raises(m.LineageBlocked, match='RECEIPT_NOT_EXACT'):
        m.attest()


def test_receipt_perms_relaxed_denied(installed):
    installed[1].chmod(0o644)
    with pytest.raises(m.LineageBlocked, match='EXACT_MODE_DRIFT'):
        m.attest()


def test_durable_state_dir_relaxed_denied(installed):
    installed[1].parent.chmod(0o755)
    with pytest.raises(m.LineageBlocked, match='ROOT_NOT_PRIVATE'):
        m.attest()


def test_receipt_missing_denied(installed):
    installed[1].unlink()
    with pytest.raises(m.LineageBlocked):
        m.attest()


def test_receipt_symlink_denied(installed):
    receipt = installed[1]; receipt.unlink()
    receipt.symlink_to(installed[0])
    with pytest.raises(m.LineageBlocked):
        m.attest()


def test_binary_symlink_denied(installed):
    binary,receipt,_ = installed
    other=binary.parent/'other';binary.rename(other);binary.symlink_to(other)
    with pytest.raises(m.LineageBlocked):
        m.attest()


def test_binary_executable_mode_drifts_denied(installed):
    installed[0].chmod(0o700)
    with pytest.raises(m.LineageBlocked, match='EXACT_MODE_DRIFT'):
        m.attest()


def test_ambiguous_executable_inventory_denied(installed,monkeypatch):
    monkeypatch.setattr(r088, 'inspect_candidates', lambda: {
        'status':'REVIEW_EXECUTABLE_PATH_OR_SYMLINK_NO_PROBE', 'selected_executable':None})
    with pytest.raises(m.LineageBlocked,match='NOT_UNAMBIGUOUS'):
        m.attest()


def test_pinned_head_must_equal_installer_commit():
    with pytest.raises(m.LineageBlocked,match='NOT_PINNED'):
        m._check_install_head('e'*40)


def test_pinned_head_missing_git_ancestry(monkeypatch):
    monkeypatch.setattr(m,'_git',lambda *args: False)
    with pytest.raises(m.LineageBlocked,match='COMMIT_UNAVAILABLE'):
        m._check_install_head(m.HEAD_AT_INSTALL)


def test_pinned_head_not_ancestor_rejected(monkeypatch):
    monkeypatch.setattr(m,'_git',lambda *args: args[0]=='cat-file')
    with pytest.raises(m.LineageBlocked,match='NOT_ANCESTOR'):
        m._check_install_head(m.HEAD_AT_INSTALL)


def test_help_flags_all_advertised_not_authorization():
    report=m.inspect_help_text(GOOD_HELP,b'',0)
    assert report['all_r087_switches_advertised'] is True
    assert report['unconfirmed_switches']==[]
    assert not report['worker_launched']
    assert not report['result_accepted']
    assert 'Codex exec help' not in repr(report)


def test_missing_help_flags_reports_only_public_names():
    report=m.inspect_help_text(b'--json --model\n',b'',0)
    assert report['all_r087_switches_advertised'] is False
    assert '--ignore-rules' in report['unconfirmed_switches']
    assert report['status']=='R087_ARGUMENTS_NOT_ALL_ADVERTISED_REQUIRES_REVIEW'
    assert 'secret' not in repr(report)


@pytest.mark.parametrize('out,err,rc',[
    (b'',b'',0),(b'--json',b'',1),
    (b'a'*65537,b'',0),(b'--json',b'b'*65537,0),
    (b'\xff\xff',b'',0),
])
def test_invalid_help_output_rejected(out,err,rc):
    with pytest.raises(m.LineageBlocked):
        m.inspect_help_text(out,err,rc)


def test_exact_sandbox_exec_help_argv(monkeypatch,installed):
    from scripts.coordination.control_plane import cf10_r077_runner_home_contract_v0_1 as home
    monkeypatch.setattr(home, 'assert_systemd_properties', lambda props: True)
    unit='forprint-cf10-codexprobe-'+'a'*16
    monkeypatch.setattr(r088,'probe_properties',lambda unit: {
        'IPAddressDeny':'any','Restart':'no','User':'forprint-runner',
        'ProtectSystem':'strict','ProtectHome':'yes','StateDirectory':'forprint-runner',
        'StateDirectoryMode':'0700','PrivateTmp':'yes'})
    argv=m.build_help_argv(unit)
    assert argv[-4:]==['--',str(installed[0]),'exec','--help']
    assert '--property=IPAddressDeny=any' in argv
    assert '--property=Restart=no' in argv
    assert 'curl' not in repr(argv) and ' -p ' not in repr(argv)


def test_invalid_sandbox_probes_denied(monkeypatch):
    monkeypatch.setattr(r088,'probe_properties',lambda unit: {
        'IPAddressDeny':'none', 'Restart':'no','User':'forprint-runner'})
    with pytest.raises(m.LineageBlocked, match='SANDBOX_CONTRACT_DRIFT'):
        m.build_help_argv('forprint-cf10-codexprobe-'+'a'*16)


def test_no_confirm_blocks_before_attest(monkeypatch):
    gate=Mock(side_effect=AssertionError('MUST NOT ATTEST'))
    monkeypatch.setattr(m,'attest',gate)
    monkeypatch.delenv('CF10_CONFIRM_CODEX_HELP_PROBE',raising=False)
    assert m.main(['--mode','help-probe'])==2
    gate.assert_not_called()


def test_real_probe_never_runs_nonroot(monkeypatch):
    monkeypatch.setattr(m.os,'geteuid',lambda:1000)
    gate=Mock(side_effect=AssertionError('MUST NOT ATTEST'))
    monkeypatch.setattr(m,'attest',gate)
    with pytest.raises(m.LineageBlocked, match='ROOT_INTERACTIVE'):
        m.probe_help()
    gate.assert_not_called()


def test_probe_mocked_stays_offline_and_command_exact(monkeypatch,installed):
    monkeypatch.setattr(m,'PROJECT',Path.cwd())
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as owner_console
    monkeypatch.setattr(owner_console, 'source_guard', lambda _root: 'c951bef0e2238ea3322a4779ced3e6d546e7be89')
    monkeypatch.setattr(m.os,'geteuid',lambda:0)
    monkeypatch.setattr(m.os,'isatty',lambda fd:True)
    monkeypatch.setattr(m.uuid,'uuid4',lambda:SimpleNamespace(hex='a'*32))
    monkeypatch.setattr(m,'build_help_argv',lambda unit:['/usr/bin/systemd-run','--',str(installed[0]),'exec','--help'])
    result=Mock(returncode=0,stdout=GOOD_HELP,stderr=b'')
    runner=Mock(return_value=result)
    monkeypatch.setattr(m.subprocess,'run',runner)
    report=m.probe_help()
    argv=runner.call_args.args[0]
    assert argv[-3:]==[str(installed[0]),'exec','--help']
    assert runner.call_args.kwargs['input']==b''
    assert runner.call_args.kwargs['env']=={'PATH':'/usr/bin:/bin','LANG':'C'}
    assert report['all_r087_switches_advertised'] is True
    assert report['provider_ready'] is False
    assert report['worker_launched'] is False


def test_probe_timeout_never_retries(monkeypatch,installed):
    import subprocess
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_r077_runner_home_contract_v0_1 as home
    monkeypatch.setattr(console, 'source_guard', lambda root: 'a'*40)
    monkeypatch.setattr(home, 'assert_runner_home', lambda: True)
    monkeypatch.setattr(m,'PROJECT',Path.cwd())
    monkeypatch.setattr(m.os,'geteuid',lambda:0)
    monkeypatch.setattr(m.os,'isatty',lambda fd:True)
    monkeypatch.setattr(m,'build_help_argv',lambda unit:['/usr/bin/systemd-run','--',str(installed[0]),'exec','--help'])
    runner=Mock(side_effect=subprocess.TimeoutExpired('systemd-run',45))
    monkeypatch.setattr(m.subprocess,'run',runner)
    with pytest.raises(m.LineageBlocked,match='TIMEOUT_NO_RETRY'):
        m.probe_help()
    runner.assert_called_once()
