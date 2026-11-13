"""CF10 S01 controlled-launch corridor *read-only gap preflight* v0.1.

No claim, spawn, ledger write, /etc or /var/lib mutation, Make wiring or authority.
This inspects existing independently verified components and *requires* both
Python entrypoints to be guarded by a separately reviewed implementation.
The CLI can never return a positive live launch preflight.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

SCHEMA = "cf10_s01_controlled_launch_corridor_v0_1"
ENTRYPOINTS = ("launch_cycle", "launch_authorized_worker_cycle")
REQUIRED_GUARD = "require_bounded_s01_launch_authority"
LIVE_MAKE_QUARANTINE = "QUARANTINED_NEEDS_INDEPENDENT_REBIND"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git_head(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=20, check=True)
    return result.stdout.decode().strip()


def _functions(source: str) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    module = ast.parse(source)
    return {node.name: node for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _has_guard_call(node: ast.AST) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and (
            isinstance(sub.func, ast.Name) and sub.func.id == REQUIRED_GUARD
            or isinstance(sub.func, ast.Attribute) and sub.func.attr == REQUIRED_GUARD
        ):
            return True
    return False


def launch_route_blockers(root: Path) -> list[str]:
    """Necessary static evidence only; never sufficient for bypass coverage."""
    rel = "scripts/coordination/control_plane/governed_worker_cycle.py"
    path = root / rel
    if path.is_symlink() or not path.is_file():
        return ["GOVERNED_CYCLE_SOURCE_UNAVAILABLE"]
    try:
        methods = _functions(path.read_text("utf-8"))
    except (ValueError, UnicodeError, SyntaxError, OSError):
        return ["GOVERNED_CYCLE_SOURCE_UNREADABLE"]
    blockers = []
    for name in ENTRYPOINTS:
        node = methods.get(name)
        if node is None or not _has_guard_call(node):
            blockers.append("DIRECT_PYTHON_LAUNCH_UNGUARDED:" + name)
    # An AST call is only a precondition; external independent runtime coverage
    # and negative bypass proofs remain mandatory before production launch.
    return blockers


def _signed_binding(root: Path, *, worker_id: str, task_prompt_id: str,
                    attempt_id: str) -> tuple[dict[str, str] | None, list[str]]:
    from scripts.coordination.control_plane import cf10_s01_runtime_rebind_v0_2 as rebind
    errors: list[str] = []
    predicate = rebind.evaluate(root, worker_id=worker_id,
                                task_prompt_id=task_prompt_id, attempt_id=attempt_id)
    if (predicate.get("predicate_pass") is not True
            or predicate.get("status") != "PREDICATE_PASS_NON_AUTHORIZING"
            or predicate.get("blockers") != []
            or predicate.get("launch_allowed") is not False
            or predicate.get("authority_granted") is not False):
        return None, ["SIGNED_PILOT_PREDICATE_NOT_VERIFIED"]
    try:
        head = _git_head(root)
        receipt, raw = rebind._trusted_json(rebind.RECEIPT_FILE)
        if not rebind._reverify_receipt(root, head, receipt):
            errors.append("RELEASE_RECEIPT_SIGNATURE_REREAD_FAILED")
        errors.extend(rebind.scope_blockers(receipt, worker_id=worker_id,
                                            task_prompt_id=task_prompt_id,
                                            attempt_id=attempt_id))
        proof_errors, proof_count = rebind.proof_blockers(receipt, head)
        errors.extend(proof_errors)
        if proof_count != len(rebind.REQUIREMENTS):
            errors.append("INDEPENDENT_PROOF_MATRIX_NOT_ACCEPTED")
        if _git_head(root) != head:
            errors.append("SOURCE_HEAD_CHANGED_DURING_CORRIDOR")
        if errors:
            return None, sorted(set(errors))
        return {"receipt_sha256": _sha(raw), "publication_commit": head,
                "worker_id": worker_id, "task_prompt_id": task_prompt_id,
                "attempt_id": attempt_id}, []
    except Exception:
        return None, ["SIGNED_BINDING_UNAVAILABLE_OR_DRIFTED"]


def _root_state_readiness() -> str:
    """Open the pre-provisioned root directory without creating or consuming."""
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as state
    try:
        dfd = state.open_root_owned_state_dir()
    except Exception:
        return "ROOT_CONTROLLED_STATE_NOT_VERIFIED"
    try:
        try:
            os.stat(state.MARKER, dir_fd=dfd, follow_symlinks=False)
            return "PERSISTENT_SINGLE_USE_ALREADY_CONSUMED"
        except FileNotFoundError:
            return "READY_READ_ONLY_NOT_RESERVED"
        except OSError:
            return "PERSISTENT_STATE_NOT_INSPECTABLE"
    finally:
        os.close(dfd)


def evaluate(root: Path, *, worker_id: str, task_prompt_id: str,
             attempt_id: str) -> dict[str, Any]:
    """Never returns launch authority, even if all necessary checks pass."""
    root = root.resolve()
    blockers: list[str] = []
    checks: dict[str, Any] = {"signed_predicate": "NOT_CHECKED",
                               "exact_receipt_binding": "NOT_VERIFIED",
                               "persistent_state": "NOT_CHECKED",
                               "python_routes": "NOT_GUARDED",
                               "live_make": "NOT_CHECKED"}
    binding = None
    if not worker_id or not task_prompt_id or not attempt_id:
        blockers.append("EXPLICIT_WORKER_TASK_ATTEMPT_REQUIRED")
    else:
        try:
            from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as state
            binding, binding_errors = _signed_binding(root, worker_id=worker_id,
                                                       task_prompt_id=task_prompt_id,
                                                       attempt_id=attempt_id)
            blockers.extend(binding_errors)
            if binding is not None:
                if state.validate_binding(binding):
                    blockers.append("ROOT_CLAIM_BINDING_CONTRACT_MISMATCH")
                else:
                    checks["signed_predicate"] = "PASS"
                    checks["exact_receipt_binding"] = "VERIFIED_READ_ONLY"
        except Exception:
            blockers.append("SIGNED_CORRIDOR_EVALUATION_UNAVAILABLE")
        checks["persistent_state"] = _root_state_readiness()
        if checks["persistent_state"] != "READY_READ_ONLY_NOT_RESERVED":
            blockers.append(checks["persistent_state"])

    routes = launch_route_blockers(root)
    blockers.extend(routes)
    checks["python_routes"] = "STATIC_GUARD_REFERENCES_PRESENT" if not routes else "UNGUARDED"
    try:
        make = (root / "Makefile").read_text("utf-8")
        if LIVE_MAKE_QUARANTINE in make:
            checks["live_make"] = "LITERAL_QUARANTINE_RETAINED"
            blockers.append("LIVE_MAKE_QUARANTINE_RETAINED")
        else:
            blockers.append("LIVE_MAKE_QUARANTINE_ABSENT_REQUIRES_INDEPENDENT_REVIEW")
            checks["live_make"] = "NOT_PROVEN_SAFE"
    except Exception:
        blockers.append("MAKEFILE_UNAVAILABLE")
    return {"schema_version": SCHEMA, "status": "BLOCKED_NON_AUTHORIZING",
            "blockers": sorted(set(blockers)), "checks": checks,
            "signed_binding_sha256": _sha(json.dumps(binding, sort_keys=True,
                separators=(",", ":")).encode()) if binding is not None else None,
            "worker_id": worker_id or None, "task_prompt_id": task_prompt_id or None,
            "attempt_id": attempt_id or None,
            "claim_record_written": False, "claim_consumed": False,
            "launch_allowed": False, "authority_granted": False,
            "live_make_wired": False, "worker_launched": False,
            "canonical_ledger_modified": False,
            "independent_runtime_coverage_attested_by_candidate": False}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("inspect", "launch-preflight"))
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--worker-id", default="")
    p.add_argument("--task-prompt-id", default="")
    p.add_argument("--attempt-id", default="")
    args = p.parse_args(argv)
    try:
        result = evaluate(args.root, worker_id=args.worker_id,
                          task_prompt_id=args.task_prompt_id,
                          attempt_id=args.attempt_id)
    except Exception:
        result = {"schema_version": SCHEMA, "status": "BLOCKED_NON_AUTHORIZING",
                  "blockers": ["UNEXPECTED_CORRIDOR_INSPECTION_FAILURE"],
                  "claim_record_written": False, "launch_allowed": False,
                  "authority_granted": False, "worker_launched": False}
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
    # This source is never a live prerequisite. The future independently reviewed
    # privileged corridor must own both atomic claim and Worker spawn.
    return 0 if args.mode == "inspect" else 2


if __name__ == "__main__":
    raise SystemExit(main())
