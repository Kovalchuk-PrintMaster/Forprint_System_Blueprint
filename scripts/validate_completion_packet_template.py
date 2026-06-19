from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = PROJECT_ROOT / "tools" / "completion_packet_template"

REQUIRED_TEMPLATE_FILES: tuple[str, ...] = (
    "README.md",
    "Makefile.fragment",
    "completion_packet.example.yaml",
    "validate_completion_packet.py",
    "apply_completion_packet.py",
)

REQUIRED_PACKET_FIELDS: tuple[str, ...] = (
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
)


def _load_example_packet(template_root: Path) -> dict[str, Any]:
    path = template_root / "completion_packet.example.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("completion packet example root must be a mapping")
    return data


def _require_non_empty_list(
    packet: dict[str, Any],
    field_name: str,
    errors: list[str],
) -> None:
    value = packet.get(field_name)
    if not isinstance(value, list) or not value:
        errors.append(f"completion_packet.example.yaml `{field_name}` must be non-empty")


def validate_template(project_root: Path = PROJECT_ROOT) -> list[str]:
    """Validate completion packet template files and contract."""

    errors: list[str] = []
    template_root = project_root / "tools" / "completion_packet_template"

    for relative_path in REQUIRED_TEMPLATE_FILES:
        if not (template_root / relative_path).exists():
            errors.append(
                f"missing template file: tools/completion_packet_template/{relative_path}"
            )

    if errors:
        return errors

    packet = _load_example_packet(template_root)

    for field_name in REQUIRED_PACKET_FIELDS:
        if field_name not in packet:
            errors.append(f"example packet missing required field: {field_name}")

    report_path = packet.get("report_path")
    if not isinstance(report_path, str) or not report_path.startswith(
        "coordination/reports/completion/"
    ):
        errors.append(
            "example packet report_path must be under coordination/reports/completion/"
        )

    _require_non_empty_list(packet, "implemented", errors)
    _require_non_empty_list(packet, "instruction_sources_reviewed", errors)
    _require_non_empty_list(packet, "standards_reviewed", errors)
    _require_non_empty_list(packet, "standards_alignment_notes", errors)
    _require_non_empty_list(packet, "current_outputs", errors)
    _require_non_empty_list(packet, "next_recommended_steps", errors)

    checks = packet.get("checks")
    if not isinstance(checks, dict):
        errors.append("example packet checks must be a mapping")
    else:
        for check_name in REQUIRED_CHECKS:
            if check_name not in checks:
                errors.append(f"example packet missing checks.{check_name}")

    boundary_confirmation = packet.get("boundary_confirmation")
    if not isinstance(boundary_confirmation, dict):
        errors.append("example packet boundary_confirmation must be a mapping")
    else:
        for flag_name in REQUIRED_BOUNDARY_FLAGS:
            if boundary_confirmation.get(flag_name) is not True:
                errors.append(
                    f"example packet boundary_confirmation.{flag_name} must be true"
                )

    readme = (template_root / "README.md").read_text(encoding="utf-8")
    for required_phrase in (
        "contract-first",
        "idempotent",
        "instruction_sources_reviewed",
        "standards_reviewed",
        "standards_alignment_notes",
        "boundary_confirmation",
        "no_production_api",
        "timestamp",
    ):
        if required_phrase not in readme:
            errors.append(f"README.md must mention `{required_phrase}`")

    make_fragment = (template_root / "Makefile.fragment").read_text(encoding="utf-8")
    for target_name in ("completion-packet-validate", "completion-packet-apply"):
        if target_name not in make_fragment:
            errors.append(f"Makefile.fragment missing target `{target_name}`")

    validator = (template_root / "validate_completion_packet.py").read_text(
        encoding="utf-8"
    )
    for symbol in ("REQUIRED_FIELDS", "REQUIRED_BOUNDARY_FLAGS", "REQUIRED_CHECKS"):
        if symbol not in validator:
            errors.append(f"validate_completion_packet.py missing `{symbol}`")

    applier = (template_root / "apply_completion_packet.py").read_text(
        encoding="utf-8"
    )
    for symbol in (
        "text_write_if_changed",
        "yaml_write_if_changed",
        "update_reports_index",
        "apply_completion_packet",
    ):
        if symbol not in applier:
            errors.append(f"apply_completion_packet.py missing `{symbol}`")

    return errors


def main() -> int:
    errors = validate_template()
    if errors:
        print("❌ Completion packet template validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("✅ Completion packet template validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
