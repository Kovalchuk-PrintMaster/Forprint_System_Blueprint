from __future__ import annotations

import re
from collections.abc import Iterable

from scripts.reporting.models import CheckResult, ReportSummary

STATUS_OK = "OK"
STATUS_WARNING = "WARNING"
STATUS_FAILED = "FAILED"

TOKEN_SUCCESS = "success"
TOKEN_WARNING = "warning"
TOKEN_FAILED = "failed"
TOKEN_INFO = "info"
TOKEN_PLANNED = "planned"
TOKEN_ACTIVE = "active"

ANSI_RESET = "\033[0m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"
ANSI_CYAN = "\033[36m"
ANSI_BLUE = "\033[34m"
ANSI_GRAY = "\033[90m"

_ZERO_WARNING_PATTERNS = (
    re.compile(r"^warnings?\s*:\s*0$", re.IGNORECASE),
    re.compile(r"^warning count\s*:\s*0$", re.IGNORECASE),
    re.compile(r"^0\s+warnings?\s*$", re.IGNORECASE),
)


def has_warning_signal(output: str) -> bool:
    """Detect warning evidence without treating explicit zero summaries as warnings."""

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if any(pattern.fullmatch(line) for pattern in _ZERO_WARNING_PATTERNS):
            continue

        normalized = line.lower()
        if "⚠" in line:
            return True
        if "warning" in normalized:
            return True

    return False


def detect_status(return_code: int, combined_output: str) -> str:
    """Normalize command exit and output evidence into one status."""

    if return_code != 0:
        return STATUS_FAILED
    if has_warning_signal(combined_output):
        return STATUS_WARNING
    return STATUS_OK


def status_token(status: str) -> str:
    """Map machine status to the visual semantic-token standard."""

    if status == STATUS_OK:
        return TOKEN_SUCCESS
    if status == STATUS_WARNING:
        return TOKEN_WARNING
    if status == STATUS_FAILED:
        return TOKEN_FAILED
    return TOKEN_INFO


def token_color(token: str) -> str | None:
    """Return an ANSI color for a semantic token."""

    mapping = {
        TOKEN_SUCCESS: ANSI_GREEN,
        TOKEN_WARNING: ANSI_YELLOW,
        TOKEN_FAILED: ANSI_RED,
        TOKEN_INFO: ANSI_CYAN,
        TOKEN_PLANNED: ANSI_GRAY,
        TOKEN_ACTIVE: ANSI_BLUE,
    }
    return mapping.get(token)


def colorize(value: str, token: str, *, use_color: bool) -> str:
    """Color a value without making color part of its meaning."""

    if not use_color:
        return value
    color = token_color(token)
    if not color:
        return value
    return f"{color}{value}{ANSI_RESET}"


def summarize_results(results: Iterable[CheckResult]) -> ReportSummary:
    """Aggregate check results into a deterministic report summary."""

    collected = tuple(results)
    passed = sum(result.status == STATUS_OK for result in collected)
    warnings = sum(result.status == STATUS_WARNING for result in collected)
    failed = sum(result.status == STATUS_FAILED for result in collected)
    duration = sum(result.duration_seconds for result in collected)

    if failed:
        overall = STATUS_FAILED
    elif warnings:
        overall = STATUS_WARNING
    else:
        overall = STATUS_OK

    blockers = tuple(
        result.title for result in collected if result.status == STATUS_FAILED
    )

    return ReportSummary(
        overall_status=overall,
        total=len(collected),
        passed=passed,
        warnings=warnings,
        failed=failed,
        duration_seconds=duration,
        blockers=blockers,
    )
