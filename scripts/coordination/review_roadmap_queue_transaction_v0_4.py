from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

REQUEST_SCHEMA = "blueprint_review_roadmap_queue_transaction_request_v0_4"
EVIDENCE_SCHEMA = "blueprint_operator_review_decision_v0_4"
READY_INTAKE_STATE = "READY_FOR_BLUEPRINT_REVIEW"
DECISIONS = {"ACCEPT", "RETURN", "HOLD"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")


class TransactionError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TransactionError(f"expected YAML mapping: {path}")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


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


def _safe_path(root: Path, raw: str, label: str) -> Path:
    value = Path(raw)
    if value.is_absolute():
        raise TransactionError(f"{label} must be root-relative")
    target = (root / value).resolve()
    resolved_root = root.resolve()
    try:
        target.relative_to(resolved_root)
    except ValueError as exc:
        raise TransactionError(f"{label} escapes Blueprint root") from exc
    return target


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _one(items: list[Any], key: str, value: Any) -> dict[str, Any]:
    rows = [
        item
        for item in items
        if isinstance(item, dict) and item.get(key) == value
    ]
    if len(rows) != 1:
        raise TransactionError(
            f"{key}={value!r}: expected one record, got {len(rows)}"
        )
    return rows[0]


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise TransactionError(f"cannot import module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_status(root: Path) -> dict[str, Any]:
    root = root.resolve()
    discovery_path = (
        root / "scripts/coordination/completion_discovery_and_intake_v0_4.py"
    )
    registry_path = (
        root
        / "coordination/registry/coordination_source_registry_v0_1.yaml"
    )
    module = _load_module(
        discovery_path,
        "forprint_completion_discovery_intake_v04",
    )
    discovery = module.discover_completions(
        blueprint_root=root,
        registry_path=registry_path,
    )
    candidates = discovery.get("review_candidates", [])
    if not isinstance(candidates, list):
        raise TransactionError("discovery review_candidates must be a list")

    if discovery.get("result_state") == "ATTENTION_REQUIRED":
        result_state = "ATTENTION_REQUIRED"
    elif candidates:
        result_state = "REVIEW_CANDIDATES_AVAILABLE"
    else:
        result_state = "NO_REVIEW_TRANSACTION_AVAILABLE"

    return {
        "schema_version": "blueprint_review_transaction_live_status_v0_4",
        "mode": "local_read_only",
        "network_independent": True,
        "result_state": result_state,
        "discovery_result_state": discovery.get("result_state"),
        "discovery_fingerprint_sha256": discovery.get(
            "discovery_fingerprint_sha256"
        ),
        "review_candidates": copy.deepcopy(candidates),
        "summary": {
            "review_candidates": len(candidates),
            "events_discovered": discovery.get("summary", {}).get(
                "events_discovered"
            ),
            "invalid_events": discovery.get("summary", {}).get(
                "invalid_events"
            ),
            "source_errors": discovery.get("summary", {}).get(
                "source_errors"
            ),
        },
        "governance": {
            "operator_decision_created": False,
            "automatic_acceptance": False,
            "automatic_return": False,
            "automatic_hold": False,
            "roadmap_mutated": False,
            "prompt_queue_mutated": False,
            "prompt_file_mutated": False,
            "module_repository_writes": False,
            "next_prompt_selection_performed": False,
            "next_prompt_activation_performed": False,
            "global_v0_4_promotion_performed": False,
            "automatic_commit": False,
            "automatic_push": False,
        },
    }


def _completed_prompt_path(root: Path, approved: Path) -> Path:
    rel = approved.resolve().relative_to(root.resolve())
    parts = list(rel.parts)
    approved_positions = [
        index for index, value in enumerate(parts) if value == "approved"
    ]
    if len(approved_positions) != 1:
        raise TransactionError(
            "prompt_path must contain exactly one approved directory"
        )
    parts[approved_positions[0]] = "completed"
    return root / Path(*parts)


def _basic_request_identity(request: dict[str, Any]) -> dict[str, Any]:
    if request.get("schema_version") != REQUEST_SCHEMA:
        raise TransactionError("request schema mismatch")

    candidate = request.get("review_candidate")
    decision = request.get("decision")
    targets = request.get("targets")
    preconditions = request.get("preconditions")

    if not isinstance(candidate, dict):
        raise TransactionError("review_candidate must be a mapping")
    if not isinstance(decision, dict):
        raise TransactionError("decision must be a mapping")
    if not isinstance(targets, dict):
        raise TransactionError("targets must be a mapping")
    if not isinstance(preconditions, dict):
        raise TransactionError("preconditions must be a mapping")

    module_id = candidate.get("module_id")
    prompt_id = candidate.get("prompt_id")
    event_id = candidate.get("event_id")
    decision_id = decision.get("decision_id")
    operator_decision = decision.get("operator_decision")
    decided_at = decision.get("decided_at")

    for label, value in {
        "module_id": module_id,
        "prompt_id": prompt_id,
        "event_id": event_id,
        "decision_id": decision_id,
    }.items():
        if not isinstance(value, str) or not value or not SAFE_ID.fullmatch(value):
            raise TransactionError(f"{label} must be a safe non-empty id")

    if operator_decision not in DECISIONS:
        raise TransactionError(
            f"operator_decision must be one of {sorted(DECISIONS)}"
        )
    if decision.get("explicit_operator_input") is not True:
        raise TransactionError(
            "explicit_operator_input=true is required"
        )
    if not isinstance(decided_at, str) or not decided_at:
        raise TransactionError("decided_at is required")

    notes = decision.get("review_notes")
    if notes is None:
        notes = ""
    if not isinstance(notes, str):
        raise TransactionError("review_notes must be a string")
    if operator_decision == "RETURN" and not notes.strip():
        raise TransactionError("RETURN requires non-empty review_notes")

    if candidate.get("intake_state") != READY_INTAKE_STATE:
        raise TransactionError(
            "review candidate is not READY_FOR_BLUEPRINT_REVIEW"
        )
    if candidate.get("operator_decision_created") is not False:
        raise TransactionError(
            "review candidate already reports an operator decision"
        )

    for field in ["event_sha256", "packet_sha256"]:
        value = candidate.get(field)
        if not isinstance(value, str) or not HEX64.fullmatch(value):
            raise TransactionError(f"{field} must be a lowercase SHA-256")

    return {
        "candidate": candidate,
        "decision": decision,
        "targets": targets,
        "preconditions": preconditions,
        "module_id": module_id,
        "prompt_id": prompt_id,
        "event_id": event_id,
        "decision_id": decision_id,
        "operator_decision": operator_decision,
        "decided_at": decided_at,
        "review_notes": notes,
    }


def _resolve_targets(
    root: Path,
    identity: dict[str, Any],
) -> dict[str, Path | str]:
    targets = identity["targets"]
    required = [
        "roadmap_path",
        "prompt_queue_path",
        "prompt_path",
        "review_evidence_path",
        "roadmap_step_id",
    ]
    missing = [key for key in required if not targets.get(key)]
    if missing:
        raise TransactionError(f"missing transaction targets: {missing}")

    roadmap = _safe_path(root, targets["roadmap_path"], "roadmap_path")
    queue = _safe_path(
        root,
        targets["prompt_queue_path"],
        "prompt_queue_path",
    )
    prompt = _safe_path(root, targets["prompt_path"], "prompt_path")
    evidence = _safe_path(
        root,
        targets["review_evidence_path"],
        "review_evidence_path",
    )
    completed = _completed_prompt_path(root, prompt)

    module_id = identity["module_id"]
    decision_id = identity["decision_id"]
    expected_evidence_parent = (
        root
        / "coordination"
        / "review_packets"
        / module_id
        / "processed"
    ).resolve()
    if evidence.parent.resolve() != expected_evidence_parent:
        raise TransactionError(
            "review evidence must be under "
            "coordination/review_packets/<module_id>/processed/"
        )
    if evidence.name != f"{decision_id}.yaml":
        raise TransactionError(
            "review evidence filename must equal <decision_id>.yaml"
        )

    for label, path in {
        "roadmap": roadmap,
        "queue": queue,
    }.items():
        if not path.is_file():
            raise TransactionError(f"{label} target is missing: {path}")

    return {
        "roadmap": roadmap,
        "queue": queue,
        "prompt": prompt,
        "completed": completed,
        "evidence": evidence,
        "roadmap_step_id": targets["roadmap_step_id"],
    }


def _review_mapping(
    identity: dict[str, Any],
    evidence_rel: str,
) -> dict[str, Any]:
    candidate = identity["candidate"]
    return {
        "decision_id": identity["decision_id"],
        "operator_decision": identity["operator_decision"],
        "decided_at": identity["decided_at"],
        "review_notes": identity["review_notes"],
        "review_evidence": evidence_rel,
        "event_id": identity["event_id"],
        "event_sha256": candidate["event_sha256"],
        "packet_sha256": candidate["packet_sha256"],
    }


def _recalculate_queue_counts(queue: dict[str, Any]) -> None:
    prompts = [
        item
        for item in queue.get("prompts", [])
        if isinstance(item, dict)
    ]
    metadata = queue.get("metadata")
    if not isinstance(metadata, dict):
        return

    values = {
        "approved_prompt_count": sum(
            1 for item in prompts if item.get("status") == "approved"
        ),
        "draft_prompt_count": sum(
            1 for item in prompts if item.get("status") == "draft"
        ),
        "completed_prompt_count": sum(
            1 for item in prompts if item.get("status") == "completed"
        ),
        "dispatchable_draft_count": sum(
            1
            for item in prompts
            if item.get("status") == "draft"
            and item.get("dispatch_ready") is True
            and item.get("execution_status") != "deferred"
        ),
        "deferred_prompt_count": sum(
            1
            for item in prompts
            if item.get("execution_status") == "deferred"
        ),
    }
    for key, value in values.items():
        if key in metadata:
            metadata[key] = value

    if "active_prompt_count" in metadata:
        metadata["active_prompt_count"] = sum(
            1 for item in prompts if item.get("status") == "approved"
        )


def _eligible_steps(roadmap: dict[str, Any]) -> list[str]:
    steps = [
        item
        for item in roadmap.get("steps", [])
        if isinstance(item, dict)
    ]
    by_id = {
        item.get("step_id"): item
        for item in steps
        if isinstance(item.get("step_id"), str)
    }
    eligible: list[str] = []
    for item in steps:
        if item.get("status") not in {"planned", "ready"}:
            continue
        deps = item.get("depends_on", [])
        if deps is None:
            deps = []
        if not isinstance(deps, list):
            continue
        if all(
            isinstance(dep, str)
            and dep in by_id
            and by_id[dep].get("status") in {"completed", "accepted"}
            for dep in deps
        ):
            step_id = item.get("step_id")
            if isinstance(step_id, str):
                eligible.append(step_id)
    return sorted(eligible)


def _same_decision_evidence(
    evidence: dict[str, Any],
    identity: dict[str, Any],
) -> bool:
    subject = evidence.get("subject", {})
    decision = evidence.get("decision", {})
    return (
        evidence.get("schema_version") == EVIDENCE_SCHEMA
        and subject.get("module_id") == identity["module_id"]
        and subject.get("prompt_id") == identity["prompt_id"]
        and subject.get("event_id") == identity["event_id"]
        and decision.get("decision_id") == identity["decision_id"]
        and decision.get("operator_decision")
        == identity["operator_decision"]
        and decision.get("decided_at") == identity["decided_at"]
        and decision.get("review_notes") == identity["review_notes"]
    )


def _already_applied(
    root: Path,
    identity: dict[str, Any],
    paths: dict[str, Path | str],
) -> bool:
    evidence = paths["evidence"]
    if not isinstance(evidence, Path) or not evidence.is_file():
        return False

    existing = load_yaml(evidence)
    if not _same_decision_evidence(existing, identity):
        raise TransactionError(
            "review evidence collision with a different decision identity"
        )

    roadmap = load_yaml(paths["roadmap"])  # type: ignore[arg-type]
    queue = load_yaml(paths["queue"])  # type: ignore[arg-type]
    roadmap_step = _one(
        roadmap["steps"],
        "step_id",
        paths["roadmap_step_id"],
    )
    queue_prompt = _one(
        queue["prompts"],
        "prompt_id",
        identity["prompt_id"],
    )
    evidence_rel = _relative(root, evidence)
    decision = identity["operator_decision"]

    if roadmap_step.get("operator_decision") != decision:
        return False
    if roadmap_step.get("review_evidence") != evidence_rel:
        return False
    if queue_prompt.get("operator_decision") != decision:
        return False
    if queue_prompt.get("review_evidence") != evidence_rel:
        return False

    prompt = paths["prompt"]
    completed = paths["completed"]
    if not isinstance(prompt, Path) or not isinstance(completed, Path):
        return False

    if decision == "ACCEPT":
        return (
            roadmap_step.get("status") == "completed"
            and queue_prompt.get("status") == "completed"
            and queue_prompt.get("execution_status") == "accepted"
            and not prompt.exists()
            and completed.is_file()
        )

    expected_execution = "returned" if decision == "RETURN" else "held"
    return (
        queue_prompt.get("status") == "approved"
        and queue_prompt.get("execution_status") == expected_execution
        and prompt.is_file()
        and not completed.exists()
    )


def _validate_preconditions(
    identity: dict[str, Any],
    paths: dict[str, Path | str],
) -> None:
    prompt = paths["prompt"]
    if not isinstance(prompt, Path) or not prompt.is_file():
        raise TransactionError(
            "prompt target is missing before new transaction"
        )

    preconditions = identity["preconditions"]
    expected = {
        "roadmap_sha256": paths["roadmap"],
        "prompt_queue_sha256": paths["queue"],
        "prompt_sha256": paths["prompt"],
    }
    for key, path in expected.items():
        value = preconditions.get(key)
        if not isinstance(value, str) or not HEX64.fullmatch(value):
            raise TransactionError(f"{key} must be a lowercase SHA-256")
        assert isinstance(path, Path)
        actual = file_sha256(path)
        if actual != value:
            raise TransactionError(
                f"{key} mismatch: expected={value} actual={actual}"
            )

    completed = paths["completed"]
    assert isinstance(completed, Path)
    if completed.exists():
        raise TransactionError(
            "completed prompt target already exists before transaction"
        )


def _frontmatter_status(path: Path, status: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise TransactionError(f"prompt frontmatter missing: {path}")
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        raise TransactionError(f"prompt frontmatter malformed: {path}")
    front = yaml.safe_load(parts[1])
    if not isinstance(front, dict):
        raise TransactionError(f"prompt frontmatter is not mapping: {path}")
    front["status"] = status
    path.write_text(
        "---\n"
        + yaml.safe_dump(
            front,
            sort_keys=False,
            allow_unicode=True,
        ).rstrip()
        + "\n---\n"
        + parts[2],
        encoding="utf-8",
    )


def prepare_transaction(
    root: Path,
    request: dict[str, Any],
) -> dict[str, Any]:
    root = root.resolve()
    identity = _basic_request_identity(request)
    paths = _resolve_targets(root, identity)

    if _already_applied(root, identity, paths):
        return {
            "schema_version": "blueprint_review_transaction_plan_v0_4",
            "result_state": "ALREADY_APPLIED",
            "decision_id": identity["decision_id"],
            "operator_decision": identity["operator_decision"],
            "operator_decision_source": "explicit_operator_input",
            "mutations_required": False,
            "next_prompt_selection_performed": False,
            "next_prompt_activation_performed": False,
            "module_repository_writes": False,
        }

    _validate_preconditions(identity, paths)

    roadmap = load_yaml(paths["roadmap"])  # type: ignore[arg-type]
    queue = load_yaml(paths["queue"])  # type: ignore[arg-type]
    roadmap_step = _one(
        roadmap["steps"],
        "step_id",
        paths["roadmap_step_id"],
    )
    queue_prompt = _one(
        queue["prompts"],
        "prompt_id",
        identity["prompt_id"],
    )

    prompt = paths["prompt"]
    assert isinstance(prompt, Path)
    prompt_rel = _relative(root, prompt)
    if queue_prompt.get("path") != prompt_rel:
        raise TransactionError(
            "queue prompt path does not match request prompt_path"
        )
    if queue_prompt.get("status") != "approved":
        raise TransactionError(
            "reviewed prompt must remain approved before decision transaction"
        )

    decision = identity["operator_decision"]
    after_prompt = (
        _relative(root, paths["completed"])  # type: ignore[arg-type]
        if decision == "ACCEPT"
        else prompt_rel
    )
    roadmap_after = (
        "completed" if decision == "ACCEPT" else roadmap_step.get("status")
    )
    queue_execution_after = {
        "ACCEPT": "accepted",
        "RETURN": "returned",
        "HOLD": "held",
    }[decision]

    return {
        "schema_version": "blueprint_review_transaction_plan_v0_4",
        "result_state": "READY_TO_APPLY",
        "decision_id": identity["decision_id"],
        "operator_decision": decision,
        "operator_decision_source": "explicit_operator_input",
        "candidate": {
            "module_id": identity["module_id"],
            "prompt_id": identity["prompt_id"],
            "event_id": identity["event_id"],
            "intake_state": identity["candidate"]["intake_state"],
        },
        "transaction": {
            "roadmap_path": _relative(root, paths["roadmap"]),  # type: ignore[arg-type]
            "prompt_queue_path": _relative(root, paths["queue"]),  # type: ignore[arg-type]
            "roadmap_step_id": paths["roadmap_step_id"],
            "prompt_before": prompt_rel,
            "prompt_after": after_prompt,
            "review_evidence_path": _relative(
                root,
                paths["evidence"],  # type: ignore[arg-type]
            ),
            "roadmap_status_before": roadmap_step.get("status"),
            "roadmap_status_after": roadmap_after,
            "queue_status_before": queue_prompt.get("status"),
            "queue_status_after": (
                "completed" if decision == "ACCEPT" else "approved"
            ),
            "queue_execution_status_before": queue_prompt.get(
                "execution_status"
            ),
            "queue_execution_status_after": queue_execution_after,
            "physical_prompt_move": decision == "ACCEPT",
            "eligible_step_ids_after_transaction": None,
        },
        "boundaries": {
            "operator_decision_created_by_tool": False,
            "decision_must_preexist_in_request": True,
            "automatic_acceptance": False,
            "automatic_return": False,
            "automatic_hold": False,
            "module_repository_writes": False,
            "next_prompt_selection_performed": False,
            "next_prompt_activation_performed": False,
            "global_v0_4_promotion_performed": False,
            "automatic_commit": False,
            "automatic_push": False,
        },
    }


def _snapshot(paths: list[Path]) -> dict[Path, bytes | None]:
    return {
        path: path.read_bytes() if path.exists() else None
        for path in paths
    }


def _restore(snapshot: dict[Path, bytes | None]) -> None:
    for path, payload in snapshot.items():
        if payload is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)


def _build_evidence(
    root: Path,
    identity: dict[str, Any],
    paths: dict[str, Path | str],
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    candidate = identity["candidate"]
    decision = identity["operator_decision"]
    result = {
        "ACCEPT": "ACCEPTED",
        "RETURN": "RETURNED",
        "HOLD": "HELD",
    }[decision]

    return {
        "schema_version": EVIDENCE_SCHEMA,
        "metadata": {
            "decision_id": identity["decision_id"],
            "module_id": identity["module_id"],
            "created_at": identity["decided_at"],
            "owner": "forprint_system_blueprint",
            "immutable_decision_record": True,
        },
        "subject": {
            "module_id": identity["module_id"],
            "prompt_id": identity["prompt_id"],
            "event_id": identity["event_id"],
            "event_path": candidate.get("event_path"),
            "event_sha256": candidate["event_sha256"],
            "packet_path": candidate.get("packet_path"),
            "packet_sha256": candidate["packet_sha256"],
            "intake_state": candidate["intake_state"],
            "discovery_fingerprint_sha256": candidate.get(
                "discovery_fingerprint_sha256"
            ),
        },
        "decision": {
            "decision_id": identity["decision_id"],
            "operator_decision": decision,
            "explicit_operator_input": True,
            "decided_at": identity["decided_at"],
            "review_notes": identity["review_notes"],
        },
        "transaction": {
            "roadmap_path": _relative(
                root,
                paths["roadmap"],  # type: ignore[arg-type]
            ),
            "prompt_queue_path": _relative(
                root,
                paths["queue"],  # type: ignore[arg-type]
            ),
            "roadmap_step_id": paths["roadmap_step_id"],
            "prompt_before": before["prompt_path"],
            "prompt_after": after["prompt_path"],
            "roadmap_status_before": before["roadmap_status"],
            "roadmap_status_after": after["roadmap_status"],
            "queue_status_before": before["queue_status"],
            "queue_status_after": after["queue_status"],
            "queue_execution_status_before": before[
                "queue_execution_status"
            ],
            "queue_execution_status_after": after[
                "queue_execution_status"
            ],
            "eligible_step_ids_after_transaction": after[
                "eligible_step_ids"
            ],
            "next_prompt_selection_performed": False,
            "next_prompt_activation_performed": False,
        },
        "semantics": {
            "accept_moves_approved_to_completed": decision == "ACCEPT",
            "return_requires_corrections": decision == "RETURN",
            "hold_is_not_return": decision == "HOLD",
            "return_hold_preserve_prompt_outside_completed": (
                decision in {"RETURN", "HOLD"}
            ),
            "same_decision_identity_is_idempotent": True,
            "conflicting_decision_identity_fails_safely": True,
        },
        "boundaries": {
            "module_repository_writes": False,
            "automatic_acceptance": False,
            "automatic_return": False,
            "automatic_hold": False,
            "next_prompt_selection_performed": False,
            "next_prompt_activation_performed": False,
            "global_v0_4_promotion_performed": False,
            "automatic_commit": False,
            "automatic_push": False,
            "rollout_or_production_write": False,
        },
        "result": result,
    }


def apply_transaction(
    root: Path,
    request: dict[str, Any],
    *,
    operator_confirmation: str,
    post_write_validator: Callable[[], None] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    identity = _basic_request_identity(request)
    paths = _resolve_targets(root, identity)

    if operator_confirmation != identity["decision_id"]:
        raise TransactionError(
            "operator_confirmation must exactly match decision_id"
        )

    if _already_applied(root, identity, paths):
        return {
            "schema_version": "blueprint_review_transaction_result_v0_4",
            "result_state": "ALREADY_APPLIED",
            "decision_id": identity["decision_id"],
            "operator_decision": identity["operator_decision"],
            "idempotent_noop": True,
            "module_repository_writes": False,
            "next_prompt_selection_performed": False,
            "next_prompt_activation_performed": False,
        }

    plan = prepare_transaction(root, request)
    _validate_preconditions(identity, paths)

    roadmap_path = paths["roadmap"]
    queue_path = paths["queue"]
    prompt_path = paths["prompt"]
    completed_path = paths["completed"]
    evidence_path = paths["evidence"]

    assert isinstance(roadmap_path, Path)
    assert isinstance(queue_path, Path)
    assert isinstance(prompt_path, Path)
    assert isinstance(completed_path, Path)
    assert isinstance(evidence_path, Path)

    snapshot = _snapshot(
        [
            roadmap_path,
            queue_path,
            prompt_path,
            completed_path,
            evidence_path,
        ]
    )

    roadmap = load_yaml(roadmap_path)
    queue = load_yaml(queue_path)
    roadmap_step = _one(
        roadmap["steps"],
        "step_id",
        paths["roadmap_step_id"],
    )
    queue_prompt = _one(
        queue["prompts"],
        "prompt_id",
        identity["prompt_id"],
    )

    before = {
        "prompt_path": _relative(root, prompt_path),
        "roadmap_status": roadmap_step.get("status"),
        "queue_status": queue_prompt.get("status"),
        "queue_execution_status": queue_prompt.get("execution_status"),
    }
    evidence_rel = _relative(root, evidence_path)
    review = _review_mapping(identity, evidence_rel)
    decision = identity["operator_decision"]

    try:
        roadmap_step["blueprint_review"] = copy.deepcopy(review)
        roadmap_step["operator_decision"] = decision
        roadmap_step["review_evidence"] = evidence_rel

        queue_prompt["blueprint_review"] = copy.deepcopy(review)
        queue_prompt["operator_decision"] = decision
        queue_prompt["review_evidence"] = evidence_rel

        if decision == "ACCEPT":
            roadmap_step["status"] = "completed"
            roadmap_step["accepted_at"] = identity["decided_at"]

            queue_prompt["status"] = "completed"
            queue_prompt["execution_status"] = "accepted"
            queue_prompt["accepted_at"] = identity["decided_at"]
            queue_prompt["path"] = _relative(root, completed_path)

            metadata = queue.get("metadata")
            if (
                isinstance(metadata, dict)
                and metadata.get("active_prompt_id")
                == identity["prompt_id"]
            ):
                metadata["active_prompt_id"] = None

            completed_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.rename(completed_path)
            _frontmatter_status(completed_path, "completed")

        elif decision == "RETURN":
            roadmap_step["returned_at"] = identity["decided_at"]
            queue_prompt["execution_status"] = "returned"
            queue_prompt["returned_at"] = identity["decided_at"]

        else:
            roadmap_step["held_at"] = identity["decided_at"]
            queue_prompt["execution_status"] = "held"
            queue_prompt["held_at"] = identity["decided_at"]

        _recalculate_queue_counts(queue)
        eligible = _eligible_steps(roadmap)

        after_prompt = (
            completed_path if decision == "ACCEPT" else prompt_path
        )
        after = {
            "prompt_path": _relative(root, after_prompt),
            "roadmap_status": roadmap_step.get("status"),
            "queue_status": queue_prompt.get("status"),
            "queue_execution_status": queue_prompt.get("execution_status"),
            "eligible_step_ids": eligible,
        }

        evidence = _build_evidence(
            root,
            identity,
            paths,
            before,
            after,
        )

        write_yaml(roadmap_path, roadmap)
        write_yaml(queue_path, queue)
        write_yaml(evidence_path, evidence)

        if post_write_validator is not None:
            post_write_validator()

        if decision == "ACCEPT":
            if prompt_path.exists() or not completed_path.is_file():
                raise TransactionError(
                    "ACCEPT physical prompt transition failed"
                )
        else:
            if not prompt_path.is_file() or completed_path.exists():
                raise TransactionError(
                    "RETURN/HOLD physical prompt invariant failed"
                )

        result = {
            "schema_version": "blueprint_review_transaction_result_v0_4",
            "result_state": {
                "ACCEPT": "ACCEPT_APPLIED",
                "RETURN": "RETURN_APPLIED",
                "HOLD": "HOLD_APPLIED",
            }[decision],
            "decision_id": identity["decision_id"],
            "operator_decision": decision,
            "review_evidence": evidence_rel,
            "transaction_fingerprint_sha256": canonical_sha256(
                {
                    "plan": plan,
                    "evidence": evidence,
                }
            ),
            "idempotent_noop": False,
            "module_repository_writes": False,
            "next_prompt_selection_performed": False,
            "next_prompt_activation_performed": False,
            "global_v0_4_promotion_performed": False,
            "automatic_commit": False,
            "automatic_push": False,
        }
        return result

    except Exception:
        _restore(snapshot)
        raise


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "ForPrint Review / Roadmap / Queue Transaction v0.4",
        f"result: {report.get('result_state')}",
    ]
    if "mode" in report:
        lines.append(f"mode: {report['mode']}")
    if "discovery_result_state" in report:
        lines.append(
            "discovery_result_state: "
            f"{report['discovery_result_state']}"
        )
    summary = report.get("summary")
    if isinstance(summary, dict):
        for key in [
            "review_candidates",
            "events_discovered",
            "invalid_events",
            "source_errors",
        ]:
            if key in summary:
                lines.append(f"{key}: {summary[key]}")
    if "operator_decision" in report:
        lines.append(
            f"operator_decision: {report['operator_decision']}"
        )
    if "decision_id" in report:
        lines.append(f"decision_id: {report['decision_id']}")
    lines.extend(
        [
            "operator_decision_created_automatically: false",
            "module_repository_writes: false",
            "next_prompt_selection_performed: false",
            "next_prompt_activation_performed: false",
            "global_v0_4_promotion_performed: false",
            "automatic_commit: false",
            "automatic_push: false",
        ]
    )
    return "\n".join(lines)


def _emit(report: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(
            json.dumps(
                report,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        )
    elif output_format == "yaml":
        print(
            yaml.safe_dump(
                report,
                sort_keys=False,
                allow_unicode=True,
            ).rstrip()
        )
    else:
        print(render_text(report))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--live-status", action="store_true")
    parser.add_argument("--request", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--operator-confirmation")
    parser.add_argument(
        "--output-format",
        choices=("text", "yaml", "json"),
        default="text",
    )
    args = parser.parse_args()

    root = args.root.resolve()

    if args.live_status or args.request is None:
        if args.apply:
            raise TransactionError("--apply requires --request")
        report = live_status(root)
        _emit(report, args.output_format)
        return 1 if report["result_state"] == "ATTENTION_REQUIRED" else 0

    request_path = args.request
    if not request_path.is_absolute():
        request_path = (root / request_path).resolve()
    try:
        request_path.relative_to(root)
    except ValueError as exc:
        raise TransactionError(
            "request file must be inside Blueprint root"
        ) from exc

    request = load_yaml(request_path)

    if args.apply:
        if not args.operator_confirmation:
            raise TransactionError(
                "--operator-confirmation is required for --apply"
            )
        report = apply_transaction(
            root,
            request,
            operator_confirmation=args.operator_confirmation,
        )
    else:
        report = prepare_transaction(root, request)

    _emit(report, args.output_format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
