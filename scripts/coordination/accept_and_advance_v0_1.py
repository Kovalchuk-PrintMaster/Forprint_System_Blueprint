#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination import manage_outgoing_prompt
from scripts.coordination import review_roadmap_queue_transaction_v0_4 as review_tx
from scripts.coordination.module_roadmap import (
    load_yaml_file,
    resolve_roadmap_path,
    validate_roadmap_document,
)
from scripts.coordination.resolve_next_module_work import (
    NextWorkError,
    resolve_next_work,
)
from scripts.coordination.resolve_next_module_work import (
    as_dict as next_work_as_dict,
)
from scripts.coordination.selection_policy_v0_1 import (
    roadmap_dependency_reasons,
)

REQUEST_SCHEMA = "blueprint_accept_and_advance_request_v0_1"
EVIDENCE_SCHEMA = "blueprint_accept_and_advance_evidence_v0_1"
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
ADVANCE_MODES = {"suggest_only", "release_explicit_prompt"}


class AcceptAndAdvanceError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise AcceptAndAdvanceError(
            f"cannot load YAML: {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise AcceptAndAdvanceError(f"expected YAML mapping: {path}")
    return data


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _atomic_write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _snapshot(paths: list[Path]) -> dict[Path, bytes | None]:
    return {
        path: path.read_bytes() if path.exists() else None
        for path in paths
    }


def _restore(snapshot: dict[Path, bytes | None]) -> None:
    for path, payload in snapshot.items():
        if payload is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)


def _safe_id(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or SAFE_ID.fullmatch(value) is None
    ):
        raise AcceptAndAdvanceError(
            f"{label} must be a safe non-empty id"
        )
    return value


def _identity(request: dict[str, Any]) -> dict[str, Any]:
    if request.get("schema_version") != REQUEST_SCHEMA:
        raise AcceptAndAdvanceError("request schema mismatch")

    operation_id = _safe_id(
        request.get("operation_id"),
        "operation_id",
    )
    operated_at = request.get("operated_at")
    if not isinstance(operated_at, str) or not operated_at:
        raise AcceptAndAdvanceError("operated_at is required")
    if request.get("explicit_operator_input") is not True:
        raise AcceptAndAdvanceError(
            "explicit_operator_input=true is required"
        )

    review = request.get("review_transaction")
    if not isinstance(review, dict):
        raise AcceptAndAdvanceError(
            "review_transaction must be a mapping"
        )
    decision = review.get("decision")
    candidate = review.get("review_candidate")
    if not isinstance(decision, dict):
        raise AcceptAndAdvanceError(
            "review_transaction.decision must be a mapping"
        )
    if not isinstance(candidate, dict):
        raise AcceptAndAdvanceError(
            "review_transaction.review_candidate must be a mapping"
        )
    if decision.get("operator_decision") != "ACCEPT":
        raise AcceptAndAdvanceError(
            "ACCEPT_AND_ADVANCE only accepts an explicit ACCEPT decision"
        )
    if decision.get("explicit_operator_input") is not True:
        raise AcceptAndAdvanceError(
            "nested review decision must have explicit_operator_input=true"
        )

    decision_id = _safe_id(
        decision.get("decision_id"),
        "review decision_id",
    )
    module_id = _safe_id(
        candidate.get("module_id"),
        "review module_id",
    )
    if module_id == "forprint_system_blueprint":
        raise AcceptAndAdvanceError(
            "H5 module ACCEPT_AND_ADVANCE does not replace self-coordination "
            "selection/activation"
        )

    advance = request.get("advance")
    if not isinstance(advance, dict):
        raise AcceptAndAdvanceError("advance must be a mapping")
    mode = advance.get("mode")
    if mode not in ADVANCE_MODES:
        raise AcceptAndAdvanceError(
            f"advance.mode must be one of {sorted(ADVANCE_MODES)}"
        )

    expected_prompt_id = None
    expected_step_id = None
    if mode == "release_explicit_prompt":
        if advance.get("explicit_operator_input") is not True:
            raise AcceptAndAdvanceError(
                "release_explicit_prompt requires "
                "advance.explicit_operator_input=true"
            )
        expected_prompt_id = _safe_id(
            advance.get("expected_prompt_id"),
            "advance.expected_prompt_id",
        )
        expected_step_id = _safe_id(
            advance.get("expected_roadmap_step_id"),
            "advance.expected_roadmap_step_id",
        )

    return {
        "operation_id": operation_id,
        "operated_at": operated_at,
        "module_id": module_id,
        "decision_id": decision_id,
        "review_request": copy.deepcopy(review),
        "advance_mode": mode,
        "expected_prompt_id": expected_prompt_id,
        "expected_step_id": expected_step_id,
        "request_fingerprint_sha256": canonical_sha256(request),
    }


