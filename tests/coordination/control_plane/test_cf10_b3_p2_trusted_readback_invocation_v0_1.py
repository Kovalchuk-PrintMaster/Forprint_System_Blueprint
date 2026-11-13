"""CF10 B3-P2: independent prelaunch + provider readback-capability opt-in regressions."""
from __future__ import annotations
import copy
import hashlib
import json
import sys
from pathlib import Path
import pytest
import yaml

from scripts.coordination.control_plane import governed_worker_cycle as cycle
from scripts.coordination.control_plane import validation_evidence_readback_selection_v0_1 as r
from scripts.coordination.control_plane.worker_runtime import invocation_adapter as inv

TASK = {"task_prompt_id":"cf10-p2-fixture-task-v0-1",
        "work_front_id":"wf-cf10-p2-fixture-v0-1",
        "work_front_ref":"coordination/work_fronts/cf10_p2_fixture_v0_1.yaml"}
ATTEMPT="cf10-u180j-a998"

def _policy(enabled=False):
    return {
        "schema_version":r.POLICY_SCHEMA,
        "status":"current_standard", "revision":r.POLICY_REVISION,
        "grants_authority":False,"default_enabled":False,
        "capability_id":r.CAPABILITY_ID,
        "opt_in_bindings":[{**TASK,"enabled":True}] if enabled else [],
    }

def _decision(root, *, enabled=False, present=True):
    path=root/r.POLICY_REF;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(yaml.safe_dump(_policy(enabled),sort_keys=False))
    b={**TASK,"attempt_id":ATTEMPT,"workspace_repo":str(root/ATTEMPT/'workspace/repo'),
       "profile_ref":"light-maintenance@r1","procedure_id":"governed_canonical_mutation",
       "training_task_id":"p2-task","training_order":1,
       "runtime_provider":inv.SUPPORTED_PROVIDER,"runtime_model":"auto"}
    prepared={"cf10_training_binding":copy.deepcopy(b),"attempt_id":ATTEMPT}
    if present:
        selection=r.resolve_selection(root=root,task_binding=b)
        prepared["validation_readback_selection"]=copy.deepcopy(selection)
        prepared["validation_readback_policy_sha256"]=selection["policy_sha256"]
        b["validation_readback_selection"]=copy.deepcopy(selection)
    decision={"binding":b}
    _rehash(decision)
    return prepared,decision

def _rehash(decision):
    decision["decision_id"]=hashlib.sha256(json.dumps(
        decision["binding"],sort_keys=True,separators=(",",":")
    ).encode()).hexdigest()

def _verify(root, prepared, decision):
    return cycle._resolve_b3_trusted_readback(
        root=root,prepared_execution=prepared,
        explicit_dispatch_decision=decision,
        expected_task_prompt_id=TASK['task_prompt_id'],
        expected_attempt_id=ATTEMPT,
    )

@pytest.mark.parametrize('enabled',[False,True])
def test_p2_prelaunch_selected_exactly(tmp_path,enabled):
    prepared,decision=_decision(tmp_path,enabled=enabled)
    checked=_verify(tmp_path,prepared,decision)
    assert checked == prepared['validation_readback_selection']
    assert checked['enabled'] is enabled
    assert inv._verify_b3_readback_invocation(
        root=tmp_path,decision=decision,trusted_selection=checked) is enabled


def test_p2_legacy_absence_four_tools(tmp_path):
    prepared,decision=_decision(tmp_path,present=False)
    assert _verify(tmp_path,prepared,decision) is None
    assert not inv._verify_b3_readback_invocation(root=tmp_path,decision=decision,trusted_selection=None)

