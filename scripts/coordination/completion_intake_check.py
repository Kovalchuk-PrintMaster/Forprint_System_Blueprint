#!/usr/bin/env python3
"""Read-only Blueprint validation of a module completion intake packet."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

OK_CHECK_VALUES = {"ok", "passed", "pass", "green", True}
REQUIRED_PACKET_STRINGS = (
    "completion_id",
    "module_id",
    "module_name",
    "phase",
    "prompt_id",
    "report_id",
    "report_path",
    "created_at",
    "summary",
    "implementation_commit",
)
REQUIRED_PACKET_LISTS = (
    "implemented",
    "instruction_sources_reviewed",
    "standards_reviewed",
    "standards_alignment_notes",
    "current_outputs",
    "next_recommended_steps",
)
REQUIRED_CHECKS = ("check_report", "tests", "governance_check")
REQUIRED_BOUNDARY_FLAGS = (
    "no_production_api",
    "no_live_external_integrations",
    "no_real_1c_sync",
    "no_production_write",
    "no_automatic_posting",
)
HEX_COMMIT = re.compile(r"^[0-9a-f]{40}$")


class CompletionIntakeCheckError(ValueError):
    """Raised when completion evidence is unsafe or incomplete."""


class DuplicateKeyError(yaml.YAMLError):
    """Raised when a YAML mapping contains a duplicate key."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


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
                f"duplicate key `{key}` at line {line}, column {column}"
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True)
class CompletionIntakeCheckResult:
    module_id: str
    prompt_id: str
    phase: str
    packet_path: str
    report_path: str
    implementation_commit: str
    completion_commit: str
    branch: str
    remote: str
    remote_commit: str
    warnings: tuple[str, ...]


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise CompletionIntakeCheckError(
            f"file does not exist: {path}"
        ) from error
    try:
        loaded = yaml.load(text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise CompletionIntakeCheckError(
            f"invalid YAML in {path}: {error}"
        ) from error
    if not isinstance(loaded, dict):
        raise CompletionIntakeCheckError(
            f"YAML root must be a mapping: {path}"
        )
    return loaded


def _required_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CompletionIntakeCheckError(
            f"completion packet field `{field}` must be a non-empty string"
        )
    return value.strip()


def _required_non_empty_list(
    data: dict[str, Any],
    field: str,
) -> list[Any]:
    value = data.get(field)
    if not isinstance(value, list) or not value:
        raise CompletionIntakeCheckError(
            f"completion packet field `{field}` must be a non-empty list"
        )
    return value


def _safe_under(root: Path, candidate: Path, *, label: str) -> Path:
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve()
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError as error:
        raise CompletionIntakeCheckError(
            f"{label} escapes repository root: {candidate}"
        ) from error
    return candidate_resolved


def _module_relative_path(
    module_root: Path,
    path: Path,
    *,
    label: str,
) -> str:
    safe = _safe_under(module_root, path, label=label)
    return safe.relative_to(module_root.resolve()).as_posix()


def _run_git_bytes(
    repo: Path,
    *args: str,
    allowed_returncodes: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        env=environment,
    )
    if completed.returncode not in allowed_returncodes:
        detail = (
            completed.stderr.decode("utf-8", errors="replace").strip()
            or completed.stdout.decode("utf-8", errors="replace").strip()
        )
        raise CompletionIntakeCheckError(
            f"git {' '.join(args)} failed in {repo}: {detail}"
        )
    return completed


def _run_git(repo: Path, *args: str) -> str:
    return _run_git_bytes(repo, *args).stdout.decode(
        "utf-8",
        errors="replace",
    ).strip()


def _verify_commit(repo: Path, commit: str, *, label: str) -> str:
    if HEX_COMMIT.fullmatch(commit) is None:
        raise CompletionIntakeCheckError(
            f"{label} must be a 40-character lowercase Git hash"
        )
    resolved = _run_git(
        repo,
        "rev-parse",
        "--verify",
        f"{commit}^{{commit}}",
    )
    if HEX_COMMIT.fullmatch(resolved) is None:
        raise CompletionIntakeCheckError(
            f"could not resolve {label}: {commit}"
        )
    return resolved


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    result = _run_git_bytes(
        repo,
        "merge-base",
        "--is-ancestor",
        ancestor,
        descendant,
        allowed_returncodes=(0, 1),
    )
    return result.returncode == 0


def _commit_has_object(repo: Path, commit: str) -> bool:
    result = _run_git_bytes(
        repo,
        "cat-file",
        "-e",
        f"{commit}^{{commit}}",
        allowed_returncodes=(0, 1),
    )
    return result.returncode == 0


def _verify_tracked_content(
    *,
    module_root: Path,
    commit: str,
    relative_path: str,
    absolute_path: Path,
    label: str,
) -> None:
    committed = _run_git_bytes(
        module_root,
        "show",
        f"{commit}:{relative_path}",
    ).stdout
    if absolute_path.read_bytes() != committed:
        raise CompletionIntakeCheckError(
            f"{label} content differs from `{commit}:{relative_path}`"
        )


def _validate_iso_date(value: str, *, field: str) -> None:
    if len(value) < 10:
        raise CompletionIntakeCheckError(
            f"`{field}` is not an ISO date/timestamp: {value!r}"
        )
    try:
        date.fromisoformat(value[:10])
    except ValueError as error:
        raise CompletionIntakeCheckError(
            f"`{field}` is not an ISO date/timestamp: {value!r}"
        ) from error


def _normalize_check(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in OK_CHECK_VALUES
    return value in OK_CHECK_VALUES


def _validate_checks(packet: dict[str, Any]) -> list[str]:
    checks = packet.get("checks")
    if not isinstance(checks, dict):
        raise CompletionIntakeCheckError(
            "completion packet `checks` must be a mapping"
        )
    for name in REQUIRED_CHECKS:
        if name not in checks:
            raise CompletionIntakeCheckError(
                f"completion packet `checks.{name}` is required"
            )
        if not _normalize_check(checks[name]):
            raise CompletionIntakeCheckError(
                f"completion packet `checks.{name}` "
                f"is not successful: {checks[name]!r}"
            )
    failed = checks.get("check_report_failed")
    if failed is not None and (
        not isinstance(failed, int) or isinstance(failed, bool)
    ):
        raise CompletionIntakeCheckError(
            "`checks.check_report_failed` must be an integer"
        )
    if isinstance(failed, int) and failed > 0:
        raise CompletionIntakeCheckError(
            f"module check report contains {failed} failed check(s)"
        )
    warning_count = checks.get("check_report_warnings")
    if warning_count is not None and (
        not isinstance(warning_count, int)
        or isinstance(warning_count, bool)
    ):
        raise CompletionIntakeCheckError(
            "`checks.check_report_warnings` must be an integer"
        )
    warnings: list[str] = []
    if isinstance(warning_count, int) and warning_count > 0:
        warnings.append(
            f"module check report contains {warning_count} warning(s)"
        )
    return warnings


def _validate_boundary(packet: dict[str, Any]) -> None:
    boundary = packet.get("boundary_confirmation")
    if not isinstance(boundary, dict) or not boundary:
        raise CompletionIntakeCheckError(
            "completion packet `boundary_confirmation` "
            "must be a non-empty mapping"
        )
    unsafe: list[str] = []
    for required in REQUIRED_BOUNDARY_FLAGS:
        if boundary.get(required) is not True:
            unsafe.append(f"{required} must be true")
    for key, value in boundary.items():
        if key.startswith("no_") and value is not True:
            unsafe.append(f"{key} must be true")
        elif key.endswith(
            ("_added", "_committed", "_written_directly")
        ) and value is not False:
            unsafe.append(f"{key} must be false")
    if unsafe:
        raise CompletionIntakeCheckError(
            "unsafe boundary confirmation:\n- "
            + "\n- ".join(sorted(set(unsafe)))
        )


def _single_record(
    records: Any,
    *,
    key: str,
    value: str,
    label: str,
) -> dict[str, Any]:
    if not isinstance(records, list):
        raise CompletionIntakeCheckError(f"{label} must be a list")
    matches = [
        record
        for record in records
        if isinstance(record, dict) and record.get(key) == value
    ]
    if len(matches) != 1:
        raise CompletionIntakeCheckError(
            f"expected exactly one {label} record for "
            f"`{value}`, found {len(matches)}"
        )
    return matches[0]


def _validate_blueprint_context(
    *,
    blueprint_root: Path,
    module_id: str,
    prompt_id: str,
    phase: str,
) -> None:
    queue_path = (
        blueprint_root
        / "coordination/outgoing_prompts"
        / module_id
        / "index.yaml"
    )
    roadmap_path = (
        blueprint_root
        / "coordination/roadmaps"
        / f"{module_id}.yaml"
    )
    queue = _load_yaml_mapping(queue_path)
    roadmap = _load_yaml_mapping(roadmap_path)
    if queue.get("module") not in {None, module_id}:
        raise CompletionIntakeCheckError(
            f"prompt queue module does not match `{module_id}`"
        )
    prompt = _single_record(
        queue.get("prompt_queue"),
        key="prompt_id",
        value=prompt_id,
        label="prompt queue",
    )
    if prompt.get("target_module") not in {None, module_id}:
        raise CompletionIntakeCheckError(
            "prompt target_module does not match packet module_id"
        )
    if prompt.get("phase") not in {None, phase}:
        raise CompletionIntakeCheckError(
            "prompt phase does not match completion packet phase"
        )
    step = _single_record(
        roadmap.get("roadmap"),
        key="step_id",
        value=prompt_id,
        label="roadmap",
    )
    if step.get("owner_module") not in {None, module_id}:
        raise CompletionIntakeCheckError(
            "roadmap owner_module does not match packet module_id"
        )
    if step.get("status") not in {"active", "completed", "accepted"}:
        raise CompletionIntakeCheckError(
            "roadmap step must be active, completed, or accepted "
            f"before intake; found {step.get('status')!r}"
        )


def _validate_branch(branch: str) -> str:
    branch = branch.strip()
    if branch.startswith("refs/heads/"):
        branch = branch.removeprefix("refs/heads/")
    forbidden = {" ", "..", "~", "^", ":", "?", "*", "[", "\\"}
    if (
        not branch
        or any(token in branch for token in forbidden)
        or branch.startswith("-")
        or branch.endswith(("/", "."))
    ):
        raise CompletionIntakeCheckError(
            f"unsafe publication branch: {branch!r}"
        )
    return branch


def _remote_branch_commit(
    *,
    module_root: Path,
    remote: str,
    branch: str,
) -> str:
    output = _run_git(
        module_root,
        "ls-remote",
        "--heads",
        remote,
        f"refs/heads/{branch}",
    )
    lines = [line for line in output.splitlines() if line.strip()]
    if len(lines) != 1:
        raise CompletionIntakeCheckError(
            f"expected one remote branch `refs/heads/{branch}` "
            f"on `{remote}`, found {len(lines)}"
        )
    fields = lines[0].split()
    if len(fields) != 2:
        raise CompletionIntakeCheckError(
            "unexpected git ls-remote output"
        )
    commit, reference = fields
    if (
        HEX_COMMIT.fullmatch(commit) is None
        or reference != f"refs/heads/{branch}"
    ):
        raise CompletionIntakeCheckError(
            "unexpected git ls-remote branch record"
        )
    return commit


def _verify_remote_containment(
    *,
    module_root: Path,
    completion_commit: str,
    remote_commit: str,
) -> None:
    if remote_commit == completion_commit:
        return
    if not _commit_has_object(module_root, remote_commit):
        raise CompletionIntakeCheckError(
            "remote branch tip differs from completion commit, "
            "and the remote tip object is not available locally; "
            "containment cannot be verified without mutating Git state"
        )
    if not _is_ancestor(
        module_root,
        completion_commit,
        remote_commit,
    ):
        raise CompletionIntakeCheckError(
            "completion commit is not contained in the selected "
            "remote branch"
        )


def check_completion_intake(
    *,
    blueprint_root: Path,
    module_id: str,
    module_root: Path,
    packet: Path,
    completion_commit: str,
    remote: str = "origin",
    branch: str | None = None,
) -> CompletionIntakeCheckResult:
    """Validate completion evidence without repository writes."""

    blueprint_root = blueprint_root.resolve()
    module_root = module_root.resolve()
    if not module_root.is_dir():
        raise CompletionIntakeCheckError(
            f"module root does not exist: {module_root}"
        )

    packet_path = packet if packet.is_absolute() else module_root / packet
    packet_path = _safe_under(
        module_root,
        packet_path,
        label="completion packet",
    )
    packet_relative = _module_relative_path(
        module_root,
        packet_path,
        label="completion packet",
    )
    if not packet_relative.startswith(
        "coordination/completion_packets/"
    ):
        raise CompletionIntakeCheckError(
            "completion packet must be under "
            "`coordination/completion_packets/`"
        )

    data = _load_yaml_mapping(packet_path)
    for field in REQUIRED_PACKET_STRINGS:
        _required_string(data, field)
    for field in REQUIRED_PACKET_LISTS:
        _required_non_empty_list(data, field)

    packet_module = _required_string(data, "module_id")
    if packet_module != module_id:
        raise CompletionIntakeCheckError(
            f"packet module_id `{packet_module}` does not match "
            f"requested module `{module_id}`"
        )

    prompt_id = _required_string(data, "prompt_id")
    phase = _required_string(data, "phase")
    created_at = _required_string(data, "created_at")
    _validate_iso_date(created_at, field="created_at")

    report_relative = _required_string(data, "report_path")
    if not report_relative.startswith(
        "coordination/reports/completion/"
    ):
        raise CompletionIntakeCheckError(
            "completion report must be under "
            "`coordination/reports/completion/`"
        )
    report_path = _safe_under(
        module_root,
        module_root / report_relative,
        label="completion report",
    )
    if not report_path.is_file():
        raise CompletionIntakeCheckError(
            f"completion report does not exist: {report_path}"
        )

    implementation_commit = _verify_commit(
        module_root,
        _required_string(data, "implementation_commit"),
        label="implementation_commit",
    )
    resolved_completion_commit = _verify_commit(
        module_root,
        completion_commit,
        label="completion_commit",
    )
    if not _is_ancestor(
        module_root,
        implementation_commit,
        resolved_completion_commit,
    ):
        raise CompletionIntakeCheckError(
            "implementation_commit is not an ancestor of "
            "completion_commit"
        )

    warnings = _validate_checks(data)
    _validate_boundary(data)
    _validate_blueprint_context(
        blueprint_root=blueprint_root,
        module_id=module_id,
        prompt_id=prompt_id,
        phase=phase,
    )

    _verify_tracked_content(
        module_root=module_root,
        commit=resolved_completion_commit,
        relative_path=packet_relative,
        absolute_path=packet_path,
        label="completion packet",
    )
    _verify_tracked_content(
        module_root=module_root,
        commit=resolved_completion_commit,
        relative_path=report_relative,
        absolute_path=report_path,
        label="completion report",
    )

    packet_branch = data.get("branch")
    if packet_branch is not None and (
        not isinstance(packet_branch, str)
        or not packet_branch.strip()
    ):
        raise CompletionIntakeCheckError(
            "completion packet `branch` must be a "
            "non-empty string when present"
        )
    selected_branch = _validate_branch(
        branch
        or (
            packet_branch.strip()
            if isinstance(packet_branch, str)
            else ""
        )
    )

    if data.get("push_status") not in {"pushed", "synced", "remote"}:
        raise CompletionIntakeCheckError(
            "completion packet `push_status` must indicate "
            "post-publication state"
        )

    selected_remote = remote.strip()
    if not selected_remote:
        raise CompletionIntakeCheckError(
            "remote must be a non-empty string"
        )

    remote_commit = _remote_branch_commit(
        module_root=module_root,
        remote=selected_remote,
        branch=selected_branch,
    )
    _verify_remote_containment(
        module_root=module_root,
        completion_commit=resolved_completion_commit,
        remote_commit=remote_commit,
    )

    return CompletionIntakeCheckResult(
        module_id=module_id,
        prompt_id=prompt_id,
        phase=phase,
        packet_path=packet_relative,
        report_path=report_relative,
        implementation_commit=implementation_commit,
        completion_commit=resolved_completion_commit,
        branch=selected_branch,
        remote=selected_remote,
        remote_commit=remote_commit,
        warnings=tuple(warnings),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only Blueprint verification of module "
            "completion evidence."
        )
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--module", required=True)
    parser.add_argument("--module-root", required=True)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--completion-commit", required=True)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch")
    args = parser.parse_args()

    try:
        result = check_completion_intake(
            blueprint_root=Path(args.root),
            module_id=args.module,
            module_root=Path(args.module_root),
            packet=Path(args.packet),
            completion_commit=args.completion_commit,
            remote=args.remote,
            branch=args.branch,
        )
    except CompletionIntakeCheckError as error:
        print("FAILED: completion intake check")
        print(f"- {error}")
        print("RESULT: COMPLETION_INTAKE_CHECK_FAILED")
        return 1

    print("Completion intake check")
    print(f"module: {result.module_id}")
    print(f"prompt: {result.prompt_id}")
    print(f"phase: {result.phase}")
    print(f"packet: {result.packet_path}")
    print(f"report: {result.report_path}")
    print(f"implementation commit: {result.implementation_commit}")
    print(f"completion commit: {result.completion_commit}")
    print(
        "publication: "
        f"{result.remote}/{result.branch} @ {result.remote_commit}"
    )
    if result.warnings:
        print("warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    else:
        print("warnings: 0")
    print("RESULT: COMPLETION_INTAKE_CHECK_PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
