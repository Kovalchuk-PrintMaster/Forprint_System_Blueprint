from __future__ import annotations

import sys

from scripts.run_blueprint_checks import (
    STATUS_FAILED,
    CheckDefinition,
    build_checks,
    run_one_check,
)


def test_catalog_contains_applicability_validator() -> None:
    checks = build_checks()
    check_ids = [item.check_id for item in checks]

    assert len(checks) == 28
    assert len(check_ids) == len(set(check_ids))

    check = {
        item.check_id: item
        for item in checks
    }["blueprint_command_applicability_validation"]

    assert check.title == "Blueprint command applicability"
    assert check.group == "documentation"
    assert check.command[-1] == (
        "scripts/validation/"
        "validate_blueprint_command_applicability.py"
    )

    assert check_ids.index(
        "module_workflow_adoption_matrix_validation"
    ) < check_ids.index(
        "blueprint_command_applicability_validation"
    ) < check_ids.index(
        "module_standards_template_validation"
    )


def test_catalog_check_failure_propagates(
    tmp_path,
) -> None:
    failing_script = tmp_path / "fail.py"
    failing_script.write_text(
        "raise SystemExit(7)\n",
        encoding="utf-8",
    )

    check = CheckDefinition(
        check_id="blueprint_command_applicability_validation",
        title="Blueprint command applicability",
        expected_result="Must fail in this test",
        command=(sys.executable, str(failing_script)),
        group="documentation",
    )

    result = run_one_check(check)

    assert result.status == STATUS_FAILED
    assert result.return_code == 7
