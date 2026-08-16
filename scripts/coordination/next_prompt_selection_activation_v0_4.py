from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

SELECTION_SCHEMA = "blueprint_next_prompt_selection_v0_4"
ACTIVATION_REQUEST_SCHEMA = "blueprint_next_prompt_activation_request_v0_4"
ACTIVATION_EVIDENCE_SCHEMA = "blueprint_next_prompt_activation_evidence_v0_4"

SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PRIORITY_ORDER = {
    "critical": 0,
    "highest": 0,
    "high": 1,
    "normal": 2,
    "medium": 2,
    "low": 3,
}


class SelectionActivationError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SelectionActivationError(f"expected YAML mapping: {path}")
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
        raise SelectionActivationError(f"{label} must be root-relative")
    root = root.resolve()
    target = (root / value).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise SelectionActivationError(
            f"{label} escapes Blueprint root"
        ) from exc
    return target


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _one(
    items: list[Any],
    key: str,
    value: Any,
) -> dict[str, Any]:
    rows = [
        item
        for item in items
        if isinstance(item, dict) and item.get(key) == value
    ]
    if len(rows) != 1:
        raise SelectionActivationError(
            f"{key}={value!r}: expected one record, got {len(rows)}"
        )
    return rows[0]


def _unique_by(items: list[Any], key: str, label: str) -> None:
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise SelectionActivationError(f"{label} contains non-mapping")
        value = item.get(key)
        if not isinstance(value, str) or not value:
            raise SelectionActivationError(
                f"{label} record missing {key}"
            )
        if value in seen:
            raise SelectionActivationError(
                f"duplicate {label} {key}: {value}"
            )
        seen.add(value)


def _paths(root: Path) -> dict[str, Path]:
    return {
        "roadmap": root / "coordination/self_coordination/roadmap.yaml",
        "queue": (
            root
            / "coordination/self_coordination/prompt_queue/index.yaml"
        ),
        "handoff": (
            root
            / "coordination/instruction_intake/bootstrap/"
            "current_handoff_v0_1.yaml"
        ),
        "health_policy": (
            root
            / "coordination/standards/governance/"
            "coordination_health_policy_v0_1.yaml"
        ),
    }


def _active_prompts(queue: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in queue.get("prompts", [])
        if isinstance(item, dict) and item.get("status") == "approved"
    ]


def _dependency_status(
    roadmap: dict[str, Any],
    step: dict[str, Any],
) -> tuple[bool, list[str]]:
    steps = roadmap.get("steps", [])
    reasons: list[str] = []
    for dependency_id in step.get("depends_on") or []:
        rows = [
            item
            for item in steps
            if isinstance(item, dict)
            and item.get("step_id") == dependency_id
        ]
        if len(rows) != 1:
            reasons.append(f"UNKNOWN_DEPENDENCY:{dependency_id}")
            continue
        dependency = rows[0]
        if dependency.get("status") != "completed":
            reasons.append(f"DEPENDENCY_NOT_COMPLETED:{dependency_id}")
            continue
        decision = dependency.get("operator_decision")
        if decision is not None and decision != "ACCEPT":
            reasons.append(f"DEPENDENCY_NOT_ACCEPTED:{dependency_id}")
    return not reasons, reasons


def _priority_rank(value: Any) -> int:
    return PRIORITY_ORDER.get(str(value or "normal").lower(), 50)


def _sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    sequence = item.get("sequence")
    queue_rank = item.get("queue_rank")
    if not isinstance(sequence, int):
        sequence = 10**9
    if not isinstance(queue_rank, int):
        queue_rank = sequence
    return (
        queue_rank,
        sequence,
        _priority_rank(item.get("priority")),
        str(item.get("created_at") or ""),
        str(item.get("prompt_id") or ""),
    )


