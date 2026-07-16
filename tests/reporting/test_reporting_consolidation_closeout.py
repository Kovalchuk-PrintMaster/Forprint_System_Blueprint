from __future__ import annotations

import runpy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

MAKE_TEMPLATE = (
    ROOT
    / "coordination"
    / "templates"
    / "module_makefile_standard.template.mk"
)
MAKE_STANDARDS = (
    ROOT / "coordination" / "standards"
    / "module_governance_make_targets.md",
    ROOT / "coordination" / "standards"
    / "make_command_standard.md",
    ROOT / "coordination" / "standards"
    / "module_make_target_contract.md",
)
POLICY_README = ROOT / "coordination" / "module_policy" / "README.md"
COMPLETION_ROOT = ROOT / "tools" / "completion_packet_template"
REPORTING_AUDIT = ROOT / "scripts" / "reporting" / "audit_consolidation.py"

CLOSEOUT_ID = "reporting_consolidation_closed_v0_1"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_canonical_make_template_exposes_full_diagnostics_target() -> None:
    source = _read(MAKE_TEMPLATE)

    assert "check-report:" in source
    assert "check-report-full:" in source
    assert "status-report:" in source
    assert "NO_COLOR" in source


def test_make_standards_define_terminal_artifact_contract() -> None:
    combined = "\n".join(_read(path) for path in MAKE_STANDARDS)

    for required in (
        "compact operator-facing",
        "check-report-full",
        "JSON",
        "Markdown",
        "NO_COLOR=1",
        "read-only",
        "exit-code semantics",
    ):
        assert required in combined

    assert "--limitNO_COLOR" not in combined


def test_module_policy_references_canonical_make_standards() -> None:
    source = _read(POLICY_README)

    for required in (
        "Reporting and completion obligations",
        "module_governance_make_targets.md",
        "make_command_standard.md",
        "module_make_target_contract.md",
        "read-only",
        "NO_COLOR=1",
        "recovery",
    ):
        assert required in source


def test_completion_packet_documents_conditional_reporting_evidence() -> None:
    readme = _read(COMPLETION_ROOT / "README.md")
    packet = yaml.safe_load(
        _read(COMPLETION_ROOT / "completion_packet.example.yaml")
    )

    assert "Reporting evidence contract v0.1" in readme
    evidence = packet["reporting_evidence"]
    assert evidence["compact_check_report"] == "make check-report"
    assert evidence["full_diagnostics"] == "make check-report-full"
    assert evidence["no_color_verified"] is True
    assert evidence["artifact_paths"]
    assert evidence["read_only_checks_verified"]
    assert isinstance(evidence["deviations"], list)


def test_reporting_registry_is_exact_and_closed() -> None:
    module = runpy.run_path(
        str(REPORTING_AUDIT),
        run_name="reporting_closeout_contract_test",
    )

    default_targets = tuple(module["DEFAULT_TARGETS"])
    shared_core = set(module["SHARED_CORE"])
    consumers = set(module["CONSOLIDATED_CONSUMERS"])

    assert len(default_targets) == 16
    assert len(default_targets) == len(set(default_targets))
    assert len(shared_core) == 7
    assert len(consumers) == 9
    assert shared_core.isdisjoint(consumers)
    assert set(default_targets) == shared_core | consumers

    source = _read(REPORTING_AUDIT)
    assert CLOSEOUT_ID in source
    assert "next implementation front" not in source
