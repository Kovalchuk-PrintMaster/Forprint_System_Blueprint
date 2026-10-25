"""Tests first: independent CF-10 B3 P0/P1 selector, no MCP activation."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane import validation_evidence_readback_selection_v0_1 as r
from scripts.coordination.control_plane import cf10_training_dispatch as training


IDENTITY = {
    "task_prompt_id": "cf10-fixture-task-v0-1",
    "work_front_id": "wf-cf10-fixture-v0-1",
    "work_front_ref": "coordination/work_fronts/fixture_v0_1.yaml",
}
ATTEMPT = "cf10-u180j-a999"


def policy() -> dict:
    return {
        "schema_version": r.POLICY_SCHEMA, "status": "current_standard",
        "revision": r.POLICY_REVISION, "grants_authority": False,
        "default_enabled": False, "capability_id": r.CAPABILITY_ID,
        "opt_in_bindings": [],
    }


def add_optin(doc: dict, identity=IDENTITY):
    doc["opt_in_bindings"].append({**identity, "enabled": True})
    return doc


def write(root: Path, doc: dict | None = None) -> Path:
    p = root / r.POLICY_REF
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(policy() if doc is None else doc, sort_keys=False))
    return p


def test_default_off_exact_bytes(tmp_path):
    p = write(tmp_path)
    output = r.resolve_selection(root=tmp_path, task_binding=IDENTITY)
    assert output["enabled"] is False
    assert output["capability_id"] == "validation_evidence_readback"
    assert output["policy_sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert all(output[k] == v for k, v in IDENTITY.items())


def test_optin_exact_identity(tmp_path):
    write(tmp_path, add_optin(policy()))
    assert r.resolve_selection(root=tmp_path, task_binding=IDENTITY)["enabled"] is True


@pytest.mark.parametrize("key", list(IDENTITY))
def test_partial_optin_identity_refused(tmp_path, key):
    changed = dict(IDENTITY)
    changed[key] = ("wf-cf10-changed" if key == "work_front_id" else
                    "coordination/work_fronts/changed.yaml" if key == "work_front_ref"
                    else "different-task")
    write(tmp_path, add_optin(policy(), changed))
    with pytest.raises(r.ReadbackSelectionError, match="partial"):
        r.resolve_selection(root=tmp_path, task_binding=IDENTITY)


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(grants_authority=True),
    lambda d: d.update(default_enabled=True),
    lambda d: d.update(revision="99"),
    lambda d: d.update(status="draft"),
    lambda d: d.update(capability_id="shell"),
    lambda d: d.update(extra="unexpected"),
    lambda d: d.update(opt_in_bindings={}),
    lambda d: d.update(opt_in_bindings=[{"enabled": True}]),
    lambda d: d.update(opt_in_bindings=[{**IDENTITY, "enabled": "true"}]),
    lambda d: d.update(opt_in_bindings=[{**IDENTITY, "enabled": True}] * 2),
])
def test_invalid_policy_fail_closed(mutate):
    p = policy()
    mutate(p)
    with pytest.raises(r.ReadbackSelectionError):
        r.validate_policy(p)


def test_duplicate_yaml_keys_refused(tmp_path):
    p = write(tmp_path)
    p.write_text(p.read_text() + "default_enabled: true\n")
    with pytest.raises(r.ReadbackSelectionError, match="duplicate"):
        r.load_policy(tmp_path)


def test_symlink_and_missing_policy_refused(tmp_path):
    with pytest.raises(r.ReadbackSelectionError, match="missing"):
        r.resolve_selection(root=tmp_path, task_binding=IDENTITY)
    external = tmp_path / "external.yaml"
    external.write_text(yaml.safe_dump(policy()))
    link = tmp_path / r.POLICY_REF
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(external)
    with pytest.raises(r.ReadbackSelectionError, match="unsafe"):
        r.load_policy(tmp_path)


def test_missing_legacy_remains_unselected_but_explicit_missing_rejected(tmp_path):
    assert r.resolve_if_registered(root=tmp_path, task_binding=IDENTITY) is None
    assert r.verify_frozen_selection(root=tmp_path, execution={}, task_binding=IDENTITY) is None
    with pytest.raises(r.ReadbackSelectionError):
        r.verify_frozen_selection(root=tmp_path, execution={
            "validation_readback_selection": {"enabled": True},
            "validation_readback_policy_sha256": "a" * 64,
        }, task_binding=IDENTITY)


@pytest.mark.parametrize("tamper", [
    "missing_selection", "missing_digest", "changed_enabled", "changed_sha",
    "changed_identity", "changed_policy_bytes",
])
def test_frozen_selector_integrity(tmp_path, tamper):
    p = write(tmp_path)
    selected = r.resolve_selection(root=tmp_path, task_binding=IDENTITY)
    state = {
        "validation_readback_selection": copy.deepcopy(selected),
        "validation_readback_policy_sha256": selected["policy_sha256"],
    }
    assert r.verify_frozen_selection(root=tmp_path, execution=state, task_binding=IDENTITY) == selected
    if tamper == "missing_selection": state.pop("validation_readback_selection")
    elif tamper == "missing_digest": state.pop("validation_readback_policy_sha256")
    elif tamper == "changed_enabled": state["validation_readback_selection"]["enabled"] = True
    elif tamper == "changed_sha": state["validation_readback_policy_sha256"] = "0" * 64
    elif tamper == "changed_identity": state["validation_readback_selection"]["work_front_id"] = "forged"
    elif tamper == "changed_policy_bytes": p.write_bytes(p.read_bytes() + b"# drift\n")
    with pytest.raises(r.ReadbackSelectionError):
        r.verify_frozen_selection(root=tmp_path, execution=state, task_binding=IDENTITY)


def _synthetic_pipeline(monkeypatch, root: Path, selected: bool = False):
    doc = policy()
    if selected:
        add_optin(doc)
    write(root, doc)
    transport = root / training.RESULT_TRANSPORT_POLICY_REF
    transport.parent.mkdir(parents=True, exist_ok=True)
    transport.write_text(yaml.safe_dump({
        "schema_version": training.RESULT_TRANSPORT_POLICY_SCHEMA,
        "status": "current_standard", "revision": "0.1.0", "grants_authority": False,
        "default_transport": training.LEGACY_RESULT_TRANSPORT,
        "allowed_transports": [training.LEGACY_RESULT_TRANSPORT, training.DRAFT_RESULT_TRANSPORT],
        "opt_in_bindings": [],
    }, sort_keys=False))
    binding = {
        **IDENTITY, "execution_profile": "light-maintenance",
        "profile_ref": "light-maintenance@r1", "procedure_id": "governed_canonical_mutation",
        "module": "forprint_system_blueprint", "training_task_id": "fixture-task",
        "training_order": 1,
    }
    monkeypatch.setattr(training, "resolve_training_task", lambda **kwargs: copy.deepcopy(binding))
    monkeypatch.setattr(training, "assert_attempt_unused", lambda **kwargs: None)
    monkeypatch.setattr(training.dispatch, "prepare_cf09_task_execution", lambda **kwargs: {
        "state": "AWAITING_ASSISTANT_ACK", "assistant_ack_validated": False,
        "module": binding["module"], "work_front_id": binding["work_front_ref"],
        "task_prompt_id": binding["task_prompt_id"], "procedure_id": binding["procedure_id"],
        "execution_profile_ref": binding["execution_profile"],
        "authority": {k: False for k in (
            "execution_authority_granted", "dispatch_authority_granted", "worker_dispatch_performed",
            "external_dispatch_allowed", "release_allowed", "push_allowed", "merge_allowed")},
    })
    def ack(**kwargs):
        v = copy.deepcopy(kwargs["prepared_execution"])
        v["state"] = "READY_FOR_EXPLICIT_DISPATCH"
        v["assistant_ack_validated"] = True
        v["authority"] = {k: False for k in (
            "execution_authority_granted", "dispatch_authority_granted", "worker_dispatch_performed",
            "external_dispatch_allowed", "release_allowed", "push_allowed", "merge_allowed")}
        v["work_front_gate"] = {"validated": True, "work_front_id": IDENTITY["work_front_id"]}
        v["handoff_manifest_sha256"] = "a" * 64
        v["governed_worker_context"] = {"schema_version": "fixture"}
        return v
    monkeypatch.setattr(training.dispatch, "validate_cf09_assistant_ack", ack)
    monkeypatch.setattr(training, "_validated_governed_worker_context_digest", lambda ready: "b" * 64)
    prepared = training.prepare_training_pre_dispatch(
        root=root, task_prompt_id=IDENTITY["task_prompt_id"],
        worker_id="worker-01", attempt_id=ATTEMPT,
    )
    return prepared, binding


def _ready(monkeypatch, root, prepared):
    return training.validate_training_assistant_ack(
        root=root, prepared_execution=prepared, assistant_ack={}, expected_ack={},
    )


def _decision(root, ready):
    workspace = root / "forprint_system_blueprint" / "worker-01" / ATTEMPT / "workspace" / "repo"
    workspace.mkdir(parents=True, exist_ok=True)
    return training.authorize_training_explicit_dispatch(
        root=root, ready_execution=ready, worker_id="worker-01", attempt_id=ATTEMPT,
        source_state_fingerprint="c" * 64, workspace_repo=workspace,
        runtime_provider="github_copilot_cli", runtime_model="auto",
    )


@pytest.mark.parametrize("selected", [False, True])
def test_pipeline_freezes_readback_in_decision_digest(tmp_path, monkeypatch, selected):
    prepared, binding = _synthetic_pipeline(monkeypatch, tmp_path, selected)
    assert prepared["validation_readback_selection"]["enabled"] is selected
    assert prepared["worker_process_launch_allowed"] is False
    ready = _ready(monkeypatch, tmp_path, prepared)
    decision = _decision(tmp_path, ready)
    assert decision["binding"]["validation_readback_selection"] == prepared["validation_readback_selection"]
    assert decision["decision_id"] == hashlib.sha256(json.dumps(
        decision["binding"], sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    assert decision["automatic_accept_allowed"] is False


@pytest.mark.parametrize("change", ["digest", "enabled", "policy_bytes"])
def test_pipeline_ack_refuses_drift(tmp_path, monkeypatch, change):
    prepared, _ = _synthetic_pipeline(monkeypatch, tmp_path)
    if change == "digest": prepared["validation_readback_policy_sha256"] = "f" * 64
    if change == "enabled": prepared["validation_readback_selection"]["enabled"] = True
    if change == "policy_bytes":
        p = tmp_path / r.POLICY_REF
        p.write_bytes(p.read_bytes() + b"# moved\n")
    with pytest.raises((r.ReadbackSelectionError, training.CF10TrainingDispatchError)):
        _ready(monkeypatch, tmp_path, prepared)


def test_pipeline_dispatch_refuses_ready_forgery(tmp_path, monkeypatch):
    prepared, _ = _synthetic_pipeline(monkeypatch, tmp_path)
    ready = _ready(monkeypatch, tmp_path, prepared)
    ready["validation_readback_selection"]["enabled"] = True
    with pytest.raises((r.ReadbackSelectionError, training.CF10TrainingDispatchError)):
        _decision(tmp_path, ready)


def test_pipeline_legacy_absent_policy_keeps_no_selector(tmp_path, monkeypatch):
    prepared, _ = _synthetic_pipeline(monkeypatch, tmp_path)
    (tmp_path / r.POLICY_REF).unlink()
    # Legacy absent policy = no permission, not partial enabled selection.
    # A new prepare without registry stays explicitly unselected.
    again = training.prepare_training_pre_dispatch(
        root=tmp_path, task_prompt_id=IDENTITY["task_prompt_id"],
        worker_id="worker-01", attempt_id=ATTEMPT,
    )
    assert "validation_readback_selection" not in again
    with pytest.raises(r.ReadbackSelectionError):
        _ready(monkeypatch, tmp_path, prepared)


def test_ambient_env_cannot_enable_readback(tmp_path, monkeypatch):
    write(tmp_path)
    monkeypatch.setenv("FORPRINT_WORKER_VALIDATION_READBACK", "true")
    monkeypatch.setenv("FORPRINT_WORKER_RESULT_TRANSPORT", "worker-completion-draft-v0-1")
    assert r.resolve_selection(root=tmp_path, task_binding=IDENTITY)["enabled"] is False


def test_invalid_task_identity_refused(tmp_path):
    write(tmp_path)
    for bad in (
        {**IDENTITY, "work_front_ref": "../bad.yaml"},
        {**IDENTITY, "work_front_ref": "/etc/passwd"},
        {**IDENTITY, "work_front_ref": "coordination/work_fronts/../bad.yaml"},
        {**IDENTITY, "task_prompt_id": "any*"},
        {**IDENTITY, "work_front_id": "  whitespace"},
    ):
        with pytest.raises(r.ReadbackSelectionError):
            r.resolve_selection(root=tmp_path, task_binding=bad)


def test_producer_does_not_widen_four_tool_invocation(tmp_path, monkeypatch):
    prepared, _ = _synthetic_pipeline(monkeypatch, tmp_path, selected=True)
    assert prepared["validation_readback_selection"]["enabled"] is True
    assert prepared["worker_process_launch_allowed"] is False
    assert prepared["canonical_attempt_ledger_append_allowed"] is False
    # B3 P0/P1 only binds a decision: it cannot synthesize an MCP config.
    assert not any(key in prepared for key in (
        "allowed_tools", "mcp_servers", "worker_process_launch_performed",
    ))
