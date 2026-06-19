from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

try:
    from validate_completion_packet import (
        CompletionPacketError,
        assert_valid_completion_packet,
        load_completion_packet,
    )
except ModuleNotFoundError:
    from scripts.validate_completion_packet import (
        CompletionPacketError,
        assert_valid_completion_packet,
        load_completion_packet,
    )

REPORTS_INDEX_PATH = Path("coordination/reports/index.yaml")
CURRENT_STATUS_YAML_PATH = Path("coordination/status/current_status.yaml")
CURRENT_STATUS_MD_PATH = Path("coordination/status/current_status.md")
NEXT_QUESTIONS_PATH = Path("coordination/status/next_questions_for_blueprint.md")


def yaml_load_mapping(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load YAML mapping from path or return default."""

    if not path.exists():
        return {} if default is None else dict(default)

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {} if default is None else dict(default)
    if not isinstance(data, dict):
        raise CompletionPacketError(f"{path} root must be a YAML mapping")
    return data


def yaml_write_if_changed(path: Path, data: dict[str, Any]) -> bool:
    """Write YAML only if serialized content changed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def text_write_if_changed(path: Path, text: str) -> bool:
    """Write text only if content changed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def _markdown_list(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return "- none\n"
    return "\n".join(f"- {item}" for item in items) + "\n"


def _markdown_mapping(mapping: Any) -> str:
    if not isinstance(mapping, dict) or not mapping:
        return "- none\n"
    return "\n".join(f"- `{key}`: `{value}`" for key, value in mapping.items()) + "\n"


def render_completion_report(packet: dict[str, Any]) -> str:
    """Render deterministic Markdown completion report from packet."""

    return (
        f"# {packet['module_name']} — Completion Report\n\n"
        f"## Metadata\n\n"
        f"- Completion ID: `{packet['completion_id']}`\n"
        f"- Module ID: `{packet['module_id']}`\n"
        f"- Phase: `{packet['phase']}`\n"
        f"- Prompt ID: `{packet['prompt_id']}`\n"
        f"- Report ID: `{packet['report_id']}`\n"
        f"- Created at: `{packet['created_at']}`\n\n"
        f"## Summary\n\n"
        f"{packet['summary'].strip()}\n\n"
        f"## Implemented\n\n"
        f"{_markdown_list(packet.get('implemented'))}\n"
        f"## Checks\n\n"
        f"{_markdown_mapping(packet.get('checks'))}\n"
        f"## Instruction sources reviewed\n\n"
        f"{_markdown_list(packet.get('instruction_sources_reviewed'))}\n"
        f"## Standards reviewed\n\n"
        f"{_markdown_list(packet.get('standards_reviewed'))}\n"
        f"## Standards alignment notes\n\n"
        f"{_markdown_list(packet.get('standards_alignment_notes'))}\n"
        f"## Boundary confirmation\n\n"
        f"{_markdown_mapping(packet.get('boundary_confirmation'))}\n"
        f"## Current outputs\n\n"
        f"{_markdown_list(packet.get('current_outputs'))}\n"
        f"## Next recommended steps\n\n"
        f"{_markdown_list(packet.get('next_recommended_steps'))}\n"
        f"## Next questions for Blueprint\n\n"
        f"{_markdown_list(packet.get('next_questions_for_blueprint'))}"
    )


def build_report_index_entry(packet: dict[str, Any]) -> dict[str, Any]:
    """Build reports/index.yaml entry from packet."""

    return {
        "report_id": packet["report_id"],
        "path": packet["report_path"],
        "status": "completed",
        "phase": packet["phase"],
        "report_file": packet["report_path"],
        "created_at": packet["created_at"],
        "responds_to_prompt_id": packet["prompt_id"],
        "summary": packet["summary"],
        "checks": packet["checks"],
        "instruction_sources_reviewed": packet["instruction_sources_reviewed"],
        "standards_reviewed": packet["standards_reviewed"],
        "standards_alignment_notes": packet["standards_alignment_notes"],
        "boundary_confirmation": packet["boundary_confirmation"],
    }


def update_reports_index(packet: dict[str, Any], module_root: Path) -> bool:
    """Append or replace matching reports/index.yaml entry by report_id."""

    path = module_root / REPORTS_INDEX_PATH
    index = yaml_load_mapping(path, default={"reports": []})
    reports = index.get("reports")
    if not isinstance(reports, list):
        raise CompletionPacketError("coordination/reports/index.yaml `reports` must be a list")

    entry = build_report_index_entry(packet)
    updated = False

    for position, existing in enumerate(reports):
        if isinstance(existing, dict) and existing.get("report_id") == packet["report_id"]:
            if existing != entry:
                reports[position] = entry
            updated = True
            break

    if not updated:
        reports.append(entry)

    index["reports"] = reports
    return yaml_write_if_changed(path, index)


def update_current_status(packet: dict[str, Any], module_root: Path) -> bool:
    """Update coordination/status/current_status.yaml with packet phase."""

    path = module_root / CURRENT_STATUS_YAML_PATH
    status = yaml_load_mapping(path)

    status["module_id"] = packet["module_id"]
    status["module_name"] = packet["module_name"]
    status["current_phase"] = packet["phase"]
    status["last_completed_step"] = f"{packet['phase']}_ready"
    status["current_status"] = f"{packet['phase']}_completed"
    status["last_prompt_id"] = packet["prompt_id"]
    status["last_report_id"] = packet["report_id"]

    validation = status.get("validation")
    if not isinstance(validation, dict):
        validation = {}
    validation.update(packet["checks"])
    status["validation"] = validation

    current_outputs = status.get("current_outputs")
    if not isinstance(current_outputs, list):
        current_outputs = []
    for output in packet.get("current_outputs", []):
        if output not in current_outputs:
            current_outputs.append(output)
    status["current_outputs"] = current_outputs

    return yaml_write_if_changed(path, status)


def render_current_status_md_block(packet: dict[str, Any]) -> str:
    """Render deterministic completion status block for current_status.md."""

    report_id = packet["report_id"]

    return (
        f"<!-- completion-packet:{report_id}:status-start -->\n"
        f"## Completion checkpoint: {packet['phase']}\n\n"
        f"- Current phase: `{packet['phase']}`\n"
        f"- Current status: `{packet['phase']}_completed`\n"
        f"- Last prompt: `{packet['prompt_id']}`\n"
        f"- Last report: `{packet['report_id']}`\n\n"
        f"### Summary\n\n"
        f"{packet['summary'].strip()}\n\n"
        f"### Checks\n\n"
        f"{_markdown_mapping(packet.get('checks'))}\n"
        f"### Boundary confirmation\n\n"
        f"{_markdown_mapping(packet.get('boundary_confirmation'))}"
        f"<!-- completion-packet:{report_id}:status-end -->\n"
    )


def update_marked_block(
    existing: str,
    start_marker: str,
    end_marker: str,
    block: str,
) -> str:
    """Append or replace a marked block without duplicating it."""

    if start_marker in existing and end_marker in existing:
        before = existing.split(start_marker, 1)[0]
        after = existing.split(end_marker, 1)[1]
        return before.rstrip() + "\n\n" + block + after.lstrip("\n")

    separator = "\n\n" if existing.strip() else ""
    return existing.rstrip() + separator + block


def update_current_status_md_if_exists(packet: dict[str, Any], module_root: Path) -> bool:
    """Update current_status.md with a marked block only if the file already exists."""

    path = module_root / CURRENT_STATUS_MD_PATH
    if not path.exists():
        return False

    existing = path.read_text(encoding="utf-8")
    report_id = packet["report_id"]
    start_marker = f"<!-- completion-packet:{report_id}:status-start -->"
    end_marker = f"<!-- completion-packet:{report_id}:status-end -->"
    block = render_current_status_md_block(packet)

    return text_write_if_changed(
        path,
        update_marked_block(existing, start_marker, end_marker, block),
    )

def render_questions_block(packet: dict[str, Any]) -> str:
    questions = packet.get("next_questions_for_blueprint", [])
    report_id = packet["report_id"]

    return (
        f"<!-- completion-packet:{report_id}:start -->\n"
        f"## {packet['phase']}\n\n"
        f"Report: `{report_id}`\n\n"
        f"### Next questions for Blueprint\n\n"
        f"{_markdown_list(questions)}"
        f"<!-- completion-packet:{report_id}:end -->\n"
    )


def update_next_questions(packet: dict[str, Any], module_root: Path) -> bool:
    """Append/update next questions block without duplication."""

    questions = packet.get("next_questions_for_blueprint", [])
    if not isinstance(questions, list) or not questions:
        return False

    path = module_root / NEXT_QUESTIONS_PATH
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    start_marker = f"<!-- completion-packet:{packet['report_id']}:start -->"
    end_marker = f"<!-- completion-packet:{packet['report_id']}:end -->"
    block = render_questions_block(packet)

    if start_marker in existing and end_marker in existing:
        before = existing.split(start_marker, 1)[0]
        after = existing.split(end_marker, 1)[1]
        new_text = before + block + after.lstrip("\n")
    else:
        separator = "\n\n" if existing.strip() else ""
        new_text = existing.rstrip() + separator + block

    return text_write_if_changed(path, new_text)


def apply_completion_packet(packet: dict[str, Any], module_root: Path) -> dict[str, bool]:
    """Apply completion packet to coordination files."""

    assert_valid_completion_packet(packet)

    report_path = module_root / packet["report_path"]
    report_changed = text_write_if_changed(report_path, render_completion_report(packet))
    index_changed = update_reports_index(packet, module_root)
    status_changed = update_current_status(packet, module_root)
    status_md_changed = update_current_status_md_if_exists(packet, module_root)
    questions_changed = update_next_questions(packet, module_root)

    return {
        "report_changed": report_changed,
        "reports_index_changed": index_changed,
        "current_status_changed": status_changed,
        "current_status_md_changed": status_md_changed,
        "next_questions_changed": questions_changed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a completion packet.")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--module-root", type=Path, default=Path("."))
    args = parser.parse_args()

    module_root = args.module_root.resolve()

    try:
        packet = load_completion_packet(args.packet)
        changes = apply_completion_packet(packet, module_root)
    except (CompletionPacketError, FileNotFoundError, yaml.YAMLError) as exc:
        print(f"❌ {exc}")
        return 1

    changed_count = sum(1 for changed in changes.values() if changed)
    print(f"✅ Completion packet applied: {args.packet}")
    print(f"Changed files: {changed_count}")
    for name, changed in changes.items():
        status = "changed" if changed else "unchanged"
        print(f"  - {name}: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
