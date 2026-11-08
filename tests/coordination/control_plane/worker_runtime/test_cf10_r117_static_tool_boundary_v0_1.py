"""R117 S02: pure negative/tool-scope tests; no real CLI/network/auth or claims."""
from __future__ import annotations
import json
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_r115_preclaim_executable_profile_v0_1 as m

WORKSPACE='/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/cf10-test-a117/workspace/repo'


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

def command(*,config=None,tools=None,readback=False):
    config = config if config is not None else canonical_mcp(WORKSPACE,readback=readback)
    tools = tools if tools is not None else ['view','edit','apply_patch','ForPrintValidation-run_validation_suite',
       'ForPrintValidation-run_repo_diff_check','ForPrintValidation-run_repo_head',
       'ForPrintValidation-run_repo_status',
       *(['ForPrintValidation-read_completed_validation_evidence'] if readback else [])]
    return [str(m.COPILOT_PILOT_PATH),'-p','TASK','--silent','--model','auto',
       '--additional-mcp-config',json.dumps(config,sort_keys=True),
       '--available-tools',*tools,'--allow-all-tools','--disable-builtin-mcps',
       '--max-ai-credits','30','--no-auto-update','--sandbox','-C',WORKSPACE]


def test_bounded_default_and_readback():
    m.assert_static_tool_and_mcp_boundary(command(),WORKSPACE)
    m.assert_static_tool_and_mcp_boundary(tuple(command()),WORKSPACE)
    more=['view','edit','apply_patch',*[x for x in sorted(m.PILOT_TOOL_UNIVERSE) if x.startswith('ForPrintValidation-')]]
    m.assert_static_tool_and_mcp_boundary(command(readback=True),WORKSPACE)

@pytest.mark.parametrize('name', ['bash','Bash','shell','web','Web','terminal','*','ForPrintValidation-run_anything',
                                    'ForPrintValidation-run_validation_suite*','other_server-run_repo_head'])
def test_unreviewed_tool_refused(name):
    with pytest.raises(m.R115PreclaimBlocked,match='TOOL_UNIVERSE'):
        m.assert_static_tool_and_mcp_boundary(command(tools=['view',name]),WORKSPACE)

@pytest.mark.parametrize('list_', [[],['view','view'], ['--sandbox'], ['view','--disable-builtin-mcps']])
def test_empty_duplicate_or_flag_spoof_refused(list_):
    with pytest.raises(m.R115PreclaimBlocked):
        m.assert_static_tool_and_mcp_boundary(command(tools=list_),WORKSPACE)

@pytest.mark.parametrize('changed',[
    lambda a:a.insert(1,'--config'),
    lambda a:a.insert(1,'--no-sandbox'),
    lambda a:a.append('--allow-all-urls'),
    lambda a:a.__setitem__(a.index('--allow-all-tools'),'--yolo'),
    lambda a:a.__setitem__(a.index('--max-ai-credits')+1,'0'),
    lambda a:a.__setitem__(a.index('--max-ai-credits')+1,'30;id'),
    lambda a:a.__setitem__(a.index('--disable-builtin-mcps'),'--enable-builtin-mcps'),
    lambda a:a.insert(-4,'--dangerous'),
])
def test_extra_flags_not_authorized(changed):
    argv=command();changed(argv)
    with pytest.raises(m.R115PreclaimBlocked):
        m.assert_static_tool_and_mcp_boundary(argv,WORKSPACE)

@pytest.mark.parametrize('config',[
    {'mcpServers': {}},
    {'mcpServers': {'ForPrintValidation':{},'Unreviewed':{}}},
    {'mcpServers': {'ForPrintValidation': {'url':'https://example.com/mcp'}}},
    {'mcpServers': {'ForPrintValidation': {'type':'http'}}},
    {'mcpServers': {'ForPrintValidation': {'transport':'sse'}}},
    {'other': {'ForPrintValidation': {}}},
])
def test_unreviewed_mcp_surface_rejected(config):
    with pytest.raises(m.R115PreclaimBlocked,match='MCP'):
        m.assert_static_tool_and_mcp_boundary(command(config=config),WORKSPACE)

def test_duplicate_json_key_rejected_even_when_value_is_identical():
    a=command();a[7]='{"mcpServers":{"ForPrintValidation":{}},"mcpServers":{"ForPrintValidation":{}}}'
    with pytest.raises(m.R115PreclaimBlocked,match='MCP'):
        m.assert_static_tool_and_mcp_boundary(a,WORKSPACE)

def test_inference_and_credentials_not_claimed():
    assert m.COPILOT_PILOT_SHA256 == '985f0e1b1b3e734bc996324651307a076ae3deae21e3fa9f9af917983ce309c4'
    assert m.PILOT_TOOL_UNIVERSE.isdisjoint({'bash','web','shell'})
    # Regression on the canonical method: this boundary must be reached before
    # the binary read/claim and cannot become a new form of authorization.
    import inspect
    source=inspect.getsource(m.assert_pilot_preclaim)
    assert source.index('assert_static_tool_and_mcp_boundary(')<source.index('assert_pinned_binary(')
    assert "'credential_cache_kernel_isolated': False" in source
    assert "'provider_vs_tool_egress_enforced': False" in source
