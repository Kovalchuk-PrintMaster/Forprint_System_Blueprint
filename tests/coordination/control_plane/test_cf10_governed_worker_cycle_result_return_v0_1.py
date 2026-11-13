from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[3]
SOURCE = (
    ROOT
    / "scripts/coordination/control_plane/"
    "governed_worker_cycle.py"
)

spec = importlib.util.spec_from_file_location(
    "_cf10_governed_worker_cycle_result_return_test",
    SOURCE,
)
assert spec is not None and spec.loader is not None
gwc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gwc
spec.loader.exec_module(gwc)


ATTEMPT = "cf10-u180j-a034"
TASK = "cf10-validation-check-pipeline-profile-and-optimization-v0-1"


def _process_evidence(
    attempt_root: Path,
    *,
    return_code: int = 0,
    timed_out: bool = False,
) -> None:
    evidence = attempt_root / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "governed_worker_cycle_worker_process_result_v0_1.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": (
                    "forprint_governed_worker_cycle_worker_process_result_v0_1"
                ),
                "attempt_id": ATTEMPT,
                "process": {
                    "process_started": True,
                    "return_code": return_code,
                    "timed_out": timed_out,
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _minimal_manifest(attempt_root: Path) -> None:
    attempt_root.mkdir(parents=True, exist_ok=True)
    (attempt_root / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "attempt_id": ATTEMPT,
                "provisioning_performed": True,
                "source_state_frozen": True,
                "assistant_ack_validated": True,
                "explicit_dispatch_decision_recorded": True,
                "worker_launch_performed": True,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    input_dir = attempt_root / "input"
    input_dir.mkdir(exist_ok=True)
    (input_dir / "governed_worker_cycle_ready_execution_v0_1.yaml").write_text(
        "{}\n",
        encoding="utf-8",
    )
    (
        input_dir
        / "governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml"
    ).write_text("{}\n", encoding="utf-8")


def test_projection_blocks_finished_process_without_valid_result() -> None:
    facts = {
        "task_resolved": True,
        "workspace_prepared": True,
        "assistant_ack_validated": True,
        "explicit_dispatch_authorized": True,
        "worker_process_started": True,
        "worker_process_finished": True,
        "worker_result_return_valid": False,
        "worker_result_return_blocked": True,
        "candidate_validation_passed": False,
        "handoff_validated": False,
        "attempt_terminal_pass": False,
        "attempt_terminal_failed": False,
        "operator_review_passed": False,
        "candidate_promoted": False,
        "canonical_validation_passed": False,
        "publication_approved": False,
        "commit_performed": False,
        "remote_containment_verified": False,
        "blocked": False,
    }

    projection = gwc.derive_cycle_projection(facts)

    assert projection["state"] == "BLOCKED"
    assert projection["next_boundary"] == "RECONCILE_BLOCKER"


def test_projection_requires_valid_result_before_candidate_validation() -> None:
    facts = {
        "task_resolved": True,
        "workspace_prepared": True,
        "assistant_ack_validated": True,
        "explicit_dispatch_authorized": True,
        "worker_process_started": True,
        "worker_process_finished": True,
        "worker_result_return_valid": True,
        "worker_result_return_blocked": False,
        "candidate_validation_passed": False,
        "handoff_validated": False,
        "attempt_terminal_pass": False,
        "attempt_terminal_failed": False,
        "operator_review_passed": False,
        "candidate_promoted": False,
        "canonical_validation_passed": False,
        "publication_approved": False,
        "commit_performed": False,
        "remote_containment_verified": False,
        "blocked": False,
    }

    projection = gwc.derive_cycle_projection(facts)

    assert projection["state"] == "VALIDATE_CANDIDATE"
    assert projection["next_boundary"] == "CANDIDATE_VALIDATION"


def test_live_facts_fail_closed_on_successful_process_without_result(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt = tmp_path / "runtime" / ATTEMPT
    _minimal_manifest(attempt)
    _process_evidence(attempt, return_code=0, timed_out=False)

    monkeypatch.setattr(
        gwc,
        "_attempt_root",
        lambda runtime_root, attempt_id, worker_id=gwc.WORKER_ID: attempt,
    )
    monkeypatch.setattr(
        gwc.training,
        "resolve_training_task",
        lambda **kwargs: {"task_prompt_id": TASK},
    )

    facts = gwc.live_facts(
        root=tmp_path,
        runtime_root=tmp_path / "runtime",
        task_prompt_id=TASK,
        attempt_id=ATTEMPT,
    )

    assert facts["worker_process_finished"] is True
    assert facts["worker_result_return_valid"] is False
    assert facts["worker_result_return_blocked"] is True
    assert facts["blocked"] is True

    projection = gwc.derive_cycle_projection(facts)
    assert projection["state"] == "BLOCKED"


def test_live_facts_accepts_only_valid_materialized_result_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt = tmp_path / "runtime" / ATTEMPT
    _minimal_manifest(attempt)
    _process_evidence(attempt, return_code=0, timed_out=False)

    result_dir = attempt / "result"
    result_dir.mkdir()
    (result_dir / "worker_result.yaml").write_text(
        "schema_version: forprint_assistant_handoff_v2_result_v0_1\n"
        f"attempt_id: {ATTEMPT}\n"
        "status: PASS\n",
        encoding="utf-8",
    )
    evidence = attempt / "evidence"
    (
        evidence / "governed_worker_cycle_result_return_v0_1.yaml"
    ).write_text(
        yaml.safe_dump(
            {
                "schema_version": (
                    "forprint_governed_worker_cycle_result_return_v0_1"
                ),
                "attempt_id": ATTEMPT,
                "result": "PASS",
                "validation_passed": True,
                "result_path": str(result_dir / "worker_result.yaml"),
                "blocked": False,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        gwc,
        "_attempt_root",
        lambda runtime_root, attempt_id, worker_id=gwc.WORKER_ID: attempt,
    )
    monkeypatch.setattr(
        gwc.training,
        "resolve_training_task",
        lambda **kwargs: {"task_prompt_id": TASK},
    )

    facts = gwc.live_facts(
        root=tmp_path,
        runtime_root=tmp_path / "runtime",
        task_prompt_id=TASK,
        attempt_id=ATTEMPT,
    )

    assert facts["worker_result_return_valid"] is True
    assert facts["worker_result_return_blocked"] is False
    assert facts["blocked"] is False

    projection = gwc.derive_cycle_projection(facts)
    assert projection["state"] == "VALIDATE_CANDIDATE"


def test_nonzero_process_is_blocked_even_if_no_result_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt = tmp_path / "runtime" / ATTEMPT
    _minimal_manifest(attempt)
    _process_evidence(attempt, return_code=2, timed_out=False)

    monkeypatch.setattr(
        gwc,
        "_attempt_root",
        lambda runtime_root, attempt_id, worker_id=gwc.WORKER_ID: attempt,
    )
    monkeypatch.setattr(
        gwc.training,
        "resolve_training_task",
        lambda **kwargs: {"task_prompt_id": TASK},
    )

    facts = gwc.live_facts(
        root=tmp_path,
        runtime_root=tmp_path / "runtime",
        task_prompt_id=TASK,
        attempt_id=ATTEMPT,
    )

    assert facts["worker_process_finished"] is True
    assert facts["worker_result_return_blocked"] is True
    assert facts["blocked"] is True
    assert gwc.derive_cycle_projection(facts)["state"] == "BLOCKED"


def test_timed_out_process_is_blocked(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt = tmp_path / "runtime" / ATTEMPT
    _minimal_manifest(attempt)
    _process_evidence(attempt, return_code=None, timed_out=True)

    monkeypatch.setattr(
        gwc,
        "_attempt_root",
        lambda runtime_root, attempt_id, worker_id=gwc.WORKER_ID: attempt,
    )
    monkeypatch.setattr(
        gwc.training,
        "resolve_training_task",
        lambda **kwargs: {"task_prompt_id": TASK},
    )

    facts = gwc.live_facts(
        root=tmp_path,
        runtime_root=tmp_path / "runtime",
        task_prompt_id=TASK,
        attempt_id=ATTEMPT,
    )

    assert facts["worker_result_return_blocked"] is True
    assert facts["blocked"] is True
    assert gwc.derive_cycle_projection(facts)["state"] == "BLOCKED"


def test_cycle_cli_exposes_explicit_result_return_reconciliation_boundary() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert '"reconcile-result-return"' in text
    assert "--confirm-result-return-reconciliation" in text
    assert "def reconcile_result_return" in text


def test_reconciliation_refuses_without_explicit_confirmation(
    tmp_path: Path,
) -> None:
    assert hasattr(gwc, "reconcile_result_return"), (
        "reconcile_result_return API missing"
    )

    with pytest.raises(
        gwc.GovernedWorkerCycleError,
        match="confirm|confirmation",
    ):
        gwc.reconcile_result_return(
            root=tmp_path,
            runtime_root=tmp_path / "runtime",
            task_prompt_id=TASK,
            attempt_id=ATTEMPT,
            confirm=False,
        )


def test_reconciliation_appends_terminal_blocked_fact_without_result_synthesis(
    tmp_path: Path,
    monkeypatch,
) -> None:
    assert hasattr(gwc, "reconcile_result_return"), (
        "reconcile_result_return API missing"
    )

    attempt = tmp_path / "runtime" / ATTEMPT
    _minimal_manifest(attempt)
    _process_evidence(attempt, return_code=0, timed_out=False)

    input_dir = attempt / "input"
    (
        input_dir / "governed_worker_cycle_source_state_v0_1.yaml"
    ).write_text(
        yaml.safe_dump(
            {
                "git_head": "a" * 40,
                "fingerprint_sha256": "f" * 64,
            }
        ),
        encoding="utf-8",
    )

    appended: list[dict] = []

    monkeypatch.setattr(
        gwc,
        "_attempt_root",
        lambda runtime_root, attempt_id, worker_id=gwc.WORKER_ID: attempt,
    )
    monkeypatch.setattr(
        gwc.training,
        "resolve_training_task",
        lambda **kwargs: {
            "work_front_id": (
                "wf-cf10-validation-check-pipeline-profile-and-optimization-v0-1"
            ),
            "profile_ref": "light-maintenance@r1",
        },
    )
    monkeypatch.setattr(
        gwc,
        "_assert_frozen_source_state_current",
        lambda *args, **kwargs: {},
    )

    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger

    started = {
        "schema_version": "forprint_execution_attempt_record_v0_1",
        "attempt_id": ATTEMPT,
        "work_front_id": (
            "wf-cf10-validation-check-pipeline-profile-and-optimization-v0-1"
        ),
        "recorded_at": "2026-10-07T12:00:00Z",
        "actor_or_worker_ref": "worker-01/provider:github_copilot_cli",
        "where": str(attempt / "workspace/repo"),
        "why": f"CF-10 governed Worker launch for canonical task {TASK}.",
        "source_fingerprint": "f" * 64,
        "profile_ref_or_revision": "light-maintenance@r1",
        "pack_hash_or_context_hash": "h" * 64,
        "launch_or_invocation_ref": "decision.yaml",
        "attempt_stage": "STARTED",
        "result_state": "PENDING",
        "result_refs": [],
        "validator_outcome": "NOT_RUN",
        "validator_evidence_refs": [],
        "failure_or_retry_ref": None,
        "resume": {
            "latest_accepted_ref": None,
            "resume_coordinates": [],
            "replay_forbidden_refs": [],
        },
    }

    monkeypatch.setattr(
        ledger,
        "load_contract",
        lambda root: {
            "storage": {"default_root": "coordination/continuity/execution_attempts"}
        },
    )
    monkeypatch.setattr(
        ledger,
        "store_root",
        lambda root, contract, override: tmp_path / "ledger",
    )
    monkeypatch.setattr(
        ledger,
        "records_for_attempt",
        lambda store, attempt_id: [started],
    )
    monkeypatch.setattr(
        ledger,
        "validate_record_data",
        lambda record, contract: [],
    )
    monkeypatch.setattr(
        ledger,
        "append_record",
        lambda root, record, store_override=None: (
            appended.append(dict(record))
            or tmp_path / "ledger" / "terminal.yaml"
        ),
    )

    result = gwc.reconcile_result_return(
        root=tmp_path,
        runtime_root=tmp_path / "runtime",
        task_prompt_id=TASK,
        attempt_id=ATTEMPT,
        confirm=True,
    )

    assert len(appended) == 1
    terminal = appended[0]
    assert terminal["attempt_id"] == ATTEMPT
    assert terminal["attempt_stage"] == "BLOCKED"
    assert terminal["result_state"] == "BLOCKED"
    assert terminal["validator_outcome"] == "FAIL"
    assert terminal["failure_or_retry_ref"] is not None
    assert any(
        "RESULT_ENVELOPE_MISSING_AFTER_SUCCESSFUL_PROCESS" in ref
        for ref in terminal["validator_evidence_refs"]
    )

    assert result["state"] == "BLOCKED"
    assert result["failure_class"] == (
        "RESULT_ENVELOPE_MISSING_AFTER_SUCCESSFUL_PROCESS"
    )
    assert result["worker_result_synthesized"] is False
    assert not (attempt / "result" / "worker_result.yaml").exists()


def test_reconciliation_refuses_when_valid_result_already_exists(
    tmp_path: Path,
) -> None:
    assert hasattr(gwc, "reconcile_result_return"), (
        "reconcile_result_return API missing"
    )

    attempt = (
        tmp_path
        / "runtime"
        / "forprint_system_blueprint"
        / "worker-01"
        / ATTEMPT
    )
    _minimal_manifest(attempt)
    _process_evidence(attempt, return_code=0, timed_out=False)
    result_dir = attempt / "result"
    result_dir.mkdir()
    (result_dir / "worker_result.yaml").write_text(
        "status: PASS\n",
        encoding="utf-8",
    )

    with pytest.raises(
        gwc.GovernedWorkerCycleError,
        match="result|already",
    ):
        gwc.reconcile_result_return(
            root=tmp_path,
            runtime_root=tmp_path / "runtime",
            task_prompt_id=TASK,
            attempt_id=ATTEMPT,
            confirm=True,
        )


# CF10_S4_RESUME_CYCLE_PASS_THROUGH_RED_V0_2


def test_launch_cycle_passes_governed_context_to_result_materializer() -> None:
    import inspect

    source = inspect.getsource(gwc.launch_cycle)
    marker = "worker_result_return.materialize_worker_result("
    assert marker in source

    call = source.split(marker, 1)[1].split(")", 1)[0]
    compact = call.replace(" ", "").replace("\n", "")
    assert "governed_worker_context=governed_worker_context" in compact


# CF10_S4_FAILURE_CLASS_PRESERVATION_RED_V0_1


def test_result_return_preserves_canonical_s4_failure_class() -> None:
    exc = RuntimeError(
        "Handoff v2 S4 resume validation failed: "
        "STALE_LIFECYCLE_ROADMAP_CURSOR"
    )

    assert gwc._result_return_failure_class(exc) == (
        "STALE_LIFECYCLE_ROADMAP_CURSOR"
    )
