from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.coordination.control_plane.operator_console.assistant_dev_sandbox import (
    AssistantDevSandboxError,
    create_sandbox,
)
from scripts.coordination.control_plane.operator_console.promotion_surface import (
    EXPLICIT_APPLY_TOKEN,
    PromotionSurfaceError,
    apply_promotion_from_preview,
    write_promotion_preview,
)
from scripts.coordination.control_plane.operator_console.sealed_result import (
    SealedResultError,
    write_checkpoint_projection,
    write_sealed_result_package,
)
from scripts.coordination.control_plane.operator_console.session_projection import (
    build_session_projection,
)
from scripts.coordination.control_plane.workspace.provision import (
    WorkspaceProvisionError,
)

SCHEMA_VERSION = "forprint_oc01_sandbox_to_canonical_real_proof_v0_1"
PROBE_RELATIVE = (
    "coordination/internal_work/blueprint/operator_console/proofs/"
    "oc01_mini8_real_promotion_probe_v0_1.txt"
)
PROFILE_ID = "light-maintenance"
PROFILE_REVISION = "r1"
PROFILE_REF = f"{PROFILE_ID}@{PROFILE_REVISION}"
PROCEDURE_ID = "governed_canonical_mutation"
ATTEMPT_ID = "oc01-mini8-real-promotion-proof"


class SandboxToCanonicalProofError(RuntimeError):
    pass


