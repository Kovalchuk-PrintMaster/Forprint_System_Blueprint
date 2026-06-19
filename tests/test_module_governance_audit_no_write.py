from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPORTS = (
    ROOT / "reports" / "module_governance_audit.json",
    ROOT / "reports" / "module_governance_audit.md",
)


def _snapshot_reports() -> dict[Path, str | None]:
    return {
        path: path.read_text(encoding="utf-8") if path.exists() else None
        for path in REPORTS
    }


def test_module_governance_audit_no_write_does_not_modify_reports() -> None:
    before = _snapshot_reports()

    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit_module_governance.py",
            "--no-write",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    after = _snapshot_reports()

    assert result.returncode == 0
    assert "ForPrint Module Governance Audit" in result.stdout
    assert after == before


def test_blueprint_check_report_uses_no_write_governance_audit() -> None:
    checks = (ROOT / "scripts" / "run_blueprint_checks.py").read_text(
        encoding="utf-8"
    )

    assert "scripts/audit_module_governance.py" in checks
    assert "--no-write" in checks
