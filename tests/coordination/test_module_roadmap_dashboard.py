from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.coordination.module_roadmap import (
    RoadmapError,
    load_yaml_file,
    render_modules_summary,
    render_roadmap_dashboard,
    resolve_roadmap_path,
    validate_roadmap_document,
)


def test_valid_module_roadmap_passes_validation(tmp_path: Path) -> None:
    root = _write_roadmap(tmp_path, module="forprint_library")

    path = resolve_roadmap_path(root=root, module="forprint_library")
    data = load_yaml_file(path)
    result = validate_roadmap_document(data, path=path)

    assert result.ok
    assert result.module == "forprint_library"
    assert result.step_count == 3
    assert result.current_step_id == "library_reference_contract_foundation_v0_2"


def test_dashboard_renders_current_step_window(tmp_path: Path) -> None:
    root = _write_roadmap(tmp_path, module="forprint_library")

    path = resolve_roadmap_path(root=root, module="forprint_library")
    data = load_yaml_file(path)
    dashboard = render_roadmap_dashboard(
        data,
        path=path,
        before_current=1,
        after_current=1,
        no_color=True,
    )

    assert "ForPrint Module Roadmap Dashboard" in dashboard
    assert "Module: forprint_library" in dashboard
    assert "┌" in dashboard
    assert "└" in dashboard
    assert "│ >  │ 2" in dashboard
    assert "library_reference_contract_foundation_v0_2" in dashboard
    assert "library_next_step_v0_3" in dashboard
    assert "\033[" not in dashboard

def test_colored_dashboard_preserves_terminal_reset_after_truncation(
    tmp_path: Path,
) -> None:
    root = _write_roadmap(tmp_path, module="forprint_library")

    path = resolve_roadmap_path(root=root, module="forprint_library")
    data = load_yaml_file(path)
    dashboard = render_roadmap_dashboard(
        data,
        path=path,
        before_current=1,
        after_current=1,
        no_color=False,
    )

    assert "┌" in dashboard
    assert "└" in dashboard
    assert "\033[0m" in dashboard
    assert dashboard.endswith("\033[0m")
    assert "\033[32maccepted" in dashboard
    assert "\033[31mcritical" in dashboard
    assert "critical…" not in dashboard

def test_colored_modules_summary_preserves_terminal_reset_after_truncation(
    tmp_path: Path,
) -> None:
    root = _write_roadmap(tmp_path, module="forprint_library")
    _write_roadmap(tmp_path, module="forprint_gateway")

    library_path = resolve_roadmap_path(root=root, module="forprint_library")
    gateway_path = resolve_roadmap_path(root=root, module="forprint_gateway")

    summary = render_modules_summary(
        [
            (library_path, load_yaml_file(library_path)),
            (gateway_path, load_yaml_file(gateway_path)),
        ],
        no_color=False,
    )

    assert "\033[0m" in summary
    assert summary.endswith("\033[0m")
    assert "\033[31mcritical" in summary
    assert "critical…" not in summary

def test_modules_summary_renders_multiple_modules(tmp_path: Path) -> None:
    root = _write_roadmap(tmp_path, module="forprint_library")
    _write_roadmap(tmp_path, module="forprint_gateway")

    library_path = resolve_roadmap_path(root=root, module="forprint_library")
    gateway_path = resolve_roadmap_path(root=root, module="forprint_gateway")

    summary = render_modules_summary(
        [
            (library_path, load_yaml_file(library_path)),
            (gateway_path, load_yaml_file(gateway_path)),
        ],
        no_color=True,
    )

    assert "ForPrint Module Roadmap Summary" in summary
    assert "┌" in summary
    assert "└" in summary
    assert "\033[" not in summary
    assert "forprint_library" in summary
    assert "forprint_gateway" in summary
    assert "library_next_step_v0_3" in summary


def test_validation_fails_for_unknown_current_step(tmp_path: Path) -> None:
    root = _write_roadmap(tmp_path, module="forprint_library")
    path = resolve_roadmap_path(root=root, module="forprint_library")
    data = load_yaml_file(path)

    data["metadata"]["current_step_id"] = "missing_step"

    result = validate_roadmap_document(data, path=path)

    assert not result.ok
    assert any("current_step_id" in error for error in result.errors)