@pytest.mark.parametrize('mutate',[
    'drop_prepared_selector','drop_prepared_digest','drop_dispatch_selector',
    'alter_dispatch_selector_rehashed','alter_prepared_selector','alter_prepared_digest',
    'alter_policy_bytes','alter_task_identity','alter_attempt_id','alter_decision_id',
    'alter_work_front_rehashed','alter_profile_rehashed',
])
def test_p2_prelaunch_fail_closed(tmp_path,mutate):
    prepared,decision=_decision(tmp_path,enabled=True)
    if mutate=='drop_prepared_selector': prepared.pop('validation_readback_selection')
    elif mutate=='drop_prepared_digest': prepared.pop('validation_readback_policy_sha256')
    elif mutate=='drop_dispatch_selector':
        decision['binding'].pop('validation_readback_selection');_rehash(decision)
    elif mutate=='alter_dispatch_selector_rehashed':
        decision['binding']['validation_readback_selection']['enabled']=False;_rehash(decision)
    elif mutate=='alter_prepared_selector': prepared['validation_readback_selection']['enabled']=False
    elif mutate=='alter_prepared_digest': prepared['validation_readback_policy_sha256']='f'*64
    elif mutate=='alter_policy_bytes': (tmp_path/r.POLICY_REF).write_text(yaml.safe_dump(_policy(False)))
    elif mutate=='alter_task_identity': prepared['cf10_training_binding']['task_prompt_id']='forged'
    elif mutate=='alter_attempt_id': decision['binding']['attempt_id']='fake';_rehash(decision)
    elif mutate=='alter_decision_id': decision['decision_id']='0'*64
    elif mutate=='alter_work_front_rehashed': decision['binding']['work_front_id']='wrong';_rehash(decision)
    elif mutate=='alter_profile_rehashed': decision['binding']['profile_ref']='bad';_rehash(decision)
    with pytest.raises(cycle.GovernedWorkerCycleError): _verify(tmp_path,prepared,decision)

@pytest.mark.parametrize('mutate',[
    'untrusted_enabled','missing_trusted','policy_drift','forged_decision',
    'forged_selector_rehashed','wrong_policy_sha','wrong_front_rehashed',
])
def test_p2_invocation_guard_fail_closed(tmp_path,mutate):
    prepared,decision=_decision(tmp_path,enabled=True)
    selection=copy.deepcopy(prepared['validation_readback_selection'])
    if mutate=='untrusted_enabled':
        decision['binding'].pop('validation_readback_selection');_rehash(decision)
    elif mutate=='missing_trusted': selection=None
    elif mutate=='policy_drift':
        (tmp_path/r.POLICY_REF).write_bytes((tmp_path/r.POLICY_REF).read_bytes()+b'\n# altered\n')
    elif mutate=='forged_decision': decision['decision_id']='0'*64
    elif mutate=='forged_selector_rehashed':
        decision['binding']['validation_readback_selection']['enabled']=False;_rehash(decision)
    elif mutate=='wrong_policy_sha': selection['policy_sha256']='f'*64
    elif mutate=='wrong_front_rehashed': decision['binding']['work_front_id']='bad';_rehash(decision)
    with pytest.raises(inv.WorkerRuntimeInvocationError):
        inv._verify_b3_readback_invocation(root=tmp_path,decision=decision,trusted_selection=selection)


