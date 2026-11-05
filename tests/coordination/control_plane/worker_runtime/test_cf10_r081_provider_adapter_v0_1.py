"""R081: old Copilot command/policy exact parity and fail-closed routing."""
from __future__ import annotations
import hashlib
import json
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_r081_provider_adapter_v0_1 as m

BASE=('view','edit','apply_patch','ForPrintValidation-run_validation_suite','ForPrintValidation-run_repo_diff_check','ForPrintValidation-run_repo_head','ForPrintValidation-run_repo_status')
PERMS=('ForPrintValidation(run_validation_suite)','ForPrintValidation(run_repo_diff_check)','ForPrintValidation(run_repo_head)','ForPrintValidation(run_repo_status)')
RB='ForPrintValidation-read_completed_validation_evidence'
RBP='ForPrintValidation(read_completed_validation_evidence)'


def inputs(readback=False, timeout=None):
    return ({'provider_id':'github_copilot_cli','model_id':'auto','workspace':'/srv/worker/workspace/repo'},
            {'base_argv':['/usr/local/bin/copilot'], 'prompt':'рядок 1\nline 2 🧪',
             'mcp_config_json':'{"mcpServers":{"ForPrintValidation":{}}}',
             'available_tools':BASE,'permission_patterns':PERMS,
             'readback_tool':RB if readback else None,
             'readback_permission':RBP if readback else None,
             'mcp_server_name':'ForPrintValidation', 'max_ai_credits':30,
             'mcp_timeout_ms':timeout})


def historical_argv(b,t):
    # An independent transcription of the R080 invocation_adapter.py argv.
    return [*t['base_argv'],'-p',t['prompt'],'--silent','--model',b['model_id'],
            '--additional-mcp-config',t['mcp_config_json'],'--available-tools',
            *t['available_tools'],*([t['readback_tool']] if t['readback_tool'] else []),
            '--allow-all-tools','--disable-builtin-mcps','--max-ai-credits',str(t['max_ai_credits']),
            '--no-auto-update','-C',b['workspace']]


def historical_policy(t):
    return {'available_tools':[*t['available_tools'],*([t['readback_tool']] if t['readback_tool'] else [])],
            'mcp_permission_patterns':[*t['permission_patterns'],*([t['readback_permission']] if t['readback_permission'] else [])],
            'permission_mode':'ALLOW_ALL_WITHIN_AVAILABLE_TOOL_UNIVERSE',
            'bash_available':False,'web_available':False,'builtin_mcps_disabled':True,
            'additional_mcp_config_source':'SESSION_ONLY_ARGV',
            'mcp_server_names':['ForPrintValidation'],'mcp_transport':'STDIO_LOCAL',
            'mcp_server_tool_timeout_ms':t['mcp_timeout_ms'],
            'persistent_mcp_config_written':False}


@pytest.mark.parametrize('readback', [False, True])
@pytest.mark.parametrize('timeout', [None, 960000])
@pytest.mark.parametrize('model', ['auto', 'gpt-4.1'])
def test_argv_policy_and_sha256_are_byte_exact_to_legacy(readback,timeout,model):
    binding, task=inputs(readback,timeout);binding['model_id']=model
    result=m.route_invocation(provider_id='github_copilot_cli',binding=binding,frozen_task=task)
    previous=historical_argv(binding,task)
    assert result['argv']==previous
    assert result['provider_policy']==historical_policy(task)
    assert hashlib.sha256('\0'.join(result['argv']).encode()).hexdigest()==hashlib.sha256('\0'.join(previous).encode()).hexdigest()
    assert result['adapter_grants_authority'] is False
    assert result['result_accepted'] is False
    assert result['claim_consumed'] is False
    assert result['process_started'] is False
    assert task['available_tools']==BASE
    assert task['permission_patterns']==PERMS


def test_provider_interface_is_r079_compatible():
    from scripts.coordination.control_plane.worker_runtime import cf10_provider_neutral_boundary_v0_1 as neutral
    assert isinstance(m.CopilotCliAdapter(),neutral.WorkerProviderAdapter)
    assert m.CopilotCliAdapter().inspect_readiness({'provider_id':'github_copilot_cli'})['worker_execution_authorized'] is False


def test_no_codex_or_claude_fallback_even_if_registry_ready():
    b,t=inputs()
    for provider in ('openai_codex_cli','anthropic_claude_code','xai_grok_cli'):
        b2=dict(b,provider_id=provider)
        with pytest.raises(m.AdapterRouteBlocked,match='ADAPTER_NOT_WIRED_NO_FALLBACK'):
            m.route_invocation(provider_id=provider,binding=b2,frozen_task=t)


def test_provider_rebinding_blocked():
    b,t=inputs()
    with pytest.raises(m.AdapterRouteBlocked,match='SELECTED_BINDING_PROVIDER_DRIFT'):
        m.route_invocation(provider_id='openai_codex_cli',binding=b,frozen_task=t)


def test_copilot_normalization_cannot_accept_untrusted_stdout():
    with pytest.raises(m.AdapterRouteBlocked,match='RESULT_NORMALIZATION_REMAINS_CANONICAL'):
        m.CopilotCliAdapter().normalize_result_candidate(b'fake success',{'provider_id':'github_copilot_cli'})


@pytest.mark.parametrize('key,value', [('max_ai_credits',29),('max_ai_credits',True),('readback_tool','mismatch'),('mcp_timeout_ms',0)])
def test_malformed_budget_and_readback_blocked(key,value):
    b,t=inputs()
    t[key]=value
    with pytest.raises(m.AdapterRouteBlocked):
        m.route_invocation(provider_id='github_copilot_cli',binding=b,frozen_task=t)


def test_provider_selection_and_adapter_do_not_mutate_input():
    b,t=inputs(True)
    before=json.dumps(t,sort_keys=True)
    m.route_invocation(provider_id='github_copilot_cli',binding=b,frozen_task=t)
    assert json.dumps(t,sort_keys=True)==before
