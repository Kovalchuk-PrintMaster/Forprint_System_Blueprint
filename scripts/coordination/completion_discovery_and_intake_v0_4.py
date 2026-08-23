from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

OUTBOX_REL = Path("coordination/completion_outbox/records")
PACKET_REL = Path("coordination/completion_packets/records")
OUTBOX_SCHEMA = "module_completion_outbox_event_v0_4"
PACKET_SCHEMA = "module_completion_packet_v0_4"
DECISION_SCHEMA = "blueprint_operator_review_decision_v0_4"

OutboxValidator = Callable[[Path, Path, Path], dict[str, Any]]
PacketValidator = Callable[[Path, Path], dict[str, Any]]


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return data


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


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _default_outbox_validator(
    event_path: Path,
    blueprint_root: Path,
    repository_root: Path,
    registry_path: Path,
) -> dict[str, Any]:
    validator_path = (
        blueprint_root
        / "scripts/coordination/validate_completion_outbox_v0_4.py"
    )
    module = _load_module(
        validator_path,
        "forprint_completion_outbox_v0_4_validator",
    )
    return module.validate_outbox_event(
        event_path,
        root=repository_root,
        registry_path=registry_path,
        template_mode=False,
    )


def _default_packet_validator(
    packet_path: Path,
    blueprint_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    validator_path = (
        blueprint_root
        / "scripts/coordination/validate_completion_packet_v0_4.py"
    )
    module = _load_module(
        validator_path,
        "forprint_completion_packet_v0_4_validator",
    )
    return module.validate_packet(
        repository_root,
        packet_path,
        template_mode=False,
    )


def _safe_repository_path(repository_root: Path, relative: Path) -> Path:
    root = repository_root.resolve()
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"registered completion path escapes repository: {relative}"
        ) from exc
    return target


def _registered_modules(registry: dict[str, Any]) -> list[dict[str, Any]]:
    modules = registry.get("modules")
    if not isinstance(modules, list):
        raise ValueError("registry.modules must be a list")
    rows = [item for item in modules if isinstance(item, dict)]
    if len(rows) != len(modules):
        raise ValueError("registry.modules contains a non-mapping record")
    return rows


def _repository_root(
    module: dict[str, Any],
    overrides: dict[str, Path] | None,
) -> Path:
    module_id = module.get("module_id")
    if not isinstance(module_id, str) or not module_id:
        raise ValueError("registered module_id must be non-empty")
    if overrides and module_id in overrides:
        return overrides[module_id].resolve()

    repository = module.get("repository")
    if not isinstance(repository, dict):
        raise ValueError(f"{module_id}: repository must be a mapping")
    local_path = repository.get("local_path")
    if not isinstance(local_path, str) or not local_path:
        raise ValueError(f"{module_id}: repository.local_path missing")
    return Path(local_path).resolve()


def _event_identity(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event.get("event_id"),
        "module_id": event.get("module_id"),
        "repository_id": event.get("repository_id"),
        "prompt_id": event.get("prompt_id"),
        "completion_id": event.get("completion_id"),
        "emitted_at": event.get("emitted_at"),
    }


def _packet_path_from_event(
    event: dict[str, Any],
    repository_root: Path,
) -> Path | None:
    completion = event.get("completion_packet")
    if not isinstance(completion, dict):
        return None
    value = completion.get("path")
    if not isinstance(value, str) or not value:
        return None
    try:
        relative = Path(value)
        return _safe_repository_path(repository_root, relative)
    except ValueError:
        return None