def _plan(monkeypatch,tmp_path,*,enabled=False,present=True):
    prepared,decision=_decision(tmp_path,enabled=enabled,present=present)
    trusted=_verify(tmp_path,prepared,decision)
    attempt=tmp_path/ATTEMPT
    repo=attempt/'workspace/repo'
    mcp=repo/inv.WORKER_VALIDATION_MCP_SCRIPT
    mcp.parent.mkdir(parents=True,exist_ok=True);mcp.write_text('# offline synthetic MCP entrypoint\n')
    config={
        'module_id':'forprint_system_blueprint','provider_adapter':'CONSOLE_COMMAND',
        'command':{'prompt_transport':'provider_adapter_owned','shell':False,
                   'base_argv':[sys.executable]},
        'tool_policy':{'exact_runtime_argv_deferred_to_launch_adapter':True,**{
           key:False for key in (
             'automatic_accept_allowed','canonical_repository_write_allowed',
             'foreign_repository_write_allowed','git_commit_allowed',
             'git_push_allowed','merge_allowed','release_allowed')}},
        'budget':{'provider_specific':{'max_ai_credits':30}},
    }
    runtime={
        'command_representation':'ARGV_NO_SHELL','working_directory':'ATTEMPT_WORKSPACE_REPO',
        'provider_id':inv.SUPPORTED_PROVIDER,'model_id':'auto','executable':sys.executable,
        'timeout_seconds':900,'runtime_id':'synthetic',
    }
    monkeypatch.setattr(inv,'_validate_authority',lambda **kwargs:None)
    monkeypatch.setattr(inv,'_validate_binding',lambda **kwargs:({'task_id':TASK['task_prompt_id']},decision['binding']))
    monkeypatch.setattr(inv,'render_worker_prompt',lambda **kwargs:'synthetic prompt')
    monkeypatch.setattr(inv.registry,'load_module_runtime_config',lambda root:config, raising=False)
    monkeypatch.setattr(inv.registry,'resolve_default_runtime',lambda root:runtime, raising=False)
    ctx={'task_envelope':{'task_id':TASK['task_prompt_id']}}
    plan=inv.build_launch_invocation(root=tmp_path,task_context=ctx,
        explicit_dispatch_decision=decision,attempt_root=attempt,
        validation_readback_selection=trusted)
    argv=plan['argv']
    cfg=json.loads(argv[argv.index('--additional-mcp-config')+1])
    tools=cfg['mcpServers'][inv.WORKER_VALIDATION_MCP_SERVER]
    return plan,tools

@pytest.mark.parametrize('enabled',[False,True])
def test_p2_invocation_wires_mcp_argv_and_permissions(tmp_path,monkeypatch,enabled):
    plan,mcps=_plan(monkeypatch,tmp_path,enabled=enabled)
    expected=['run_validation_suite','run_repo_diff_check','run_repo_head','run_repo_status']
    if enabled: expected.append('read_completed_validation_evidence')
    assert mcps['tools']==expected
    assert ('--enable-completed-readback' in mcps['args']) is enabled
    assert ('ForPrintValidation-read_completed_validation_evidence' in plan['provider_policy']['available_tools']) is enabled
    assert ('ForPrintValidation-read_completed_validation_evidence' in plan['argv']) is enabled
    assert ('ForPrintValidation(read_completed_validation_evidence)' in plan['provider_policy']['mcp_permission_patterns']) is enabled
    assert plan['authority']['automatic_accept_allowed'] is False
    assert plan['authority']['commit_allowed'] is False
    assert plan['effects']['worker_process_started'] is False


def test_p2_historical_invocation_unchanged(tmp_path,monkeypatch):
    plan,mcps=_plan(monkeypatch,tmp_path,present=False)
    assert len(mcps['tools'])==4
    assert '--enable-completed-readback' not in mcps['args']


def test_p2_no_ambient_environment_optin(tmp_path,monkeypatch):
    monkeypatch.setenv('FORPRINT_ENABLE_COMPLETED_READBACK','true')
    plan,mcps=_plan(monkeypatch,tmp_path)
    assert len(mcps['tools'])==4
    assert '--enable-completed-readback' not in mcps['args']


def test_p2_launch_wires_gate_before_started():
    import inspect
    src=inspect.getsource(cycle.launch_cycle)
    assert src.index('_resolve_b3_trusted_readback(')<src.index('_project_native_started_record(')
    assert '"validation_readback_selection": trusted_readback_selection' in src


def test_p2_recovery_tool_remains_non_authorizing():
    src = (Path(__file__).resolve().parents[3] / 'scripts/coordination/control_plane/worker_runtime/worker_validation_mcp.py').read_text()
    assert 'COMPLETED_VALIDATION_READBACK_SCHEMA' in src
    assert 'if not enable_completed_readback:' in src
    assert 'readback accepts no Worker parameters' in src
