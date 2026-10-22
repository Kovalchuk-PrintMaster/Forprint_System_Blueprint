from __future__ import annotations

import copy
import hashlib
import inspect
import json
import runpy
from pathlib import Path

import pytest

from scripts.coordination.control_plane import governed_worker_cycle as cycle
from scripts.coordination.control_plane.worker_runtime import invocation_adapter

ROOT = Path(__file__).resolve().parents[3]
P0 = runpy.run_path(str(ROOT / "tests/coordination/control_plane/test_cf10_s4_transport_selection_authority_v0_1.py"))
LEGACY = "handoff-v2-full"
DRAFT = "worker-completion-draft-v0-1"


def _setup(monkeypatch, tmp_path: Path, *, draft: bool = False):
    task = P0["_task_binding"]()
    policy = P0["_policy"]()
    if draft:
        policy["opt_in_bindings"] = [P0["_optin"](task)]
    prepared = P0["_prepare_synthetic"](monkeypatch, tmp_path, task, policy)
    decision = P0["_dispatch_synthetic"](monkeypatch, tmp_path, prepared)
    return task, prepared, decision


def _verified(tmp_path, task, prepared, decision, *, task_id=None, attempt_id=None):
    resolver = getattr(cycle, "_resolve_stage4c_trusted_transport", None)
    assert callable(resolver), "STAGE4C_TRUSTED_SELECTOR_NOT_IMPLEMENTED"
    return resolver(
        root=tmp_path,
        prepared_execution=prepared,
        explicit_dispatch_decision=decision,
        expected_task_prompt_id=task["task_prompt_id"] if task_id is None else task_id,
        expected_attempt_id=prepared["attempt_id"] if attempt_id is None else attempt_id,
    )


