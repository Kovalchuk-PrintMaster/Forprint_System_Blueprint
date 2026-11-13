from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.operator_console import promotion_surface
from scripts.coordination.control_plane.operator_console.promotion_surface import (
    EXPLICIT_APPLY_TOKEN,
    PromotionSurfaceError,
    apply_promotion_from_preview,
    build_promotion_preview,
    write_promotion_preview,
)
from scripts.coordination.control_plane.operator_console.sealed_result import (
    SEALED_RESULT_SCHEMA,
)


def git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    return cp.stdout.strip()


def promotion_contract() -> dict:
    return {
        "contract_id": "worker_candidate_promotion_contract",
        "authority_semantics": {
            "worker_can_promote": False,
            "worker_can_commit_canonical": False,
            "worker_can_push": False,
            "worker_can_merge": False,
            "worker_can_release": False,
            "worker_can_auto_accept": False,
            "promotion_authority": "OPERATOR_CONTROLLED_CF10",
        },
        "required_pre_promotion_checks": [
            "handoff_v2_result_validation",
            "work_front_scope_validation",
            "execution_profile_ceiling_validation",
            "procedure_conformance",
            "source_freshness_validation",
            "changed_path_validation",
            "operator_review",
        ],
    }


def fixture_repo(tmp_path: Path) -> tuple[Path, Path, str]:
    canonical = tmp_path / "canonical"
    candidate = tmp_path / "candidate"
    canonical.mkdir()
    git(canonical, "init", "-q")
    git(canonical, "config", "user.email", "oc01@example.invalid")
    git(canonical, "config", "user.name", "OC01 Test")

    (canonical / "existing.txt").write_text("old\n", encoding="utf-8")
    (canonical / "delete.txt").write_text("delete-me\n", encoding="utf-8")
    contract_path = (
        canonical
        / "coordination/standards/automation/"
        / "worker_candidate_promotion_contract_v0_1.yaml"
    )
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        yaml.safe_dump(promotion_contract(), sort_keys=False),
        encoding="utf-8",
    )
    git(canonical, "add", ".")
    git(canonical, "commit", "-q", "-m", "baseline")
    source_head = git(canonical, "rev-parse", "HEAD")

    subprocess.run(
        ["git", "clone", "-q", str(canonical), str(candidate)],
        check=True,
    )
    (candidate / "existing.txt").write_text("new\n", encoding="utf-8")
    (candidate / "new.txt").write_text("created\n", encoding="utf-8")
    (candidate / "delete.txt").unlink()
    return canonical.resolve(), candidate.resolve(), source_head


def write_yaml(path: Path, value: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
    )
    return path.resolve()