def _candidate_records(
    root: Path,
    roadmap: dict[str, Any],
    queue: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    steps = roadmap.get("steps", [])
    prompts = queue.get("prompts", [])
    _unique_by(steps, "step_id", "roadmap steps")
    _unique_by(prompts, "prompt_id", "prompt queue")

    eligible: list[dict[str, Any]] = []
    blocked: dict[str, list[str]] = {}

    for prompt in prompts:
        if not isinstance(prompt, dict):
            continue
        if prompt.get("status") != "draft":
            continue
        if prompt.get("execution_status") != "planned":
            continue
        if prompt.get("dispatch_ready") is not True:
            continue

        prompt_id = prompt["prompt_id"]
        step_id = prompt.get("roadmap_step_id")
        reasons: list[str] = []

        rows = [
            item
            for item in steps
            if isinstance(item, dict) and item.get("step_id") == step_id
        ]
        if len(rows) != 1:
            reasons.append("ROADMAP_STEP_REFERENCE_INVALID")
        else:
            step = rows[0]
            if step.get("status") not in {"planned", "ready"}:
                reasons.append(
                    f"ROADMAP_STATUS_NOT_ELIGIBLE:{step.get('status')}"
                )
            dep_ok, dep_reasons = _dependency_status(roadmap, step)
            if not dep_ok:
                reasons.extend(dep_reasons)

        raw_path = prompt.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            reasons.append("PROMPT_PATH_MISSING")
        else:
            try:
                prompt_path = _safe_path(root, raw_path, "prompt path")
            except SelectionActivationError:
                reasons.append("PROMPT_PATH_INVALID")
            else:
                if not prompt_path.is_file():
                    reasons.append("PROMPT_FILE_MISSING")
                elif prompt_path.parent.name != "draft":
                    reasons.append("PROMPT_NOT_IN_DRAFT_DIRECTORY")

        if reasons:
            blocked[prompt_id] = reasons
        else:
            eligible.append(copy.deepcopy(prompt))

    eligible.sort(key=_sort_key)
    return eligible, blocked


def select_next_prompt(
    root: Path,
    *,
    override_prompt_id: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    paths = _paths(root)
    roadmap = load_yaml(paths["roadmap"])
    queue = load_yaml(paths["queue"])

    active = _active_prompts(queue)
    if len(active) > 1:
        return {
            "schema_version": SELECTION_SCHEMA,
            "result_state": "ATTENTION_REQUIRED",
            "error_code": "MULTIPLE_ACTIVE_PROMPTS",
            "active_prompt_count": len(active),
            "active_prompt_ids": sorted(
                item["prompt_id"] for item in active
            ),
            "selected_prompt": None,
            "selection_performed": False,
            "activation_performed": False,
        }

    eligible, blocked = _candidate_records(root, roadmap, queue)
    eligible_ids = [item["prompt_id"] for item in eligible]

    if override_prompt_id is not None:
        if not SAFE_ID.fullmatch(override_prompt_id):
            raise SelectionActivationError(
                "override_prompt_id contains unsafe characters"
            )
        if override_prompt_id not in eligible_ids:
            raise SelectionActivationError(
                "explicit override is not dependency-eligible and "
                "dispatchable"
            )
        selected = next(
            item
            for item in eligible
            if item["prompt_id"] == override_prompt_id
        )
        selection_source = "explicit_validated_override"
    else:
        selected = eligible[0] if eligible else None
        selection_source = "deterministic_queue_order"

    if active:
        result_state = "ACTIVE_PROMPT_PRESENT"
        selected_for_activation = None
    elif selected is None:
        result_state = "NO_ELIGIBLE_PROMPT"
        selected_for_activation = None
    else:
        result_state = "NEXT_PROMPT_SELECTED"
        selected_for_activation = selected

    payload = {
        "schema_version": SELECTION_SCHEMA,
        "result_state": result_state,
        "selection_source": selection_source,
        "active_prompt_count": len(active),
        "active_prompt_ids": [
            item["prompt_id"] for item in active
        ],
        "eligible_prompt_ids": eligible_ids,
        "blocked_prompts": blocked,
        "selected_prompt": copy.deepcopy(selected_for_activation),
        "selection_performed": selected_for_activation is not None,
        "activation_performed": False,
        "module_repository_writes": False,
        "automatic_acceptance": False,
        "automatic_return": False,
        "automatic_hold": False,
        "tracking_events_reference_run": False,
        "dark_zone_audit_run": False,
        "global_v0_4_promotion_performed": False,
        "automatic_commit": False,
        "automatic_push": False,
    }
    fingerprint_payload = copy.deepcopy(payload)
    fingerprint_payload.pop("schema_version", None)
    payload["selection_fingerprint_sha256"] = canonical_sha256(
        fingerprint_payload
    )
    return payload


def _completed_path(root: Path, draft_path: Path) -> Path:
    if draft_path.parent.name != "draft":
        raise SelectionActivationError(
            "activation prompt path must be under a draft directory"
        )
    return (
        draft_path.parent.parent
        / "approved"
        / draft_path.name
    ).resolve()


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


def _frontmatter_status(path: Path, status: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SelectionActivationError(
            f"prompt frontmatter missing: {path}"
        )
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        raise SelectionActivationError(
            f"prompt frontmatter malformed: {path}"
        )
    front = yaml.safe_load(parts[1])
    if not isinstance(front, dict):
        raise SelectionActivationError(
            f"prompt frontmatter invalid: {path}"
        )
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


def _recalculate_queue_counts(queue: dict[str, Any]) -> None:
    prompts = [
        item
        for item in queue.get("prompts", [])
        if isinstance(item, dict)
    ]
    metadata = queue.setdefault("metadata", {})
    metadata["approved_prompt_count"] = sum(
        item.get("status") == "approved" for item in prompts
    )
    metadata["draft_prompt_count"] = sum(
        item.get("status") == "draft" for item in prompts
    )
    metadata["completed_prompt_count"] = sum(
        item.get("status") == "completed" for item in prompts
    )
    metadata["dispatchable_draft_count"] = sum(
        item.get("status") == "draft"
        and item.get("dispatch_ready") is True
        and item.get("execution_status") != "deferred"
        for item in prompts
    )
    metadata["deferred_prompt_count"] = sum(
        item.get("execution_status") == "deferred"
        for item in prompts
    )
    if "active_prompt_count" in metadata:
        metadata["active_prompt_count"] = sum(
            item.get("status") == "approved" for item in prompts
        )


def _health_state(
    value: int,
    minimum: int,
    target: int,
) -> str:
    if value < minimum:
        return "below_minimum"
    if value < target:
        return "minimum_met_target_not_met"
    return "target_met"


def _compute_health(
    roadmap: dict[str, Any],
    queue: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    current_id = roadmap.get("metadata", {}).get("current_step_id")
    current = _one(roadmap["steps"], "step_id", current_id)
    current_sequence = current.get("sequence")
    if not isinstance(current_sequence, int):
        raise SelectionActivationError("current roadmap sequence invalid")

    future = sum(
        isinstance(item, dict)
        and isinstance(item.get("sequence"), int)
        and item["sequence"] > current_sequence
        and item.get("status") in {"active", "planned", "ready"}
        for item in roadmap["steps"]
    )
    dispatchable = sum(
        isinstance(item, dict)
        and item.get("status") == "draft"
        and item.get("dispatch_ready") is True
        and item.get("execution_status") != "deferred"
        for item in queue["prompts"]
    )

    road = policy["roadmap"]
    prompt = policy["prompt_buffer"]
    road_min = road["minimum_future_steps"]
    road_target = road["target_future_steps"]
    prompt_min = prompt["minimum_dispatchable_drafts"]
    prompt_target = prompt["target_dispatchable_drafts"]

    warnings: list[str] = []
    advisories: list[str] = []
    if future < road_min:
        warnings.append("ROADMAP_HORIZON_BELOW_MINIMUM")
    elif future < road_target:
        advisories.append("ROADMAP_HORIZON_BELOW_TARGET")

    if dispatchable < prompt_min:
        warnings.append("PROMPT_BUFFER_BELOW_MINIMUM")
    elif dispatchable < prompt_target:
        advisories.append("PROMPT_BUFFER_BELOW_TARGET")

    return {
        "roadmap_future_steps": future,
        "roadmap_state": _health_state(
            future,
            road_min,
            road_target,
        ),
        "dispatchable_draft_prompts": dispatchable,
        "prompt_buffer_state": _health_state(
            dispatchable,
            prompt_min,
            prompt_target,
        ),
        "warnings": sorted(warnings),
        "advisories": sorted(advisories),
        "blocking_errors": [],
        "overall_state": (
            "warning"
            if warnings
            else ("advisory" if advisories else "healthy")
        ),
    }


def _update_handoff(
    handoff: dict[str, Any],
    roadmap: dict[str, Any],
    queue: dict[str, Any],
    health: dict[str, Any],
    *,
    activated_at: str,
) -> None:
    current_id = roadmap["metadata"]["current_step_id"]
    current = _one(roadmap["steps"], "step_id", current_id)
    prompt = _one(queue["prompts"], "roadmap_step_id", current_id)

    handoff.setdefault("metadata", {})["snapshot_updated_at"] = activated_at

    plan = handoff.setdefault("current_blueprint_plan", {})
    plan["active_blueprint_step"] = {
        "id": current_id,
        "status": current.get("status"),
        "sequence": current.get("sequence"),
        "title": current.get("title"),
    }
    plan["active_prompt"] = {
        "id": prompt.get("prompt_id"),
        "status": prompt.get("status"),
        "execution_status": prompt.get("execution_status"),
        "path": prompt.get("path"),
    }

    current_sequence = current["sequence"]
    ordered = sorted(
        [
            item
            for item in roadmap["steps"]
            if isinstance(item, dict)
            and isinstance(item.get("sequence"), int)
            and item["sequence"] >= current_sequence
            and item.get("status") in {"active", "planned", "ready"}
        ],
        key=lambda item: item["sequence"],
    )
    plan["next_planned_steps"] = [
        {
            "index": item["sequence"],
            "id": item["step_id"],
            "status": item["status"],
        }
        for item in ordered[:8]
    ]

    handoff["next_10_steps"] = [
        {
            "order": index,
            "id": item["step_id"],
            "title": item.get("title"),
            "status": item["status"],
        }
        for index, item in enumerate(ordered[:10], 1)
    ]

    existing = handoff.setdefault("self_coordination_health", {})
    existing.update(health)
    existing["evaluated_at"] = activated_at


def _request_identity(
    request: dict[str, Any],
) -> dict[str, Any]:
    if request.get("schema_version") != ACTIVATION_REQUEST_SCHEMA:
        raise SelectionActivationError(
            "unsupported activation request schema"
        )

    activation_id = request.get("activation_id")
    activated_at = request.get("activated_at")
    selection = request.get("selection")
    targets = request.get("targets")
    preconditions = request.get("preconditions")

    if not isinstance(activation_id, str) or not SAFE_ID.fullmatch(
        activation_id
    ):
        raise SelectionActivationError("invalid activation_id")
    if not isinstance(activated_at, str) or not activated_at:
        raise SelectionActivationError("activated_at is required")
    if not isinstance(selection, dict):
        raise SelectionActivationError("selection mapping is required")
    if not isinstance(targets, dict):
        raise SelectionActivationError("targets mapping is required")
    if not isinstance(preconditions, dict):
        raise SelectionActivationError(
            "preconditions mapping is required"
        )

    prompt_id = selection.get("prompt_id")
    step_id = selection.get("roadmap_step_id")
    fingerprint = selection.get("selection_fingerprint_sha256")
    selection_source = selection.get(
        "selection_source",
        "deterministic_queue_order",
    )
    if selection_source not in {
        "deterministic_queue_order",
        "explicit_validated_override",
    }:
        raise SelectionActivationError("invalid selection_source")
    if not isinstance(prompt_id, str) or not SAFE_ID.fullmatch(prompt_id):
        raise SelectionActivationError("invalid selected prompt_id")
    if not isinstance(step_id, str) or not SAFE_ID.fullmatch(step_id):
        raise SelectionActivationError("invalid roadmap_step_id")
    if not isinstance(fingerprint, str) or not HEX64.fullmatch(
        fingerprint
    ):
        raise SelectionActivationError("invalid selection fingerprint")

    identity = {
        "activation_id": activation_id,
        "activated_at": activated_at,
        "prompt_id": prompt_id,
        "roadmap_step_id": step_id,
        "selection_fingerprint_sha256": fingerprint,
        "selection_source": selection_source,
        "targets": copy.deepcopy(targets),
        "preconditions": copy.deepcopy(preconditions),
    }
    identity["identity_sha256"] = canonical_sha256(identity)
    return identity


def _resolve_targets(
    root: Path,
    identity: dict[str, Any],
) -> dict[str, Path]:
    targets = identity["targets"]
    required = [
        "roadmap_path",
        "prompt_queue_path",
        "handoff_path",
        "prompt_path",
        "activation_evidence_path",
    ]
    missing = [key for key in required if not targets.get(key)]
    if missing:
        raise SelectionActivationError(
            f"missing activation targets: {missing}"
        )

    roadmap = _safe_path(root, targets["roadmap_path"], "roadmap_path")
    queue = _safe_path(
        root,
        targets["prompt_queue_path"],
        "prompt_queue_path",
    )
    handoff = _safe_path(root, targets["handoff_path"], "handoff_path")
    prompt = _safe_path(root, targets["prompt_path"], "prompt_path")
    approved = _completed_path(root, prompt)
    evidence = _safe_path(
        root,
        targets["activation_evidence_path"],
        "activation_evidence_path",
    )

    expected_parent = (
        root
        / "coordination/internal_work/blueprint/governance/"
        "next_prompt_activation"
    ).resolve()
    if evidence.parent.resolve() != expected_parent:
        raise SelectionActivationError(
            "activation evidence must be under "
            "coordination/internal_work/blueprint/governance/"
            "next_prompt_activation/"
        )
    if evidence.name != f"{identity['activation_id']}.yaml":
        raise SelectionActivationError(
            "activation evidence filename must equal <activation_id>.yaml"
        )

    for label, path in {
        "roadmap": roadmap,
        "queue": queue,
        "handoff": handoff,
    }.items():
        if not path.is_file():
            raise SelectionActivationError(
                f"{label} target is missing: {path}"
            )

    return {
        "roadmap": roadmap,
        "queue": queue,
        "handoff": handoff,
        "prompt": prompt,
        "approved": approved,
        "evidence": evidence,
    }


def _existing_evidence_state(
    identity: dict[str, Any],
    paths: dict[str, Path],
) -> str | None:
    evidence_path = paths["evidence"]
    if not evidence_path.is_file():
        return None
    evidence = load_yaml(evidence_path)
    existing = evidence.get("activation_identity_sha256")
    if existing == identity["identity_sha256"]:
        return "same"
    raise SelectionActivationError(
        "activation_id already exists with different activation identity"
    )


def _validate_preconditions(
    identity: dict[str, Any],
    paths: dict[str, Path],
) -> None:
    prompt = paths["prompt"]
    if not prompt.is_file():
        raise SelectionActivationError(
            "draft prompt target is missing before new activation"
        )
    if paths["approved"].exists():
        raise SelectionActivationError(
            "approved prompt target already exists"
        )

    expected = identity["preconditions"]
    checks = {
        "roadmap_sha256": file_sha256(paths["roadmap"]),
        "prompt_queue_sha256": file_sha256(paths["queue"]),
        "handoff_sha256": file_sha256(paths["handoff"]),
        "prompt_sha256": file_sha256(prompt),
    }
    for key, actual in checks.items():
        value = expected.get(key)
        if not isinstance(value, str) or not HEX64.fullmatch(value):
            raise SelectionActivationError(
                f"invalid precondition hash: {key}"
            )
        if value != actual:
            raise SelectionActivationError(
                f"precondition mismatch: {key}"
            )


def prepare_activation(
    root: Path,
    request: dict[str, Any],
) -> dict[str, Any]:
    root = root.resolve()
    identity = _request_identity(request)
    paths = _resolve_targets(root, identity)

    existing = _existing_evidence_state(identity, paths)
    if existing == "same":
        return {
            "schema_version": ACTIVATION_REQUEST_SCHEMA,
            "result_state": "ALREADY_APPLIED",
            "activation_id": identity["activation_id"],
            "idempotent_noop": True,
        }

    _validate_preconditions(identity, paths)

    override = (
        identity["prompt_id"]
        if identity["selection_source"] == "explicit_validated_override"
        else None
    )
    selection = select_next_prompt(
        root,
        override_prompt_id=override,
    )
    if selection.get("result_state") != "NEXT_PROMPT_SELECTED":
        raise SelectionActivationError(
            "current state is not eligible for activation"
        )
    selected = selection.get("selected_prompt")
    if not isinstance(selected, dict):
        raise SelectionActivationError("selection result missing prompt")
    if selected.get("prompt_id") != identity["prompt_id"]:
        raise SelectionActivationError(
            "request prompt does not match deterministic selection"
        )
    if selected.get("roadmap_step_id") != identity["roadmap_step_id"]:
        raise SelectionActivationError(
            "request roadmap step does not match deterministic selection"
        )
    if (
        selection.get("selection_fingerprint_sha256")
        != identity["selection_fingerprint_sha256"]
    ):
        raise SelectionActivationError(
            "selection fingerprint changed"
        )

    if selected.get("path") != _relative(root, paths["prompt"]):
        raise SelectionActivationError(
            "request prompt path does not match selected queue record"
        )

    return {
        "schema_version": ACTIVATION_REQUEST_SCHEMA,
        "result_state": "ACTIVATION_READY",
        "activation_id": identity["activation_id"],
        "prompt_id": identity["prompt_id"],
        "roadmap_step_id": identity["roadmap_step_id"],
        "selection_fingerprint_sha256": identity[
            "selection_fingerprint_sha256"
        ],
        "selection_source": identity["selection_source"],
        "activation_identity_sha256": identity["identity_sha256"],
        "mutation_paths": sorted(
            {
                _relative(root, paths["roadmap"]),
                _relative(root, paths["queue"]),
                _relative(root, paths["handoff"]),
                _relative(root, paths["prompt"]),
                _relative(root, paths["approved"]),
                _relative(root, paths["evidence"]),
            }
        ),
        "selection_performed": True,
        "activation_performed": False,
        "automatic_acceptance": False,
        "automatic_return": False,
        "automatic_hold": False,
        "module_repository_writes": False,
        "tracking_events_reference_run": False,
        "dark_zone_audit_run": False,
        "global_v0_4_promotion_performed": False,
        "automatic_commit": False,
        "automatic_push": False,
    }


def apply_activation(
    root: Path,
    request: dict[str, Any],
    *,
    activation_confirmation: str,
    post_write_validator: Callable[[], None] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    identity = _request_identity(request)
    paths = _resolve_targets(root, identity)

    if activation_confirmation != identity["activation_id"]:
        raise SelectionActivationError(
            "activation_confirmation must exactly match activation_id"
        )

    existing = _existing_evidence_state(identity, paths)
    if existing == "same":
        return {
            "schema_version": ACTIVATION_EVIDENCE_SCHEMA,
            "result_state": "ALREADY_APPLIED",
            "activation_id": identity["activation_id"],
            "idempotent_noop": True,
            "selection_performed": False,
            "activation_performed": False,
            "automatic_acceptance": False,
            "automatic_return": False,
            "automatic_hold": False,
            "module_repository_writes": False,
            "automatic_commit": False,
            "automatic_push": False,
        }

    plan = prepare_activation(root, request)

    snapshot = _snapshot(
        [
            paths["roadmap"],
            paths["queue"],
            paths["handoff"],
            paths["prompt"],
            paths["approved"],
            paths["evidence"],
        ]
    )

    roadmap = load_yaml(paths["roadmap"])
    queue = load_yaml(paths["queue"])
    handoff = load_yaml(paths["handoff"])
    health_policy = load_yaml(_paths(root)["health_policy"])

    step = _one(
        roadmap["steps"],
        "step_id",
        identity["roadmap_step_id"],
    )
    prompt = _one(
        queue["prompts"],
        "prompt_id",
        identity["prompt_id"],
    )

    before = {
        "roadmap_current_step_id": (
            roadmap.get("metadata", {}).get("current_step_id")
        ),
        "roadmap_status": step.get("status"),
        "queue_active_prompt_id": (
            queue.get("metadata", {}).get("active_prompt_id")
        ),
        "queue_status": prompt.get("status"),
        "queue_execution_status": prompt.get("execution_status"),
        "prompt_path": prompt.get("path"),
    }

    try:
        if _active_prompts(queue):
            raise SelectionActivationError(
                "WIP=1 violation: active prompt already exists"
            )

        dep_ok, reasons = _dependency_status(roadmap, step)
        if not dep_ok:
            raise SelectionActivationError(
                "dependency eligibility changed: " + ", ".join(reasons)
            )
        if step.get("status") not in {"planned", "ready"}:
            raise SelectionActivationError(
                "roadmap step is no longer activatable"
            )
        if (
            prompt.get("status") != "draft"
            or prompt.get("execution_status") != "planned"
            or prompt.get("dispatch_ready") is not True
        ):
            raise SelectionActivationError(
                "prompt is no longer dispatchable draft"
            )

        step["status"] = "active"
        roadmap_metadata = roadmap.setdefault("metadata", {})
        roadmap_metadata["current_step_id"] = identity["roadmap_step_id"]

        current_sequence = step.get("sequence")
        if not isinstance(current_sequence, int):
            raise SelectionActivationError(
                "activated roadmap step sequence is invalid"
            )
        roadmap_metadata["actionable_steps_after_current"] = sum(
            isinstance(item, dict)
            and isinstance(item.get("sequence"), int)
            and item["sequence"] > current_sequence
            and item.get("status") in {"active", "planned", "ready"}
            for item in roadmap["steps"]
        )

        workstream = roadmap_metadata.get("v0_4_workstream")
        if isinstance(workstream, dict):
            workstream["current_phase"] = identity["roadmap_step_id"]

        prompt["status"] = "approved"
        prompt["execution_status"] = "ready_for_module_pull"
        prompt["path"] = _relative(root, paths["approved"])
        prompt["activated_at"] = identity["activated_at"]

        queue.setdefault("metadata", {})[
            "active_prompt_id"
        ] = identity["prompt_id"]
        _recalculate_queue_counts(queue)

        paths["approved"].parent.mkdir(parents=True, exist_ok=True)
        paths["prompt"].rename(paths["approved"])
        _frontmatter_status(paths["approved"], "approved")

        health = _compute_health(roadmap, queue, health_policy)
        _update_handoff(
            handoff,
            roadmap,
            queue,
            health,
            activated_at=identity["activated_at"],
        )

        after = {
            "roadmap_current_step_id": (
                roadmap.get("metadata", {}).get("current_step_id")
            ),
            "roadmap_status": step.get("status"),
            "queue_active_prompt_id": (
                queue.get("metadata", {}).get("active_prompt_id")
            ),
            "queue_status": prompt.get("status"),
            "queue_execution_status": prompt.get("execution_status"),
            "prompt_path": prompt.get("path"),
            "health": health,
        }

        evidence = {
            "schema_version": ACTIVATION_EVIDENCE_SCHEMA,
            "activation_id": identity["activation_id"],
            "activation_identity_sha256": identity["identity_sha256"],
            "activated_at": identity["activated_at"],
            "selection": {
                "prompt_id": identity["prompt_id"],
                "roadmap_step_id": identity["roadmap_step_id"],
                "selection_fingerprint_sha256": identity[
                    "selection_fingerprint_sha256"
                ],
                "selection_source": identity["selection_source"],
            },
            "transaction": {
                "before": before,
                "after": after,
                "mutation_paths": plan["mutation_paths"],
                "selection_performed": True,
                "activation_performed": True,
                "wip_limit": 1,
                "dependency_eligibility_revalidated": True,
                "physical_prompt_move": "draft_to_approved",
                "exact_rollback_on_failure": True,
            },
            "boundaries": {
                "operator_decision_created": False,
                "automatic_acceptance": False,
                "automatic_return": False,
                "automatic_hold": False,
                "module_repository_writes": False,
                "tracking_events_reference_run": False,
                "dark_zone_audit_run": False,
                "global_v0_4_promotion_performed": False,
                "automatic_commit": False,
                "automatic_push": False,
                "rollout_or_production_write": False,
            },
            "result": "ACTIVATED",
        }

        write_yaml(paths["roadmap"], roadmap)
        write_yaml(paths["queue"], queue)
        write_yaml(paths["handoff"], handoff)
        write_yaml(paths["evidence"], evidence)

        if post_write_validator is not None:
            post_write_validator()

        if paths["prompt"].exists() or not paths["approved"].is_file():
            raise SelectionActivationError(
                "physical prompt activation transition failed"
            )

        return {
            "schema_version": ACTIVATION_EVIDENCE_SCHEMA,
            "result_state": "ACTIVATED",
            "activation_id": identity["activation_id"],
            "prompt_id": identity["prompt_id"],
            "roadmap_step_id": identity["roadmap_step_id"],
            "activation_evidence": _relative(root, paths["evidence"]),
            "selection_performed": True,
            "activation_performed": True,
            "idempotent_noop": False,
            "automatic_acceptance": False,
            "automatic_return": False,
            "automatic_hold": False,
            "module_repository_writes": False,
            "tracking_events_reference_run": False,
            "dark_zone_audit_run": False,
            "global_v0_4_promotion_performed": False,
            "automatic_commit": False,
            "automatic_push": False,
        }

    except Exception:
        _restore(snapshot)
        raise


def live_status(root: Path) -> dict[str, Any]:
    report = select_next_prompt(root)
    report["mode"] = "local_read_only"
    return report


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "ForPrint Next-Prompt Selection / Activation v0.4",
        f"result: {report.get('result_state')}",
    ]
    if "mode" in report:
        lines.append(f"mode: {report['mode']}")
    lines.extend(
        [
            (
                "active_prompt_count: "
                f"{report.get('active_prompt_count', 0)}"
            ),
            (
                "active_prompt_ids: "
                f"{report.get('active_prompt_ids', [])}"
            ),
            (
                "eligible_prompt_ids: "
                f"{report.get('eligible_prompt_ids', [])}"
            ),
            (
                "selected_prompt_id: "
                f"{(report.get('selected_prompt') or {}).get('prompt_id')}"
            ),
            (
                "selection_performed: "
                f"{str(report.get('selection_performed', False)).lower()}"
            ),
            (
                "activation_performed: "
                f"{str(report.get('activation_performed', False)).lower()}"
            ),
            (
                "automatic_acceptance: "
                f"{str(report.get('automatic_acceptance', False)).lower()}"
            ),
            (
                "automatic_return: "
                f"{str(report.get('automatic_return', False)).lower()}"
            ),
            (
                "automatic_hold: "
                f"{str(report.get('automatic_hold', False)).lower()}"
            ),
            (
                "tracking_events_reference_run: "
                f"{str(report.get('tracking_events_reference_run', False)).lower()}"
            ),
            (
                "dark_zone_audit_run: "
                f"{str(report.get('dark_zone_audit_run', False)).lower()}"
            ),
            (
                "global_v0_4_promotion_performed: "
                f"{str(report.get('global_v0_4_promotion_performed', False)).lower()}"
            ),
            (
                "module_repository_writes: "
                f"{str(report.get('module_repository_writes', False)).lower()}"
            ),
            (
                "automatic_commit: "
                f"{str(report.get('automatic_commit', False)).lower()}"
            ),
            (
                "automatic_push: "
                f"{str(report.get('automatic_push', False)).lower()}"
            ),
        ]
    )
    if report.get("error_code"):
        lines.append(f"error_code: {report['error_code']}")
    return "\n".join(lines)


def _emit(report: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
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
    parser.add_argument("--override-prompt-id")
    parser.add_argument("--request", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--activation-confirmation")
    parser.add_argument(
        "--output-format",
        choices=("text", "yaml", "json"),
        default="text",
    )
    args = parser.parse_args()

    root = args.root.resolve()

    if args.live_status or args.request is None:
        if args.apply:
            raise SelectionActivationError(
                "--apply requires --request"
            )
        report = select_next_prompt(
            root,
            override_prompt_id=args.override_prompt_id,
        )
        report["mode"] = "local_read_only"
        _emit(report, args.output_format)
        return 1 if report["result_state"] == "ATTENTION_REQUIRED" else 0

    request_path = args.request
    if not request_path.is_absolute():
        request_path = (root / request_path).resolve()
    try:
        request_path.relative_to(root)
    except ValueError as exc:
        raise SelectionActivationError(
            "request file must be inside Blueprint root"
        ) from exc

    request = load_yaml(request_path)
    if args.apply:
        if not args.activation_confirmation:
            raise SelectionActivationError(
                "--activation-confirmation is required for --apply"
            )
        report = apply_activation(
            root,
            request,
            activation_confirmation=args.activation_confirmation,
        )
    else:
        report = prepare_activation(root, request)

    _emit(report, args.output_format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
