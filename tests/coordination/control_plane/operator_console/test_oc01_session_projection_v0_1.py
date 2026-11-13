from __future__ import annotations

import pytest
from scripts.coordination.control_plane.operator_console.session_projection import ALLOWED_ACTOR_TYPES, SessionProjectionError, build_session_projection


def launch():
    return {"identity": {"module_id": "forprint_system_blueprint", "prompt_id": "oc01-example"}}


def invocation():
    return {"attempt_id": "cf10-u180j-a999", "worker_id": "worker-01", "workspace_repo": "/tmp/runtime/worker-01/cf10-u180j-a999/workspace/repo", "heartbeat_seconds": 15}


def manifest():
    return {"schema_version": "forprint_worker_workspace_manifest_v0_1", "attempt_id": "cf10-u180j-a999", "workspace_repo": "/tmp/runtime/worker-01/cf10-u180j-a999/workspace/repo", "canonical_write_allowed": False, "source_head": "a" * 40, "source_state_fingerprint": "b" * 64, "workspace_state": "PROVISIONED_NOT_DISPATCHED"}


@pytest.mark.parametrize("actor_type", sorted(ALLOWED_ACTOR_TYPES))
def test_actor_types_remain_authority_neutral(actor_type):
    p = build_session_projection(launch_request=launch(), worker_invocation=invocation(), actor_type=actor_type, actor_id="actor-01")
    assert p["actor"]["authority_conferred"] is False
    assert all(value is False for value in p["authority"].values())
    assert p["write_readiness"]["canonical_write_ready"] is False
    assert p["session"]["canonical_session_state"] == "DEPENDENCY_PENDING_CF10"
    assert p["session"]["exclusive_module_lease"] == "DEPENDENCY_PENDING_CF10"


def test_identity_and_workspace_manifest_are_reused():
    p = build_session_projection(launch_request=launch(), worker_invocation=invocation(), actor_type="operator_assistant", actor_id="assistant-01", workspace_manifest=manifest())
    assert p["execution_identity"]["attempt_id"] == "cf10-u180j-a999"
    assert p["execution_identity"]["worker_id"] == "worker-01"
    assert p["workspace"]["binding_state"] == "MANIFEST_BOUND"
    assert p["workspace"]["source_head"] == "a" * 40
    assert p["workspace"]["canonical_write_allowed_by_oc01"] is False


def test_heartbeat_configuration_is_not_session_authority():
    p = build_session_projection(launch_request=launch(), worker_invocation=invocation(), actor_type="internal_worker", actor_id="worker-01")
    assert p["heartbeat"]["configuration_observed"] is True
    assert p["heartbeat"]["session_authority"] is False
    assert p["heartbeat"]["lease_authority"] is False


def test_invalid_actor_rejected():
    with pytest.raises(SessionProjectionError, match="unsupported actor_type"):
        build_session_projection(launch_request=launch(), worker_invocation=invocation(), actor_type="superuser", actor_id="actor")


def test_missing_identity_rejected():
    with pytest.raises(SessionProjectionError, match="launch_request.identity"):
        build_session_projection(launch_request={}, worker_invocation=invocation(), actor_type="human_terminal", actor_id="human")


def test_workspace_attempt_mismatch_rejected():
    m = manifest(); m["attempt_id"] = "other"
    with pytest.raises(SessionProjectionError, match="attempt_id mismatch"):
        build_session_projection(launch_request=launch(), worker_invocation=invocation(), actor_type="human_terminal", actor_id="human", workspace_manifest=m)


def test_workspace_canonical_write_true_rejected():
    m = manifest(); m["canonical_write_allowed"] = True
    with pytest.raises(SessionProjectionError, match="canonical_write_allowed must remain false"):
        build_session_projection(launch_request=launch(), worker_invocation=invocation(), actor_type="operator_assistant", actor_id="assistant", workspace_manifest=m)


def test_projection_has_no_execution_side_effects():
    p = build_session_projection(launch_request=launch(), worker_invocation=invocation(), actor_type="human_terminal", actor_id="human")
    assert all(value is False for value in p["execution_boundaries"].values())
