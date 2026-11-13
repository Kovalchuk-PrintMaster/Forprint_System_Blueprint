from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from scripts.coordination import roadmap_execution_reconciliation as rr


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def event(root: Path, sequence: int, event_type: str, work_id: str) -> None:
    write_yaml(
        root / "coordination/continuity/events" / f"{sequence:06d}__{work_id}.yaml",
        {
            "schema_version": "fixture",
            "sequence": sequence,
            "event_id": f"evt-{work_id}-{sequence}",
            "event_type": event_type,
            "work_id": work_id,
        },
    )


def fixture_root(tmp_path: Path) -> Path:
    root = tmp_path
    source_root = Path(__file__).resolve().parents[2]
    for relative in (
        "coordination/standards/governance/project_constitution_v0_1.yaml",
        "scripts/coordination/project_authority_v0_1.py",
        "scripts/validation/validate_project_constitution_v0_1.py",
        "coordination/standards/automation/work_front_contract_v0_1.yaml",
        "scripts/coordination/work_front_v0_1.py",
    ):
        source = source_root / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    write_yaml(
        root / "coordination/roadmaps/details/forprint_system_blueprint/continuity/"
        "2026-09-10__continuity_assistant_handoff_micro_roadmap_v0_1.yaml",
        {
            "status": "completed_execution_micro_roadmap",
            "historical_completion_evidence": {
                "schema_version": "forprint_legacy_roadmap_completion_evidence_v0_1",
                "authority": "HISTORICAL_ACCEPTANCE_EVIDENCE_NOT_EXECUTION_STATE",
                "step_state_fields_retired": True,
                "completed_step_ids": [
                    "legacy-a",
                    "legacy-b",
                    "legacy-checkpoint",
                ],
            },
            "steps": [
                {"order": 1, "id": "legacy-a", "work": "legacy-shared"},
                {
                    "order": 2,
                    "id": "legacy-b",
                    "work": "legacy-shared",
                    "depends_on": ["legacy-a"],
                },
                {
                    "order": 3,
                    "id": "legacy-checkpoint",
                    "work": "legacy-checkpoint-work",
                    "depends_on": ["legacy-b"],
                },
            ],
        },
    )
    write_yaml(
        root / "coordination/roadmaps/details/forprint_system_blueprint/"
        "control_foundation_near_horizon_program_v0_1.yaml",
        {
            "steps": [
                {
                    "order": 1,
                    "id": "CF-01",
                    "work_id": "u180a",
                    "depends_on": ["u179h:CLOSED"],
                },
                {
                    "order": 2,
                    "id": "CF-02",
                    "work_id": "u180b",
                    "depends_on": ["CF-01"],
                },
                {"order": 3, "id": "CF-03", "depends_on": ["CF-02"]},
                {
                    "order": 10,
                    "id": "CF-10",
                    "work_id": "u180c",
                    "depends_on": ["CF-01"],
                },
            ]
        },
    )
    event(root, 1, "CHECKPOINT_RECORDED", "legacy-checkpoint-work")
    event(root, 2, "WORK_CLOSED", "u179h")
    event(root, 3, "WORK_CLOSED", "u180a")
    event(root, 4, "WORK_ACTIVATED", "u180b")
    return root


def control_row(execution: dict) -> dict:
    return next(
        row
        for row in execution["roadmaps"]
        if row["roadmap_id"] == "control_foundation_near_horizon"
    )


def continuity_row(execution: dict) -> dict:
    return next(
        row for row in execution["roadmaps"] if row["roadmap_id"] == "continuity_foundation"
    )