def _run_git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if cp.returncode != 0:
        raise SandboxToCanonicalProofError(
            "git command failed rc="
            + str(cp.returncode)
            + ": "
            + " ".join(args)
            + "\n"
            + cp.stdout
        )
    return cp.stdout


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        dict(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(raw)


def _assert_outside(canonical: Path, path: Path, label: str) -> None:
    canonical = canonical.resolve()
    path = path.resolve()
    if path == canonical or canonical in path.parents:
        raise SandboxToCanonicalProofError(
            f"{label} must remain outside canonical repository"
        )


def _write_yaml_new(path: Path, value: Mapping[str, Any]) -> Path:
    if path.exists() or path.is_symlink():
        raise SandboxToCanonicalProofError(
            f"refusing to overwrite immutable proof input/evidence: {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            dict(value),
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )
    return path.resolve()


def _status_paths(repo: Path) -> list[str]:
    raw = _run_git(
        repo,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    paths: list[str] = []
    for row in raw.splitlines():
        if not row:
            continue
        path = row[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return sorted(set(paths))


def _staged_paths(repo: Path) -> list[str]:
    return sorted(
        x
        for x in _run_git(
            repo,
            "diff",
            "--cached",
            "--name-only",
        ).splitlines()
        if x
    )


def _path_fingerprint(repo: Path, relative: str) -> dict[str, Any]:
    path = (repo / relative).resolve()
    if path.is_symlink():
        target = path.readlink().as_posix().encode("utf-8")
        return {"kind": "symlink", "sha256": _sha256_bytes(target)}
    if path.is_file():
        return {"kind": "file", "sha256": _sha256_file(path)}
    if path.exists():
        return {"kind": "other", "sha256": None}
    return {"kind": "missing", "sha256": None}


def _snapshot_dirty_bytes(repo: Path, paths: list[str]) -> dict[str, Any]:
    return {
        relative: _path_fingerprint(repo, relative)
        for relative in paths
    }


def _probe_content(base_head: str) -> str:
    return (
        "OC01-MINI-8 REAL PROMOTION PROBE\n"
        f"source_head={base_head}\n"
        "flow=sandbox->checkpoint->sealed-result->preview->explicit-promotion->validation\n"
        "promotion_authority=OPERATOR_CONTROLLED_CF10\n"
        "automatic_stage=false\n"
        "automatic_commit=false\n"
        "automatic_push=false\n"
        "automatic_merge=false\n"
        "automatic_release=false\n"
    )


def _session(canonical: Path) -> dict[str, Any]:
    return build_session_projection(
        launch_request={
            "identity": {
                "module_id": "forprint_system_blueprint",
                "prompt_id": "oc01-mini8-sandbox-to-canonical-real-proof",
            }
        },
        worker_invocation={
            "attempt_id": ATTEMPT_ID,
            "worker_id": "operator-assistant",
            "workspace_repo": str(canonical / ".oc01-not-used-as-workspace"),
            "heartbeat_seconds": 30,
        },
        actor_type="operator_assistant",
        actor_id="oc01-mini8-operator-assistant-proof",
        workspace_manifest=None,
    )


def _handoff_inputs(
    *,
    runtime: Path,
    sealed: Mapping[str, Any],
) -> dict[str, Path]:
    changed = list(sealed["changed_paths"])
    source_fingerprint = sealed.get("source_state_fingerprint")
    cursor = {
        "contour": "OC01-MINI-8",
        "event_sequence": 8,
        "state": "REAL_PROMOTION_PROOF",
    }
    binding_material = {
        "attempt_id": sealed["attempt_id"],
        "base_head": sealed["base_head"],
        "changed_paths": changed,
        "source_state_fingerprint": source_fingerprint,
        "cursor": cursor,
    }
    handoff_sha = _canonical_sha256(binding_material)

    work_front = {
        "work_front_id": "wf-oc01-mini8-real-promotion-runtime",
        "scope": changed,
        "proof_only": True,
    }
    origin = {
        "launch_mode": "TASK_EXECUTION",
        "handoff_manifest_sha256": handoff_sha,
        "source_state_fingerprint": source_fingerprint,
        "lifecycle_roadmap_cursor": cursor,
        "execution_profile_revision_for_task_execution": {
            "profile_id": PROFILE_ID,
            "revision": PROFILE_REVISION,
        },
        "governed_procedure_revision_or_not_required_reason": {
            "classification": "GRAPH_REQUIRED",
            "procedure_id": PROCEDURE_ID,
        },
        "proof_binding_material_sha256": handoff_sha,
    }
    handoff = {
        "attempt_id": sealed["attempt_id"],
        "status": "PASS",
        "handoff_manifest_sha256": handoff_sha,
        "changed_paths": changed,
        "resume_coordinates": {
            "attempt_id": sealed["attempt_id"],
            "handoff_manifest_sha256": handoff_sha,
            "source_state_fingerprint": source_fingerprint,
            "lifecycle_roadmap_cursor": cursor,
        },
        "proof_only": True,
    }

    inputs = runtime / "promotion_inputs"
    return {
        "work_front": _write_yaml_new(inputs / "work_front.yaml", work_front),
        "origin": _write_yaml_new(inputs / "origin_handoff.yaml", origin),
        "handoff": _write_yaml_new(inputs / "handoff_result.yaml", handoff),
    }


def run_sandbox_to_canonical_real_proof(
    *,
    canonical_repo: Path | str,
    runtime_root: Path | str,
    expected_base_head: str,
    explicit_authorization: str,
) -> dict[str, Any]:
    canonical = Path(canonical_repo).expanduser().resolve()
    runtime = Path(runtime_root).expanduser().resolve()

    if not (canonical / ".git").exists():
        raise SandboxToCanonicalProofError(
            "canonical_repo must be a Git checkout"
        )
    _assert_outside(canonical, runtime, "runtime_root")
    if runtime.exists():
        raise SandboxToCanonicalProofError(
            "runtime_root already exists; proof replay is forbidden"
        )

    current_head = _run_git(canonical, "rev-parse", "HEAD").strip()
    if current_head != expected_base_head:
        raise SandboxToCanonicalProofError(
            "BASE_HEAD mismatch: expected="
            + expected_base_head
            + " observed="
            + current_head
        )

    probe = canonical / PROBE_RELATIVE
    if probe.exists() or probe.is_symlink():
        raise SandboxToCanonicalProofError(
            "dedicated canonical proof target must be absent before proof"
        )

    before_status = _status_paths(canonical)
    before_staged = _staged_paths(canonical)
    before_dirty_fingerprints = _snapshot_dirty_bytes(
        canonical,
        before_status,
    )

    runtime.mkdir(parents=True, exist_ok=False)
    session = _session(canonical)

    try:
        created = create_sandbox(
            canonical_repo=canonical,
            runtime_root=runtime / "sandbox_runtime",
            module_id="forprint_system_blueprint",
            worker_id="operator-assistant",
            attempt_id=ATTEMPT_ID,
            expected_base_head=expected_base_head,
            session_projection=session,
        )
        manifest = Path(created["sandbox"]["manifest"]).resolve()
        workspace = Path(created["sandbox"]["workspace_repo"]).resolve()

        if workspace == canonical:
            raise SandboxToCanonicalProofError(
                "sandbox workspace unexpectedly equals canonical repository"
            )
        if created["sandbox"]["canonical_write_allowed"] is not False:
            raise SandboxToCanonicalProofError(
                "sandbox unexpectedly allows canonical writes"
            )

        workspace_probe = workspace / PROBE_RELATIVE
        if workspace_probe.exists():
            raise SandboxToCanonicalProofError(
                "sandbox proof target unexpectedly existed at baseline"
            )
        workspace_probe.parent.mkdir(parents=True, exist_ok=True)
        expected_probe_content = _probe_content(expected_base_head)
        workspace_probe.write_text(
            expected_probe_content,
            encoding="utf-8",
        )

        checkpoint = write_checkpoint_projection(
            manifest_path=manifest,
            session_projection=session,
        )
        if checkpoint["worker_delta"]["worker_delta_exact"] is not True:
            raise SandboxToCanonicalProofError(
                "worker delta is not exact"
            )
        if checkpoint["worker_delta"]["changed_paths"] != [PROBE_RELATIVE]:
            raise SandboxToCanonicalProofError(
                "worker delta is not restricted to dedicated proof target"
            )
        if checkpoint["recommended_canonical_write_set"] != [PROBE_RELATIVE]:
            raise SandboxToCanonicalProofError(
                "checkpoint recommended write-set drift"
            )

        sealed = write_sealed_result_package(
            manifest_path=manifest,
            session_projection=session,
            validation_evidence=[
                "oc01-mini8-worker-delta-exact:PASS",
                "oc01-mini8-probe-content-pre-promotion:PASS",
            ],
            artifacts=[str(workspace_probe)],
            open_issues=[],
        )
        if sealed["changed_paths"] != [PROBE_RELATIVE]:
            raise SandboxToCanonicalProofError(
                "sealed result changed path drift"
            )
        if sealed["recommended_canonical_write_set"] != [PROBE_RELATIVE]:
            raise SandboxToCanonicalProofError(
                "sealed result recommended write-set drift"
            )

        source_inputs = _handoff_inputs(
            runtime=runtime,
            sealed=sealed,
        )
        preview_path = runtime / "promotion" / "preview.yaml"
        preview = write_promotion_preview(
            output_path=preview_path,
            root=canonical,
            candidate_root=workspace,
            sealed_result_path=sealed["result_path"],
            work_front_path=source_inputs["work_front"],
            origin_handoff_manifest_path=source_inputs["origin"],
            handoff_result_path=source_inputs["handoff"],
            expected_profile_ref=PROFILE_REF,
            expected_procedure_id=PROCEDURE_ID,
            operator_review=True,
        )
        if preview["changed_paths"] != [PROBE_RELATIVE]:
            raise SandboxToCanonicalProofError(
                "promotion preview changed path drift"
            )
        if preview["actions_performed"]["canonical_write"] is not False:
            raise SandboxToCanonicalProofError(
                "promotion preview unexpectedly mutated canonical"
            )

        if probe.exists():
            raise SandboxToCanonicalProofError(
                "canonical proof target appeared before explicit apply"
            )

        def validate_after_apply(paths: list[str]) -> dict[str, Any]:
            if paths != [PROBE_RELATIVE]:
                return {
                    "result": "FAIL",
                    "reason": "unexpected promoted path set",
                }
            if not probe.is_file():
                return {
                    "result": "FAIL",
                    "reason": "canonical proof target missing",
                }
            if probe.read_text(encoding="utf-8") != expected_probe_content:
                return {
                    "result": "FAIL",
                    "reason": "canonical proof content mismatch",
                }
            if _run_git(canonical, "rev-parse", "HEAD").strip() != expected_base_head:
                return {
                    "result": "FAIL",
                    "reason": "canonical HEAD changed during promotion",
                }
            if _staged_paths(canonical) != before_staged:
                return {
                    "result": "FAIL",
                    "reason": "canonical staging changed during promotion",
                }
            cp = subprocess.run(
                [
                    "git",
                    "-C",
                    str(canonical),
                    "diff",
                    "--check",
                    "--",
                    PROBE_RELATIVE,
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if cp.returncode != 0:
                return {
                    "result": "FAIL",
                    "reason": "git diff --check failed",
                    "output": cp.stdout,
                }
            return {
                "result": "PASS",
                "validated_paths": paths,
                "probe_sha256": _sha256_file(probe),
                "head_unchanged": True,
                "staging_unchanged": True,
            }

        apply_evidence = runtime / "promotion" / "apply_result.yaml"
        recovery_root = runtime / "promotion" / "recovery"
        applied = apply_promotion_from_preview(
            preview_path=preview["preview_path"],
            root=canonical,
            candidate_root=workspace,
            recovery_root=recovery_root,
            evidence_path=apply_evidence,
            explicit_authorization=explicit_authorization,
            expected_preview_sha256=preview["preview_sha256"],
            post_apply_validator=validate_after_apply,
        )
    except (
        AssistantDevSandboxError,
        SealedResultError,
        PromotionSurfaceError,
        WorkspaceProvisionError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        raise SandboxToCanonicalProofError(str(exc)) from exc

    if explicit_authorization != EXPLICIT_APPLY_TOKEN:
        raise SandboxToCanonicalProofError(
            "explicit authorization unexpectedly accepted"
        )

    shared = applied.get("shared_result")
    if not isinstance(shared, Mapping):
        raise SandboxToCanonicalProofError(
            "shared candidate promotion result missing"
        )
    if shared.get("candidate_promoted") is not True:
        raise SandboxToCanonicalProofError(
            "shared candidate promotion did not promote candidate"
        )
    if shared.get("canonical_write_performed") is not True:
        raise SandboxToCanonicalProofError(
            "shared candidate promotion did not record bounded canonical write"
        )
    for key in (
        "staging_performed",
        "commit_performed",
        "push_performed",
        "merge_performed",
        "release_performed",
        "automatic_accept_performed",
    ):
        if shared.get(key) is not False:
            raise SandboxToCanonicalProofError(
                f"shared promotion unexpectedly performed {key}"
            )

    surface_actions = applied.get("actions_performed_by_surface")
    if not isinstance(surface_actions, Mapping) or any(
        value is not False for value in surface_actions.values()
    ):
        raise SandboxToCanonicalProofError(
            "promotion surface unexpectedly performed forbidden action"
        )

    after_head = _run_git(canonical, "rev-parse", "HEAD").strip()
    after_staged = _staged_paths(canonical)
    after_status = _status_paths(canonical)
    if after_head != expected_base_head:
        raise SandboxToCanonicalProofError(
            "canonical HEAD changed during MINI-8 proof"
        )
    if after_staged != before_staged:
        raise SandboxToCanonicalProofError(
            "canonical staging changed during MINI-8 proof"
        )

    expected_after_status = sorted(set(before_status) | {PROBE_RELATIVE})
    if after_status != expected_after_status:
        raise SandboxToCanonicalProofError(
            "canonical status changed outside dedicated proof target"
        )

    after_existing_fingerprints = _snapshot_dirty_bytes(
        canonical,
        before_status,
    )
    if after_existing_fingerprints != before_dirty_fingerprints:
        raise SandboxToCanonicalProofError(
            "pre-existing canonical dirty path bytes changed during proof"
        )

    if not probe.is_file():
        raise SandboxToCanonicalProofError(
            "canonical proof target missing after promotion"
        )
    expected_content = _probe_content(expected_base_head)
    if probe.read_text(encoding="utf-8") != expected_content:
        raise SandboxToCanonicalProofError(
            "canonical proof target content mismatch after promotion"
        )

    if not apply_evidence.is_file():
        raise SandboxToCanonicalProofError(
            "shared promotion evidence missing"
        )
    sealed_path = Path(sealed["result_path"]).resolve()
    checkpoint_path = Path(checkpoint["evidence_path"]).resolve()
    preview_written = Path(preview["preview_path"]).resolve()
    for label, evidence in (
        ("checkpoint", checkpoint_path),
        ("sealed result", sealed_path),
        ("preview", preview_written),
        ("apply evidence", apply_evidence),
    ):
        _assert_outside(canonical, evidence, label)
        if not evidence.is_file():
            raise SandboxToCanonicalProofError(
                f"{label} evidence missing: {evidence}"
            )

    proof_path = runtime / "result" / "oc01_mini8_real_proof_v0_1.yaml"
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "state": "PASS",
        "proof_flow": (
            "SANDBOX_TO_CHECKPOINT_TO_SEALED_RESULT_TO_PREVIEW_"
            "TO_EXPLICIT_CF10_PROMOTION_TO_VALIDATION"
        ),
        "canonical_repo": str(canonical),
        "runtime_root": str(runtime),
        "base_head": expected_base_head,
        "attempt_id": ATTEMPT_ID,
        "probe": {
            "path": PROBE_RELATIVE,
            "operation": "CREATE",
            "sha256": _sha256_file(probe),
            "created_in_sandbox_first": True,
            "canonical_absent_before_explicit_apply": True,
            "canonical_present_after_explicit_apply": True,
        },
        "sandbox": {
            "manifest": str(manifest),
            "workspace": str(workspace),
            "canonical_write_allowed": False,
            "local_commit_required": False,
        },
        "checkpoint": {
            "path": str(checkpoint_path),
            "sha256": checkpoint["checkpoint_sha256"],
            "changed_paths": checkpoint["worker_delta"]["changed_paths"],
        },
        "sealed_result": {
            "path": str(sealed_path),
            "sha256": sealed["package_sha256"],
            "recommended_canonical_write_set": sealed[
                "recommended_canonical_write_set"
            ],
        },
        "promotion_preview": {
            "path": str(preview_written),
            "sha256": preview["preview_sha256"],
            "explicit_authorization_required": True,
            "exact_preview_sha256_required": True,
        },
        "promotion_apply": {
            "path": str(apply_evidence),
            "sha256": _sha256_file(apply_evidence),
            "recovery_root": str(recovery_root),
            "delegated_to_shared_cf10_engine": True,
            "candidate_promoted": True,
            "canonical_write_performed": True,
            "staging_performed": False,
            "commit_performed": False,
            "push_performed": False,
            "merge_performed": False,
            "release_performed": False,
            "automatic_accept_performed": False,
        },
        "canonical_invariants": {
            "head_before": expected_base_head,
            "head_after": after_head,
            "head_unchanged": True,
            "staged_paths_before": before_staged,
            "staged_paths_after": after_staged,
            "staging_unchanged": True,
            "status_paths_before": before_status,
            "status_paths_after": after_status,
            "only_probe_added_to_status": True,
            "preexisting_dirty_path_bytes_unchanged": True,
        },
        "authority": {
            "console_is_state_authority": False,
            "new_execution_truth_created": False,
            "new_lease_authority_created": False,
            "sandbox_direct_canonical_write_authority": False,
            "promotion_authority_owner": "OPERATOR_CONTROLLED_CF10",
            "commit_authority": False,
            "push_authority": False,
            "merge_authority": False,
            "release_authority": False,
        },
        "completion_boundary": {
            "mini8_real_proof": "PASS",
            "after_publication": "USEFUL_MINIMUM_PROVEN_PARTIAL_OC01",
            "must_not_claim": "OC01_FULL_COMPLETE",
        },
        "hash_scope": "canonical_json_without_package_sha256",
    }
    payload["package_sha256"] = _canonical_sha256(payload)
    proof_path = _write_yaml_new(proof_path, payload)

    result = dict(payload)
    result["proof_path"] = str(proof_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OC-01 MINI-8 sandbox-to-canonical real proof"
    )
    parser.add_argument("--canonical-repo", default=".")
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--base-head", required=True)
    parser.add_argument("--authorization", required=True)
    args = parser.parse_args()

    result = run_sandbox_to_canonical_real_proof(
        canonical_repo=args.canonical_repo,
        runtime_root=args.runtime_root,
        expected_base_head=args.base_head,
        explicit_authorization=args.authorization,
    )

    print("OC01_MINI8_SANDBOX_TO_CANONICAL_REAL_PROOF=PASS")
    print(f"PROOF_EVIDENCE={result['proof_path']}")
    print(f"PROOF_SHA256={result['package_sha256']}")
    print(
        "SEALED_RESULT_SHA256="
        + result["sealed_result"]["sha256"]
    )
    print(
        "PREVIEW_SHA256="
        + result["promotion_preview"]["sha256"]
    )
    print(f"PROMOTED_PROBE={result['probe']['path']}")
    print(f"CANONICAL_HEAD={result['base_head']}")
    print("EXPLICIT_PROMOTION=true")
    print("SHARED_CF10_PROMOTION_ENGINE_REUSED=true")
    print("CANONICAL_WRITE_PERFORMED=true")
    print("CANONICAL_WRITE_PATH_COUNT=1")
    print("STAGING_PERFORMED=false")
    print("COMMIT_PERFORMED=false")
    print("PUSH_PERFORMED=false")
    print("MERGE_PERFORMED=false")
    print("RELEASE_PERFORMED=false")
    print("PREEXISTING_DIRTY_BYTES_UNCHANGED=true")
    print("COMPLETION_AFTER_PUBLICATION=USEFUL_MINIMUM_PROVEN_PARTIAL_OC01")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
