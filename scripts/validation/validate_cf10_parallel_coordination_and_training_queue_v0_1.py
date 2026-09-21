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
START_MARKER = (
    "<!-- cf10-temporary-parallel-assistant-coordination-2026-09-21:start -->"
)
END_MARKER = (
    "<!-- cf10-temporary-parallel-assistant-coordination-2026-09-21:end -->"
)

FORBIDDEN = (
    ROOT
    / "coordination/instruction_intake/bootstrap/current_handoff_v0_2.yaml",
    ROOT / "coordination/registry/multi_assistant_registry_v0_1.yaml",
    ROOT
    / "coordination/standards/automation/"
    "multi_assistant_locking_contract_v0_1.yaml",
)


def main() -> int:
    text = START.read_text(encoding="utf-8")
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        raise RuntimeError("temporary coordination marker topology invalid")

    required_phrases = (
        "CF-10 / Internal Worker Engineering",
        "Roadmap Enrichment / Portfolio Knowledge",
        "cross-workstream notice",
        "surface/path",
        "reason",
        "expected mutation",
        "collision risk",
        "does **not** create write",
        "not** a new execution-",
        "cf10_worker_training_queue_v0_1.yaml",
    )
    missing = [item for item in required_phrases if item not in text]
    if missing:
        raise RuntimeError(
            "START_HERE coordination content missing: " + repr(missing)
        )

    data = yaml.safe_load(QUEUE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("Worker Training Queue root must be mapping")
    if data.get("schema_version") != "forprint_cf10_worker_training_queue_v0_1":
        raise RuntimeError("unexpected Worker Training Queue schema")
    if data.get("work_id") != "u180j" or data.get("step_id") != "CF-10":
        raise RuntimeError("Worker Training Queue is outside CF-10")

    authority = data.get("authority") or {}
    forbidden_true = (
        "queue_is_execution_authority",
        "dispatch_authority_granted",
        "release_authority_granted",
        "foreign_write_authority_granted",
        "automatic_accept_authority_granted",
        "global_portfolio_planning_authority_granted",
    )
    for key in forbidden_true:
        if authority.get(key) is not False:
            raise RuntimeError(f"queue authority widening: {key}")

    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise RuntimeError("Worker Training Queue tasks missing")

    required_task_fields = (
        "task_id",
        "order",
        "complexity",
        "training_goal",
        "prerequisites",
        "acceptance",
        "retry_policy",
        "final_control_task",
    )
    seen_ids = set()
    orders = []
    finals = []
    for task in tasks:
        if not isinstance(task, dict):
            raise RuntimeError("queue task must be mapping")
        missing_fields = [
            key for key in required_task_fields if key not in task
        ]
        if missing_fields:
            raise RuntimeError(
                f"task fields missing for {task.get('task_id')}: "
                + repr(missing_fields)
            )
        task_id = task["task_id"]
        if task_id in seen_ids:
            raise RuntimeError("duplicate task_id: " + str(task_id))
        seen_ids.add(task_id)
        orders.append(task["order"])
        if task["final_control_task"] is True:
            finals.append(task)

    if orders != sorted(orders) or len(set(orders)) != len(orders):
        raise RuntimeError("task order is not strictly unique ascending")
    if len(finals) != 1:
        raise RuntimeError("exactly one final_control_task is required")
    if finals[0]["order"] != max(orders):
        raise RuntimeError("final control task must be highest order")
    if finals[0]["task_id"] != "project_execution_planning_system_control_task":
        raise RuntimeError("unexpected final control task")

    boundary = data.get("parallel_workstream_boundary") or {}
    if boundary.get("global_roadmap_enrichment_in_scope") is not False:
        raise RuntimeError("CF-10 queue widened into global roadmap enrichment")
    if boundary.get("silence_grants_write_authority") is not False:
        raise RuntimeError("silence incorrectly grants write authority")

    for path in FORBIDDEN:
        if path.exists():
            raise RuntimeError(
                "forbidden temporary framework artifact exists: " + str(path)
            )

    print("CF10_PARALLEL_COORDINATION_AND_TRAINING_QUEUE_VALIDATION=PASS")
    print("WORK_ID=u180j")
    print("STEP_ID=CF-10")
    print("TRAINING_TASK_COUNT=" + str(len(tasks)))
    print("FINAL_CONTROL_TASK=project_execution_planning_system_control_task")
    print("GLOBAL_ROADMAP_ENRICHMENT_IN_SCOPE=false")
    print("QUEUE_GRANTS_EXECUTION_AUTHORITY=false")
    print("NEW_ORCHESTRATION_FRAMEWORK_CREATED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