def _queue_prompt_contract_binding(
    blueprint_root: Path,
    module_id: str,
    prompt_id: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    # Read queue-authoritative contract binding without mutating Blueprint.

    queue_path = (
        blueprint_root
        / "coordination"
        / "outgoing_prompts"
        / module_id
        / "index.yaml"
    )
    if not queue_path.is_file():
        return None, []

    try:
        queue = load_yaml(queue_path)
    except Exception as exc:
        return None, [f"Prompt Queue YAML invalid during intake: {exc}"]
    if queue.get("schema_version") != "prompt_queue_v0_2":
        return None, ["Prompt Queue schema mismatch during intake"]
    if queue.get("module") != module_id:
        return None, ["Prompt Queue module mismatch during intake"]

    rows = queue.get("prompt_queue")
    if not isinstance(rows, list):
        return None, ["Prompt Queue prompt_queue must be a list during intake"]
    matches = [
        item
        for item in rows
        if isinstance(item, dict)
        and item.get("prompt_id") == prompt_id
    ]
    if not matches:
        return None, []
    if len(matches) != 1:
        return None, [
            f"Prompt Queue has {len(matches)} rows for prompt_id={prompt_id!r}"
        ]

    binding = matches[0].get("prompt_contract")
    if binding is None:
        return None, []
    if not isinstance(binding, dict):
        return None, [
            "Prompt Queue prompt_contract binding must be a mapping or null"
        ]
    return dict(binding), []


def _packet_queue_contract_errors(
    packet_contract: Any,
    queue_binding: dict[str, Any],
) -> list[str]:
    if not isinstance(packet_contract, dict):
        return [
            "Completion Packet prompt_contract cannot be compared to "
            "queue-authoritative binding"
        ]

    errors: list[str] = []
    for key in (
        "schema_version",
        "contract_id",
        "path",
        "file_sha256",
        "payload_sha256",
        "source_prompt_sha256",
    ):
        if packet_contract.get(key) != queue_binding.get(key):
            errors.append(
                "Completion Packet Prompt Contract does not match "
                f"queue-authoritative binding: {key}"
            )
    return errors


def _b1_completion_claim_binding_errors(
    *,
    blueprint_root: Path,
    registry_path: Path,
    repository_root: Path,
    module_id: str,
    prompt_id: str,
    packet: dict[str, Any],
    queue_binding: dict[str, Any],
) -> list[str]:
    # Bind B1 completion provenance to the actual validated CLAIM chain.
    event_tool = _load_module(
        blueprint_root
        / "scripts/coordination/prompt_execution_events_v0_1.py",
        "forprint_prompt_execution_events_v0_1_for_completion_intake",
    )

    (
        b1_required,
        _observed_binding,
        _contract,
        binding_errors,
    ) = event_tool._queue_contract_binding_state(
        blueprint_root,
        {"prompt_contract": queue_binding},
        module_id,
        prompt_id,
    )
    if binding_errors:
        return [
            "B1 queue Prompt Contract cannot authorize completion: " + item
            for item in binding_errors
        ]
    if not b1_required:
        return []

    provenance = packet.get("completion_provenance")
    if not isinstance(provenance, dict):
        return [
            "B1 completion requires provenance before CLAIM binding comparison"
        ]

    completion_identity = provenance.get("execution_identity")
    completion_evidence = provenance.get("preflight_evidence")
    if not isinstance(completion_identity, dict):
        return [
            "B1 completion provenance execution_identity unavailable for "
            "CLAIM binding comparison"
        ]
    if not isinstance(completion_evidence, dict):
        return [
            "B1 completion provenance preflight_evidence unavailable for "
            "CLAIM binding comparison"
        ]

    events_rel = getattr(
        event_tool,
        "EVENTS_REL",
        Path("coordination/prompt_execution_events/records"),
    )
    events_dir = _safe_repository_path(
        repository_root,
        Path(events_rel),
    )
    if not events_dir.is_dir():
        return [
            "B1 completion requires module-owned execution events with a "
            "validated CLAIM"
        ]

    subject_records: list[dict[str, Any]] = []
    errors: list[str] = []

    for event_path in sorted(events_dir.glob("*.yaml")):
        if not event_path.is_file():
            continue
        try:
            raw = load_yaml(event_path)
        except Exception:
            continue

        if (
            raw.get("module_id") != module_id
            or raw.get("prompt_id") != prompt_id
        ):
            continue

        report = event_tool.validate_event(
            event_path,
            blueprint_root=blueprint_root,
            repository_root=repository_root,
            registry_path=registry_path,
            template_mode=False,
        )
        if report.get("result") != "PASSED":
            details = "; ".join(
                str(item) for item in report.get("errors", [])
            )
            relative = event_path.relative_to(repository_root).as_posix()
            errors.append(
                "B1 completion subject execution event is invalid: "
                + relative
                + (f": {details}" if details else "")
            )
            continue

        subject_records.append(dict(report))

    if errors:
        return errors
    if not subject_records:
        return [
            "B1 completion requires a validated CLAIM execution event for "
            f"{module_id}/{prompt_id}"
        ]

    subject_records.sort(
        key=lambda item: (
            int(item.get("sequence") or 0),
            str(item.get("occurred_at") or ""),
            str(item.get("event_id") or ""),
        )
    )
    transition_errors = event_tool._transition_errors(subject_records)
    if transition_errors:
        return [
            "B1 completion execution chain invalid: " + str(item)
            for item in transition_errors
        ]

    claim = subject_records[0]
    if claim.get("event_type") != "CLAIMED" or claim.get("sequence") != 1:
        return ["B1 completion execution chain does not start with CLAIMED"]

    claim_identity = claim.get("execution_identity")
    if not isinstance(claim_identity, dict):
        return ["B1 validated CLAIM execution_identity is unavailable"]

    for key in (
        "execution_epoch_id",
        "preflight_fingerprint_sha256",
    ):
        if completion_identity.get(key) != claim_identity.get(key):
            errors.append(
                "B1 completion execution identity does not match CLAIM: "
                + key
            )

    if completion_evidence != claim_identity.get("preflight_evidence"):
        errors.append(
            "B1 completion preflight evidence path/SHA does not match CLAIM"
        )

    return errors


def _discover_module(
    *,
    module: dict[str, Any],
    blueprint_root: Path,
    registry_path: Path,
    repository_root: Path,
    outbox_validator: Callable[..., dict[str, Any]],
    packet_validator: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    module_id = module.get("module_id")
    repository = module.get("repository", {})
    repository_id = (
        repository.get("repository_id")
        if isinstance(repository, dict)
        else None
    )
    source = module.get("sources", {}).get("completion_outbox", {})
    registered_availability = (
        source.get("availability")
        if isinstance(source, dict)
        else None
    )
    registered_path = (
        source.get("path")
        if isinstance(source, dict)
        else None
    )

    result: dict[str, Any] = {
        "module_id": module_id,
        "repository_id": repository_id,
        "registry_availability": registered_availability,
        "registered_outbox_path": registered_path,
        "observed_source_state": "unknown",
        "events": [],
        "warnings": [],
        "errors": [],
    }

    if not repository_root.is_dir():
        result["observed_source_state"] = "repository_unavailable"
        result["warnings"].append("registered repository local_path is unavailable")
        return result

    if registered_path != OUTBOX_REL.as_posix():
        result["observed_source_state"] = "registry_locator_invalid"
        result["errors"].append("registered outbox path is not canonical")
        return result

    outbox_dir = _safe_repository_path(repository_root, OUTBOX_REL)
    if not outbox_dir.exists():
        result["observed_source_state"] = "not_present_yet"
        if registered_availability not in {"not_present_yet", "present"}:
            result["warnings"].append(
                "registry availability is neither not_present_yet nor present"
            )
        return result

    if not outbox_dir.is_dir():
        result["observed_source_state"] = "invalid_source"
        result["errors"].append("registered outbox path exists but is not a directory")
        return result

    event_files = sorted(
        path
        for path in outbox_dir.glob("*.yaml")
        if path.is_file()
    )
    result["observed_source_state"] = (
        "present_empty" if not event_files else "present"
    )

    seen_event_ids: set[str] = set()
    for event_path in event_files:
        event_record: dict[str, Any] = {
            "path": str(event_path.relative_to(repository_root)),
            "event_sha256": file_sha256(event_path),
            "classification": "invalid_outbox_event",
            "outbox_validation": None,
            "packet_validation": None,
        }

        try:
            event = load_yaml(event_path)
        except Exception as exc:
            event_record["identity"] = {}
            event_record["outbox_validation"] = {
                "result": "FAILED",
                "errors": [f"cannot load event: {exc}"],
                "warnings": [],
            }
            result["events"].append(event_record)
            continue

        event_record["identity"] = _event_identity(event)
        event_id = event.get("event_id")
        if isinstance(event_id, str) and event_id:
            if event_id in seen_event_ids:
                event_record["outbox_validation"] = {
                    "result": "FAILED",
                    "errors": ["duplicate event_id in discovered outbox"],
                    "warnings": [],
                }
                result["events"].append(event_record)
                continue
            seen_event_ids.add(event_id)

        outbox_report = outbox_validator(
            event_path,
            blueprint_root,
            repository_root,
            registry_path,
        )
        event_record["outbox_validation"] = copy.deepcopy(outbox_report)
        if outbox_report.get("result") != "PASSED":
            result["events"].append(event_record)
            continue

        if event.get("schema_version") != OUTBOX_SCHEMA:
            event_record["outbox_validation"] = {
                "result": "FAILED",
                "errors": ["outbox schema mismatch after validation"],
                "warnings": [],
            }
            result["events"].append(event_record)
            continue

        packet_path = _packet_path_from_event(event, repository_root)
        if packet_path is None or not packet_path.is_file():
            event_record["classification"] = "invalid_completion_packet"
            event_record["packet_validation"] = {
                "result": "FAILED",
                "errors": ["bound Completion Packet v0.4 path is unavailable"],
                "warnings": [],
            }
            result["events"].append(event_record)
            continue

        packet_report = packet_validator(
            packet_path,
            blueprint_root,
            repository_root,
        )
        event_record["packet_path"] = str(
            packet_path.relative_to(repository_root)
        )
        event_record["packet_sha256"] = file_sha256(packet_path)
        event_record["packet_validation"] = copy.deepcopy(packet_report)
        if packet_report.get("result") != "PASSED":
            event_record["classification"] = "invalid_completion_packet"
            result["events"].append(event_record)
            continue

        try:
            packet = load_yaml(packet_path)
        except Exception as exc:
            event_record["classification"] = "invalid_completion_packet"
            event_record["packet_validation"] = {
                "result": "FAILED",
                "errors": [f"cannot load packet after validation: {exc}"],
                "warnings": [],
            }
            result["events"].append(event_record)
            continue

        if packet.get("schema_version") != PACKET_SCHEMA:
            event_record["classification"] = "invalid_completion_packet"
            event_record["packet_validation"] = {
                "result": "FAILED",
                "errors": ["Completion Packet v0.4 schema mismatch"],
                "warnings": [],
            }
            result["events"].append(event_record)
            continue

        packet_module_id = packet.get("module_id")
        packet_prompt_id = packet.get("prompt_id")
        if (
            not isinstance(packet_module_id, str)
            or not isinstance(packet_prompt_id, str)
        ):
            event_record["classification"] = "invalid_completion_packet"
            event_record["packet_validation"] = {
                "result": "FAILED",
                "errors": [
                    "Completion Packet module_id/prompt_id unavailable for "
                    "queue-authoritative contract binding"
                ],
                "warnings": [],
            }
            result["events"].append(event_record)
            continue

        queue_binding, queue_binding_errors = _queue_prompt_contract_binding(
            blueprint_root,
            packet_module_id,
            packet_prompt_id,
        )
        if queue_binding_errors:
            event_record["classification"] = "invalid_completion_packet"
            event_record["packet_validation"] = {
                "result": "FAILED",
                "errors": queue_binding_errors,
                "warnings": [],
            }
            result["events"].append(event_record)
            continue
        if queue_binding is not None:
            binding_errors = _packet_queue_contract_errors(
                packet.get("prompt_contract"),
                queue_binding,
            )
            if binding_errors:
                event_record["classification"] = "invalid_completion_packet"
                event_record["packet_validation"] = {
                    "result": "FAILED",
                    "errors": binding_errors,
                    "warnings": [],
                }
                result["events"].append(event_record)
                continue

            claim_binding_errors = _b1_completion_claim_binding_errors(
                blueprint_root=blueprint_root,
                registry_path=registry_path,
                repository_root=repository_root,
                module_id=packet_module_id,
                prompt_id=packet_prompt_id,
                packet=packet,
                queue_binding=queue_binding,
            )
            if claim_binding_errors:
                event_record["classification"] = "invalid_completion_packet"
                event_record["packet_validation"] = {
                    "result": "FAILED",
                    "errors": claim_binding_errors,
                    "warnings": [],
                }
                result["events"].append(event_record)
                continue

        event_record["classification"] = "ready_for_blueprint_review"
        revision = event.get("revision")
        if isinstance(revision, dict):
            supersedes = revision.get("supersedes_event_id")
            if isinstance(supersedes, str) and supersedes:
                event_record["supersedes_event_id"] = supersedes
        result["events"].append(event_record)

    valid_by_id = {
        item.get("identity", {}).get("event_id"): item
        for item in result["events"]
        if item.get("classification") == "ready_for_blueprint_review"
        and isinstance(item.get("identity", {}).get("event_id"), str)
    }
    superseded_by: dict[str, list[str]] = {}
    for item in valid_by_id.values():
        target = item.get("supersedes_event_id")
        event_id = item.get("identity", {}).get("event_id")
        if isinstance(target, str) and isinstance(event_id, str):
            superseded_by.setdefault(target, []).append(event_id)

    for target, successors in sorted(superseded_by.items()):
        if len(successors) > 1:
            for successor in successors:
                candidate = valid_by_id.get(successor)
                if candidate is not None:
                    candidate["classification"] = "ambiguous_supersession"
            target_record = valid_by_id.get(target)
            if target_record is not None:
                target_record["classification"] = "ambiguous_supersession_target"
            result["errors"].append(
                f"multiple valid events supersede {target}: {','.join(sorted(successors))}"
            )
            continue
        target_record = valid_by_id.get(target)
        if target_record is not None:
            target_record["classification"] = "superseded"
            target_record["superseded_by_event_id"] = successors[0]

    return result



def _decision_subject_key(value: dict[str, Any]) -> tuple[str, ...] | None:
    fields = (
        "module_id",
        "prompt_id",
        "event_id",
        "event_path",
        "event_sha256",
        "packet_path",
        "packet_sha256",
    )
    parts = tuple(value.get(field) for field in fields)
    if not all(isinstance(item, str) and item for item in parts):
        return None
    return parts


def _candidate_decision_key(value: dict[str, Any]) -> tuple[str, ...] | None:
    return _decision_subject_key(value)


def _load_operator_decision_index(
    blueprint_root: Path,
) -> tuple[dict[tuple[str, ...], dict[str, Any]], list[str]]:
    review_root = blueprint_root / "coordination/review_packets"
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    errors: list[str] = []

    if not review_root.exists():
        return {}, []

    for path in sorted(review_root.glob("*/processed/*.yaml")):
        relative = path.relative_to(blueprint_root).as_posix()
        try:
            record = load_yaml(path)
        except Exception as exc:
            errors.append(
                f"INVALID_OPERATOR_DECISION_EVIDENCE:{relative}:{exc}"
            )
            continue

        if record.get("schema_version") != DECISION_SCHEMA:
            continue

        subject = record.get("subject")
        decision = record.get("decision")
        if not isinstance(subject, dict) or not isinstance(decision, dict):
            errors.append(
                f"INVALID_OPERATOR_DECISION_EVIDENCE:{relative}:"
                "subject_or_decision_not_mapping"
            )
            continue

        key = _decision_subject_key(subject)
        decision_id = decision.get("decision_id")
        operator_decision = decision.get("operator_decision")
        explicit = decision.get("explicit_operator_input")
        result = record.get("result")

        if (
            key is None
            or not isinstance(decision_id, str)
            or not decision_id
            or operator_decision not in {"ACCEPT", "RETURN", "HOLD"}
            or explicit is not True
            or result not in {"ACCEPTED", "RETURNED", "HELD"}
        ):
            errors.append(
                f"INVALID_OPERATOR_DECISION_EVIDENCE:{relative}:"
                "identity_or_decision_contract"
            )
            continue

        grouped.setdefault(key, []).append(
            {
                "evidence_path": relative,
                "decision_id": decision_id,
                "operator_decision": operator_decision,
                "result": result,
            }
        )

    index: dict[tuple[str, ...], dict[str, Any]] = {}
    for key, records in sorted(grouped.items()):
        if len(records) != 1:
            paths = ",".join(
                sorted(str(item["evidence_path"]) for item in records)
            )
            errors.append(
                "AMBIGUOUS_OPERATOR_DECISION_EVIDENCE:"
                + "|".join(key)
                + ":"
                + paths
            )
            continue
        index[key] = records[0]

    return index, sorted(errors)


def discover_completions(
    *,
    blueprint_root: Path,
    registry_path: Path,
    repository_overrides: dict[str, Path] | None = None,
    outbox_validator: Callable[..., dict[str, Any]] | None = None,
    packet_validator: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    blueprint_root = blueprint_root.resolve()
    registry_path = registry_path.resolve()
    registry = load_yaml(registry_path)

    policy = registry.get("lookup_policy")
    if not isinstance(policy, dict):
        raise ValueError("registry.lookup_policy must be a mapping")
    if policy.get("module_repository_access") != "read_only_from_blueprint":
        raise ValueError("Blueprint module repository access must be read-only")
    if policy.get("completion_outbox_authority") != "module_owned":
        raise ValueError("completion outbox authority must remain module-owned")
    if policy.get("completion_outbox_future_path") != OUTBOX_REL.as_posix():
        raise ValueError("completion outbox locator mismatch")
    if (
        policy.get("missing_future_source_behavior")
        != "record_not_present_yet_do_not_fabricate"
    ):
        raise ValueError("missing outbox fabrication policy mismatch")

    outbox_validator = outbox_validator or _default_outbox_validator
    packet_validator = packet_validator or _default_packet_validator

    sources: list[dict[str, Any]] = []
    for module in sorted(
        _registered_modules(registry),
        key=lambda item: str(item.get("module_id")),
    ):
        repository_root = _repository_root(module, repository_overrides)
        source_result = _discover_module(
            module=module,
            blueprint_root=blueprint_root,
            registry_path=registry_path,
            repository_root=repository_root,
            outbox_validator=outbox_validator,
            packet_validator=packet_validator,
        )
        sources.append(source_result)

    decision_index, decision_evidence_errors = (
        _load_operator_decision_index(blueprint_root)
    )
    review_candidates = []
    reconciled_decisions = []

    for source in sources:
        for event in source["events"]:
            if event.get("classification") != "ready_for_blueprint_review":
                continue

            identity = event.get("identity", {})
            candidate = {
                "module_id": source.get("module_id"),
                "repository_id": source.get("repository_id"),
                "event_id": identity.get("event_id"),
                "prompt_id": identity.get("prompt_id"),
                "completion_id": identity.get("completion_id"),
                "event_path": event.get("path"),
                "event_sha256": event.get("event_sha256"),
                "packet_path": event.get("packet_path"),
                "packet_sha256": event.get("packet_sha256"),
                "intake_state": "READY_FOR_BLUEPRINT_REVIEW",
                "operator_decision_created": False,
            }

            decision_record = decision_index.get(
                _candidate_decision_key(candidate)
            )
            if decision_record is not None:
                reconciled_decisions.append(
                    {
                        "module_id": candidate["module_id"],
                        "prompt_id": candidate["prompt_id"],
                        "event_id": candidate["event_id"],
                        "event_sha256": candidate["event_sha256"],
                        "packet_sha256": candidate["packet_sha256"],
                        "decision_id": decision_record["decision_id"],
                        "operator_decision": decision_record[
                            "operator_decision"
                        ],
                        "result": decision_record["result"],
                        "evidence_path": decision_record["evidence_path"],
                    }
                )
                continue

            review_candidates.append(candidate)

    review_candidates.sort(
        key=lambda item: (
            str(item.get("module_id")),
            str(item.get("event_id")),
        )
    )
    reconciled_decisions.sort(
        key=lambda item: (
            str(item.get("module_id")),
            str(item.get("event_id")),
            str(item.get("decision_id")),
        )
    )

    event_records = [
        event
        for source in sources
        for event in source.get("events", [])
    ]
    observed_states = {
        state: sum(
            1 for source in sources
            if source.get("observed_source_state") == state
        )
        for state in sorted(
            {
                str(source.get("observed_source_state"))
                for source in sources
            }
        )
    }

    invalid_events = sum(
        1
        for event in event_records
        if event.get("classification")
        in {
            "invalid_outbox_event",
            "invalid_completion_packet",
            "ambiguous_supersession",
            "ambiguous_supersession_target",
        }
    )
    superseded = sum(
        1
        for event in event_records
        if event.get("classification") == "superseded"
    )
    source_errors = (
        sum(
            len(source.get("errors", []))
            for source in sources
        )
        + len(decision_evidence_errors)
    )

    stable_payload = {
        "sources": sources,
        "review_candidates": review_candidates,
        "reconciled_decisions": reconciled_decisions,
        "decision_evidence_errors": decision_evidence_errors,
    }
    fingerprint = canonical_sha256(stable_payload)

    result_state = (
        "ATTENTION_REQUIRED"
        if invalid_events or source_errors
        else (
            "READY_FOR_BLUEPRINT_REVIEW"
            if review_candidates
            else "NO_COMPLETIONS_AVAILABLE"
        )
    )

    return {
        "schema_version": "blueprint_completion_discovery_and_intake_v0_4",
        "mode": "local_read_only",
        "network_independent": True,
        "result_state": result_state,
        "discovery_fingerprint_sha256": fingerprint,
        "summary": {
            "registered_sources": len(sources),
            "observed_source_states": observed_states,
            "events_discovered": len(event_records),
            "review_candidates": len(review_candidates),
            "reconciled_decisions": len(reconciled_decisions),
            "superseded_events": superseded,
            "invalid_events": invalid_events,
            "source_errors": source_errors,
            "decision_evidence_errors": len(decision_evidence_errors),
        },
        "review_candidates": review_candidates,
        "reconciled_decisions": reconciled_decisions,
        "decision_evidence_errors": decision_evidence_errors,
        "sources": sources,
        "governance": {
            "module_owned_outboxes_preserved": True,
            "module_repository_writes": False,
            "missing_sources_fabricated": False,
            "operator_decision_created": False,
            "operator_decisions_observed": len(reconciled_decisions),
            "automatic_acceptance": False,
            "automatic_return": False,
            "normal_v0_4_acceptance_allowed": False,
            "global_v0_4_promotion_performed": False,
            "step25_review_roadmap_queue_transaction_implemented": False,
        },
    }


def _tree_fingerprint(root: Path) -> str:
    rows: list[tuple[str, str]] = []
    for path in sorted(
        item for item in root.rglob("*") if item.is_file()
    ):
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if relative.startswith(".git/"):
            continue
        rows.append((relative, file_sha256(path)))
    return canonical_sha256(rows)


def render_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "ForPrint Completion Discovery + Intake v0.4",
        f"result: {report['result_state']}",
        f"mode: {report['mode']}",
        f"network_independent: {str(report['network_independent']).lower()}",
        f"registered_sources: {summary['registered_sources']}",
        f"events_discovered: {summary['events_discovered']}",
        f"review_candidates: {summary['review_candidates']}",
        f"reconciled_decisions: {summary.get('reconciled_decisions', 0)}",
        f"decision_evidence_errors: {summary.get('decision_evidence_errors', 0)}",
        f"superseded_events: {summary['superseded_events']}",
        f"invalid_events: {summary['invalid_events']}",
        f"source_errors: {summary['source_errors']}",
        (
            "discovery_fingerprint_sha256: "
            f"{report['discovery_fingerprint_sha256']}"
        ),
        "observed_source_states:",
    ]
    states = summary["observed_source_states"]
    if states:
        for key in sorted(states):
            lines.append(f"  {key}: {states[key]}")
    else:
        lines.append("  -")
    lines.extend(
        [
            "review_candidate_ids:",
            *(
                [
                    "  "
                    + f"{item['module_id']}:{item['event_id']}"
                    for item in report["review_candidates"]
                ]
                or ["  -"]
            ),
            "operator_decision_created: false",
            "normal_v0_4_acceptance_allowed: false",
            "global_v0_4_promotion_performed: false",
            "module_repository_writes: false",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path(
            "coordination/registry/"
            "coordination_source_registry_v0_1.yaml"
        ),
    )
    parser.add_argument(
        "--output-format",
        choices=("text", "yaml", "json"),
        default="text",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    registry = args.registry
    if not registry.is_absolute():
        registry = (root / registry).resolve()

    report = discover_completions(
        blueprint_root=root,
        registry_path=registry,
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
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        )
    else:
        print(render_text(report))

    return 1 if report["result_state"] == "ATTENTION_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
