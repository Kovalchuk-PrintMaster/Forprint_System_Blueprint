from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

DECISION_SCHEMA = "forprint_operator_approval_decision_v0_1"
INPUT_SCHEMA = "forprint_operator_approval_input_v0_1"
LAUNCH_REQUEST_SCHEMA = "forprint_launch_request_v0_1"

DECISIONS = ("APPROVE", "HOLD", "REJECT")
TRANSPORTS = ("FILESYSTEM", "CLI")
STATE_AWAITING_APPROVAL = "AWAITING_OPERATOR_APPROVAL"

EVAL_OK = "OK"
EVAL_INVALID = "INVALID"

INVALID_LAUNCH_REQUEST = "LAUNCH_REQUEST_INVALID"
REQUEST_REVALIDATION_FAILED = "LAUNCH_REQUEST_REVALIDATION_FAILED"
REQUEST_ID_DRIFT = "LAUNCH_REQUEST_ID_DRIFT"
REQUEST_FINGERPRINT_DRIFT = "LAUNCH_REQUEST_FINGERPRINT_DRIFT"
LAUNCH_REQUEST_SHA_DRIFT = "LAUNCH_REQUEST_SHA_DRIFT"
DECISION_NOT_APPROVE = "DECISION_NOT_APPROVE"
APPROVAL_EXPIRED = "APPROVAL_EXPIRED"
DECISION_BINDING_DRIFT = "DECISION_BINDING_DRIFT"


@dataclass(frozen=True)
class GatewayEvaluation:
    status: str
    request_id: str | None
    current_state: str | None
    allowed_decisions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    current_launch_request: dict[str, Any] | None


