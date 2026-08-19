from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "scripts/coordination/review_roadmap_queue_transaction_v0_4.py"


def tool_module():
    spec = importlib.util.spec_from_file_location(
        "review_tx_module_schema_test",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def fixture_state(tmp_path: Path) -> dict[str, Path]:
    roadmap = tmp_path / "coordination/roadmaps/demo.yaml"
    queue = tmp_path / "coordination/outgoing_prompts/demo/index.yaml"
    approved = (
        tmp_path
        / "coordination/outgoing_prompts/demo/approved/demo_prompt.md"
    )

    roadmap.parent.mkdir(parents=True, exist_ok=True)
    queue.parent.mkdir(parents=True, exist_ok=True)
    approved.parent.mkdir(parents=True, exist_ok=True)

    roadmap.write_text(
        yaml.safe_dump(
            {
                "schema_version": "module_development_roadmap_v0_1",
                "module": "demo",
                "metadata": {
                    "current_step_id": "demo_prompt",
                    "updated_at": "2026-08-17",
                },
                "roadmap": [
                    {
                        "sequence": 1,
                        "step_id": "demo_prompt",
                        "title": "Demo",
                        "status": "active",
                        "priority": "critical",
                        "owner_module": "demo",
                        "depends_on": [],
                        "expected_outputs": [],
                        "evidence": {
                            "blueprint_review_status": "not_started",
                        },
                    },
                    {
                        "sequence": 2,
                        "step_id": "demo_next",
                        "title": "Next",
                        "status": "planned",
                        "priority": "high",
                        "owner_module": "demo",
                        "depends_on": [
                            {
                                "type": "module_step",
                                "module": "demo",
                                "step_id": "demo_prompt",
                                "status": "pending",
                            }
                        ],
                        "expected_outputs": [],
                        "evidence": {},
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    queue.write_text(
        yaml.safe_dump(
            {
                "schema_version": "prompt_queue_v0_2",
                "module": "demo",
                "prompt_queue": [
                    {
                        "prompt_id": "demo_prompt",
                        "sequence": 1,
                        "title": "Demo",
                        "file": "approved/demo_prompt.md",
                        "target_module": "demo",
                        "phase": "demo",
                        "priority": "critical",
                        "module_execution": {
                            "status": "completed_by_module",
                            "completion_commit": "abc",
                            "completion_report": "report.md",
                            "completed_at": "2026-08-17",
                        },
                        "blueprint_review": {
                            "status": "not_started",
                            "acceptance_commit": None,
                            "accepted_at": None,
                            "review_notes": None,
                        },
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    approved.write_text("# Demo prompt\n", encoding="utf-8")
    return {
        "root": tmp_path,
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
) -> dict:
    return {
        "schema_version": (
            "blueprint_review_roadmap_queue_transaction_request_v0_4"
        ),
        "review_candidate": {
            "module_id": "demo",
            "prompt_id": "demo_prompt",
            "event_id": "event_demo_001",
            "event_path": (
                "coordination/completion_outbox/records/event_demo_001.yaml"
            ),
            "event_sha256": "a" * 64,
            "packet_path": (
                "coordination/completion_packets/records/packet_demo_001.yaml"
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
            "decided_at": "2026-08-18T19:30:00+03:00",
            "review_notes": "explicit operator review",
        },
        "targets": {
            "roadmap_path": str(paths["roadmap"].relative_to(paths["root"])),
            "prompt_queue_path": str(
                paths["queue"].relative_to(paths["root"])
            ),
            "prompt_path": str(
                paths["approved"].relative_to(paths["root"])
            ),
            "review_evidence_path": (
                "coordination/review_packets/demo/processed/"
                f"{decision_id}.yaml"
            ),
            "roadmap_step_id": "demo_prompt",
        },
        "preconditions": {
            "roadmap_sha256": module.file_sha256(paths["roadmap"]),
            "prompt_queue_sha256": module.file_sha256(paths["queue"]),
            "prompt_sha256": module.file_sha256(paths["approved"]),
        },
    }


def test_module_schema_accept_plan_is_read_only(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")

    before = {
        key: paths[key].read_bytes()
        for key in ("roadmap", "queue", "approved")
    }

    plan = module.prepare_transaction(paths["root"], request)

    assert plan["result_state"] == "READY_TO_APPLY"
    assert plan["transaction"]["roadmap_status_before"] == "active"
    assert plan["transaction"]["roadmap_status_after"] == "accepted"
    assert plan["transaction"]["queue_status_before"] == "approved"
    assert plan["transaction"]["queue_status_after"] == "completed"
    assert (
        plan["transaction"]["queue_execution_status_after"]
        == "completed_by_module"
    )
    assert (
        plan["transaction"]["queue_review_status_after"]
        == "accepted_by_blueprint"
    )
    assert plan["boundaries"]["next_prompt_activation_performed"] is False

    for key in ("roadmap", "queue", "approved"):
        assert paths[key].read_bytes() == before[key]


def test_module_schema_accept_applies_canonical_fields(
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
    step = roadmap["roadmap"][0]
    next_step = roadmap["roadmap"][1]
    prompt = queue["prompt_queue"][0]

    completed = (
        paths["root"]
        / "coordination/outgoing_prompts/demo/completed/demo_prompt.md"
    )
    evidence_path = (
        paths["root"]
        / "coordination/review_packets/demo/processed/"
        "decision_demo_001.yaml"
    )

    assert result["result_state"] == "ACCEPT_APPLIED"
    assert result["module_repository_writes"] is False
    assert result["next_prompt_selection_performed"] is False
    assert result["next_prompt_activation_performed"] is False
    assert result["global_v0_4_promotion_performed"] is False

    assert step["status"] == "accepted"
    assert step["operator_decision"] == "ACCEPT"
    assert step["evidence"]["blueprint_review_status"] == (
        "accepted_by_blueprint"
    )
    assert next_step["depends_on"][0]["status"] == "accepted"

    assert prompt["module_execution"]["status"] == "completed_by_module"
    assert prompt["blueprint_review"]["status"] == "accepted_by_blueprint"
    assert prompt["blueprint_review"]["accepted_at"] == "2026-08-18"
    assert prompt["operator_decision"] == "ACCEPT"
    assert prompt["file"] == "completed/demo_prompt.md"

    assert not paths["approved"].exists()
    assert completed.is_file()
    assert completed.read_text(encoding="utf-8") == "# Demo prompt\n"
    assert evidence_path.is_file()

    evidence = load(evidence_path)
    assert evidence["result"] == "ACCEPTED"
    assert evidence["decision"]["explicit_operator_input"] is True
    assert evidence["transaction"]["queue_review_status_before"] == (
        "not_started"
    )
    assert evidence["transaction"]["queue_review_status_after"] == (
        "accepted_by_blueprint"
    )
    assert evidence["transaction"]["eligible_step_ids_after_transaction"] == [
        "demo_next"
    ]


def test_module_schema_accept_is_idempotent(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")

    first = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )
    roadmap_after = paths["roadmap"].read_bytes()
    queue_after = paths["queue"].read_bytes()

    second = module.apply_transaction(
        paths["root"],
        copy.deepcopy(request),
        operator_confirmation="decision_demo_001",
    )

    assert first["result_state"] == "ACCEPT_APPLIED"
    assert second["result_state"] == "ALREADY_APPLIED"
    assert second["idempotent_noop"] is True
    assert paths["roadmap"].read_bytes() == roadmap_after
    assert paths["queue"].read_bytes() == queue_after


def test_module_schema_accept_rolls_back_exactly(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")

    before = {
        key: paths[key].read_bytes()
        for key in ("roadmap", "queue", "approved")
    }

    def fail() -> None:
        raise RuntimeError("synthetic post-write validation failure")

    with pytest.raises(
        RuntimeError,
        match="synthetic post-write validation failure",
    ):
        module.apply_transaction(
            paths["root"],
            request,
            operator_confirmation="decision_demo_001",
            post_write_validator=fail,
        )

    for key in ("roadmap", "queue", "approved"):
        assert paths[key].read_bytes() == before[key]

    assert not (
        paths["root"]
        / "coordination/outgoing_prompts/demo/completed/demo_prompt.md"
    ).exists()
    assert not (
        paths["root"]
        / "coordination/review_packets/demo/processed/"
        "decision_demo_001.yaml"
    ).exists()


def test_module_schema_return_uses_legacy_status_contract(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "RETURN")

    result = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )

    roadmap = load(paths["roadmap"])
    queue = load(paths["queue"])

    assert result["result_state"] == "RETURN_APPLIED"
    assert roadmap["roadmap"][0]["status"] == "active"
    assert queue["prompt_queue"][0]["module_execution"]["status"] == (
        "returned_for_fix"
    )
    assert queue["prompt_queue"][0]["blueprint_review"]["status"] == (
        "returned_for_fix"
    )
    assert queue["prompt_queue"][0]["file"] == "approved/demo_prompt.md"
    assert paths["approved"].is_file()


def test_module_schema_hold_preserves_module_completion(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "HOLD")

    result = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )

    roadmap = load(paths["roadmap"])
    queue = load(paths["queue"])

    assert result["result_state"] == "HOLD_APPLIED"
    assert roadmap["roadmap"][0]["status"] == "active"
    assert queue["prompt_queue"][0]["module_execution"]["status"] == (
        "completed_by_module"
    )
    assert queue["prompt_queue"][0]["blueprint_review"]["status"] == (
        "pending_review"
    )
    assert paths["approved"].is_file()
