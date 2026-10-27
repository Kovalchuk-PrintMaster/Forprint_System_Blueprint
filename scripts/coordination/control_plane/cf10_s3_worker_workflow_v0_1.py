#!/usr/bin/env python3
"""CF-10 S3: bounded post-worker status/run/resume/report, reusing governed authority.

No new dispatcher, retry policy, task selection or acceptance. Mutating advance
MUST route through the existing Make target and its deployment preflight.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable

import yaml

SCHEMA = "cf10_s3_bounded_worker_workflow_v0_1"
IDENT = re.compile(r"^[a-z0-9][a-z0-9-]{2,110}$")
ADVANCE_STATES = frozenset({"VALIDATE_CANDIDATE", "FINALIZE_HANDOFF", "ATTEMPT_TERMINAL"})
REVIEW_STATE = "AWAITING_OPERATOR_REVIEW"


class WorkflowBlocked(RuntimeError):
    pass


def require(ok: bool, why: str) -> None:
    if not ok:
        raise WorkflowBlocked(why)


def _status(root: Path, runtime: Path, task: str, attempt: str) -> dict:
    from scripts.coordination.control_plane.governed_worker_cycle import status
    return status(root=root, runtime_root=runtime, task_prompt_id=task, attempt_id=attempt)


def _report(root: Path, runtime: Path, task: str, attempt: str) -> dict:
    from scripts.coordination.control_plane.cf10_attempt_operator_report_v0_2 import collect
    return collect(root, runtime, task, attempt)


def _overlay(root: Path, runtime: Path, proof: Path, task: str, attempt: str) -> dict:
    from scripts.coordination.control_plane.cf10_zero_delta_status_projection_v0_1 import project
    return project(root, runtime, proof, task, attempt)


def _advance_via_existing_make(root: Path, runtime: Path, task: str, attempt: str, python: str) -> dict:
    """The Make prerequisite preflight cannot be bypassed by this adapter."""
    args = ["make", "-s", "governed-worker-cycle-advance",
            "GOVERNED_WORKER_TASK=" + task,
            "GOVERNED_WORKER_ATTEMPT=" + attempt,
            "GOVERNED_WORKER_RUNTIME_ROOT=" + str(runtime),
            "PYTHON=" + python]
    cp = subprocess.run(args, cwd=root, capture_output=True, text=True, check=False, timeout=1200)
    require(cp.returncode == 0, "NATIVE_MAKE_ADVANCE_FAILED:rc=" + str(cp.returncode) + ":" + cp.stderr[-500:])
    # Make may emit preflight messages before the YAML. Return raw stdout;
    # the canonical source of state is a fresh status() read, not parsing stdout.
    return {"delegated_to": "governed-worker-cycle-advance",
            "return_code": cp.returncode, "stdout_tail": cp.stdout[-1500:]}


def inspect(root: Path, runtime: Path, task: str, attempt: str, proof: Path | None = None,
            *, status_fn: Callable = _status, report_fn: Callable = _report,
            overlay_fn: Callable = _overlay) -> dict[str, Any]:
    require(bool(IDENT.fullmatch(attempt)) and bool(IDENT.fullmatch(task)), "INVALID_IDS")
    projection = status_fn(root, runtime, task, attempt)
    require(isinstance(projection, dict), "INVALID_GOVERNED_STATUS")
    require(projection.get("derived_non_authoritative") is True,
            "GOVERNED_STATUS_MUST_BE_NON_AUTHORITATIVE")
    require(projection.get("task_prompt_id") in (None, task) and projection.get("attempt_id") in (None, attempt),
            "GOVERNED_STATUS_IDENTITY_MISMATCH")
    state = projection.get("state")
    facts = projection.get("facts") or {}
    require(isinstance(facts, dict), "INVALID_GOVERNED_FACTS")
    result: dict[str, Any] = {
        "schema_version": SCHEMA, "report_role": "DERIVED_NON_AUTHORITATIVE",
        "attempt_id": attempt, "task_prompt_id": task,
        "governed_state": state, "governed_boundary": projection.get("next_boundary"),
        "classification": "STOP_FOR_GOVERNED_BOUNDARY", "next_action": "INSPECT_GOVERNED_STATUS",
        "execution_performed": False, "mutating_advance_allowed": False,
        "operator_decision_written": False, "automatic_dispatch": False,
        "automatic_accept": False, "automatic_promotion": False,
        "automatic_commit": False, "automatic_push": False,
        "automatic_publication": False, "roadmap_lifecycle_closed": False,
    }
    if state in ("BLOCKED", "UNKNOWN") or projection.get("contradictions"):
        return {**result, "classification": "BLOCKED", "next_action": "OPERATOR_DIAGNOSIS",
                "blockers": list(projection.get("contradictions") or ["GOVERNED_STATE_" + str(state)])}
    if state == REVIEW_STATE:
        s1 = report_fn(root, runtime, task, attempt)
        require(isinstance(s1, dict), "S1_NOT_MAPPING")
        blockers = s1.get("blockers")
        if blockers:
            return {**result, "classification": "BLOCKED", "next_action": "INVESTIGATE_S1_EVIDENCE",
                    "blockers": blockers}
        require(s1.get("attempt_id") == attempt and s1.get("task_prompt_id") == task,
                "S1_IDENTITY_MISMATCH")
        changes = s1.get("declared_changed_paths")
        out = {**result, "classification": "OPERATOR_GATE", "next_action": "EXPLICIT_OPERATOR_REVIEW",
               "worker_result_status": s1.get("worker_result_status"),
               "changed_paths": changes, "operator_decision": s1.get("operator_decision_state"),
               "s1_result_classification": s1.get("result_classification"),
               "evidence_validated_by_s1": True}
        if changes == [] and proof is not None:
            overlay = overlay_fn(root, runtime, proof, task, attempt)
            require(isinstance(overlay, dict) and overlay.get("review_evidence_validated") is True,
                    "S2C_NOT_VALIDATED")
            require(overlay.get("attempt_id") == attempt and overlay.get("task_prompt_id") == task,
                    "S2C_IDENTITY_MISMATCH")
            require(overlay.get("next_dispatch_authorized") is False and
                    overlay.get("roadmap_lifecycle_closed") is False,
                    "S2C_AUTHORITY_WIDENED")
            out["review_overlay_state"] = overlay.get("review_overlay_state")
            out["operator_decision"] = overlay.get("decision")
            out["next_action"] = overlay.get("next_boundary")
            out["decision_record_sha256"] = overlay.get("decision_record_sha256")
        elif changes == []:
            out["next_action"] = "PROVIDE_ATTEMPT_BOUND_S2A_PROOF_FOR_ZERO_DELTA_OVERLAY"
        return out
    if state in ADVANCE_STATES:
        finished = facts.get("worker_process_finished") is True
        returned = facts.get("worker_result_return_valid") is True
        not_blocked = facts.get("blocked") is not True and facts.get("worker_result_return_blocked") is not True
        not_terminal = facts.get("attempt_terminal_pass") is not True and facts.get("attempt_terminal_failed") is not True
        if finished and returned and not_blocked and not_terminal:
            return {**result, "classification": "READY_FOR_BOUND_POSTWORKER_ADVANCE",
                    "next_action": "EXISTING_GOVERNED_MAKE_ADVANCE", "mutating_advance_allowed": True}
        return {**result, "classification": "BLOCKED",
                "next_action": "RESOLVE_EXISTING_RESULT_RETURN_OR_VALIDATION",
                "blockers": ["POSTWORKER_ADVANCE_PRECONDITIONS_UNSATISFIED"]}
    if state == "OBSERVE_WORKER":
        return {**result, "classification": "WAIT_FOR_WORKER_RESULT",
                "next_action": "RECHECK_AFTER_WORKER_PROCESS_EXIT"}
    if state == "READY_FOR_WORKER_LAUNCH":
        return {**result, "classification": "OPERATOR_GATE",
                "next_action": "EXISTING_EXPLICIT_WORKER_LAUNCH_GATE"}
    if state == "READY_FOR_EXPLICIT_DISPATCH":
        return {**result, "classification": "OPERATOR_GATE",
                "next_action": "EXISTING_EXPLICIT_DISPATCH_GATE"}
    if state in ("PROMOTE_CANDIDATE", "CANONICAL_VALIDATION", "AWAITING_PUBLICATION_APPROVAL",
                 "VERIFY_REMOTE_CONTAINMENT", "PUBLISHED"):
        return {**result, "classification": "OPERATOR_OR_EXISTING_GOVERNANCE_GATE",
                "next_action": "REVIEW_PROMOTION_PUBLICATION_POLICY"}
    return result


def run_one(root: Path, runtime: Path, task: str, attempt: str, proof: Path | None,
            python: str, *, status_fn: Callable = _status,
            report_fn: Callable = _report, overlay_fn: Callable = _overlay,
            advance_fn: Callable = _advance_via_existing_make) -> dict:
    first = inspect(root, runtime, task, attempt, proof,
                    status_fn=status_fn, report_fn=report_fn, overlay_fn=overlay_fn)
    if first["classification"] != "READY_FOR_BOUND_POSTWORKER_ADVANCE":
        return {**first, "run_action": "NO_MUTATION_OR_GATE_REACHED"}
    launched = advance_fn(root, runtime, task, attempt, python)
    after = inspect(root, runtime, task, attempt, proof,
                    status_fn=status_fn, report_fn=report_fn, overlay_fn=overlay_fn)
    require(after["governed_state"] in (REVIEW_STATE, "BLOCKED", "UNKNOWN"),
            "ADVANCE_DID_NOT_REACH_EXPECTED_BOUNDARY")
    return {**after, "execution_performed": True,
            "run_action": "EXISTING_MAKE_ADVANCE_EXECUTED", "advance_result": launched}


def report_attempt(root: Path, runtime: Path, task: str, attempt: str, proof: Path | None,
                   output: Path, *, status_fn: Callable = _status,
                   report_fn: Callable = _report,
                   overlay_fn: Callable = _overlay, write_fn: Callable | None = None) -> dict:
    current = inspect(root, runtime, task, attempt, proof,
                      status_fn=status_fn, report_fn=report_fn, overlay_fn=overlay_fn)
    require(current["governed_state"] == REVIEW_STATE and current["classification"] == "OPERATOR_GATE",
            "REPORT_REQUIRES_VALID_TERMINAL_OPERATOR_REVIEW")
    report = report_fn(root, runtime, task, attempt)
    require(report.get("blockers") == [], "S1_REPORT_HAS_BLOCKERS")
    if write_fn is None:
        from scripts.coordination.control_plane.cf10_attempt_operator_report_v0_2 import write_preview
        write_fn = write_preview
    archive = write_fn(root, report, output)
    return {**current, "report_artifact": str(archive), "run_action": "S1_REPORT_WRITTEN_IN_TMP"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "run", "resume", "report"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--runtime-root", type=Path, default=Path("/srv/software_development/forprint-worker-runtime"))
    parser.add_argument("--task", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--proof-file", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--python", default=".venv_blueprint/bin/python")
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    a = parser.parse_args(argv)
    try:
        root = a.root.resolve(strict=True)
        require(root.name == "forprint_system_blueprint" and (root / ".git").exists(),
                "EXPECTED_BLUEPRINT_REPOSITORY")
        runtime = a.runtime_root.resolve(strict=True)
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        proof = a.proof_file
        if proof is not None:
            require(not proof.is_symlink(), "PROOF_FILE_IS_SYMLINK")
            proof = proof.resolve(strict=True)
            require(proof.is_file() and proof.is_relative_to((root / "tmp").resolve(strict=True)),
                    "PROOF_NOT_BOUND_TO_BLUEPRINT_TMP")
        if a.action == "status":
            data = inspect(root, runtime, a.task, a.attempt_id, proof)
        elif a.action in ("run", "resume"):
            data = run_one(root, runtime, a.task, a.attempt_id, proof, a.python)
        else:
            require(a.output_dir is not None, "REPORT_OUTPUT_DIR_REQUIRED")
            data = report_attempt(root, runtime, a.task, a.attempt_id, proof, a.output_dir)
        if a.format == "json":
            print(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
        return 0 if data.get("classification") != "BLOCKED" else 2
    except (WorkflowBlocked, OSError, ValueError, TypeError, RuntimeError, yaml.YAMLError,
            subprocess.TimeoutExpired) as exc:
        print("CF10_S3_BLOCKED=" + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