def test_current_real_shape_is_in_sync_with_external_dependency(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    execution, reconciliation = rr.compute(root)
    assert reconciliation["roadmap_sync"] == "IN_SYNC"
    cf = control_row(execution)
    assert cf["previous_step"] == "CF-01"
    assert cf["current_step"] == "CF-02"
    assert cf["next_step"] == "CF-03"
    assert cf["next_step_state"] == "BLOCKED_UNBOUND"
    assert "CF-10" in cf["ready_candidates"]
    assert cf["next_activation"] == "REQUIRES_OPERATOR"


def test_closed_cf02_advances_derived_cursor_without_auto_activation(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    event(root, 5, "CHECKPOINT_RECORDED", "u180b")
    event(root, 6, "VALIDATION_PASSED", "u180b")
    event(root, 7, "WORK_CLOSED", "u180b")
    execution, reconciliation = rr.compute(root)
    assert reconciliation["roadmap_sync"] == "IN_SYNC"
    cf = control_row(execution)
    assert cf["previous_step"] == "CF-02"
    assert cf["current_step"] is None
    assert cf["next_step"] == "CF-03"
    assert cf["next_step_state"] == "READY_UNBOUND"
    assert "CF-03" in cf["ready_candidates"]
    assert cf["next_activation"] == "REQUIRES_OPERATOR"


def test_historical_shared_binding_and_checkpoint_hint_are_bounded_migration(
    tmp_path: Path,
) -> None:
    root = fixture_root(tmp_path)
    execution, reconciliation = rr.compute(root)
    assert reconciliation["roadmap_sync"] == "IN_SYNC"
    legacy = continuity_row(execution)
    assert "DUPLICATE_WORK_BINDING" not in legacy["reason_codes"]
    assert "HISTORICAL_SHARED_WORK_BINDING_USED" in legacy["informational_codes"]
    assert "HISTORICAL_PRE_ENFORCEMENT_EVIDENCE_USED" in legacy["informational_codes"]
    historical = next(row for row in legacy["steps"] if row["step_id"] == "legacy-checkpoint")
    assert historical["observed_event_lifecycle_state"] == "CHECKPOINTED"
    assert historical["lifecycle_state"] == "CLOSED"
    assert historical["derived_state"] == "COMPLETE"


def test_sync_then_check_is_exact_and_non_mutating_to_sources(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    roadmap = root / rr.ROADMAPS["control_foundation_near_horizon"]["path"]
    events = root / rr.EVENT_ROOT
    before_roadmap = hashlib.sha256(roadmap.read_bytes()).hexdigest()
    before_events = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in events.glob("*.yaml")
    }
    assert rr.sync(root) == 0
    assert rr.check(root) == 0
    assert hashlib.sha256(roadmap.read_bytes()).hexdigest() == before_roadmap
    assert {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in events.glob("*.yaml")
    } == before_events


def test_roadmap_change_makes_projection_stale(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    assert rr.sync(root) == 0
    roadmap = root / rr.ROADMAPS["control_foundation_near_horizon"]["path"]
    data = yaml.safe_load(roadmap.read_text(encoding="utf-8"))
    data["steps"][2]["priority"] = "P0"
    write_yaml(roadmap, data)
    assert rr.check(root) == 2


def test_duplicate_work_binding_is_conflict_for_current_program(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    roadmap = root / rr.ROADMAPS["control_foundation_near_horizon"]["path"]
    data = yaml.safe_load(roadmap.read_text(encoding="utf-8"))
    data["steps"][2]["work_id"] = "u180b"
    write_yaml(roadmap, data)
    _, reconciliation = rr.compute(root)
    assert reconciliation["roadmap_sync"] == "EXECUTION_CONFLICT"


def test_closed_step_with_unsatisfied_external_dependency_is_conflict(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    event(root, 5, "WORK_ACTIVATED", "u179h")
    _, reconciliation = rr.compute(root)
    assert reconciliation["roadmap_sync"] == "EXECUTION_CONFLICT"


def test_gate_checkpoint_current_work_passes(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    assert rr.sync(root) == 0
    assert (
        rr.gate(
            root,
            action="checkpoint",
            roadmap_id="control_foundation_near_horizon",
            step_id="CF-02",
            work_id="u180b",
        )
        == 0
    )


def test_gate_blocks_plan_of_parallel_ready_work_while_wip_is_open(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    assert rr.sync(root) == 0
    assert (
        rr.gate(
            root,
            action="plan",
            roadmap_id="control_foundation_near_horizon",
            step_id="CF-10",
            work_id="u180c",
        )
        != 0
    )


def test_gate_requires_exact_binding(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    assert rr.sync(root) == 0
    assert (
        rr.gate(
            root,
            action="checkpoint",
            roadmap_id="control_foundation_near_horizon",
            step_id="CF-02",
            work_id="wrong",
        )
        != 0
    )


def test_dispatch_reconciliation_does_not_grant_dispatch_authority(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    assert rr.sync(root) == 0
    assert (
        rr.gate(
            root,
            action="dispatch",
            roadmap_id=None,
            step_id=None,
            work_id=None,
        )
        != 0
    )


def test_gate_fails_closed_when_project_constitution_validator_missing(
    tmp_path: Path, capsys
) -> None:
    root = fixture_root(tmp_path)
    validator = root / "scripts/validation/validate_project_constitution_v0_1.py"
    validator.unlink()
    assert rr.sync(root) == 0
    assert (
        rr.gate(
            root,
            action="checkpoint",
            roadmap_id="control_foundation_near_horizon",
            step_id="CF-02",
            work_id="u180b",
        )
        == 4
    )
    captured = capsys.readouterr().out
    assert "GATE_REASON=PROJECT_CONSTITUTION_INVALID" in captured
    assert "CONSTITUTION_ERROR=VALIDATOR_MISSING" in captured


def valid_work_front(root: Path) -> Path:
    path = root / "coordination/work_fronts/test_front.yaml"
    write_yaml(
        path,
        {
            "work_front_id": "wf-test-dispatch",
            "objective": "Exercise the Work Front gate.",
            "scope": ["scripts/coordination/example.py"],
            "exclusions": ["release"],
            "provenance": {
                "source_refs": ["test:fixture"],
                "chat_is_authority": False,
            },
            "dependencies": [],
            "outputs": ["bounded result"],
            "acceptance": ["gate validates front"],
            "stop_conditions": ["scope widening required"],
            "authority": {
                "layer": "WORK_FRONT",
                "permissions": ["read"],
                "widening_requested": False,
            },
            "capability_reuse": {
                "search_performed": True,
                "searched_surfaces": ["scripts/coordination"],
                "disposition": "REUSE",
                "target_refs": ["scripts/coordination/example.py"],
            },
        },
    )
    return path


def test_dispatch_requires_work_front(tmp_path: Path, capsys) -> None:
    root = fixture_root(tmp_path)
    assert rr.sync(root) == 0
    assert (
        rr.gate(
            root,
            action="dispatch",
            roadmap_id=None,
            step_id=None,
            work_id=None,
        )
        == 4
    )
    captured = capsys.readouterr().out
    assert "GATE_REASON=WORK_FRONT_REQUIRED" in captured


def test_valid_dispatch_front_is_validated_but_dispatch_authority_remains_blocked(
    tmp_path: Path, capsys
) -> None:
    root = fixture_root(tmp_path)
    front = valid_work_front(root)
    assert rr.sync(root) == 0
    assert (
        rr.gate(
            root,
            action="dispatch",
            roadmap_id=None,
            step_id=None,
            work_id=None,
            front=str(front.relative_to(root)),
        )
        == 5
    )
    captured = capsys.readouterr().out
    assert "WORK_FRONT_GATE=PASS" in captured
    assert "DISPATCH_AUTHORITY=false" in captured
    assert "ROADMAP_GATE=BLOCKED_AUTHORITY" in captured


def test_assistant_pack_validates_supplied_work_front(tmp_path: Path, capsys) -> None:
    root = fixture_root(tmp_path)
    front = valid_work_front(root)
    assert rr.sync(root) == 0
    assert (
        rr.gate(
            root,
            action="assistant-pack",
            roadmap_id=None,
            step_id=None,
            work_id=None,
            front=str(front.relative_to(root)),
        )
        == 0
    )
    captured = capsys.readouterr().out
    assert "WORK_FRONT_GATE=PASS" in captured
    assert "ROADMAP_GATE=PASS" in captured
