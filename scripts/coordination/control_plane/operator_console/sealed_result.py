from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.control_plane.operator_console.assistant_dev_sandbox import (
    AssistantDevSandboxError,
    sandbox_status,
)
from scripts.coordination.control_plane.workspace.provision import (
    WorkspaceProvisionError,
    derive_worker_delta_from_manifest,
)

CHECKPOINT_SCHEMA = "forprint_oc01_checkpoint_projection_v0_1"
SEALED_RESULT_SCHEMA = "forprint_oc01_sealed_result_v0_1"
PAUSE_RESUME_STATE = "DEPENDENCY_PENDING_CF10"
PROMOTION_STATE = "NEXT_SLICE_OC01_MINI_5"


class SealedResultError(RuntimeError):
    pass


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise SealedResultError(f"{label} cannot be a symlink")
    if not path.is_file():
        raise SealedResultError(f"{label} missing: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SealedResultError(f"{label} must be a mapping")
    return value


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _attempt_binding(manifest_path: Path | str) -> tuple[Path, dict[str, Any]]:
    manifest_path = Path(manifest_path).expanduser().resolve()
    manifest = _load_yaml(manifest_path, "workspace manifest")
    attempt_root = manifest_path.parent.resolve()
    expected_workspace = attempt_root / "workspace" / "repo"
    actual_workspace = manifest.get("workspace_repo")
    if not isinstance(actual_workspace, str) or not actual_workspace.strip():
        raise SealedResultError("workspace manifest workspace_repo missing")
    if Path(actual_workspace).expanduser().resolve() != expected_workspace.resolve():
        raise SealedResultError("workspace manifest does not match attempt workspace layout")
    if manifest.get("canonical_write_allowed") is not False:
        raise SealedResultError("workspace canonical_write_allowed must remain false")
    return attempt_root, manifest


def _resume_projection(
    *,
    attempt_root: Path,
    resume_evidence_path: Path | str | None,
) -> dict[str, Any]:
    if resume_evidence_path is None:
        return {
            "source": None,
            "resume_coordinates": None,
            "freshness_resume": None,
            "evidence_state": "NOT_SUPPLIED",
            "pause_resume_authority": False,
        }

    path = Path(resume_evidence_path).expanduser().resolve()
    allowed_roots = (
        (attempt_root / "evidence").resolve(),
        (attempt_root / "result").resolve(),
    )
    if not any(path == root or path.is_relative_to(root) for root in allowed_roots):
        raise SealedResultError(
            "resume evidence must remain inside the bound attempt evidence/result surface"
        )
    value = _load_yaml(path, "resume evidence")
    return {
        "source": str(path),
        "resume_coordinates": value.get("resume_coordinates"),
        "freshness_resume": value.get("freshness_resume"),
        "evidence_state": "PROJECTED_NOT_AUTHORITY",
        "pause_resume_authority": False,
    }


def _write_immutable_yaml(path: Path, payload: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise SealedResultError(f"refusing to overwrite sealed evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            dict(payload),
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )


def build_checkpoint_projection(
    *,
    manifest_path: Path | str,
    session_projection: Mapping[str, Any],
    resume_evidence_path: Path | str | None = None,
) -> dict[str, Any]:
    attempt_root, manifest = _attempt_binding(manifest_path)

    try:
        sandbox = sandbox_status(
            manifest_path=manifest_path,
            session_projection=session_projection,
        )
        worker_delta = derive_worker_delta_from_manifest(manifest_path)
    except (AssistantDevSandboxError, WorkspaceProvisionError, ValueError) as exc:
        raise SealedResultError(str(exc)) from exc

    resume = _resume_projection(
        attempt_root=attempt_root,
        resume_evidence_path=resume_evidence_path,
    )

    changed_paths = worker_delta.get("changed_paths")
    if not isinstance(changed_paths, list) or not all(
        isinstance(item, str) and item for item in changed_paths
    ):
        raise SealedResultError("shared worker delta changed_paths is invalid")

    payload: dict[str, Any] = {
        "schema_version": CHECKPOINT_SCHEMA,
        "state": "CHECKPOINT_PROJECTED",
        "identity": {
            "module_id": manifest.get("module_id"),
            "worker_id": manifest.get("worker_id"),
            "attempt_id": manifest.get("attempt_id"),
            "actor_type": sandbox["actor"]["actor_type"],
            "actor_id": sandbox["actor"]["actor_id"],
        },
        "base": {
            "base_head": sandbox["base"]["base_head"],
            "source_state_fingerprint": sandbox["base"]["source_state_fingerprint"],
            "workspace_manifest": str(Path(manifest_path).expanduser().resolve()),
            "worker_baseline_fingerprint": worker_delta.get(
                "baseline_fingerprint_sha256"
            ),
        },
        "worker_delta": worker_delta,
        "environment_delta": sandbox["environment_delta"],
        "resume_projection": resume,
        "recommended_canonical_write_set": sorted(changed_paths),
        "promotion_preconditions": [
            "OC01_MINI_5_NOT_YET_ACTIVE",
            "EXCLUSIVE_MODULE_LEASE_REQUIRED",
            "CANONICAL_SOURCE_FRESHNESS_REQUIRED",
            "EXACT_WRITE_SET_REVIEW_REQUIRED",
            "EXPLICIT_PROMOTION_AUTHORIZATION_REQUIRED",
        ],
        "authority": {
            "state_authority": False,
            "lease_authority": False,
            "pause_resume_authority": False,
            "canonical_write_authority": False,
            "promotion_authority": False,
            "release_authority": False,
        },
        "actions_performed": {
            "pause": False,
            "resume": False,
            "canonical_write": False,
            "promotion": False,
            "remote_push": False,
            "merge": False,
            "release": False,
        },
        "dependency_state": {
            "canonical_pause_resume": PAUSE_RESUME_STATE,
            "local_sandbox_commits": "DEPENDENCY_PENDING_CF10",
            "canonical_promotion": PROMOTION_STATE,
        },
    }
    payload["checkpoint_sha256"] = _canonical_sha256(payload)
    return payload


def write_checkpoint_projection(
    *,
    manifest_path: Path | str,
    session_projection: Mapping[str, Any],
    resume_evidence_path: Path | str | None = None,
) -> dict[str, Any]:
    attempt_root, _ = _attempt_binding(manifest_path)
    path = attempt_root / "evidence" / "oc01_checkpoint_projection_v0_1.yaml"
    payload = build_checkpoint_projection(
        manifest_path=manifest_path,
        session_projection=session_projection,
        resume_evidence_path=resume_evidence_path,
    )
    _write_immutable_yaml(path, payload)
    result = dict(payload)
    result["evidence_path"] = str(path.resolve())
    return result


def _normalize_strings(values: Sequence[str] | None) -> list[str]:
    if values is None:
        return []
    return sorted(
        {item.strip() for item in values if isinstance(item, str) and item.strip()}
    )


def build_sealed_result_package(
    *,
    manifest_path: Path | str,
    session_projection: Mapping[str, Any],
    validation_evidence: Sequence[str],
    artifacts: Sequence[str] | None = None,
    open_issues: Sequence[str] | None = None,
    resume_evidence_path: Path | str | None = None,
) -> dict[str, Any]:
    attempt_root, manifest = _attempt_binding(manifest_path)
    checkpoint_path = attempt_root / "evidence" / "oc01_checkpoint_projection_v0_1.yaml"
    checkpoint = _load_yaml(checkpoint_path, "OC01 checkpoint projection")

    if checkpoint.get("schema_version") != CHECKPOINT_SCHEMA:
        raise SealedResultError("checkpoint projection schema mismatch")

    checkpoint_hash = checkpoint.get("checkpoint_sha256")
    checkpoint_core = dict(checkpoint)
    checkpoint_core.pop("checkpoint_sha256", None)
    if checkpoint_hash != _canonical_sha256(checkpoint_core):
        raise SealedResultError("checkpoint projection hash mismatch")

    try:
        sandbox = sandbox_status(
            manifest_path=manifest_path,
            session_projection=session_projection,
        )
    except AssistantDevSandboxError as exc:
        raise SealedResultError(str(exc)) from exc

    validation = _normalize_strings(validation_evidence)
    if not validation:
        raise SealedResultError("at least one validation_evidence item is required")

    worker_delta = checkpoint.get("worker_delta")
    if not isinstance(worker_delta, dict):
        raise SealedResultError("checkpoint worker_delta missing")
    changed_paths = worker_delta.get("changed_paths")
    if not isinstance(changed_paths, list):
        raise SealedResultError("checkpoint changed_paths invalid")

    resume = checkpoint.get("resume_projection")
    if resume_evidence_path is not None:
        resume = _resume_projection(
            attempt_root=attempt_root,
            resume_evidence_path=resume_evidence_path,
        )

    payload: dict[str, Any] = {
        "schema_version": SEALED_RESULT_SCHEMA,
        "state": "SEALED",
        "module_id": manifest.get("module_id"),
        "worker_id": manifest.get("worker_id"),
        "attempt_id": manifest.get("attempt_id"),
        "base_head": sandbox["base"]["base_head"],
        "final_workspace_head": sandbox["environment_delta"][
            "current_workspace_head"
        ],
        "source_state_fingerprint": sandbox["base"]["source_state_fingerprint"],
        "changed_paths": sorted(changed_paths),
        "worker_delta": worker_delta,
        "environment_delta": sandbox["environment_delta"],
        "validation_evidence": validation,
        "artifacts": _normalize_strings(artifacts),
        "checkpoint_projection": {
            "path": str(checkpoint_path.resolve()),
            "checkpoint_sha256": checkpoint_hash,
        },
        "resume_coordinates": (
            resume.get("resume_coordinates") if isinstance(resume, dict) else None
        ),
        "freshness_resume": (
            resume.get("freshness_resume") if isinstance(resume, dict) else None
        ),
        "open_issues": _normalize_strings(open_issues),
        "recommended_canonical_write_set": sorted(changed_paths),
        "promotion_preconditions": checkpoint.get("promotion_preconditions", []),
        "authority": {
            "state_authority": False,
            "lease_authority": False,
            "pause_resume_authority": False,
            "canonical_write_authority": False,
            "promotion_authority": False,
            "remote_push_authority": False,
            "merge_authority": False,
            "release_authority": False,
        },
        "actions_performed": {
            "canonical_write": False,
            "promotion": False,
            "remote_push": False,
            "merge": False,
            "release": False,
        },
        "hash_scope": "canonical_json_without_package_sha256",
    }
    payload["package_sha256"] = _canonical_sha256(payload)
    return payload


def write_sealed_result_package(
    *,
    manifest_path: Path | str,
    session_projection: Mapping[str, Any],
    validation_evidence: Sequence[str],
    artifacts: Sequence[str] | None = None,
    open_issues: Sequence[str] | None = None,
    resume_evidence_path: Path | str | None = None,
) -> dict[str, Any]:
    attempt_root, _ = _attempt_binding(manifest_path)
    path = attempt_root / "result" / "oc01_sealed_result_v0_1.yaml"
    payload = build_sealed_result_package(
        manifest_path=manifest_path,
        session_projection=session_projection,
        validation_evidence=validation_evidence,
        artifacts=artifacts,
        open_issues=open_issues,
        resume_evidence_path=resume_evidence_path,
    )
    _write_immutable_yaml(path, payload)
    result = dict(payload)
    result["result_path"] = str(path.resolve())
    return result


def sealed_result_status(*, manifest_path: Path | str) -> dict[str, Any]:
    attempt_root, manifest = _attempt_binding(manifest_path)
    checkpoint = attempt_root / "evidence" / "oc01_checkpoint_projection_v0_1.yaml"
    result = attempt_root / "result" / "oc01_sealed_result_v0_1.yaml"
    return {
        "schema_version": "forprint_oc01_sealed_result_status_v0_1",
        "module_id": manifest.get("module_id"),
        "attempt_id": manifest.get("attempt_id"),
        "checkpoint": {
            "exists": checkpoint.is_file(),
            "path": str(checkpoint.resolve()),
        },
        "sealed_result": {
            "exists": result.is_file(),
            "path": str(result.resolve()),
        },
        "canonical_pause_resume": PAUSE_RESUME_STATE,
        "canonical_promotion": PROMOTION_STATE,
        "authority": {
            "state_authority": False,
            "canonical_write_authority": False,
            "promotion_authority": False,
        },
    }


def _load_session(path: Path | str) -> dict[str, Any]:
    return _load_yaml(Path(path).expanduser().resolve(), "session projection")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OC-01 MINI-4 checkpoint projection and deterministic result seal"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    checkpoint = sub.add_parser("checkpoint")
    checkpoint.add_argument("--manifest", required=True)
    checkpoint.add_argument("--session-projection", required=True)
    checkpoint.add_argument("--resume-evidence")

    seal = sub.add_parser("seal")
    seal.add_argument("--manifest", required=True)
    seal.add_argument("--session-projection", required=True)
    seal.add_argument("--validation-evidence", action="append", default=[])
    seal.add_argument("--artifact", action="append", default=[])
    seal.add_argument("--open-issue", action="append", default=[])
    seal.add_argument("--resume-evidence")

    status = sub.add_parser("status")
    status.add_argument("--manifest", required=True)

    args = parser.parse_args()
    if args.command == "checkpoint":
        result = write_checkpoint_projection(
            manifest_path=args.manifest,
            session_projection=_load_session(args.session_projection),
            resume_evidence_path=args.resume_evidence,
        )
    elif args.command == "seal":
        result = write_sealed_result_package(
            manifest_path=args.manifest,
            session_projection=_load_session(args.session_projection),
            validation_evidence=args.validation_evidence,
            artifacts=args.artifact,
            open_issues=args.open_issue,
            resume_evidence_path=args.resume_evidence,
        )
    else:
        result = sealed_result_status(manifest_path=args.manifest)

    print(
        yaml.safe_dump(
            result,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ).rstrip()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
