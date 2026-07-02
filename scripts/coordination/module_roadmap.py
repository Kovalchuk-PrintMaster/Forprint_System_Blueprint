from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = "module_development_roadmap_v0_1"

DEFAULT_STATUS_VALUES = (
    "planned",
    "ready",
    "active",
    "completed",
    "accepted",
    "paused",
    "blocked",
    "deferred",
    "cancelled",
    "superseded",
)

DEFAULT_PRIORITY_VALUES = (
    "critical",
    "high",
    "normal",
    "low",
    "reference",
)

DONE_STATUSES = {"completed", "accepted", "cancelled", "superseded"}
ANSI_RESET = "\033[0m"
ANSI_RE = re.compile(r"\033\[[0-9;]*m")


class RoadmapError(ValueError):
    """Raised when a module roadmap cannot be loaded or rendered."""


@dataclass
class ValidationResult:
    path: Path
    module: str
    step_count: int
    current_step_id: str | None
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RoadmapError(f"Roadmap file does not exist: {path}")

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(loaded, dict):
        raise RoadmapError(f"Roadmap file must contain a YAML mapping: {path}")

    return loaded


def resolve_roadmap_path(
    *,
    root: Path,
    module: str | None = None,
    roadmap: str | None = None,
) -> Path:
    if roadmap:
        candidate = Path(roadmap)
        if not candidate.is_absolute():
            candidate = root / candidate
        return candidate

    if not module:
        raise RoadmapError("Either module or roadmap path must be provided.")

    candidates = (
        root / "coordination" / "roadmaps" / f"{module}.yaml",
        root / "coordination" / "roadmaps" / f"{module}__roadmap.yaml",
        root
        / "coordination"
        / "roadmaps"
        / f"{module}__module_development_roadmap.yaml",
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    formatted = "\n".join(f"  - {candidate}" for candidate in candidates)
    raise RoadmapError(
        "Could not find module roadmap file. Checked:\n" + formatted,
    )


def validate_roadmap_document(
    data: dict[str, Any],
    *,
    path: Path,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    schema_version = data.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        errors.append(
            "schema_version must be "
            f"{SCHEMA_VERSION!r}, got {schema_version!r}",
        )

    module = _string_value(data.get("module"))
    if not module:
        errors.append("module must be a non-empty string")
        module = "<unknown>"

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("metadata must be a mapping")
        metadata = {}

    roadmap = data.get("roadmap")
    if not isinstance(roadmap, list):
        errors.append("roadmap must be a list")
        roadmap = []

    status_values = _string_set(data.get("status_values"), DEFAULT_STATUS_VALUES)
    priority_values = _string_set(
        data.get("priority_values"),
        DEFAULT_PRIORITY_VALUES,
    )

    seen_step_ids: set[str] = set()
    seen_sequences: set[int] = set()

    for index, raw_step in enumerate(roadmap, start=1):
        if not isinstance(raw_step, dict):
            errors.append(f"roadmap[{index}] must be a mapping")
            continue

        step_id = _string_value(raw_step.get("step_id"))
        if not step_id:
            errors.append(f"roadmap[{index}].step_id must be a non-empty string")
        elif step_id in seen_step_ids:
            errors.append(f"duplicate step_id: {step_id}")
        else:
            seen_step_ids.add(step_id)

        sequence = raw_step.get("sequence")
        if not isinstance(sequence, int):
            errors.append(f"roadmap[{index}].sequence must be an integer")
        elif sequence in seen_sequences:
            errors.append(f"duplicate sequence: {sequence}")
        else:
            seen_sequences.add(sequence)

        title = _string_value(raw_step.get("title"))
        if not title:
            errors.append(f"roadmap[{index}].title must be a non-empty string")

        status = _string_value(raw_step.get("status"))
        if not status:
            errors.append(f"roadmap[{index}].status must be a non-empty string")
        elif status not in status_values:
            errors.append(
                f"roadmap[{index}].status {status!r} is not in status_values",
            )

        priority = _string_value(raw_step.get("priority"))
        if not priority:
            errors.append(f"roadmap[{index}].priority must be a non-empty string")
        elif priority not in priority_values:
            errors.append(
                f"roadmap[{index}].priority {priority!r} "
                "is not in priority_values",
            )

        owner_module = _string_value(raw_step.get("owner_module"))
        if owner_module and owner_module != module:
            warnings.append(
                f"roadmap[{index}].owner_module {owner_module!r} "
                f"does not match module {module!r}",
            )

        depends_on = raw_step.get("depends_on", [])
        if depends_on is not None and not isinstance(depends_on, list):
            errors.append(f"roadmap[{index}].depends_on must be a list")

        expected_outputs = raw_step.get("expected_outputs", [])
        if expected_outputs is not None and not isinstance(expected_outputs, list):
            errors.append(f"roadmap[{index}].expected_outputs must be a list")

        evidence = raw_step.get("evidence", {})
        if evidence is not None and not isinstance(evidence, dict):
            errors.append(f"roadmap[{index}].evidence must be a mapping")

    current_step_id = _string_value(metadata.get("current_step_id"))
    if current_step_id and current_step_id not in seen_step_ids:
        errors.append(
            f"metadata.current_step_id {current_step_id!r} "
            "does not match any roadmap step_id",
        )

    if not roadmap:
        warnings.append("roadmap is empty")

    return ValidationResult(
        path=path,
        module=module,
        step_count=len(roadmap),
        current_step_id=current_step_id or None,
        errors=errors,
        warnings=warnings,
    )


def render_roadmap_dashboard(
    data: dict[str, Any],
    *,
    path: Path,
    before_current: int = 5,
    after_current: int = 10,
    no_color: bool = False,
) -> str:
    validation = validate_roadmap_document(data, path=path)
    if not validation.ok:
        details = "\n".join(f"  - {error}" for error in validation.errors)
        raise RoadmapError(f"Invalid roadmap {path}:\n{details}")

    steps = _sorted_steps(data.get("roadmap", []))
    current_step_id = _derive_current_step_id(data, steps)

    current_index = _step_index(steps, current_step_id)
    if current_index is None:
        current_index = 0

    start = max(0, current_index - before_current)
    end = min(len(steps), current_index + after_current + 1)
    visible_steps = steps[start:end]

    lines = [
        "ForPrint Module Roadmap Dashboard",
        f"Module: {validation.module}",
        f"Roadmap: {path}",
        f"Current step: {current_step_id or '-'}",
        f"Window: {before_current} before / {after_current} after",
        "",
    ]

    table_rows: list[tuple[str, ...]] = []

    for step in visible_steps:
        marker = ">"
        if _string_value(step.get("step_id")) != current_step_id:
            marker = ""

        status = _string_value(step.get("status")) or "unknown"
        priority = _string_value(step.get("priority")) or "unknown"

        table_rows.append(
            (
                marker,
                str(step.get("sequence", "-")),
                _token(status, no_color=no_color),
                _token(priority, no_color=no_color),
                _string_value(step.get("step_id")) or "-",
                _string_value(step.get("title")) or "-",
                _dependency_summary(step),
                _evidence_summary(step),
            ),
        )

    lines.extend(
        _boxed_table(
            headers=(
                "",
                "Seq",
                "Status",
                "Priority",
                "Step ID",
                "Title",
                "Deps",
                "Evidence",
            ),
            widths=(2, 4, 14, 10, 44, 48, 18, 16),
            rows=table_rows,
        ),
    )

    if validation.warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"  - {warning}" for warning in validation.warnings)

    return _finalize_output(lines, no_color=no_color)

def render_modules_summary(
    roadmaps: list[tuple[Path, dict[str, Any]]],
    *,
    no_color: bool = False,
) -> str:
    lines = [
        "ForPrint Module Roadmap Summary",
        "",
        _row(
            "Module",
            "Current",
            "Status",
            "Priority",
            "Next ready",
            "Blocked",
        ),
        _row(
            "------",
            "-------",
            "------",
            "--------",
            "----------",
            "-------",
        ),
    ]

    for path, data in roadmaps:
        validation = validate_roadmap_document(data, path=path)
        if not validation.ok:
            lines.append(
                _row(
                    validation.module,
                    "invalid",
                    _token("failed", no_color=no_color),
                    "-",
                    "-",
                    str(len(validation.errors)),
                ),
            )
            continue

        steps = _sorted_steps(data.get("roadmap", []))
        current_step_id = _derive_current_step_id(data, steps)
        current_step = _find_step(steps, current_step_id)
        next_ready = _find_next_ready_step(steps, current_step_id)
        blocked_count = sum(
            1 for step in steps if _string_value(step.get("status")) == "blocked"
        )

        lines.append(
            _row(
                validation.module,
                current_step_id or "-",
                _token(
                    _string_value(current_step.get("status")) if current_step else "-",
                    no_color=no_color,
                ),
                _token(
                    _string_value(current_step.get("priority"))
                    if current_step
                    else "-",
                    no_color=no_color,
                ),
                _string_value(next_ready.get("step_id")) if next_ready else "-",
                str(blocked_count),
            ),
        )

    return _finalize_output(lines, no_color=no_color)


def _sorted_steps(raw_steps: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_steps, list):
        return []

    steps = [step for step in raw_steps if isinstance(step, dict)]
    return sorted(steps, key=lambda step: step.get("sequence", 0))


def _derive_current_step_id(
    data: dict[str, Any],
    steps: list[dict[str, Any]],
) -> str | None:
    metadata = data.get("metadata")
    if isinstance(metadata, dict):
        current_step_id = _string_value(metadata.get("current_step_id"))
        if current_step_id:
            return current_step_id

    for preferred_status in ("active", "ready"):
        for step in steps:
            if _string_value(step.get("status")) == preferred_status:
                return _string_value(step.get("step_id"))

    for step in steps:
        status = _string_value(step.get("status"))
        if status not in DONE_STATUSES:
            return _string_value(step.get("step_id"))

    if steps:
        return _string_value(steps[-1].get("step_id"))

    return None


def _step_index(
    steps: list[dict[str, Any]],
    current_step_id: str | None,
) -> int | None:
    if not current_step_id:
        return None

    for index, step in enumerate(steps):
        if _string_value(step.get("step_id")) == current_step_id:
            return index

    return None


def _find_step(
    steps: list[dict[str, Any]],
    step_id: str | None,
) -> dict[str, Any] | None:
    if not step_id:
        return None

    for step in steps:
        if _string_value(step.get("step_id")) == step_id:
            return step

    return None


def _find_next_ready_step(
    steps: list[dict[str, Any]],
    current_step_id: str | None,
) -> dict[str, Any] | None:
    current_index = _step_index(steps, current_step_id)

    for index, step in enumerate(steps):
        if current_index is not None and index <= current_index:
            continue
        if _string_value(step.get("status")) == "ready":
            return step

    for index, step in enumerate(steps):
        if current_index is not None and index <= current_index:
            continue
        if _string_value(step.get("status")) == "planned":
            return step

    return None


def _dependency_summary(step: dict[str, Any]) -> str:
    depends_on = step.get("depends_on")
    if not isinstance(depends_on, list) or not depends_on:
        return "-"

    statuses: dict[str, int] = {}
    for dependency in depends_on:
        if not isinstance(dependency, dict):
            continue
        status = _string_value(dependency.get("status")) or "unknown"
        statuses[status] = statuses.get(status, 0) + 1

    if not statuses:
        return str(len(depends_on))

    return ", ".join(f"{status}:{count}" for status, count in sorted(statuses.items()))


def _evidence_summary(step: dict[str, Any]) -> str:
    evidence = step.get("evidence")
    if not isinstance(evidence, dict):
        return "-"

    markers: list[str] = []
    if evidence.get("module_commit"):
        markers.append("commit")
    if evidence.get("blueprint_acceptance_commit"):
        markers.append("accepted")
    if evidence.get("completion_report"):
        markers.append("report")
    if evidence.get("check_report"):
        markers.append("check")

    return ",".join(markers) if markers else "-"


def _finalize_output(lines: list[str], *, no_color: bool) -> str:
    rendered = "\n".join(lines)
    if no_color:
        return rendered
    return rendered + ANSI_RESET


def _row(*values: str) -> str:
    widths = (24, 14, 10, 44, 48, 18, 16)
    padded = []
    for value, width in zip(values, widths, strict=False):
        raw_value = value.replace("\n", " ")
        color = _leading_ansi_color(raw_value)
        clean_value = _strip_ansi(raw_value)
        cell = _format_visible_cell(clean_value, width)
        if color:
            cell = f"{color}{cell}{ANSI_RESET}"
        padded.append(cell)
    return " | ".join(padded)

def _boxed_table(
    *,
    headers: tuple[str, ...],
    widths: tuple[int, ...],
    rows: list[tuple[str, ...]],
) -> list[str]:
    return [
        _boxed_border(widths, left="┌", separator="┬", right="┐"),
        _boxed_row(headers, widths),
        _boxed_border(widths, left="├", separator="┼", right="┤"),
        *[_boxed_row(row, widths) for row in rows],
        _boxed_border(widths, left="└", separator="┴", right="┘"),
    ]


def _boxed_border(
    widths: tuple[int, ...],
    *,
    left: str,
    separator: str,
    right: str,
) -> str:
    return left + separator.join("─" * (width + 2) for width in widths) + right


def _boxed_row(values: tuple[str, ...], widths: tuple[int, ...]) -> str:
    cells = []
    for value, width in zip(values, widths, strict=False):
        cells.append(_visible_cell(value, width))
    return "│ " + " │ ".join(cells) + " │"


def _visible_cell(value: str, width: int) -> str:
    raw_value = value.replace("\n", " ")
    color = _leading_ansi_color(raw_value)
    clean_value = _strip_ansi(raw_value)
    cell = _format_visible_cell(clean_value, width)
    if color:
        return f"{color}{cell}{ANSI_RESET}"
    return cell


def _format_visible_cell(value: str, width: int) -> str:
    if len(value) > width:
        value = value[: width - 1] + "…"
    return value.ljust(width)


def _strip_ansi(value: str) -> str:
    return ANSI_RE.sub("", value)


def _leading_ansi_color(value: str) -> str | None:
    match = ANSI_RE.match(value)
    if not match:
        return None

    color = match.group(0)
    if color == ANSI_RESET:
        return None
    return color

def _token(value: str, *, no_color: bool) -> str:
    if no_color:
        return value

    color = _token_color(value)
    if not color:
        return value

    return f"{color}{value}{ANSI_RESET}"


def _token_color(value: str) -> str | None:
    if value in {"success", "ok", "completed", "accepted", "applied"}:
        return "\033[32m"
    if value in {"critical", "blocked", "failed"}:
        return "\033[31m"
    if value in {"high", "warning", "new", "changed", "ready"}:
        return "\033[33m"
    if value in {"active", "in_progress"}:
        return "\033[34m"
    if value in {"deferred", "paused", "reference"}:
        return "\033[36m"
    return None


def _string_set(value: Any, default: tuple[str, ...]) -> set[str]:
    if not isinstance(value, list):
        return set(default)

    values = {_string_value(item) for item in value}
    values.discard("")
    return values or set(default)


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()
