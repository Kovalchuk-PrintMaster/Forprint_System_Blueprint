"""R115 negative controls: local fixtures only, no real Copilot/systemd/claims."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_r115_preclaim_executable_profile_v0_1 as r115
from scripts.coordination.control_plane.worker_runtime import cf10_r081_provider_adapter_v0_1 as provider
m = r115


WORKSPACE='/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/cf10-test-a115/workspace/repo'


def canonical_mcp(workspace, *, readback=False, **overrides):
    from pathlib import Path
    attempt=Path(workspace).parents[1].name
    root=Path(workspace).parents[1]
    names=['run_validation_suite','run_repo_diff_check','run_repo_head','run_repo_status']
    if readback:names.append('read_completed_validation_evidence')
    spec={'type':'local',
          'command':'/srv/software_development/forprint-project/forprint_system_blueprint/.venv_blueprint/bin/python',
          'args':[str(Path(workspace)/m.PILOT_MCP_SCRIPT),
                  '--attempt-id',attempt,
                  '--task-id','cf10-fixture-task-v0-1',
                  '--work-front-id','wf-cf10-fixture-v0-1',
                  '--decision-id','d'*64,
                  '--workspace-repo',workspace,
                  '--evidence-root',str(root/'evidence'/'structured_command'),
                  *(['--enable-completed-readback'] if readback else [])],
          'tools':names, 'cwd':workspace}
    spec.update(overrides)
    return {'mcpServers':{'ForPrintValidation':spec}}

def sample_argv():
    binding={'provider_id':'github_copilot_cli','model_id':'auto','workspace':WORKSPACE}
    task={'base_argv':[str(r115.COPILOT_PILOT_PATH)],'prompt':'TASK',
          'mcp_config_json':__import__('json').dumps(canonical_mcp(WORKSPACE)),
          'available_tools':('view','edit','apply_patch','ForPrintValidation-run_validation_suite',
                            'ForPrintValidation-run_repo_diff_check','ForPrintValidation-run_repo_head','ForPrintValidation-run_repo_status'),
          'permission_patterns':('ForPrintValidation(run_validation_suite)',),
          'readback_tool':None,'readback_permission':None,
          'mcp_server_name':'ForPrintValidation','max_ai_credits':30,
          'mcp_timeout_ms':None}
    return provider.route_invocation(provider_id='github_copilot_cli',
                                     binding=binding,frozen_task=task)['argv']


def sample_command(**overrides):
    props={'IPAddressDeny':'','RestrictAddressFamilies':'AF_UNIX AF_INET AF_INET6',
           'PrivateNetwork':'no','ProtectSystem':'strict','NoNewPrivileges':'yes'}
    props.update(overrides)
    return ['/usr/bin/systemd-run','--no-block',
            *['--property='+k+'='+v for k,v in props.items()],
            '--','/usr/bin/python3','-I','-B','/path/gate.py']


def test_r081_emits_explicit_sandbox_with_existing_permissions():
    argv=sample_argv()
    assert argv[-4:]==['--no-auto-update','--sandbox','-C',WORKSPACE]
    r115.assert_frozen_argv(argv,WORKSPACE)


@pytest.mark.parametrize('bad_argv',[
    ['/usr/local/bin/copilot'],['/usr/bin/true'],[str(r115.COPILOT_PILOT_PATH)],
])
def test_legacy_and_unpinned_executables_block(bad_argv):
    with pytest.raises(r115.R115PreclaimBlocked,match='FROZEN_PROVIDER_BINARY_PATH'):
        r115.assert_frozen_argv(bad_argv,WORKSPACE)


@pytest.mark.parametrize('delta',[
    lambda a: a.remove('--sandbox'),
    lambda a: a.insert(-2,'--sandbox'),
    lambda a: a.insert(1,'--sandbox'),
    lambda a: a.__setitem__(-1,'/tmp/other'),
    lambda a: a.__setitem__(-4,'--no-sandbox'),
    lambda a: a.append('--no-sandbox'),
    lambda a: a.append('--allow-all-paths'),
    lambda a: a.append('--allow-all-urls'),
    lambda a: a.append('--yolo'),
    lambda a: a.append('--allow-all'),
    lambda a: a.remove('--additional-mcp-config'),
    lambda a: a.append('--model'),
])
def test_frozen_argv_tampering_blocks(delta):
    argv=sample_argv();delta(argv)
    with pytest.raises(r115.R115PreclaimBlocked):
        r115.assert_frozen_argv(argv,WORKSPACE)


def test_no_sandbox_setting_inside_prompt_can_never_grant_sandbox():
    argv=sample_argv();argv[-4]='--no-auto-update';argv.remove('--sandbox');
    argv[argv.index('-p')+1]='--sandbox'
    with pytest.raises(r115.R115PreclaimBlocked,match='SANDBOX_ARGV_TAIL'):
        r115.assert_frozen_argv(argv,WORKSPACE)


@pytest.mark.parametrize('props,code',[
    ({'IPAddressDeny':'any'},'NETWORK_DENIED'),
    ({'IPAddressDeny':'  ANY '},'NETWORK_DENIED'),
    ({'RestrictAddressFamilies':'AF_UNIX AF_NETLINK'},'AF_INET_UNAVAILABLE'),
    ({'RestrictAddressFamilies':'~AF_INET AF_INET6'},'AF_INET_UNAVAILABLE'),
    ({'PrivateNetwork':'yes'},'NETWORK_NAMESPACE_BLOCKED'),
])
def test_network_impossibility_denied_before_claim(props,code):
    values=r115.parse_systemd_properties(sample_command(**props))
    with pytest.raises(r115.R115PreclaimBlocked,match=code):
        r115.assert_inference_network_not_impossible(values)


def test_network_feasibility_is_not_egress_or_sandbox_proof():
    props=r115.parse_systemd_properties(sample_command())
    assert r115.assert_inference_network_not_impossible(props) is None
    assert 'ProtectSystem' in props


def test_duplicate_systemd_keys_cannot_override_network_deny():
    cmd=sample_command()
    cmd.insert(2,'--property=IPAddressDeny=any')
    with pytest.raises(r115.R115PreclaimBlocked,match='PROPERTY_DUPLICATE'):
        r115.parse_systemd_properties(cmd)


def test_malformed_property_rejected():
    with pytest.raises(r115.R115PreclaimBlocked,match='PROPERTY_MALFORMED'):
        r115.parse_systemd_properties(['--property=not-a-pair'])


def test_combined_gate_rejects_invalid_network_without_reading_binary(monkeypatch):
    monkeypatch.setattr(r115,'assert_pinned_binary',lambda: (_ for _ in ()).throw(AssertionError('should not reach binary')))
    with pytest.raises(r115.R115PreclaimBlocked,match='NETWORK_DENIED'):
        r115.assert_pilot_preclaim(argv=sample_argv(),workspace=WORKSPACE,
                                  systemd_command=sample_command(IPAddressDeny='any'))


def test_combined_gate_would_not_authorize_even_after_negative_checks(monkeypatch):
    monkeypatch.setattr(r115,'assert_pinned_binary',lambda:None)
    row=r115.assert_pilot_preclaim(argv=sample_argv(),workspace=WORKSPACE,
                                  systemd_command=sample_command())
    assert row['live_worker_authorized'] is False
    assert row['effective_sandbox_policy_attested'] is False
    assert row['provider_vs_tool_egress_enforced'] is False
    assert row['claim_consumed'] is False


def test_pinned_binary_sha_and_inode_via_disposable_file(tmp_path,monkeypatch):
    payload=b'fixture binary only'
    binary=tmp_path/'copilot'
    binary.write_bytes(payload)
    binary.chmod(0o700)
    monkeypatch.setattr(r115,'COPILOT_PILOT_PATH',binary)
    monkeypatch.setattr(r115,'COPILOT_PILOT_BYTES',len(payload))
    monkeypatch.setattr(r115,'COPILOT_PILOT_SHA256',hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(r115,'_require_root_owned_parent',lambda _:None)
    if os.geteuid()!=0:
        # inode must be root-owned, no test account credential promotion
        with pytest.raises(r115.R115PreclaimBlocked,match='INODE_OR_SIZE'):
            r115.assert_pinned_binary()
        return
    r115.assert_pinned_binary()
    binary.write_bytes(b'x'*len(payload))
    with pytest.raises(r115.R115PreclaimBlocked,match='SHA256_MISMATCH'):
        r115.assert_pinned_binary()
    binary.unlink()
    binary.symlink_to(tmp_path/'other')
    with pytest.raises(r115.R115PreclaimBlocked,match='MISSING_OR_LINKED'):
        r115.assert_pinned_binary()


def test_real_hooks_before_irreversible_root_receipt():
    text=(Path(__file__).resolve().parents[4] / 'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py').read_text()
    assert 'r115.assert_pilot_preclaim(' in text
    assert text.index('r115.assert_pilot_preclaim(',text.index('def _core')) < text.index('receipts.claim(',text.index('def _core'))
    assert 'LIVE_CUTOVER_ENABLED=False' in text