@dataclass(frozen=True)
class DispatchApprovalValidation:
    valid: bool
    reason_codes: tuple[str, ...]
    decision_id: str | None


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_yaml_mapping(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{label} is missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a YAML mapping: {path}")
    return data


def _nested(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _load_launch_gate(root: Path):
    gate_path = root / Path("scripts") / "coordination" / "build_launch_request.py"
    if not gate_path.is_file():
        raise ValueError(f"launch-request gate is missing: {gate_path}")
    spec = importlib.util.spec_from_file_location(
        "forprint_launch_request_gate_runtime",
        gate_path,
    )
    if spec is None or spec.loader is None:
        raise ValueError("launch-request gate import spec could not be created")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def _resolve_bound_path(raw: Any, *, root: Path, label: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"{label} path is missing")
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _revalidate_launch_request(
    *,
    root: Path,
    module_root: Path,
    launch_request: dict[str, Any],
) -> dict[str, Any]:
    gate = _load_launch_gate(root)
    task_context_archive = _resolve_bound_path(
        _nested(launch_request, "task_context", "archive_path"),
        root=root,
        label="task-context archive",
    )
    dependency_raw = _nested(
        launch_request,
        "dependency_readiness",
        "path",
    )
    dependency_path = (
        _resolve_bound_path(
            dependency_raw,
            root=root,
            label="dependency-readiness snapshot",
        )
        if dependency_raw
        else None
    )
    current = gate.build_launch_request(
        root=root,
        module_root=module_root,
        task_context_archive=task_context_archive,
        dependency_readiness_path=dependency_path,
    )
    if not isinstance(current.document, dict):
        raise ValueError("launch-request revalidation returned an invalid document")
    return current.document


def _validate_launch_request_shape(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("schema_version") != LAUNCH_REQUEST_SCHEMA:
        errors.append("unsupported launch-request schema")
    for path in (
        ("request_id",),
        ("state",),
        ("identity", "module_id"),
        ("identity", "prompt_id"),
        ("identity", "task_context_id"),
        ("identity", "context_fingerprint_sha256"),
        ("identity", "request_fingerprint_sha256"),
        ("task_context", "archive_path"),
        ("task_context", "archive_sha256"),
        ("repository_revalidation", "blueprint_head"),
        ("repository_revalidation", "module_head"),
    ):
        if not _nested(document, *path):
            errors.append("missing:" + ".".join(path))
    return errors


def evaluate_gateway(
    *,
    root: Path,
    module_root: Path,
    launch_request_path: Path,
) -> GatewayEvaluation:
    root = root.resolve()
    module_root = module_root.resolve()
    launch_request_path = launch_request_path.resolve()

    try:
        original = _load_yaml_mapping(
            launch_request_path,
            label="launch request",
        )
    except Exception as exc:
        return GatewayEvaluation(
            status=EVAL_INVALID,
            request_id=None,
            current_state=None,
            allowed_decisions=(),
            reason_codes=(f"{INVALID_LAUNCH_REQUEST}:{exc}",),
            current_launch_request=None,
        )

    shape_errors = _validate_launch_request_shape(original)
    if shape_errors:
        return GatewayEvaluation(
            status=EVAL_INVALID,
            request_id=original.get("request_id"),
            current_state=original.get("state"),
            allowed_decisions=(),
            reason_codes=tuple(
                f"{INVALID_LAUNCH_REQUEST}:{item}" for item in shape_errors
            ),
            current_launch_request=None,
        )

    try:
        current = _revalidate_launch_request(
            root=root,
            module_root=module_root,
            launch_request=original,
        )
    except Exception as exc:
        return GatewayEvaluation(
            status=EVAL_INVALID,
            request_id=original.get("request_id"),
            current_state=original.get("state"),
            allowed_decisions=(),
            reason_codes=(f"{REQUEST_REVALIDATION_FAILED}:{exc}",),
            current_launch_request=None,
        )

    reasons: list[str] = []
    if current.get("request_id") != original.get("request_id"):
        reasons.append(REQUEST_ID_DRIFT)
    if _nested(
        current,
        "identity",
        "request_fingerprint_sha256",
    ) != _nested(
        original,
        "identity",
        "request_fingerprint_sha256",
    ):
        reasons.append(REQUEST_FINGERPRINT_DRIFT)

    if reasons:
        return GatewayEvaluation(
            status=EVAL_INVALID,
            request_id=original.get("request_id"),
            current_state=current.get("state"),
            allowed_decisions=(),
            reason_codes=tuple(sorted(set(reasons))),
            current_launch_request=current,
        )

    current_state = current.get("state")
    if current_state == STATE_AWAITING_APPROVAL:
        allowed = ("APPROVE", "HOLD", "REJECT")
    else:
        allowed = ("HOLD", "REJECT")

    return GatewayEvaluation(
        status=EVAL_OK,
        request_id=original.get("request_id"),
        current_state=current_state,
        allowed_decisions=allowed,
        reason_codes=(),
        current_launch_request=current,
    )


def _load_decision_input(path: Path) -> dict[str, Any]:
    data = _load_yaml_mapping(path, label="operator approval input")
    if data.get("schema_version") != INPUT_SCHEMA:
        raise ValueError("operator approval input schema is unsupported")
    return data


def build_operator_decision(
    *,
    root: Path,
    module_root: Path,
    launch_request_path: Path,
    decision: str,
    decided_by: str,
    reason: str,
    transport: str = "CLI",
    expires_in_minutes: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    decision = decision.upper().strip()
    transport = transport.upper().strip()
    if decision not in DECISIONS:
        raise ValueError(f"unsupported decision: {decision}")
    if transport not in TRANSPORTS:
        raise ValueError(f"unsupported transport: {transport}")
    if not decided_by.strip():
        raise ValueError("decided_by must be non-empty")
    if not reason.strip():
        raise ValueError("reason must be non-empty")

    evaluation = evaluate_gateway(
        root=root,
        module_root=module_root,
        launch_request_path=launch_request_path,
    )
    if evaluation.status != EVAL_OK:
        raise ValueError(
            "launch request is not decision-eligible: "
            + ",".join(evaluation.reason_codes)
        )
    if decision not in evaluation.allowed_decisions:
        raise PermissionError(
            f"decision {decision} is not allowed while request state is "
            f"{evaluation.current_state}"
        )

    original = _load_yaml_mapping(
        launch_request_path.resolve(),
        label="launch request",
    )
    current = evaluation.current_launch_request
    if not isinstance(current, dict):
        raise ValueError("current launch request is missing after revalidation")

    decided_at = now or datetime.now(UTC)
    if decided_at.tzinfo is None:
        raise ValueError("decision time must be timezone-aware")
    decided_at = decided_at.astimezone(UTC)

    if decision == "APPROVE":
        ttl = 30 if expires_in_minutes is None else expires_in_minutes
        if ttl <= 0 or ttl > 1440:
            raise ValueError("APPROVE expiry must be between 1 and 1440 minutes")
        expires_at: str | None = (
            decided_at + timedelta(minutes=ttl)
        ).isoformat()
    else:
        expires_at = None

    launch_sha = _sha256_path(launch_request_path.resolve())
    request_id = str(original["request_id"])
    request_fingerprint = str(
        _nested(original, "identity", "request_fingerprint_sha256")
    )
    stable = {
        "request_id": request_id,
        "request_fingerprint_sha256": request_fingerprint,
        "launch_request_sha256": launch_sha,
        "decision": decision,
        "decided_by": decided_by.strip(),
        "decided_at": decided_at.isoformat(),
        "transport": transport,
    }
    decision_digest = hashlib.sha256(
        json.dumps(
            stable,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    decision_id = f"{request_id}__{decision.lower()}__{decision_digest[:16]}"

    module_id = _nested(original, "identity", "module_id")
    prompt_id = _nested(original, "identity", "prompt_id")
    task_context_id = _nested(original, "identity", "task_context_id")
    context_fingerprint = _nested(
        original,
        "identity",
        "context_fingerprint_sha256",
    )
    blueprint_head = _nested(
        original,
        "repository_revalidation",
        "blueprint_head",
    )
    module_head = _nested(
        original,
        "repository_revalidation",
        "module_head",
    )
    dependency_sha = _nested(
        original,
        "dependency_readiness",
        "sha256",
    )

    return {
        "schema_version": DECISION_SCHEMA,
        "decision_id": decision_id,
        "request_id": request_id,
        "request_fingerprint_sha256": request_fingerprint,
        "launch_request_sha256": launch_sha,
        "module_id": module_id,
        "prompt_id": prompt_id,
        "task_context_id": task_context_id,
        "task_context_fingerprint_sha256": context_fingerprint,
        "blueprint_head": blueprint_head,
        "module_head": module_head,
        "dependency_readiness_sha256": dependency_sha,
        "decision": decision,
        "decided_by": decided_by.strip(),
        "decided_at": decided_at.isoformat(),
        "expires_at": expires_at,
        "transport": transport,
        "reason": reason.strip(),
        "authority": {
            "human_operator_decision": True,
            "eligible_as_future_worker_dispatch_authority": decision == "APPROVE",
            "direct_worker_dispatch_allowed_by_gateway": False,
            "blueprint_accept": False,
            "prompt_claim": False,
            "next_prompt_release": False,
        },
        "revalidation": {
            "performed_immediately_before_decision": True,
            "launch_request_state": evaluation.current_state,
            "request_id_match": True,
            "request_fingerprint_match": True,
            "current_blueprint_head": _nested(
                current,
                "repository_revalidation",
                "blueprint_head",
            ),
            "current_module_head": _nested(
                current,
                "repository_revalidation",
                "module_head",
            ),
            "current_fresh_context_state": _nested(
                current,
                "repository_revalidation",
                "fresh_context_state",
            ),
            "current_unclassified_dirty_paths": _nested(
                current,
                "repository_revalidation",
                "unclassified_dirty_paths",
            ),
            "current_dependency_readiness_status": _nested(
                current,
                "dependency_readiness",
                "status",
            ),
        },
        "governance_alignment": {
            "q4_artifact_type": "operator_decision",
            "q4_manual_authority_preserved": True,
            "q4_execution_effect": (
                "resume_affected_scope"
                if decision == "APPROVE"
                else "no_execution_change"
            ),
            "q4_acceptance_effect": "no_acceptance_change",
            "q5_event_family": "operator_decision",
            "q5_event_emission": "DEFERRED_TO_EVENT_RUNTIME",
            "q6_attention_reason": (
                "operator_acceptance_required"
                if evaluation.current_state == STATE_AWAITING_APPROVAL
                else "dependency_blocked"
            ),
            "q6_attention_is_decision": False,
            "phase_boundary_approval_conflated": False,
        },
        "evidence_refs": [
            str(launch_request_path.resolve()),
            str(
                _nested(
                    original,
                    "task_context",
                    "archive_path",
                )
            ),
        ],
    }


def write_operator_decision(
    *,
    document: dict[str, Any],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    decided_at = datetime.fromisoformat(str(document["decided_at"]))
    stamp = decided_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"{document['decision_id']}__{stamp}.yaml"
    if path.exists():
        raise ValueError(f"operator decision artifact already exists: {path}")
    path.write_text(
        yaml.safe_dump(
            document,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )
    return path


def validate_approval_for_dispatch(
    *,
    root: Path,
    module_root: Path,
    launch_request_path: Path,
    decision_path: Path,
    now: datetime | None = None,
) -> DispatchApprovalValidation:
    reasons: list[str] = []
    try:
        decision = _load_yaml_mapping(
            decision_path.resolve(),
            label="operator approval decision",
        )
        launch_request = _load_yaml_mapping(
            launch_request_path.resolve(),
            label="launch request",
        )
    except Exception as exc:
        return DispatchApprovalValidation(
            valid=False,
            reason_codes=(f"{DECISION_BINDING_DRIFT}:{exc}",),
            decision_id=None,
        )

    decision_id = decision.get("decision_id")
    if decision.get("schema_version") != DECISION_SCHEMA:
        reasons.append(DECISION_BINDING_DRIFT)
    if decision.get("decision") != "APPROVE":
        reasons.append(DECISION_NOT_APPROVE)
    if decision.get("launch_request_sha256") != _sha256_path(
        launch_request_path.resolve()
    ):
        reasons.append(LAUNCH_REQUEST_SHA_DRIFT)
    if decision.get("request_id") != launch_request.get("request_id"):
        reasons.append(DECISION_BINDING_DRIFT)
    if decision.get("request_fingerprint_sha256") != _nested(
        launch_request,
        "identity",
        "request_fingerprint_sha256",
    ):
        reasons.append(DECISION_BINDING_DRIFT)
    if decision.get("task_context_fingerprint_sha256") != _nested(
        launch_request,
        "identity",
        "context_fingerprint_sha256",
    ):
        reasons.append(DECISION_BINDING_DRIFT)
    if decision.get("blueprint_head") != _nested(
        launch_request,
        "repository_revalidation",
        "blueprint_head",
    ):
        reasons.append(DECISION_BINDING_DRIFT)
    if decision.get("module_head") != _nested(
        launch_request,
        "repository_revalidation",
        "module_head",
    ):
        reasons.append(DECISION_BINDING_DRIFT)
    if decision.get("dependency_readiness_sha256") != _nested(
        launch_request,
        "dependency_readiness",
        "sha256",
    ):
        reasons.append(DECISION_BINDING_DRIFT)

    expires_raw = decision.get("expires_at")
    try:
        expires_at = datetime.fromisoformat(str(expires_raw))
        if expires_at.tzinfo is None:
            raise ValueError("naive expiry")
    except Exception:
        reasons.append(APPROVAL_EXPIRED)
    else:
        current_time = now or datetime.now(UTC)
        if current_time.tzinfo is None:
            raise ValueError("validation time must be timezone-aware")
        if current_time.astimezone(UTC) >= expires_at.astimezone(UTC):
            reasons.append(APPROVAL_EXPIRED)

    evaluation = evaluate_gateway(
        root=root,
        module_root=module_root,
        launch_request_path=launch_request_path,
    )
    if evaluation.status != EVAL_OK:
        reasons.extend(evaluation.reason_codes)
    else:
        if evaluation.current_state != STATE_AWAITING_APPROVAL:
            reasons.append(REQUEST_FINGERPRINT_DRIFT)
        if evaluation.request_id != launch_request.get("request_id"):
            reasons.append(REQUEST_ID_DRIFT)
        current = evaluation.current_launch_request
        if isinstance(current, dict):
            if _nested(
                current,
                "identity",
                "request_fingerprint_sha256",
            ) != decision.get("request_fingerprint_sha256"):
                reasons.append(REQUEST_FINGERPRINT_DRIFT)
        else:
            reasons.append(REQUEST_REVALIDATION_FAILED)

    unique = tuple(sorted(set(reasons)))
    return DispatchApprovalValidation(
        valid=not unique,
        reason_codes=unique,
        decision_id=str(decision_id) if decision_id else None,
    )


def _render_evaluation(evaluation: GatewayEvaluation) -> str:
    allowed = set(evaluation.allowed_decisions)
    attention_reason = (
        "operator_acceptance_required"
        if evaluation.current_state == STATE_AWAITING_APPROVAL
        else "dependency_blocked"
    )
    return "\n".join(
        [
            f"OPERATOR_APPROVAL_GATEWAY_EVALUATION={evaluation.status}",
            f"REQUEST_ID={evaluation.request_id}",
            f"CURRENT_STATE={evaluation.current_state}",
            f"APPROVE_ALLOWED={str('APPROVE' in allowed).lower()}",
            f"HOLD_ALLOWED={str('HOLD' in allowed).lower()}",
            f"REJECT_ALLOWED={str('REJECT' in allowed).lower()}",
            f"REASON_CODES={','.join(evaluation.reason_codes)}",
            f"Q6_ATTENTION_REASON={attention_reason}",
            "WORKER_DISPATCH_PERFORMED=false",
            "PROMPT_CLAIM_PERFORMED=false",
            "BLUEPRINT_ACCEPT_PERFORMED=false",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "ForPrint transport-neutral Operator Approval Gateway. "
            "It writes immutable decisions but never dispatches workers."
        )
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--module-root", required=True)
    parser.add_argument("--launch-request", required=True)
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--decision", choices=DECISIONS)
    parser.add_argument("--decided-by")
    parser.add_argument("--reason")
    parser.add_argument("--transport", choices=TRANSPORTS, default="CLI")
    parser.add_argument("--expires-in-minutes", type=int)
    parser.add_argument("--decision-input")
    parser.add_argument(
        "--output-dir",
        default=str(Path("tmp") / "control_plane" / "operator_approval_decisions"),
    )
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--validate-decision")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    module_root = Path(args.module_root).resolve()
    launch_request = Path(args.launch_request).resolve()

    if args.evaluate:
        evaluation = evaluate_gateway(
            root=root,
            module_root=module_root,
            launch_request_path=launch_request,
        )
        print(_render_evaluation(evaluation))
        return 0 if evaluation.status == EVAL_OK else 1

    if args.validate_decision:
        validation = validate_approval_for_dispatch(
            root=root,
            module_root=module_root,
            launch_request_path=launch_request,
            decision_path=Path(args.validate_decision).resolve(),
        )
        print(
            "OPERATOR_APPROVAL_VALID_FOR_DISPATCH="
            + str(validation.valid).lower()
        )
        print(f"DECISION_ID={validation.decision_id}")
        print("INVALIDATION_REASONS=" + ",".join(validation.reason_codes))
        print("WORKER_DISPATCH_PERFORMED=false")
        return 0 if validation.valid else 2

    decision = args.decision
    decided_by = args.decided_by
    reason = args.reason
    transport = args.transport
    expires = args.expires_in_minutes

    if args.decision_input:
        payload = _load_decision_input(Path(args.decision_input).resolve())
        decision = payload.get("decision")
        decided_by = payload.get("decided_by")
        reason = payload.get("reason")
        transport = payload.get("transport", "FILESYSTEM")
        expires = payload.get("expires_in_minutes")

    if not decision or not decided_by or not reason:
        parser.error(
            "decision, decided-by and reason are required unless --evaluate "
            "or --validate-decision is used"
        )

    try:
        document = build_operator_decision(
            root=root,
            module_root=module_root,
            launch_request_path=launch_request,
            decision=str(decision),
            decided_by=str(decided_by),
            reason=str(reason),
            transport=str(transport),
            expires_in_minutes=(
                int(expires) if expires is not None else None
            ),
        )
    except PermissionError as exc:
        print(f"OPERATOR_DECISION_REFUSED={exc}")
        print("WORKER_DISPATCH_PERFORMED=false")
        return 2
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    if args.no_write:
        print(
            yaml.safe_dump(
                document,
                sort_keys=False,
                allow_unicode=True,
                width=112,
            ).rstrip()
        )
        print("OPERATOR_DECISION_ARTIFACT_WRITTEN=false")
        print("WORKER_DISPATCH_PERFORMED=false")
        return 0

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    output = write_operator_decision(
        document=document,
        output_dir=output_dir,
    )
    print("OPERATOR_DECISION_ARTIFACT_WRITTEN=true")
    print(f"DECISION={document['decision']}")
    print(f"DECISION_ID={document['decision_id']}")
    print(f"DECISION_PATH={output}")
    print(f"DECISION_SHA256={_sha256_path(output)}")
    print("WORKER_DISPATCH_PERFORMED=false")
    print("PROMPT_CLAIM_PERFORMED=false")
    print("BLUEPRINT_ACCEPT_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
