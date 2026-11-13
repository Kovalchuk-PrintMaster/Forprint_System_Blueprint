#!/usr/bin/env python3
"""Read-only Blueprint validation of a module completion intake packet."""

from __future__ import annotations

import argparse
import json
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
HEX_COMMIT = re.compile(r"^[0-9a-f]{7,40}$")
FULL_HEX_COMMIT = re.compile(r"^[0-9a-f]{40}$")
LEGACY_PACKET_SCHEMA = "module_completion_packet_v0_1"
LEGACY_INTAKE_PROTOCOL = "blueprint_completion_intake_v0_1"
CURRENT_PACKET_SCHEMA = "module_completion_packet_v0_2"
CURRENT_INTAKE_PROTOCOL = "blueprint_completion_intake_v0_2"
CANDIDATE_PACKET_SCHEMA = "module_completion_packet_v0_3"
CANDIDATE_INTAKE_PROTOCOL = "blueprint_completion_intake_v0_3"
PROMPT_CONTRACT_SCHEMA = "module_prompt_contract_v0_3"
STRUCTURED_OUTPUT_FORMATS = {"json", "yaml"}


class CompletionIntakeCheckError(ValueError):
    """Raised when completion evidence is unsafe or incomplete."""


class DuplicateKeyError(yaml.YAMLError):
    """Raised when a YAML mapping contains a duplicate key."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


@dataclass(frozen=True)
class PacketProtocol:
    """Normalized completion packet schema and intake protocol metadata."""

    schema_version: str
    protocol_version: str
    supersedes_completion_id: str | None
    revision_reason: str | None
    historical_legacy: bool


@dataclass(frozen=True)
class CompletionIntakeIssue:
    """Machine-readable intake failure without an acceptance decision."""

    code: str
    failure_class: str
    message: str
    field: str | None
    remediation_owner: str
    implementation_failure_proven: bool


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
            raise DuplicateKeyError(f"duplicate key `{key}` at line {line}, column {column}")
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
    warnings: tuple[str, ...] = ()
    schema_version: str = LEGACY_PACKET_SCHEMA
    protocol_version: str = LEGACY_INTAKE_PROTOCOL
    supersedes_completion_id: str | None = None
    historical_legacy: bool = True
    implementation_base_commit: str | None = None
    requirement_coverage: tuple[str, ...] = ()
    check_coverage: tuple[str, ...] = ()
    intake_stages: tuple[str, ...] = ()
    candidate_reference: bool = False
    packet_push_status: str | None = None
    publication_verified: bool = False


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise CompletionIntakeCheckError(f"file does not exist: {path}") from error
    try:
        loaded = yaml.load(text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise CompletionIntakeCheckError(f"invalid YAML in {path}: {error}") from error
    if not isinstance(loaded, dict):
        raise CompletionIntakeCheckError(f"YAML root must be a mapping: {path}")
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


def _optional_non_empty_string(
    data: dict[str, Any],
    field: str,
) -> str | None:
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise CompletionIntakeCheckError(
            f"[PACKET_PROTOCOL_FIELD_INVALID] "
            f"completion packet field `{field}` must be a non-empty string"
        )
    return value.strip()


def _packet_protocol(data: dict[str, Any]) -> PacketProtocol:
    schema = data.get("schema_version")
    protocol = data.get("protocol_version")

    if schema is None and protocol in {
        None,
        LEGACY_INTAKE_PROTOCOL,
    }:
        return PacketProtocol(
            schema_version=LEGACY_PACKET_SCHEMA,
            protocol_version=LEGACY_INTAKE_PROTOCOL,
            supersedes_completion_id=None,
            revision_reason=None,
            historical_legacy=True,
        )

    if schema == LEGACY_PACKET_SCHEMA:
        if protocol not in {None, LEGACY_INTAKE_PROTOCOL}:
            raise CompletionIntakeCheckError(
                "[PACKET_PROTOCOL_MISMATCH] legacy packet schema must use "
                f"`{LEGACY_INTAKE_PROTOCOL}`"
            )
        return PacketProtocol(
            schema_version=LEGACY_PACKET_SCHEMA,
            protocol_version=LEGACY_INTAKE_PROTOCOL,
            supersedes_completion_id=None,
            revision_reason=None,
            historical_legacy=True,
        )

    if schema == CURRENT_PACKET_SCHEMA:
        if protocol != CURRENT_INTAKE_PROTOCOL:
            raise CompletionIntakeCheckError(
                "[PACKET_PROTOCOL_MISMATCH] "
                f"`{CURRENT_PACKET_SCHEMA}` requires "
                f"`{CURRENT_INTAKE_PROTOCOL}`"
            )

        implementation_commit = data.get("implementation_commit")
        if (
            not isinstance(implementation_commit, str)
            or FULL_HEX_COMMIT.fullmatch(implementation_commit) is None
        ):
            raise CompletionIntakeCheckError(
                "[COMMIT_IDENTIFIER_INVALID] v0.2 completion packet "
                "`implementation_commit` must be a full 40-character "
                "lowercase Git hash"
            )

        supersedes = _optional_non_empty_string(
            data,
            "supersedes_completion_id",
        )
        revision_reason = _optional_non_empty_string(
            data,
            "revision_reason",
        )
        if (supersedes is None) != (revision_reason is None):
            raise CompletionIntakeCheckError(
                "[SUPERSEDING_PACKET_INCOMPLETE] "
                "`supersedes_completion_id` and `revision_reason` "
                "must be provided together"
            )

        return PacketProtocol(
            schema_version=CURRENT_PACKET_SCHEMA,
            protocol_version=CURRENT_INTAKE_PROTOCOL,
            supersedes_completion_id=supersedes,
            revision_reason=revision_reason,
            historical_legacy=False,
        )

    if schema == CANDIDATE_PACKET_SCHEMA:
        if protocol != CANDIDATE_INTAKE_PROTOCOL:
            raise CompletionIntakeCheckError(
                "[PACKET_PROTOCOL_MISMATCH] "
                f"`{CANDIDATE_PACKET_SCHEMA}` requires "
                f"`{CANDIDATE_INTAKE_PROTOCOL}`"
            )

        supersedes = _optional_non_empty_string(
            data,
            "supersedes_completion_id",
        )
        revision_reason = _optional_non_empty_string(
            data,
            "revision_reason",
        )
        supersedes_packet_path = _optional_non_empty_string(
            data,
            "supersedes_packet_path",
        )
        supplied = (
            supersedes is not None,
            revision_reason is not None,
            supersedes_packet_path is not None,
        )
        if len(set(supplied)) != 1:
            raise CompletionIntakeCheckError(
                "[SUPERSEDING_PACKET_INCOMPLETE] v0.3 superseding evidence "
                "must provide `supersedes_completion_id`, "
                "`supersedes_packet_path`, and `revision_reason` together"
            )

        return PacketProtocol(
            schema_version=CANDIDATE_PACKET_SCHEMA,
            protocol_version=CANDIDATE_INTAKE_PROTOCOL,
            supersedes_completion_id=supersedes,
            revision_reason=revision_reason,
            historical_legacy=False,
        )

    raise CompletionIntakeCheckError(
        f"[UNSUPPORTED_PACKET_SCHEMA] unsupported completion packet schema: {schema!r}"
    )


def _safe_under(root: Path, candidate: Path, *, label: str) -> Path:
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve()
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError as error:
        raise CompletionIntakeCheckError(f"{label} escapes repository root: {candidate}") from error
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
        raise CompletionIntakeCheckError(f"git {' '.join(args)} failed in {repo}: {detail}")
    return completed


def _run_git(repo: Path, *args: str) -> str:
    return (
        _run_git_bytes(repo, *args)
        .stdout.decode(
            "utf-8",
            errors="replace",
        )
        .strip()
    )


def _verify_commit(repo: Path, commit: str, *, label: str) -> str:
    if HEX_COMMIT.fullmatch(commit) is None:
        raise CompletionIntakeCheckError(
            f"[COMMIT_IDENTIFIER_INVALID] {label} must be a 7-to-40 character lowercase Git hash"
        )
    resolved = _run_git(
        repo,
        "rev-parse",
        "--verify",
        f"{commit}^{{commit}}",
    )
    if FULL_HEX_COMMIT.fullmatch(resolved) is None:
        raise CompletionIntakeCheckError(
            f"[COMMIT_RESOLUTION_FAILED] could not resolve {label}: {commit}"
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
        raise CompletionIntakeCheckError(f"{label} content differs from `{commit}:{relative_path}`")


def _validate_iso_date(value: str, *, field: str) -> None:
    if len(value) < 10:
        raise CompletionIntakeCheckError(f"`{field}` is not an ISO date/timestamp: {value!r}")
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
        raise CompletionIntakeCheckError("completion packet `checks` must be a mapping")
    for name in REQUIRED_CHECKS:
        if name not in checks:
            raise CompletionIntakeCheckError(f"completion packet `checks.{name}` is required")
        if not _normalize_check(checks[name]):
            raise CompletionIntakeCheckError(
                f"completion packet `checks.{name}` is not successful: {checks[name]!r}"
            )
    failed = checks.get("check_report_failed")
    if failed is not None and (not isinstance(failed, int) or isinstance(failed, bool)):
        raise CompletionIntakeCheckError("`checks.check_report_failed` must be an integer")
    if isinstance(failed, int) and failed > 0:
        raise CompletionIntakeCheckError(f"module check report contains {failed} failed check(s)")
    warning_count = checks.get("check_report_warnings")
    if warning_count is not None and (
        not isinstance(warning_count, int) or isinstance(warning_count, bool)
    ):
        raise CompletionIntakeCheckError("`checks.check_report_warnings` must be an integer")
    warnings: list[str] = []
    if isinstance(warning_count, int) and warning_count > 0:
        warnings.append(f"module check report contains {warning_count} warning(s)")
    return warnings


def _validate_boundary(packet: dict[str, Any]) -> None:
    boundary = packet.get("boundary_confirmation")
    if not isinstance(boundary, dict) or not boundary:
        raise CompletionIntakeCheckError(
            "completion packet `boundary_confirmation` must be a non-empty mapping"
        )
    unsafe: list[str] = []
    for required in REQUIRED_BOUNDARY_FLAGS:
        if boundary.get(required) is not True:
            unsafe.append(f"{required} must be true")
    for key, value in boundary.items():
        if key.startswith("no_") and value is not True:
            unsafe.append(f"{key} must be true")
        elif key.endswith(("_added", "_committed", "_written_directly")) and value is not False:
            unsafe.append(f"{key} must be false")
    if unsafe:
        raise CompletionIntakeCheckError(
            "unsafe boundary confirmation:\n- " + "\n- ".join(sorted(set(unsafe)))
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
        record for record in records if isinstance(record, dict) and record.get(key) == value
    ]
    if len(matches) != 1:
        raise CompletionIntakeCheckError(
            f"expected exactly one {label} record for `{value}`, found {len(matches)}"
        )
    return matches[0]


def _git_path_exists_at_commit(
    repo: Path,
    commit: str,
    relative_path: str,
) -> bool:
    result = _run_git_bytes(
        repo,
        "cat-file",
        "-e",
        f"{commit}:{relative_path}",
        allowed_returncodes=(0, 1),
    )
    return result.returncode == 0


def _git_yaml_at_commit(
    repo: Path,
    commit: str,
    relative_path: str,
) -> dict[str, Any]:
    completed = _run_git_bytes(
        repo,
        "show",
        f"{commit}:{relative_path}",
    )
    try:
        loaded = yaml.load(
            completed.stdout.decode("utf-8", errors="replace"),
            Loader=UniqueKeyLoader,
        )
    except yaml.YAMLError as error:
        raise CompletionIntakeCheckError(
            f"[SUPERSEDED_PACKET_INVALID] invalid YAML in committed evidence "
            f"`{relative_path}`: {error}"
        ) from error
    if not isinstance(loaded, dict):
        raise CompletionIntakeCheckError(
            f"[SUPERSEDED_PACKET_INVALID] committed evidence "
            f"`{relative_path}` must be a YAML mapping"
        )
    return loaded


def _git_changed_paths(
    repo: Path,
    base_commit: str,
    tip_commit: str,
) -> set[str]:
    output = _run_git(
        repo,
        "diff",
        "--name-only",
        base_commit,
        tip_commit,
    )
    return {line.strip() for line in output.splitlines() if line.strip()}


def _load_markdown_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise CompletionIntakeCheckError(
            "[REPORT_PACKET_MISMATCH] v0.3 completion report must start with YAML frontmatter"
        )
    closing = text.find("\n---", 4)
    if closing < 0:
        raise CompletionIntakeCheckError(
            "[REPORT_PACKET_MISMATCH] v0.3 completion report frontmatter is not closed"
        )
    raw = text[4:closing]
    try:
        loaded = yaml.load(raw, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise CompletionIntakeCheckError(
            f"[REPORT_PACKET_MISMATCH] invalid completion report frontmatter: {error}"
        ) from error
    if not isinstance(loaded, dict):
        raise CompletionIntakeCheckError(
            "[REPORT_PACKET_MISMATCH] completion report frontmatter must be a YAML mapping"
        )
    return loaded


def _prompt_contract_path(
    blueprint_root: Path,
    module_id: str,
    prompt_id: str,
) -> Path:
    return blueprint_root / "coordination" / "prompt_contracts" / module_id / f"{prompt_id}.yaml"


def _validate_prompt_contract(
    *,
    blueprint_root: Path,
    module_id: str,
    prompt_id: str,
    phase: str,
) -> tuple[dict[str, Any], Path]:
    contract_path = _prompt_contract_path(
        blueprint_root,
        module_id,
        prompt_id,
    )
    if not contract_path.is_file():
        raise CompletionIntakeCheckError(
            f"[PROMPT_CONTRACT_MISSING] current v0.3 prompt contract is missing: {contract_path}"
        )
    contract = _load_yaml_mapping(contract_path)
    if contract.get("schema_version") != PROMPT_CONTRACT_SCHEMA:
        raise CompletionIntakeCheckError(
            f"[PROMPT_CONTRACT_INVALID] prompt contract schema must be `{PROMPT_CONTRACT_SCHEMA}`"
        )
    if contract.get("module_id") != module_id:
        raise CompletionIntakeCheckError(
            "[PROMPT_CONTRACT_INVALID] prompt contract module_id mismatch"
        )
    if contract.get("prompt_id") != prompt_id:
        raise CompletionIntakeCheckError(
            "[PROMPT_CONTRACT_INVALID] prompt contract prompt_id mismatch"
        )
    if contract.get("phase") != phase:
        raise CompletionIntakeCheckError("[PROMPT_CONTRACT_INVALID] prompt contract phase mismatch")

    source_prompt = contract.get("source_prompt")
    if not isinstance(source_prompt, dict):
        raise CompletionIntakeCheckError(
            "[PROMPT_CONTRACT_INVALID] prompt contract `source_prompt` must be a mapping"
        )
    source_path = source_prompt.get("path")
    source_hash = source_prompt.get("sha256")
    if (
        not isinstance(source_path, str)
        or not source_path.strip()
        or not isinstance(source_hash, str)
        or re.fullmatch(r"[0-9a-f]{64}", source_hash) is None
    ):
        raise CompletionIntakeCheckError(
            "[PROMPT_CONTRACT_INVALID] prompt contract source_prompt must "
            "contain `path` and 64-character lowercase `sha256`"
        )
    prompt_path = _safe_under(
        blueprint_root,
        blueprint_root / source_path,
        label="prompt contract source prompt",
    )
    if not prompt_path.is_file():
        raise CompletionIntakeCheckError(
            f"[PROMPT_SOURCE_HASH_MISMATCH] source prompt file does not exist: {source_path}"
        )
    actual_hash = __import__("hashlib").sha256(prompt_path.read_bytes()).hexdigest()
    if actual_hash != source_hash:
        raise CompletionIntakeCheckError(
            "[PROMPT_SOURCE_HASH_MISMATCH] source prompt hash differs from the prompt contract"
        )

    requirements = contract.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise CompletionIntakeCheckError(
            "[PROMPT_CONTRACT_INVALID] prompt contract requirements must be a non-empty list"
        )
    requirement_ids: set[str] = set()
    for item in requirements:
        if not isinstance(item, dict):
            raise CompletionIntakeCheckError(
                "[PROMPT_CONTRACT_INVALID] every requirement must be a mapping"
            )
        requirement_id = item.get("id")
        if (
            not isinstance(requirement_id, str)
            or not requirement_id.strip()
            or requirement_id in requirement_ids
        ):
            raise CompletionIntakeCheckError(
                "[PROMPT_CONTRACT_INVALID] requirement ids must be unique non-empty strings"
            )
        requirement_ids.add(requirement_id)
        if item.get("evidence_policy") not in {
            "paths_and_tests",
            "artifacts",
            "boundary",
        }:
            raise CompletionIntakeCheckError(
                "[PROMPT_CONTRACT_INVALID] unsupported requirement "
                f"evidence_policy for `{requirement_id}`"
            )

    required_checks = contract.get("required_checks")
    if not isinstance(required_checks, list) or not required_checks:
        raise CompletionIntakeCheckError(
            "[PROMPT_CONTRACT_INVALID] required_checks must be a non-empty list"
        )
    check_ids: set[str] = set()
    for item in required_checks:
        if not isinstance(item, dict):
            raise CompletionIntakeCheckError(
                "[PROMPT_CONTRACT_INVALID] every required check must be a mapping"
            )
        check_id = item.get("id")
        command = item.get("command")
        if (
            not isinstance(check_id, str)
            or not check_id.strip()
            or check_id in check_ids
            or not isinstance(command, str)
            or not command.strip()
        ):
            raise CompletionIntakeCheckError(
                "[PROMPT_CONTRACT_INVALID] required checks need unique ids and non-empty commands"
            )
        check_ids.add(check_id)

    return contract, contract_path


def _validate_v0_3_completion_evidence(
    *,
    blueprint_root: Path,
    module_root: Path,
    module_id: str,
    prompt_id: str,
    phase: str,
    packet: dict[str, Any],
    packet_protocol: PacketProtocol,
    report_path: Path,
    completion_commit: str,
) -> tuple[str, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    contract, _contract_path = _validate_prompt_contract(
        blueprint_root=blueprint_root,
        module_id=module_id,
        prompt_id=prompt_id,
        phase=phase,
    )

    packet_contract = packet.get("prompt_contract")
    if not isinstance(packet_contract, dict):
        raise CompletionIntakeCheckError(
            "[PROMPT_CONTRACT_REFERENCE_INVALID] v0.3 packet `prompt_contract` must be a mapping"
        )
    for key, expected in (
        ("contract_id", contract.get("contract_id")),
        ("revision", PROMPT_CONTRACT_SCHEMA),
        (
            "source_prompt_sha256",
            contract.get("source_prompt", {}).get("sha256"),
        ),
    ):
        if packet_contract.get(key) != expected:
            raise CompletionIntakeCheckError(
                "[PROMPT_CONTRACT_REFERENCE_INVALID] packet prompt contract "
                f"`{key}` does not match Blueprint contract"
            )

    implementation_range = packet.get("implementation_range")
    if not isinstance(implementation_range, dict):
        raise CompletionIntakeCheckError(
            "[IMPLEMENTATION_RANGE_INVALID] v0.3 packet `implementation_range` must be a mapping"
        )
    base_raw = implementation_range.get("base_commit")
    tip_raw = implementation_range.get("tip_commit")
    if (
        not isinstance(base_raw, str)
        or FULL_HEX_COMMIT.fullmatch(base_raw) is None
        or not isinstance(tip_raw, str)
        or FULL_HEX_COMMIT.fullmatch(tip_raw) is None
    ):
        raise CompletionIntakeCheckError(
            "[IMPLEMENTATION_RANGE_INVALID] implementation base/tip commits "
            "must be full 40-character lowercase Git hashes"
        )
    expected_base = contract.get("implementation_base_commit")
    if expected_base is not None and base_raw != expected_base:
        raise CompletionIntakeCheckError(
            "[IMPLEMENTATION_RANGE_INVALID] implementation base commit does "
            "not match the prompt contract"
        )
    base_commit = _verify_commit(
        module_root,
        base_raw,
        label="implementation_base_commit",
    )
    tip_commit = _verify_commit(
        module_root,
        tip_raw,
        label="implementation_tip_commit",
    )
    if not _is_ancestor(module_root, base_commit, tip_commit):
        raise CompletionIntakeCheckError(
            "[IMPLEMENTATION_RANGE_INVALID] implementation base commit is "
            "not an ancestor of implementation tip commit"
        )
    if not _is_ancestor(module_root, tip_commit, completion_commit):
        raise CompletionIntakeCheckError(
            "[IMPLEMENTATION_RANGE_INVALID] implementation tip commit is "
            "not an ancestor of completion commit"
        )

    changed_paths = _git_changed_paths(
        module_root,
        base_commit,
        tip_commit,
    )

    contract_requirements = {
        item["id"]: item for item in contract["requirements"] if item.get("required", True)
    }
    raw_results = packet.get("requirement_results")
    if not isinstance(raw_results, list) or not raw_results:
        raise CompletionIntakeCheckError(
            "[PROMPT_REQUIREMENT_COVERAGE_INCOMPLETE] v0.3 packet "
            "`requirement_results` must be a non-empty list"
        )
    results: dict[str, dict[str, Any]] = {}
    for item in raw_results:
        if not isinstance(item, dict):
            raise CompletionIntakeCheckError(
                "[PROMPT_REQUIREMENT_COVERAGE_INCOMPLETE] requirement results must be mappings"
            )
        requirement_id = item.get("requirement_id")
        if not isinstance(requirement_id, str) or not requirement_id or requirement_id in results:
            raise CompletionIntakeCheckError(
                "[PROMPT_REQUIREMENT_COVERAGE_INCOMPLETE] requirement result "
                "ids must be unique non-empty strings"
            )
        results[requirement_id] = item

    missing = sorted(set(contract_requirements) - set(results))
    unknown = sorted(set(results) - {item["id"] for item in contract["requirements"]})
    if missing or unknown:
        raise CompletionIntakeCheckError(
            "[PROMPT_REQUIREMENT_COVERAGE_INCOMPLETE] requirement coverage "
            f"mismatch; missing={missing}, unknown={unknown}"
        )

    boundary = packet.get("boundary_confirmation")
    for requirement_id, requirement in contract_requirements.items():
        result = results[requirement_id]
        if result.get("status") != "completed":
            raise CompletionIntakeCheckError(
                "[PROMPT_REQUIREMENT_COVERAGE_INCOMPLETE] requirement "
                f"`{requirement_id}` is not completed"
            )
        policy = requirement["evidence_policy"]
        if policy == "paths_and_tests":
            implementation_paths = result.get("implementation_paths")
            test_paths = result.get("test_paths")
            if (
                not isinstance(implementation_paths, list)
                or not implementation_paths
                or not isinstance(test_paths, list)
                or not test_paths
            ):
                raise CompletionIntakeCheckError(
                    "[PROMPT_REQUIREMENT_EVIDENCE_INVALID] requirement "
                    f"`{requirement_id}` requires implementation_paths "
                    "and test_paths"
                )
            evidence_paths = implementation_paths + test_paths
            for relative_path in evidence_paths:
                if (
                    not isinstance(relative_path, str)
                    or not relative_path
                    or not _git_path_exists_at_commit(
                        module_root,
                        tip_commit,
                        relative_path,
                    )
                ):
                    raise CompletionIntakeCheckError(
                        "[PROMPT_REQUIREMENT_EVIDENCE_INVALID] requirement "
                        f"`{requirement_id}` references missing evidence path "
                        f"`{relative_path}` at implementation tip"
                    )
            if requirement.get("changed_path_required", True) and not any(
                path in changed_paths for path in evidence_paths
            ):
                raise CompletionIntakeCheckError(
                    "[PROMPT_REQUIREMENT_EVIDENCE_INVALID] requirement "
                    f"`{requirement_id}` has no evidence path changed inside "
                    "the implementation range"
                )
        elif policy == "artifacts":
            artifact_paths = result.get("artifact_paths")
            if not isinstance(artifact_paths, list) or not artifact_paths:
                raise CompletionIntakeCheckError(
                    "[PROMPT_REQUIREMENT_EVIDENCE_INVALID] requirement "
                    f"`{requirement_id}` requires artifact_paths"
                )
            for relative_path in artifact_paths:
                if (
                    not isinstance(relative_path, str)
                    or not relative_path
                    or not _git_path_exists_at_commit(
                        module_root,
                        tip_commit,
                        relative_path,
                    )
                ):
                    raise CompletionIntakeCheckError(
                        "[PROMPT_REQUIREMENT_EVIDENCE_INVALID] requirement "
                        f"`{requirement_id}` references missing artifact "
                        f"`{relative_path}` at implementation tip"
                    )
        elif policy == "boundary":
            for flag in requirement.get("boundary_flags", []):
                if not isinstance(boundary, dict) or boundary.get(flag) is not True:
                    raise CompletionIntakeCheckError(
                        "[SAFETY_CONFIRMATION_INVALID] requirement "
                        f"`{requirement_id}` requires boundary flag "
                        f"`{flag}: true`"
                    )

    required_checks = {item["id"]: item for item in contract["required_checks"]}
    raw_check_results = packet.get("check_results")
    if not isinstance(raw_check_results, list) or not raw_check_results:
        raise CompletionIntakeCheckError(
            "[REQUIRED_CHECK_EVIDENCE_MISSING] v0.3 packet `check_results` must be a non-empty list"
        )
    check_results: dict[str, dict[str, Any]] = {}
    for item in raw_check_results:
        if not isinstance(item, dict):
            raise CompletionIntakeCheckError(
                "[REQUIRED_CHECK_EVIDENCE_MISSING] check results must be mappings"
            )
        check_id = item.get("check_id")
        if not isinstance(check_id, str) or not check_id or check_id in check_results:
            raise CompletionIntakeCheckError(
                "[REQUIRED_CHECK_EVIDENCE_MISSING] check result ids must be "
                "unique non-empty strings"
            )
        check_results[check_id] = item

    missing_checks = sorted(set(required_checks) - set(check_results))
    if missing_checks:
        raise CompletionIntakeCheckError(
            "[REQUIRED_CHECK_EVIDENCE_MISSING] missing required check results: "
            + ", ".join(missing_checks)
        )
    for check_id, expected in required_checks.items():
        result = check_results[check_id]
        if result.get("command") != expected["command"]:
            raise CompletionIntakeCheckError(
                f"[REQUIRED_CHECK_EVIDENCE_MISSING] check command mismatch for `{check_id}`"
            )
        if not _normalize_check(result.get("status")):
            raise CompletionIntakeCheckError(
                f"[REQUIRED_CHECK_EVIDENCE_FAILED] required check `{check_id}` did not pass"
            )

    current_outputs = packet.get("current_outputs", [])
    for relative_path in current_outputs:
        if (
            not isinstance(relative_path, str)
            or not relative_path
            or relative_path.startswith("/")
            or ".." in Path(relative_path).parts
            or not _git_path_exists_at_commit(
                module_root,
                completion_commit,
                relative_path,
            )
        ):
            raise CompletionIntakeCheckError(
                "[CURRENT_OUTPUT_MISSING] current output is not committed "
                f"at completion commit: {relative_path!r}"
            )

    report_frontmatter = _load_markdown_frontmatter(report_path)
    report_expectations = {
        "schema_version": CANDIDATE_PACKET_SCHEMA,
        "protocol_version": CANDIDATE_INTAKE_PROTOCOL,
        "prompt_id": prompt_id,
        "target_module": module_id,
        "phase": phase,
        "prompt_contract_id": contract.get("contract_id"),
        "implementation_base_commit": base_commit,
        "implementation_tip_commit": tip_commit,
    }
    for key, expected in report_expectations.items():
        if report_frontmatter.get(key) != expected:
            raise CompletionIntakeCheckError(
                "[REPORT_PACKET_MISMATCH] completion report frontmatter "
                f"`{key}` does not match packet/contract evidence"
            )

    if packet_protocol.supersedes_completion_id is not None:
        supersedes_packet_path = packet.get("supersedes_packet_path")
        if (
            not isinstance(supersedes_packet_path, str)
            or not supersedes_packet_path.startswith("coordination/completion_packets/records/")
            or not _git_path_exists_at_commit(
                module_root,
                completion_commit,
                supersedes_packet_path,
            )
        ):
            raise CompletionIntakeCheckError(
                "[SUPERSEDED_PACKET_MISSING] superseded packet path does not "
                "resolve at completion commit"
            )
        historical = _git_yaml_at_commit(
            module_root,
            completion_commit,
            supersedes_packet_path,
        )
        if historical.get("completion_id") != packet_protocol.supersedes_completion_id:
            raise CompletionIntakeCheckError(
                "[SUPERSEDED_PACKET_INVALID] superseded packet completion_id "
                "does not match `supersedes_completion_id`"
            )

    stages = (
        "schema_protocol_valid",
        "safety_boundary_valid",
        "blueprint_control_valid",
        "publication_evidence_valid",
        "prompt_contract_valid",
        "implementation_range_valid",
        "prompt_requirement_coverage_valid",
        "required_check_coverage_valid",
        "packet_report_consistent",
        "superseding_chain_valid",
    )
    return (
        base_commit,
        tip_commit,
        tuple(sorted(contract_requirements)),
        tuple(sorted(required_checks)),
        stages,
    )


def _validate_blueprint_context(
    *,
    blueprint_root: Path,
    module_id: str,
    prompt_id: str,
    phase: str,
) -> None:
    queue_path = blueprint_root / "coordination/outgoing_prompts" / module_id / "index.yaml"
    roadmap_path = blueprint_root / "coordination/roadmaps" / f"{module_id}.yaml"
    queue = _load_yaml_mapping(queue_path)
    roadmap = _load_yaml_mapping(roadmap_path)
    if queue.get("module") not in {None, module_id}:
        raise CompletionIntakeCheckError(f"prompt queue module does not match `{module_id}`")
    prompt = _single_record(
        queue.get("prompt_queue"),
        key="prompt_id",
        value=prompt_id,
        label="prompt queue",
    )
    if prompt.get("target_module") not in {None, module_id}:
        raise CompletionIntakeCheckError("prompt target_module does not match packet module_id")
    if prompt.get("phase") not in {None, phase}:
        raise CompletionIntakeCheckError("prompt phase does not match completion packet phase")
    step = _single_record(
        roadmap.get("roadmap"),
        key="step_id",
        value=prompt_id,
        label="roadmap",
    )
    if step.get("owner_module") not in {None, module_id}:
        raise CompletionIntakeCheckError("roadmap owner_module does not match packet module_id")
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
        raise CompletionIntakeCheckError(f"unsafe publication branch: {branch!r}")
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
            f"expected one remote branch `refs/heads/{branch}` on `{remote}`, found {len(lines)}"
        )
    fields = lines[0].split()
    if len(fields) != 2:
        raise CompletionIntakeCheckError("unexpected git ls-remote output")
    commit, reference = fields
    if HEX_COMMIT.fullmatch(commit) is None or reference != f"refs/heads/{branch}":
        raise CompletionIntakeCheckError("unexpected git ls-remote branch record")
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
            "completion commit is not contained in the selected remote branch"
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
    allow_candidate_reference: bool = False,
) -> CompletionIntakeCheckResult:
    """Validate completion evidence without repository writes."""

    blueprint_root = blueprint_root.resolve()
    module_root = module_root.resolve()
    if not module_root.is_dir():
        raise CompletionIntakeCheckError(f"module root does not exist: {module_root}")

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
    if not packet_relative.startswith("coordination/completion_packets/"):
        raise CompletionIntakeCheckError(
            "completion packet must be under `coordination/completion_packets/`"
        )

    data = _load_yaml_mapping(packet_path)
    packet_protocol = _packet_protocol(data)

    required_strings = tuple(
        field for field in REQUIRED_PACKET_STRINGS if field != "implementation_commit"
    )
    for field in required_strings:
        _required_string(data, field)
    required_lists = (
        tuple(field for field in REQUIRED_PACKET_LISTS if field != "implemented")
        if packet_protocol.schema_version == CANDIDATE_PACKET_SCHEMA
        else REQUIRED_PACKET_LISTS
    )
    for field in required_lists:
        _required_non_empty_list(data, field)

    packet_module = _required_string(data, "module_id")
    if packet_module != module_id:
        raise CompletionIntakeCheckError(
            f"packet module_id `{packet_module}` does not match requested module `{module_id}`"
        )

    prompt_id = _required_string(data, "prompt_id")
    phase = _required_string(data, "phase")
    created_at = _required_string(data, "created_at")
    _validate_iso_date(created_at, field="created_at")

    report_relative = _required_string(data, "report_path")
    if not report_relative.startswith("coordination/reports/completion/"):
        raise CompletionIntakeCheckError(
            "completion report must be under `coordination/reports/completion/`"
        )
    report_path = _safe_under(
        module_root,
        module_root / report_relative,
        label="completion report",
    )
    if not report_path.is_file():
        raise CompletionIntakeCheckError(f"completion report does not exist: {report_path}")

    resolved_completion_commit = _verify_commit(
        module_root,
        completion_commit,
        label="completion_commit",
    )

    implementation_base_commit: str | None = None
    requirement_coverage: tuple[str, ...] = ()
    check_coverage: tuple[str, ...] = ()
    intake_stages: tuple[str, ...] = ()

    if packet_protocol.schema_version == CANDIDATE_PACKET_SCHEMA:
        implementation_commit = ""
    else:
        implementation_commit = _verify_commit(
            module_root,
            _required_string(data, "implementation_commit"),
            label="implementation_commit",
        )
        if not _is_ancestor(
            module_root,
            implementation_commit,
            resolved_completion_commit,
        ):
            raise CompletionIntakeCheckError(
                "implementation_commit is not an ancestor of completion_commit"
            )

    warnings = (
        [] if packet_protocol.schema_version == CANDIDATE_PACKET_SCHEMA else _validate_checks(data)
    )
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

    if packet_protocol.schema_version == CANDIDATE_PACKET_SCHEMA:
        (
            implementation_base_commit,
            implementation_commit,
            requirement_coverage,
            check_coverage,
            intake_stages,
        ) = _validate_v0_3_completion_evidence(
            blueprint_root=blueprint_root,
            module_root=module_root,
            module_id=module_id,
            prompt_id=prompt_id,
            phase=phase,
            packet=data,
            packet_protocol=packet_protocol,
            report_path=report_path,
            completion_commit=resolved_completion_commit,
        )

    candidate_reference = packet_protocol.schema_version == CANDIDATE_PACKET_SCHEMA

    packet_branch = data.get("branch")
    if packet_branch is not None and (
        not isinstance(packet_branch, str) or not packet_branch.strip()
    ):
        raise CompletionIntakeCheckError(
            "completion packet `branch` must be a non-empty string when present"
        )
    selected_branch = _validate_branch(
        branch or (packet_branch.strip() if isinstance(packet_branch, str) else "")
    )

    packet_push_status = data.get("push_status")
    post_publication_statuses = {"pushed", "synced", "remote"}
    allowed_push_statuses = set(post_publication_statuses)
    if candidate_reference:
        allowed_push_statuses.add("pending_operator_publication")

    if packet_push_status not in allowed_push_statuses:
        if candidate_reference:
            raise CompletionIntakeCheckError(
                "candidate completion packet `push_status` must be one of: "
                "pending_operator_publication, pushed, synced, remote"
            )
        raise CompletionIntakeCheckError(
            "completion packet `push_status` must indicate post-publication state"
        )

    selected_remote = remote.strip()
    if not selected_remote:
        raise CompletionIntakeCheckError("remote must be a non-empty string")

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

    if candidate_reference and not allow_candidate_reference:
        raise CompletionIntakeCheckError(
            "[PROTOCOL_NOT_ACTIVATED] v0.3 completion evidence passed "
            "candidate validation but v0.3 is not operational current yet; "
            "use `--allow-candidate-reference` only for read-only reference "
            "validation"
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
        schema_version=packet_protocol.schema_version,
        protocol_version=packet_protocol.protocol_version,
        supersedes_completion_id=(packet_protocol.supersedes_completion_id),
        historical_legacy=packet_protocol.historical_legacy,
        warnings=tuple(warnings),
        implementation_base_commit=implementation_base_commit,
        requirement_coverage=requirement_coverage,
        check_coverage=check_coverage,
        intake_stages=intake_stages,
        candidate_reference=candidate_reference,
        packet_push_status=(packet_push_status if isinstance(packet_push_status, str) else None),
        publication_verified=True,
    )


def _classify_intake_error(
    error: CompletionIntakeCheckError,
) -> CompletionIntakeIssue:
    raw_message = str(error)
    code_match = re.match(
        r"^\[(?P<code>[A-Z0-9_]+)\]\s*(?P<message>.*)$",
        raw_message,
        flags=re.DOTALL,
    )
    if code_match is not None:
        code = code_match.group("code")
        message = code_match.group("message")
    else:
        code = ""
        message = raw_message

    lowered = message.lower()
    field: str | None = None
    remediation_owner = "module"
    failure_class = "evidence_failure"
    implementation_failure_proven = False

    if code in {
        "UNSUPPORTED_PACKET_SCHEMA",
        "PACKET_PROTOCOL_MISMATCH",
        "PACKET_PROTOCOL_FIELD_INVALID",
        "SUPERSEDING_PACKET_INCOMPLETE",
    }:
        failure_class = "protocol_compatibility"
    elif code == "PROTOCOL_NOT_ACTIVATED":
        failure_class = "protocol_activation_gate"
        field = "protocol_version"
        remediation_owner = "blueprint"
    elif code in {
        "PROMPT_CONTRACT_MISSING",
        "PROMPT_CONTRACT_INVALID",
        "PROMPT_SOURCE_HASH_MISMATCH",
    }:
        failure_class = "blueprint_control_failure"
        field = "prompt_contract"
        remediation_owner = "blueprint"
    elif code == "PROMPT_CONTRACT_REFERENCE_INVALID":
        failure_class = "protocol_compatibility"
        field = "prompt_contract"
    elif code in {
        "PROMPT_REQUIREMENT_COVERAGE_INCOMPLETE",
        "PROMPT_REQUIREMENT_EVIDENCE_INVALID",
        "REQUIRED_CHECK_EVIDENCE_MISSING",
        "REQUIRED_CHECK_EVIDENCE_FAILED",
        "REPORT_PACKET_MISMATCH",
        "IMPLEMENTATION_RANGE_INVALID",
        "SUPERSEDED_PACKET_MISSING",
        "SUPERSEDED_PACKET_INVALID",
        "CURRENT_OUTPUT_MISSING",
    }:
        failure_class = "evidence_failure"
    elif code in {
        "COMMIT_IDENTIFIER_INVALID",
        "COMMIT_RESOLUTION_FAILED",
    }:
        failure_class = "evidence_failure"
        field = "commit"
    elif "unsafe boundary confirmation" in lowered:
        code = "SAFETY_CONFIRMATION_INVALID"
        failure_class = "protocol_compatibility"
        field = "boundary_confirmation"
    elif "completion packet field" in lowered:
        code = code or "PACKET_FIELD_INVALID"
        failure_class = "protocol_compatibility"
    elif "completion packet `checks" in lowered or ("module check report" in lowered):
        code = code or "MODULE_CHECK_EVIDENCE_FAILED"
        failure_class = "evidence_failure"
        field = "checks"
    elif "content differs from" in lowered:
        code = "EVIDENCE_COMMIT_MISMATCH"
        failure_class = "evidence_failure"
    elif "file does not exist" in lowered or ("completion report does not exist" in lowered):
        code = "EVIDENCE_FILE_MISSING"
        failure_class = "evidence_failure"
    elif "implementation_commit is not an ancestor" in lowered:
        code = "IMPLEMENTATION_COMMIT_NOT_ANCESTOR"
        failure_class = "evidence_failure"
        field = "implementation_commit"
    elif "remote branch" in lowered or "ls-remote" in lowered:
        code = "PUBLICATION_EVIDENCE_FAILED"
        failure_class = "evidence_failure"
        field = "publication"
    elif "prompt " in lowered or "roadmap " in lowered:
        code = "BLUEPRINT_CONTROL_MISMATCH"
        failure_class = "blueprint_control_failure"
        remediation_owner = "blueprint"
    elif "git " in lowered:
        code = code or "GIT_EVIDENCE_FAILED"
        failure_class = "evidence_failure"
    else:
        code = code or "UNCLASSIFIED_INTAKE_FAILURE"

    return CompletionIntakeIssue(
        code=code,
        failure_class=failure_class,
        message=message,
        field=field,
        remediation_owner=remediation_owner,
        implementation_failure_proven=implementation_failure_proven,
    )


def _failure_payload(
    error: CompletionIntakeCheckError,
) -> dict[str, Any]:
    issue = _classify_intake_error(error)
    return {
        "result": "failed",
        "status": "BLOCKED",
        "decision": None,
        "automatic_acceptance": False,
        "automatic_return": False,
        "issue": {
            "code": issue.code,
            "failure_class": issue.failure_class,
            "message": issue.message,
            "field": issue.field,
            "remediation_owner": issue.remediation_owner,
            "implementation_failure_proven": (issue.implementation_failure_proven),
        },
    }


def _success_payload(
    result: CompletionIntakeCheckResult,
) -> dict[str, Any]:
    status = (
        "REFERENCE_VALIDATION_READY" if result.candidate_reference else "READY_FOR_OPERATOR_REVIEW"
    )
    return {
        "result": "passed",
        "status": status,
        "decision": None,
        "automatic_acceptance": False,
        "automatic_return": False,
        "module_id": result.module_id,
        "prompt_id": result.prompt_id,
        "phase": result.phase,
        "packet_path": result.packet_path,
        "report_path": result.report_path,
        "implementation_commit": result.implementation_commit,
        "implementation_base_commit": result.implementation_base_commit,
        "completion_commit": result.completion_commit,
        "publication": {
            "remote": result.remote,
            "branch": result.branch,
            "remote_commit": result.remote_commit,
            "verified": result.publication_verified,
            "verification_source": "git_remote_containment",
            "packet_push_status": result.packet_push_status,
        },
        "packet_protocol": {
            "schema_version": result.schema_version,
            "protocol_version": result.protocol_version,
            "supersedes_completion_id": (result.supersedes_completion_id),
            "historical_legacy": result.historical_legacy,
        },
        "coverage": {
            "requirements": list(result.requirement_coverage),
            "required_checks": list(result.check_coverage),
            "intake_stages": list(result.intake_stages),
        },
        "candidate_reference": result.candidate_reference,
        "warnings": list(result.warnings),
    }


def _print_structured(
    payload: dict[str, Any],
    *,
    output_format: str,
) -> None:
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if output_format == "yaml":
        print(
            yaml.safe_dump(
                payload,
                sort_keys=False,
                allow_unicode=True,
            ),
            end="",
        )
        return
    raise ValueError(f"unsupported structured output format: {output_format}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=("Read-only Blueprint verification of module completion evidence.")
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--module", required=True)
    parser.add_argument("--module-root", required=True)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--completion-commit", required=True)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch")
    parser.add_argument(
        "--allow-candidate-reference",
        action="store_true",
        help=(
            "Allow read-only v0.3 candidate reference validation. This never enables acceptance."
        ),
    )
    parser.add_argument(
        "--output-format",
        choices=("text", "json", "yaml"),
        default="text",
    )
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
            allow_candidate_reference=args.allow_candidate_reference,
        )
    except CompletionIntakeCheckError as error:
        if args.output_format in STRUCTURED_OUTPUT_FORMATS:
            _print_structured(
                _failure_payload(error),
                output_format=args.output_format,
            )
        else:
            print("FAILED: completion intake check")
            print(f"- {error}")
            print("RESULT: COMPLETION_INTAKE_CHECK_FAILED")
        return 1

    if args.output_format in STRUCTURED_OUTPUT_FORMATS:
        _print_structured(
            _success_payload(result),
            output_format=args.output_format,
        )
        return 0

    print("Completion intake check")
    print(f"module: {result.module_id}")
    print(f"prompt: {result.prompt_id}")
    print(f"phase: {result.phase}")
    print(f"packet: {result.packet_path}")
    print(f"report: {result.report_path}")
    print(f"implementation commit: {result.implementation_commit}")
    print(f"completion commit: {result.completion_commit}")
    print(f"packet schema: {result.schema_version}")
    print(f"intake protocol: {result.protocol_version}")
    print(
        "operator status: "
        + (
            "REFERENCE_VALIDATION_READY"
            if result.candidate_reference
            else "READY_FOR_OPERATOR_REVIEW"
        )
    )
    if result.implementation_base_commit:
        print(f"implementation base commit: {result.implementation_base_commit}")
    if result.requirement_coverage:
        print(f"requirement coverage: {len(result.requirement_coverage)}")
    if result.check_coverage:
        print(f"required check coverage: {len(result.check_coverage)}")
    print(f"packet push status: {result.packet_push_status}")
    print(f"publication: {result.remote}/{result.branch} @ {result.remote_commit}")
    print(f"publication verified: {str(result.publication_verified).lower()}")
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
