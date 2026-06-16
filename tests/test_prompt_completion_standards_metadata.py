from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "tools" / "module_coordination_template" / "validate_prompt_completion_report.py"
APPLY_PATH = ROOT / "tools" / "module_coordination_template" / "apply_prompt_completion_report.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_report(path: Path, extra_frontmatter: dict | None = None) -> None:
    frontmatter = {
        "report_id": "gateway_blueprint_standards_visibility_ready",
        "prompt_id": "gateway_blueprint_standards_visibility_advisory_alignment_v0_7",
        "target_module": "forprint_integration_gateway",
        "phase": "blueprint_standards_visibility_advisory_alignment_v0_7",
        "completed_step": "gateway_blueprint_standards_visibility_ready",
        "status": "completed_in_module",
        "implementation_commit": "abc1234",
        "checks": {
            "governance_check": "ok",
            "make_check": "ok",
            "make_check_report": "ok",
            "blueprint_standards_check": "ok",
        },
        "boundary_confirmation": {
            "no_production_api_added": True,
            "no_real_external_integrations_added": True,
            "no_database_ownership_added": True,
            "no_operational_data_ownership_added": True,
            "no_queue_redis_s3_dependency_added": True,
            "no_1c_writes_added": True,
            "no_automatic_posting_added": True,
            "no_final_price_calculation_added": True,
        },
    }
    if extra_frontmatter:
        frontmatter.update(extra_frontmatter)

    path.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, sort_keys=False)
        + "---\n\n# Completion report\n",
        encoding="utf-8",
    )


def test_completion_report_accepts_standards_metadata(tmp_path: Path) -> None:
    validator = load_module(VALIDATOR_PATH, "validate_prompt_completion_report_standards")
    report = tmp_path / "completion.md"
    write_report(
        report,
        {
            "standards_reviewed": [
                "coordination/standards/index.yaml",
                {
                    "standard_id": "module_standards_awareness_protocol",
                    "file": "module_standards_awareness_protocol.md",
                },
            ],
            "standards_alignment_notes": [
                "Standards were reviewed as advisory guidance.",
                "No destructive refactor was performed.",
            ],
        },
    )

    assert validator.validate_completion_report(report) == []


def test_completion_report_rejects_malformed_standards_metadata(tmp_path: Path) -> None:
    validator = load_module(VALIDATOR_PATH, "validate_prompt_completion_report_standards_bad")
    report = tmp_path / "completion.md"
    write_report(
        report,
        {
            "standards_reviewed": "coordination/standards/index.yaml",
            "standards_alignment_notes": ["Reviewed."],
        },
    )

    issues = validator.validate_completion_report(report)

    assert any("standards_reviewed" in issue for issue in issues)


def test_apply_carries_standards_metadata_into_reports_index(tmp_path: Path) -> None:
    apply_module = load_module(APPLY_PATH, "apply_prompt_completion_report_standards")
    report = tmp_path / "coordination" / "reports" / "completion.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    write_report(
        report,
        {
            "standards_reviewed": ["coordination/standards/index.yaml"],
            "standards_alignment_notes": ["Standards visibility was checked."],
        },
    )

    result = apply_module.apply_prompt_completion_report(report, write=True, module_root=tmp_path)

    assert result["ok"] is True

    reports_index = yaml.safe_load(
        (tmp_path / "coordination" / "reports" / "index.yaml").read_text(encoding="utf-8")
    )
    record = reports_index["reports"][0]

    assert record["standards_reviewed"] == ["coordination/standards/index.yaml"]
    assert record["standards_alignment_notes"] == ["Standards visibility was checked."]
