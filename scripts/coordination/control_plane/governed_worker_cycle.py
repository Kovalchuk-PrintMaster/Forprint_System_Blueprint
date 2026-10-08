"""Thin governed Worker-cycle coordinator for CF-10.

The coordinator is an operator-facing workflow layer, not a new execution
authority. It delegates task resolution/ACK/dispatch preparation to the existing
CF-10 training adapter and workspace preparation to the existing workspace layer.

v0.1 keeps Worker process launch explicit and operator-confirmed, while
candidate promotion and publication remain separate later corridor boundaries.
Reusable launch/result bindings stay behind this same governed entrypoint.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import argparse
import json
import subprocess
from typing import Any

import yaml

from scripts.coordination.control_plane import cf10_training_dispatch as training
from scripts.coordination.control_plane.context.task_context_adapter import (
    build_internal_task_context,
    build_source_state,
)
from scripts.coordination.control_plane.dispatch_intent import (
    governed_worker_context_sha256,
)
from scripts.coordination.control_plane.workspace import (
    plan_workspace,
    provision_workspace,
    seal_pre_dispatch_workspace,
)
from scripts.coordination.control_plane.worker_runtime import (
    worker_result_return,
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
    elif (
        _bool(facts, "blocked")
        or _bool(facts, "worker_result_return_blocked")
        or _bool(facts, "attempt_terminal_failed")
    ):
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



def _git_output(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise GovernedWorkerCycleError(
            "git command failed: "
            + " ".join(args)
            + "\n"
            + result.stdout.strip()
        )
    return result.stdout.strip()


def _git_is_ancestor(root: Path, older: str, newer: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise GovernedWorkerCycleError(
        "git ancestry check failed: " + result.stdout.strip()
    )


def _refresh_relevant_paths(
    canonical: Path,
    binding: dict[str, Any],
) -> tuple[str, ...]:
    paths = {
        "coordination/internal_work/blueprint/worker_tasks/index.yaml",
        "coordination/internal_work/blueprint/worker_training/cf10_worker_training_queue_v0_1.yaml",
        "coordination/standards/governance/project_constitution_v0_1.yaml",
        "coordination/module_policy/forprint_system_blueprint/module_policy.md",
        "coordination/registry/execution_profiles_v0_1.yaml",
        "coordination/registry/governed_canonical_mutation_procedure_v0_1.yaml",
        "coordination/standards/automation/assistant_handoff_v2_contract_v0_1.yaml",
        "coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml",
        "coordination/work_fronts/cf10_governed_worker_cycle_v0_1.yaml",
        "Makefile",
        "scripts/coordination/control_plane/governed_worker_cycle.py",
        "scripts/coordination/control_plane/cf10_training_dispatch.py",
        "scripts/coordination/control_plane/dispatch_intent.py",
        "scripts/coordination/control_plane/context",
        "scripts/coordination/control_plane/workspace",
        "scripts/coordination/control_plane/worker_runtime",
        "scripts/coordination/assistant_handoff_v2_runtime_v0_1.py",
        "scripts/coordination/execution_attempt_ledger_v0_1.py",
    }

    for key in ("task_ref", "work_front_ref"):
        value = binding.get(key)
        if isinstance(value, str) and value:
            paths.add(value)

    front_ref = binding.get("work_front_ref")
    if isinstance(front_ref, str) and front_ref:
        front = _load_yaml(canonical / front_ref, "Work Front")
        scope = front.get("scope")
        if isinstance(scope, list):
            for value in scope:
                if not isinstance(value, str) or not value:
                    continue
                candidate = Path(value)
                if candidate.is_absolute() or ".." in candidate.parts:
                    raise GovernedWorkerCycleError(
                        "Work Front scope contains unsafe refresh path"
                    )
                paths.add(candidate.as_posix().rstrip("/"))

    return tuple(sorted(paths))


def _path_matches_refresh_scope(
    path: str,
    relevant_paths: tuple[str, ...],
) -> bool:
    for raw in relevant_paths:
        base = raw.rstrip("/")
        if path == base or path.startswith(base + "/"):
            return True
    return False



def _assert_frozen_source_state_current(
    canonical: Path,
    frozen_source_state: dict[str, Any],
    *,
    boundary: str,
) -> dict[str, Any]:
    frozen_head = frozen_source_state.get("git_head")
    frozen_fp = frozen_source_state.get("fingerprint_sha256")
    if not isinstance(frozen_head, str) or not frozen_head:
        raise GovernedWorkerCycleError(
            f"{boundary}: frozen source HEAD missing"
        )
    if not isinstance(frozen_fp, str) or len(frozen_fp) != 64:
        raise GovernedWorkerCycleError(
            f"{boundary}: frozen source fingerprint invalid"
        )

    current = build_source_state(canonical)
    current_head = current.get("git_head")
    current_fp = current.get("fingerprint_sha256")
    if not isinstance(current_head, str) or not current_head:
        raise GovernedWorkerCycleError(
            f"{boundary}: current source HEAD missing"
        )
    if not isinstance(current_fp, str) or len(current_fp) != 64:
        raise GovernedWorkerCycleError(
            f"{boundary}: current source fingerprint invalid"
        )

    if current_head != frozen_head or current_fp != frozen_fp:
        raise GovernedWorkerCycleError(
            f"{boundary}: frozen source state is stale; "
            f"frozen_head={frozen_head} current_head={current_head} "
            f"frozen_fingerprint={frozen_fp} "
            f"current_fingerprint={current_fp}; "
            "prepare a new attempt before crossing this boundary"
        )

    return current


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



def refresh_cycle(
    *,
    root: Path | str,
    runtime_root: Path | str,
    task_prompt_id: str,
    attempt_id: str,
    worker_id: str = WORKER_ID,
) -> dict[str, Any]:
    """Refresh a stale pre-ACK workspace while the attempt remains unstarted."""
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

    attempt = _attempt_root(runtime, attempt_id, worker_id)
    if not attempt.is_dir():
        raise GovernedWorkerCycleError(
            f"prepared attempt runtime missing: {attempt}"
        )

    input_dir = attempt / "input"
    manifest = _load_yaml(attempt / "manifest.yaml", "workspace manifest")
    prepared = _load_yaml(
        input_dir / "governed_worker_cycle_prepared_execution_v0_1.yaml",
        "prepared execution",
    )
    expected_ack = _load_yaml(
        input_dir / "governed_worker_cycle_expected_ack_v0_1.yaml",
        "expected ACK",
    )
    old_source = _load_yaml(
        input_dir / "governed_worker_cycle_source_state_v0_1.yaml",
        "source state",
    )

    if manifest.get("attempt_id") != attempt_id:
        raise GovernedWorkerCycleError("workspace manifest attempt mismatch")
    if manifest.get("workspace_state") != "PROVISIONED_NOT_DISPATCHED":
        raise GovernedWorkerCycleError(
            "refresh requires PROVISIONED_NOT_DISPATCHED workspace"
        )

    for key in (
        "assistant_ack_validated",
        "explicit_dispatch_decision_recorded",
        "dispatch_authority_granted",
        "worker_launch_performed",
        "canonical_attempt_ledger_appended",
    ):
        if manifest.get(key) is not False:
            raise GovernedWorkerCycleError(
                f"refresh forbidden after pre-dispatch boundary: {key}"
            )

    if prepared.get("state") != "AWAITING_ASSISTANT_ACK":
        raise GovernedWorkerCycleError(
            "refresh requires AWAITING_ASSISTANT_ACK"
        )
    if prepared.get("assistant_ack_validated") is not False:
        raise GovernedWorkerCycleError(
            "refresh forbidden after Assistant ACK"
        )
    if prepared.get("attempt_id") != attempt_id:
        raise GovernedWorkerCycleError("prepared execution attempt mismatch")
    if prepared.get("worker_id") != worker_id:
        raise GovernedWorkerCycleError("prepared execution worker mismatch")
    if prepared.get("cf10_training_binding") != binding:
        raise GovernedWorkerCycleError(
            "prepared task binding changed; use a new attempt_id"
        )

    for forbidden in (
        input_dir / "governed_worker_cycle_ready_execution_v0_1.yaml",
        input_dir
        / "governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml",
    ):
        if forbidden.exists():
            raise GovernedWorkerCycleError(
                "refresh forbidden after ACK/dispatch artifact exists"
            )

    old_head = old_source.get("git_head")
    old_fp = old_source.get("fingerprint_sha256")
    if not isinstance(old_head, str) or not old_head:
        raise GovernedWorkerCycleError("prepared source HEAD missing")
    if not isinstance(old_fp, str) or len(old_fp) != 64:
        raise GovernedWorkerCycleError(
            "prepared source fingerprint invalid"
        )

    rebuilt_ack = training.build_training_canonical_ack(
        root=canonical,
        prepared_execution=prepared,
        source_state_fingerprint=old_fp,
        worker_id=worker_id,
        attempt_id=attempt_id,
    )
    if rebuilt_ack != expected_ack:
        raise GovernedWorkerCycleError(
            "prepared expected ACK is not canonical"
        )

    current_source = build_source_state(canonical)
    current_head = current_source.get("git_head")
    current_fp = current_source.get("fingerprint_sha256")
    if not isinstance(current_head, str) or not current_head:
        raise GovernedWorkerCycleError("current source HEAD missing")
    if not isinstance(current_fp, str) or len(current_fp) != 64:
        raise GovernedWorkerCycleError(
            "current source fingerprint invalid"
        )

    if current_head == old_head and current_fp == old_fp:
        return {
            "schema_version": (
                "forprint_governed_worker_cycle_refresh_result_v0_1"
            ),
            "task_prompt_id": task_prompt_id,
            "attempt_id": attempt_id,
            "state": "AWAITING_ASSISTANT_ACK",
            "next_boundary": "EXPLICIT_ASSISTANT_ACK",
            "refresh_performed": False,
            "source_head": current_head,
            "source_state_fingerprint": current_fp,
            "assistant_ack_validated": False,
            "dispatch_authority_granted": False,
            "worker_launch_performed": False,
        }

    relevant_paths = _refresh_relevant_paths(canonical, binding)
    changed_paths: list[str] = []
    if current_head != old_head:
        if not _git_is_ancestor(canonical, old_head, current_head):
            raise GovernedWorkerCycleError(
                "prepared source HEAD is not an ancestor of current HEAD"
            )
        changed = _git_output(
            canonical,
            "diff",
            "--name-only",
            f"{old_head}..{current_head}",
            "--",
            *relevant_paths,
        )
        changed_paths = [
            line for line in changed.splitlines() if line
        ]
        if changed_paths:
            raise GovernedWorkerCycleError(
                "execution-relevant source changed; use a new attempt_id: "
                + ",".join(changed_paths)
            )

    old_dirty = old_source.get("durable_dirty_paths")
    current_dirty = current_source.get("durable_dirty_paths")
    if not isinstance(old_dirty, list) or not isinstance(current_dirty, list):
        raise GovernedWorkerCycleError(
            "durable dirty path evidence missing"
        )

    old_relevant_dirty = sorted(
        path
        for path in old_dirty
        if isinstance(path, str)
        and _path_matches_refresh_scope(path, relevant_paths)
    )
    current_relevant_dirty = sorted(
        path
        for path in current_dirty
        if isinstance(path, str)
        and _path_matches_refresh_scope(path, relevant_paths)
    )
    if current_relevant_dirty != old_relevant_dirty:
        raise GovernedWorkerCycleError(
            "execution-relevant dirty overlay changed; use a new attempt_id"
        )

    recheck = build_source_state(canonical)
    if (
        recheck.get("git_head") != current_head
        or recheck.get("fingerprint_sha256") != current_fp
    ):
        raise GovernedWorkerCycleError(
            "canonical source changed during refresh preflight"
        )

    archive_base = attempt.parent / (
        attempt_id
        + "__predispatch_superseded__"
        + old_head[:7]
        + "_"
        + old_fp[:12]
        + "_to_"
        + current_head[:7]
        + "_"
        + current_fp[:12]
    )
    archive = archive_base
    refresh_ordinal = 1
    while archive.exists():
        refresh_ordinal += 1
        archive = Path(
            str(archive_base) + f"__r{refresh_ordinal:02d}"
        )

    supersession = {
        "schema_version": (
            "forprint_governed_worker_cycle_predispatch_supersession_v0_1"
        ),
        "recorded_at": (
            datetime.now(UTC).isoformat().replace("+00:00", "Z")
        ),
        "task_prompt_id": task_prompt_id,
        "attempt_id": attempt_id,
        "old_source_head": old_head,
        "old_source_state_fingerprint": old_fp,
        "new_source_head": current_head,
        "new_source_state_fingerprint": current_fp,
        "refresh_ordinal": refresh_ordinal,
        "relevant_paths_checked": list(relevant_paths),
        "relevant_committed_drift": changed_paths,
        "relevant_dirty_overlay_unchanged": True,
        "assistant_ack_validated": False,
        "dispatch_authority_granted": False,
        "worker_launch_performed": False,
        "canonical_attempt_ledger_appended": False,
    }

    _write_yaml_new(
        attempt
        / "evidence/"
        "governed_worker_cycle_predispatch_supersession_v0_1.yaml",
        supersession,
    )

    attempt.rename(archive)
    try:
        refreshed = prepare_cycle(
            root=canonical,
            runtime_root=runtime,
            task_prompt_id=task_prompt_id,
            attempt_id=attempt_id,
            worker_id=worker_id,
        )
    except Exception:
        if not attempt.exists() and archive.exists():
            archive.rename(attempt)
        raise

    if (
        refreshed.get("source_head") != current_head
        or refreshed.get("source_state_fingerprint") != current_fp
    ):
        raise GovernedWorkerCycleError(
            "canonical source changed while refreshed preparation was created"
        )

    result = {
        "schema_version": (
            "forprint_governed_worker_cycle_refresh_result_v0_1"
        ),
        "task_prompt_id": task_prompt_id,
        "attempt_id": attempt_id,
        "state": "AWAITING_ASSISTANT_ACK",
        "next_boundary": "EXPLICIT_ASSISTANT_ACK",
        "refresh_performed": True,
        "superseded_runtime_archive": str(archive),
        "source_head": current_head,
        "source_state_fingerprint": current_fp,
        "assistant_ack_validated": False,
        "dispatch_authority_granted": False,
        "worker_launch_performed": False,
    }
    _write_yaml_new(
        attempt
        / "evidence/governed_worker_cycle_refresh_result_v0_1.yaml",
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
    source_state = _load_yaml(
        input_dir / "governed_worker_cycle_source_state_v0_1.yaml",
        "source state",
    )
    _assert_frozen_source_state_current(
        canonical,
        source_state,
        boundary="assistant ACK",
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
    _assert_frozen_source_state_current(
        canonical,
        source_state,
        boundary="explicit dispatch authorization",
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
        "worker_result_return_valid": False,
        "worker_result_return_blocked": False,
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
            return_code = process.get("return_code")
            timed_out = process.get("timed_out") is True
            facts["worker_process_finished"] = (
                return_code is not None and not timed_out
            )
            if timed_out or (
                return_code is not None and return_code != 0
            ):
                facts["worker_result_return_blocked"] = True
                facts["blocked"] = True

    result_return_path = (
        attempt
        / "evidence/governed_worker_cycle_result_return_v0_1.yaml"
    )
    if result_return_path.is_file():
        value = _load_yaml(
            result_return_path,
            "Worker result-return evidence",
        )
        result_path_raw = value.get("result_path")
        result_path = (
            Path(result_path_raw)
            if isinstance(result_path_raw, str) and result_path_raw
            else None
        )
        result_valid = (
            value.get("result") == "PASS"
            and value.get("validation_passed") is True
            and value.get("blocked") is False
            and result_path is not None
            and result_path.is_file()
            and not result_path.is_symlink()
        )
        if result_valid:
            facts["worker_result_return_valid"] = True
            facts["worker_result_return_blocked"] = False
        elif value.get("blocked") is True or value.get("result") == "BLOCKED":
            facts["worker_result_return_blocked"] = True
            facts["blocked"] = True
    elif facts["worker_process_finished"]:
        facts["worker_result_return_blocked"] = True
        facts["blocked"] = True

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
        if "refresh_performed" in value:
            print(
                "REFRESH_PERFORMED="
                + str(value["refresh_performed"]).lower()
            )
        if value.get("source_head"):
            print("SOURCE_HEAD=" + str(value["source_head"]))
        if "worker_process_launched" in value:
            print(
                "WORKER_PROCESS_LAUNCHED="
                + str(value["worker_process_launched"]).lower()
            )
        if value.get("process_return_code") is not None:
            print(
                "PROCESS_RETURN_CODE="
                + str(value["process_return_code"])
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=(
            "status",
            "prepare",
            "refresh",
            "ack",
            "authorize-dispatch",
            "launch",
            "reconcile-result-return",
        ),
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--runtime-root", default=str(DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--task-prompt-id")
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--worker-id", default=WORKER_ID)
    parser.add_argument("--confirm-ack", action="store_true")
    parser.add_argument("--confirm-dispatch-authorization", action="store_true")
    parser.add_argument("--confirm-launch", action="store_true")
    parser.add_argument(
        "--confirm-result-return-reconciliation",
        action="store_true",
    )
    parser.add_argument(
        "--output-format",
        choices=("text", "yaml", "json"),
        default="text",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    runtime_root = Path(args.runtime_root).resolve()

    if (
        args.action
        in {
            "status",
            "prepare",
            "refresh",
            "launch",
            "reconcile-result-return",
        }
        and not args.task_prompt_id
    ):
        parser.error(
            "--task-prompt-id is required for "
            "status/prepare/refresh/launch/reconcile-result-return"
        )

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
    elif args.action == "refresh":
        result = refresh_cycle(
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
    elif args.action == "authorize-dispatch":
        result = authorize_dispatch(
            root=root,
            runtime_root=runtime_root,
            attempt_id=args.attempt_id,
            confirm=args.confirm_dispatch_authorization,
            worker_id=args.worker_id,
        )
    elif args.action == "launch":
        result = launch_cycle(
            root=root,
            runtime_root=runtime_root,
            task_prompt_id=args.task_prompt_id,
            attempt_id=args.attempt_id,
            confirm=args.confirm_launch,
            worker_id=args.worker_id,
        )
    else:
        result = reconcile_result_return(
            root=root,
            runtime_root=runtime_root,
            task_prompt_id=args.task_prompt_id,
            attempt_id=args.attempt_id,
            confirm=args.confirm_result_return_reconciliation,
            worker_id=args.worker_id,
        )

    _print_result(result, args.output_format)
    return 0


# CF10_GOVERNED_WORKER_CYCLE_SLICE_B2_LIVE_LAUNCH_START
def _b2_call_supported_kwargs(func, values):
    import inspect

    signature = inspect.signature(func)
    parameters = signature.parameters
    accepts_var_kwargs = any(
        item.kind is inspect.Parameter.VAR_KEYWORD
        for item in parameters.values()
    )

    kwargs = dict(values) if accepts_var_kwargs else {
        name: value
        for name, value in values.items()
        if name in parameters
        and parameters[name].kind is not inspect.Parameter.POSITIONAL_ONLY
    }

    missing = []
    for name, parameter in parameters.items():
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if parameter.default is not inspect.Parameter.empty:
            continue
        if parameter.kind is inspect.Parameter.POSITIONAL_ONLY or name not in kwargs:
            missing.append(name)

    if missing:
        raise RuntimeError(
            "CF10 B2 missing required integration arguments for "
            f"{getattr(func, '__name__', repr(func))}: {missing}"
        )

    return func(**kwargs)


def _b2_build_started_record(*, attempt_id, record_data):
    import copy

    if not isinstance(record_data, dict):
        raise TypeError("started record_data must be a mapping")

    record = copy.deepcopy(record_data)
    observed = (
        record.get("attempt_id")
        or record.get("execution_attempt_id")
        or record.get("id")
    )

    if observed is not None and observed != attempt_id:
        raise RuntimeError(
            "STARTED record attempt identity mismatch: "
            f"expected={attempt_id!r} observed={observed!r}"
        )

    if observed is None:
        record["attempt_id"] = attempt_id

    if record.get("attempt_stage") != "STARTED":
        raise RuntimeError(
            "STARTED record attempt_stage must be STARTED"
        )
    if record.get("result_state") != "PENDING":
        raise RuntimeError(
            "STARTED record result_state must be PENDING"
        )

    return record


def _b2_find_launch_mapping(value):
    if not isinstance(value, dict):
        raise RuntimeError("canonical B1 invocation plan must be a mapping")

    paths = value.get("paths")
    if not isinstance(paths, dict):
        raise RuntimeError(
            "canonical B1 invocation plan paths mapping missing"
        )

    required_top = (
        "argv",
        "workspace_repo",
        "timeout_seconds",
    )
    missing_top = [
        key for key in required_top
        if value.get(key) is None
    ]
    required_paths = ("stdout", "stderr")
    missing_paths = [
        key for key in required_paths
        if not isinstance(paths.get(key), str) or not paths.get(key)
    ]

    if missing_top or missing_paths:
        raise RuntimeError(
            "canonical B1 invocation plan missing launcher fields: "
            f"top={missing_top} paths={missing_paths}"
        )

    launch = {
        "argv": value["argv"],
        "cwd": value["workspace_repo"],
        "stdout_path": paths["stdout"],
        "stderr_path": paths["stderr"],
        "timeout_seconds": value["timeout_seconds"],
    }

    if value.get("heartbeat_seconds") is not None:
        launch["heartbeat_seconds"] = value["heartbeat_seconds"]
    if value.get("stall_threshold_seconds") is not None:
        launch["stall_threshold_seconds"] = value[
            "stall_threshold_seconds"
        ]

    return launch


def _b2_sanitize_process_result(value):
    if not isinstance(value, dict):
        return {"result_type": type(value).__name__}

    denied = {
        "argv",
        "full_argv",
        "prompt",
        "prompt_text",
        "secret",
        "secret_value",
        "secrets",
        "environment",
        "env",
    }
    return {
        key: item
        for key, item in value.items()
        if str(key).lower() not in denied
    }


def launch_authorized_worker_cycle(
    *,
    root,
    runtime_root,
    task_prompt_id,
    attempt_id,
    started_record_data,
    worker_id="worker-01",
    invocation_context=None,
):
    from scripts.coordination import execution_attempt_ledger_v0_1
    from scripts.coordination.control_plane import cf10_training_dispatch
    from scripts.coordination.control_plane.worker_runtime import (
        invocation_adapter,
        launcher,
    )

    facts = live_facts(
        root=root,
        runtime_root=runtime_root,
        task_prompt_id=task_prompt_id,
        attempt_id=attempt_id,
        worker_id=worker_id,
    )
    projection = derive_cycle_projection(facts)

    if projection.get("state") != "READY_FOR_WORKER_LAUNCH":
        raise RuntimeError(
            "CF10 governed Worker Cycle is not launch-ready: "
            f"state={projection.get('state')!r}"
        )

    canonical = Path(root).resolve()
    attempt = _attempt_root(Path(runtime_root), attempt_id, worker_id)
    source_state = _load_yaml(
        attempt / "input/governed_worker_cycle_source_state_v0_1.yaml",
        "source state",
    )
    _assert_frozen_source_state_current(
        canonical,
        source_state,
        boundary="Worker process launch",
    )

    context = {
        "root": root,
        "runtime_root": runtime_root,
        "task_prompt_id": task_prompt_id,
        "attempt_id": attempt_id,
        "worker_id": worker_id,
        "facts": facts,
        "cycle_facts": facts,
        "projection": projection,
        "cycle_projection": projection,
    }
    if invocation_context:
        extra_context = dict(invocation_context)
        collisions = sorted(set(extra_context) & set(context))
        if collisions:
            raise RuntimeError(
                "invocation_context cannot override canonical cycle keys: "
                f"{collisions}"
            )
        context.update(extra_context)

    builder = getattr(invocation_adapter, "build_launch_invocation", None)
    if builder is None:
        builder = getattr(invocation_adapter, "build_invocation", None)
    if builder is None:
        raise RuntimeError(
            "canonical invocation adapter has no public launch builder"
        )

    invocation_plan = _b2_call_supported_kwargs(builder, context)

    evidence_builder = getattr(
        invocation_adapter,
        "build_invocation_evidence",
        None,
    )
    if evidence_builder is None:
        raise RuntimeError(
            "canonical invocation adapter has no evidence builder"
        )

    evidence_context = dict(context)
    evidence_context.update(
        {
            "invocation": invocation_plan,
            "invocation_plan": invocation_plan,
            "plan": invocation_plan,
            "document": invocation_plan,
        }
    )
    invocation_evidence = _b2_call_supported_kwargs(
        evidence_builder,
        evidence_context,
    )

    started_record = _b2_build_started_record(
        attempt_id=attempt_id,
        record_data=started_record_data,
    )

    ledger_contract = execution_attempt_ledger_v0_1.load_contract(
        Path(root).resolve()
    )
    validation_errors = execution_attempt_ledger_v0_1.validate_record_data(
        started_record,
        ledger_contract,
    )
    if validation_errors:
        raise RuntimeError(
            "STARTED record failed canonical ledger validation: "
            + "; ".join(validation_errors)
        )

    launch_values = dict(_b2_find_launch_mapping(invocation_plan))
    launch_values.pop("on_started", None)
    callback_state = {"started_record_appended": False}

    def on_started(*_args, **_kwargs):
        if callback_state["started_record_appended"]:
            raise RuntimeError(
                "STARTED ledger append attempted more than once"
            )

        _b2_call_supported_kwargs(
            cf10_training_dispatch.assert_attempt_unused,
            {
                "root": root,
                "attempt_id": attempt_id,
                "worker_id": worker_id,
            },
        )

        _b2_call_supported_kwargs(
            execution_attempt_ledger_v0_1.append_record,
            {
                "root": root,
                "record": started_record,
                "data": started_record,
                "record_data": started_record,
            },
        )
        callback_state["started_record_appended"] = True

    launch_values["on_started"] = on_started
    process_result = launcher.launch_process(**launch_values)

    if not callback_state["started_record_appended"]:
        raise RuntimeError(
            "Worker process returned without STARTED ledger append"
        )

    return {
        "state": "OBSERVE_WORKER",
        "attempt_id": attempt_id,
        "task_prompt_id": task_prompt_id,
        "worker_id": worker_id,
        "started_record_appended": True,
        "invocation_evidence": invocation_evidence,
        "process_result": _b2_sanitize_process_result(process_result),
        "candidate_promotion_allowed": False,
        "automatic_accept_allowed": False,
        "staging_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "release_allowed": False,
    }
# CF10_GOVERNED_WORKER_CYCLE_SLICE_B2_LIVE_LAUNCH_END
def _validated_project_native_governed_worker_context(
    *,
    prepared_execution: dict[str, Any],
    explicit_dispatch_decision: dict[str, Any],
) -> dict[str, Any]:
    context = prepared_execution.get("governed_worker_context")
    if not isinstance(context, dict):
        raise GovernedWorkerCycleError(
            "prepared governed Worker context missing"
        )
    if context.get("schema_version") != (
        "forprint_governed_worker_context_projection_v0_1"
    ):
        raise GovernedWorkerCycleError(
            "prepared governed Worker context schema invalid"
        )

    prepared_digest = prepared_execution.get(
        "governed_worker_context_sha256"
    )
    if not isinstance(prepared_digest, str) or len(prepared_digest) != 64:
        raise GovernedWorkerCycleError(
            "prepared governed Worker context digest invalid"
        )
    recomputed = governed_worker_context_sha256(context)
    if recomputed != prepared_digest:
        raise GovernedWorkerCycleError(
            "prepared governed Worker context digest drift"
        )

    handoff_hash = prepared_execution.get("handoff_manifest_sha256")
    if context.get("handoff_manifest_sha256") != handoff_hash:
        raise GovernedWorkerCycleError(
            "prepared governed Worker context Handoff binding drift"
        )

    decision_binding = explicit_dispatch_decision.get("binding")
    if not isinstance(decision_binding, dict):
        raise GovernedWorkerCycleError(
            "explicit dispatch decision binding missing"
        )
    if (
        decision_binding.get("governed_worker_context_sha256")
        != prepared_digest
    ):
        raise GovernedWorkerCycleError(
            "explicit dispatch governed Worker context digest drift"
        )

    authority = context.get("authority")
    if not isinstance(authority, dict):
        raise GovernedWorkerCycleError(
            "governed Worker context authority missing"
        )
    required_false = (
        "context_grants_authority",
        "dispatch_authority_granted",
        "release_authority_granted",
        "cross_repository_write_authority_granted",
    )
    widened = [
        key for key in required_false
        if authority.get(key) is not False
    ]
    if widened:
        raise GovernedWorkerCycleError(
            "governed Worker context authority widened: "
            + ",".join(widened)
        )
    return context


def _project_native_started_record(
    *,
    canonical: Path,
    attempt: Path,
    task_prompt_id: str,
    attempt_id: str,
    worker_id: str,
    source_state: dict[str, Any],
    prepared_execution: dict[str, Any],
    explicit_dispatch_decision: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    binding = training.resolve_training_task(
        root=canonical,
        task_prompt_id=task_prompt_id,
    )
    decision_binding = explicit_dispatch_decision.get("binding")
    if not isinstance(decision_binding, dict):
        raise GovernedWorkerCycleError(
            "explicit dispatch decision binding missing"
        )

    task_context = build_internal_task_context(
        canonical,
        task_id=task_prompt_id,
        module_root=".",
    )
    context_state = task_context.get("source_state")
    if not isinstance(context_state, dict):
        raise GovernedWorkerCycleError(
            "project-native task context source_state missing"
        )

    source_fp = source_state.get("fingerprint_sha256")
    context_fp = context_state.get("fingerprint_sha256")
    if (
        not isinstance(source_fp, str)
        or len(source_fp) != 64
        or context_fp != source_fp
    ):
        raise GovernedWorkerCycleError(
            "project-native task context / frozen source fingerprint drift"
        )

    expected = {
        "attempt_id": attempt_id,
        "worker_id": worker_id,
        "task_prompt_id": task_prompt_id,
        "work_front_id": binding["work_front_id"],
        "profile_ref": binding["profile_ref"],
        "procedure_id": binding["procedure_id"],
    }
    observed = {
        "attempt_id": decision_binding.get("attempt_id"),
        "worker_id": decision_binding.get("worker_id"),
        "task_prompt_id": decision_binding.get("task_prompt_id"),
        "work_front_id": decision_binding.get("work_front_id"),
        "profile_ref": decision_binding.get("profile_ref"),
        "procedure_id": decision_binding.get("procedure_id"),
    }
    drift = [
        key
        for key, expected_value in expected.items()
        if observed.get(key) != expected_value
    ]
    if drift:
        raise GovernedWorkerCycleError(
            "explicit dispatch / project-native launch binding drift: "
            + ",".join(drift)
        )

    runtime_provider = decision_binding.get("runtime_provider")
    workspace_repo = decision_binding.get("workspace_repo")
    if not isinstance(runtime_provider, str) or not runtime_provider:
        raise GovernedWorkerCycleError(
            "runtime provider missing from explicit dispatch decision"
        )
    if not isinstance(workspace_repo, str) or not workspace_repo:
        raise GovernedWorkerCycleError(
            "workspace repo missing from explicit dispatch decision"
        )

    handoff_hash = prepared_execution.get("handoff_manifest_sha256")
    if not isinstance(handoff_hash, str) or len(handoff_hash) != 64:
        raise GovernedWorkerCycleError(
            "prepared Handoff manifest hash invalid"
        )

    _validated_project_native_governed_worker_context(
        prepared_execution=prepared_execution,
        explicit_dispatch_decision=explicit_dispatch_decision,
    )

    decision_ref = (
        attempt
        / "input/"
        "governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml"
    )

    record = {
        "schema_version": "forprint_execution_attempt_record_v0_1",
        "attempt_id": attempt_id,
        "work_front_id": binding["work_front_id"],
        "recorded_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "actor_or_worker_ref": (
            f"{worker_id}/provider:{runtime_provider}"
        ),
        "where": workspace_repo,
        "why": (
            "CF-10 governed Worker launch for canonical task "
            f"{task_prompt_id}."
        ),
        "source_fingerprint": source_fp,
        "profile_ref_or_revision": binding["profile_ref"],
        "pack_hash_or_context_hash": handoff_hash,
        "launch_or_invocation_ref": str(decision_ref),
        "attempt_stage": "STARTED",
        "result_state": "PENDING",
        "result_refs": [],
        "validator_outcome": "NOT_RUN",
        "validator_evidence_refs": [],
        "failure_or_retry_ref": None,
        "resume": {
            "latest_accepted_ref": None,
            "resume_coordinates": [],
            "replay_forbidden_refs": [],
        },
    }
    return record, task_context


def _result_return_failure_class(exc: Exception) -> str:
    raw_message = str(exc)
    message = raw_message.lower()
    if "missing result frame" in message:
        return "RESULT_ENVELOPE_MISSING_AFTER_SUCCESSFUL_PROCESS"

    for failure_class in worker_result_return.S4_RESUME_FAILURE_CLASSES:
        if failure_class in raw_message:
            return failure_class

    return "RESULT_ENVELOPE_INVALID_AFTER_PROCESS"


def _terminal_blocked_record(
    *,
    started_record: dict[str, Any],
    failure_class: str,
    evidence_ref: str,
) -> dict[str, Any]:
    record = dict(started_record)
    record["recorded_at"] = datetime.now(UTC).isoformat().replace(
        "+00:00",
        "Z",
    )
    record["attempt_stage"] = "BLOCKED"
    record["result_state"] = "BLOCKED"
    record["result_refs"] = [evidence_ref]
    record["validator_outcome"] = "FAIL"
    record["validator_evidence_refs"] = [
        failure_class,
        evidence_ref,
    ]
    record["failure_or_retry_ref"] = failure_class
    record["resume"] = {
        "latest_accepted_ref": None,
        "resume_coordinates": [],
        "replay_forbidden_refs": [],
    }
    return record


def _append_terminal_blocked_fact(
    *,
    canonical: Path,
    started_record: dict[str, Any],
    failure_class: str,
    evidence_ref: str,
) -> Path:
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger

    contract = ledger.load_contract(canonical)
    record = _terminal_blocked_record(
        started_record=started_record,
        failure_class=failure_class,
        evidence_ref=evidence_ref,
    )
    errors = ledger.validate_record_data(record, contract)
    if errors:
        raise GovernedWorkerCycleError(
            "terminal BLOCKED record failed ledger validation: "
            + "; ".join(errors)
        )
    return ledger.append_record(
        canonical,
        record,
    )


def reconcile_result_return(
    *,
    root: Path | str,
    runtime_root: Path | str,
    task_prompt_id: str,
    attempt_id: str,
    confirm: bool,
    worker_id: str = WORKER_ID,
) -> dict[str, Any]:
    if confirm is not True:
        raise GovernedWorkerCycleError(
            "explicit result-return reconciliation confirmation is required"
        )

    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger

    canonical = Path(root).resolve()
    attempt = _attempt_root(
        Path(runtime_root),
        attempt_id,
        worker_id,
    )
    result_path = attempt / "result/worker_result.yaml"
    if result_path.exists() or result_path.is_symlink():
        raise GovernedWorkerCycleError(
            "result-return reconciliation refused: "
            "worker result already exists"
        )

    binding = training.resolve_training_task(
        root=canonical,
        task_prompt_id=task_prompt_id,
    )

    process_path = (
        attempt
        / "evidence/governed_worker_cycle_worker_process_result_v0_1.yaml"
    )
    process_evidence = _load_yaml(
        process_path,
        "Worker process result",
    )
    process = process_evidence.get("process")
    if not isinstance(process, dict):
        raise GovernedWorkerCycleError(
            "Worker process result mapping missing"
        )

    if (
        process.get("return_code") == 0
        and process.get("timed_out") is False
    ):
        failure_class = (
            "RESULT_ENVELOPE_MISSING_AFTER_SUCCESSFUL_PROCESS"
        )
    elif process.get("timed_out") is True:
        failure_class = "WORKER_PROCESS_TIMED_OUT_BEFORE_VALID_RESULT"
    else:
        failure_class = "WORKER_PROCESS_FAILED_BEFORE_VALID_RESULT"

    contract = ledger.load_contract(canonical)
    store = ledger.store_root(canonical, contract, None)
    records = ledger.records_for_attempt(store, attempt_id)
    if not records:
        raise GovernedWorkerCycleError(
            "result-return reconciliation requires an existing STARTED record"
        )
    latest = records[-1]
    if latest.get("result_state") != "PENDING":
        raise GovernedWorkerCycleError(
            "result-return reconciliation refused: "
            "attempt is already terminal"
        )
    if latest.get("attempt_stage") != "STARTED":
        raise GovernedWorkerCycleError(
            "result-return reconciliation requires STARTED/PENDING attempt"
        )
    if latest.get("work_front_id") != binding.get("work_front_id"):
        raise GovernedWorkerCycleError(
            "result-return reconciliation Work Front binding mismatch"
        )

    evidence_path = (
        attempt
        / "evidence/governed_worker_cycle_result_return_v0_1.yaml"
    )
    evidence = {
        "schema_version": (
            "forprint_governed_worker_cycle_result_return_v0_1"
        ),
        "attempt_id": attempt_id,
        "task_prompt_id": task_prompt_id,
        "worker_id": worker_id,
        "recorded_at": datetime.now(UTC).isoformat().replace(
            "+00:00",
            "Z",
        ),
        "result": "BLOCKED",
        "validation_passed": False,
        "result_path": None,
        "blocked": True,
        "failure_class": failure_class,
        "process_result_evidence": str(process_path),
        "worker_result_synthesized": False,
        "candidate_validation_allowed": False,
        "candidate_promotion_allowed": False,
        "automatic_accept_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "release_allowed": False,
    }
    _write_yaml_new(evidence_path, evidence)

    terminal = _terminal_blocked_record(
        started_record=latest,
        failure_class=failure_class,
        evidence_ref=str(evidence_path),
    )
    errors = ledger.validate_record_data(terminal, contract)
    if errors:
        raise GovernedWorkerCycleError(
            "terminal BLOCKED record failed ledger validation: "
            + "; ".join(errors)
        )
    ledger_path = ledger.append_record(
        canonical,
        terminal,
    )

    return {
        "schema_version": (
            "forprint_governed_worker_cycle_result_return_reconciliation_v0_1"
        ),
        "state": "BLOCKED",
        "next_boundary": "RECONCILE_BLOCKER",
        "attempt_id": attempt_id,
        "task_prompt_id": task_prompt_id,
        "failure_class": failure_class,
        "result_return_evidence": str(evidence_path),
        "terminal_ledger_record": str(ledger_path),
        "worker_result_synthesized": False,
        "candidate_validation_allowed": False,
        "candidate_promotion_allowed": False,
        "automatic_retry": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "release_allowed": False,
    }


def launch_cycle(
    *,
    root: Path | str,
    runtime_root: Path | str,
    task_prompt_id: str,
    attempt_id: str,
    confirm: bool,
    worker_id: str = WORKER_ID,
) -> dict[str, Any]:
    """Launch one already-authorized Worker through canonical project surfaces."""

    if confirm is not True:
        raise GovernedWorkerCycleError(
            "explicit --confirm-launch is required"
        )

    canonical = Path(root).resolve()
    runtime = Path(runtime_root).resolve()
    attempt = _attempt_root(runtime, attempt_id, worker_id)
    input_dir = attempt / "input"

    source_state = _load_yaml(
        input_dir / "governed_worker_cycle_source_state_v0_1.yaml",
        "source state",
    )
    prepared_execution = _load_yaml(
        input_dir / "governed_worker_cycle_prepared_execution_v0_1.yaml",
        "prepared execution",
    )
    explicit_dispatch_decision = _load_yaml(
        input_dir
        / "governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml",
        "explicit dispatch decision",
    )

    _assert_frozen_source_state_current(
        canonical,
        source_state,
        boundary="project-native Worker launch",
    )

    started_record, task_context = _project_native_started_record(
        canonical=canonical,
        attempt=attempt,
        task_prompt_id=task_prompt_id,
        attempt_id=attempt_id,
        worker_id=worker_id,
        source_state=source_state,
        prepared_execution=prepared_execution,
        explicit_dispatch_decision=explicit_dispatch_decision,
    )
    governed_worker_context = (
        _validated_project_native_governed_worker_context(
            prepared_execution=prepared_execution,
            explicit_dispatch_decision=explicit_dispatch_decision,
        )
    )

    result = launch_authorized_worker_cycle(
        root=canonical,
        runtime_root=runtime,
        task_prompt_id=task_prompt_id,
        attempt_id=attempt_id,
        worker_id=worker_id,
        started_record_data=started_record,
        invocation_context={
            "task_context": task_context,
            "governed_worker_context": governed_worker_context,
            "explicit_dispatch_decision": explicit_dispatch_decision,
            "attempt_root": attempt,
        },
    )

    process = result.get("process_result")
    if not isinstance(process, dict):
        raise GovernedWorkerCycleError(
            "sanitized Worker process result missing"
        )

    evidence = {
        "schema_version": (
            "forprint_governed_worker_cycle_worker_process_result_v0_1"
        ),
        "attempt_id": attempt_id,
        "task_prompt_id": task_prompt_id,
        "worker_id": worker_id,
        "recorded_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "invocation_evidence": result.get("invocation_evidence"),
        "process": process,
        "candidate_promotion_allowed": False,
        "automatic_accept_allowed": False,
        "staging_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "release_allowed": False,
    }
    evidence_path = (
        attempt
        / "evidence/"
        "governed_worker_cycle_worker_process_result_v0_1.yaml"
    )
    _write_yaml_new(evidence_path, evidence)

    result_return_evidence_path = (
        attempt
        / "evidence/governed_worker_cycle_result_return_v0_1.yaml"
    )
    return_code = process.get("return_code")
    timed_out = process.get("timed_out") is True

    if return_code == 0 and not timed_out:
        handoff_hash = prepared_execution.get(
            "handoff_manifest_sha256"
        )
        if not isinstance(handoff_hash, str) or len(handoff_hash) != 64:
            raise GovernedWorkerCycleError(
                "prepared Handoff manifest hash invalid at result return"
            )
        stdout_path = process.get("stdout_path")
        if not isinstance(stdout_path, str) or not stdout_path:
            raise GovernedWorkerCycleError(
                "Worker process stdout path missing at result return"
            )

        try:
            materialized = worker_result_return.materialize_worker_result(
                root=canonical,
                attempt_root=attempt,
                stdout_path=stdout_path,
                origin_manifest={
                    "handoff_manifest_sha256": handoff_hash,
                },
                expected_attempt_id=attempt_id,
                governed_worker_context=governed_worker_context,
            )
            result_return_evidence = {
                "schema_version": (
                    "forprint_governed_worker_cycle_result_return_v0_1"
                ),
                "attempt_id": attempt_id,
                "task_prompt_id": task_prompt_id,
                "worker_id": worker_id,
                "recorded_at": datetime.now(UTC).isoformat().replace(
                    "+00:00",
                    "Z",
                ),
                "result": "PASS",
                "validation_passed": True,
                "result_path": materialized["result_path"],
                "blocked": False,
                "failure_class": None,
                "worker_result_synthesized": False,
                "candidate_validation_allowed": True,
                "candidate_promotion_allowed": False,
                "automatic_accept_allowed": False,
                "commit_allowed": False,
                "push_allowed": False,
                "merge_allowed": False,
                "release_allowed": False,
            }
        except worker_result_return.WorkerResultReturnError as exc:
            failure_class = _result_return_failure_class(exc)
            result_return_evidence = {
                "schema_version": (
                    "forprint_governed_worker_cycle_result_return_v0_1"
                ),
                "attempt_id": attempt_id,
                "task_prompt_id": task_prompt_id,
                "worker_id": worker_id,
                "recorded_at": datetime.now(UTC).isoformat().replace(
                    "+00:00",
                    "Z",
                ),
                "result": "BLOCKED",
                "validation_passed": False,
                "result_path": None,
                "blocked": True,
                "failure_class": failure_class,
                "error": (
                    f"{type(exc).__name__}: {exc}"
                ),
                "worker_result_synthesized": False,
                "candidate_validation_allowed": False,
                "candidate_promotion_allowed": False,
                "automatic_accept_allowed": False,
                "commit_allowed": False,
                "push_allowed": False,
                "merge_allowed": False,
                "release_allowed": False,
            }
    else:
        failure_class = (
            "WORKER_PROCESS_TIMED_OUT_BEFORE_VALID_RESULT"
            if timed_out
            else "WORKER_PROCESS_FAILED_BEFORE_VALID_RESULT"
        )
        result_return_evidence = {
            "schema_version": (
                "forprint_governed_worker_cycle_result_return_v0_1"
            ),
            "attempt_id": attempt_id,
            "task_prompt_id": task_prompt_id,
            "worker_id": worker_id,
            "recorded_at": datetime.now(UTC).isoformat().replace(
                "+00:00",
                "Z",
            ),
            "result": "BLOCKED",
            "validation_passed": False,
            "result_path": None,
            "blocked": True,
            "failure_class": failure_class,
            "worker_result_synthesized": False,
            "candidate_validation_allowed": False,
            "candidate_promotion_allowed": False,
            "automatic_accept_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
            "release_allowed": False,
        }

    _write_yaml_new(
        result_return_evidence_path,
        result_return_evidence,
    )

    terminal_ledger_path = None
    if result_return_evidence.get("blocked") is True:
        terminal_ledger_path = _append_terminal_blocked_fact(
            canonical=canonical,
            started_record=started_record,
            failure_class=str(
                result_return_evidence["failure_class"]
            ),
            evidence_ref=str(result_return_evidence_path),
        )

    projection = status(
        root=canonical,
        runtime_root=runtime,
        task_prompt_id=task_prompt_id,
        attempt_id=attempt_id,
        worker_id=worker_id,
    )
    projection["worker_process_launched"] = True
    projection["process_return_code"] = process.get("return_code")
    projection["process_result_evidence"] = str(evidence_path)
    projection["result_return_evidence"] = str(
        result_return_evidence_path
    )
    if terminal_ledger_path is not None:
        projection["terminal_ledger_record"] = str(
            terminal_ledger_path
        )
    return projection


if __name__ == "__main__":
    raise SystemExit(main())
