from pathlib import Path

import yaml

REGISTRY = Path(
    "coordination/internal_work/blueprint/module_preparation/module_preparation_registry_v0_1.yaml"
)
QUEUE = Path(
    "coordination/internal_work/blueprint/module_preparation/module_preparation_queue_v0_1.yaml"
)


def _registry() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


def _queue() -> dict:
    return yaml.safe_load(QUEUE.read_text(encoding="utf-8"))


def test_portfolio_has_23_inventory_modules() -> None:
    registry = _registry()
    assert registry["module_count"] == 23
    assert len(registry["modules"]) == 23


def test_logistics_is_bootstrap_ready_but_release_blocked() -> None:
    logistics = next(
        row for row in _registry()["modules"] if row["module_id"] == "logistics_service"
    )
    assert logistics["preparation_state"] == "BOOTSTRAP_READY"
    assert logistics["bootstrap_prompt_state"] == (
        "REPLACEMENT_CANDIDATE_AWAITING_EXPLICIT_RELEASE_AUTHORIZATION"
    )
    assert "BOOTSTRAP_REPLACEMENT_PROMPT_RELEASE_AUTHORIZATION_REQUIRED" in (logistics["blockers"])


def test_inspector_obligations_are_visible_before_inventory() -> None:
    inspector = next(
        row for row in _registry()["modules"] if row["module_id"] == "forprint_project_inspector"
    )
    assert inspector["preparation_state"] == "DISCOVERED"
    assert inspector["pending_blueprint_obligation_count"] == 9
    assert "FORENSIC_INVENTORY_NOT_STARTED" in inspector["blockers"]


def test_inspector_repository_provisioning_gap_blocks_forensic_inventory() -> None:
    registry = _registry()
    queue = _queue()
    inspector = next(
        row for row in registry["modules"] if row["module_id"] == "forprint_project_inspector"
    )
    queue_row = next(
        row for row in queue["queue_rows"] if row["module_id"] == "forprint_project_inspector"
    )
    assert inspector["repository_url"] is None
    assert inspector["repository_status"] == "planned_directory_created"
    assert inspector["repository_path_exists"] is True
    assert inspector["repository_git_detected"] is False
    assert inspector["repository_provisioning_required"] is True
    assert "REPOSITORY_PROVISIONING_REQUIRED" in inspector["blockers"]
    assert queue_row["action"] == "AWAIT_EXPLICIT_REPOSITORY_PROVISIONING_AUTHORITY"
    assert queue_row["dispatch_allowed"] is False


def test_historical_modules_remain_explicitly_high_risk() -> None:
    modules = {row["module_id"]: row for row in _registry()["modules"]}
    assert modules["calculator_engine"]["historical_legacy_risk"] is True
    assert modules["telegram_bot"]["historical_legacy_risk"] is True


def test_registry_queue_never_select_development_priority_or_dispatch() -> None:
    registry = _registry()
    queue = _queue()
    assert registry["development_priority_selection_allowed"] is False
    assert registry["worker_launch_allowed"] is False
    assert queue["development_priority_selection_performed"] is False
    assert queue["worker_launch_allowed"] is False
    assert all(row["dispatch_allowed"] is False for row in queue["queue_rows"])
