from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CheckDefinition:
    """Declarative definition of one isolated project check.

    `group` defaults to the legacy core group so existing callers that use the
    original four-argument constructor remain compatible.
    """

    check_id: str
    title: str
    expected_result: str
    command: tuple[str, ...] | list[str]
    group: str = "core_quality"


@dataclass(frozen=True, slots=True, init=False)
class CheckResult:
    """Structured result of one isolated project check.

    The initializer accepts both the current `duration_seconds` name and the
    legacy `duration_sec` name and positional order.
    """

    check_id: str
    title: str
    expected_result: str
    command: tuple[str, ...]
    group: str
    status: str
    return_code: int
    duration_seconds: float
    stdout: str
    stderr: str
    stdout_tail: str
    stderr_tail: str

    def __init__(
        self,
        check_id: str,
        title: str,
        expected_result: str,
        status: str,
        return_code: int,
        duration_sec: float | None = None,
        command: tuple[str, ...] | list[str] = (),
        stdout_tail: str = "",
        stderr_tail: str = "",
        *,
        group: str = "core_quality",
        duration_seconds: float | None = None,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        if duration_seconds is None and duration_sec is None:
            raise TypeError("duration_seconds or duration_sec is required")
        if duration_seconds is not None and duration_sec is not None:
            if float(duration_seconds) != float(duration_sec):
                raise ValueError(
                    "duration_seconds and duration_sec must match when both are provided"
                )

        duration = (
            float(duration_seconds)
            if duration_seconds is not None
            else float(duration_sec)
        )

        object.__setattr__(self, "check_id", check_id)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "expected_result", expected_result)
        object.__setattr__(self, "command", tuple(command))
        object.__setattr__(self, "group", group)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "return_code", int(return_code))
        object.__setattr__(self, "duration_seconds", duration)
        object.__setattr__(self, "stdout", stdout)
        object.__setattr__(self, "stderr", stderr)
        object.__setattr__(self, "stdout_tail", stdout_tail)
        object.__setattr__(self, "stderr_tail", stderr_tail)

    @property
    def duration_sec(self) -> float:
        """Legacy read alias retained for existing callers."""

        return self.duration_seconds


@dataclass(frozen=True, slots=True)
class ReportSummary:
    """Aggregated check-report state."""

    overall_status: str
    total: int
    passed: int
    warnings: int
    failed: int
    duration_seconds: float
    blockers: tuple[str, ...] = field(default_factory=tuple)
