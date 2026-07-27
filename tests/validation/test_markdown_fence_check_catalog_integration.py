from __future__ import annotations

from scripts.run_blueprint_checks import build_checks


def test_markdown_fence_validator_is_in_check_catalog() -> None:
    checks = build_checks()
    matches = [
        check
        for check in checks
        if check.check_id == "markdown_fence_validation"
    ]

    assert len(matches) == 1

    check = matches[0]

    assert check.title == "Markdown fences"
    assert (
        check.expected_result
        == "No new Markdown fence defects beyond baseline"
    )
    assert check.command[1:] == (
        "scripts/validation/validate_markdown_fences.py",
    )
    assert check.group == "documentation"


def test_markdown_fence_check_follows_diagrams_index() -> None:
    check_ids = [
        check.check_id
        for check in build_checks()
    ]

    diagrams_index = check_ids.index(
        "diagrams_index_validation"
    )
    markdown_index = check_ids.index(
        "markdown_fence_validation"
    )
    standards_index = check_ids.index(
        "standards_index_validation"
    )

    assert diagrams_index < markdown_index < standards_index
