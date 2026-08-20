from __future__ import annotations

import copy
from pathlib import Path

import yaml

from scripts.coordination.prompt_execution_events_v0_1 import (
    discover_execution_events,
    validate_event,
)


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    blueprint = tmp_path / "blueprint"
    module = tmp_path / "module"
    queue = (
        blueprint
        / "coordination/outgoing_prompts/demo/index.yaml"
    )
    write_yaml(
        queue,
        {
            "schema_version": "prompt_queue_v0_2",
            "module": "demo",
            "prompt_queue": [
                {
                    "prompt_id": "demo_prompt_v0_1",
                    "sequence": 1,
                    "title": "Demo prompt",
                    "file": "approved/demo.md",
                    "target_module": "demo",
                    "phase": "demo",
                    "priority": "high",
                    "module_execution": {
                        "status": "ready_for_module_pull",
                        "completion_commit": None,
                        "completion_report": None,
                        "completed_at": None,
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
    )
    prompt = queue.parent / "approved/demo.md"
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text("# Demo\n", encoding="utf-8")

    registry = (
        blueprint
        / "coordination/registry/"
        "coordination_source_registry_v0_1.yaml"
    )
    write_yaml(
        registry,
        {
            "schema_version": "coordination_source_registry_v0_1",
            "metadata": {
                "owner": "forprint_system_blueprint",
            },
            "modules": [
                {
                    "module_id": "demo",
                    "repository": {
                        "repository_id": "demo",
                        "local_path": str(module),
                    },
                    "sources": {
                        "prompt_queue": {
                            "owner": "forprint_system_blueprint",
                            "repository": "forprint_system_blueprint",
                            "path": (
                                "coordination/outgoing_prompts/"
                                "demo/index.yaml"
                            ),
                            "availability": "present",
                        }
                    },
                    "boundaries": {
                        "blueprint_lookup_mode": "read_only",
                        "blueprint_may_write_repository": False,
                    },
                }
            ],
        },
    )
    module.mkdir(parents=True, exist_ok=True)
    return blueprint, module, registry


def event_data(
    *,
    event_id: str,
    sequence: int,
    event_type: str,
    prompt_id: str = "demo_prompt_v0_1",
) -> dict:
    blocked = event_type in {"BLOCKED", "UNABLE_TO_EXECUTE"}
    return {
        "schema_version": "module_prompt_execution_event_v0_1",
        "event_id": event_id,
        "module_id": "demo",
        "prompt_id": prompt_id,
        "sequence": sequence,
        "event_type": event_type,
        "occurred_at": f"2026-08-19T19:{30 + sequence:02d}:00+03:00",
        "immutable": True,
        "execution": {
            "reason_code": "DEP_WAIT" if blocked else None,
            "reason": "waiting for dependency" if blocked else None,
            "blocking_refs": ["dependency_x"] if blocked else [],
        },
        "boundaries": {
            "blueprint_repository_write_performed": False,
            "operator_decision_created": False,
            "completion_claimed": False,
            "acceptance_claimed": False,
            "return_or_hold_claimed": False,
        },
    }


def write_event(
    module: Path,
    data: dict,
) -> Path:
    path = (
        module
        / "coordination/prompt_execution_events/records"
        / f"{data['event_id']}.yaml"
    )
    write_yaml(path, data)
    return path


def test_claimed_event_validates_and_projects(tmp_path: Path) -> None:
    blueprint, module, registry = fixture(tmp_path)
    path = write_event(
        module,
        event_data(
            event_id="demo_claimed_001",
            sequence=1,
            event_type="CLAIMED",
        ),
    )

    validation = validate_event(
        path,
        blueprint_root=blueprint,
        repository_root=module,
        registry_path=registry,
    )
    assert validation["result"] == "PASSED"
    assert validation["observed_status"] == "claimed"

    before = (
        blueprint
        / "coordination/outgoing_prompts/demo/index.yaml"
    ).read_bytes()
    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    after = (
        blueprint
        / "coordination/outgoing_prompts/demo/index.yaml"
    ).read_bytes()

    assert before == after
    assert report["result_state"] == "EXECUTION_OBSERVATIONS_AVAILABLE"
    projection = report["projections"][0]
    assert projection["queue_recorded_status"] == "ready_for_module_pull"
    assert projection["observed_status"] == "claimed"
    assert projection["classification"] == "CURRENT_EXECUTION_OBSERVATION"
    assert report["governance"]["queue_mutated"] is False
    assert report["governance"]["module_repository_writes"] is False


def test_first_event_must_be_claimed(tmp_path: Path) -> None:
    blueprint, module, registry = fixture(tmp_path)
    write_event(
        module,
        event_data(
            event_id="demo_progress_001",
            sequence=1,
            event_type="IN_PROGRESS",
        ),
    )

    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    assert report["result_state"] == "ATTENTION_REQUIRED"
    assert report["summary"]["transition_errors"] == 1
    assert "START->IN_PROGRESS" in report["transition_errors"][0]
    assert report["projections"] == []


def test_claim_progress_block_resume_is_valid(tmp_path: Path) -> None:
    blueprint, module, registry = fixture(tmp_path)
    for sequence, event_type in enumerate(
        ("CLAIMED", "IN_PROGRESS", "BLOCKED", "IN_PROGRESS"),
        start=1,
    ):
        write_event(
            module,
            event_data(
                event_id=f"demo_{sequence:03d}",
                sequence=sequence,
                event_type=event_type,
            ),
        )

    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    assert report["result_state"] == "EXECUTION_OBSERVATIONS_AVAILABLE"
    assert report["projections"][0]["observed_status"] == "in_progress"
    assert report["summary"]["transition_errors"] == 0


def test_blocked_requires_reason(tmp_path: Path) -> None:
    blueprint, module, registry = fixture(tmp_path)
    data = event_data(
        event_id="demo_blocked_001",
        sequence=1,
        event_type="BLOCKED",
    )
    data["execution"]["reason"] = None
    path = write_event(module, data)

    report = validate_event(
        path,
        blueprint_root=blueprint,
        repository_root=module,
        registry_path=registry,
    )
    assert report["result"] == "FAILED"
    assert any(
        "BLOCKED requires execution.reason" in item
        for item in report["errors"]
    )


def test_unable_to_execute_requires_reason_code(tmp_path: Path) -> None:
    blueprint, module, registry = fixture(tmp_path)
    data = event_data(
        event_id="demo_unable_001",
        sequence=1,
        event_type="UNABLE_TO_EXECUTE",
    )
    data["execution"]["reason_code"] = None
    path = write_event(module, data)

    report = validate_event(
        path,
        blueprint_root=blueprint,
        repository_root=module,
        registry_path=registry,
    )
    assert report["result"] == "FAILED"
    assert any(
        "UNABLE_TO_EXECUTE requires safe execution.reason_code" in item
        for item in report["errors"]
    )


def test_unknown_prompt_is_invalid(tmp_path: Path) -> None:
    blueprint, module, registry = fixture(tmp_path)
    path = write_event(
        module,
        event_data(
            event_id="unknown_claimed_001",
            sequence=1,
            event_type="CLAIMED",
            prompt_id="unknown_prompt_v0_1",
        ),
    )

    report = validate_event(
        path,
        blueprint_root=blueprint,
        repository_root=module,
        registry_path=registry,
    )
    assert report["result"] == "FAILED"
    assert any(
        "expected one queue record" in item
        for item in report["errors"]
    )


def test_execution_event_cannot_claim_operator_decision(
    tmp_path: Path,
) -> None:
    blueprint, module, registry = fixture(tmp_path)
    data = event_data(
        event_id="demo_claimed_001",
        sequence=1,
        event_type="CLAIMED",
    )
    data["operator_decision"] = "ACCEPT"
    path = write_event(module, data)

    report = validate_event(
        path,
        blueprint_root=blueprint,
        repository_root=module,
        registry_path=registry,
    )
    assert report["result"] == "FAILED"
    assert any(
        "forbidden decision/completion fields" in item
        for item in report["errors"]
    )


def test_return_hold_and_completed_are_not_event_types(
    tmp_path: Path,
) -> None:
    blueprint, module, registry = fixture(tmp_path)
    for event_type in ("RETURN", "HOLD", "COMPLETED"):
        data = event_data(
            event_id=f"demo_{event_type.lower()}_001",
            sequence=1,
            event_type="CLAIMED",
        )
        data["event_type"] = event_type
        path = write_event(module, data)
        report = validate_event(
            path,
            blueprint_root=blueprint,
            repository_root=module,
            registry_path=registry,
        )
        assert report["result"] == "FAILED"
        assert any(
            "event_type must be one of" in item
            for item in report["errors"]
        )
        path.unlink()


def test_missing_event_directory_is_clean_not_present_yet(
    tmp_path: Path,
) -> None:
    blueprint, _, registry = fixture(tmp_path)

    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    assert report["result_state"] == "NO_EXECUTION_EVENTS_AVAILABLE"
    assert report["source_states"]["demo"] == "not_present_yet"
    assert report["source_errors"] == []


def test_duplicate_sequence_is_attention_required(tmp_path: Path) -> None:
    blueprint, module, registry = fixture(tmp_path)
    write_event(
        module,
        event_data(
            event_id="demo_claimed_001",
            sequence=1,
            event_type="CLAIMED",
        ),
    )
    data = event_data(
        event_id="demo_claimed_duplicate",
        sequence=1,
        event_type="CLAIMED",
    )
    data["occurred_at"] = "2026-08-19T19:40:00+03:00"
    write_event(module, data)

    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    assert report["result_state"] == "ATTENTION_REQUIRED"
    assert any(
        "duplicate execution event sequence" in item
        for item in report["transition_errors"]
    )


def test_completed_queue_makes_event_historical(
    tmp_path: Path,
) -> None:
    blueprint, module, registry = fixture(tmp_path)
    write_event(
        module,
        event_data(
            event_id="demo_claimed_001",
            sequence=1,
            event_type="CLAIMED",
        ),
    )
    queue_path = (
        blueprint
        / "coordination/outgoing_prompts/demo/index.yaml"
    )
    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    queue["prompt_queue"][0]["module_execution"]["status"] = (
        "completed_by_module"
    )
    write_yaml(queue_path, queue)

    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    assert report["result_state"] == "EXECUTION_OBSERVATIONS_AVAILABLE"
    assert report["projections"][0]["classification"] == (
        "HISTORICAL_EXECUTION_OBSERVATION"
    )


def test_multiple_current_prompt_observations_violate_wip_one(
    tmp_path: Path,
) -> None:
    blueprint, module, registry = fixture(tmp_path)
    queue_path = (
        blueprint
        / "coordination/outgoing_prompts/demo/index.yaml"
    )
    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    second = copy.deepcopy(queue["prompt_queue"][0])
    second["prompt_id"] = "demo_prompt_v0_2"
    second["sequence"] = 2
    queue["prompt_queue"].append(second)
    write_yaml(queue_path, queue)

    for prompt_id, suffix in (
        ("demo_prompt_v0_1", "one"),
        ("demo_prompt_v0_2", "two"),
    ):
        write_event(
            module,
            event_data(
                event_id=f"demo_{suffix}_claimed_001",
                sequence=1,
                event_type="CLAIMED",
                prompt_id=prompt_id,
            ),
        )

    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    assert report["result_state"] == "ATTENTION_REQUIRED"
    assert report["summary"]["wip_errors"] == 1
    assert "multiple current execution observations" in report["wip_errors"][0]

def test_sequence_must_be_contiguous(tmp_path: Path) -> None:
    blueprint, module, registry = fixture(tmp_path)
    write_event(
        module,
        event_data(
            event_id="demo_claimed_001",
            sequence=1,
            event_type="CLAIMED",
        ),
    )
    write_event(
        module,
        event_data(
            event_id="demo_progress_003",
            sequence=3,
            event_type="IN_PROGRESS",
        ),
    )
    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    assert report["result_state"] == "ATTENTION_REQUIRED"
    assert any(
        "non-contiguous execution event sequence" in item
        for item in report["transition_errors"]
    )


def test_occurred_at_cannot_move_backwards(tmp_path: Path) -> None:
    blueprint, module, registry = fixture(tmp_path)
    first = event_data(
        event_id="demo_claimed_001",
        sequence=1,
        event_type="CLAIMED",
    )
    first["occurred_at"] = "2026-08-19T19:40:00+03:00"
    write_event(module, first)

    second = event_data(
        event_id="demo_progress_002",
        sequence=2,
        event_type="IN_PROGRESS",
    )
    second["occurred_at"] = "2026-08-19T19:39:00+03:00"
    write_event(module, second)

    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    assert report["result_state"] == "ATTENTION_REQUIRED"
    assert any(
        "occurred_at moved backwards" in item
        for item in report["transition_errors"]
    )


def test_unknown_module_filter_fails_closed(tmp_path: Path) -> None:
    blueprint, _, registry = fixture(tmp_path)
    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
        module_filter={"not_registered"},
    )
    assert report["result_state"] == "ATTENTION_REQUIRED"
    assert any(
        "unknown module filter" in item
        for item in report["source_errors"]
    )


def test_returned_queue_state_does_not_reactivate_stale_event(
    tmp_path: Path,
) -> None:
    blueprint, module, registry = fixture(tmp_path)
    write_event(
        module,
        event_data(
            event_id="demo_claimed_001",
            sequence=1,
            event_type="CLAIMED",
        ),
    )
    queue_path = (
        blueprint / "coordination/outgoing_prompts/demo/index.yaml"
    )
    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    queue["prompt_queue"][0]["module_execution"]["status"] = (
        "returned_for_fix"
    )
    write_yaml(queue_path, queue)

    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    assert report["result_state"] == "ATTENTION_REQUIRED"
    assert report["summary"]["queue_state_errors"] == 1


def test_discovery_does_not_write_module_repository(
    tmp_path: Path,
) -> None:
    blueprint, module, registry = fixture(tmp_path)
    write_event(
        module,
        event_data(
            event_id="demo_claimed_001",
            sequence=1,
            event_type="CLAIMED",
        ),
    )
    before = {
        path.relative_to(module).as_posix(): path.read_bytes()
        for path in module.rglob("*")
        if path.is_file()
    }
    discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    after = {
        path.relative_to(module).as_posix(): path.read_bytes()
        for path in module.rglob("*")
        if path.is_file()
    }
    assert before == after


def test_prompt_dashboard_surfaces_claim(tmp_path: Path) -> None:
    from scripts.coordination.render_prompt_dashboard import (
        render_dashboard,
    )

    blueprint, module, registry = fixture(tmp_path)
    write_event(
        module,
        event_data(
            event_id="demo_claimed_001",
            sequence=1,
            event_type="CLAIMED",
        ),
    )
    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )
    rendered = render_dashboard(
        blueprint / "coordination/outgoing_prompts/demo/index.yaml",
        use_color=False,
        execution_report=report,
    )
    assert "Module Execution Observation" in rendered
    assert "demo_prompt_v0_1=claimed" in rendered


def test_h3_is_wired_into_pulse_and_make_check() -> None:
    root = Path(__file__).resolve().parents[2]
    pulse = (
        root / "scripts/coordination/coordination_pulse.py"
    ).read_text(encoding="utf-8")
    makefile = (root / "Makefile").read_text(encoding="utf-8")

    assert '"prompt_execution": {' in pulse
    assert "PROMPT_EXECUTION_TRANSITION_INVALID" in pulse
    assert '"MODULE EXECUTION"' in pulse
    assert "check-prompt-execution-observability" in makefile

def test_missing_repository_is_coverage_state_not_source_error(
    tmp_path: Path,
) -> None:
    blueprint, module, registry = fixture(tmp_path)
    module.rmdir()

    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )

    assert report["result_state"] == "NO_EXECUTION_EVENTS_AVAILABLE"
    assert report["source_states"]["demo"] == "repository_not_present"
    assert report["source_errors"] == []
    assert report["summary"]["repository_not_present"] == 1
    assert report["summary"]["event_source_not_present_yet"] == 0

def test_blueprint_self_module_is_not_external_h3_source(
    tmp_path: Path,
) -> None:
    blueprint, _, registry = fixture(tmp_path)
    registry_data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    registry_data["modules"].append(
        {
            "module_id": "forprint_system_blueprint",
            "repository": {
                "repository_id": "forprint_system_blueprint",
                "local_path": str(blueprint),
            },
            "sources": {
                "prompt_queue": {
                    "owner": "forprint_system_blueprint",
                    "repository": "forprint_system_blueprint",
                    "path": (
                        "coordination/outgoing_prompts/"
                        "forprint_system_blueprint/index.yaml"
                    ),
                    "availability": "present",
                }
            },
            "boundaries": {
                "blueprint_lookup_mode": "read_only",
                "blueprint_may_write_repository": True,
            },
        }
    )
    write_yaml(registry, registry_data)

    report = discover_execution_events(
        blueprint_root=blueprint,
        registry_path=registry,
    )

    assert report["result_state"] == "NO_EXECUTION_EVENTS_AVAILABLE"
    assert report["source_errors"] == []
    assert report["source_states"]["forprint_system_blueprint"] == (
        "self_module_not_applicable"
    )
    assert report["summary"]["self_module_not_applicable"] == 1
