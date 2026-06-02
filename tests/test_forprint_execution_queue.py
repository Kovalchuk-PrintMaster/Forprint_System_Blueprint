from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_forprint_execution_queue_file_exists() -> None:
    assert (ROOT / "machine" / "forprint_execution_queue.yaml").exists()


def test_forprint_execution_queue_has_required_priority_sections() -> None:
    data = _load_yaml(ROOT / "machine" / "forprint_execution_queue.yaml")

    priorities = data["execution_queue"]["priorities"]

    assert "p0" in priorities
    assert "p1" in priorities
    assert "p2" in priorities


def test_operational_registry_is_marked_as_internal_data_custodian() -> None:
    data = _load_yaml(ROOT / "machine" / "forprint_execution_queue.yaml")

    decisions = {
        item["id"]: item
        for item in data["execution_queue"]["active_decisions"]
    }

    decision = decisions["operational_registry_internal_data_custodian"]

    assert decision["status"] == "accepted"
    assert decision["owner_module"] == "forprint_operational_registry"
    assert "internal ForPrint database" in decision["summary"]


def test_library_is_marked_as_canonical_semantic_authority() -> None:
    data = _load_yaml(ROOT / "machine" / "forprint_execution_queue.yaml")

    decisions = {
        item["id"]: item
        for item in data["execution_queue"]["active_decisions"]
    }

    decision = decisions["library_canonical_semantic_authority"]

    assert decision["status"] == "accepted"
    assert decision["owner_module"] == "forprint_library"
    assert "canonical product/service/material/operation IDs" in decision["summary"]


def test_calculator_is_marked_as_primary_order_formalization_point() -> None:
    data = _load_yaml(ROOT / "machine" / "forprint_execution_queue.yaml")

    decisions = {
        item["id"]: item
        for item in data["execution_queue"]["active_decisions"]
    }

    decision = decisions["calculator_primary_order_formalization_point"]

    assert decision["status"] == "accepted"
    assert decision["owner_module"] == "calculator_engine"
    assert "primary formalization point" in decision["title"]
    assert "primarily pass through Calculator" in decision["summary"]


def test_accounting_registry_v0_5_is_waiting_for_real_sanitized_samples() -> None:
    data = _load_yaml(ROOT / "machine" / "forprint_execution_queue.yaml")

    waiting_items = {
        item["module_id"]: item
        for item in data["execution_queue"]["blocked_or_waiting"]
    }

    accounting = waiting_items["forprint_accounting_registry_service"]

    assert accounting["waiting_for"] == "real_sanitized_one_c_export_samples"
    assert accounting["next_allowed_step"] == "real_export_profile_pack"
    assert "live_1c_write" in accounting["forbidden_until_approved"]


def test_control_plane_is_planned_and_deferred() -> None:
    data = _load_yaml(ROOT / "machine" / "forprint_execution_queue.yaml")

    assert (
        data["execution_queue"]["control_plane_status"]
        == "planned_high_priority_deferred_until_core_modules_alive"
    )

    p2_items = {
        item["module_id"]: item
        for item in data["execution_queue"]["priorities"]["p2"]
    }

    assert p2_items["forprint_control_plane"]["status"] == "planned_high_priority_deferred"


def test_gateway_is_not_p0() -> None:
    data = _load_yaml(ROOT / "machine" / "forprint_execution_queue.yaml")

    p0_modules = {
        item["module_id"]
        for item in data["execution_queue"]["priorities"]["p0"]
    }

    assert "forprint_integration_gateway" not in p0_modules


def test_operational_registry_v0_6_is_queued_as_p1() -> None:
    data = _load_yaml(ROOT / "machine" / "forprint_execution_queue.yaml")

    p1_items = {
        item["id"]: item
        for item in data["execution_queue"]["priorities"]["p1"]
    }

    item = p1_items["operational_registry_v0_6_core_data_model"]

    assert item["module_id"] == "forprint_operational_registry"
    assert item["status"] == "queued"


def test_library_canonical_governance_is_queued_as_p1() -> None:
    data = _load_yaml(ROOT / "machine" / "forprint_execution_queue.yaml")

    p1_items = {
        item["id"]: item
        for item in data["execution_queue"]["priorities"]["p1"]
    }

    item = p1_items["library_canonical_product_service_governance"]

    assert item["module_id"] == "forprint_library"
    assert item["status"] == "queued"


def test_module_status_reporting_standard_is_declared() -> None:
    data = _load_yaml(ROOT / "machine" / "forprint_execution_queue.yaml")

    standard = data["execution_queue"]["module_status_reporting_standard"]

    assert standard["status"] == "queued"
    assert standard["required_directory"] == "coordination/status"
    assert "coordination/status/current_status.yaml" in standard["required_files"]


def test_human_execution_queue_document_exists() -> None:
    assert (ROOT / "human" / "forprint_execution_queue.md").exists()


def test_adr_0013_exists() -> None:
    assert (ROOT / "adr" / "0013-strategic-agreements-and-execution-queue.md").exists()
