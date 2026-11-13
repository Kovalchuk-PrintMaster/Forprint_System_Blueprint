"""R087: source-only Codex candidate. Never spawn, authenticate or launch."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

# This test runs both after installation and in an entirely isolated bundle.
MODULE = Path(__file__).resolve().parents[4] / 'scripts/coordination/control_plane/worker_runtime/cf10_r087_codex_cli_candidate_v0_1.py'
spec = importlib.util.spec_from_file_location('cf10_r087_codex_candidate_fixture', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def bind(**changes):
    value = {
        'provider_id': 'openai_codex_cli', 'model_id': 'codex-fixture-model',
        'attempt_id': 'cf10-u180j-a995', 'worker_id': 'worker-01',
        'source_head': 'a'*40,
        'executable': '/opt/forprint/codex/bin/codex',
        'runtime_root': '/srv/software_development/forprint-worker-runtime',
        'workspace': '/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/cf10-u180j-a995/workspace/repo',
        'execution_authorized': False, 'provider_ready': False,
        'claim_consumed': False, 'automatic_retry': False, 'automatic_fallback': False,
    }
    value.update(changes)
    return value


def task(**changes):
    value = {'prompt': 'Candidate-only; never execute.',
             'result_transport': 'CANONICAL_HANDOFF_PENDING_ADAPTER_PROOF'}
    value.update(changes)
    return value


def test_readiness_requires_exact_codex_provider_and_never_ready():
    r=m.inspect_readiness(bind())
    assert r['registered_state']=='NOT_CONFIGURED'
    assert r['provider_ready'] is False
    assert r['live_dispatch_wired'] is False
    with pytest.raises(m.CodexCandidateBlocked,match='PROVIDER_ID_MISMATCH'):
        m.inspect_readiness(bind(provider_id='anthropic_claude_code'))


def test_argv_uses_explicit_model_readonly_ephemeral_jsonl_and_stdin_no_secret():
    plan=m.build_invocation(bind(),task())
    argv=plan['argv']
    assert argv[:3] == ['/opt/forprint/codex/bin/codex','exec','--json']
    assert argv[-1] == '-'
    assert argv[argv.index('--model')+1]=='codex-fixture-model'
    assert argv[argv.index('--sandbox')+1]=='read-only'
    assert argv[argv.index('--cd')+1]==bind()['workspace']
    assert '--ephemeral' in argv and '--ignore-user-config' in argv
    assert '--ignore-rules' in argv
    assert not any(x in argv for x in ('--add-dir','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check','--config','workspace-write','danger-full-access'))
    assert plan['stdin_transport']=='UNOPENED_PIPE_PLACEHOLDER'
    assert plan['candidate_only'] and plan['result_accepted'] is False
    assert all(plan[x] is False for x in ('adapter_grants_authority','claim_consumed','process_started','automatic_fallback','automatic_retry'))
    assert not any('Candidate-only; never execute.' in x for x in argv)


def test_argv_deterministic_and_prompt_bound_by_digest_not_exposed():
    p1=m.build_invocation(bind(),task())
    p2=m.build_invocation(bind(),task())
    assert p1==p2
    assert p1['prompt_sha256']==hashlib.sha256(task()['prompt'].encode()).hexdigest()
    assert 'Candidate-only' not in json.dumps(p1)
    assert p1['argv_sha256']==hashlib.sha256(json.dumps(p1['argv'],separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def test_prompt_digest_mismatch_fails():
    with pytest.raises(m.CodexCandidateBlocked,match='FROZEN_PROMPT_SHA_DRIFT'):
        m.build_invocation(bind(),task(prompt_sha256='0'*64))


def test_correct_prompt_digest_allowed():
    prompt=task()['prompt']
    assert m.build_invocation(bind(),task(prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest()))['candidate_only']


@pytest.mark.parametrize('bad',[None,'','auto','bad model','--dangerously-bypass-approvals-and-sandbox','../codex','q'*81])
def test_model_must_be_explicit_safe_token(bad):
    with pytest.raises(m.CodexCandidateBlocked,match='EXPLICIT_MODEL_REQUIRED'):
        m.build_invocation(bind(model_id=bad),task())


@pytest.mark.parametrize('field,bad',[('provider_id','github_copilot_cli'),('attempt_id','cf10-u180j-a1'),('worker_id','root'),('source_head','a'*39),('executable','codex'),('workspace','/tmp/escape'),('runtime_root','relative')])
def test_binding_rejects_wrong_provider_attempt_or_path(field,bad):
    with pytest.raises(m.CodexCandidateBlocked):
        m.build_invocation(bind(**{field:bad}),task())


@pytest.mark.parametrize('field',[ 'execution_authorized', 'provider_ready', 'claim_consumed', 'automatic_retry', 'automatic_fallback'])
def test_authority_widening_fails(field):
    with pytest.raises(m.CodexCandidateBlocked,match='AUTHORITY_BOUNDARY'):
        m.build_invocation(bind(**{field: True}),task())


def test_workspace_traversal_or_duplicate_slash_fails():
    for name in ('/opt/forprint/../bin/codex','/opt//forprint/bin/codex','/opt/forprint/./codex'):
        with pytest.raises(m.CodexCandidateBlocked):
            m.build_invocation(bind(executable=name),task())


def test_canonical_repo_as_workspace_forbidden():
    with pytest.raises(m.CodexCandidateBlocked):
        m.build_invocation(bind(runtime_root='/srv/software_development/forprint-project',workspace='/srv/software_development/forprint-project/forprint_system_blueprint/worker-01/cf10-u180j-a995/workspace/repo'),task())


def test_prompt_transport_requires_canonical_handoff_pending():
    with pytest.raises(m.CodexCandidateBlocked,match='RESULT_TRANSPORT_NOT_BOUND'):
        m.build_invocation(bind(),task(result_transport='stdout_directly_accept'))


def test_result_normalization_denied_even_well_formed_jsonl():
    stream=b'{"type":"thread.started","thread_id":"x"}\n{"type":"turn.completed"}\n'
    with pytest.raises(m.CodexCandidateBlocked,match='CANONICAL_HANDOFF_NORMALIZATION_NOT_IMPLEMENTED'):
        m.CodexCliCandidateAdapter().normalize_result_candidate(stream,bind())


def test_sanitized_event_observation_never_accepts_result():
    stream=b'{"type":"thread.started","thread_id":"x"}\n{"type":"item.completed","item":{"text":"SECRET"}}\n{"type":"turn.completed","usage":{"input_tokens":99}}\n'
    result=m.observe_jsonl_candidate(stream,bind())
    assert result['event_counts']['turn.completed']==1
    assert result['result_accepted'] is False
    assert result['handoff_result_validated'] is False
    assert result['canonical_ledger_written'] is False
    assert 'SECRET' not in json.dumps(result)


@pytest.mark.parametrize('stream',[b'',b'[]\n',b'{"type":"unknown"}\n',b'{"type":"turn.failed"}\n',b'{"type":"turn.completed"}\n{"type":"turn.completed"}\n',b'{"type":"thread.started"}\n',b'not json\n'])
def test_jsonl_malformed_unknown_failure_or_no_completion_blocks(stream):
    with pytest.raises(m.CodexCandidateBlocked):
        m.observe_jsonl_candidate(stream,bind())


def test_jsonl_oversize_and_line_length_fails():
    with pytest.raises(m.CodexCandidateBlocked):
        m.observe_jsonl_candidate(b'a'*(m.MAX_JSONL_BYTES+1),bind())
    with pytest.raises(m.CodexCandidateBlocked):
        m.observe_jsonl_candidate(b'a'*(m.MAX_LINE_BYTES+1),bind())


def test_registered_codex_remains_unconfigured_and_router_copilot_only_if_repo_available():
    root=Path(__file__).resolve().parents[4]
    registry=root/'coordination/registry/worker_runtime_adapters_v0_1.yaml'
    router=root/'scripts/coordination/control_plane/worker_runtime/cf10_r081_provider_adapter_v0_1.py'
    if not registry.is_file() or not router.is_file():
        pytest.skip('isolated package: full repo unavailable')
    import yaml
    data=yaml.safe_load(registry.read_text())
    codex=next(p for p in data['providers'] if p['provider_id']=='openai_codex_cli')
    assert codex['state']=='NOT_CONFIGURED' and codex['ready'] is False
    assert codex['executable'] is None and codex['auth'] is None
    assert 'openai_codex_cli' not in router.read_text(encoding='utf-8')


def test_no_process_or_os_network_calls_in_source():
    raw=MODULE.read_text(encoding='utf-8')
    assert 'subprocess' not in raw and 'os.system' not in raw and 'Popen' not in raw
    assert 'import requests' not in raw and 'urllib' not in raw