def _rehash(decision):
    decision["decision_id"] = hashlib.sha256(
        json.dumps(decision["binding"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_stage4c_default_legacy_is_bound(tmp_path, monkeypatch):
    task, prepared, decision = _setup(monkeypatch, tmp_path)
    assert _verified(tmp_path, task, prepared, decision) == LEGACY


def test_stage4c_synthetic_exact_optin_is_bound(tmp_path, monkeypatch):
    task, prepared, decision = _setup(monkeypatch, tmp_path, draft=True)
    assert _verified(tmp_path, task, prepared, decision) == DRAFT


@pytest.mark.parametrize("tamper", [
    "changed_decision_id",
    "changed_selector_with_rehashed_decision",
    "changed_work_front_with_rehashed_decision",
    "removed_decision_selector_with_rehashed_decision",
    "removed_prepared_policy_sha",
    "changed_prepared_selector",
])
def test_stage4c_refuses_selection_tampering(tmp_path, monkeypatch, tamper):
    task, prepared, decision = _setup(monkeypatch, tmp_path)
    prepared = copy.deepcopy(prepared)
    decision = copy.deepcopy(decision)
    if tamper == "changed_decision_id":
        decision["decision_id"] = "0" * 64
    elif tamper == "changed_selector_with_rehashed_decision":
        decision["binding"]["result_transport_selection"]["transport"] = DRAFT
        _rehash(decision)
    elif tamper == "changed_work_front_with_rehashed_decision":
        decision["binding"]["work_front_id"] = "wf-forged"
        _rehash(decision)
    elif tamper == "removed_decision_selector_with_rehashed_decision":
        decision["binding"].pop("result_transport_selection")
        _rehash(decision)
    elif tamper == "removed_prepared_policy_sha":
        prepared.pop("result_transport_policy_sha256")
    elif tamper == "changed_prepared_selector":
        prepared["result_transport_selection"]["transport"] = DRAFT
    with pytest.raises(cycle.GovernedWorkerCycleError):
        _verified(tmp_path, task, prepared, decision)


@pytest.mark.parametrize("identity_field", ["task", "attempt"])
def test_stage4c_refuses_wrong_identity(tmp_path, monkeypatch, identity_field):
    task, prepared, decision = _setup(monkeypatch, tmp_path)
    kwargs = {"task_id": "wrong-task"} if identity_field == "task" else {"attempt_id": "wrong-attempt"}
    with pytest.raises(cycle.GovernedWorkerCycleError):
        _verified(tmp_path, task, prepared, decision, **kwargs)


def test_stage4c_refuses_policy_byte_drift(tmp_path, monkeypatch):
    task, prepared, decision = _setup(monkeypatch, tmp_path)
    policy = tmp_path / "coordination/registry/cf10_worker_result_transport_policy_v0_1.yaml"
    with policy.open("ab") as stream:
        stream.write(b"\n# adversarial post-dispatch drift\n")
    with pytest.raises(cycle.GovernedWorkerCycleError):
        _verified(tmp_path, task, prepared, decision)


def test_stage4c_cycle_passes_explicit_transport_at_result_return():
    source = inspect.getsource(cycle.launch_cycle)
    assert "result_transport=" in source, "STAGE4C_RESULT_RETURN_WIRING_MISSING"


def test_stage4c_invocation_builder_accepts_bounded_transport():
    parameters = inspect.signature(invocation_adapter.build_launch_invocation).parameters
    assert "result_transport" in parameters, "STAGE4C_INVOCATION_WIRING_MISSING"


# Stage 4C behavioral regressions: prompt transport is bound before Worker stdout.
def _prompt_transport_fixture():
    adapter_tests = runpy.run_path(str(
        ROOT / "tests/coordination/control_plane/worker_runtime/"
        "test_cf10_worker_runtime_invocation_adapter_v0_1.py"
    ))
    context = adapter_tests["_context"]()
    decision = adapter_tests["_decision"](Path("/tmp/stage4c/workspace"))
    binding = decision["binding"]
    binding["result_transport_selection"] = {
        "schema_version": "forprint_cf10_result_transport_selection_v0_1",
        "transport": DRAFT,
        "policy_ref": "coordination/registry/cf10_worker_result_transport_policy_v0_1.yaml",
        "policy_sha256": "3" * 64,
        "policy_revision": "0.1.0",
        "task_prompt_id": binding["task_prompt_id"],
        "work_front_id": binding["work_front_id"],
        "work_front_ref": binding["work_front_ref"],
    }
    _rehash(decision)
    return context, decision, P0["_governed_context"]()


def test_stage4c_draft_prompt_uses_completion_json_without_origin_sha():
    context, decision, governed = _prompt_transport_fixture()
    prompt = invocation_adapter.render_worker_prompt(
        task_context=context,
        explicit_dispatch_decision=decision,
        governed_worker_context=governed,
        result_transport=DRAFT,
    )
    assert "FORPRINT_WORKER_COMPLETION_DRAFT_V0_1_BEGIN" in prompt
    assert "FORPRINT_WORKER_COMPLETION_DRAFT_V0_1_END" in prompt
    assert "FORPRINT_HANDOFF_V2_RESULT_BEGIN" not in prompt
    assert "S4 RESULT RESUME BINDING" not in prompt
    assert "handoff_manifest_sha256" not in prompt
    assert "roadmap_status_sha256" not in prompt
    assert "- Do not accept/promote/commit/push/merge/release." in prompt


def test_stage4c_invocation_rejects_declared_draft_as_legacy():
    context, decision, governed = _prompt_transport_fixture()
    with pytest.raises(invocation_adapter.WorkerRuntimeInvocationError):
        invocation_adapter.render_worker_prompt(
            task_context=context,
            explicit_dispatch_decision=decision,
            governed_worker_context=governed,
        )


def test_stage4c_invocation_rejects_rehashed_mode_mismatch():
    context, decision, governed = _prompt_transport_fixture()
    decision["binding"]["result_transport_selection"]["transport"] = LEGACY
    _rehash(decision)
    with pytest.raises(invocation_adapter.WorkerRuntimeInvocationError):
        invocation_adapter.render_worker_prompt(
            task_context=context,
            explicit_dispatch_decision=decision,
            governed_worker_context=governed,
            result_transport=DRAFT,
        )


def test_stage4c_invocation_rejects_selector_hash_drift():
    context, decision, governed = _prompt_transport_fixture()
    decision["binding"]["result_transport_selection"]["policy_sha256"] = "4" * 64
    with pytest.raises(invocation_adapter.WorkerRuntimeInvocationError):
        invocation_adapter.render_worker_prompt(
            task_context=context,
            explicit_dispatch_decision=decision,
            governed_worker_context=governed,
            result_transport=DRAFT,
        )


def test_stage4c_draft_requires_frozen_context():
    context, decision, _ = _prompt_transport_fixture()
    with pytest.raises(invocation_adapter.WorkerRuntimeInvocationError):
        invocation_adapter.render_worker_prompt(
            task_context=context,
            explicit_dispatch_decision=decision,
            result_transport=DRAFT,
        )


def test_stage4c_legacy_absence_preserves_full_handoff_frame():
    adapter_tests = runpy.run_path(str(
        ROOT / "tests/coordination/control_plane/worker_runtime/"
        "test_cf10_worker_runtime_invocation_adapter_v0_1.py"
    ))
    context = adapter_tests["_context"]()
    decision = adapter_tests["_decision"](Path("/tmp/stage4c/workspace"))
    prompt = invocation_adapter.render_worker_prompt(
        task_context=context,
        explicit_dispatch_decision=decision,
    )
    assert "FORPRINT_HANDOFF_V2_RESULT_BEGIN" in prompt
    assert "FORPRINT_HANDOFF_V2_RESULT_END" in prompt
    assert "FORPRINT_WORKER_COMPLETION_DRAFT_V0_1_BEGIN" not in prompt


@pytest.mark.parametrize("tamper", [
    "missing_prepared_training_binding",
    "missing_dispatch_binding",
])
def test_stage4c_real_dispatch_cannot_downgrade_to_unbound_legacy(tmp_path, monkeypatch, tamper):
    task, prepared, decision = _setup(monkeypatch, tmp_path)
    assert "decision_id" in decision
    if tamper == "missing_prepared_training_binding":
        prepared.pop("cf10_training_binding")
    else:
        decision.pop("binding")
    with pytest.raises(cycle.GovernedWorkerCycleError, match="Stage 4C task binding unavailable"):
        _verified(tmp_path, task, prepared, decision)
