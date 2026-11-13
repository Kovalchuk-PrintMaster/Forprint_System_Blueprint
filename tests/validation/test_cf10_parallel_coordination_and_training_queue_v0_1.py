from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
START = ROOT / "coordination/bootstrap/START_HERE.md"
QUEUE = (
    ROOT
    / "coordination/internal_work/blueprint/worker_training/"
    "cf10_worker_training_queue_v0_1.yaml"
)


def queue() -> dict:
    data = yaml.safe_load(QUEUE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_temporary_parallel_coordination_is_convention_not_authority() -> None:
    text = START.read_text(encoding="utf-8")
    assert "Temporary parallel assistant coordination — 2026-09-21" in text
    assert "CF-10 / Internal Worker Engineering" in text
    assert "Roadmap Enrichment / Portfolio Knowledge" in text
    assert "absence of a response" in text
    assert "does **not** create write" in text
    assert "not** a new execution-" in text


def test_training_queue_has_required_task_shape_and_one_final_task() -> None:
    data = queue()
    tasks = data["tasks"]
    required = {
        "task_id",
        "order",
        "complexity",
        "training_goal",
        "prerequisites",
        "acceptance",
        "retry_policy",
        "final_control_task",
    }
    assert all(required <= set(task) for task in tasks)
    assert [task["order"] for task in tasks] == sorted(
        task["order"] for task in tasks
    )
    final = [task for task in tasks if task["final_control_task"]]
    assert len(final) == 1
    assert final[0]["task_id"] == (
        "project_execution_planning_system_control_task"
    )
    assert final[0]["order"] == max(task["order"] for task in tasks)


def test_training_queue_does_not_widen_global_or_dispatch_authority() -> None:
    data = queue()
    authority = data["authority"]
    assert authority["queue_is_execution_authority"] is False
    assert authority["dispatch_authority_granted"] is False
    assert authority["release_authority_granted"] is False
    assert authority["foreign_write_authority_granted"] is False
    assert authority["automatic_accept_authority_granted"] is False
    assert authority["global_portfolio_planning_authority_granted"] is False
    assert (
        data["parallel_workstream_boundary"][
            "global_roadmap_enrichment_in_scope"
        ]
        is False
    )


def test_a001_is_retained_as_non_reusable_training_evidence() -> None:
    history = queue()["attempt_history"]
    row = next(
        item for item in history
        if item["attempt_id"] == "cf10-u180j-a001"
    )
    assert row["process_started"] is True
    assert row["result"] == "BLOCKED_NO_MUTATION"
    assert row["reusable"] is False
    assert row["next_retry_attempt_id"] == "cf10-u180j-a002"
