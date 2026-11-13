"""CF-10 S01 signed runtime rebind *predicate* v0.2.

Never launches a Worker, writes the ledger, alters external authority or attaches
itself to the active launch Make targets. A positive result is a necessary,
non-authorizing precondition, NOT single-use launch permission. The live
Make quarantine remains a separate mandatory boundary.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Callable

SCHEMA = "cf10_s01_runtime_rebind_predicate_v0_2"
PROOF_SCHEMA = "cf10_s01_independent_proof_v0_2"
PROOF_ROOT = Path("/etc/forprint/cf10_release_authority/proofs")
RECEIPT_FILE = Path("/etc/forprint/cf10_release_authority/signed_release_v0_1.json")
REQUIREMENTS = (
    "writer_entrypoints_and_callbacks",
    "active_and_short_lived_process_enrollment",
    "drain_restart_and_old_writer_exclusion",
    "systemd_cron_manual_ssh_remote_paths",
    "lock_inode_acl_mount_and_dac",
    "independent_dynamic_non_bypass_proof",
    "independent_signature_and_publication",
    "separate_release_quarantine_acceptance",
)
REQUIRED_SCOPE_KEYS = frozenset((
    "worker_id", "task_prompt_id", "attempt_id", "max_active_workers", "max_attempts",
    "explicit_operator_dispatch_required", "automatic_retry_allowed",
    "automatic_accept_allowed", "route",
))
TASK_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,159}\Z")
ATTEMPT_RE = re.compile(r"cf10-[a-zA-Z0-9][a-zA-Z0-9_.-]{1,159}\Z")
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")


def _digest(raw: bytes) -> str:
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def _baseline(root: Path) -> dict:
    # This evaluator checks Ed25519 signature, current time, exact signed source
    # bytes, remote publication, activation and installed protocol. It NEVER
    # supplies launch authority, so only its candidate_preconditions_pass is used.
    from scripts.coordination.control_plane import cf10_s01_release_gate_candidate_v0_1 as candidate
    return candidate.evaluate(root, mode="preflight")


def _trusted_json(path: Path) -> tuple[dict, bytes]:
    from scripts.coordination import execution_attempt_writer_activation_v0_1 as activation
    return activation.trusted_json(path)


def _reverify_receipt(root: Path, head: str, receipt: dict) -> bool:
    """Re-verify the *same bytes we use* for pilot/proof binding.

    The earlier baseline is not enough if the signed file changes between
    reads. This independent verification closes that trust-boundary gap.
    """
    try:
        from scripts.coordination.control_plane import cf10_s01_release_gate_candidate_v0_1 as gate
        from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer
        trust, _ = _trusted_json(gate.RELEASE_TRUST)
        activation, activation_raw = _trusted_json(gate.ACTIVATION_DECISION)
        _, coverage_raw = _trusted_json(gate.COVERAGE)
        protocol = writer.load_enforced_protocol(required=True)
        if not protocol:
            return False
        guard_raw = (root / gate.SOURCE_GUARD).read_bytes()
        ledger_raw = (root / gate.SOURCE_LEDGER).read_bytes()
        remote = gate.command(root, 'remote', 'get-url', 'origin')
        bad = gate.verify_release_receipt(
            receipt, trust, activation, head=head, remote=remote,
            protocol_sha=protocol['sha256'], coverage_sha=_digest(coverage_raw),
            activation_sha=_digest(activation_raw), guard_sha=_digest(guard_raw),
            ledger_sha=_digest(ledger_raw),
        )
        return not bad
    except Exception:
        return False


def _head(root: Path) -> str:
    p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                       capture_output=True, timeout=20)
    return p.stdout.decode().strip()


def scope_blockers(receipt: dict, *, worker_id: str, task_prompt_id: str,
                   attempt_id: str) -> list[str]:
    errors: list[str] = []
    if worker_id != "worker-01" or not TASK_RE.fullmatch(task_prompt_id) or not ATTEMPT_RE.fullmatch(attempt_id):
        return ["PILOT_INPUT_INVALID"]
    scope = receipt.get("pilot_scope")
    if not isinstance(scope, dict) or set(scope) != REQUIRED_SCOPE_KEYS:
        return ["SIGNED_PILOT_SCOPE_INCOMPLETE"]
    expected = {"worker_id": worker_id, "task_prompt_id": task_prompt_id, "attempt_id": attempt_id,
                "max_active_workers": 1, "max_attempts": 1,
                "explicit_operator_dispatch_required": True,
                "automatic_retry_allowed": False, "automatic_accept_allowed": False,
                "route": "GOVERNED_WORKER_CYCLE_ONLY"}
    for name, value in expected.items():
        observed = scope.get(name)
        # bool is a subclass of int; type matching avoids True == 1 confusion.
        if type(observed) is not type(value) or observed != value:
            errors.append("SIGNED_PILOT_SCOPE_MISMATCH:" + name)
    return errors


def proof_blockers(receipt: dict, head: str,
                   reader: Callable[[Path], tuple[dict, bytes]] = _trusted_json) -> tuple[list[str], int]:
    errors: list[str] = []
    verified = 0
    pins = receipt.get("independent_proofs")
    if not isinstance(pins, dict) or set(pins) != set(REQUIREMENTS) or any(
        not isinstance(v, str) or not SHA64.fullmatch(v) for v in pins.values()
    ):
        return ["SIGNED_PROOF_MATRIX_INVALID"], 0
    signer = receipt.get("signer_id")
    review = receipt.get("independent_operator_review_ref")
    if not isinstance(signer, str) or not signer or not isinstance(review, str) or not review:
        return ["PROOF_SIGNER_OR_REVIEW_REF_INVALID"], 0
    for key in REQUIREMENTS:
        path = PROOF_ROOT / (key + ".json")
        try:
            doc, raw = reader(path)
            if not isinstance(doc, dict) or _digest(raw) != pins[key]:
                errors.append("PROOF_BYTES_MISMATCH:" + key)
                continue
            if (doc.get("schema_version") != PROOF_SCHEMA or doc.get("requirement") != key or
                    doc.get("publication_commit") != head or doc.get("signer_id") != signer or
                    doc.get("independent_operator_review_ref") != review or doc.get("decision") != "ACCEPTED"):
                errors.append("PROOF_CONTENT_NOT_ACCEPTED:" + key)
                continue
            evidence = doc.get("evidence")
            if not isinstance(evidence, list) or not evidence or any(
                not isinstance(item, dict) or set(item) != {"ref", "sha256", "result"}
                or not isinstance(item["ref"], str) or not item["ref"].strip()
                or not isinstance(item["sha256"], str) or not SHA64.fullmatch(item["sha256"])
                or item["result"] != "PASS" for item in evidence
            ):
                errors.append("PROOF_EVIDENCE_UNSTRUCTURED:" + key)
                continue
            # These signed, root-controlled proof summaries are not a substitute
            # for independently reviewing the underlying referenced evidence.
            verified += 1
        except Exception:
            # Never expose /etc content, signer keys or raw exception messages.
            errors.append("ROOT_CONTROLLED_PROOF_UNAVAILABLE:" + key)
    return errors, verified


def evaluate(root: Path, *, worker_id: str, task_prompt_id: str,
             attempt_id: str) -> dict[str, Any]:
    blockers: list[str] = []
    head = ""
    checks: dict[str, Any] = {"baseline": "BLOCKED", "proof_files_verified": 0,
                             "pilot_scope": "BLOCKED", "head_stable": False}
    root = root.resolve()
    if not worker_id or not task_prompt_id or not attempt_id:
        blockers.append("EXPLICIT_PILOT_PARAMETERS_REQUIRED")
    if not blockers:
        try:
            baseline = _baseline(root)
            head = baseline.get("checks", {}).get("head", "")
            if (baseline.get("candidate_preconditions_pass") is not True or
                    baseline.get("blockers") != [] or not SHA40.fullmatch(head)):
                blockers.append("EXISTING_SIGNED_RELEASE_AND_ACTIVATION_GATE_BLOCKED")
            else:
                checks["baseline"] = "PASS"
        except Exception:
            blockers.append("EXISTING_RELEASE_EVALUATOR_UNAVAILABLE")
    if not blockers:
        try:
            receipt, _ = _trusted_json(RECEIPT_FILE)
            if not _reverify_receipt(root, head, receipt):
                blockers.append("SIGNED_RECEIPT_REREAD_CRYPTOGRAPHIC_CHECK_FAILED")
            blockers.extend(scope_blockers(receipt, worker_id=worker_id,
                                           task_prompt_id=task_prompt_id, attempt_id=attempt_id))
            if not blockers:
                checks["pilot_scope"] = "SIGNED_MATCH"
                evidence_errors, count = proof_blockers(receipt, head)
                checks["proof_files_verified"] = count
                blockers.extend(evidence_errors)
        except Exception:
            blockers.append("SIGNED_RELEASE_RECEIPT_UNAVAILABLE")
    # Recheck git publication binding after the external file reads. The
    # independent signer is responsible for signed decision freshness.
    if head:
        try:
            checks["head_stable"] = (_head(root) == head)
            if not checks["head_stable"]:
                blockers.append("SOURCE_HEAD_CHANGED_DURING_PREDICATE")
        except Exception:
            blockers.append("SOURCE_HEAD_RECHECK_FAILED")
    passed = not blockers and checks["proof_files_verified"] == len(REQUIREMENTS)
    return {
        "schema_version": SCHEMA,
        "status": "PREDICATE_PASS_NON_AUTHORIZING" if passed else "BLOCKED_NON_AUTHORIZING",
        "predicate_pass": passed,
        "blockers": sorted(set(blockers)),
        "checks": checks,
        "worker_id": worker_id or None, "task_prompt_id": task_prompt_id or None,
        "attempt_id": attempt_id or None,
        "launch_allowed": False, "authority_granted": False,
        "single_use_enforced": False, "live_make_wired": False,
        "worker_launched": False, "ledger_modified": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "predicate-check", "launch-preflight"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--worker-id", default="")
    parser.add_argument("--task-prompt-id", default="")
    parser.add_argument("--attempt-id", default="")
    args = parser.parse_args(argv)
    try:
        report = evaluate(args.root, worker_id=args.worker_id,
                          task_prompt_id=args.task_prompt_id, attempt_id=args.attempt_id)
    except Exception:
        report = {"schema_version": SCHEMA, "status": "BLOCKED_NON_AUTHORIZING",
                  "blockers": ["UNEXPECTED_PREDICATE_FAILURE"], "predicate_pass": False,
                  "launch_allowed": False, "authority_granted": False,
                  "live_make_wired": False, "worker_launched": False}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    # Even a hypothetical positive predicate MUST NOT serve as launch-preflight.
    if args.mode == "launch-preflight":
        return 2
    if args.mode == "predicate-check":
        return 0 if report["predicate_pass"] is True else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