def _evidence_path(root: Path, operation_id: str) -> Path:
    return (
        root
        / "coordination/internal_work/blueprint/governance/"
        "accept_and_advance"
        / f"{operation_id}.yaml"
    )


def _existing_evidence(
    root: Path,
    identity: dict[str, Any],
) -> dict[str, Any] | None:
    path = _evidence_path(root, identity["operation_id"])
    if not path.is_file():
        return None
    evidence = load_yaml(path)
    if (
        evidence.get("request_fingerprint_sha256")
        != identity["request_fingerprint_sha256"]
    ):
        raise AcceptAndAdvanceError(
            "operation_id already exists with a different request identity"
        )
    return evidence


def _queue_path(root: Path, module: str) -> Path:
    return root / "coordination/outgoing_prompts" / module / "index.yaml"


def _unresolved_queue_records(
    root: Path,
    module: str,
) -> list[dict[str, Any]]:
    queue = load_yaml(_queue_path(root, module))
    if queue.get("schema_version") != "prompt_queue_v0_2":
        raise AcceptAndAdvanceError(
            "H5 advance requires Prompt Queue v0.2"
        )
    rows = queue.get("prompt_queue")
    if not isinstance(rows, list):
        raise AcceptAndAdvanceError("prompt_queue must be a list")

    unresolved: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        execution = item.get("module_execution")
        review = item.get("blueprint_review")
        execution_status = (
            execution.get("status")
            if isinstance(execution, dict)
            else None
        )
        review_status = (
            review.get("status")
            if isinstance(review, dict)
            else None
        )
        if execution_status == "superseded":
            continue
        if review_status == "accepted_by_blueprint":
            continue
        unresolved.append(
            {
                "prompt_id": item.get("prompt_id"),
                "module_execution_status": execution_status,
                "blueprint_review_status": review_status,
            }
        )
    return unresolved


def _next_work(
    root: Path,
    module: str,
    *,
    override_step_id: str | None = None,
) -> dict[str, Any]:
    try:
        suggestion = resolve_next_work(
            root=root,
            module=module,
            override_step_id=override_step_id,
        )
    except NextWorkError as exc:
        raise AcceptAndAdvanceError(
            f"next-work resolution failed: {exc}"
        ) from exc
    return next_work_as_dict(suggestion, root=root)


def _advance_snapshot_paths(
    root: Path,
    identity: dict[str, Any],
    next_work: dict[str, Any],
) -> list[Path]:
    candidates = next_work.get("draft_candidates")
    if not isinstance(candidates, list) or len(candidates) != 1:
        return []

    raw_candidate = candidates[0]
    if not isinstance(raw_candidate, str) or not raw_candidate:
        return []

    root = root.resolve()
    candidate = (root / raw_candidate).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise AcceptAndAdvanceError(
            "next-work draft candidate escapes Blueprint root"
        ) from exc

    approved = (
        candidate.parent.parent
        / "approved"
        / candidate.name
    ).resolve()

    return [
        resolve_roadmap_path(
            root=root,
            module=identity["module_id"],
        ),
        _queue_path(root, identity["module_id"]),
        candidate,
        approved,
        _evidence_path(root, identity["operation_id"]),
    ]


