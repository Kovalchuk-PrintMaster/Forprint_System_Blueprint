from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.coordination import continuity
from scripts.coordination import continuity_lifecycle as lifecycle
from scripts.validation.validate_continuity_lifecycle_v0_1 import (
    validate_lifecycle_semantics,
)


def _git(root: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    return cp.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "forprint@example.invalid")
    _git(root, "config", "user.name", "ForPrint Test")
    (root / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    _git(root, "add", "tracked.txt")
    _git(root, "commit", "-m", "baseline")
    return root


def _checkpoint(
    root: Path,
    event_root: Path,
    *,
    work_id: str,
    event_id: str,
    bootstrap_historical_import: bool = False,
) -> Path:
    digest = hashlib.sha256((root / "tracked.txt").read_bytes()).hexdigest()
    hashes = {"tracked.txt": digest}
    state = continuity.build_source_state(
        root,
        bounded_final_applied_artifact_hashes=hashes,
    )
    spec = {
        "schema_version": continuity.SPEC_SCHEMA,
        "event_id": event_id,
        "work_id": work_id,
        "occurred_at": "2026-09-11T10:00:00Z",
        "actor": "test",
        "summary": "checkpoint",
        "bootstrap_historical_import": bootstrap_historical_import,
        "what_changed": ["test change"],
        "why": "test lifecycle",
        "evidence": [{"kind": "test", "result": "PASS"}],
        "decision_rationale": "test lifecycle contract",
        "rejected_alternative_when_material": "none",
        "blockers": [],
        "unknowns": [],
        "next_actions": [
            {"order": 1, "id": "a"},
            {"order": 2, "id": "b"},
            {"order": 3, "id": "c"},
            {"order": 4, "id": "d"},
            {"order": 5, "id": "e"},
        ],
        "source_state_before": state,
        "source_state_after": state,
        "final_applied_artifact_hashes": hashes,
        "external_baseline_preserved": True,
    }
    spec_path = root / "tmp" / f"{event_id}.yaml"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        yaml.safe_dump(spec, sort_keys=False),
        encoding="utf-8",
    )
    return continuity.append_checkpoint(
        root=root,
        spec_path=spec_path,
        event_root=event_root,
    )


