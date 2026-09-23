from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Diagnostic:
    severity: str
    code: str
    message: str
    path: str | None = None
    phase: str | None = None


@dataclass
class CommandResult:
    argv: list[str]
    return_code: int
    stdout: str
    phase: str


@dataclass
class FileResult:
    path: str
    adapter: str
    initial_sha256: str
    final_sha256: str | None = None
    repaired: bool = False
    repair_passes: int = 0
    status: str = "PENDING"
    diagnostics: list[Diagnostic] = field(default_factory=list)
    commands: list[CommandResult] = field(default_factory=list)


@dataclass
class CompileReport:
    schema_version: str
    mutation_id: str
    mode: str
    target_root: str
    candidate_root: str
    result_state: str = "PENDING"
    applied: bool = False
    rolled_back: bool = False
    external_baseline_preserved: bool | None = None
    files: list[FileResult] = field(default_factory=list)
    project_commands: list[CommandResult] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompilerPolicy:
    max_repair_passes: int = 3
    strict_unknown: bool = False
    require_git_root: bool = True
    preserve_external_dirty_baseline: bool = True
    allow_safe_repairs: bool = True
    allow_unsafe_repairs: bool = False
    command_timeout_seconds: int = 300
    protected_target_prefixes: tuple[str, ...] = (
        ".git",
        "tmp/mutation_compiler",
    )


def normalize_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe relative path: {value}")
    if not path.parts:
        raise ValueError("empty path")
    return path
