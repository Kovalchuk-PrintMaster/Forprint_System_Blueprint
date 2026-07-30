#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
MODULE_ID = "forprint_system_blueprint"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def load_renderer(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "inventory_status_renderer_for_consistency_gate",
        path,
    )

    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load renderer: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_metrics(
    wave: dict[str, Any],
    dashboard: dict[str, Any],
) -> dict[str, int]:
    combined = wave.get("combined_lower_bounds")

    if not isinstance(combined, dict):
        raise ValueError("combined_lower_bounds is missing")

    source_keys = {
        "tracked": "tracked_files",
        "reviewed": "wave_1_plus_wave_2_reviewed",
        "purpose": "purpose_evidenced",
        "dependencies": "dependencies_mapped",
        "verified": "fully_verified",
    }
    result: dict[str, int] = {}

    for output_key, source_key in source_keys.items():
        value = combined.get(source_key)

        if not isinstance(value, int) or value < 0:
            raise ValueError(f"invalid combined metric: {source_key}")

        result[output_key] = value

    summary = wave.get("summary")
    scope = dashboard.get("scope")

    if not isinstance(summary, dict):
        raise ValueError("Wave 2 summary is missing")

    if not isinstance(scope, dict):
        raise ValueError("dashboard scope is missing")

    extra = {
        "unknown_records": summary.get("records_with_unknowns"),
        "changed_paths": scope.get("changed_paths_since_rci_commit"),
        "scope_delta": scope.get("artifact_map_scope_delta"),
    }

    for key, value in extra.items():
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"invalid metric: {key}")

        result[key] = value

    return result


def rollout_state(
    maintenance: dict[str, Any],
) -> str | None:
    rollout = maintenance.get("external_rollout")

    if isinstance(rollout, dict):
        value = rollout.get("state")
        return value if isinstance(value, str) else None

    value = maintenance.get("external_rollout_state")
    return value if isinstance(value, str) else None


def validate_inventory_status(
    *,
    wave_path: Path,
    dashboard_path: Path,
    maintenance_path: Path,
    roadmap_path: Path,
    renderer_path: Path,
    module_id: str,
) -> dict[str, Any]:
    errors: list[str] = []
    wave = load_yaml(wave_path)
    dashboard = load_yaml(dashboard_path)
    maintenance = load_yaml(maintenance_path)
    roadmap = load_yaml(roadmap_path)

    try:
        expected = canonical_metrics(wave, dashboard)
    except ValueError as exc:
        return {
            "schema_version": ("blueprint_inventory_status_consistency_report_v0_1"),
            "metadata": {
                "result": "FAILED",
                "module_id": module_id,
            },
            "summary": {
                "error_count": 1,
                "metric_count": 0,
            },
            "errors": [str(exc)],
            "metrics": {},
        }

    renderer = load_renderer(renderer_path)

    if module_id != MODULE_ID:
        errors.append("requested module mismatch")

    if getattr(renderer, "SUPPORTED_MODULE", None) != MODULE_ID:
        errors.append("renderer supported module mismatch")

    try:
        actual = renderer.build_metrics(wave, dashboard)
    except Exception as exc:
        errors.append(f"renderer build_metrics failed: {exc}")
        actual = {}

    for key, expected_value in expected.items():
        actual_value = actual.get(key)

        if actual_value != expected_value:
            errors.append(
                f"metric mismatch for {key}: expected {expected_value!r}, found {actual_value!r}"
            )

    tracked = expected["tracked"]
    reviewed = expected["reviewed"]
    purpose = expected["purpose"]
    dependencies = expected["dependencies"]
    verified = expected["verified"]

    if tracked <= 0 or reviewed <= 0:
        errors.append("tracked and reviewed scopes must be positive")
        repository_lower_bound = 0.0
        reviewed_quality_lower_bound = 0.0
    else:
        repository_lower_bound = min(
            reviewed / tracked,
            purpose / tracked,
            dependencies / tracked,
            verified / tracked,
        )
        reviewed_quality_lower_bound = min(
            purpose / reviewed,
            dependencies / reviewed,
            verified / reviewed,
        )

    metadata = roadmap.get("metadata")
    current_step = metadata.get("current_step_id") if isinstance(metadata, dict) else None

    if not isinstance(current_step, str) or not current_step:
        errors.append("roadmap current_step_id is missing")

    state = rollout_state(maintenance)

    if state != "gated":
        errors.append(f"external rollout must remain gated, found {state!r}")

    try:
        rendered = renderer.render_inventory_status(
            wave,
            dashboard,
            maintenance,
            roadmap,
            module_id,
        )
    except Exception as exc:
        errors.append(f"renderer execution failed: {exc}")
        rendered = ""

    plain = ANSI_RE.sub("", rendered)
    required_fragments = [
        "Coverage and nested quality",
        "Metric dependencies",
        "Current blockers and drift",
        "How to read this status",
        f"{repository_lower_bound * 100:.2f}%",
        f"{reviewed_quality_lower_bound * 100:.2f}%",
        f"{purpose}/{tracked}",
        f"{dependencies}/{tracked}",
        f"{verified}/{tracked}",
        str(expected["unknown_records"]),
        str(expected["changed_paths"]),
        str(expected["scope_delta"]),
        str(current_step),
        "external rollout=gated",
    ]

    for fragment in required_fragments:
        if fragment not in plain:
            errors.append(f"rendered status lacks required fragment: {fragment!r}")

    local_summary = wave.get("summary")

    if isinstance(local_summary, dict) and tracked > 0:
        local_values = [
            local_summary.get("purpose_evidenced"),
            local_summary.get("dependencies_mapped"),
            local_summary.get("fully_verified"),
        ]

        if all(isinstance(value, int) for value in local_values):
            incorrect = min(local_values) / tracked
            incorrect_text = f"{incorrect * 100:.2f}%"
            correct_text = f"{repository_lower_bound * 100:.2f}%"

            if incorrect_text != correct_text and incorrect_text in plain:
                errors.append("Wave 2 local metrics are shown as repository totals")

    passed = not errors

    return {
        "schema_version": ("blueprint_inventory_status_consistency_report_v0_1"),
        "metadata": {
            "result": "PASSED" if passed else "FAILED",
            "module_id": module_id,
        },
        "summary": {
            "error_count": len(errors),
            "metric_count": len(expected),
            "repository_semantic_lower_bound": (repository_lower_bound),
            "reviewed_quality_lower_bound": (reviewed_quality_lower_bound),
            "external_rollout_state": state,
            "current_step_id": current_step,
        },
        "errors": errors,
        "metrics": {
            "canonical": expected,
            "renderer": actual,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", required=True)
    parser.add_argument("--dashboard", required=True)
    parser.add_argument("--maintenance", required=True)
    parser.add_argument("--roadmap", required=True)
    parser.add_argument("--renderer", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = validate_inventory_status(
        wave_path=Path(args.wave),
        dashboard_path=Path(args.dashboard),
        maintenance_path=Path(args.maintenance),
        roadmap_path=Path(args.roadmap),
        renderer_path=Path(args.renderer),
        module_id=args.module,
    )
    Path(args.output).write_text(
        yaml.safe_dump(
            report,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )
    return 0 if report["metadata"]["result"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
