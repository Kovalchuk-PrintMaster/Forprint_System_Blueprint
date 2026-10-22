from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane import cf10_training_dispatch as training

ROOT = Path(__file__).resolve().parents[3]
POLICY_REL = Path("coordination/registry/cf10_worker_result_transport_policy_v0_1.yaml")
TASK_ID = "cf10-verification-tier-self-hardening-v0-1"
SCHEMA = "forprint_cf10_worker_result_transport_policy_v0_1"
SELECTION_SCHEMA = "forprint_cf10_result_transport_selection_v0_1"
LEGACY = "handoff-v2-full"
DRAFT = "worker-completion-draft-v0-1"
ATTEMPT = "cf10-u180j-a004"


def _require_stage4cp0() -> None:
    assert (ROOT / POLICY_REL).is_file(), (
        "STAGE4CP0_TESTS_FIRST_RED: versioned transport policy is not registered"
    )
    assert callable(getattr(training, "validate_result_transport_policy_data", None)), (
        "STAGE4CP0_TESTS_FIRST_RED: producer policy validator missing"
    )
    assert callable(getattr(training, "resolve_result_transport_selection", None)), (
        "STAGE4CP0_TESTS_FIRST_RED: producer transport selector missing"
    )


def _policy() -> dict:
    return {
        "schema_version": SCHEMA,
        "status": "current_standard",
        "revision": "0.1.0",
        "grants_authority": False,
        "default_transport": LEGACY,
        "allowed_transports": [LEGACY, DRAFT],
        "opt_in_bindings": [],
    }


def _task_binding() -> dict:
    return training.resolve_training_task(root=ROOT, task_prompt_id=TASK_ID)


def _optin(binding: dict) -> dict:
    return {
        "task_prompt_id": binding["task_prompt_id"],
        "work_front_id": binding["work_front_id"],
        "work_front_ref": binding["work_front_ref"],
        "transport": DRAFT,
    }


def _write_policy(root: Path, document: dict) -> bytes:
    p = root / POLICY_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_dump(document, sort_keys=False).encode("utf-8")
    p.write_bytes(data)
    return data


def _expect_reject_policy(document: dict) -> None:
    _require_stage4cp0()
    with pytest.raises(training.CF10TrainingDispatchError):
        training.validate_result_transport_policy_data(document)


def _governed_context() -> dict:
    return {
        "schema_version": "forprint_governed_worker_context_projection_v0_1",
        "handoff_manifest_sha256": "1" * 64,
        "handoff_source_state_fingerprint": "2" * 64,
        "dependency_health_slice": {},
        "lifecycle_roadmap_cursor": {"roadmap_sync": "IN_SYNC", "open_work": {"u180j": "ACTIVE"}},
        "resume_coordinates": {"work_id": "u180j"},
        "expected_result_schema_revision": "0.1.0",
        "execution_bindings": {},
        "authority": {
            "context_grants_authority": False,
            "dispatch_authority_granted": False,
            "release_authority_granted": False,
            "cross_repository_write_authority_granted": False,
        },
    }