def test_full_lifecycle_and_closed_immutability(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    event_root = root / "coordination/continuity/events"

    lifecycle.plan(
        root=root,
        event_root=event_root,
        event_id="evt-test-plan",
        work_id="work-test",
        actor="test",
        summary="planned",
        reason="test",
    )
    lifecycle.activate(
        root=root,
        event_root=event_root,
        event_id="evt-test-active",
        work_id="work-test",
        actor="test",
        summary="active",
        reason="start",
    )
    _checkpoint(
        root,
        event_root,
        work_id="work-test",
        event_id="evt-test-checkpoint",
    )
    lifecycle.validation_passed(
        root=root,
        event_root=event_root,
        event_id="evt-test-validated",
        work_id="work-test",
        actor="test",
        summary="validated",
        evidence=["pytest"],
    )
    lifecycle.close(
        root=root,
        event_root=event_root,
        event_id="evt-test-closed",
        work_id="work-test",
        actor="test",
        summary="closed",
        evidence=["pytest", "continuity validation"],
    )

    states = lifecycle.work_states(event_root)
    assert states["work-test"]["state"] == "CLOSED"

    with pytest.raises(lifecycle.LifecycleError, match="invalid from CLOSED|immutable"):
        lifecycle.activate(
            root=root,
            event_root=event_root,
            event_id="evt-test-reopen",
            work_id="work-test",
            actor="test",
            summary="reopen",
            reason="forbidden",
            remediation=True,
        )


def test_direct_active_to_closed_is_forbidden(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    event_root = root / "coordination/continuity/events"
    lifecycle.plan(
        root=root,
        event_root=event_root,
        event_id="evt-direct-plan",
        work_id="work-direct",
        actor="test",
        summary="planned",
        reason="test",
    )
    lifecycle.activate(
        root=root,
        event_root=event_root,
        event_id="evt-direct-active",
        work_id="work-direct",
        actor="test",
        summary="active",
        reason="start",
    )
    with pytest.raises(lifecycle.LifecycleError, match="requires VALIDATED"):
        lifecycle.close(
            root=root,
            event_root=event_root,
            event_id="evt-direct-close",
            work_id="work-direct",
            actor="test",
            summary="close",
            evidence=["invalid direct close"],
        )


def test_validation_failure_returns_to_active(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    event_root = root / "coordination/continuity/events"
    lifecycle.plan(
        root=root,
        event_root=event_root,
        event_id="evt-rem-plan",
        work_id="work-rem",
        actor="test",
        summary="planned",
        reason="test",
    )
    lifecycle.activate(
        root=root,
        event_root=event_root,
        event_id="evt-rem-active",
        work_id="work-rem",
        actor="test",
        summary="active",
        reason="start",
    )
    _checkpoint(
        root,
        event_root,
        work_id="work-rem",
        event_id="evt-rem-checkpoint",
    )
    lifecycle.validation_failed(
        root=root,
        event_root=event_root,
        event_id="evt-rem-failed",
        work_id="work-rem",
        actor="test",
        summary="failed",
        reason="gate failed",
        evidence=["pytest failure"],
    )
    assert lifecycle.work_states(event_root)["work-rem"]["state"] == "ACTIVE"


def test_nonempty_blockers_require_explicit_deferral(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    event_root = root / "coordination/continuity/events"
    lifecycle.plan(
        root=root,
        event_root=event_root,
        event_id="evt-block-plan",
        work_id="work-block",
        actor="test",
        summary="planned",
        reason="test",
    )
    lifecycle.activate(
        root=root,
        event_root=event_root,
        event_id="evt-block-active",
        work_id="work-block",
        actor="test",
        summary="active",
        reason="start",
    )

    digest = hashlib.sha256((root / "tracked.txt").read_bytes()).hexdigest()
    hashes = {"tracked.txt": digest}
    state = continuity.build_source_state(
        root,
        bounded_final_applied_artifact_hashes=hashes,
    )
    spec = {
        "schema_version": continuity.SPEC_SCHEMA,
        "event_id": "evt-block-checkpoint",
        "work_id": "work-block",
        "occurred_at": "2026-09-11T10:00:00Z",
        "actor": "test",
        "summary": "checkpoint with blocker",
        "what_changed": ["test"],
        "why": "test blocker close gate",
        "evidence": [{"kind": "test", "result": "PASS"}],
        "decision_rationale": "test",
        "rejected_alternative_when_material": "none",
        "blockers": ["external dependency"],
        "unknowns": [],
        "next_actions": [{"order": i, "id": f"a{i}"} for i in range(1, 6)],
        "source_state_before": state,
        "source_state_after": state,
        "final_applied_artifact_hashes": hashes,
        "external_baseline_preserved": True,
    }
    spec_path = root / "tmp/block.yaml"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    continuity.append_checkpoint(
        root=root,
        spec_path=spec_path,
        event_root=event_root,
    )
    lifecycle.validation_passed(
        root=root,
        event_root=event_root,
        event_id="evt-block-validated",
        work_id="work-block",
        actor="test",
        summary="validated",
        evidence=["pytest"],
    )

    with pytest.raises(lifecycle.LifecycleError, match="explicit"):
        lifecycle.close(
            root=root,
            event_root=event_root,
            event_id="evt-block-close-fail",
            work_id="work-block",
            actor="test",
            summary="close",
            evidence=["pytest"],
        )

    lifecycle.close(
        root=root,
        event_root=event_root,
        event_id="evt-block-close",
        work_id="work-block",
        actor="test",
        summary="close deferred",
        evidence=["pytest"],
        defer_all_blockers=True,
        defer_rationale="explicitly deferred to follow-up work",
    )
    assert lifecycle.work_states(event_root)["work-block"]["state"] == "CLOSED"


def test_legacy_supersede_boundary(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    event_root = root / "coordination/continuity/events"
    _checkpoint(
        root,
        event_root,
        work_id="legacy-work",
        event_id="evt-legacy-checkpoint",
    )
    lifecycle.supersede_legacy(
        root=root,
        event_root=event_root,
        event_id="evt-legacy-superseded",
        work_id="legacy-work",
        actor="test",
        summary="legacy migrated closed",
        superseded_by_work_id="replacement-work",
        enforcement_boundary_sequence=1,
        reason="pre-enforcement migration",
    )
    assert lifecycle.work_states(event_root)["legacy-work"]["state"] == "CLOSED"


def test_historical_import_is_not_live_work_and_reserves_work_id(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    event_root = root / "coordination/continuity/events"
    _checkpoint(
        root,
        event_root,
        work_id="historical-work",
        event_id="evt-historical-checkpoint",
        bootstrap_historical_import=True,
    )

    assert "historical-work" not in lifecycle.work_states(event_root)
    with pytest.raises(lifecycle.LifecycleError, match="unused work_id"):
        lifecycle.plan(
            root=root,
            event_root=event_root,
            event_id="evt-historical-reuse",
            work_id="historical-work",
            actor="test",
            summary="forbidden reuse",
            reason="must use new work id",
        )


def test_validation_is_scoped_to_its_own_checkpoint(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    event_root = root / "coordination/continuity/events"

    lifecycle.plan(
        root=root,
        event_root=event_root,
        event_id="evt-a-plan",
        work_id="work-a",
        actor="test",
        summary="a planned",
        reason="test",
    )
    lifecycle.activate(
        root=root,
        event_root=event_root,
        event_id="evt-a-active",
        work_id="work-a",
        actor="test",
        summary="a active",
        reason="start",
    )
    _checkpoint(
        root,
        event_root,
        work_id="work-a",
        event_id="evt-a-checkpoint",
    )

    (root / "tracked.txt").write_text("changed by work b\n", encoding="utf-8")
    lifecycle.plan(
        root=root,
        event_root=event_root,
        event_id="evt-b-plan",
        work_id="work-b",
        actor="test",
        summary="b planned",
        reason="test",
    )
    lifecycle.activate(
        root=root,
        event_root=event_root,
        event_id="evt-b-active",
        work_id="work-b",
        actor="test",
        summary="b active",
        reason="start",
    )
    _checkpoint(
        root,
        event_root,
        work_id="work-b",
        event_id="evt-b-checkpoint",
    )

    with pytest.raises(lifecycle.LifecycleError, match="unreconciled"):
        lifecycle.validation_passed(
            root=root,
            event_root=event_root,
            event_id="evt-a-validate",
            work_id="work-a",
            actor="test",
            summary="a validate",
            evidence=["pytest"],
        )


def test_canonical_checkpoint_writer_requires_active_when_enforced(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    event_root = root / "coordination/continuity/events"
    contract_path = root / "coordination/standards/automation/continuity_contract_v0_1.yaml"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        yaml.safe_dump(
            {
                "lifecycle": {
                    "enforcement": {
                        "enabled": True,
                    }
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    spec = _spec_for_guard = {
        "schema_version": continuity.SPEC_SCHEMA,
        "event_id": "evt-guard-checkpoint",
        "work_id": "work-guard",
        "occurred_at": "2026-09-11T10:00:00Z",
        "actor": "test",
        "summary": "guard checkpoint",
        "what_changed": ["test"],
        "why": "test direct checkpoint admission",
        "evidence": [{"kind": "test", "result": "PASS"}],
        "decision_rationale": "test",
        "rejected_alternative_when_material": "none",
        "blockers": [],
        "unknowns": [],
        "next_actions": [{"order": i, "id": f"a{i}"} for i in range(1, 6)],
        "external_baseline_preserved": True,
    }
    digest = hashlib.sha256((root / "tracked.txt").read_bytes()).hexdigest()
    hashes = {"tracked.txt": digest}
    state = continuity.build_source_state(
        root,
        bounded_final_applied_artifact_hashes=hashes,
    )
    _spec_for_guard["source_state_before"] = state
    _spec_for_guard["source_state_after"] = state
    _spec_for_guard["final_applied_artifact_hashes"] = hashes
    spec_path = root / "tmp/guard.yaml"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        yaml.safe_dump(spec, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(continuity.ContinuityError, match="requires ACTIVE"):
        continuity.append_checkpoint(
            root=root,
            spec_path=spec_path,
            event_root=event_root,
        )

    lifecycle.plan(
        root=root,
        event_root=event_root,
        event_id="evt-guard-plan",
        work_id="work-guard",
        actor="test",
        summary="planned",
        reason="test",
    )
    lifecycle.activate(
        root=root,
        event_root=event_root,
        event_id="evt-guard-active",
        work_id="work-guard",
        actor="test",
        summary="active",
        reason="start",
    )
    appended = continuity.append_checkpoint(
        root=root,
        spec_path=spec_path,
        event_root=event_root,
    )
    assert appended.is_file()


def test_validator_accepts_enforced_stream(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract_dir = root / "coordination/standards/automation"
    contract_dir.mkdir(parents=True)
    contract = {
        "event_model": {
            "event_types": [
                "WORK_PLANNED",
                "WORK_ACTIVATED",
                "CHECKPOINT_RECORDED",
                "VALIDATION_PASSED",
                "VALIDATION_FAILED",
                "WORK_CLOSED",
                "WORK_SUPERSEDED",
            ]
        },
        "lifecycle": {
            "enforcement": {
                "enabled": True,
                "pre_enforcement_boundary_sequence": 1,
                "pre_enforcement_boundary_event_id": "evt-legacy-checkpoint",
            }
        },
    }
    event_root = root / "coordination/continuity/events"
    _checkpoint(
        root,
        event_root,
        work_id="legacy-work",
        event_id="evt-legacy-checkpoint",
    )
    (contract_dir / "continuity_contract_v0_1.yaml").write_text(
        yaml.safe_dump(contract, sort_keys=False),
        encoding="utf-8",
    )
    lifecycle.plan(
        root=root,
        event_root=event_root,
        event_id="evt-new-plan",
        work_id="new-work",
        actor="test",
        summary="planned",
        reason="test",
    )
    lifecycle.activate(
        root=root,
        event_root=event_root,
        event_id="evt-new-active",
        work_id="new-work",
        actor="test",
        summary="active",
        reason="start",
    )
    _checkpoint(
        root,
        event_root,
        work_id="new-work",
        event_id="evt-new-checkpoint",
    )
    lifecycle.validation_passed(
        root=root,
        event_root=event_root,
        event_id="evt-new-validated",
        work_id="new-work",
        actor="test",
        summary="validated",
        evidence=["pytest"],
    )
    lifecycle.close(
        root=root,
        event_root=event_root,
        event_id="evt-new-closed",
        work_id="new-work",
        actor="test",
        summary="closed",
        evidence=["pytest"],
    )

    ok, reason, details = validate_lifecycle_semantics(
        root=root,
        event_root=event_root,
    )
    assert ok, reason
    assert details["work_states"]["new-work"] == "CLOSED"
