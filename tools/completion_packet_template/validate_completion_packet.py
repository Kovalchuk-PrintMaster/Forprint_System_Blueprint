from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

EXPECTED_MODULE_ID = "example_module_id"

REQUIRED_FIELDS: tuple[str, ...] = (
    "completion_id",
    "module_id",
    "module_name",
    "phase",
    "prompt_id",
    "report_id",
    "report_path",
    "created_at",
    "summary",
    "implemented",
    "checks",
    "instruction_sources_reviewed",
    "standards_reviewed",
    "standards_alignment_notes",
    "boundary_confirmation",
    "current_outputs",
    "next_recommended_steps",
    "next_questions_for_blueprint",
)

REQUIRED_CHECKS: tuple[str, ...] = (
    "check_report",
    "tests",
    "governance_check",
)

REQUIRED_BOUNDARY_FLAGS: tuple[str, ...] = (
    "no_production_api",
    "no_live_external_integrations",
    "no_real_1c_sync",
    "no_production_write",
    "no_automatic_posting",
    "no_accounting_payment_truth",
    "no_crm_dashboard",
    "no_telegram_runtime_ui",
    "no_calculator_final_price_ownership",
    "no_library_catalog_ownership",
    "no_warehouse_stock_truth",
    "no_prepress_lifecycle_ownership",
)


class CompletionPacketError(ValueError):
    """Raised when a completion packet is invalid."""


def load_completion_packet(path: Path) -> dict[str, Any]:
    """Load completion packet YAML."""

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CompletionPacketError("completion packet root must be a mapping")
    return data


def _require_non_empty_list(
    packet: dict[str, Any],
    field_name: str,
    errors: list[str],
) -> None:
    value = packet.get(field_name)
    if not isinstance(value, list) or not value:
        errors.append(f"`{field_name}` must be a non-empty list")


def validate_completion_packet(packet: dict[str, Any]) -> list[str]:
    """Return validation errors for a completion packet."""

    errors: list[str] = []

    for field_name in REQUIRED_FIELDS:
        if field_name not in packet:
            errors.append(f"missing required field: {field_name}")

    if packet.get("module_id") != EXPECTED_MODULE_ID:
        errors.append(f"`module_id` must be `{EXPECTED_MODULE_ID}`")

    report_id = packet.get("report_id")
    if not isinstance(report_id, str) or not report_id.strip():
        errors.append("`report_id` must be a non-empty string")

    report_path = packet.get("report_path")
    if not isinstance(report_path, str) or not report_path.strip():
        errors.append("`report_path` must be a non-empty string")
    elif not report_path.startswith("coordination/reports/completion/"):
        errors.append("`report_path` must be under coordination/reports/completion/")

    _require_non_empty_list(packet, "instruction_sources_reviewed", errors)
    _require_non_empty_list(packet, "standards_reviewed", errors)
    _require_non_empty_list(packet, "standards_alignment_notes", errors)

    checks = packet.get("checks")
    if not isinstance(checks, dict):
        errors.append("`checks` must be a mapping")
    else:
        for check_name in REQUIRED_CHECKS:
            if check_name not in checks:
                errors.append(f"`checks.{check_name}` is required")

    boundary_confirmation = packet.get("boundary_confirmation")
    if not isinstance(boundary_confirmation, dict):
        errors.append("`boundary_confirmation` must be a mapping")
    else:
        for flag_name in REQUIRED_BOUNDARY_FLAGS:
            if boundary_confirmation.get(flag_name) is not True:
                errors.append(f"`boundary_confirmation.{flag_name}` must be true")

    return errors


def assert_valid_completion_packet(packet: dict[str, Any]) -> None:
    """Raise CompletionPacketError if packet is invalid."""

    errors = validate_completion_packet(packet)
    if errors:
        raise CompletionPacketError(
            "completion packet validation failed:\n- " + "\n- ".join(errors)
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a completion packet.")
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()

    try:
        packet = load_completion_packet(args.packet)
        assert_valid_completion_packet(packet)
    except (CompletionPacketError, FileNotFoundError, yaml.YAMLError) as exc:
        print(f"❌ {exc}")
        return 1

    print(f"✅ Completion packet is valid: {args.packet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