def _activate_roadmap_step(
    *,
    root: Path,
    module: str,
    step_id: str,
    release_result: manage_outgoing_prompt.OperationResult,
    operated_at: str,
) -> None:
    roadmap_path = resolve_roadmap_path(root=root, module=module)
    roadmap = load_yaml_file(roadmap_path)
    rows = roadmap.get("roadmap")
    if not isinstance(rows, list):
        raise AcceptAndAdvanceError(
            "module roadmap must contain roadmap list"
        )

    matches = [
        item
        for item in rows
        if isinstance(item, dict)
        and item.get("step_id") == step_id
    ]
    if len(matches) != 1:
        raise AcceptAndAdvanceError(
            f"expected one roadmap step {step_id!r}, got {len(matches)}"
        )
    step = matches[0]
    if step.get("status") not in {"planned", "ready"}:
        raise AcceptAndAdvanceError(
            "explicit next roadmap step is no longer activatable"
        )

    reasons = roadmap_dependency_reasons(
        roadmap_module=module,
        steps=rows,
        step=step,
    )
    if reasons:
        raise AcceptAndAdvanceError(
            "dependency eligibility failed: " + ", ".join(reasons)
        )

    step["status"] = "active"
    prompt_binding = step.get("prompt")
    if isinstance(prompt_binding, dict):
        prompt_binding["prompt_id"] = release_result.prompt_id
        prompt_binding["prompt_file"] = release_result.destination
        prompt_binding["prompt_queue_sequence"] = release_result.sequence
    else:
        step["prompt_id"] = release_result.prompt_id
        step["prompt_file"] = release_result.destination
        step["prompt_queue_sequence"] = release_result.sequence

    metadata = roadmap.setdefault("metadata", {})
    metadata["current_step_id"] = step_id
    metadata["updated_at"] = operated_at[:10]

    planning = metadata.get("planning_horizon")
    if isinstance(planning, dict):
        planning["current_ready_step"] = step_id

    roadmap_path.write_text(
        yaml.safe_dump(
            roadmap,
            sort_keys=False,
            allow_unicode=True,
            width=100,
        ),
        encoding="utf-8",
    )

    validation = validate_roadmap_document(
        roadmap,
        path=roadmap_path,
    )
    if validation.errors:
        raise AcceptAndAdvanceError(
            "activated roadmap became invalid: "
            + "; ".join(validation.errors)
        )


def _blocked_result(
    *,
    identity: dict[str, Any],
    review_result: dict[str, Any],
    next_work: dict[str, Any],
    code: str,
    detail: str,
) -> dict[str, Any]:
    return {
        "schema_version": EVIDENCE_SCHEMA,
        "result_state": "ACCEPT_APPLIED_ADVANCE_BLOCKED",
        "operation_id": identity["operation_id"],
        "module_id": identity["module_id"],
        "review_result": copy.deepcopy(review_result),
        "advance": {
            "mode": identity["advance_mode"],
            "result": "BLOCKED",
            "code": code,
            "detail": detail,
            "next_work": copy.deepcopy(next_work),
        },
        "compound_evidence_written": False,
        "retry_safe": True,
        "automatic_acceptance": False,
        "automatic_selection": False,
        "automatic_activation": False,
        "module_repository_writes": False,
        "automatic_commit": False,
        "automatic_push": False,
    }


def prepare_operation(
    root: Path,
    request: dict[str, Any],
) -> dict[str, Any]:
    root = root.resolve()
    identity = _identity(request)

    existing = _existing_evidence(root, identity)
    if existing is not None:
        return {
            "schema_version": EVIDENCE_SCHEMA,
            "result_state": "ALREADY_APPLIED",
            "operation_id": identity["operation_id"],
            "idempotent_noop": True,
            "evidence_path": str(
                _evidence_path(root, identity["operation_id"]).relative_to(root)
            ),
        }

    review_plan = review_tx.prepare_transaction(
        root,
        identity["review_request"],
    )

    next_work = None
    advance_preview_state = "AFTER_ACCEPT_REEVALUATION_REQUIRED"
    if review_plan.get("result_state") == "ALREADY_APPLIED":
        override_step_id = (
            identity["expected_step_id"]
            if identity["advance_mode"] == "release_explicit_prompt"
            else None
        )
        next_work = _next_work(
            root,
            identity["module_id"],
            override_step_id=override_step_id,
        )
        advance_preview_state = "CURRENT_ACCEPTED_STATE_RESOLVED"

    return {
        "schema_version": REQUEST_SCHEMA,
        "result_state": "READY_TO_APPLY",
        "operation_id": identity["operation_id"],
        "module_id": identity["module_id"],
        "review_plan": review_plan,
        "advance": {
            "mode": identity["advance_mode"],
            "expected_prompt_id": identity["expected_prompt_id"],
            "expected_roadmap_step_id": identity["expected_step_id"],
            "preview_state": advance_preview_state,
            "next_work": next_work,
        },
        "boundaries": {
            "explicit_accept_required": True,
            "explicit_compound_confirmation_required": True,
            "release_policy_bypass": False,
            "automatic_selection": False,
            "h6_ranking_changes": False,
            "wip_limit": 1,
            "module_repository_writes": False,
            "automatic_commit": False,
            "automatic_push": False,
        },
    }


