"""S01 one-attempt governed pilot launch *REVIEW CANDIDATE*.

This source is not installed/wired by the package.  No signer or authority is
created here. Only independently approved integration may expose the CLI.

Trust relies on a root-only OS execution boundary and on the canonical,
independently provisioned Ed25519 activation/release trust stores. It is not a
security boundary against arbitrary hostile Python code already running as root.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

WORKER = "worker-01"
PROJECT = Path("/srv/software_development/forprint-project/forprint_system_blueprint")
RUNTIME = Path("/srv/software_development/forprint-worker-runtime")
BRANCH = "audit/blueprint-inventory-refresh-2026-07-29"
_SHA40 = re.compile(r"[a-f0-9]{40}\Z")


class PilotLaunchBlocked(RuntimeError):
    pass


@dataclass
class _Session:
    root: Path
    worker: str
    task: str
    attempt: str
    head: str
    expires_at: datetime
    phase: str = "READY"


# Private in-process guard; never usable as externally supplied authority.
_SESSION: ContextVar[_Session | None] = ContextVar("cf10_s01_review_candidate_session", default=None)


def _fail(code: str):
    raise PilotLaunchBlocked(code)


def _utc(s: object) -> datetime:
    if not isinstance(s, str):
        _fail("SIGNED_TIME_FIELD_INVALID")
    try:
        value = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        _fail("SIGNED_TIME_FIELD_INVALID")
    if value.tzinfo is None:
        _fail("SIGNED_TIMEZONE_MISSING")
    return value.astimezone(timezone.utc)


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=20, check=True)
    return proc.stdout.decode("utf-8").strip()


def _head(root: Path) -> str:
    value = _git(root, "rev-parse", "HEAD")
    if not _SHA40.fullmatch(value):
        _fail("HEAD_FORMAT_INVALID")
    return value


def require_live_session(*, root: Path | str, task_prompt_id: str,
                         attempt_id: str, worker_id: str, route: str) -> None:
    """Two entrypoints must enter one authorized, consumed single-use session.

    Strict session scopes ensure a direct Python call without the root-controlled
    corridor fails before it reads attempt state or appends to the ledger.
    """
    s = _SESSION.get()
    if s is None or os.geteuid() != 0:
        _fail("S01_ROOT_AUTHORIZED_SESSION_REQUIRED")
    if (Path(root).resolve() != s.root or worker_id != s.worker
            or task_prompt_id != s.task or attempt_id != s.attempt):
        _fail("S01_SIGNED_PILOT_SCOPE_DRIFT")
    if datetime.now(timezone.utc) >= s.expires_at:
        _fail("S01_SIGNED_LEASE_EXPIRED_DURING_LAUNCH")
    # Recheck both guarded Python entrypoints *inside the same process*.
    # Outer preclaim checks alone cannot rule out a source/HEAD change before
    # the inner call that reaches the actual Worker invocation adapter.
    if _head(s.root) != s.head:
        _fail("S01_SOURCE_HEAD_CHANGED_WITHIN_LAUNCH")
    _assert_reviewed_live_source(s.root, s.head)
    if route == "launch_cycle" and s.phase == "READY":
        s.phase = "OUTER_ENTERED"
    elif route == "launch_authorized_worker_cycle" and s.phase == "OUTER_ENTERED":
        s.phase = "INNER_ENTERED"
    else:
        _fail("S01_UNEXPECTED_OR_REPEATED_LAUNCH_ROUTE")


def _authenticate(root: Path, *, task: str, attempt: str) -> tuple[dict, datetime]:
    """Recheck canonical trusted readers and all 8 root-controlled proof rows."""
    from scripts.coordination import execution_attempt_writer_activation_v0_1 as activation
    from scripts.coordination.control_plane import cf10_s01_runtime_rebind_v0_2 as rebind
    from scripts.coordination.control_plane import cf10_s01_release_gate_candidate_v0_1 as release

    gate = activation.evaluate(root, stage="verify")
    if gate.get("status") != "PASS" or gate.get("blockers") != []:
        _fail("WRITER_ACTIVATION_NOT_VERIFIED")
    predicate = rebind.evaluate(root, worker_id=WORKER, task_prompt_id=task, attempt_id=attempt)
    if (predicate.get("status") != "PREDICATE_PASS_NON_AUTHORIZING"
            or predicate.get("predicate_pass") is not True or predicate.get("blockers") != []
            or predicate.get("checks", {}).get("proof_files_verified") != len(rebind.REQUIREMENTS)):
        _fail("SIGNED_RELEASE_SCOPE_OR_PROOF_MATRIX_NOT_VERIFIED")

    receipt, raw = activation.trusted_json(rebind.RECEIPT_FILE)
    if not rebind._reverify_receipt(root, _head(root), receipt):
        _fail("RELEASE_RECEIPT_SIGNATURE_RECHECK_FAILED")
    if rebind.scope_blockers(receipt, worker_id=WORKER, task_prompt_id=task, attempt_id=attempt):
        _fail("RELEASE_PILOT_SCOPE_DRIFT")
    proof_errors, proof_count = rebind.proof_blockers(receipt, _head(root))
    if proof_errors or proof_count != len(rebind.REQUIREMENTS):
        _fail("INDEPENDENT_PROOFS_REREAD_FAILED")
    activation_doc, _ = activation.trusted_json(activation.DECISION_FILE)
    now = datetime.now(timezone.utc)
    expiry = min(_utc(receipt.get("expires_at")), _utc(activation_doc.get("expires_at")))
    if expiry <= now:
        _fail("SIGNED_LEASE_EXPIRED_BEFORE_CLAIM")
    binding = {
        "receipt_sha256": hashlib.sha256(raw).hexdigest(),
        "publication_commit": _head(root),
        "worker_id": WORKER, "task_prompt_id": task, "attempt_id": attempt,
    }
    return binding, expiry


def _assert_reviewed_live_source(root: Path, head: str) -> None:
    """The live path must be reviewed, published and bound to the Make target.

    A bare module installed via untracked tmp or an edited Makefile must not
    become an alternative CLI route around the original quarantine.
    """
    # All major code-bearing enforcement / runtime dependencies must equal
    # published Git objects. These are necessary source pins, not a claim that
    # arbitrary root code or external hosts are fully covered.
    rels = (
        "Makefile",
        "scripts/coordination/control_plane/governed_worker_cycle.py",
        "scripts/coordination/control_plane/cf10_s01_live_pilot_corridor_v0_1.py",
        "scripts/coordination/control_plane/cf10_s01_release_gate_candidate_v0_1.py",
        "scripts/coordination/control_plane/cf10_s01_runtime_rebind_v0_2.py",
        "scripts/coordination/control_plane/cf10_s01_root_controlled_single_use_v0_2.py",
        "scripts/coordination/execution_attempt_writer_activation_v0_1.py",
        "scripts/coordination/execution_attempt_writer_lock_v0_1.py",
        "scripts/coordination/execution_attempt_ledger_v0_1.py",
        "scripts/coordination/control_plane/cf10_training_dispatch.py",
        "scripts/coordination/control_plane/worker_runtime/invocation_adapter.py",
        "scripts/coordination/control_plane/worker_runtime/launcher.py",
    )
    for rel in rels:
        path = root / rel
        if not path.is_file() or path.is_symlink():
            _fail("S01_PUBLISHED_LIVE_SOURCE_UNAVAILABLE")
        try:
            frozen = subprocess.run(["git", "show", head + ":" + rel], cwd=root,
                                    capture_output=True, timeout=20, check=True).stdout
        except (OSError, subprocess.SubprocessError):
            _fail("S01_PUBLISHED_LIVE_SOURCE_UNAVAILABLE")
        if frozen != path.read_bytes():
            _fail("S01_LIVE_SOURCE_WORKTREE_DRIFT")
    make = (root / "Makefile").read_text("utf-8")
    marker = "CF10_S01_AUTHORIZED_ONE_SHOT_LAUNCH_V0_1"
    if marker not in make or "cf10_s01_live_pilot_corridor_v0_1 launch" not in make:
        _fail("S01_INDEPENDENT_MAKE_BINDING_NOT_PUBLISHED")


def _preclaim_cycle_readiness(root: Path, runtime: Path, task: str, attempt: str) -> None:
    """Avoid consuming the single-use slot when the attempt is already unready."""
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    # Canonical runtime facts/projection; this is read-only and never a substitute
    # for the second source-state checks inside the canonical launch functions.
    facts = cycle.live_facts(root=root, runtime_root=runtime, task_prompt_id=task,
                             attempt_id=attempt, worker_id=WORKER)
    projection = cycle.derive_cycle_projection(facts)
    if projection.get("state") != "READY_FOR_WORKER_LAUNCH":
        _fail("GOVERNED_ATTEMPT_NOT_READY_FOR_WORKER_LAUNCH")


def _claim(binding: dict) -> None:
    """Persistent, durable no-retry claim, using the already-existing primitive."""
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    fd = once.open_root_owned_state_dir()
    try:
        result = once.consume_once_fd(fd, binding)
    finally:
        os.close(fd)
    if result.get("status") != "CONSUMED_NO_LAUNCH_NON_AUTHORIZING" or result.get("claim_record_written") is not True:
        _fail("S01_ONE_SHOT_CLAIM_FAILED_OR_ALREADY_CONSUMED")


def launch_once(*, root: Path, runtime_root: Path, task_prompt_id: str,
                attempt_id: str, confirm: bool) -> dict[str, Any]:
    """Potential live binding ONLY AFTER an independent review and publication.

    This function never provisions signers, authorizes a receipt, or replaces
    live Make quarantine. The candidate package does not install this module.
    """
    if os.geteuid() != 0:
        _fail("ROOT_ONLY_CORRIDOR")
    if confirm is not True:
        _fail("EXPLICIT_OPERATOR_CONFIRMATION_REQUIRED")
    if Path(root).resolve() != PROJECT or Path(runtime_root).resolve() != RUNTIME:
        _fail("S01_CANONICAL_ROOT_OR_RUNTIME_REQUIRED")
    if _git(PROJECT, "branch", "--show-current") != BRANCH:
        _fail("S01_APPROVED_BRANCH_REQUIRED")
    if _git(PROJECT, "diff", "--cached", "--name-only"):
        _fail("S01_STAGED_SOURCE_NOT_ALLOWED")
    head = _head(PROJECT)
    _assert_reviewed_live_source(PROJECT, head)
    if _git(PROJECT, "ls-remote", "--exit-code", "origin", "refs/heads/" + BRANCH).split()[0] != head:
        _fail("S01_REMOTE_HEAD_NOT_VERIFIED")

    binding, expires = _authenticate(PROJECT, task=task_prompt_id, attempt=attempt_id)
    if binding["publication_commit"] != head:
        _fail("S01_BINDING_HEAD_DRIFT")
    _preclaim_cycle_readiness(PROJECT, RUNTIME, task_prompt_id, attempt_id)
    # Immediately before the irreversible claim, re-evaluate trusted signatures,
    # scope, proof contents, source HEAD and current expiry. No caller token.
    fresh, expires = _authenticate(PROJECT, task=task_prompt_id, attempt=attempt_id)
    if fresh != binding or _head(PROJECT) != head:
        _fail("S01_PRECLAIM_SIGNED_BINDING_DRIFT")

    _assert_reviewed_live_source(PROJECT, head)
    _claim(binding)  # NEVER retry on failure, crash or post-claim errors.
    session = _Session(PROJECT, WORKER, task_prompt_id, attempt_id, head, expires)
    token = _SESSION.set(session)
    try:
        if datetime.now(timezone.utc) >= expires or _head(PROJECT) != head:
            _fail("S01_POSTCLAIM_SIGNED_OR_SOURCE_DRIFT_NO_RETRY")
        from scripts.coordination.control_plane import governed_worker_cycle as cycle
        result = cycle.launch_cycle(root=PROJECT, runtime_root=RUNTIME, task_prompt_id=task_prompt_id,
                                    attempt_id=attempt_id, worker_id=WORKER, confirm=True)
        if session.phase != "INNER_ENTERED":
            _fail("S01_INNER_LAUNCH_ROUTE_NOT_VERIFIED_NO_RETRY")
        return result
    finally:
        _SESSION.reset(token)


def inspect() -> dict:
    return {
        "schema_version": "cf10_s01_live_pilot_corridor_candidate_v0_1",
        "status": "REVIEW_CANDIDATE_NOT_WIRED",
        "requires_independent_source_review": True,
        "requires_eight_independent_proofs": True,
        "requires_signed_approval_after_final_source_publication": True,
        "production_launch_verified_by_inspection": False,
        "worker_launched": False, "authority_granted": False,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("inspect", "launch-preflight", "launch"))
    p.add_argument("--root", type=Path, default=PROJECT)
    p.add_argument("--runtime-root", type=Path, default=RUNTIME)
    p.add_argument("--task-prompt-id", default="")
    p.add_argument("--attempt-id", default="")
    p.add_argument("--confirm-launch", action="store_true")
    args = p.parse_args(argv)
    if args.mode != "launch":
        print(json.dumps(inspect(), indent=2, sort_keys=True))
        return 0 if args.mode == "inspect" else 2
    try:
        result = launch_once(root=args.root, runtime_root=args.runtime_root,
                             task_prompt_id=args.task_prompt_id,
                             attempt_id=args.attempt_id, confirm=args.confirm_launch)
        # Return of launch_cycle is NOT independent proof that a Worker
        # spawned or completed successfully. The canonical immutable result,
        # terminal ledger and operator acceptance establish those facts.
        print(json.dumps({"status": "GOVERNED_CYCLE_RETURNED_REQUIRES_EVIDENCE_REVIEW",
                          "attempt_id": args.attempt_id,
                          "worker_spawn_confirmed_here": False,
                          "worker_result_accepted_here": False,
                          "result_state": result.get("state")}, sort_keys=True))
        return 0
    except Exception as exc:
        # Do not echo signed payloads, private root file content or traceback.
        reason = str(exc) if isinstance(exc, PilotLaunchBlocked) else "UNEXPECTED_FAIL_CLOSED"
        print(json.dumps({"status": "BLOCKED", "reason": reason,
                          "automatic_retry": False, "launch_success_not_claimed": True,
                          "operator_review_required": True}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
