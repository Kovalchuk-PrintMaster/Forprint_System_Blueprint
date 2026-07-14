#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.module_roadmap import (
    DONE_STATUSES,
    load_yaml_file,
    resolve_roadmap_path,
    validate_roadmap_document,
)

ACTIVE_EXECUTION_STATUSES = {"ready_for_module_pull", "in_progress"}
PROMPT_FILES = {".md", ".yaml", ".yml"}


class NextWorkError(ValueError):
    """Raised when next-work state cannot be resolved safely."""


@dataclass(frozen=True)
class NextWorkSuggestion:
    result: str
    signal: str
    module: str
    current_step: dict[str, Any] | None
    next_step: dict[str, Any] | None
    active_prompts: tuple[dict[str, Any], ...]
    draft_candidates: tuple[Path, ...]
    conflicting_drafts: tuple[Path, ...]
    action: str
    decision_required: bool


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NextWorkError(f"file does not exist: {path}") from exc
    except yaml.YAMLError as exc:
        raise NextWorkError(f"invalid YAML in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise NextWorkError(f"YAML root must be a mapping: {path}")
    return data


def _sorted_steps(roadmap_data: dict[str, Any]) -> list[dict[str, Any]]:
    raw = roadmap_data.get("roadmap")
    if not isinstance(raw, list):
        return []
    return sorted(
        [item for item in raw if isinstance(item, dict)],
        key=lambda item: item.get("sequence", 0),
    )


def _current_step(
    roadmap_data: dict[str, Any],
    steps: list[dict[str, Any]],
) -> dict[str, Any] | None:
    metadata = roadmap_data.get("metadata")
    current_id = metadata.get("current_step_id") if isinstance(metadata, dict) else None
    if isinstance(current_id, str):
        for step in steps:
            if step.get("step_id") == current_id:
                return step

    for preferred in ("active", "ready"):
        for step in steps:
            if step.get("status") == preferred:
                return step

    for step in steps:
        if step.get("status") not in DONE_STATUSES:
            return step

    return steps[-1] if steps else None


def _next_step(
    steps: list[dict[str, Any]],
    current: dict[str, Any] | None,
) -> dict[str, Any] | None:
    current_index = None
    if current is not None:
        for index, step in enumerate(steps):
            if step.get("step_id") == current.get("step_id"):
                current_index = index
                break

    start = 0 if current_index is None else current_index + 1
    for step in steps[start:]:
        if step.get("status") not in DONE_STATUSES:
            return step
    return None


def _active_prompts(queue_data: dict[str, Any]) -> list[dict[str, Any]]:
    queue = queue_data.get("prompt_queue")
    if not isinstance(queue, list):
        raise NextWorkError("prompt queue `prompt_queue` must be a list")

    active: list[dict[str, Any]] = []
    for item in queue:
        if not isinstance(item, dict):
            continue
        execution = item.get("module_execution")
        status = execution.get("status") if isinstance(execution, dict) else None
        if status in ACTIVE_EXECUTION_STATUSES:
            active.append(item)
    return active


def _draft_files(drafts_dir: Path) -> list[Path]:
    if not drafts_dir.exists():
        return []
    return sorted(
        path
        for path in drafts_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in PROMPT_FILES
        and path.name != ".gitkeep"
    )


def _matches_step(path: Path, step: dict[str, Any]) -> bool:
    step_id = step.get("step_id")
    if not isinstance(step_id, str) or not step_id:
        return False

    normalized_name = path.stem.replace("-", "_")
    if step_id.replace("-", "_") in normalized_name:
        return True

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False

    return step_id in text


def resolve_next_work(
    *,
    root: Path,
    module: str,
) -> NextWorkSuggestion:
    root = root.resolve()
    module_dir = root / "coordination" / "outgoing_prompts" / module
    queue_path = module_dir / "index.yaml"
    roadmap_path = resolve_roadmap_path(root=root, module=module)

    queue_data = _load_yaml_mapping(queue_path)
    roadmap_data = load_yaml_file(roadmap_path)
    validation = validate_roadmap_document(roadmap_data, path=roadmap_path)
    if validation.errors:
        raise NextWorkError(
            "roadmap is invalid:\n- " + "\n- ".join(validation.errors)
        )

    active = _active_prompts(queue_data)
    steps = _sorted_steps(roadmap_data)
    current = _current_step(roadmap_data, steps)
    upcoming = _next_step(steps, current)

    if active:
        return NextWorkSuggestion(
            result="ACTIVE_PROMPT_EXISTS",
            signal="GREEN",
            module=module,
            current_step=current,
            next_step=upcoming,
            active_prompts=tuple(active),
            draft_candidates=(),
            conflicting_drafts=(),
            action="Module should continue or pull the current approved prompt.",
            decision_required=False,
        )

    drafts = _draft_files(module_dir / "drafts")

    if upcoming is None:
        return NextWorkSuggestion(
            result="NEXT_WORK_UNDEFINED",
            signal="YELLOW",
            module=module,
            current_step=current,
            next_step=None,
            active_prompts=(),
            draft_candidates=(),
            conflicting_drafts=tuple(drafts),
            action="Blueprint roadmap decision is required before another prompt is prepared.",
            decision_required=True,
        )

    matches = [path for path in drafts if _matches_step(path, upcoming)]
    conflicts = [path for path in drafts if path not in matches]

    if len(matches) == 1:
        return NextWorkSuggestion(
            result="DRAFT_CANDIDATE_FOUND",
            signal="GREEN",
            module=module,
            current_step=current,
            next_step=upcoming,
            active_prompts=(),
            draft_candidates=tuple(matches),
            conflicting_drafts=tuple(conflicts),
            action="Review the draft candidate and decide whether to promote it to approved.",
            decision_required=True,
        )

    if len(matches) > 1:
        return NextWorkSuggestion(
            result="MULTIPLE_DRAFT_CANDIDATES",
            signal="YELLOW",
            module=module,
            current_step=current,
            next_step=upcoming,
            active_prompts=(),
            draft_candidates=tuple(matches),
            conflicting_drafts=tuple(conflicts),
            action="Choose one documented draft candidate or reconcile them before promotion.",
            decision_required=True,
        )

    if drafts:
        return NextWorkSuggestion(
            result="DRAFT_ROADMAP_CONFLICT",
            signal="YELLOW",
            module=module,
            current_step=current,
            next_step=upcoming,
            active_prompts=(),
            draft_candidates=(),
            conflicting_drafts=tuple(drafts),
            action="Existing drafts do not match the next roadmap step; review the mismatch.",
            decision_required=True,
        )

    return NextWorkSuggestion(
        result="ROADMAP_PROMPT_NEEDED",
        signal="YELLOW",
        module=module,
        current_step=current,
        next_step=upcoming,
        active_prompts=(),
        draft_candidates=(),
        conflicting_drafts=(),
        action="Prepare a draft prompt using only the documented next roadmap step.",
        decision_required=True,
    )


def _step_payload(step: dict[str, Any] | None) -> dict[str, Any] | None:
    if step is None:
        return None
    return {
        "sequence": step.get("sequence"),
        "step_id": step.get("step_id"),
        "title": step.get("title"),
        "status": step.get("status"),
        "priority": step.get("priority"),
        "summary": step.get("summary"),
        "expected_outputs": step.get("expected_outputs", []),
        "depends_on": step.get("depends_on", []),
    }


def as_dict(suggestion: NextWorkSuggestion, *, root: Path) -> dict[str, Any]:
    def rel(path: Path) -> str:
        try:
            return path.relative_to(root.resolve()).as_posix()
        except ValueError:
            return str(path)

    return {
        "result": suggestion.result,
        "signal": suggestion.signal,
        "module": suggestion.module,
        "current_step": _step_payload(suggestion.current_step),
        "next_step": _step_payload(suggestion.next_step),
        "active_prompts": [
            {
                "prompt_id": item.get("prompt_id"),
                "sequence": item.get("sequence"),
                "file": item.get("file"),
                "status": (
                    item.get("module_execution", {}).get("status")
                    if isinstance(item.get("module_execution"), dict)
                    else None
                ),
            }
            for item in suggestion.active_prompts
        ],
        "draft_candidates": [rel(path) for path in suggestion.draft_candidates],
        "conflicting_drafts": [rel(path) for path in suggestion.conflicting_drafts],
        "action": suggestion.action,
        "decision_required": suggestion.decision_required,
    }


def render(suggestion: NextWorkSuggestion, *, root: Path) -> str:
    data = as_dict(suggestion, root=root)
    lines = [
        f"RESULT: {data['result']}",
        f"SIGNAL: {data['signal']}",
        f"MODULE: {data['module']}",
    ]

    current = data["current_step"]
    if current:
        lines.append(
            "CURRENT_STEP: "
            f"{current.get('sequence')} | {current.get('step_id')} | {current.get('status')}"
        )
    else:
        lines.append("CURRENT_STEP: -")

    upcoming = data["next_step"]
    if upcoming:
        lines.append(
            "NEXT_STEP: "
            f"{upcoming.get('sequence')} | {upcoming.get('step_id')} | {upcoming.get('status')}"
        )
        if upcoming.get("title"):
            lines.append(f"NEXT_TITLE: {upcoming['title']}")
    else:
        lines.append("NEXT_STEP: -")

    lines.append(f"ACTIVE_PROMPTS: {len(data['active_prompts'])}")
    for item in data["active_prompts"]:
        lines.append(
            f"  - {item.get('sequence')} | {item.get('prompt_id')} | {item.get('status')}"
        )

    lines.append(f"DRAFT_CANDIDATES: {len(data['draft_candidates'])}")
    for path in data["draft_candidates"]:
        lines.append(f"  - {path}")

    lines.append(f"CONFLICTING_DRAFTS: {len(data['conflicting_drafts'])}")
    for path in data["conflicting_drafts"]:
        lines.append(f"  - {path}")

    lines.extend(
        [
            f"DECISION_REQUIRED: {'yes' if data['decision_required'] else 'no'}",
            f"ACTION: {data['action']}",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve documented next work for a ForPrint module."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--module", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        suggestion = resolve_next_work(root=args.root, module=args.module)
    except NextWorkError as exc:
        print(f"RESULT: FAILED\nSIGNAL: RED\nERROR: {exc}")
        return 1

    if args.json:
        print(
            json.dumps(
                as_dict(suggestion, root=args.root),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(render(suggestion, root=args.root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