def _prepared(binding: dict) -> dict:
    governed = _governed_context()
    digest = hashlib.sha256(
        (json.dumps(governed, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    ).hexdigest()
    return {
        "schema_version": "forprint_cf09_dispatcher_pre_execution_envelope_v0_1",
        "mode": "TASK_EXECUTION",
        "state": "AWAITING_ASSISTANT_ACK",
        "assistant_ack_validated": False,
        "module": "forprint_system_blueprint",
        "work_front_id": binding["work_front_ref"],
        "execution_profile_ref": binding["execution_profile"],
        "task_prompt_id": binding["task_prompt_id"],
        "task_module_root": ".",
        "procedure_id": binding["procedure_id"],
        "handoff_manifest_sha256": "1" * 64,
        "governed_worker_context": governed,
        "governed_worker_context_sha256": digest,
        "work_front_gate": {"validated": True, "work_front_id": binding["work_front_id"]},
        "authority": {
            "execution_authority_granted": False,
            "dispatch_authority_granted": False,
            "worker_dispatch_performed": False,
            "external_dispatch_allowed": False,
            "release_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
        },
        "cf10_training_binding": copy.deepcopy(binding),
        "worker_id": "worker-01",
        "attempt_id": ATTEMPT,
        "workspace_required_before_dispatch": True,
        "worker_process_launch_allowed": False,
        "canonical_attempt_ledger_append_allowed": False,
    }


def _prepare_synthetic(monkeypatch, root: Path, binding: dict, policy: dict) -> dict:
    _require_stage4cp0()
    _write_policy(root, policy)
    monkeypatch.setattr(training, "resolve_training_task", lambda **kw: copy.deepcopy(binding))
    monkeypatch.setattr(training, "assert_attempt_unused", lambda **kw: None)
    monkeypatch.setattr(training.dispatch, "prepare_cf09_task_execution", lambda **kw: _prepared(binding))
    return training.prepare_training_pre_dispatch(
        root=root, task_prompt_id=binding["task_prompt_id"],
        worker_id="worker-01", attempt_id=ATTEMPT,
    )


def _ack_synthetic(monkeypatch, root: Path, prepared: dict, *, mutate=None) -> dict:
    _require_stage4cp0()
    def generic_ack(**kwargs):
        ready = copy.deepcopy(kwargs["prepared_execution"])
        ready["state"] = "READY_FOR_EXPLICIT_DISPATCH"
        ready["assistant_ack_validated"] = True
        if mutate:
            mutate(ready)
        return ready
    monkeypatch.setattr(training.dispatch, "validate_cf09_assistant_ack", generic_ack)
    return training.validate_training_assistant_ack(
        root=root, prepared_execution=prepared,
        assistant_ack={"synthetic": "ACK"}, expected_ack={"synthetic": "ACK"},
    )


def _dispatch_synthetic(monkeypatch, root: Path, prepared: dict, *, mutate=None) -> dict:
    _require_stage4cp0()
    if mutate:
        mutate(prepared)
    ready = copy.deepcopy(prepared)
    ready["state"] = "READY_FOR_EXPLICIT_DISPATCH"
    ready["assistant_ack_validated"] = True
    monkeypatch.setattr(training, "resolve_training_task", lambda **kw: copy.deepcopy(prepared["cf10_training_binding"]))
    monkeypatch.setattr(training, "assert_attempt_unused", lambda **kw: None)
    workspace = root / "forprint_system_blueprint/worker-01" / ATTEMPT / "workspace/repo"
    workspace.mkdir(parents=True, exist_ok=True)
    return training.authorize_training_explicit_dispatch(
        root=root, ready_execution=ready, worker_id="worker-01",
        attempt_id=ATTEMPT, source_state_fingerprint="d" * 64,
        workspace_repo=workspace, runtime_provider="github_copilot_cli", runtime_model="auto",
    )


def test_cf10_stage4cp0_registered_policy_is_default_closed() -> None:
    _require_stage4cp0()
    raw = (ROOT / POLICY_REL).read_bytes()
    policy = yaml.safe_load(raw)
    assert policy == _policy()
    assert training.validate_result_transport_policy_data(policy) == policy


def test_cf10_stage4cp0_default_origin_bound_selection(tmp_path: Path) -> None:
    _require_stage4cp0()
    raw = _write_policy(tmp_path, _policy())
    selection = training.resolve_result_transport_selection(root=tmp_path, task_binding=_task_binding())
    assert selection["schema_version"] == SELECTION_SCHEMA
    assert selection["transport"] == LEGACY
    assert selection["policy_ref"] == POLICY_REL.as_posix()
    assert selection["policy_sha256"] == hashlib.sha256(raw).hexdigest()
    assert selection["policy_revision"] == "0.1.0"
    assert selection["task_prompt_id"] == TASK_ID
    assert selection["work_front_id"] == _task_binding()["work_front_id"]


def test_cf10_stage4cp0_synthetic_exact_optin(tmp_path: Path) -> None:
    _require_stage4cp0()
    binding = _task_binding()
    p = _policy()
    p["opt_in_bindings"] = [_optin(binding)]
    _write_policy(tmp_path, p)
    selection = training.resolve_result_transport_selection(root=tmp_path, task_binding=binding)
    assert selection["transport"] == DRAFT
    assert selection["task_prompt_id"] == binding["task_prompt_id"]
    assert selection["work_front_ref"] == binding["work_front_ref"]


@pytest.mark.parametrize("mutate", [
    lambda p: p.update(default_transport=DRAFT),
    lambda p: p.update(grants_authority=True),
    lambda p: p.update(revision=""),
    lambda p: p.update(allowed_transports=[LEGACY]),
    lambda p: p.update(allowed_transports=[DRAFT, LEGACY]),
    lambda p: p.update(opt_in_bindings={}),
    lambda p: p.update(status="draft"),
    lambda p: p.update(schema_version="unknown"),
    lambda p: p.update(runtime_shell=True),
    lambda p: p.update(opt_in_bindings=[{"task_prompt_id": "*", "work_front_id": "*", "work_front_ref": "*", "transport": DRAFT}]),
    lambda p: p.update(opt_in_bindings=[{"task_prompt_id": TASK_ID, "work_front_id": "wf-unreviewed", "work_front_ref": "*", "transport": "custom-shell"}]),
    lambda p: p.update(opt_in_bindings=[{"task_prompt_id": "x", "work_front_id": "y", "work_front_ref": "z", "transport": LEGACY}]),
    lambda p: p.update(opt_in_bindings=[{"task_prompt_id": "x", "work_front_id": "y", "work_front_ref": "z", "transport": DRAFT}] * 2),
])
def test_cf10_stage4cp0_invalid_policy_fails_closed(mutate) -> None:
    policy = _policy()
    mutate(policy)
    _expect_reject_policy(policy)


@pytest.mark.parametrize("mutate", [
    lambda b: b.update(work_front_id="wf-untrusted"),
    lambda b: b.update(work_front_ref="coordination/work_fronts/not-the-one.yaml"),
    lambda b: b.update(task_prompt_id="*"),
])
def test_cf10_stage4cp0_mismatched_task_binding_fails_closed(tmp_path: Path, mutate) -> None:
    _require_stage4cp0()
    binding = _task_binding()
    p = _policy()
    p["opt_in_bindings"] = [_optin(binding)]
    _write_policy(tmp_path, p)
    mutate(binding)
    with pytest.raises(training.CF10TrainingDispatchError):
        training.resolve_result_transport_selection(root=tmp_path, task_binding=binding)


def test_cf10_stage4cp0_prepare_records_source_provenance(tmp_path: Path, monkeypatch) -> None:
    binding = _task_binding()
    prepared = _prepare_synthetic(monkeypatch, tmp_path, binding, _policy())
    selector = prepared["result_transport_selection"]
    assert selector["transport"] == LEGACY
    assert selector["policy_sha256"] == hashlib.sha256((tmp_path / POLICY_REL).read_bytes()).hexdigest()
    assert prepared["worker_process_launch_allowed"] is False
    assert prepared["canonical_attempt_ledger_append_allowed"] is False


def test_cf10_stage4cp0_ack_preserves_exact_selection(tmp_path: Path, monkeypatch) -> None:
    binding = _task_binding()
    prepared = _prepare_synthetic(monkeypatch, tmp_path, binding, _policy())
    ready = _ack_synthetic(monkeypatch, tmp_path, prepared)
    assert ready["result_transport_selection"] == prepared["result_transport_selection"]
    assert ready["result_transport_selection"] is not prepared["result_transport_selection"]
    assert ready["assistant_ack_validated"] is True


@pytest.mark.parametrize("mutate", [
    lambda r: r["result_transport_selection"].update(transport=DRAFT),
    lambda r: r["result_transport_selection"].update(policy_sha256="0" * 64),
    lambda r: r["result_transport_selection"].update(work_front_id="wf-forged"),
    lambda r: r.pop("result_transport_selection"),
])
def test_cf10_stage4cp0_ack_tampering_refused(tmp_path: Path, monkeypatch, mutate) -> None:
    binding = _task_binding()
    prepared = _prepare_synthetic(monkeypatch, tmp_path, binding, _policy())
    with pytest.raises(training.CF10TrainingDispatchError):
        _ack_synthetic(monkeypatch, tmp_path, prepared, mutate=mutate)


def test_cf10_stage4cp0_policy_byte_drift_on_ack_refused(tmp_path: Path, monkeypatch) -> None:
    binding = _task_binding()
    prepared = _prepare_synthetic(monkeypatch, tmp_path, binding, _policy())
    with (tmp_path / POLICY_REL).open("ab") as handle:
        handle.write(b"\n# changed after prepare\n")
    with pytest.raises(training.CF10TrainingDispatchError):
        _ack_synthetic(monkeypatch, tmp_path, prepared)


def test_cf10_stage4cp0_dispatch_hash_binds_trusted_selection(tmp_path: Path, monkeypatch) -> None:
    binding = _task_binding()
    prepared = _prepare_synthetic(monkeypatch, tmp_path, binding, _policy())
    decision = _dispatch_synthetic(monkeypatch, tmp_path, prepared)
    frozen = decision["binding"]["result_transport_selection"]
    assert frozen == prepared["result_transport_selection"]
    assert frozen["transport"] == LEGACY
    assert hashlib.sha256(json.dumps(decision["binding"], sort_keys=True, separators=(",", ":")).encode()).hexdigest() == decision["decision_id"]
    assert decision["external_dispatch_allowed"] is False
    assert decision["release_allowed"] is False
    assert decision["automatic_accept_allowed"] is False


@pytest.mark.parametrize("mutate", [
    lambda p: p["result_transport_selection"].update(transport=DRAFT),
    lambda p: p["result_transport_selection"].update(policy_sha256="0" * 64),
    lambda p: p["result_transport_selection"].update(task_prompt_id="forged"),
    lambda p: p["result_transport_selection"].update(work_front_ref="forged"),
    lambda p: p["result_transport_selection"].update(policy_revision="forged"),
    lambda p: p["result_transport_selection"].update(command="bash"),
    lambda p: p.pop("result_transport_selection"),
])
def test_cf10_stage4cp0_dispatch_selector_tamper_refused(tmp_path: Path, monkeypatch, mutate) -> None:
    binding = _task_binding()
    prepared = _prepare_synthetic(monkeypatch, tmp_path, binding, _policy())
    with pytest.raises(training.CF10TrainingDispatchError):
        _dispatch_synthetic(monkeypatch, tmp_path, prepared, mutate=mutate)


def test_cf10_stage4cp0_policy_byte_drift_on_dispatch_refused(tmp_path: Path, monkeypatch) -> None:
    binding = _task_binding()
    prepared = _prepare_synthetic(monkeypatch, tmp_path, binding, _policy())
    with (tmp_path / POLICY_REL).open("ab") as handle:
        handle.write(b"\n# changed after prepare\n")
    with pytest.raises(training.CF10TrainingDispatchError):
        _dispatch_synthetic(monkeypatch, tmp_path, prepared)


def test_cf10_stage4cp0_opt_in_does_not_grant_launch_or_acceptance(tmp_path: Path, monkeypatch) -> None:
    binding = _task_binding()
    policy = _policy()
    policy["opt_in_bindings"] = [_optin(binding)]
    prepared = _prepare_synthetic(monkeypatch, tmp_path, binding, policy)
    assert prepared["result_transport_selection"]["transport"] == DRAFT
    assert prepared["worker_process_launch_allowed"] is False
    assert prepared["canonical_attempt_ledger_append_allowed"] is False
    assert prepared["authority"]["dispatch_authority_granted"] is False


def test_cf10_stage4cp0_transport_cannot_be_model_or_env_chosen(tmp_path: Path, monkeypatch) -> None:
    binding = _task_binding()
    _require_stage4cp0()
    _write_policy(tmp_path, _policy())
    monkeypatch.setenv("FORPRINT_WORKER_RESULT_TRANSPORT", DRAFT)
    selection = training.resolve_result_transport_selection(root=tmp_path, task_binding=binding)
    assert selection["transport"] == LEGACY
    assert "worker_stdout" not in selection
    assert "model_response" not in selection


def test_cf10_stage4cp0_historical_legacy_absence_not_upgraded() -> None:
    _require_stage4cp0()
    # Past decisions are immutable; absence of the new selection is never evidence for draft.
    assert training.LEGACY_RESULT_TRANSPORT == LEGACY