def _perform_explicit_release(
    *,
    root: Path,
    identity: dict[str, Any],
    review_result: dict[str, Any],
    next_work: dict[str, Any],
) -> dict[str, Any]:
    try:
        next_work = _next_work(
            root,
            identity["module_id"],
            override_step_id=identity["expected_step_id"],
        )
    except AcceptAndAdvanceError as exc:
        return _blocked_result(
            identity=identity,
            review_result=review_result,
            next_work=next_work,
            code="EXPLICIT_OVERRIDE_NOT_ELIGIBLE",
            detail=str(exc),
        )

    unresolved = _unresolved_queue_records(
        root,
        identity["module_id"],
    )
    if unresolved:
        return _blocked_result(
            identity=identity,
            review_result=review_result,
            next_work=next_work,
            code="UNRESOLVED_PROMPT_EXISTS",
            detail=json.dumps(unresolved, ensure_ascii=False),
        )

    if next_work.get("result") != "DRAFT_CANDIDATE_FOUND":
        return _blocked_result(
            identity=identity,
            review_result=review_result,
            next_work=next_work,
            code="NEXT_WORK_NOT_SINGLE_DRAFT",
            detail=str(next_work.get("result")),
        )

    next_step = next_work.get("next_step")
    if not isinstance(next_step, dict):
        return _blocked_result(
            identity=identity,
            review_result=review_result,
            next_work=next_work,
            code="NEXT_STEP_MISSING",
            detail="next-work projection has no next_step",
        )
    if next_step.get("step_id") != identity["expected_step_id"]:
        return _blocked_result(
            identity=identity,
            review_result=review_result,
            next_work=next_work,
            code="EXPECTED_STEP_MISMATCH",
            detail=(
                f"expected={identity['expected_step_id']} "
                f"actual={next_step.get('step_id')}"
            ),
        )

    candidates = next_work.get("draft_candidates")
    if not isinstance(candidates, list) or len(candidates) != 1:
        return _blocked_result(
            identity=identity,
            review_result=review_result,
            next_work=next_work,
            code="DRAFT_CARDINALITY_INVALID",
            detail=f"draft_candidates={candidates!r}",
        )

    try:
        preview = manage_outgoing_prompt.release_prompt(
            root=root,
            module=identity["module_id"],
            prompt_id=identity["expected_prompt_id"],
            apply=False,
        )
    except manage_outgoing_prompt.WorkflowError as exc:
        return _blocked_result(
            identity=identity,
            review_result=review_result,
            next_work=next_work,
            code="RELEASE_POLICY_OR_WORKFLOW_BLOCKED",
            detail=str(exc),
        )

    candidate_path = (root / candidates[0]).resolve()
    preview_source = (
        (root / preview.source).resolve()
        if preview.source is not None
        else None
    )
    if preview_source != candidate_path:
        return _blocked_result(
            identity=identity,
            review_result=review_result,
            next_work=next_work,
            code="EXPECTED_PROMPT_MISMATCH",
            detail=(
                f"resolver_candidate={candidate_path} "
                f"release_source={preview_source}"
            ),
        )

    roadmap_path = resolve_roadmap_path(
        root=root,
        module=identity["module_id"],
    )
    queue_path = _queue_path(root, identity["module_id"])
    approved_path = (
        root / preview.destination
        if preview.destination is not None
        else None
    )
    if approved_path is None:
        raise AcceptAndAdvanceError(
            "release preview did not provide destination"
        )

    advance_snapshot = _snapshot(
        [
            roadmap_path,
            queue_path,
            candidate_path,
            approved_path,
        ]
    )

    try:
        release_result = manage_outgoing_prompt.release_prompt(
            root=root,
            module=identity["module_id"],
            prompt_id=identity["expected_prompt_id"],
            apply=True,
        )
        _activate_roadmap_step(
            root=root,
            module=identity["module_id"],
            step_id=identity["expected_step_id"],
            release_result=release_result,
            operated_at=identity["operated_at"],
        )

        unresolved_after = _unresolved_queue_records(
            root,
            identity["module_id"],
        )
        if len(unresolved_after) != 1:
            raise AcceptAndAdvanceError(
                "WIP=1 postcondition failed: "
                f"unresolved_count={len(unresolved_after)}"
            )
        active = unresolved_after[0]
        if (
            active.get("prompt_id") != identity["expected_prompt_id"]
            or active.get("module_execution_status")
            != "ready_for_module_pull"
        ):
            raise AcceptAndAdvanceError(
                "WIP=1 postcondition does not point to released prompt"
            )

        next_after = _next_work(root, identity["module_id"])
        return {
            "release_result": asdict(release_result),
            "next_work_after": next_after,
            "selection_source": "explicit_operator_bound_candidate",
            "next_prompt_selection_performed": True,
            "next_prompt_activation_performed": True,
            "wip_limit": 1,
            "dependency_eligibility_revalidated": True,
            "advance_rollback_scope": [
                str(path.relative_to(root))
                for path in advance_snapshot
            ],
        }
    except Exception:
        _restore(advance_snapshot)
        raise


