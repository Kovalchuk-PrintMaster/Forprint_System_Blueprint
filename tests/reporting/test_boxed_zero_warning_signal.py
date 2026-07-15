from __future__ import annotations

from scripts.reporting.statuses import (
    STATUS_OK,
    STATUS_WARNING,
    detect_status,
    has_warning_signal,
)


def test_plain_zero_warning_summary_is_ok() -> None:
    assert has_warning_signal("Warnings: 0\n") is False
    assert has_warning_signal("Warning count: 0\n") is False
    assert detect_status(0, "Warnings: 0\n") == STATUS_OK


def test_boxed_zero_warning_summary_is_ok() -> None:
    output = (
        "ForPrint Coordination Document Manifest\n"
        "│ Warnings:              │ 0                                      │\n"
    )

    assert has_warning_signal(output) is False
    assert detect_status(0, output) == STATUS_OK


def test_ascii_boxed_zero_warning_summary_is_ok() -> None:
    output = "| Warnings: | 0 |\n"

    assert has_warning_signal(output) is False
    assert detect_status(0, output) == STATUS_OK


def test_colored_boxed_zero_warning_summary_is_ok() -> None:
    output = (
        "│ \033[32mWarnings:              \033[0m"
        "│ \033[32m0                                      \033[0m│\n"
    )

    assert has_warning_signal(output) is False
    assert detect_status(0, output) == STATUS_OK


def test_boxed_positive_warning_summary_is_warning() -> None:
    output = "│ Warnings:              │ 1                                      │\n"

    assert has_warning_signal(output) is True
    assert detect_status(0, output) == STATUS_WARNING


def test_explicit_warning_message_remains_warning() -> None:
    output = "WARNING: review required\n"

    assert has_warning_signal(output) is True
    assert detect_status(0, output) == STATUS_WARNING
