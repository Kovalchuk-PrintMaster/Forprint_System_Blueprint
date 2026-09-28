"""Thin governed Worker-cycle coordinator for CF-10.

The coordinator is an operator-facing workflow layer, not a new execution
authority. It delegates task resolution/ACK/dispatch preparation to the existing
CF-10 training adapter and workspace preparation to the existing workspace layer.

v0.1 intentionally stops before Worker process launch and before publication.
Those remain explicit later corridor boundaries while the reusable launch/result
and publication bindings are converged behind this same entrypoint.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
from typing import Any

import yaml

from scripts.coordination.control_plane import cf10_training_dispatch as training
from scripts.coordination.control_plane.context.task_context_adapter import (
    build_source_state,
)
from scripts.coordination.control_plane.workspace import (
    plan_workspace,
    provision_workspace,
    seal_pre_dispatch_workspace,
)


MODULE_ID = "forprint_system_blueprint"
WORKER_ID = "worker-01"
DEFAULT_RUNTIME_ROOT = Path("/srv/software_development/forprint-worker-runtime")

STATE_SEQUENCE = (
    "RESOLVE_TASK",
    "PREPARE_WORKSPACE",
    "AWAITING_ASSISTANT_ACK",
    "READY_FOR_EXPLICIT_DISPATCH",
    "READY_FOR_WORKER_LAUNCH",
    "OBSERVE_WORKER",
    "VALIDATE_CANDIDATE",
    "FINALIZE_HANDOFF",
    "ATTEMPT_TERMINAL",
    "AWAITING_OPERATOR_REVIEW",
    "PROMOTE_CANDIDATE",
    "CANONICAL_VALIDATION",
    "AWAITING_PUBLICATION_APPROVAL",
    "VERIFY_REMOTE_CONTAINMENT",
    "PUBLISHED",
)

NEXT_BOUNDARY_BY_STATE = {
    "RESOLVE_TASK": "RESOLVE_AUTHORITATIVE_TASK",
    "PREPARE_WORKSPACE": "PREPARE_ISOLATED_WORKSPACE",
    "AWAITING_ASSISTANT_ACK": "EXPLICIT_ASSISTANT_ACK",
    "READY_FOR_EXPLICIT_DISPATCH": "EXPLICIT_DISPATCH_AUTHORIZATION",
    "READY_FOR_WORKER_LAUNCH": "WORKER_PROCESS_LAUNCH",
    "OBSERVE_WORKER": "WORKER_PROCESS_OBSERVATION",
    "VALIDATE_CANDIDATE": "CANDIDATE_VALIDATION",
    "FINALIZE_HANDOFF": "HANDOFF_V2_RESULT_FINALIZATION",
    "ATTEMPT_TERMINAL": "TERMINAL_ATTEMPT_RECONCILIATION",
    "AWAITING_OPERATOR_REVIEW": "OPERATOR_REVIEW",
    "PROMOTE_CANDIDATE": "CANDIDATE_PROMOTION",
    "CANONICAL_VALIDATION": "CANONICAL_VALIDATION",
    "AWAITING_PUBLICATION_APPROVAL": "PUBLICATION_APPROVAL",
    "VERIFY_REMOTE_CONTAINMENT": "REMOTE_CONTAINMENT_VERIFICATION",
    "PUBLISHED": "NEXT_ELIGIBLE_TASK_OR_CONTOUR_DECISION",
    "BLOCKED": "RECONCILE_BLOCKER",
    "UNKNOWN": "INSPECT_CONTRADICTORY_OR_INSUFFICIENT_EVIDENCE",
}


class GovernedWorkerCycleError(RuntimeError):
    """Raised when a cycle transition cannot be derived safely."""


def _bool(facts: dict[str, Any], key: str) -> bool:
    return facts.get(key) is True


def _contradictions(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    dependencies = [
        ("workspace_prepared", "task_resolved"),
        ("assistant_ack_validated", "workspace_prepared"),
        ("explicit_dispatch_authorized", "assistant_ack_validated"),
        ("worker_process_started", "explicit_dispatch_authorized"),
        ("worker_process_finished", "worker_process_started"),
        ("candidate_validation_passed", "worker_process_finished"),
        ("handoff_validated", "candidate_validation_passed"),
        ("attempt_terminal_pass", "handoff_validated"),
        ("operator_review_passed", "attempt_terminal_pass"),
        ("candidate_promoted", "operator_review_passed"),
        ("canonical_validation_passed", "candidate_promoted"),
        ("publication_approved", "canonical_validation_passed"),
        ("commit_performed", "publication_approved"),
        ("remote_containment_verified", "commit_performed"),
    ]

    for child, parent in dependencies:
        if _bool(facts, child) and not _bool(facts, parent):
            errors.append(f"{child}=true requires {parent}=true")

    if _bool(facts, "attempt_terminal_failed") and _bool(
        facts, "attempt_terminal_pass"
    ):
        errors.append("attempt cannot be terminal PASS and FAIL simultaneously")

    if _bool(facts, "candidate_promoted") and _bool(
        facts, "attempt_terminal_failed"
    ):
        errors.append("failed attempt cannot have promoted candidate")

    return errors


def derive_cycle_projection(facts: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(facts, dict):
        raise GovernedWorkerCycleError("facts must be a mapping")

    contradictions = _contradictions(facts)
    if contradictions:
        state = "UNKNOWN"
    elif _bool(facts, "blocked") or _bool(facts, "attempt_terminal_failed"):
        state = "BLOCKED"
    elif _bool(facts, "remote_containment_verified"):
        state = "PUBLISHED"
    elif _bool(facts, "commit_performed"):
        state = "VERIFY_REMOTE_CONTAINMENT"
    elif _bool(facts, "canonical_validation_passed"):
        state = "AWAITING_PUBLICATION_APPROVAL"
    elif _bool(facts, "candidate_promoted"):
        state = "CANONICAL_VALIDATION"
    elif _bool(facts, "operator_review_passed"):
        state = "PROMOTE_CANDIDATE"
    elif _bool(facts, "attempt_terminal_pass"):
        state = "AWAITING_OPERATOR_REVIEW"
    elif _bool(facts, "handoff_validated"):
        state = "ATTEMPT_TERMINAL"
    elif _bool(facts, "candidate_validation_passed"):
        state = "FINALIZE_HANDOFF"
    elif _bool(facts, "worker_process_finished"):
        state = "VALIDATE_CANDIDATE"
    elif _bool(facts, "worker_process_started"):
        state = "OBSERVE_WORKER"
    elif _bool(facts, "explicit_dispatch_authorized"):
        state = "READY_FOR_WORKER_LAUNCH"
    elif _bool(facts, "assistant_ack_validated"):
        state = "READY_FOR_EXPLICIT_DISPATCH"
    elif _bool(facts, "workspace_prepared"):
        state = "AWAITING_ASSISTANT_ACK"
    elif _bool(facts, "task_resolved"):
        state = "PREPARE_WORKSPACE"
    else:
        state = "RESOLVE_TASK"

    return {
        "schema_version": "forprint_governed_worker_cycle_projection_v0_1",
        "state": state,
        "next_boundary": NEXT_BOUNDARY_BY_STATE[state],
        "contradictions": contradictions,
        "derived_non_authoritative": True,
        "authority": {
            "projection_grants_execution": False,
            "projection_grants_dispatch": False,
            "projection_grants_acceptance": False,
            "projection_grants_promotion": False,
            "projection_grants_publication": False,
            "automatic_accept": False,
            "automatic_push": False,
            "automatic_merge": False,
            "automatic_release": False,
        },
    }


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise GovernedWorkerCycleError(f"{label} missing: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GovernedWorkerCycleError(f"{label} must be a mapping")
    return value


def _write_yaml_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise GovernedWorkerCycleError(f"refusing to overwrite artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            value,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )


def _attempt_root(
    runtime_root: Path,
    attempt_id: str,
    worker_id: str = WORKER_ID,
) -> Path:
    return runtime_root.resolve() / MODULE_ID / worker_id / attempt_id


def prepare_cycle(
    *,
    root: Path | str,
    runtime_root: Path | str,
    task_prompt_id: str,
    attempt_id: str,
    worker_id: str = WORKER_ID,
) -> dict[str, Any]:
    canonical = Path(root).resolve()
    runtime = Path(runtime_root).resolve()

    binding = training.resolve_training_task(
        root=canonical,
        task_prompt_id=task_prompt_id,
    )
    training.assert_attempt_unused(
        root=canonical,
        attempt_id=attempt_id,
    )

    source_state = build_source_state(canonical)
    source_fp = source_state.get("fingerprint_sha256")
    if not isinstance(source_fp, str) or len(source_fp) != 64:
        raise GovernedWorkerCycleError("canonical source fingerprint invalid")

    plan = plan_workspace(
        canonical_repo=canonical,
        runtime_root=runtime,
        module_id=MODULE_ID,
        worker_id=worker_id,
        attempt_id=attempt_id,
        source_state=source_state,
    )

    provision_workspace(plan)
    seal = seal_pre_dispatch_workspace(
        plan,
        frozen_source_state=source_state,
    )

    prepared = training.prepare_training_pre_dispatch(
        root=canonical,
        task_prompt_id=task_prompt_id,
        worker_id=worker_id,
        attempt_id=attempt_id,
    )

    expected_ack = training.build_training_canonical_ack(
        root=canonical,
        prepared_execution=prepared,
        source_state_fingerprint=source_fp,
        worker_id=worker_id,
        attempt_id=attempt_id,
    )

    attempt = _attempt_root(runtime, attempt_id, worker_id)
    input_dir = attempt / "input"

    _write_yaml_new(
        input_dir / "governed_worker_cycle_prepared_execution_v0_1.yaml",
        prepared,
    )
    _write_yaml_new(
        input_dir / "governed_worker_cycle_expected_ack_v0_1.yaml",
        expected_ack,
    )
    _write_yaml_new(
        input_dir / "governed_worker_cycle_source_state_v0_1.yaml",
        source_state,
    )

    result = {
        "schema_version": "forprint_governed_worker_cycle_prepare_result_v0_1",
        "task_prompt_id": task_prompt_id,
        "attempt_id": attempt_id,
        "worker_id": worker_id,
        "work_front_id": binding["work_front_id"],
        "source_head": source_state.get("git_head"),
        "source_state_fingerprint": source_fp,
        "workspace_repo": str(plan.layout.workspace_repo),
        "workspace_manifest": str(plan.layout.manifest),
        "workspace_seal_evidence": seal.get("evidence_path"),
        "state": "AWAITING_ASSISTANT_ACK",
        "next_boundary": "EXPLICIT_ASSISTANT_ACK",
        "automatic_dispatch": False,
        "worker_launch_performed": False,
        "candidate_promoted": False,
        "commit_performed": False,
        "push_performed": False,
    }
    _write_yaml_new(
        attempt / "evidence/governed_worker_cycle_prepare_result_v0_1.yaml",
        result,
    )
    return result


def confirm_assistant_ack(
    *,
    root: Path | str,
    runtime_root: Path | str,
    attempt_id: str,
    confirm: bool,
    worker_id: str = WORKER_ID,
) -> dict[str, Any]:
    if confirm is not True:
        raise GovernedWorkerCycleError("explicit --confirm-ack is required")

    canonical = Path(root).resolve()
    attempt = _attempt_root(Path(runtime_root), attempt_id, worker_id)
    input_dir = attempt / "input"

    prepared = _load_yaml(
        input_dir / "governed_worker_cycle_prepared_execution_v0_1.yaml",
        "prepared execution",
    )
    expected_ack = _load_yaml(
        input_dir / "governed_worker_cycle_expected_ack_v0_1.yaml",
        "expected ACK",
    )

    ready = training.validate_training_assistant_ack(
        root=canonical,
        prepared_execution=prepared,
        assistant_ack=expected_ack,
        expected_ack=expected_ack,
    )

    _write_yaml_new(
        input_dir / "governed_worker_cycle_ready_execution_v0_1.yaml",
        ready,
    )

    return {
        "schema_version": "forprint_governed_worker_cycle_ack_result_v0_1",
        "attempt_id": attempt_id,
        "state": "READY_FOR_EXPLICIT_DISPATCH",
        "next_boundary": "EXPLICIT_DISPATCH_AUTHORIZATION",
        "assistant_ack_validated": True,
        "dispatch_authority_granted": False,
        "worker_launch_performed": False,
    }


def authorize_dispatch(
    *,
    root: Path | str,
    runtime_root: Path | str,
    attempt_id: str,
    confirm: bool,
    worker_id: str = WORKER_ID,
) -> dict[str, Any]:
    if confirm is not True:
        raise GovernedWorkerCycleError(
            "explicit --confirm-dispatch-authorization is required"
        )

    canonical = Path(root).resolve()
    attempt = _attempt_root(Path(runtime_root), attempt_id, worker_id)
    input_dir = attempt / "input"

    ready = _load_yaml(
        input_dir / "governed_worker_cycle_ready_execution_v0_1.yaml",
        "ready execution",
    )
    source_state = _load_yaml(
        input_dir / "governed_worker_cycle_source_state_v0_1.yaml",
        "source state",
    )
    manifest = _load_yaml(attempt / "manifest.yaml", "workspace manifest")

    source_fp = source_state.get("fingerprint_sha256")
    workspace_repo = manifest.get("workspace_repo")
    if not isinstance(source_fp, str) or len(source_fp) != 64:
        raise GovernedWorkerCycleError("source-state fingerprint invalid")
    if not isinstance(workspace_repo, str) or not workspace_repo:
        raise GovernedWorkerCycleError("workspace_repo missing from manifest")

    decision = training.authorize_training_explicit_dispatch(
        root=canonical,
        ready_execution=ready,
        worker_id=worker_id,
        attempt_id=attempt_id,
        source_state_fingerprint=source_fp,
        workspace_repo=Path(workspace_repo),
        runtime_provider="github_copilot_cli",
        runtime_model="auto",
    )

    _write_yaml_new(
        input_dir / "governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml",
        decision,
    )

    return {
        "schema_version": (
            "forprint_governed_worker_cycle_dispatch_authorization_result_v0_1"
        ),
        "attempt_id": attempt_id,
        "state": "READY_FOR_WORKER_LAUNCH",
        "next_boundary": "WORKER_PROCESS_LAUNCH",
        "explicit_dispatch_authorized": True,
        "worker_launch_performed": False,
        "automatic_dispatch": False,
        "automatic_accept": False,
    }


def live_facts(
    *,
    root: Path | str,
    runtime_root: Path | str,
    task_prompt_id: str,
    attempt_id: str,
    worker_id: str = WORKER_ID,
) -> dict[str, Any]:
    canonical = Path(root).resolve()
    attempt = _attempt_root(Path(runtime_root), attempt_id, worker_id)

    facts: dict[str, Any] = {
        "task_resolved": False,
        "workspace_prepared": False,
        "assistant_ack_validated": False,
        "explicit_dispatch_authorized": False,
        "worker_process_started": False,
        "worker_process_finished": False,
        "candidate_validation_passed": False,
        "handoff_validated": False,
        "attempt_terminal_pass": False,
        "attempt_terminal_failed": False,
        "operator_review_passed": False,
        "candidate_promoted": False,
        "canonical_validation_passed": False,
        "publication_approved": False,
        "commit_performed": False,
        "remote_containment_verified": False,
        "blocked": False,
    }

    training.resolve_training_task(
        root=canonical,
        task_prompt_id=task_prompt_id,
    )
    facts["task_resolved"] = True

    manifest_path = attempt / "manifest.yaml"
    if manifest_path.is_file():
        manifest = _load_yaml(manifest_path, "workspace manifest")
        facts["workspace_prepared"] = (
            manifest.get("provisioning_performed") is True
            and manifest.get("source_state_frozen") is True
        )
        facts["assistant_ack_validated"] = (
            manifest.get("assistant_ack_validated") is True
        )
        facts["explicit_dispatch_authorized"] = (
            manifest.get("explicit_dispatch_decision_recorded") is True
        )
        facts["worker_process_started"] = (
            manifest.get("worker_launch_performed") is True
        )

    if (
        attempt
        / "input/governed_worker_cycle_ready_execution_v0_1.yaml"
    ).is_file():
        facts["assistant_ack_validated"] = True

    if (
        attempt
        / "input/governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml"
    ).is_file():
        facts["explicit_dispatch_authorized"] = True

    for process_path in sorted((attempt / "evidence").glob("*process*result*.yaml")):
        value = _load_yaml(process_path, "process result")
        process = value.get("process")
        if isinstance(process, dict):
            facts["worker_process_started"] = (
                process.get("process_started") is True
                or facts["worker_process_started"]
            )
            facts["worker_process_finished"] = (
                process.get("return_code") is not None
                and process.get("timed_out") is False
            )

    for candidate_path in sorted(
        (attempt / "evidence").glob("*candidate*validation*.yaml")
    ):
        value = _load_yaml(candidate_path, "candidate validation")
        if value.get("result") == "PASS":
            facts["candidate_validation_passed"] = True
        if value.get("candidate_validation_result") == "PASS":
            facts["candidate_validation_passed"] = True

    for handoff_path in sorted((attempt / "result").glob("*handoff_v2_result*.yaml")):
        value = _load_yaml(handoff_path, "Handoff result")
        if value.get("status") == "PASS":
            facts["handoff_validated"] = True

    try:
        from scripts.coordination import execution_attempt_ledger_v0_1 as ledger

        contract = ledger.load_contract(canonical)
        store = ledger.store_root(canonical, contract, None)
        records = ledger.records_for_attempt(store, attempt_id)
        for record in records:
            if (
                record.get("attempt_stage") == "FINISHED"
                and record.get("result_state") == "SUCCEEDED"
                and record.get("validator_outcome") == "PASS"
            ):
                facts["attempt_terminal_pass"] = True
            if (
                record.get("attempt_stage") in {"FINISHED", "BLOCKED"}
                and record.get("result_state") in {"FAILED", "BLOCKED"}
            ):
                facts["attempt_terminal_failed"] = True
    except Exception:
        # Status projection fails closed through missing facts; it never invents
        # a terminal state when the ledger cannot be read.
        pass

    promotion_path = (
        attempt / "evidence/worker_candidate_promotion_v0_1.yaml"
    )
    if promotion_path.is_file():
        promotion = _load_yaml(promotion_path, "promotion evidence")
        facts["operator_review_passed"] = (
            promotion.get("operator_review") == "PASS"
            or promotion.get("promotion_authority") == "OPERATOR_CONTROLLED_CF10"
        )
        facts["candidate_promoted"] = promotion.get("candidate_promoted") is True

    validation_path = (
        attempt / "evidence/governed_worker_cycle_canonical_validation_v0_1.yaml"
    )
    if validation_path.is_file():
        value = _load_yaml(validation_path, "canonical validation")
        facts["canonical_validation_passed"] = value.get("result") == "PASS"

    publication_path = (
        attempt / "evidence/governed_worker_cycle_publication_v0_1.yaml"
    )
    if publication_path.is_file():
        value = _load_yaml(publication_path, "publication evidence")
        facts["publication_approved"] = value.get("operator_approved") is True
        facts["commit_performed"] = value.get("commit_performed") is True
        facts["remote_containment_verified"] = (
            value.get("remote_containment_verified") is True
        )

    return facts


def status(
    *,
    root: Path | str,
    runtime_root: Path | str,
    task_prompt_id: str,
    attempt_id: str,
    worker_id: str = WORKER_ID,
) -> dict[str, Any]:
    facts = live_facts(
        root=root,
        runtime_root=runtime_root,
        task_prompt_id=task_prompt_id,
        attempt_id=attempt_id,
        worker_id=worker_id,
    )
    projection = derive_cycle_projection(facts)
    projection["task_prompt_id"] = task_prompt_id
    projection["attempt_id"] = attempt_id
    projection["facts"] = facts
    return projection


def _print_result(value: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    elif output_format == "yaml":
        print(yaml.safe_dump(value, sort_keys=False, allow_unicode=True))
    else:
        print("STATE=" + str(value.get("state")))
        print("NEXT_BOUNDARY=" + str(value.get("next_boundary")))
        if value.get("attempt_id"):
            print("ATTEMPT_ID=" + str(value["attempt_id"]))
        if value.get("task_prompt_id"):
            print("TASK_PROMPT_ID=" + str(value["task_prompt_id"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=("status", "prepare", "ack", "authorize-dispatch"),
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--runtime-root", default=str(DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--task-prompt-id")
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--worker-id", default=WORKER_ID)
    parser.add_argument("--confirm-ack", action="store_true")
    parser.add_argument("--confirm-dispatch-authorization", action="store_true")
    parser.add_argument(
        "--output-format",
        choices=("text", "yaml", "json"),
        default="text",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    runtime_root = Path(args.runtime_root).resolve()

    if args.action in {"status", "prepare"} and not args.task_prompt_id:
        parser.error("--task-prompt-id is required for status/prepare")

    if args.action == "status":
        result = status(
            root=root,
            runtime_root=runtime_root,
            task_prompt_id=args.task_prompt_id,
            attempt_id=args.attempt_id,
            worker_id=args.worker_id,
        )
    elif args.action == "prepare":
        result = prepare_cycle(
            root=root,
            runtime_root=runtime_root,
            task_prompt_id=args.task_prompt_id,
            attempt_id=args.attempt_id,
            worker_id=args.worker_id,
        )
    elif args.action == "ack":
        result = confirm_assistant_ack(
            root=root,
            runtime_root=runtime_root,
            attempt_id=args.attempt_id,
            confirm=args.confirm_ack,
            worker_id=args.worker_id,
        )
    else:
        result = authorize_dispatch(
            root=root,
            runtime_root=runtime_root,
            attempt_id=args.attempt_id,
            confirm=args.confirm_dispatch_authorization,
            worker_id=args.worker_id,
        )

    _print_result(result, args.output_format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
