"""R118 S01: canonical MCP command/args/cwd/tool binding; negative fixtures only."""
from __future__ import annotations
import copy
import json
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_r115_preclaim_executable_profile_v0_1 as m
WORKSPACE='/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/cf10-test-a118/workspace/repo'

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
          'tools':names,'cwd':workspace}
    spec.update(overrides)
    return {'mcpServers': {'ForPrintValidation':spec}}

def command(*,config=None,tools=None,readback=False):
    config=config if config is not None else canonical_mcp(WORKSPACE,readback=readback)
    names=['run_validation_suite','run_repo_diff_check','run_repo_head','run_repo_status']
    if readback:names.append('read_completed_validation_evidence')
    tools=tools if tools is not None else ['view','edit','apply_patch', *['ForPrintValidation-'+x for x in names]]
    return [str(m.COPILOT_PILOT_PATH),'-p','TASK','--silent','--model','auto',
            '--additional-mcp-config',json.dumps(config,sort_keys=True),
            '--available-tools',*tools,'--allow-all-tools','--disable-builtin-mcps',
            '--max-ai-credits','30','--no-auto-update','--sandbox','-C',WORKSPACE]


def test_actual_invocation_adapter_type_local_accepted():
    spec=canonical_mcp(WORKSPACE)['mcpServers']['ForPrintValidation']
    assert spec['type']=='local'
    m.assert_static_tool_and_mcp_boundary(command(),WORKSPACE)
    m.assert_static_tool_and_mcp_boundary(command(readback=True),WORKSPACE)
    m.assert_static_tool_and_mcp_boundary(command(config=canonical_mcp(WORKSPACE,timeout=950_000)),WORKSPACE)

def altered(key,value):
    cfg=copy.deepcopy(canonical_mcp(WORKSPACE))
    cfg['mcpServers']['ForPrintValidation'][key]=value
    return command(config=cfg)

@pytest.mark.parametrize('key,value',[
 ('type','stdio'),('type','http'),('transport','stdio'),('env',{}),
 ('env',{'GH_TOKEN':'leak'}),('envFile','/tmp/env'),('headers',{}),
 ('url','https://example.invalid/mcp'),('network',{}),
 ('command','/bin/sh'),('command','/tmp/evil/python'),('command','python3'),
 ('command',[]),('command',{}),
 ('cwd','/tmp'),('cwd',WORKSPACE+'/../secret'),
 ('args',[]),('args',['-c','import os']),('args',['--version']),
 ('tools',[]),('tools',['run_validation_suite','run_unreviewed']),
 ('timeout',0),('timeout',900_000),('timeout',1_200_001),('timeout',True),
 ('autoApprove',True),('disabled',False),('source','worker'),
])
def test_mcp_command_or_policy_widening_rejected(key,value):
    with pytest.raises(m.R115PreclaimBlocked,match='MCP_'):
        m.assert_static_tool_and_mcp_boundary(altered(key,value),WORKSPACE)

@pytest.mark.parametrize('index,value',[
 (0,'/tmp/mcp.py'),(1,'--other'),(2,'cf10-other-a999'),
 (3,'--other'),(4,'task;echo'),(5,'--other'),(6,'wf bad'),
 (7,'--other'),(8,'a'*63),(9,'--other'),
 (10,'/tmp'),(11,'--other'),(12,'/tmp/evidence'),
])
def test_mcp_argument_mutation_rejected(index,value):
    cfg=canonical_mcp(WORKSPACE)
    cfg['mcpServers']['ForPrintValidation']['args'][index]=value
    with pytest.raises(m.R115PreclaimBlocked,match='MCP_'):
        m.assert_static_tool_and_mcp_boundary(command(config=cfg),WORKSPACE)

def test_expected_python_allowlist_rejects_workspace_interpreter():
    cfg=canonical_mcp(WORKSPACE)
    cfg['mcpServers']['ForPrintValidation']['command']=WORKSPACE+'/python'
    with pytest.raises(m.R115PreclaimBlocked,match='MCP_INTERPRETER'):
        m.assert_static_tool_and_mcp_boundary(command(config=cfg),WORKSPACE)

def test_model_tools_must_equal_subprocess_tools_not_just_subset():
    a=command(tools=['view','edit','apply_patch','ForPrintValidation-run_validation_suite'])
    with pytest.raises(m.R115PreclaimBlocked,match='MCP_MODEL_TOOL_LIST_DRIFT'):
        m.assert_static_tool_and_mcp_boundary(a,WORKSPACE)

def test_readback_needs_source_scoped_flag_and_tool_binding():
    cfg=canonical_mcp(WORKSPACE,readback=True)
    cfg['mcpServers']['ForPrintValidation']['args'].pop()
    with pytest.raises(m.R115PreclaimBlocked,match='MCP_'):
        m.assert_static_tool_and_mcp_boundary(command(config=cfg,readback=True),WORKSPACE)
    cfg=canonical_mcp(WORKSPACE,readback=False)
    cfg['mcpServers']['ForPrintValidation']['tools'].append('read_completed_validation_evidence')
    with pytest.raises(m.R115PreclaimBlocked,match='MCP_'):
        m.assert_static_tool_and_mcp_boundary(command(config=cfg),WORKSPACE)

def test_canonical_invocation_source_crosswalk_is_same_contract():
    from pathlib import Path
    # This is not inference: source crosswalk is maintained alongside exact
    # local preclaim fixtures, with the legacy adapter still the producer.
    source=Path(__file__).resolve().parents[4]/'scripts/coordination/control_plane/worker_runtime/invocation_adapter.py'
    if source.exists():
        content=source.read_text()
        assert '"type": "local"' in content
        assert '"command": python_executable' in content
        assert '"cwd": str(workspace)' in content
        assert '"tools": [' in content
        assert '"--attempt-id"' in content


def test_no_runtime_authorization_or_credential_claim():
    import inspect
    text=inspect.getsource(m.assert_pilot_preclaim)
    assert text.index('assert_static_tool_and_mcp_boundary(') < text.index('assert_pinned_binary(')
    assert "'provider_vs_tool_egress_enforced': False" in text
    assert "'credential_cache_kernel_isolated': False" in text