def source_inputs(
    tmp_path: Path,
    source_head: str,
    changed: list[str],
) -> dict[str, Path | str]:
    origin = {
        "launch_mode": "TASK_EXECUTION",
        "handoff_manifest_sha256": "a" * 64,
        "source_state_fingerprint": "b" * 64,
        "lifecycle_roadmap_cursor": {"event_sequence": 1},
        "execution_profile_revision_for_task_execution": {
            "profile_id": "light-maintenance",
            "revision": "r1",
        },
        "governed_procedure_revision_or_not_required_reason": {
            "classification": "GRAPH_REQUIRED",
            "procedure_id": "governed_canonical_mutation",
        },
    }
    handoff = {
        "attempt_id": "oc01-mini5-attempt",
        "status": "PASS",
        "handoff_manifest_sha256": "a" * 64,
        "changed_paths": changed,
        "resume_coordinates": {
            "attempt_id": "oc01-mini5-attempt",
            "handoff_manifest_sha256": "a" * 64,
            "source_state_fingerprint": "b" * 64,
            "lifecycle_roadmap_cursor": {"event_sequence": 1},
        },
    }
    work_front = {
        "work_front_id": "wf-candidate-change",
        "scope": changed,
    }
    sealed = {
        "schema_version": SEALED_RESULT_SCHEMA,
        "state": "SEALED",
        "module_id": "forprint_system_blueprint",
        "worker_id": "operator-assistant",
        "attempt_id": "oc01-mini5-attempt",
        "base_head": source_head,
        "final_workspace_head": source_head,
        "source_state_fingerprint": "b" * 64,
        "changed_paths": changed,
        "worker_delta": {
            "changed_paths": changed,
            "worker_delta_exact": True,
        },
        "environment_delta": {
            "current_workspace_head": source_head,
        },
        "validation_evidence": ["pytest:PASS"],
        "artifacts": [],
        "checkpoint_projection": {
            "path": "/tmp/checkpoint.yaml",
            "checkpoint_sha256": "c" * 64,
        },
        "resume_coordinates": handoff["resume_coordinates"],
        "freshness_resume": {"valid": True, "errors": []},
        "open_issues": [],
        "recommended_canonical_write_set": changed,
        "promotion_preconditions": [
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
    sealed["package_sha256"] = promotion_surface._canonical_sha256(sealed)

    return {
        "sealed": write_yaml(tmp_path / "inputs/sealed.yaml", sealed),
        "work_front": write_yaml(tmp_path / "inputs/work_front.yaml", work_front),
        "origin": write_yaml(tmp_path / "inputs/origin.yaml", origin),
        "handoff": write_yaml(tmp_path / "inputs/handoff.yaml", handoff),
        "profile": "light-maintenance@r1",
        "procedure": "governed_canonical_mutation",
    }


def preview_kwargs(tmp_path: Path) -> tuple[Path, Path, dict]:
    canonical, candidate, source_head = fixture_repo(tmp_path)
    changed = ["delete.txt", "existing.txt", "new.txt"]
    inputs = source_inputs(tmp_path, source_head, changed)
    kwargs = {
        "root": canonical,
        "candidate_root": candidate,
        "sealed_result_path": inputs["sealed"],
        "work_front_path": inputs["work_front"],
        "origin_handoff_manifest_path": inputs["origin"],
        "handoff_result_path": inputs["handoff"],
        "expected_profile_ref": inputs["profile"],
        "expected_procedure_id": inputs["procedure"],
        "operator_review": True,
    }
    return canonical, candidate, kwargs


def test_preview_reuses_shared_plan_without_canonical_mutation(
    tmp_path: Path,
) -> None:
    canonical, _, kwargs = preview_kwargs(tmp_path)
    head_before = git(canonical, "rev-parse", "HEAD")
    status_before = git(canonical, "status", "--porcelain=v1")

    preview = build_promotion_preview(**kwargs)

    operations = {
        row["path"]: row["operation"]
        for row in preview["shared_promotion_plan"]["operations"]
    }
    assert operations == {
        "delete.txt": "DELETE",
        "existing.txt": "MODIFY",
        "new.txt": "CREATE",
    }
    assert preview["authority"]["promotion_authority"] == "OPERATOR_CONTROLLED_CF10"
    assert preview["actions_performed"]["canonical_write"] is False
    assert git(canonical, "rev-parse", "HEAD") == head_before
    assert git(canonical, "status", "--porcelain=v1") == status_before


def test_preview_requires_explicit_operator_review(tmp_path: Path) -> None:
    _, _, kwargs = preview_kwargs(tmp_path)
    kwargs["operator_review"] = False
    with pytest.raises(PromotionSurfaceError, match="operator review"):
        build_promotion_preview(**kwargs)


def test_tampered_sealed_result_is_rejected(tmp_path: Path) -> None:
    _, _, kwargs = preview_kwargs(tmp_path)
    path = Path(kwargs["sealed_result_path"])
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    value["changed_paths"] = ["existing.txt"]
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")

    with pytest.raises(PromotionSurfaceError, match="hash mismatch"):
        build_promotion_preview(**kwargs)


def test_preview_evidence_is_immutable_and_outside_canonical(
    tmp_path: Path,
) -> None:
    canonical, _, kwargs = preview_kwargs(tmp_path)
    output = tmp_path / "evidence" / "preview.yaml"
    written = write_promotion_preview(output_path=output, **kwargs)
    assert Path(written["preview_path"]).is_file()

    with pytest.raises(PromotionSurfaceError, match="overwrite"):
        write_promotion_preview(output_path=output, **kwargs)

    with pytest.raises(PromotionSurfaceError, match="outside"):
        write_promotion_preview(
            output_path=canonical / "preview.yaml",
            **kwargs,
        )


def test_apply_requires_token_and_exact_preview_hash(tmp_path: Path) -> None:
    canonical, candidate, kwargs = preview_kwargs(tmp_path)
    preview_path = tmp_path / "evidence" / "preview.yaml"
    preview = write_promotion_preview(output_path=preview_path, **kwargs)

    common = {
        "preview_path": preview_path,
        "root": canonical,
        "candidate_root": candidate,
        "recovery_root": tmp_path / "recovery",
        "evidence_path": tmp_path / "evidence" / "apply.yaml",
        "expected_preview_sha256": preview["preview_sha256"],
    }

    with pytest.raises(PromotionSurfaceError, match="authorization"):
        apply_promotion_from_preview(
            explicit_authorization="NO",
            **common,
        )

    with pytest.raises(PromotionSurfaceError, match="expected preview sha256"):
        apply_promotion_from_preview(
            explicit_authorization=EXPLICIT_APPLY_TOKEN,
            expected_preview_sha256="0" * 64,
            **{k: v for k, v in common.items() if k != "expected_preview_sha256"},
        )


def test_apply_revalidates_source_freshness_before_mutation(
    tmp_path: Path,
) -> None:
    canonical, candidate, kwargs = preview_kwargs(tmp_path)
    preview_path = tmp_path / "evidence" / "preview.yaml"
    preview = write_promotion_preview(output_path=preview_path, **kwargs)
    (canonical / "existing.txt").write_text("drift\n", encoding="utf-8")

    with pytest.raises(PromotionSurfaceError, match="TARGET_FRESHNESS_DRIFT"):
        apply_promotion_from_preview(
            preview_path=preview_path,
            root=canonical,
            candidate_root=candidate,
            recovery_root=tmp_path / "recovery",
            evidence_path=tmp_path / "evidence" / "apply.yaml",
            explicit_authorization=EXPLICIT_APPLY_TOKEN,
            expected_preview_sha256=preview["preview_sha256"],
        )

    assert (canonical / "existing.txt").read_text(encoding="utf-8") == "drift\n"
    assert not (canonical / "new.txt").exists()


def test_apply_delegates_exact_mutation_without_staging_commit_or_push(
    tmp_path: Path,
) -> None:
    canonical, candidate, kwargs = preview_kwargs(tmp_path)
    preview_path = tmp_path / "evidence" / "preview.yaml"
    preview = write_promotion_preview(output_path=preview_path, **kwargs)
    head_before = git(canonical, "rev-parse", "HEAD")

    result = apply_promotion_from_preview(
        preview_path=preview_path,
        root=canonical,
        candidate_root=candidate,
        recovery_root=tmp_path / "recovery",
        evidence_path=tmp_path / "evidence" / "apply.yaml",
        explicit_authorization=EXPLICIT_APPLY_TOKEN,
        expected_preview_sha256=preview["preview_sha256"],
        post_apply_validator=lambda paths: {
            "result": "PASS",
            "paths": paths,
        },
    )

    assert result["shared_result"]["candidate_promoted"] is True
    assert result["shared_result"]["canonical_write_performed"] is True
    assert result["shared_result"]["staging_performed"] is False
    assert result["shared_result"]["commit_performed"] is False
    assert result["shared_result"]["push_performed"] is False
    assert result["actions_performed_by_surface"]["commit"] is False
    assert (canonical / "existing.txt").read_text(encoding="utf-8") == "new\n"
    assert (canonical / "new.txt").read_text(encoding="utf-8") == "created\n"
    assert not (canonical / "delete.txt").exists()
    assert git(canonical, "rev-parse", "HEAD") == head_before
    assert git(canonical, "diff", "--cached", "--name-only") == ""
    assert (tmp_path / "evidence" / "apply.yaml").is_file()


def test_apply_rejects_candidate_root_different_from_preview(
    tmp_path: Path,
) -> None:
    canonical, _, kwargs = preview_kwargs(tmp_path)
    preview_path = tmp_path / "evidence" / "preview.yaml"
    preview = write_promotion_preview(output_path=preview_path, **kwargs)
    other = tmp_path / "other-candidate"
    other.mkdir()

    with pytest.raises(PromotionSurfaceError, match="candidate root differs"):
        apply_promotion_from_preview(
            preview_path=preview_path,
            root=canonical,
            candidate_root=other,
            recovery_root=tmp_path / "recovery",
            evidence_path=tmp_path / "evidence" / "apply.yaml",
            explicit_authorization=EXPLICIT_APPLY_TOKEN,
            expected_preview_sha256=preview["preview_sha256"],
        )
