"""Governed candidate admission/promotion runtime for CF-10.

This runtime performs no staging, commit, push, merge, release or automatic
ACCEPT. Promotion is an explicit operator-controlled canonical file mutation
after all required pre-promotion checks pass.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import hashlib
import shutil
import subprocess
from typing import Any

import yaml


CONTRACT_REL = (
    "coordination/standards/automation/"
    "worker_candidate_promotion_contract_v0_1.yaml"
)

REQUIRED_PRE_PROMOTION_CHECKS = {
    "handoff_v2_result_validation",
    "work_front_scope_validation",
    "execution_profile_ceiling_validation",
    "procedure_conformance",
    "source_freshness_validation",
    "changed_path_validation",
    "operator_review",
}

ALLOWED_OPERATIONS = {"CREATE", "MODIFY", "DELETE"}


class CandidatePromotionError(RuntimeError):
    """Raised when candidate admission/promotion cannot safely proceed."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise CandidatePromotionError(f"{label} missing: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CandidatePromotionError(f"{label} must be a mapping")
    return value


def _run_git(
    repo: Path,
    *args: str,
    binary: bool = False,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=not binary,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE if binary else subprocess.STDOUT,
        check=False,
    )


def _safe_relative_path(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise CandidatePromotionError("changed path must be a non-empty string")
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise CandidatePromotionError(f"unsafe changed path: {raw!r}")
    normalized = candidate.as_posix()
    if normalized in {"", "."}:
        raise CandidatePromotionError(f"unsafe changed path: {raw!r}")
    return normalized


def normalize_changed_paths(paths: list[str]) -> list[str]:
    if not isinstance(paths, list) or not paths:
        raise CandidatePromotionError("changed_paths must be a non-empty list")
    normalized = sorted({_safe_relative_path(item) for item in paths})
    if len(normalized) != len(paths):
        raise CandidatePromotionError("changed_paths contain duplicates")
    return normalized


def load_promotion_contract(root: Path | str) -> dict[str, Any]:
    root_path = Path(root).resolve()
    return _load_yaml(root_path / CONTRACT_REL, "promotion contract")


def validate_promotion_contract(contract: dict[str, Any]) -> None:
    if contract.get("contract_id") != "worker_candidate_promotion_contract":
        raise CandidatePromotionError("promotion contract id mismatch")

    authority = contract.get("authority_semantics")
    if not isinstance(authority, dict):
        raise CandidatePromotionError("promotion authority semantics missing")

    if authority.get("promotion_authority") != "OPERATOR_CONTROLLED_CF10":
        raise CandidatePromotionError("promotion authority is not operator controlled")

    for key in (
        "worker_can_promote",
        "worker_can_commit_canonical",
        "worker_can_push",
        "worker_can_merge",
        "worker_can_release",
        "worker_can_auto_accept",
    ):
        if authority.get(key) is not False:
            raise CandidatePromotionError(f"forbidden authority widened: {key}")

    required = set(contract.get("required_pre_promotion_checks") or [])
    if not REQUIRED_PRE_PROMOTION_CHECKS.issubset(required):
        raise CandidatePromotionError(
            "promotion contract is missing required pre-promotion checks"
        )


def _git_object_exists(repo: Path, source_head: str, relative: str) -> bool:
    result = _run_git(repo, "cat-file", "-e", f"{source_head}:{relative}")
    return result.returncode == 0


def _git_blob(repo: Path, source_head: str, relative: str) -> bytes:
    result = _run_git(
        repo,
        "show",
        f"{source_head}:{relative}",
        binary=True,
    )
    if result.returncode != 0:
        raise CandidatePromotionError(
            f"cannot read source blob {source_head}:{relative}"
        )
    return result.stdout


def _origin_profile_ref(origin_manifest: dict[str, Any]) -> str:
    value = origin_manifest.get("execution_profile_revision_for_task_execution")
    if not isinstance(value, dict):
        raise CandidatePromotionError("origin Handoff profile binding missing")
    profile_id = value.get("profile_id")
    revision = value.get("revision")
    if not isinstance(profile_id, str) or not isinstance(revision, str):
        raise CandidatePromotionError("origin Handoff profile binding invalid")
    return f"{profile_id}@{revision}"


def _origin_procedure_id(origin_manifest: dict[str, Any]) -> str:
    value = origin_manifest.get(
        "governed_procedure_revision_or_not_required_reason"
    )
    if not isinstance(value, dict):
        raise CandidatePromotionError("origin Handoff procedure binding missing")
    if value.get("classification") != "GRAPH_REQUIRED":
        raise CandidatePromotionError(
            "origin Handoff procedure classification is not GRAPH_REQUIRED"
        )
    procedure_id = value.get("procedure_id")
    if not isinstance(procedure_id, str) or not procedure_id:
        raise CandidatePromotionError("origin Handoff procedure id missing")
    return procedure_id


def _validate_handoff_result(
    *,
    origin_manifest: dict[str, Any],
    handoff_result: dict[str, Any],
    attempt_id: str,
    changed_paths: list[str],
) -> None:
    if origin_manifest.get("launch_mode") != "TASK_EXECUTION":
        raise CandidatePromotionError("origin Handoff is not TASK_EXECUTION")

    manifest_sha = origin_manifest.get("handoff_manifest_sha256")
    if not isinstance(manifest_sha, str) or len(manifest_sha) != 64:
        raise CandidatePromotionError("origin Handoff hash missing")

    if handoff_result.get("attempt_id") != attempt_id:
        raise CandidatePromotionError("Handoff result attempt mismatch")
    if handoff_result.get("status") != "PASS":
        raise CandidatePromotionError("Handoff result is not PASS")
    if handoff_result.get("handoff_manifest_sha256") != manifest_sha:
        raise CandidatePromotionError("Handoff result manifest binding mismatch")
    if normalize_changed_paths(handoff_result.get("changed_paths") or []) != changed_paths:
        raise CandidatePromotionError("Handoff result changed_paths mismatch")

    resume = handoff_result.get("resume_coordinates")
    if not isinstance(resume, dict):
        raise CandidatePromotionError("Handoff result resume_coordinates missing")
    if resume.get("attempt_id") != attempt_id:
        raise CandidatePromotionError("Handoff resume attempt mismatch")
    if resume.get("handoff_manifest_sha256") != manifest_sha:
        raise CandidatePromotionError("Handoff resume manifest hash mismatch")

    # Handoff-composite self-consistency only. This is deliberately NOT
    # compared with the canonical continuity source fingerprint.
    if (
        resume.get("source_state_fingerprint")
        != origin_manifest.get("source_state_fingerprint")
    ):
        raise CandidatePromotionError(
            "Handoff composite source_state_fingerprint is not self-consistent"
        )
    if (
        resume.get("lifecycle_roadmap_cursor")
        != origin_manifest.get("lifecycle_roadmap_cursor")
    ):
        raise CandidatePromotionError(
            "Handoff lifecycle/roadmap cursor is not self-consistent"
        )


def classify_target_operation(
    *,
    canonical_repo: Path,
    candidate_root: Path,
    source_head: str,
    relative: str,
) -> dict[str, Any]:
    relative = _safe_relative_path(relative)
    canonical = canonical_repo / relative
    candidate = candidate_root / relative

    source_exists = _git_object_exists(canonical_repo, source_head, relative)
    canonical_exists = canonical.exists()
    candidate_exists = candidate.exists()

    if source_exists:
        source_bytes = _git_blob(canonical_repo, source_head, relative)
        source_sha = _sha256_bytes(source_bytes)

        if not canonical.is_file():
            raise CandidatePromotionError(
                f"TARGET_FRESHNESS_DRIFT: canonical target missing: {relative}"
            )
        canonical_bytes = canonical.read_bytes()
        if canonical_bytes != source_bytes:
            raise CandidatePromotionError(
                "TARGET_FRESHNESS_DRIFT: canonical target changed after "
                f"source freeze: {relative}"
            )

        if candidate_exists:
            if not candidate.is_file():
                raise CandidatePromotionError(
                    f"candidate target is not a file: {relative}"
                )
            candidate_bytes = candidate.read_bytes()
            if candidate_bytes == source_bytes:
                raise CandidatePromotionError(
                    f"changed path is an effective no-op: {relative}"
                )
            return {
                "path": relative,
                "operation": "MODIFY",
                "source_state": "EXISTING_FILE",
                "source_sha256": source_sha,
                "canonical_pre_sha256": source_sha,
                "candidate_sha256": _sha256_bytes(candidate_bytes),
            }

        return {
            "path": relative,
            "operation": "DELETE",
            "source_state": "EXISTING_FILE",
            "source_sha256": source_sha,
            "canonical_pre_sha256": source_sha,
            "candidate_sha256": None,
        }

    if canonical_exists:
        raise CandidatePromotionError(
            "TARGET_FRESHNESS_DRIFT: target absent at source HEAD but "
            f"exists canonically: {relative}"
        )

    if not candidate_exists:
        raise CandidatePromotionError(
            f"changed path absent in source and candidate: {relative}"
        )
    if not candidate.is_file():
        raise CandidatePromotionError(
            f"candidate target is not a file: {relative}"
        )

    return {
        "path": relative,
        "operation": "CREATE",
        "source_state": "ABSENT_AT_SOURCE_HEAD",
        "source_sha256": None,
        "canonical_pre_sha256": None,
        "candidate_sha256": _sha256_bytes(candidate.read_bytes()),
    }


def build_candidate_promotion_plan(
    *,
    root: Path | str,
    candidate_root: Path | str,
    source_head: str,
    attempt_id: str,
    changed_paths: list[str],
    work_front: dict[str, Any],
    origin_handoff_manifest: dict[str, Any],
    handoff_result: dict[str, Any],
    expected_profile_ref: str,
    expected_procedure_id: str,
    operator_review: bool,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    canonical_repo = Path(root).resolve()
    candidate_repo = Path(candidate_root).resolve()

    if not canonical_repo.is_dir():
        raise CandidatePromotionError("canonical repository is missing")
    if not candidate_repo.is_dir():
        raise CandidatePromotionError("candidate root is missing")

    contract_value = contract or load_promotion_contract(canonical_repo)
    validate_promotion_contract(contract_value)

    paths = normalize_changed_paths(changed_paths)

    if operator_review is not True:
        raise CandidatePromotionError("explicit operator review is required")

    if work_front.get("work_front_id") in {None, ""}:
        raise CandidatePromotionError("Work Front id missing")
    if normalize_changed_paths(work_front.get("scope") or []) != paths:
        raise CandidatePromotionError("Work Front scope does not equal changed paths")

    _validate_handoff_result(
        origin_manifest=origin_handoff_manifest,
        handoff_result=handoff_result,
        attempt_id=attempt_id,
        changed_paths=paths,
    )

    if _origin_profile_ref(origin_handoff_manifest) != expected_profile_ref:
        raise CandidatePromotionError("execution profile ceiling mismatch")
    if _origin_procedure_id(origin_handoff_manifest) != expected_procedure_id:
        raise CandidatePromotionError("governed procedure mismatch")

    head = _run_git(canonical_repo, "rev-parse", "HEAD")
    if head.returncode != 0:
        raise CandidatePromotionError("cannot resolve canonical HEAD")
    if head.stdout.strip() != source_head:
        raise CandidatePromotionError(
            "canonical HEAD drifted after candidate source freeze"
        )

    operations = [
        classify_target_operation(
            canonical_repo=canonical_repo,
            candidate_root=candidate_repo,
            source_head=source_head,
            relative=relative,
        )
        for relative in paths
    ]

    checks = {
        "handoff_v2_result_validation": "PASS",
        "work_front_scope_validation": "PASS",
        "execution_profile_ceiling_validation": "PASS",
        "procedure_conformance": "PASS",
        "source_freshness_validation": "PASS",
        "changed_path_validation": "PASS",
        "operator_review": "PASS",
    }

    return {
        "schema_version": "forprint_worker_candidate_promotion_plan_v0_1",
        "attempt_id": attempt_id,
        "source_head": source_head,
        "work_front_id": work_front["work_front_id"],
        "changed_paths": paths,
        "operations": operations,
        "required_pre_promotion_checks": checks,
        "operator_review": "PASS",
        "candidate_input_mode": "EXACT_CANDIDATE_ARTIFACTS",
        "canonical_continuity_fingerprint_compared_to_handoff_composite": False,
        "promotion_authority": "OPERATOR_CONTROLLED_CF10",
        "staging_performed": False,
        "commit_performed": False,
        "push_performed": False,
        "merge_performed": False,
        "release_performed": False,
        "automatic_accept_performed": False,
    }


def _write_yaml_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise CandidatePromotionError(f"refusing to overwrite evidence: {path}")
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


def apply_candidate_promotion(
    *,
    plan: dict[str, Any],
    root: Path | str,
    candidate_root: Path | str,
    recovery_root: Path | str,
    evidence_path: Path | str | None = None,
    post_apply_validator: Callable[[list[str]], bool | dict[str, Any]] | None = None,
) -> dict[str, Any]:
    canonical_repo = Path(root).resolve()
    candidate_repo = Path(candidate_root).resolve()
    recovery = Path(recovery_root).resolve()

    if plan.get("promotion_authority") != "OPERATOR_CONTROLLED_CF10":
        raise CandidatePromotionError("promotion plan authority mismatch")
    if plan.get("operator_review") != "PASS":
        raise CandidatePromotionError("promotion plan lacks operator review")

    checks = plan.get("required_pre_promotion_checks")
    if not isinstance(checks, dict):
        raise CandidatePromotionError("promotion plan checks missing")
    for name in REQUIRED_PRE_PROMOTION_CHECKS:
        if checks.get(name) != "PASS":
            raise CandidatePromotionError(f"promotion check is not PASS: {name}")

    paths = normalize_changed_paths(plan.get("changed_paths") or [])
    operations = plan.get("operations")
    if not isinstance(operations, list) or len(operations) != len(paths):
        raise CandidatePromotionError("promotion operations mismatch")

    operation_map: dict[str, dict[str, Any]] = {}
    for row in operations:
        if not isinstance(row, dict):
            raise CandidatePromotionError("promotion operation must be mapping")
        relative = _safe_relative_path(str(row.get("path", "")))
        operation = row.get("operation")
        if operation not in ALLOWED_OPERATIONS:
            raise CandidatePromotionError(f"unsupported operation: {operation!r}")
        operation_map[relative] = row

    if sorted(operation_map) != paths:
        raise CandidatePromotionError("promotion operation path surface mismatch")

    if recovery.exists():
        raise CandidatePromotionError(
            f"recovery root already exists; replay forbidden: {recovery}"
        )

    evidence = Path(evidence_path).resolve() if evidence_path else None
    if evidence is not None and evidence.exists():
        raise CandidatePromotionError(
            f"promotion evidence already exists; replay forbidden: {evidence}"
        )

    recovery.mkdir(parents=True, exist_ok=False)
    preimage: dict[str, dict[str, Any]] = {}

    for relative in paths:
        target = canonical_repo / relative
        existed = target.is_file()
        row: dict[str, Any] = {
            "path": relative,
            "existed_before": existed,
        }
        if existed:
            dst = recovery / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, dst)
            row["preimage_path"] = str(dst)
            row["preimage_sha256"] = _sha256_bytes(target.read_bytes())
        else:
            if target.exists():
                raise CandidatePromotionError(
                    f"non-file canonical target cannot be promoted: {relative}"
                )
            row["preimage_path"] = None
            row["preimage_sha256"] = None
        preimage[relative] = row

    mutation_started = False

    def rollback() -> None:
        for relative in paths:
            target = canonical_repo / relative
            row = preimage[relative]
            if row["existed_before"]:
                source = Path(str(row["preimage_path"]))
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            elif target.exists():
                if target.is_file():
                    target.unlink()
                else:
                    raise CandidatePromotionError(
                        f"rollback found non-file target: {relative}"
                    )

    try:
        for relative in paths:
            row = operation_map[relative]
            operation = row["operation"]
            target = canonical_repo / relative
            candidate = candidate_repo / relative

            if operation in {"CREATE", "MODIFY"}:
                if not candidate.is_file():
                    raise CandidatePromotionError(
                        f"candidate file missing during apply: {relative}"
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                mutation_started = True
                shutil.copy2(candidate, target)
            elif operation == "DELETE":
                if target.is_file():
                    mutation_started = True
                    target.unlink()
                elif target.exists():
                    raise CandidatePromotionError(
                        f"cannot delete non-file target: {relative}"
                    )

        post_sha: dict[str, str | None] = {}
        for relative in paths:
            operation = operation_map[relative]["operation"]
            target = canonical_repo / relative
            candidate = candidate_repo / relative

            if operation in {"CREATE", "MODIFY"}:
                if not target.is_file() or target.read_bytes() != candidate.read_bytes():
                    raise CandidatePromotionError(
                        f"canonical/candidate equality failed: {relative}"
                    )
                post_sha[relative] = _sha256_bytes(target.read_bytes())
            else:
                if target.exists():
                    raise CandidatePromotionError(
                        f"DELETE promotion left target present: {relative}"
                    )
                post_sha[relative] = None

        validator_result: bool | dict[str, Any] | None = None
        if post_apply_validator is not None:
            validator_result = post_apply_validator(paths)
            valid = (
                validator_result is True
                or (
                    isinstance(validator_result, dict)
                    and validator_result.get("result") == "PASS"
                )
            )
            if not valid:
                raise CandidatePromotionError(
                    "post-apply canonical validation did not PASS"
                )

        result = {
            "schema_version": "forprint_worker_candidate_promotion_result_v0_1",
            "attempt_id": plan.get("attempt_id"),
            "source_head": plan.get("source_head"),
            "work_front_id": plan.get("work_front_id"),
            "promotion_authority": "OPERATOR_CONTROLLED_CF10",
            "candidate_input_mode": "EXACT_CANDIDATE_ARTIFACTS",
            "changed_paths": paths,
            "operations": operations,
            "preimage": preimage,
            "canonical_post_promotion_sha256": post_sha,
            "post_apply_validation": validator_result,
            "candidate_promoted": True,
            "canonical_write_performed": True,
            "rollback_performed": False,
            "staging_performed": False,
            "commit_performed": False,
            "push_performed": False,
            "merge_performed": False,
            "release_performed": False,
            "automatic_accept_performed": False,
        }

        if evidence is not None:
            _write_yaml_new(evidence, result)

        return result

    except Exception:
        if mutation_started:
            rollback()
        raise
