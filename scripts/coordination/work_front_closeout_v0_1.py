"""Bounded, non-authoritative Work Front closeout preparation.

Stage 1 only: plan/check. Never writes governance/roadmap/event-store files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import yaml


class CloseoutError(RuntimeError):
    pass


EXPECTED_EVIDENCE_STATUS = "VALIDATION_COMPLETE_PENDING_OPERATOR_RECONCILIATION"
ALLOWED_REPORT_KINDS = {"local_validation_evidence_candidate", "normalized_work_front_validation_evidence_v0_1"}
STAGE4C_SCHEMA = "forprint_cf10_stage4c_completion_evidence_v0_1"
VERIFICATION_KEYS = ("focused", "worker_pipeline", "continuity_planning", "work_front", "work_front_contract")
CANONICAL_PREFIX = "coordination/internal_work/blueprint/governance/"


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash(path: Path) -> str:
    return _hash_bytes(path.read_bytes())


def _repo_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise CloseoutError("FILE_PATH_INVALID")
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts:
        raise CloseoutError("FILE_OUTSIDE_ROOT")
    candidate = root / p
    if candidate.is_symlink() or not candidate.is_file():
        raise CloseoutError(f"FILE_MISSING_OR_SYMLINK: {relative}")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise CloseoutError("FILE_OUTSIDE_ROOT")
    return candidate


def _run_git(root: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if proc.returncode != 0:
        raise CloseoutError(f"GIT_FAILED: {' '.join(args)}: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def _load_json(path: Path) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise CloseoutError("JSON_INVALID") from exc
    if not isinstance(result, dict):
        raise CloseoutError("JSON_MAPPING_REQUIRED")
    return result


def _sha_matches(root: Path, relative: str, expected: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected)):
        raise CloseoutError(f"SHA_INVALID: {relative}")
    if _hash(_repo_file(root, relative)) != expected:
        raise CloseoutError(f"SHA_MISMATCH: {relative}")


def _canonical_json(obj: dict[str, Any]) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _ensure_same_root(root: Path) -> None:
    if _run_git(root, "rev-parse", "--show-toplevel").decode().strip() != str(root):
        raise CloseoutError("NOT_GIT_ROOT")


def _read_front(root: Path, front_path: str) -> dict[str, Any]:
    path = _repo_file(root, front_path)
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CloseoutError("FRONT_YAML_INVALID") from exc
    if not isinstance(parsed, dict):
        raise CloseoutError("FRONT_MAPPING_REQUIRED")
    # Reuse project-owned authority and structural validation, do not reimplement it.
    from scripts.coordination.work_front_v0_1 import WorkFrontError, validate_work_front
    try:
        outcome = validate_work_front(root, front_path)
    except WorkFrontError as exc:
        raise CloseoutError(f"WORK_FRONT_INVALID: {exc}") from exc
    if outcome.get("status") != "PASS" or outcome.get("dispatch_authority_conferred") is not False:
        raise CloseoutError("WORK_FRONT_AUTHORITY_INVALID")
    return parsed


def make_plan(root: Path, front_path: str, evidence_path: str, *, forbidden_attempt: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    _ensure_same_root(root)
    front = _read_front(root, front_path)
    evidence = _load_json(_repo_file(root, evidence_path))
    if evidence.get("report_kind") not in ALLOWED_REPORT_KINDS or evidence.get("status") != EXPECTED_EVIDENCE_STATUS:
        raise CloseoutError("EVIDENCE_NOT_VALIDATED_CANDIDATE")
    if evidence.get("work_front_id") != front.get("work_front_id") or evidence.get("work_front_path") != front_path:
        raise CloseoutError("EVIDENCE_WORK_FRONT_MISMATCH")
    if not isinstance(front.get("acceptance"), list) or not front["acceptance"]:
        raise CloseoutError("FRONT_ACCEPTANCE_MISSING")
    auth = evidence.get("operator_authorization")
    if not isinstance(auth, dict):
        raise CloseoutError("EVIDENCE_AUTHORITY_MISSING")
    if auth.get("roadmap_or_ledger_mutation") is not False:
        raise CloseoutError("EVIDENCE_AUTHORITY_WIDENED")
    if auth.get("dispatch") is not False:
        raise CloseoutError("EVIDENCE_DISPATCH_WIDENED")
    if auth.get("commit_or_push") is not False:
        raise CloseoutError("EVIDENCE_COMMIT_WIDENED")

    source = evidence.get("source_state")
    if not isinstance(source, dict) or not isinstance(source.get("file_sha256"), dict):
        raise CloseoutError("SOURCE_BINDING_MISSING")
    _sha_matches(root, front_path, source.get("work_front_sha256"))
    source_files = source["file_sha256"]
    if not source_files:
        raise CloseoutError("SOURCE_FILES_MISSING")
    for name, digest in sorted(source_files.items()):
        _sha_matches(root, name, digest)

    head = _run_git(root, "rev-parse", "HEAD").decode().strip()
    if source.get("head") != head:
        raise CloseoutError("HEAD_DRIFT")
    staged_hash = _hash_bytes(_run_git(root, "diff", "--cached", "--binary"))
    if source.get("staged_diff_sha256") != staged_hash:
        raise CloseoutError("STAGING_DRIFT")
    if _run_git(root, "diff", "--check").strip():
        raise CloseoutError("GIT_DIFF_CHECK_OUTPUT")

    verification = evidence.get("verification")
    if not isinstance(verification, dict):
        raise CloseoutError("EVIDENCE_VERIFICATION_MISSING")
    expected_keys = (
        VERIFICATION_KEYS if evidence.get("schema_version") == STAGE4C_SCHEMA
        else tuple(evidence.get("required_verification_keys") or sorted(verification))
    )
    if not expected_keys or not all(isinstance(k, str) and k for k in expected_keys):
        raise CloseoutError("VERIFICATION_KEYS_INVALID")
    if set(verification) != set(expected_keys):
        raise CloseoutError("VERIFICATION_SET_MISMATCH")
    log_refs: dict[str, dict[str, Any]] = {}
    counted = 0
    for key in expected_keys:
        row = verification.get(key)
        if not isinstance(row, dict) or row.get("result") != "PASS":
            raise CloseoutError(f"VERIFICATION_NOT_PASS: {key}")
        _sha_matches(root, row.get("log_path"), row.get("log_sha256"))
        log_refs[key] = {
            "log_path": row["log_path"], "log_sha256": row["log_sha256"],
            "test_executions": row.get("test_executions"),
        }
        if row.get("test_executions") is not None:
            if type(row["test_executions"]) is not int or row["test_executions"] < 0:
                raise CloseoutError("TEST_COUNT_INVALID")
            counted += row["test_executions"]
    if counted != evidence.get("test_execution_count"):
        raise CloseoutError("TEST_COUNT_MISMATCH")
    if evidence.get("schema_version") == STAGE4C_SCHEMA:
        if evidence.get("implementation", {}).get("live_worker_executed_by_this_report") is not False:
            raise CloseoutError("LIVE_EXECUTION_BOUNDARY_INVALID")

    forbids: dict[str, Any] = {"attempt_id": forbidden_attempt, "absence_in_repo_at_plan": None}
    if forbidden_attempt:
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{1,127}", forbidden_attempt):
            raise CloseoutError("FORBIDDEN_ATTEMPT_INVALID")
        ledger_dir = root / "coordination/continuity/execution_attempts"
        if not ledger_dir.is_dir():
            raise CloseoutError("LEDGER_DIRECTORY_MISSING")
        matches = sorted(p.name for p in ledger_dir.glob(forbidden_attempt + "__*") if p.is_file())
        if matches:
            raise CloseoutError("FORBIDDEN_ATTEMPT_EXISTS: " + ",".join(matches))
        forbids["absence_in_repo_at_plan"] = True

    unstaged_hash = _hash_bytes(_run_git(root, "diff", "--binary"))
    # Untracked sources are not included in git diff. Snapshot bytes outside tmp.
    untracked = _run_git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    untracked_sha: dict[str, str] = {}
    for name_bytes in untracked:
        if not name_bytes:
            continue
        name = os.fsdecode(name_bytes)
        if name == "tmp" or name.startswith("tmp/"):
            continue
        untracked_sha[name] = _hash(_repo_file(root, name))

    return {
        "schema_version": "forprint_blueprint_work_front_closeout_plan_v0_1",
        "status": "READY_FOR_OPERATOR_ACCEPTANCE_REVIEW",
        "authority": {
            "plan_is_acceptance": False, "canonical_write_allowed": False,
            "work_item_close_allowed": False, "worker_dispatch_allowed": False,
            "automatic_commit_or_push": False,
        },
        "work_front": {"path": front_path, "id": front["work_front_id"], "sha256": _hash(_repo_file(root, front_path))},
        "completion_evidence": {"path": evidence_path, "sha256": _hash(_repo_file(root, evidence_path)),
                                "status": evidence["status"], "verified_test_executions": counted},
        "verified_logs": log_refs,
        "implementation_file_sha256": dict(sorted(source_files.items())),
        "source_state": {"head": head, "staged_diff_sha256": staged_hash, "unstaged_diff_sha256": unstaged_hash,
                         "untracked_excluding_tmp_sha256": untracked_sha},
        "forbidden_attempt": forbids,
        "acceptance_review": [{"index": i + 1, "criterion": entry,
                               "operator_attestation": "PENDING_MANUAL_REVIEW"}
                              for i, entry in enumerate(front["acceptance"])],
        "proposed_completion": {
            "state": "VALIDATION_COMPLETE_PENDING_PUBLICATION_AND_OPERATOR_APPROVAL",
            "canonical_directory": CANONICAL_PREFIX,
            "write_performed": False,
            "publication_commit_verified": False,
            "lifecycle_derived_state_changed": False,
            "additional_audit_needed": ["independent historical ledger baseline", "canonical record type acceptance",
                                        "published implementation commit", "operator approval"],
        },
        "no_canonical_mutation": True,
    }


def _plan_file(root: Path, name: str) -> Path:
    if not re.fullmatch(r"[a-zA-Z0-9_.-]+\.json", name):
        raise CloseoutError("PLAN_NAME_INVALID")
    return root / "tmp" / name


def write_plan(root: Path, obj: dict[str, Any], plan_file: str) -> Path:
    dest = _plan_file(root, plan_file)
    data = _canonical_json(obj)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if dest.is_symlink() or dest.read_bytes() != data:
            raise CloseoutError("PLAN_EXISTS_WITH_DIFFERENT_BYTES")
        return dest
    try:
        with dest.open("xb") as handle:
            handle.write(data)
    except FileExistsError as exc:
        raise CloseoutError("PLAN_CONCURRENT_WRITE") from exc
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--front", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--action", choices=["plan", "check"], default="plan")
    parser.add_argument("--plan-name", default="work_front_closeout_plan_v0_1.json")
    parser.add_argument("--forbid-attempt-id")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        plan = make_plan(root, args.front, args.evidence, forbidden_attempt=args.forbid_attempt_id)
        output = _plan_file(root, args.plan_name)
        if args.action == "plan":
            write_plan(root, plan, args.plan_name)
        else:
            if not output.is_file() or output.is_symlink() or output.read_bytes() != _canonical_json(plan):
                raise CloseoutError("PLAN_STALE_OR_MISSING")
        print("WORK_FRONT_CLOSEOUT_EVIDENCE=PASS")
        print("WORK_FRONT_CLOSEOUT_ACTION=" + args.action.upper())
        print("WORK_FRONT_CLOSEOUT_ACCEPTANCE=" + plan["status"])
        print("WORK_FRONT_CLOSEOUT_PLAN=" + str(output))
        print("WORK_FRONT_CLOSEOUT_PLAN_SHA256=" + _hash_bytes(_canonical_json(plan)))
        print("CANONICAL_MUTATION=false")
        print("WORKER_DISPATCH=false")
        return 0
    except (CloseoutError, OSError, ValueError, yaml.YAMLError) as exc:
        print("WORK_FRONT_CLOSEOUT=BLOCKED")
        print("REASON=" + str(exc))
        print("CANONICAL_MUTATION=false")
        return 2


if __name__ == "__main__":
    sys.exit(main())
