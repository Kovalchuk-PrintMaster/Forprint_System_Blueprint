"""R129: source-only convergence checks; no claim/systemd/Worker on import."""
from __future__ import annotations
from copy import deepcopy
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_r129_canonical_lifecycle_convergence_v0_1 as r129


def fixture():
    c, e = r129.synthetic_fixture()
    return deepcopy(c), deepcopy(e)


def updated_candidate(c):
    c['candidate_sha256'] = r129.sha({k: v for k, v in c.items() if k != 'candidate_sha256'})
    return c


def test_synthetic_end_to_end_non_authorizing():
    c, events = fixture()
    report = r129.convergence(c, events)
    assert report['source_only_trace_valid'] is True
    assert report['mode'] == 'SYNTHETIC_ONLY_NON_AUTHORIZING'
    assert report['synthetic_event_count'] == 11
    assert len(report['open_boundaries']) == 6
    assert report['authority'] == {
       'live_worker_allowed': False, 'claim_consumed': False,
       'root_release_granted': False, 'automatic_retry': False,
       'tool_cancellation_attested': False, 'g1_g5_closed': False,
    }
    expected = dict(report)
    assert expected.pop('report_sha256') == r129.sha(expected)


def test_determinism():
    c, e = fixture()
    assert r129.convergence(c, e) == r129.convergence(*fixture())


@pytest.mark.parametrize('key', ['attempt_id', 'task_id', 'work_front_id', 'decision_id', 'epoch', 'source_head', 'capsule_id'])
def test_reject_candidate_identity_or_pin(key):
    c, e = fixture()
    c[key] = 'WRONG'
    updated_candidate(c)
    with pytest.raises(r129.ConvergenceHold): r129.convergence(c, e)


@pytest.mark.parametrize('key', ['canonical_invocation_sha256', 'canonical_argv_sha256', 'r123_binding_sha256'])
def test_reject_candidate_digests(key):
    c, e = fixture()
    c[key] = 'n' * 64
    updated_candidate(c)
    with pytest.raises(r129.ConvergenceHold): r129.convergence(c, e)


def test_reject_candidate_hash_tamper():
    c, e = fixture()
    c['work_front_id'] = 'changed-but-valid'
    with pytest.raises(r129.ConvergenceHold, match='CANDIDATE_DIGEST'):
        r129.convergence(c, e)


def test_reject_live_cutover_even_with_positive_trace():
    c, e = fixture()
    with pytest.raises(r129.ConvergenceHold, match='LIVE_CUTOVER'):
        r129.convergence(c, e, live_cutover_enabled=True)


@pytest.mark.parametrize('key', ['live_worker', 'claim_consumed', 'release_granted', 'candidate_executable_in_current_R115', 'ipc_broker_launched', 'g1_g5_closed'])
def test_reject_candidate_authority(key):
    c, e = fixture()
    c['authority'][key] = True
    updated_candidate(c)
    with pytest.raises(r129.ConvergenceHold, match='CANDIDATE_AUTHORITY'):
        r129.convergence(c, e)


@pytest.mark.parametrize('tools', [['run_repo_head','run_repo_status'],['run_validation_suite'],[],['run_repo_head','run_repo_head']])
def test_reject_widened_proxy_tools(tools):
    c, e = fixture()
    c['candidate_mcp_config']['mcpServers']['ForPrintValidation']['tools'] = tools
    updated_candidate(c)
    with pytest.raises(r129.ConvergenceHold, match='MODEL_TOOL_ALLOWLIST'):
        r129.convergence(c, e)


@pytest.mark.parametrize('slot,value',[(2,'/tmp/unsafe.sock'),(4,'cf10-other'),(6,'other-epoch'),(8,'b'*40),(10,'wrong-capsule')])
def test_reject_wrong_proxy_binding(slot, value):
    c, e = fixture()
    c['candidate_mcp_config']['mcpServers']['ForPrintValidation']['args'][slot] = value
    updated_candidate(c)
    with pytest.raises(r129.ConvergenceHold, match='PROXY_BINDING'):
        r129.convergence(c, e)


@pytest.mark.parametrize('position', range(len(r129.STEPS)))
def test_reject_wrong_transition(position):
    c, e = fixture()
    e[position]['step'] = 'FAKE_STEP'
    with pytest.raises(r129.ConvergenceHold, match='EVENT_SEQUENCE'):
        r129.convergence(c, e)


def test_reject_transition_swap():
    c, e = fixture()
    e[4], e[5] = e[5], e[4]
    with pytest.raises(r129.ConvergenceHold, match='EVENT_SEQUENCE'):
        r129.convergence(c, e)


@pytest.mark.parametrize('key', ['attempt_id', 'epoch', 'source_head', 'unit'])
def test_reject_inconsistent_ledger_identity(key):
    c, e = fixture()
    e[9][key] = 'changed'
    with pytest.raises(r129.ConvergenceHold, match='EVENT_BINDING'):
        r129.convergence(c, e)


@pytest.mark.parametrize('origin', ['provider', 'worker', 'operator'])
def test_root_revoke_must_be_external(origin):
    c, e = fixture()
    e[7]['origin'] = origin
    with pytest.raises(r129.ConvergenceHold, match='EVENT_SEQUENCE'):
        r129.convergence(c, e)


def test_reject_false_kernel_empty():
    c, e = fixture()
    e[8]['cgroup_populated'] = 'UNKNOWN'
    with pytest.raises(r129.ConvergenceHold, match='KERNEL_QUIESCENCE'):
        r129.convergence(c, e)


def test_reject_missing_witness_transition():
    c, e = fixture()
    e[8]['kernel_transition'] = 'NOT_WITNESSED'
    with pytest.raises(r129.ConvergenceHold, match='KERNEL_QUIESCENCE'):
        r129.convergence(c, e)


@pytest.mark.parametrize('status,accepted',[('COMPLETED', False),('REVIEW_REQUIRED',True),('ACCEPTED',True)])
def test_terminal_not_automatic_acceptance(status,accepted):
    c, e = fixture()
    e[9]['terminal_status'], e[9]['result_accepted'] = status, accepted
    with pytest.raises(r129.ConvergenceHold, match='TERMINAL_IS_NOT_ACCEPTANCE'):
        r129.convergence(c, e)


def test_reject_missing_review():
    c, e = fixture()
    with pytest.raises(r129.ConvergenceHold, match='TRACE_LENGTH'):
        r129.convergence(c, e[:-1])


def test_reject_extra_unreviewed_event_field():
    c, e = fixture()
    e[3]['release_allowed'] = True
    with pytest.raises(r129.ConvergenceHold, match='EVENT_KEYS'):
        r129.convergence(c, e)


def test_reject_real_claimed_events():
    c, e = fixture()
    e[5]['synthetic'] = False
    with pytest.raises(r129.ConvergenceHold, match='EVENT_SEQUENCE'):
        r129.convergence(c, e)


def test_reject_invalid_tool_evidence():
    c, e = fixture()
    e[6]['evidence_digest'] = 'empty'
    with pytest.raises(r129.ConvergenceHold, match='READONLY_TOOLCALL_DIGEST'):
        r129.convergence(c, e)


def test_no_worker_or_implicit_privilege_in_source():
    from pathlib import Path
    source = Path(r129.__file__).read_text()
    assert 'LIVE_CUTOVER_ENABLED=False' in source
    assert 'source_only_trace_valid' in source
    assert 'tool_cancellation_attested' in source
    assert r129.SOURCE_BLOBS['scripts/coordination/control_plane/worker_runtime/cf10_systemd_terminal_bridge_v0_1.py']
