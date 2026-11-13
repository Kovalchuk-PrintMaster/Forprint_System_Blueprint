"""R134: prospective IPC never becomes a production R115 preclaim."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import pytest

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r115_preclaim_executable_profile_v0_1 as r115,
    cf10_r127_canonical_ipc_cutover_candidate_v0_1 as r127,
    cf10_r129_canonical_lifecycle_convergence_v0_1 as r129,
    cf10_r134_ipc_preclaim_crosswalk_v0_1 as r134,
)


def source_pair():
    c, _ = r129.synthetic_fixture()
    attempt = c['attempt_id']
    workspace = str(r115.PILOT_MCP_BASE_WORKSPACE / attempt / 'workspace' / 'repo')
    old_tools = ['run_validation_suite','run_repo_diff_check','run_repo_head','run_repo_status']
    old_spec = {
      'type': 'local',
      'command': str(r129.REPO / '.venv_blueprint/bin/python'),
      'args': [str(Path(workspace) / r115.PILOT_MCP_SCRIPT),
               '--attempt-id',attempt,'--task-id','cf10-task-r134',
               '--work-front-id','cf10','--decision-id','d'*64,
               '--workspace-repo',workspace,'--evidence-root',
               str(r115.PILOT_MCP_BASE_WORKSPACE / attempt / 'evidence' / 'structured_command')],
      'cwd': workspace,'tools': old_tools,
    }
    argv = [str(r115.COPILOT_PILOT_PATH), '-p','fixture prompt', '--silent','--model','auto',
            '--additional-mcp-config',json.dumps({'mcpServers':{'ForPrintValidation':old_spec}},sort_keys=True),
            '--available-tools','view','edit','apply_patch',
            *['ForPrintValidation-'+t for t in old_tools],
            '--allow-all-tools','--disable-builtin-mcps','--max-ai-credits','30',
            '--no-auto-update','--sandbox','-C',workspace]
    r115.assert_frozen_argv(argv,workspace)
    r115.assert_static_tool_and_mcp_boundary(argv,workspace)
    inv = {
        'schema_version':'forprint_worker_runtime_launch_invocation_v0_1',
        'provider_id':'github_copilot_cli','command_representation':'ARGV_NO_SHELL',
        'attempt_id':attempt,'task_id':'cf10-task-r134', 'work_front_id':'cf10',
        'decision_id':'d'*64,'workspace_repo':workspace,
        'argv':argv,'argv_sha256':hashlib.sha256('\0'.join(argv).encode()).hexdigest(),
        'invocation_sha256':'b'*64,'authority':{'adapter_grants_authority':False},
        'effects':{'worker_process_started':False},
    }
    c['task_id'] = inv['task_id']
    c['work_front_id'] = inv['work_front_id']
    c['decision_id'] = inv['decision_id']
    c['canonical_invocation_sha256'] = inv['invocation_sha256']
    c['canonical_argv_sha256'] = inv['argv_sha256']
    spec = c['candidate_mcp_config']['mcpServers']['ForPrintValidation']
    spec['cwd'] = workspace
    spec['command'] = str(r129.REPO / '.venv_blueprint/bin/python')
    spec['args'][0] = str(r129.REPO / r129.PROXY)
    c['candidate_sha256'] = r129.sha({k:v for k,v in c.items() if k!='candidate_sha256'})
    r129.validate_r127_candidate(c)
    return inv, c


def test_review_source_crosswalk_success_but_never_live():
    inv,c=source_pair()
    result = r134.verify_source_only(invocation=inv,candidate=c)
    assert result['status'] == r134.REVIEW_ONLY
    assert result['candidate_sha256']==c['candidate_sha256']
    assert result['original_argv_sha256']!=result['review_only_argv_sha256']
    assert result['model_tools']==['ForPrintValidation-run_repo_head']
    assert result['legacy_r115_rejects_prospective_argv'] is True
    assert all(result[k] is False for k in (
      'root_lease_attested','credential_egress_attested','copilot_sandbox_attested',
      'kernel_witness_attested','terminal_ledger_attested','live_cutover_authorized',
      'claim_consumed','worker_started','automatic_retry'))
    assert result['report_sha256']==r134._sha_doc({k:v for k,v in result.items() if k!='report_sha256'})


def test_deterministic_no_credentials_exposed():
    inv,c=source_pair()
    assert r134.verify_source_only(invocation=inv,candidate=c)==r134.verify_source_only(invocation=inv,candidate=c)
    result=r134.verify_source_only(invocation=inv,candidate=c)
    assert 'fixture prompt' not in json.dumps(result)
    assert '--additional-mcp-config' not in json.dumps(result)


@pytest.mark.parametrize('target,key,value',[
    ('inv','attempt_id','cf10-other-a997'),
    ('inv','task_id','another-task'),
    ('inv','decision_id','0'*64),
    ('inv','work_front_id','another'),
    ('inv','workspace_repo','/tmp/fake'),
    ('inv','invocation_sha256','f'*64),
    ('inv','argv_sha256','f'*64),
    ('inv','provider_id','other-ai'),
    ('inv','command_representation','SHELL'),
    ('c','capsule_id','other'),
    ('c','candidate_sha256','f'*64),
    ('c','source_head','notsha'),
    ('c','epoch','../../wrong'),
])
def test_identity_and_digest_drift_holds(target,key,value):
    inv,c=source_pair()
    (inv if target=='inv' else c)[key]=value
    with pytest.raises(r134.IPCPreclaimHold):r134.verify_source_only(invocation=inv,candidate=c)


@pytest.mark.parametrize('key,value',[
   ('command','/usr/bin/python'),
   ('command','/bin/sh'),
   ('cwd','/tmp/wrong'),
   ('tools',['run_validation_suite']),
   ('tools',['run_repo_head','run_repo_status']),
   ('args',[]),
])
def test_new_proxy_scope_holds(key,value):
    inv,c=source_pair()
    c['candidate_mcp_config']['mcpServers']['ForPrintValidation'][key]=value
    c['candidate_sha256']=r129.sha({k:v for k,v in c.items() if k!='candidate_sha256'})
    with pytest.raises(r134.IPCPreclaimHold):r134.verify_source_only(invocation=inv,candidate=c)


@pytest.mark.parametrize('index,value',[
    (0,'/usr/local/bin/copilot'),
    (2,'changed prompt'),
    (7,'{}'),
    (9,'Bash'),
    (-1,'/tmp/evil'),
    (-4,'--no-sandbox'),
])
def test_existing_argv_mutation_denied(index,value):
    inv,c=source_pair()
    inv['argv'][index]=value
    with pytest.raises(r134.IPCPreclaimHold):r134.verify_source_only(invocation=inv,candidate=c)


def test_extra_candidate_env_disallowed_even_if_rehashed():
    inv,c=source_pair()
    c['candidate_mcp_config']['mcpServers']['ForPrintValidation']['env']={'TOKEN':'fake'}
    c['candidate_sha256']=r129.sha({k:v for k,v in c.items() if k!='candidate_sha256'})
    with pytest.raises(r134.IPCPreclaimHold):r134.verify_source_only(invocation=inv,candidate=c)


def test_authority_widened_denied():
    inv,c=source_pair()
    inv['authority']['adapter_grants_authority']=True
    with pytest.raises(r134.IPCPreclaimHold):r134.verify_source_only(invocation=inv,candidate=c)


def test_r127_real_builder_calls_preclaim_crosswalk_fail_closed():
    code=Path(r127.__file__).read_text('utf8')
    assert 'r134.verify_source_only(invocation=invocation, candidate=candidate)' in code
    assert 'deny(\'R134_PRECLAIM_CROSSWALK\')' in code
    assert code.index('r134.verify_source_only(')>code.index('candidate = render_review_candidate(')


def test_no_runtime_authority_in_crosswalk():
    code=Path(r134.__file__).read_text('utf8')
    for forbidden in ('subprocess.Popen','systemd-run','revoke_lease(','.append_observation(','git push','LIVE_CUTOVER_ENABLED=True'):
        assert forbidden not in code
    inv,c=source_pair()
    assert r134.verify_source_only(invocation=inv,candidate=c)['live_cutover_authorized'] is False
