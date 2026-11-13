from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

EVENT_SCHEMA = "module_prompt_execution_event_v0_1"
EXECUTION_IDENTITY_SCHEMA = "module_execution_identity_v0_1"
QUEUE_SCHEMA = "prompt_queue_v0_2"
EVENTS_REL = Path("coordination/prompt_execution_events/records")
REGISTRY_REL = Path("coordination/registry/coordination_source_registry_v0_1.yaml")
BLUEPRINT_MODULE = "forprint_system_blueprint"

EVENT_TYPES = {
    "CLAIMED": "claimed",
    "IN_PROGRESS": "in_progress",
    "BLOCKED": "blocked",
    "UNABLE_TO_EXECUTE": "unable_to_execute",
}
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
PROMPT_ID = re.compile(r"^[a-z0-9][a-z0-9_]*$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

ACTIVE_QUEUE_STATUSES = {
    "ready_for_module_pull",
    "in_progress",
    "blocked",
}
TERMINAL_QUEUE_STATUSES = {
    "completed_by_module",
    "superseded",
}

ALLOWED_TRANSITIONS: dict[str | None, set[str]] = {
    None: {"CLAIMED"},
    "CLAIMED": {"IN_PROGRESS", "BLOCKED", "UNABLE_TO_EXECUTE"},
    "IN_PROGRESS": {"IN_PROGRESS", "BLOCKED", "UNABLE_TO_EXECUTE"},
    "BLOCKED": {"BLOCKED", "IN_PROGRESS", "UNABLE_TO_EXECUTE"},
    "UNABLE_TO_EXECUTE": {"UNABLE_TO_EXECUTE", "IN_PROGRESS"},
}

FORBIDDEN_EVENT_KEYS = {
    "operator_decision",
    "blueprint_review",
    "completion_commit",
    "completion_report",
    "accepted_at",
    "returned_at",
    "held_at",
}


class PromptExecutionEventError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PromptExecutionEventError(
            f"cannot load YAML {path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise PromptExecutionEventError(
            f"expected YAML mapping: {path}"
        )
    return value


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _relative_or_absolute(base: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _safe_under(root: Path, relative: Path, label: str) -> Path:
    root = root.resolve()
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PromptExecutionEventError(
            f"{label} escapes repository root: {relative}"
        ) from exc
    return target


def _safe_blueprint_path(
    blueprint_root: Path,
    raw: Any,
    label: str,
) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise PromptExecutionEventError(
            f"{label} must be a non-empty Blueprint-relative path"
        )
    value = Path(raw)
    if value.is_absolute():
        raise PromptExecutionEventError(
            f"{label} must be Blueprint-relative"
        )
    return _safe_under(blueprint_root, value, label)


def _parse_occurred_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _valid_occurred_at(value: Any) -> bool:
    return _parse_occurred_at(value) is not None


def _registry_modules(registry: dict[str, Any]) -> list[dict[str, Any]]:
    modules = registry.get("modules")
    if not isinstance(modules, list):
        raise PromptExecutionEventError(
            "coordination source registry modules must be a list"
        )
    rows = [item for item in modules if isinstance(item, dict)]
    if len(rows) != len(modules):
        raise PromptExecutionEventError(
            "coordination source registry contains non-mapping module records"
        )
    return rows


def _registry_module(
    registry: dict[str, Any],
    module_id: str,
) -> dict[str, Any]:
    matches = [
        item
        for item in _registry_modules(registry)
        if item.get("module_id") == module_id
    ]
    if len(matches) != 1:
        raise PromptExecutionEventError(
            f"module_id={module_id!r}: expected one registry record, "
            f"got {len(matches)}"
        )
    return matches[0]


def _registry_is_read_only(module: dict[str, Any]) -> bool:
    boundaries = module.get("boundaries")
    return (
        isinstance(boundaries, dict)
        and boundaries.get("blueprint_lookup_mode") == "read_only"
        and boundaries.get("blueprint_may_write_repository") is False
    )


def _repository_root(module: dict[str, Any]) -> Path:
    repository = module.get("repository")
    if not isinstance(repository, dict):
        raise PromptExecutionEventError(
            "registry module repository must be a mapping"
        )
    local_path = repository.get("local_path")
    if not isinstance(local_path, str) or not local_path.strip():
        raise PromptExecutionEventError(
            "registry repository.local_path must be non-empty"
        )
    return Path(local_path).resolve()


def _queue_path(
    blueprint_root: Path,
    module: dict[str, Any],
) -> Path:
    sources = module.get("sources")
    if not isinstance(sources, dict):
        raise PromptExecutionEventError(
            "registry module sources must be a mapping"
        )
    queue = sources.get("prompt_queue")
    if not isinstance(queue, dict):
        raise PromptExecutionEventError(
            "registry module prompt_queue source is missing"
        )
    if queue.get("owner") != "forprint_system_blueprint":
        raise PromptExecutionEventError(
            "registry prompt_queue owner must be forprint_system_blueprint"
        )
    if queue.get("availability") != "present":
        raise PromptExecutionEventError(
            "registry prompt_queue must be present for execution events"
        )
    return _safe_blueprint_path(
        blueprint_root,
        queue.get("path"),
        "registry prompt_queue.path",
    )


def _queue_prompt(
    blueprint_root: Path,
    module: dict[str, Any],
    prompt_id: str,
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    queue_path = _queue_path(blueprint_root, module)
    queue = load_yaml(queue_path)
    if queue.get("schema_version") != QUEUE_SCHEMA:
        raise PromptExecutionEventError(
            f"prompt queue must use {QUEUE_SCHEMA}: {queue_path}"
        )
    module_id = module.get("module_id")
    if queue.get("module") != module_id:
        raise PromptExecutionEventError(
            "prompt queue module does not match registry module_id"
        )
    rows = queue.get("prompt_queue")
    if not isinstance(rows, list):
        raise PromptExecutionEventError(
            "prompt queue prompt_queue must be a list"
        )
    matches = [
        item
        for item in rows
        if isinstance(item, dict)
        and item.get("prompt_id") == prompt_id
    ]
    if len(matches) != 1:
        raise PromptExecutionEventError(
            f"prompt_id={prompt_id!r}: expected one queue record, "
            f"got {len(matches)}"
        )
    prompt = matches[0]
    if prompt.get("target_module") != module_id:
        raise PromptExecutionEventError(
            "queue prompt target_module does not match event module"
        )
    execution = prompt.get("module_execution")
    if not isinstance(execution, dict):
        raise PromptExecutionEventError(
            "queue prompt module_execution must be a mapping"
        )
    return queue, prompt, queue_path



def _queue_contract_binding_state(
    blueprint_root: Path,
    prompt: dict[str, Any],
    module_id: str,
    prompt_id: str,
) -> tuple[
    bool,
    dict[str, Any] | None,
    dict[str, Any] | None,
    list[str],
]:
    # Resolve queue-authoritative Prompt Contract and B1 discriminator.

    binding = prompt.get("prompt_contract")
    if binding is None:
        return False, None, None, []
    if not isinstance(binding, dict):
        return False, None, None, [
            "prompt queue prompt_contract binding must be a mapping or null"
        ]

    errors: list[str] = []
    required = (
        "schema_version",
        "contract_id",
        "path",
        "file_sha256",
        "payload_sha256",
        "source_prompt_sha256",
    )
    for key in required:
        value = binding.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"prompt queue prompt_contract.{key} missing")
    for key in (
        "file_sha256",
        "payload_sha256",
        "source_prompt_sha256",
    ):
        value = binding.get(key)
        if (
            isinstance(value, str)
            and re.fullmatch(r"[0-9a-f]{64}", value) is None
        ):
            errors.append(
                f"prompt queue prompt_contract.{key} must be lowercase SHA-256"
            )
    if (
        binding.get("schema_version")
        not in {None, "module_prompt_contract_v0_4"}
    ):
        errors.append("prompt queue Prompt Contract schema mismatch")
    if errors:
        return False, dict(binding), None, errors

    rel = binding["path"]
    contract_path = (blueprint_root / rel).resolve()
    try:
        contract_path.relative_to(blueprint_root.resolve())
    except ValueError:
        return False, dict(binding), None, [
            "prompt queue Prompt Contract path escapes Blueprint root"
        ]
    if not contract_path.is_file():
        return False, dict(binding), None, [
            "prompt queue bound Prompt Contract is unavailable"
        ]
    if file_sha256(contract_path) != binding["file_sha256"]:
        return False, dict(binding), None, [
            "prompt queue bound Prompt Contract file SHA mismatch"
        ]

    try:
        contract = load_yaml(contract_path)
    except Exception as exc:
        return False, dict(binding), None, [
            f"prompt queue bound Prompt Contract YAML invalid: {exc}"
        ]

    metadata = contract.get("metadata")
    source_prompt = contract.get("source_prompt")
    integrity = contract.get("integrity")
    if contract.get("schema_version") != "module_prompt_contract_v0_4":
        errors.append("bound Prompt Contract schema mismatch")
    if not isinstance(metadata, dict):
        errors.append("bound Prompt Contract metadata missing")
        metadata = {}
    if metadata.get("contract_id") != binding.get("contract_id"):
        errors.append("bound Prompt Contract contract_id mismatch")
    if metadata.get("module_id") != module_id:
        errors.append("bound Prompt Contract module_id mismatch")
    if metadata.get("prompt_id") != prompt_id:
        errors.append("bound Prompt Contract prompt_id mismatch")
    if not isinstance(source_prompt, dict):
        errors.append("bound Prompt Contract source_prompt missing")
        source_prompt = {}
    if source_prompt.get("sha256") != binding.get(
        "source_prompt_sha256"
    ):
        errors.append("bound Prompt Contract source prompt SHA mismatch")
    if not isinstance(integrity, dict):
        errors.append("bound Prompt Contract integrity missing")
        integrity = {}
    if integrity.get("payload_sha256") != binding.get("payload_sha256"):
        errors.append("bound Prompt Contract payload SHA mismatch")
    if errors:
        return False, dict(binding), contract, errors

    policy = contract.get("execution_baseline_policy")
    if policy is None:
        return False, dict(binding), contract, []
    if not isinstance(policy, dict):
        return False, dict(binding), contract, [
            "bound Prompt Contract execution_baseline_policy must be a mapping"
        ]
    if (
        policy.get("schema_version")
        != "module_execution_baseline_policy_v0_1"
    ):
        return False, dict(binding), contract, [
            "bound Prompt Contract execution_baseline_policy schema mismatch"
        ]
    return True, dict(binding), contract, []


def _expected_preflight_evidence_path(
    prompt_id: str,
    execution_epoch_id: str,
) -> str:
    return (
        "coordination/execution_preflight/records/"
        f"{prompt_id}__{execution_epoch_id}.yaml"
    )


def _validate_bound_preflight_evidence(
    identity: dict[str, Any],
    *,
    repository_root: Path,
    module_id: str,
    prompt_id: str,
    contract_binding: dict[str, Any],
    contract: dict[str, Any],
) -> list[str]:
    # Validate immutable module-owned B1 preflight evidence for an event.

    errors: list[str] = []
    epoch = identity.get("execution_epoch_id")
    fingerprint = identity.get("preflight_fingerprint_sha256")
    evidence = identity.get("preflight_evidence")
    if not isinstance(evidence, dict):
        return [
            "B1-bound execution_identity.preflight_evidence must be a mapping"
        ]

    path_value = evidence.get("path")
    sha_value = evidence.get("sha256")
    if not isinstance(path_value, str) or not path_value.strip():
        errors.append(
            "B1-bound execution_identity.preflight_evidence.path missing"
        )
    if (
        not isinstance(sha_value, str)
        or re.fullmatch(r"[0-9a-f]{64}", sha_value) is None
    ):
        errors.append(
            "B1-bound execution_identity.preflight_evidence.sha256 "
            "must be lowercase SHA-256"
        )
    if errors:
        return errors

    if isinstance(epoch, str):
        expected_path = _expected_preflight_evidence_path(
            prompt_id,
            epoch,
        )
        if path_value != expected_path:
            errors.append(
                "B1 preflight evidence path must be canonical for "
                "prompt_id + execution_epoch_id"
            )

    evidence_path = (repository_root / path_value).resolve()
    try:
        evidence_path.relative_to(repository_root.resolve())
    except ValueError:
        errors.append("B1 preflight evidence path escapes module repository")
        return errors
    if not evidence_path.is_file():
        errors.append("B1 preflight evidence file is unavailable")
        return errors
    if file_sha256(evidence_path) != sha_value:
        errors.append("B1 preflight evidence file SHA mismatch")
        return errors

    try:
        report = load_yaml(evidence_path)
    except Exception as exc:
        errors.append(f"B1 preflight evidence YAML invalid: {exc}")
        return errors

    if report.get("schema_version") != "blueprint_execution_preflight_v0_1":
        errors.append("B1 preflight evidence schema mismatch")
    if report.get("result") != "READY":
        errors.append("B1 preflight evidence result must be READY")

    report_contract = report.get("contract")
    if not isinstance(report_contract, dict):
        errors.append("B1 preflight evidence contract must be a mapping")
        report_contract = {}
    if report_contract.get("contract_id") != contract_binding.get(
        "contract_id"
    ):
        errors.append("B1 preflight contract_id mismatch")
    if report_contract.get("module_id") != module_id:
        errors.append("B1 preflight module_id mismatch")
    if report_contract.get("prompt_id") != prompt_id:
        errors.append("B1 preflight prompt_id mismatch")

    policy = contract.get("execution_baseline_policy")
    if not isinstance(policy, dict):
        errors.append("B1 Prompt Contract policy unavailable")
        policy = {}
    if report.get("release_baseline") != policy.get("release_baseline"):
        errors.append(
            "B1 preflight release_baseline does not match Prompt Contract"
        )
    execution_baseline = report.get("execution_baseline")
    if not isinstance(execution_baseline, dict) or not execution_baseline:
        errors.append("B1 preflight execution_baseline must be non-empty")

    report_fingerprint = report.get("preflight_fingerprint_sha256")
    if report_fingerprint != fingerprint:
        errors.append("B1 preflight fingerprint does not match CLAIM identity")

    report_identity = report.get("execution_identity")
    if not isinstance(report_identity, dict):
        errors.append("B1 preflight execution_identity must be a mapping")
        report_identity = {}
    if report_identity.get("execution_epoch_id") != epoch:
        errors.append("B1 preflight execution epoch does not match CLAIM")
    if (
        report_identity.get("claim_must_bind_preflight_fingerprint")
        is not True
    ):
        errors.append(
            "B1 preflight must require CLAIM to bind its fingerprint"
        )
    if report_identity.get("head_chasing_after_claim_allowed") is not False:
        errors.append("B1 preflight must forbid HEAD chasing after CLAIM")

    revalidation = report.get("revalidation")
    if not isinstance(revalidation, dict):
        errors.append("B1 preflight revalidation must be a mapping")

    boundaries = report.get("boundaries")
    if isinstance(boundaries, dict):
        for key in (
            "blueprint_repository_writes",
            "module_repository_writes",
            "operator_decision_created",
            "automatic_acceptance",
        ):
            if boundaries.get(key) is not False:
                errors.append(
                    f"B1 preflight boundaries.{key} must be false"
                )
    return errors


def _validate_execution_identity(
    data: dict[str, Any],
    *,
    template_mode: bool,
) -> tuple[dict[str, Any] | None, list[str]]:
    if "execution_identity" not in data:
        return None, []

    identity = data.get("execution_identity")
    if not isinstance(identity, dict):
        return None, ["execution_identity must be a mapping"]

    errors: list[str] = []
    if identity.get("schema_version") != EXECUTION_IDENTITY_SCHEMA:
        errors.append(
            "execution_identity.schema_version must be "
            + EXECUTION_IDENTITY_SCHEMA
        )

    epoch = identity.get("execution_epoch_id")
    fingerprint = identity.get("preflight_fingerprint_sha256")

    if template_mode:
        if not isinstance(epoch, str) or not epoch.strip():
            errors.append(
                "execution_identity.execution_epoch_id must be non-empty"
            )
        if not isinstance(fingerprint, str) or not fingerprint.strip():
            errors.append(
                "execution_identity.preflight_fingerprint_sha256 "
                "must be non-empty"
            )
    else:
        if not isinstance(epoch, str) or HEX64.fullmatch(epoch) is None:
            errors.append(
                "execution_identity.execution_epoch_id must be "
                "a 64-character lowercase sha256"
            )
        if (
            not isinstance(fingerprint, str)
            or HEX64.fullmatch(fingerprint) is None
        ):
            errors.append(
                "execution_identity.preflight_fingerprint_sha256 must be "
                "a 64-character lowercase sha256"
            )

    if (
        isinstance(epoch, str)
        and isinstance(fingerprint, str)
        and epoch != fingerprint
    ):
        errors.append(
            "execution_identity.execution_epoch_id must equal "
            "preflight_fingerprint_sha256"
        )

    evidence = identity.get("preflight_evidence")
    if evidence is not None:
        if not isinstance(evidence, dict):
            errors.append(
                "execution_identity.preflight_evidence must be a mapping"
            )
        else:
            path_value = evidence.get("path")
            sha_value = evidence.get("sha256")
            if not isinstance(path_value, str) or not path_value.strip():
                errors.append(
                    "execution_identity.preflight_evidence.path missing"
                )
            if not isinstance(sha_value, str) or not sha_value.strip():
                errors.append(
                    "execution_identity.preflight_evidence.sha256 missing"
                )
            elif (
                not template_mode
                and re.fullmatch(r"[0-9a-f]{64}", sha_value) is None
            ):
                errors.append(
                    "execution_identity.preflight_evidence.sha256 must be "
                    "a 64-character lowercase sha256"
                )

    return dict(identity), errors


def _execution_identity_transition_errors(
    records: list[dict[str, Any]],
) -> list[str]:
    if not records:
        return []

    errors: list[str] = []
    first = records[0].get("execution_identity")

    if first is None:
        for record in records[1:]:
            if record.get("execution_identity") is not None:
                errors.append(
                    "execution identity cannot be introduced after "
                    f"historical CLAIMED event at {record.get('event_id')}"
                )
        return errors

    if not isinstance(first, dict):
        return ["CLAIMED execution_identity projection is invalid"]

    expected_epoch = first.get("execution_epoch_id")
    expected_fingerprint = first.get("preflight_fingerprint_sha256")
    expected_evidence = first.get("preflight_evidence")

    for record in records[1:]:
        event_id = record.get("event_id")
        identity = record.get("execution_identity")
        if identity is None:
            errors.append(
                "B1-bound execution event is missing execution_identity "
                f"at {event_id}"
            )
            continue
        if not isinstance(identity, dict):
            errors.append(
                f"B1-bound execution_identity is invalid at {event_id}"
            )
            continue
        if (
            identity.get("execution_epoch_id") != expected_epoch
            or identity.get("preflight_fingerprint_sha256")
            != expected_fingerprint
        ):
            errors.append(
                "B1 execution identity changed after CLAIMED "
                f"at {event_id}"
            )
        if identity.get("preflight_evidence") != expected_evidence:
            errors.append(
                "B1 preflight evidence binding changed after CLAIMED "
                f"at {event_id}"
            )

    return errors


def _validate_boundaries(data: dict[str, Any]) -> list[str]:
    boundaries = data.get("boundaries")
    if not isinstance(boundaries, dict):
        return ["boundaries must be a mapping"]

    errors: list[str] = []
    required_false = (
        "blueprint_repository_write_performed",
        "operator_decision_created",
        "completion_claimed",
        "acceptance_claimed",
        "return_or_hold_claimed",
    )
    for field in required_false:
        if boundaries.get(field) is not False:
            errors.append(
                f"boundaries.{field} must be false"
            )
    return errors


def validate_event(
    event_path: Path,
    *,
    blueprint_root: Path,
    repository_root: Path | None = None,
    registry_path: Path | None = None,
    template_mode: bool = False,
) -> dict[str, Any]:
    blueprint_root = blueprint_root.resolve()
    event_path = event_path.resolve()
    data = load_yaml(event_path)
    errors: list[str] = []

    if data.get("schema_version") != EVENT_SCHEMA:
        errors.append(f"schema_version must be {EVENT_SCHEMA}")

    event_id = data.get("event_id")
    if (
        not isinstance(event_id, str)
        or not event_id
        or SAFE_ID.fullmatch(event_id) is None
    ):
        errors.append("event_id must be a safe non-empty id")

    module_id = data.get("module_id")
    if (
        not isinstance(module_id, str)
        or not module_id
        or SAFE_ID.fullmatch(module_id) is None
    ):
        errors.append("module_id must be a safe non-empty id")

    prompt_id = data.get("prompt_id")
    if (
        not isinstance(prompt_id, str)
        or PROMPT_ID.fullmatch(prompt_id) is None
    ):
        errors.append("prompt_id must be a canonical lowercase prompt id")

    sequence = data.get("sequence")
    if not isinstance(sequence, int) or sequence < 1:
        errors.append("sequence must be a positive integer")

    event_type = data.get("event_type")
    if event_type not in EVENT_TYPES:
        errors.append(
            f"event_type must be one of {sorted(EVENT_TYPES)}"
        )

    if not _valid_occurred_at(data.get("occurred_at")):
        errors.append(
            "occurred_at must be an ISO timestamp with timezone"
        )

    if data.get("immutable") is not True:
        errors.append("immutable must be true")

    forbidden = sorted(FORBIDDEN_EVENT_KEYS.intersection(data))
    if forbidden:
        errors.append(
            "execution event contains forbidden decision/completion fields: "
            + ",".join(forbidden)
        )

    execution = data.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution must be a mapping")
        execution = {}

    reason = execution.get("reason")
    reason_code = execution.get("reason_code")
    blocking_refs = execution.get("blocking_refs", [])

    if event_type in {"BLOCKED", "UNABLE_TO_EXECUTE"}:
        if not isinstance(reason, str) or not reason.strip():
            errors.append(
                f"{event_type} requires execution.reason"
            )
        if (
            not isinstance(reason_code, str)
            or not reason_code.strip()
            or SAFE_ID.fullmatch(reason_code) is None
        ):
            errors.append(
                f"{event_type} requires safe execution.reason_code"
            )
    elif reason_code is not None and (
        not isinstance(reason_code, str)
        or not reason_code.strip()
        or SAFE_ID.fullmatch(reason_code) is None
    ):
        errors.append(
            "execution.reason_code must be null or a safe non-empty id"
        )

    if not isinstance(blocking_refs, list) or any(
        not isinstance(item, str) or not item.strip()
        for item in blocking_refs
    ):
        errors.append(
            "execution.blocking_refs must be a list of non-empty strings"
        )
    elif len(blocking_refs) != len(set(blocking_refs)):
        errors.append("execution.blocking_refs contains duplicates")

    execution_identity, identity_errors = _validate_execution_identity(
        data,
        template_mode=template_mode,
    )
    errors.extend(identity_errors)
    errors.extend(_validate_boundaries(data))

    queue_status: str | None = None
    queue_review_status: str | None = None
    queue_path_text: str | None = None

    if not template_mode and not errors:
        if repository_root is None:
            errors.append(
                "repository_root is required outside template mode"
            )
        else:
            repository_root = repository_root.resolve()
            try:
                relative_event = event_path.relative_to(repository_root)
            except ValueError:
                errors.append(
                    "event path must be inside the module repository"
                )
            else:
                try:
                    relative_event.relative_to(EVENTS_REL)
                except ValueError:
                    errors.append(
                        f"event must stay under {EVENTS_REL.as_posix()}/"
                    )
                if isinstance(event_id, str):
                    expected_name = f"{event_id}.yaml"
                    if event_path.name != expected_name:
                        errors.append(
                            "event filename must equal event_id + '.yaml'"
                        )

            if registry_path is None:
                registry_path = blueprint_root / REGISTRY_REL
            registry = load_yaml(registry_path.resolve())
            if isinstance(module_id, str):
                try:
                    module = _registry_module(registry, module_id)
                    if not _registry_is_read_only(module):
                        errors.append(
                            "registry module must preserve read-only "
                            "Blueprint lookup boundaries"
                        )
                    registered_root = _repository_root(module)
                    if registered_root != repository_root:
                        errors.append(
                            "repository_root does not match registry local_path"
                        )
                    _, prompt, queue_path = _queue_prompt(
                        blueprint_root,
                        module,
                        str(prompt_id),
                    )
                    (
                        b1_required,
                        queue_contract_binding,
                        queue_contract,
                        queue_contract_errors,
                    ) = _queue_contract_binding_state(
                        blueprint_root,
                        prompt,
                        module_id,
                        str(prompt_id),
                    )
                    errors.extend(queue_contract_errors)
                    if b1_required:
                        if execution_identity is None:
                            errors.append(
                                "B1-bound Prompt Contract requires "
                                "execution_identity on every execution event"
                            )
                        elif (
                            queue_contract_binding is not None
                            and queue_contract is not None
                        ):
                            errors.extend(
                                _validate_bound_preflight_evidence(
                                    execution_identity,
                                    repository_root=repository_root,
                                    module_id=module_id,
                                    prompt_id=str(prompt_id),
                                    contract_binding=queue_contract_binding,
                                    contract=queue_contract,
                                )
                            )
                    module_execution = prompt.get("module_execution")
                    blueprint_review = prompt.get("blueprint_review")
                    if isinstance(module_execution, dict):
                        queue_status = module_execution.get("status")
                    if isinstance(blueprint_review, dict):
                        queue_review_status = blueprint_review.get("status")
                    queue_path_text = _relative_or_absolute(
                        blueprint_root,
                        queue_path,
                    )
                except PromptExecutionEventError as exc:
                    errors.append(str(exc))

    result = {
        "schema_version": "blueprint_prompt_execution_event_validation_v0_1",
        "result": "PASSED" if not errors else "FAILED",
        "event_path": (
            _relative_or_absolute(
                repository_root or blueprint_root,
                event_path,
            )
        ),
        "event_sha256": file_sha256(event_path),
        "event_id": event_id,
        "module_id": module_id,
        "prompt_id": prompt_id,
        "sequence": sequence,
        "event_type": event_type,
        "observed_status": EVENT_TYPES.get(str(event_type)),
        "occurred_at": data.get("occurred_at"),
        "execution_identity": execution_identity,
        "queue_status_current": queue_status,
        "blueprint_review_status_current": queue_review_status,
        "prompt_queue_path": queue_path_text,
        "errors": errors,
        "boundaries": {
            "module_repository_writes": False,
            "blueprint_repository_writes": False,
            "operator_decision_created": False,
            "automatic_acceptance": False,
            "automatic_return": False,
            "automatic_hold": False,
            "completion_claimed": False,
        },
    }
    return result


def _transition_errors(
    records: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = _execution_identity_transition_errors(records)
    previous_type: str | None = None
    previous_time: datetime | None = None
    expected_sequence = 1
    seen_sequences: set[int] = set()

    for record in records:
        sequence = record.get("sequence")
        event_type = record.get("event_type")
        event_id = record.get("event_id")

        if not isinstance(sequence, int):
            continue
        if sequence in seen_sequences:
            errors.append(f"duplicate execution event sequence {sequence}")
            continue
        seen_sequences.add(sequence)

        if sequence != expected_sequence:
            errors.append(
                "non-contiguous execution event sequence: "
                f"expected {expected_sequence}, got {sequence} at {event_id}"
            )
        expected_sequence = sequence + 1

        current_time = _parse_occurred_at(record.get("occurred_at"))
        if current_time is not None:
            if previous_time is not None and current_time < previous_time:
                errors.append(
                    f"execution event occurred_at moved backwards at {event_id}"
                )
            previous_time = current_time

        allowed = ALLOWED_TRANSITIONS.get(previous_type, set())
        if event_type not in allowed:
            errors.append(
                f"invalid execution transition {previous_type or 'START'}"
                f"->{event_type} at {event_id}"
            )
        previous_type = str(event_type)

    return errors


def _projection_classification(queue_status: Any) -> str:
    if queue_status in ACTIVE_QUEUE_STATUSES:
        return "CURRENT_EXECUTION_OBSERVATION"
    if queue_status in TERMINAL_QUEUE_STATUSES:
        return "HISTORICAL_EXECUTION_OBSERVATION"
    return "QUEUE_STATE_REQUIRES_REVIEW"


def discover_execution_events(
    *,
    blueprint_root: Path,
    registry_path: Path | None = None,
    module_filter: set[str] | None = None,
) -> dict[str, Any]:
    blueprint_root = blueprint_root.resolve()
    registry_path = (
        registry_path.resolve()
        if registry_path is not None
        else (blueprint_root / REGISTRY_REL).resolve()
    )
    registry = load_yaml(registry_path)

    source_states: dict[str, str] = {}
    source_errors: list[str] = []
    event_records: list[dict[str, Any]] = []
    invalid_records: list[dict[str, Any]] = []

    modules = _registry_modules(registry)
    if module_filter is not None:
        registered_ids = {
            str(item.get("module_id"))
            for item in modules
            if isinstance(item.get("module_id"), str)
        }
        for module_id in sorted(module_filter - registered_ids):
            source_errors.append(
                f"unknown module filter: {module_id}"
            )
        modules = [
            item
            for item in modules
            if item.get("module_id") in module_filter
        ]

    for module in modules:
        module_id = module.get("module_id")
        if not isinstance(module_id, str):
            continue

        if module_id == BLUEPRINT_MODULE:
            source_states[module_id] = "self_module_not_applicable"
            continue

        if not _registry_is_read_only(module):
            source_states[module_id] = "invalid_source"
            source_errors.append(
                f"{module_id}: registry does not preserve read-only "
                "Blueprint lookup boundaries"
            )
            continue

        try:
            repository_root = _repository_root(module)
        except PromptExecutionEventError as exc:
            source_errors.append(
                f"{module_id}: {exc}"
            )
            continue

        if not repository_root.is_dir():
            source_states[module_id] = "repository_not_present"
            continue

        events_dir = _safe_under(
            repository_root,
            EVENTS_REL,
            "execution event directory",
        )
        if not events_dir.exists():
            source_states[module_id] = "not_present_yet"
            continue
        if not events_dir.is_dir():
            source_states[module_id] = "invalid_source"
            source_errors.append(
                f"{module_id}: execution event path is not a directory"
            )
            continue

        source_states[module_id] = "present"
        for event_path in sorted(events_dir.glob("*.yaml")):
            report = validate_event(
                event_path,
                blueprint_root=blueprint_root,
                repository_root=repository_root,
                registry_path=registry_path,
                template_mode=False,
            )
            record = dict(report)
            record["repository_root"] = str(repository_root)
            if report["result"] == "PASSED":
                event_records.append(record)
            else:
                invalid_records.append(record)

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in event_records:
        key = (
            str(record["module_id"]),
            str(record["prompt_id"]),
        )
        grouped.setdefault(key, []).append(record)

    projections: list[dict[str, Any]] = []
    transition_errors: list[str] = []
    queue_state_errors: list[str] = []

    for (module_id, prompt_id), records in sorted(grouped.items()):
        records.sort(
            key=lambda item: (
                int(item.get("sequence") or 0),
                str(item.get("occurred_at") or ""),
                str(item.get("event_id") or ""),
            )
        )
        errors = _transition_errors(records)
        if errors:
            transition_errors.extend(
                f"{module_id}/{prompt_id}: {error}"
                for error in errors
            )
            continue

        latest = records[-1]
        classification = _projection_classification(
            latest.get("queue_status_current")
        )
        if classification == "QUEUE_STATE_REQUIRES_REVIEW":
            queue_state_errors.append(
                f"{module_id}/{prompt_id}: observed execution event "
                f"cannot be current while queue status is "
                f"{latest.get('queue_status_current')!r}"
            )
        projections.append(
            {
                "module_id": module_id,
                "prompt_id": prompt_id,
                "queue_recorded_status": latest.get(
                    "queue_status_current"
                ),
                "blueprint_review_status": latest.get(
                    "blueprint_review_status_current"
                ),
                "observed_status": latest.get("observed_status"),
                "event_type": latest.get("event_type"),
                "event_id": latest.get("event_id"),
                "event_sequence": latest.get("sequence"),
                "event_path": latest.get("event_path"),
                "event_sha256": latest.get("event_sha256"),
                "occurred_at": latest.get("occurred_at"),
                "execution_identity": latest.get(
                    "execution_identity"
                ),
                "classification": classification,
            }
        )

    active_by_module: dict[str, list[str]] = {}
    for item in projections:
        if item["classification"] != "CURRENT_EXECUTION_OBSERVATION":
            continue
        active_by_module.setdefault(
            str(item["module_id"]),
            [],
        ).append(str(item["prompt_id"]))

    wip_errors = [
        (
            f"{module_id}: multiple current execution observations: "
            + ",".join(sorted(prompt_ids))
        )
        for module_id, prompt_ids in sorted(active_by_module.items())
        if len(set(prompt_ids)) > 1
    ]

    attention = bool(
        invalid_records
        or transition_errors
        or queue_state_errors
        or source_errors
        or wip_errors
    )
    if attention:
        result_state = "ATTENTION_REQUIRED"
    elif projections:
        result_state = "EXECUTION_OBSERVATIONS_AVAILABLE"
    else:
        result_state = "NO_EXECUTION_EVENTS_AVAILABLE"

    payload: dict[str, Any] = {
        "schema_version": "blueprint_prompt_execution_event_discovery_v0_1",
        "mode": "local_read_only",
        "network_independent": True,
        "result_state": result_state,
        "source_path": EVENTS_REL.as_posix(),
        "source_states": source_states,
        "summary": {
            "registered_modules_scanned": len(modules),
            "events_discovered": len(event_records) + len(invalid_records),
            "valid_events": len(event_records),
            "invalid_events": len(invalid_records),
            "current_projections": sum(
                1
                for item in projections
                if item["classification"]
                == "CURRENT_EXECUTION_OBSERVATION"
            ),
            "historical_projections": sum(
                1
                for item in projections
                if item["classification"]
                == "HISTORICAL_EXECUTION_OBSERVATION"
            ),
            "source_errors": len(source_errors),
            "repository_not_present": sum(
                1
                for state in source_states.values()
                if state == "repository_not_present"
            ),
            "event_source_not_present_yet": sum(
                1
                for state in source_states.values()
                if state == "not_present_yet"
            ),
            "self_module_not_applicable": sum(
                1
                for state in source_states.values()
                if state == "self_module_not_applicable"
            ),
            "transition_errors": len(transition_errors),
            "queue_state_errors": len(queue_state_errors),
            "wip_errors": len(wip_errors),
        },
        "projections": projections,
        "invalid_events": invalid_records,
        "source_errors": source_errors,
        "transition_errors": transition_errors,
        "queue_state_errors": queue_state_errors,
        "wip_errors": wip_errors,
        "governance": {
            "queue_mutated": False,
            "roadmap_mutated": False,
            "module_repository_writes": False,
            "operator_decision_created": False,
            "automatic_acceptance": False,
            "automatic_return": False,
            "automatic_hold": False,
            "completion_claimed": False,
            "next_prompt_selection_performed": False,
            "next_prompt_activation_performed": False,
            "automatic_commit": False,
            "automatic_push": False,
        },
    }
    fingerprint_payload = dict(payload)
    fingerprint_payload.pop("schema_version", None)
    payload["discovery_fingerprint_sha256"] = canonical_sha256(
        fingerprint_payload
    )
    return payload


def render_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "ForPrint Prompt Execution Events v0.1",
        f"result_state: {report['result_state']}",
        f"mode: {report['mode']}",
        "network_independent: true",
        "",
        "SUMMARY",
        f"events_discovered: {summary['events_discovered']}",
        f"valid_events: {summary['valid_events']}",
        f"invalid_events: {summary['invalid_events']}",
        f"current_projections: {summary['current_projections']}",
        f"historical_projections: {summary['historical_projections']}",
        "",
        "OBSERVED EXECUTION",
    ]
    if report["projections"]:
        for item in report["projections"]:
            lines.append(
                "  "
                f"{item['module_id']} / {item['prompt_id']}: "
                f"queue={item['queue_recorded_status']} "
                f"observed={item['observed_status']} "
                f"event={item['event_id']} "
                f"class={item['classification']}"
            )
    else:
        lines.append("  -")

    lines.extend(
        [
            "",
            "ATTENTION",
            "source_errors: "
            + (
                "; ".join(report["source_errors"])
                if report["source_errors"]
                else "-"
            ),
            "transition_errors: "
            + (
                "; ".join(report["transition_errors"])
                if report["transition_errors"]
                else "-"
            ),
            "queue_state_errors: "
            + (
                "; ".join(report["queue_state_errors"])
                if report["queue_state_errors"]
                else "-"
            ),
            "wip_errors: "
            + (
                "; ".join(report["wip_errors"])
                if report["wip_errors"]
                else "-"
            ),
            "",
            "BOUNDARIES",
            "queue_mutated: false",
            "roadmap_mutated: false",
            "module_repository_writes: false",
            "operator_decision_created: false",
            "automatic_acceptance: false",
            "automatic_return: false",
            "automatic_hold: false",
            "completion_claimed: false",
        ]
    )
    return "\n".join(lines)


def _main_validate(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    event = args.event
    if not event.is_absolute():
        if args.template:
            event = (root / event).resolve()
        else:
            repository_root = args.module_root.resolve()
            event = (repository_root / event).resolve()

    repository_root = None
    if not args.template:
        repository_root = args.module_root.resolve()

    registry = args.registry
    if not registry.is_absolute():
        registry = (root / registry).resolve()

    report = validate_event(
        event,
        blueprint_root=root,
        repository_root=repository_root,
        registry_path=registry,
        template_mode=args.template,
    )
    print(
        yaml.safe_dump(
            report,
            sort_keys=False,
            allow_unicode=True,
        ).rstrip()
    )
    return 0 if report["result"] == "PASSED" else 1


def _main_discover(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    registry = args.registry
    if not registry.is_absolute():
        registry = (root / registry).resolve()

    module_filter = {args.module} if args.module else None
    report = discover_execution_events(
        blueprint_root=root,
        registry_path=registry,
        module_filter=module_filter,
    )
    if args.output_format == "yaml":
        print(
            yaml.safe_dump(
                report,
                sort_keys=False,
                allow_unicode=True,
            ).rstrip()
        )
    elif args.output_format == "json":
        print(
            json.dumps(
                report,
                sort_keys=True,
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(render_text(report))
    return 1 if report["result_state"] == "ATTENTION_REQUIRED" else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--root", type=Path, default=Path("."))
    validate_parser.add_argument(
        "--registry",
        type=Path,
        default=REGISTRY_REL,
    )
    validate_parser.add_argument(
        "--module-root",
        type=Path,
        default=Path("."),
    )
    validate_parser.add_argument("--event", type=Path, required=True)
    validate_parser.add_argument("--template", action="store_true")
    validate_parser.set_defaults(handler=_main_validate)

    discover_parser = subparsers.add_parser("discover")
    discover_parser.add_argument("--root", type=Path, default=Path("."))
    discover_parser.add_argument(
        "--registry",
        type=Path,
        default=REGISTRY_REL,
    )
    discover_parser.add_argument("--module")
    discover_parser.add_argument(
        "--output-format",
        choices=("text", "yaml", "json"),
        default="text",
    )
    discover_parser.set_defaults(handler=_main_discover)

    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
