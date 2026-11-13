from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_module_governance_protocol_docs_exist() -> None:
    expected_docs = [
        ROOT / "coordination" / "standards" / "module_governance_protocol.md",
        ROOT / "coordination" / "standards" / "module_assistant_start_protocol.md",
        ROOT / "coordination" / "standards" / "module_pre_commit_protocol.md",
        ROOT / "coordination" / "standards" / "module_governance_make_targets.md",
    ]

    for path in expected_docs:
        assert path.exists(), path


def test_module_governance_protocol_mentions_required_concepts() -> None:
    content = (
        ROOT / "coordination" / "standards" / "module_governance_protocol.md"
    ).read_text(encoding="utf-8")

    required_terms = [
        "Module Assistant Start Protocol",
        "Pre-commit protocol",
        "Post-commit report protocol",
        "Directive sync protocol",
        "make governance-check",
        "make coordination-sync-check",
        "make blueprint-check",
        "make blueprint-sync-directives",
        "make coordination-check",
        "make check-report",
        "current_status.yaml",
        "active directives",
        "validation",
        "boundaries",
    ]

    lower_content = content.casefold()
    for term in required_terms:
        assert term.casefold() in lower_content


def test_module_governance_make_targets_doc_mentions_required_targets() -> None:
    content = (
        ROOT / "coordination" / "standards" / "module_governance_make_targets.md"
    ).read_text(encoding="utf-8")

    required_targets = [
        "check",
        "check-report",
        "status-report",
        "coordination-sync-check",
        "blueprint-check",
        "blueprint-sync-directives",
        "coordination-check",
        "coordination-fix",
        "module-policy-check",
        "governance-check",
    ]

    for target in required_targets:
        assert target in content


def test_module_governance_audit_script_exists() -> None:
    assert (ROOT / "scripts" / "audit_module_governance.py").exists()


def test_module_governance_audit_script_generates_reports(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit_module_governance.py",
            "--report-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    json_report = tmp_path / "module_governance_audit.json"
    markdown_report = tmp_path / "module_governance_audit.md"

    assert result.returncode == 0
    assert json_report.exists()
    assert markdown_report.exists()
    assert "ForPrint Module Governance Audit" in result.stdout


def test_makefile_has_module_governance_audit_target() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "module-governance-audit" in makefile
    assert "scripts/audit_module_governance.py" in makefile


def test_blueprint_check_report_mentions_module_governance_audit() -> None:
    check_runner = (ROOT / "scripts" / "run_blueprint_checks.py").read_text(
        encoding="utf-8"
    )

    assert "Module governance audit" in check_runner
    assert "audit_module_governance.py" in check_runner
