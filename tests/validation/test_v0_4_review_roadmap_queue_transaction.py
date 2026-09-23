from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "scripts/coordination/review_roadmap_queue_transaction_v0_4.py"
HANDOFF = (
    ROOT
    / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
)
BOOTSTRAP = (
    ROOT
    / "coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_1.yaml"
)
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
QUEUE = ROOT / "coordination/self_coordination/prompt_queue/index.yaml"

STEP24 = "blueprint_v0_4_completion_discovery_and_intake_v0_1"
STEP25 = "blueprint_v0_4_review_roadmap_queue_transaction_v0_1"
STEP26 = "blueprint_v0_4_next_prompt_selection_and_activation_v0_1"


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def tool_module():
    spec = importlib.util.spec_from_file_location(
        "review_roadmap_queue_v04",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_state(tmp_path: Path) -> dict[str, Path]:
    root = tmp_path / "blueprint"
    roadmap = root / "coordination/roadmaps/demo.yaml"
    queue = root / "coordination/outgoing_prompts/demo/index.yaml"
    approved = (
        root
        / "coordination/outgoing_prompts/demo/approved/demo_prompt.md"
    )

    write_yaml(
        roadmap,
        {
            "schema_version": "demo_roadmap_v0_1",
            "metadata": {"current_step_id": "demo_step_1"},
            "steps": [
                {
                    "step_id": "demo_step_1",
                    "sequence": 1,
                    "status": "active",
                    "depends_on": [],
                },
                {
                    "step_id": "demo_step_2",
                    "sequence": 2,
                    "status": "planned",
                    "depends_on": ["demo_step_1"],
                },
            ],
        },
    )
    write_yaml(
        queue,
        {
            "schema_version": "demo_prompt_queue_v0_1",
            "metadata": {
                "active_prompt_id": "demo_prompt",
                "approved_prompt_count": 1,
                "draft_prompt_count": 0,
                "completed_prompt_count": 0,
                "dispatchable_draft_count": 0,
                "deferred_prompt_count": 0,
            },
            "prompts": [
                {
                    "prompt_id": "demo_prompt",
                    "status": "approved",
                    "execution_status": "in_progress",
                    "dispatch_ready": True,
                    "path": (
                        "coordination/outgoing_prompts/demo/"
                        "approved/demo_prompt.md"
                    ),
                    "roadmap_step_id": "demo_step_1",
                }
            ],
        },
    )
    approved.parent.mkdir(parents=True, exist_ok=True)
    approved.write_text(
        "---\n"
        "schema_version: demo_prompt_v0_1\n"
        "prompt_id: demo_prompt\n"
        "status: approved\n"
        "roadmap_step_id: demo_step_1\n"
        "---\n"
        "# Demo prompt\n",
        encoding="utf-8",
    )
    return {
        "root": root,
        "roadmap": roadmap,
        "queue": queue,
        "approved": approved,
    }


def request_for(
    module,
    paths: dict[str, Path],
    decision: str,
    *,
    decision_id: str = "decision_demo_001",
    notes: str = "reviewed",
) -> dict:
    root = paths["root"]
    return {
        "schema_version": (
            "blueprint_review_roadmap_queue_transaction_request_v0_4"
        ),
        "review_candidate": {
            "module_id": "demo",
            "prompt_id": "demo_prompt",
            "event_id": "event_demo_001",
            "event_path": (
                "coordination/completion_outbox/records/"
                "event_demo_001.yaml"
            ),
            "event_sha256": "a" * 64,
            "packet_path": (
                "coordination/completion_packets/records/"
                "completion_demo_001.yaml"
            ),
            "packet_sha256": "b" * 64,
            "intake_state": "READY_FOR_BLUEPRINT_REVIEW",
            "operator_decision_created": False,
            "discovery_fingerprint_sha256": "c" * 64,
        },
        "decision": {
            "decision_id": decision_id,
            "operator_decision": decision,
            "explicit_operator_input": True,
            "decided_at": "2026-08-16T18:30:00+03:00",
            "review_notes": notes,
        },
        "targets": {
            "roadmap_path": str(paths["roadmap"].relative_to(root)),
            "prompt_queue_path": str(paths["queue"].relative_to(root)),
            "prompt_path": str(paths["approved"].relative_to(root)),
            "review_evidence_path": (
                f"coordination/review_packets/demo/processed/"
                f"{decision_id}.yaml"
            ),
            "roadmap_step_id": "demo_step_1",
        },
        "preconditions": {
            "roadmap_sha256": module.file_sha256(paths["roadmap"]),
            "prompt_queue_sha256": module.file_sha256(paths["queue"]),
            "prompt_sha256": module.file_sha256(paths["approved"]),
        },
    }


def test_live_status_is_read_only_and_matches_live_discovery() -> None:
    module = tool_module()
    before = module.file_sha256(ROADMAP)
    report = module.live_status(ROOT)
    after = module.file_sha256(ROADMAP)

    assert before == after

    candidates = report["review_candidates"]
    summary = report["summary"]
    governance = report["governance"]

    assert isinstance(candidates, list)
    candidate_count = len(candidates)

    assert summary["review_candidates"] == candidate_count
    assert summary["events_discovered"] >= candidate_count
    assert summary["invalid_events"] >= 0
    assert summary["source_errors"] >= 0

    if candidate_count:
        assert report["result_state"] == "REVIEW_CANDIDATES_AVAILABLE"
    else:
        assert report["result_state"] == "NO_REVIEW_TRANSACTION_AVAILABLE"

    assert governance["operator_decision_created"] is False
    assert governance["automatic_acceptance"] is False
    assert governance["automatic_return"] is False
    assert governance["automatic_hold"] is False

    assert governance["roadmap_mutated"] is False
    assert governance["prompt_queue_mutated"] is False
    assert governance["prompt_file_mutated"] is False
    assert governance["module_repository_writes"] is False

    assert governance["next_prompt_selection_performed"] is False
    assert governance["next_prompt_activation_performed"] is False
    assert governance["global_v0_4_promotion_performed"] is False
    assert governance["automatic_commit"] is False
    assert governance["automatic_push"] is False


def test_preview_is_read_only(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")

    before = {
        key: module.file_sha256(paths[key])
        for key in ["roadmap", "queue", "approved"]
    }
    plan = module.prepare_transaction(paths["root"], request)
    after = {
        key: module.file_sha256(paths[key])
        for key in ["roadmap", "queue", "approved"]
    }

    assert before == after
    assert plan["result_state"] == "READY_TO_APPLY"
    assert plan["operator_decision"] == "ACCEPT"
    assert plan["boundaries"]["operator_decision_created_by_tool"] is False
    assert plan["boundaries"]["next_prompt_activation_performed"] is False


def test_accept_is_atomic_and_moves_prompt_to_completed(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")

    result = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )

    roadmap = load(paths["roadmap"])
    queue = load(paths["queue"])
    step = roadmap["steps"][0]
    prompt = queue["prompts"][0]
    completed = (
        paths["root"]
        / "coordination/outgoing_prompts/demo/completed/demo_prompt.md"
    )
    evidence = (
        paths["root"]
        / "coordination/review_packets/demo/processed/"
        "decision_demo_001.yaml"
    )

    assert result["result_state"] == "ACCEPT_APPLIED"
    assert step["status"] == "completed"
    assert step["operator_decision"] == "ACCEPT"
    assert prompt["status"] == "completed"
    assert prompt["execution_status"] == "accepted"
    assert queue["metadata"]["active_prompt_id"] is None
    assert queue["metadata"]["approved_prompt_count"] == 0
    assert queue["metadata"]["completed_prompt_count"] == 1
    assert not paths["approved"].exists()
    assert completed.is_file()
    assert "status: completed" in completed.read_text(encoding="utf-8")
    assert evidence.is_file()

    record = load(evidence)
    assert record["result"] == "ACCEPTED"
    assert record["decision"]["explicit_operator_input"] is True
    assert record["transaction"]["next_prompt_selection_performed"] is False
    assert record["transaction"]["next_prompt_activation_performed"] is False
    assert record["transaction"]["eligible_step_ids_after_transaction"] == [
        "demo_step_2"
    ]


def test_return_preserves_approved_prompt_and_roadmap_status(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(
        module,
        paths,
        "RETURN",
        notes="correct the completion evidence",
    )

    result = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )

    roadmap = load(paths["roadmap"])
    queue = load(paths["queue"])
    assert result["result_state"] == "RETURN_APPLIED"
    assert roadmap["steps"][0]["status"] == "active"
    assert roadmap["steps"][0]["operator_decision"] == "RETURN"
    assert queue["prompts"][0]["status"] == "approved"
    assert queue["prompts"][0]["execution_status"] == "returned"
    assert paths["approved"].is_file()
    assert not (
        paths["root"]
        / "coordination/outgoing_prompts/demo/completed/demo_prompt.md"
    ).exists()


def test_hold_is_distinct_from_return_and_does_not_archive(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "HOLD", notes="await operator input")

    result = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )

    roadmap = load(paths["roadmap"])
    queue = load(paths["queue"])
    evidence = load(
        paths["root"]
        / "coordination/review_packets/demo/processed/"
        "decision_demo_001.yaml"
    )

    assert result["result_state"] == "HOLD_APPLIED"
    assert roadmap["steps"][0]["status"] == "active"
    assert queue["prompts"][0]["status"] == "approved"
    assert queue["prompts"][0]["execution_status"] == "held"
    assert evidence["semantics"]["hold_is_not_return"] is True
    assert evidence["semantics"][
        "return_hold_preserve_prompt_outside_completed"
    ] is True
    assert paths["approved"].is_file()


def test_explicit_operator_input_and_confirmation_are_required(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    request["decision"]["explicit_operator_input"] = False

    with pytest.raises(module.TransactionError):
        module.prepare_transaction(paths["root"], request)

    request["decision"]["explicit_operator_input"] = True
    with pytest.raises(module.TransactionError):
        module.apply_transaction(
            paths["root"],
            request,
            operator_confirmation="wrong_decision_id",
        )


def test_return_requires_correction_notes(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "RETURN", notes="")

    with pytest.raises(module.TransactionError):
        module.prepare_transaction(paths["root"], request)


def test_transaction_rolls_back_exactly_on_post_write_failure(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")

    before = {
        key: paths[key].read_bytes()
        for key in ["roadmap", "queue", "approved"]
    }

    def fail() -> None:
        raise RuntimeError("synthetic validation failure")

    with pytest.raises(RuntimeError, match="synthetic validation failure"):
        module.apply_transaction(
            paths["root"],
            request,
            operator_confirmation="decision_demo_001",
            post_write_validator=fail,
        )

    assert paths["roadmap"].read_bytes() == before["roadmap"]
    assert paths["queue"].read_bytes() == before["queue"]
    assert paths["approved"].read_bytes() == before["approved"]
    assert not (
        paths["root"]
        / "coordination/outgoing_prompts/demo/completed/demo_prompt.md"
    ).exists()
    assert not (
        paths["root"]
        / "coordination/review_packets/demo/processed/"
        "decision_demo_001.yaml"
    ).exists()


def test_same_decision_identity_is_idempotent(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")

    first = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )
    roadmap_after_first = paths["roadmap"].read_bytes()
    queue_after_first = paths["queue"].read_bytes()

    second = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )

    assert first["result_state"] == "ACCEPT_APPLIED"
    assert second["result_state"] == "ALREADY_APPLIED"
    assert second["idempotent_noop"] is True
    assert paths["roadmap"].read_bytes() == roadmap_after_first
    assert paths["queue"].read_bytes() == queue_after_first


def test_conflicting_decision_identity_fails_safely(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    accept = request_for(module, paths, "ACCEPT")
    module.apply_transaction(
        paths["root"],
        accept,
        operator_confirmation="decision_demo_001",
    )

    conflict = copy.deepcopy(accept)
    conflict["decision"]["operator_decision"] = "HOLD"
    conflict["decision"]["review_notes"] = "conflict"

    with pytest.raises(
        module.TransactionError,
        match="different decision identity",
    ):
        module.apply_transaction(
            paths["root"],
            conflict,
            operator_confirmation="decision_demo_001",
        )


def test_evidence_path_cannot_escape_blueprint_review_area(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "HOLD")
    request["targets"]["review_evidence_path"] = "../outside.yaml"

    with pytest.raises(module.TransactionError):
        module.prepare_transaction(paths["root"], request)


def test_current_step25_implementation_does_not_advance_lifecycle() -> None:
    roadmap = load(ROADMAP)
    queue = load(QUEUE)
    handoff = load(HANDOFF)
    bootstrap = load(BOOTSTRAP)

    current_id = roadmap["metadata"]["current_step_id"]
    assert current_id in {STEP25, STEP26, "blueprint_v0_4_tracking_events_reference_v0_1"}
    assert queue["metadata"]["active_prompt_id"] == current_id

    step25 = next(
        item for item in roadmap["steps"] if item["step_id"] == STEP25
    )
    prompt25 = next(
        item for item in queue["prompts"] if item["prompt_id"] == STEP25
    )
    state = handoff["review_roadmap_queue_transaction_v0_4"]

    if current_id == STEP25:
        assert step25["status"] == "active"
        assert prompt25["status"] == "approved"
        assert prompt25["execution_status"] == "ready_for_module_pull"
        assert state["implementation_status"] == "READY_FOR_OPERATOR_REVIEW"
        assert state["operator_decision_created"] is False
    else:
        assert step25["status"] == "completed"
        assert step25["operator_decision"] == "ACCEPT"
        assert prompt25["status"] == "completed"
        assert prompt25["execution_status"] == "accepted"
        assert prompt25["operator_decision"] == "ACCEPT"
        assert state["implementation_status"] == "accepted_v0_4"
        assert state["operator_decision_created"] is True
        assert state["operator_decision"] == "ACCEPT"

        step26 = next(
            item for item in roadmap["steps"] if item["step_id"] == STEP26
        )
        prompt26 = next(
            item for item in queue["prompts"] if item["prompt_id"] == STEP26
        )
        if current_id == STEP26:
            assert step26["status"] == "active"
            assert prompt26["status"] == "approved"
            assert prompt26["execution_status"] == "ready_for_module_pull"
        else:
            current_prompt = next(
                item
                for item in queue["prompts"]
                if item["prompt_id"] == current_id
            )
            assert step26["status"] == "completed"
            assert step26["operator_decision"] == "ACCEPT"
            assert prompt26["status"] == "completed"
            assert prompt26["execution_status"] == "accepted"
            assert current_prompt["status"] == "approved"
            assert current_prompt["execution_status"] == "ready_for_module_pull"

    assert state["transaction_engine_implemented"] is True
    assert state["step26_selection_activation_implemented"] is False
    assert state["tracking_events_reference_run"] is False
    assert state["global_v0_4_promotion_performed"] is False
    assert state["module_repository_writes"] is False
    assert state["automatic_acceptance"] is False
    assert state["automatic_return"] is False
    assert state["automatic_hold"] is False
    assert state["automatic_commit"] is False
    assert state["automatic_push"] is False

    prior = handoff["completion_discovery_intake_v0_4"]
    assert prior["review_roadmap_queue_transaction_implemented"] is False
    assert prior["operator_decision"] == "ACCEPT"

    source_map = bootstrap["source_of_truth_map"]
    assert (
        source_map["review_roadmap_queue_transaction_v0_4_tool"]
        == "scripts/coordination/review_roadmap_queue_transaction_v0_4.py"
    )
    assert (
        source_map["review_roadmap_queue_transaction_v0_4_test"]
        == "tests/validation/test_v0_4_review_roadmap_queue_transaction.py"
    )