def apply_operation(
    root: Path,
    request: dict[str, Any],
    *,
    operator_confirmation: str,
) -> dict[str, Any]:
    root = root.resolve()
    identity = _identity(request)

    if operator_confirmation != identity["operation_id"]:
        raise AcceptAndAdvanceError(
            "operator_confirmation must exactly match operation_id"
        )

    existing = _existing_evidence(root, identity)
    if existing is not None:
        return {
            "schema_version": EVIDENCE_SCHEMA,
            "result_state": "ALREADY_APPLIED",
            "operation_id": identity["operation_id"],
            "idempotent_noop": True,
            "evidence_path": str(
                _evidence_path(root, identity["operation_id"]).relative_to(root)
            ),
        }

    review_result = review_tx.apply_transaction(
        root,
        identity["review_request"],
        operator_confirmation=identity["decision_id"],
    )
    if review_result.get("result_state") not in {
        "ACCEPT_APPLIED",
        "ALREADY_APPLIED",
    }:
        raise AcceptAndAdvanceError(
            "nested ACCEPT transaction did not reach accepted state"
        )

    if identity["advance_mode"] == "release_explicit_prompt":
        try:
            next_work = _next_work(
                root,
                identity["module_id"],
                override_step_id=identity["expected_step_id"],
            )
        except AcceptAndAdvanceError as exc:
            fallback_next_work = _next_work(
                root,
                identity["module_id"],
            )
            return _blocked_result(
                identity=identity,
                review_result=review_result,
                next_work=fallback_next_work,
                code="EXPLICIT_OVERRIDE_NOT_ELIGIBLE",
                detail=str(exc),
            )
    else:
        next_work = _next_work(root, identity["module_id"])

    advance_result: dict[str, Any]
    advance_snapshot: dict[Path, bytes | None] | None = None
    if identity["advance_mode"] == "suggest_only":
        advance_result = {
            "mode": "suggest_only",
            "result": "SUGGESTED",
            "next_work": next_work,
            "next_prompt_selection_performed": False,
            "next_prompt_activation_performed": False,
        }
    else:
        snapshot_paths = _advance_snapshot_paths(
            root,
            identity,
            next_work,
        )
        if snapshot_paths:
            advance_snapshot = _snapshot(snapshot_paths)

        try:
            release = _perform_explicit_release(
                root=root,
                identity=identity,
                review_result=review_result,
                next_work=next_work,
            )
        except Exception as exc:
            return _blocked_result(
                identity=identity,
                review_result=review_result,
                next_work=next_work,
                code="ADVANCE_TRANSACTION_FAILED",
                detail=str(exc),
            )

        if release.get("result_state") == "ACCEPT_APPLIED_ADVANCE_BLOCKED":
            return release

        advance_result = {
            "mode": "release_explicit_prompt",
            "result": "ACTIVATED",
            "expected_prompt_id": identity["expected_prompt_id"],
            "expected_roadmap_step_id": identity["expected_step_id"],
            **release,
        }

    evidence = {
        "schema_version": EVIDENCE_SCHEMA,
        "operation_id": identity["operation_id"],
        "request_fingerprint_sha256": identity[
            "request_fingerprint_sha256"
        ],
        "operated_at": identity["operated_at"],
        "subject": {
            "module_id": identity["module_id"],
            "accepted_prompt_id": identity["review_request"][
                "review_candidate"
            ].get("prompt_id"),
            "review_decision_id": identity["decision_id"],
        },
        "review_result": copy.deepcopy(review_result),
        "advance": copy.deepcopy(advance_result),
        "semantics": {
            "accept_is_explicit_operator_decision": True,
            "advance_is_optional": True,
            "release_requires_existing_authorization_policy": True,
            "blocked_advance_does_not_rollback_accept": True,
            "release_mode_uses_explicit_expected_ids": True,
            "h6_default_ranking_not_implemented_here": True,
            "wip_limit": 1,
        },
        "boundaries": {
            "automatic_acceptance": False,
            "automatic_return": False,
            "automatic_hold": False,
            "automatic_selection": False,
            "release_policy_bypass": False,
            "module_repository_writes": False,
            "network_required": False,
            "automatic_commit": False,
            "automatic_push": False,
            "global_promotion": False,
        },
        "result": (
            "ACCEPTED_AND_ADVANCED"
            if identity["advance_mode"] == "release_explicit_prompt"
            else "ACCEPTED_AND_SUGGESTED"
        ),
    }

    evidence_path = _evidence_path(root, identity["operation_id"])
    try:
        _atomic_write_yaml(evidence_path, evidence)
    except Exception as exc:
        if advance_snapshot is not None:
            _restore(advance_snapshot)
        return _blocked_result(
            identity=identity,
            review_result=review_result,
            next_work=next_work,
            code="COMPOUND_EVIDENCE_WRITE_FAILED",
            detail=str(exc),
        )

    return {
        "schema_version": EVIDENCE_SCHEMA,
        "result_state": (
            "ACCEPT_AND_ADVANCE_APPLIED"
            if identity["advance_mode"] == "release_explicit_prompt"
            else "ACCEPT_AND_SUGGEST_APPLIED"
        ),
        "operation_id": identity["operation_id"],
        "module_id": identity["module_id"],
        "review_result": review_result,
        "advance": advance_result,
        "evidence_path": str(evidence_path.relative_to(root)),
        "idempotent_noop": False,
        "automatic_acceptance": False,
        "automatic_selection": False,
        "module_repository_writes": False,
        "automatic_commit": False,
        "automatic_push": False,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "ForPrint ACCEPT_AND_ADVANCE v0.1",
        f"result: {report.get('result_state')}",
        f"operation_id: {report.get('operation_id', '-')}",
    ]
    if "module_id" in report:
        lines.append(f"module: {report['module_id']}")
    review = report.get("review_result")
    if isinstance(review, dict):
        lines.append(
            f"review_result: {review.get('result_state', '-')}"
        )
    advance = report.get("advance")
    if isinstance(advance, dict):
        lines.append(f"advance_mode: {advance.get('mode', '-')}")
        lines.append(
            f"advance_result: {advance.get('result', '-')}"
        )
        if advance.get("code"):
            lines.append(f"advance_code: {advance['code']}")
        if advance.get("detail"):
            lines.append(f"advance_detail: {advance['detail']}")
    if "evidence_path" in report:
        lines.append(f"evidence: {report['evidence_path']}")
    lines.extend(
        [
            "automatic_acceptance: false",
            "automatic_selection: false",
            "module_repository_writes: false",
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
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
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
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--operator-confirmation")
    parser.add_argument(
        "--output-format",
        choices=("text", "yaml", "json"),
        default="text",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    request_path = args.request
    if not request_path.is_absolute():
        request_path = (root / request_path).resolve()
    try:
        request_path.relative_to(root)
    except ValueError as exc:
        raise AcceptAndAdvanceError(
            "request path must stay inside Blueprint root"
        ) from exc

    request = load_yaml(request_path)

    try:
        if args.apply:
            if not args.operator_confirmation:
                raise AcceptAndAdvanceError(
                    "--apply requires --operator-confirmation"
                )
            report = apply_operation(
                root,
                request,
                operator_confirmation=args.operator_confirmation,
            )
        else:
            report = prepare_operation(root, request)
    except (
        AcceptAndAdvanceError,
        review_tx.TransactionError,
    ) as exc:
        print(f"FAILED: {exc}")
        return 2

    _emit(report, args.output_format)
    return (
        2
        if report.get("result_state")
        == "ACCEPT_APPLIED_ADVANCE_BLOCKED"
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
