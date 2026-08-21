#!/usr/bin/env python3
"""Prepare and release Blueprint-owned Prompt Queue v0.2 artifacts safely."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

ARTIFACT_SCHEMA = "outgoing_prompt_artifact_v0_1"
QUEUE_SCHEMA = "prompt_queue_v0_2"
POLICY_SCHEMA = "outgoing_prompt_release_policy_v0_1"
OUTGOING_ROOT = Path("coordination/outgoing_prompts")
MODULES_PATH = Path("machine/modules.yaml")
POLICY_PATH = Path(
    "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)

ALLOWED_PRIORITIES = {"critical", "high", "normal", "low", "reference"}
ALLOWED_SOURCE_STATES = {"draft"}
ALLOWED_PREPARED_STATES = {"prepared"}
ALLOWED_RELEASED_STATES = {"released"}
ALLOWED_MODULE_EXECUTION_STATES = {
    "planned",
    "ready_for_module_pull",
    "in_progress",
    "completed_by_module",
    "returned_for_fix",
    "paused",
    "blocked",
    "superseded",
}
PROMPT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_]*$")
PHASE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_]*$")


class WorkflowError(RuntimeError):
    """Raised when a prompt workflow contract is violated."""


class DuplicateKeyError(yaml.YAMLError):
    """Raised for duplicate YAML mapping keys."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as error:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from error
        if duplicate:
            line = key_node.start_mark.line + 1
            column = key_node.start_mark.column + 1
            raise DuplicateKeyError(
                f"duplicate key {key!r} at line {line}, column {column}"
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True)
class PromptArtifact:
    prompt_id: str
    target_module: str
    roadmap_step_id: str | None
    title: str
    phase: str
    priority: str
    created_at: str
    source_change: str
    lifecycle_state: str
    lineage: dict[str, Any]
    body: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class OperationResult:
    operation: str
    state: str
    apply: bool
    module: str
    prompt_id: str
    source: str | None
    destination: str | None
    index: str | None
    sequence: int | None
    message: str


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise WorkflowError(f"required file does not exist: {path}") from error
    try:
        data = yaml.load(text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise WorkflowError(f"invalid YAML in {path}: {error}") from error
    if not isinstance(data, dict):
        raise WorkflowError(f"YAML root must be a mapping: {path}")
    return data


def _safe_dump(data: dict[str, Any]) -> str:
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utc_now(now: datetime | None = None) -> datetime:
    value = now or datetime.now(UTC)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _timestamp(now: datetime | None = None) -> str:
    return _utc_now(now).isoformat().replace("+00:00", "Z")


def _parse_date(value: Any, *, field: str) -> str:
    if not isinstance(value, str):
        raise WorkflowError(f"`{field}` must be an ISO date string")
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise WorkflowError(f"`{field}` must use YYYY-MM-DD") from error
    return value


def _require_string(
    metadata: dict[str, Any],
    key: str,
    *,
    pattern: re.Pattern[str] | None = None,
) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError(f"`{key}` must be a non-empty string")
    value = value.strip()
    if pattern is not None and pattern.fullmatch(value) is None:
        raise WorkflowError(f"`{key}` has unsupported format: {value!r}")
    return value


def _parse_front_matter(text: str, *, path: Path) -> tuple[dict[str, Any], str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise WorkflowError(f"managed prompt lacks YAML front matter: {path}")
    try:
        metadata_text, body = normalized[4:].split("\n---\n", 1)
    except ValueError as error:
        raise WorkflowError(f"managed prompt front matter is not closed: {path}") from error
    try:
        metadata = yaml.load(metadata_text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise WorkflowError(f"invalid prompt front matter in {path}: {error}") from error
    if not isinstance(metadata, dict):
        raise WorkflowError(f"prompt front matter must be a mapping: {path}")
    if not body.strip():
        raise WorkflowError(f"prompt body must not be empty: {path}")
    return metadata, body.rstrip() + "\n"


def _parse_artifact(
    text: str,
    *,
    path: Path,
    allowed_states: set[str],
) -> PromptArtifact:
    metadata, body = _parse_front_matter(text, path=path)
    if metadata.get("schema_version") != ARTIFACT_SCHEMA:
        raise WorkflowError(
            f"unsupported prompt schema in {path}: "
            f"{metadata.get('schema_version')!r}"
        )

    prompt_id = _require_string(
        metadata,
        "prompt_id",
        pattern=PROMPT_ID_PATTERN,
    )
    target_module = _require_string(metadata, "target_module")
    raw_roadmap_step_id = metadata.get("roadmap_step_id")
    roadmap_step_id: str | None
    if raw_roadmap_step_id is None:
        roadmap_step_id = None
    elif (
        isinstance(raw_roadmap_step_id, str)
        and PROMPT_ID_PATTERN.fullmatch(raw_roadmap_step_id) is not None
    ):
        roadmap_step_id = raw_roadmap_step_id
    else:
        raise WorkflowError(
            "`roadmap_step_id` must be a canonical stable id when present"
        )
    title = _require_string(metadata, "title")
    phase = _require_string(metadata, "phase", pattern=PHASE_PATTERN)
    priority = _require_string(metadata, "priority")
    if priority not in ALLOWED_PRIORITIES:
        raise WorkflowError(
            f"`priority` must be one of {sorted(ALLOWED_PRIORITIES)}"
        )
    created_at = _parse_date(metadata.get("created_at"), field="created_at")
    source_change = _require_string(metadata, "source_change")
    lifecycle_state = _require_string(metadata, "lifecycle_state")
    if lifecycle_state not in allowed_states:
        raise WorkflowError(
            f"`lifecycle_state` must be one of {sorted(allowed_states)}; "
            f"found {lifecycle_state!r}"
        )

    lineage = metadata.get("lineage")
    if not isinstance(lineage, dict):
        raise WorkflowError("`lineage` must be a mapping")
    supersedes = lineage.get("supersedes")
    if supersedes is not None and (
        not isinstance(supersedes, str)
        or PROMPT_ID_PATTERN.fullmatch(supersedes) is None
    ):
        raise WorkflowError(
            "`lineage.supersedes` must be null or a canonical prompt_id"
        )

    return PromptArtifact(
        prompt_id=prompt_id,
        target_module=target_module,
        roadmap_step_id=roadmap_step_id,
        title=title,
        phase=phase,
        priority=priority,
        created_at=created_at,
        source_change=source_change,
        lifecycle_state=lifecycle_state,
        lineage=dict(lineage),
        body=body,
        metadata=dict(metadata),
    )


def _render_artifact(metadata: dict[str, Any], body: str) -> str:
    return f"---\n{_safe_dump(metadata)}---\n{body.rstrip()}\n"


def _known_modules(root: Path) -> set[str]:
    data = _load_yaml_mapping(root / MODULES_PATH)
    rows = data.get("modules")
    if not isinstance(rows, list):
        raise WorkflowError(f"`modules` must be a list: {root / MODULES_PATH}")
    result: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise WorkflowError(f"`modules[{index}]` must be a mapping")
        module_id = row.get("id")
        if not isinstance(module_id, str) or not module_id:
            raise WorkflowError(f"`modules[{index}].id` must be a string")
        if module_id in result:
            raise WorkflowError(f"duplicate module id: {module_id}")
        result.add(module_id)
    return result


def _validate_module(root: Path, module: str) -> None:
    if module not in _known_modules(root):
        raise WorkflowError(f"unknown target module: {module}")


def _module_dir(root: Path, module: str) -> Path:
    path = (root / OUTGOING_ROOT / module).resolve()
    outgoing_root = (root / OUTGOING_ROOT).resolve()
    try:
        path.relative_to(outgoing_root)
    except ValueError as error:
        raise WorkflowError("resolved module path escapes outgoing prompt root") from error
    return path


def _artifact_filename(artifact: PromptArtifact) -> str:
    return f"{artifact.created_at}__{artifact.prompt_id}.md"


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _queue_data(index_path: Path, module: str) -> dict[str, Any]:
    data = _load_yaml_mapping(index_path)
    if data.get("schema_version") != QUEUE_SCHEMA:
        raise WorkflowError(
            f"release requires {QUEUE_SCHEMA}: {index_path}"
        )
    if data.get("module") != module:
        raise WorkflowError(
            f"queue module mismatch in {index_path}: "
            f"{data.get('module')!r}"
        )
    rows = data.get("prompt_queue")
    if not isinstance(rows, list):
        raise WorkflowError(f"`prompt_queue` must be a list: {index_path}")
    return data


def _queue_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data["prompt_queue"]
    result: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_sequences: set[int] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise WorkflowError(f"`prompt_queue[{index}]` must be a mapping")
        prompt_id = row.get("prompt_id")
        sequence = row.get("sequence")
        if not isinstance(prompt_id, str) or not prompt_id:
            raise WorkflowError(
                f"`prompt_queue[{index}].prompt_id` must be a string"
            )
        if prompt_id in seen_ids:
            raise WorkflowError(f"duplicate queue prompt_id: {prompt_id}")
        seen_ids.add(prompt_id)
        if not isinstance(sequence, int) or sequence < 1:
            raise WorkflowError(
                f"`prompt_queue[{index}].sequence` must be a positive integer"
            )
        if sequence in seen_sequences:
            raise WorkflowError(f"duplicate queue sequence: {sequence}")
        seen_sequences.add(sequence)
        result.append(row)
    return result


def _release_allowed(root: Path, module: str) -> tuple[bool, str]:
    policy_path = root / POLICY_PATH
    data = _load_yaml_mapping(policy_path)
    if data.get("schema_version") != POLICY_SCHEMA:
        raise WorkflowError(f"unsupported release policy: {policy_path}")
    release = data.get("release")
    if not isinstance(release, dict):
        raise WorkflowError(f"`release` must be a mapping: {policy_path}")

    global_enabled = release.get("global_enabled")
    if not isinstance(global_enabled, bool):
        raise WorkflowError("`release.global_enabled` must be boolean")

    authorized_modules = release.get("authorized_modules")
    if not isinstance(authorized_modules, list) or not all(
        isinstance(item, str) for item in authorized_modules
    ):
        raise WorkflowError(
            "`release.authorized_modules` must be a list of module ids"
        )

    evidence_value = release.get("authorization_evidence")
    authorized = global_enabled or module in authorized_modules
    if not authorized:
        return False, (
            "release is governance-gated; module is not explicitly authorized"
        )

    if not isinstance(evidence_value, str) or not evidence_value.strip():
        raise WorkflowError(
            "authorized release requires `release.authorization_evidence`"
        )
    evidence_path = (root / evidence_value).resolve()
    try:
        evidence_path.relative_to(root.resolve())
    except ValueError as error:
        raise WorkflowError(
            "release authorization evidence must remain inside Blueprint"
        ) from error
    if not evidence_path.is_file():
        raise WorkflowError(
            f"release authorization evidence does not exist: {evidence_path}"
        )
    return True, evidence_value


def prepare_prompt(
    *,
    root: Path,
    source: Path,
    apply: bool,
    replace: bool = False,
    now: datetime | None = None,
) -> OperationResult:
    root = root.resolve()
    source = source.resolve()
    try:
        source_text = source.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise WorkflowError(f"prompt source does not exist: {source}") from error

    artifact = _parse_artifact(
        source_text,
        path=source,
        allowed_states=ALLOWED_SOURCE_STATES,
    )
    _validate_module(root, artifact.target_module)
    if (
        artifact.target_module == "logistics_service"
        and artifact.roadmap_step_id is None
    ):
        raise WorkflowError(
            "Logistics pilot managed prompts require `roadmap_step_id`"
        )

    module_dir = _module_dir(root, artifact.target_module)
    destination = (
        module_dir / "drafts" / _artifact_filename(artifact)
    )
    source_digest = _sha256_text(source_text)

    metadata = dict(artifact.metadata)
    metadata["lifecycle_state"] = "prepared"
    metadata["prepared_at"] = _timestamp(now)
    metadata["prepared_from_sha256"] = source_digest
    prepared_text = _render_artifact(metadata, artifact.body)

    if destination.exists():
        existing_text = destination.read_text(encoding="utf-8")
        existing = _parse_artifact(
            existing_text,
            path=destination,
            allowed_states=ALLOWED_PREPARED_STATES,
        )
        if (
            existing.prompt_id == artifact.prompt_id
            and existing.target_module == artifact.target_module
            and existing.metadata.get("prepared_from_sha256")
            == source_digest
        ):
            return OperationResult(
                operation="prepare",
                state="already_prepared",
                apply=apply,
                module=artifact.target_module,
                prompt_id=artifact.prompt_id,
                source=str(source),
                destination=str(destination.relative_to(root)),
                index=None,
                sequence=None,
                message="identical prepared artifact already exists",
            )
        if not replace:
            raise WorkflowError(
                f"prepared artifact already exists with different content: "
                f"{destination}; use --replace explicitly"
            )

    if apply:
        _atomic_write(destination, prepared_text)

    return OperationResult(
        operation="prepare",
        state="prepared" if apply else "preview",
        apply=apply,
        module=artifact.target_module,
        prompt_id=artifact.prompt_id,
        source=str(source),
        destination=str(destination.relative_to(root)),
        index=None,
        sequence=None,
        message=(
            "prepared draft written"
            if apply
            else "no writes performed; rerun with --apply"
        ),
    )


def _find_prepared_draft(
    *,
    root: Path,
    module: str,
    prompt_id: str,
) -> tuple[Path, PromptArtifact, str] | None:
    drafts_dir = _module_dir(root, module) / "drafts"
    matches: list[tuple[Path, PromptArtifact, str]] = []
    if not drafts_dir.exists():
        return None
    for path in sorted(drafts_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        try:
            artifact = _parse_artifact(
                text,
                path=path,
                allowed_states=ALLOWED_PREPARED_STATES,
            )
        except WorkflowError:
            continue
        if artifact.prompt_id == prompt_id:
            matches.append((path, artifact, text))
    if len(matches) > 1:
        raise WorkflowError(
            f"multiple prepared drafts use prompt_id {prompt_id!r}"
        )
    return matches[0] if matches else None


def _existing_release(
    *,
    root: Path,
    module: str,
    prompt_id: str,
    index_path: Path,
    data: dict[str, Any],
) -> OperationResult | None:
    records = [
        row
        for row in _queue_records(data)
        if row.get("prompt_id") == prompt_id
    ]
    if not records:
        return None
    record = records[0]
    file_value = record.get("file")
    if not isinstance(file_value, str) or not file_value:
        raise WorkflowError(
            f"released queue record has invalid file: {prompt_id}"
        )
    artifact_path = _module_dir(root, module) / file_value
    if not artifact_path.is_file():
        raise WorkflowError(
            f"queue record exists but approved artifact is missing: "
            f"{artifact_path}"
        )
    artifact_text = artifact_path.read_text(encoding="utf-8")
    artifact = _parse_artifact(
        artifact_text,
        path=artifact_path,
        allowed_states=ALLOWED_RELEASED_STATES,
    )
    if artifact.prompt_id != prompt_id or artifact.target_module != module:
        raise WorkflowError(
            f"released artifact identity mismatch: {artifact_path}"
        )
    execution = record.get("module_execution")
    if not isinstance(execution, dict):
        raise WorkflowError(
            f"released queue record lacks module_execution: {prompt_id}"
        )
    status = execution.get("status")
    if status not in ALLOWED_MODULE_EXECUTION_STATES:
        raise WorkflowError(
            f"released queue record has unsupported status: {status!r}"
        )
    return OperationResult(
        operation="release",
        state="already_released",
        apply=True,
        module=module,
        prompt_id=prompt_id,
        source=None,
        destination=str(artifact_path.relative_to(root)),
        index=str(index_path.relative_to(root)),
        sequence=record.get("sequence"),
        message=(
            "release already exists; existing execution state was preserved"
        ),
    )


def release_prompt(
    *,
    root: Path,
    module: str,
    prompt_id: str,
    apply: bool,
    now: datetime | None = None,
) -> OperationResult:
    root = root.resolve()
    if PROMPT_ID_PATTERN.fullmatch(prompt_id) is None:
        raise WorkflowError(f"unsupported prompt_id format: {prompt_id!r}")
    _validate_module(root, module)

    module_dir = _module_dir(root, module)
    index_path = module_dir / "index.yaml"
    data = _queue_data(index_path, module)

    existing = _existing_release(
        root=root,
        module=module,
        prompt_id=prompt_id,
        index_path=index_path,
        data=data,
    )
    prepared_match = _find_prepared_draft(
        root=root,
        module=module,
        prompt_id=prompt_id,
    )
    if existing is not None:
        if prepared_match is not None:
            raise WorkflowError(
                "partial release detected: queue record and prepared draft "
                "both exist; follow the recovery runbook"
            )
        return existing
    if prepared_match is None:
        raise WorkflowError(
            f"prepared draft not found for module={module!r}, "
            f"prompt_id={prompt_id!r}"
        )

    prepared_path, artifact, prepared_text = prepared_match
    if artifact.target_module != module:
        raise WorkflowError(
            "prepared artifact target module does not match release module"
        )
    if module == "logistics_service" and artifact.roadmap_step_id is None:
        raise WorkflowError(
            "Logistics pilot release requires structured `roadmap_step_id`"
        )

    allowed, policy_evidence = _release_allowed(root, module)
    if not allowed:
        raise WorkflowError(policy_evidence)

    records = _queue_records(data)
    sequence = max(
        (int(row["sequence"]) for row in records),
        default=0,
    ) + 1

    approved_path = module_dir / "approved" / prepared_path.name
    if approved_path.exists():
        raise WorkflowError(
            "approved artifact exists without matching queue record; "
            "follow the recovery runbook"
        )

    released_at = _timestamp(now)
    released_metadata = dict(artifact.metadata)
    released_metadata["lifecycle_state"] = "released"
    released_metadata["released_at"] = released_at
    released_metadata["release_policy_evidence"] = policy_evidence
    released_text = _render_artifact(
        released_metadata,
        artifact.body,
    )

    queue_record = {
        "prompt_id": artifact.prompt_id,
        "sequence": sequence,
        "title": artifact.title,
        "file": f"approved/{approved_path.name}",
        "target_module": module,
        "roadmap_step_id": artifact.roadmap_step_id,
        "phase": artifact.phase,
        "priority": artifact.priority,
        "module_execution": {
            "status": "ready_for_module_pull",
            "completion_commit": None,
            "completion_report": None,
            "completed_at": None,
        },
        "blueprint_review": {
            "status": "not_started",
            "acceptance_commit": None,
            "accepted_at": None,
            "review_notes": None,
        },
        "release": {
            "released_at": released_at,
            "source_change": artifact.source_change,
            "prepared_from_sha256": artifact.metadata.get(
                "prepared_from_sha256"
            ),
            "authorization_evidence": policy_evidence,
        },
    }
    updated_data = dict(data)
    updated_data["prompt_queue"] = [*records, queue_record]
    updated_index_text = _safe_dump(updated_data)

    if not apply:
        return OperationResult(
            operation="release",
            state="preview",
            apply=False,
            module=module,
            prompt_id=prompt_id,
            source=str(prepared_path.relative_to(root)),
            destination=str(approved_path.relative_to(root)),
            index=str(index_path.relative_to(root)),
            sequence=sequence,
            message="no writes performed; rerun with --apply",
        )

    original_index_text = index_path.read_text(encoding="utf-8")
    try:
        _atomic_write(approved_path, released_text)
        _atomic_write(index_path, updated_index_text)
        prepared_path.unlink()
        _fsync_directory(prepared_path.parent)
    except Exception as error:
        rollback_errors: list[str] = []
        try:
            approved_path.unlink(missing_ok=True)
            _fsync_directory(approved_path.parent)
        except Exception as rollback_error:
            rollback_errors.append(
                f"approved rollback failed: {rollback_error}"
            )
        try:
            _atomic_write(index_path, original_index_text)
        except Exception as rollback_error:
            rollback_errors.append(
                f"index rollback failed: {rollback_error}"
            )
        try:
            if not prepared_path.exists():
                _atomic_write(prepared_path, prepared_text)
        except Exception as rollback_error:
            rollback_errors.append(
                f"draft rollback failed: {rollback_error}"
            )
        detail = (
            "; ".join(rollback_errors)
            if rollback_errors
            else "rollback completed"
        )
        raise WorkflowError(
            f"release transaction failed: {error}; {detail}"
        ) from error

    return OperationResult(
        operation="release",
        state="released",
        apply=True,
        module=module,
        prompt_id=prompt_id,
        source=str(prepared_path.relative_to(root)),
        destination=str(approved_path.relative_to(root)),
        index=str(index_path.relative_to(root)),
        sequence=sequence,
        message="approved artifact and ready queue record written",
    )


def _print_result(result: OperationResult) -> None:
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare and release Blueprint-owned Prompt Queue v0.2 "
            "artifacts. Commands preview by default."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser(
        "prepare",
        help="Validate and write a non-executable prepared draft.",
    )
    prepare.add_argument("--root", default=".")
    prepare.add_argument("--source", required=True)
    prepare.add_argument("--apply", action="store_true")
    prepare.add_argument("--replace", action="store_true")

    release = subparsers.add_parser(
        "release",
        help="Release one prepared prompt into Prompt Queue v0.2.",
    )
    release.add_argument("--root", default=".")
    release.add_argument("--module", required=True)
    release.add_argument("--prompt-id", required=True)
    release.add_argument("--apply", action="store_true")

    return parser


def main() -> int:
    args = _build_parser().parse_args()
    root = Path(args.root)
    try:
        if args.command == "prepare":
            result = prepare_prompt(
                root=root,
                source=Path(args.source),
                apply=args.apply,
                replace=args.replace,
            )
        else:
            result = release_prompt(
                root=root,
                module=args.module,
                prompt_id=args.prompt_id,
                apply=args.apply,
            )
    except WorkflowError as error:
        print(f"FAILED: {error}")
        return 1

    _print_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
