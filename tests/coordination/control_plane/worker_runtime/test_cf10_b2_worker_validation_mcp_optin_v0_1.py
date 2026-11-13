"""B2 optional informational Worker MCP: default hidden, exact identity binding."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

mcp_types = pytest.importorskip('mcp.types')
from scripts.coordination.control_plane.worker_runtime import worker_validation_mcp as module


def binding(tmp_path):
    attempt = tmp_path / 'cf10-u180j-fixture-a001'
    repo = attempt / 'workspace/repo'
    ev = attempt / 'evidence/structured_command'
    repo.mkdir(parents=True); ev.mkdir(parents=True)
    return {
        'attempt_id': attempt.name,
        'task_id': 'fixture-task', 'work_front_id': 'fixture-front',
        'decision_id': 'd' * 64, 'workspace_repo': str(repo),
        'evidence_root': str(ev),
    }


def tools(server):
    h = server.get_request_handler('tools/list').handler
    return asyncio.run(h(None, None)).tools


def call(server, name, args):
    h = server.get_request_handler('tools/call').handler
    params = mcp_types.CallToolRequestParams.model_validate({
        '_meta': {}, 'name': name, 'arguments': args,
    })
    return asyncio.run(h(None, params))


def test_optin_default_hidden_and_cannot_be_called(tmp_path):
    server = module.build_server(**binding(tmp_path))
    assert [t.name for t in tools(server)] == [
        'run_validation_suite', 'run_repo_diff_check', 'run_repo_head', 'run_repo_status',
    ]
    result = call(server, 'read_completed_validation_evidence', {})
    assert result.is_error is True


def test_optin_requires_trusted_boolean(tmp_path):
    with pytest.raises(module.WorkerValidationMCPError):
        module.build_server(**binding(tmp_path), enable_completed_readback='yes')


def test_optin_shows_fifth_tool_and_never_executes(tmp_path, monkeypatch):
    b = binding(tmp_path)
    server = module.build_server(**b, enable_completed_readback=True)
    names = [t.name for t in tools(server)]
    assert names[-1] == 'read_completed_validation_evidence'
    assert len(names) == 5
    called = []
    def forbid(**kwargs):
        raise AssertionError('executor was invoked in readback')
    monkeypatch.setattr(module.structured_executor, 'build_execution_plan', forbid)
    monkeypatch.setattr(module.structured_executor, 'execute_execution_plan', forbid)
    def verified_discovery(**kwargs):
        called.append(kwargs)
        return {
            'status': 'PASS_NON_AUTHORIZING', 'acceptance_granted': False,
            'replay_skip_authorized': False, 'verified_completed_validation': [],
        }
    monkeypatch.setattr(module, 'discover_completed_validation_evidence', verified_discovery)
    result = call(server, 'read_completed_validation_evidence', {})
    assert result.is_error is False
    assert result.structured_content['replay_skip_authorized'] is False
    assert called == [{
        'attempt_root': str(Path(b['workspace_repo']).parent.parent),
        'expected_task_id': b['task_id'],
        'expected_work_front_id': b['work_front_id'],
        'expected_decision_id': b['decision_id'],
        'expected_workspace': b['workspace_repo'],
    }]


def test_optin_rejects_worker_paths_and_hidden_parameters(tmp_path, monkeypatch):
    b = binding(tmp_path)
    server = module.build_server(**b, enable_completed_readback=True)
    called = []
    monkeypatch.setattr(module, 'discover_completed_validation_evidence',
                        lambda **kw: called.append(kw))
    for arg in ({'execution_id': 'structured-exec-' + '0'*20},
                {'attempt_root': '/tmp/attacker'}, {'skip_tests': True}):
        result = call(server, 'read_completed_validation_evidence', arg)
        assert result.is_error is True
    assert called == []


def test_optin_fails_closed_on_wrong_evidence_root(tmp_path, monkeypatch):
    b = binding(tmp_path)
    fake = tmp_path / 'unrelated-evidence'
    fake.mkdir()
    b['evidence_root'] = str(fake)
    server = module.build_server(**b, enable_completed_readback=True)
    called = []
    monkeypatch.setattr(module, 'discover_completed_validation_evidence',
                        lambda **kw: called.append(kw))
    result = call(server, 'read_completed_validation_evidence', {})
    assert result.is_error is True
    assert called == []