def test_validation_fails_for_duplicate_step_id(tmp_path: Path) -> None:
    root = _write_roadmap(tmp_path, module="forprint_library")
    path = resolve_roadmap_path(root=root, module="forprint_library")
    data = load_yaml_file(path)

    data["roadmap"][1]["step_id"] = data["roadmap"][0]["step_id"]

    result = validate_roadmap_document(data, path=path)

    assert not result.ok
    assert any("duplicate step_id" in error for error in result.errors)


def test_resolve_roadmap_path_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(RoadmapError):
        resolve_roadmap_path(root=tmp_path, module="missing_module")


def _write_roadmap(tmp_path: Path, *, module: str) -> Path:
    roadmaps_dir = tmp_path / "coordination" / "roadmaps"
    roadmaps_dir.mkdir(parents=True, exist_ok=True)

    path = roadmaps_dir / f"{module}.yaml"
    path.write_text(
        yaml.safe_dump(
            _roadmap_data(module),
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return tmp_path


def _roadmap_data(module: str) -> dict[str, object]:
    prefix = "library" if module == "forprint_library" else "gateway"

    return {
        "schema_version": "module_development_roadmap_v0_1",
        "module": module,
        "metadata": {
            "owner": "forprint_system_blueprint",
            "status": "active",
            "purpose": "Test roadmap.",
            "current_step_id": f"{prefix}_reference_contract_foundation_v0_2",
            "default_dashboard_window": {
                "before_current": 5,
                "after_current": 10,
            },
        },
        "roadmap": [
            {
                "step_id": f"{prefix}_make_first_readiness_v0_1",
                "sequence": 1,
                "title": "Make-first readiness",
                "status": "accepted",
                "priority": "high",
                "owner_module": module,
                "scope": "foundation",
                "prompt": {
                    "prompt_id": f"{prefix}_make_first_readiness_v0_1",
                    "prompt_file": None,
                    "prompt_queue_sequence": 1,
                },
                "depends_on": [],
                "expected_outputs": ["Make targets available"],
                "evidence": {
                    "module_commit": "abc1234",
                    "blueprint_acceptance_commit": "def5678",
                    "completion_report": "coordination/reports/example.md",
                    "check_report": None,
                    "test_summary": "tests passed",
                },
                "notes": None,
            },
            {
                "step_id": f"{prefix}_reference_contract_foundation_v0_2",
                "sequence": 2,
                "title": "Reference contract foundation",
                "status": "active",
                "priority": "critical",
                "owner_module": module,
                "scope": "foundation",
                "prompt": {
                    "prompt_id": f"{prefix}_reference_contract_foundation_v0_2",
                    "prompt_file": None,
                    "prompt_queue_sequence": 2,
                },
                "depends_on": [
                    {
                        "type": "document",
                        "reference": "coordination/standards/example.md",
                        "status": "acknowledged",
                    },
                ],
                "expected_outputs": ["Reference contracts updated"],
                "evidence": {
                    "module_commit": None,
                    "blueprint_acceptance_commit": None,
                    "completion_report": None,
                    "check_report": None,
                    "test_summary": None,
                },
                "notes": None,
            },
            {
                "step_id": f"{prefix}_next_step_v0_3",
                "sequence": 3,
                "title": "Next step",
                "status": "ready",
                "priority": "normal",
                "owner_module": module,
                "scope": "next",
                "prompt": {
                    "prompt_id": None,
                    "prompt_file": None,
                    "prompt_queue_sequence": None,
                },
                "depends_on": [],
                "expected_outputs": ["Next outputs"],
                "evidence": {
                    "module_commit": None,
                    "blueprint_acceptance_commit": None,
                    "completion_report": None,
                    "check_report": None,
                    "test_summary": None,
                },
                "notes": None,
            },
        ],
        "status_values": [
            "planned",
            "ready",
            "active",
            "completed",
            "accepted",
            "paused",
            "blocked",
            "deferred",
            "cancelled",
            "superseded",
        ],
        "priority_values": [
            "critical",
            "high",
            "normal",
            "low",
            "reference",
        ],
        "dependency_types": [
            "module_step",
            "prompt",
            "document",
            "contract",
            "external_decision",
            "manual_review",
        ],
    }
