from __future__ import annotations

from pathlib import Path

import scripts.audit_module_governance as governance
from scripts.audit_module_governance import ModuleAuditResult
from scripts.reporting.coordination_result_tables import (
    render_module_governance_summary,
)


def _result(status: str = "OK") -> ModuleAuditResult:
    return ModuleAuditResult(
        module_id="forprint_test",
        module_name="ForPrint Test",
        local_path="/tmp/forprint_test",
        declared_status="active",
        audit_status=status,
        missing_files=[],
        missing_targets=[],
        notes=[],
    )


def test_shared_governance_renderer_is_compact_and_boxed() -> None:
    rendered = render_module_governance_summary(
        modules_checked=14,
        summary={
            "OK": 6,
            "NEEDS_ALIGNMENT": 6,
            "WARN": 2,
            "DEFERRED": 0,
        },
        report_writing=False,
        report_json=None,
        report_markdown=None,
        use_color=False,
    )

    assert "ForPrint Module Governance Audit" in rendered
    assert "Modules checked:" in rendered
    assert "Report writing: disabled" in rendered
    assert "NEEDS_ALIGNMENT:" in rendered
    assert "┌" in rendered
    assert "└" in rendered
    assert "\x1b[" not in rendered


def test_shared_governance_renderer_shows_artifact_paths() -> None:
    rendered = render_module_governance_summary(
        modules_checked=1,
        summary={
            "OK": 1,
            "NEEDS_ALIGNMENT": 0,
            "WARN": 0,
            "DEFERRED": 0,
        },
        report_writing=True,
        report_json="reports/module_governance_audit.json",
        report_markdown="reports/module_governance_audit.md",
        use_color=False,
    )

    assert "JSON report:" in rendered
    assert "reports/module_governance_audit.json" in rendered
    assert "Markdown report:" in rendered
    assert "reports/module_governance_audit.md" in rendered


def test_governance_main_no_write_uses_shared_terminal_renderer(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(governance, "_load_modules", lambda: [{}])
    monkeypatch.setattr(
        governance,
        "_audit_module",
        lambda _module: _result(),
    )
    monkeypatch.setenv("NO_COLOR", "1")

    result = governance.main(["--no-write"])

    captured = capsys.readouterr()
    assert result == 0
    assert captured.err == ""
    assert "ForPrint Module Governance Audit" in captured.out
    assert "Modules checked:" in captured.out
    assert "Report writing: disabled" in captured.out
    assert "┌" in captured.out
    assert "\x1b[" not in captured.out


def test_governance_main_write_mode_preserves_writer_calls(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    calls: list[tuple[str, Path]] = []

    monkeypatch.setattr(governance, "_load_modules", lambda: [{}])
    monkeypatch.setattr(
        governance,
        "_audit_module",
        lambda _module: _result(),
    )
    monkeypatch.setattr(
        governance,
        "_write_json",
        lambda _results, path: calls.append(("json", path)),
    )
    monkeypatch.setattr(
        governance,
        "_write_markdown",
        lambda _results, path: calls.append(("markdown", path)),
    )
    monkeypatch.setenv("NO_COLOR", "1")

    result = governance.main(["--report-dir", str(tmp_path)])

    captured = capsys.readouterr()
    assert result == 0
    assert calls == [
        ("json", tmp_path / "module_governance_audit.json"),
        ("markdown", tmp_path / "module_governance_audit.md"),
    ]
    assert "JSON report:" in captured.out
    assert str(tmp_path / "module_governance_audit.json") in captured.out
    assert "Markdown report:" in captured.out
    assert str(tmp_path / "module_governance_audit.md") in captured.out
