from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from scripts.coordination.control_plane import candidate_promotion as promotion


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


def fixture_repo(tmp_path: Path) -> tuple[Path, Path, str]:
    canonical = tmp_path / "canonical"
    candidate = tmp_path / "candidate"
    canonical.mkdir()
    git(canonical, "init")
    git(canonical, "config", "user.email", "test@example.invalid")
    git(canonical, "config", "user.name", "Test")
    (canonical / "existing.txt").write_text("old\n", encoding="utf-8")
    (canonical / "delete.txt").write_text("delete-me\n", encoding="utf-8")
    git(canonical, "add", "existing.txt", "delete.txt")
    git(canonical, "commit", "-m", "baseline")
    source_head = git(canonical, "rev-parse", "HEAD")

    subprocess.run(
        ["git", "clone", str(canonical), str(candidate)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    (candidate / "existing.txt").write_text("new\n", encoding="utf-8")
    (candidate / "new.txt").write_text("created\n", encoding="utf-8")
    (candidate / "delete.txt").unlink()
    return canonical, candidate, source_head


def contract() -> dict:
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
        "required_pre_promotion_checks": sorted(
            promotion.REQUIRED_PRE_PROMOTION_CHECKS
        ),
    }


def origin() -> dict:
    return {
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


def handoff(changed_paths: list[str]) -> dict:
    return {
        "attempt_id": "cf10-u180j-a020",
        "status": "PASS",
        "handoff_manifest_sha256": "a" * 64,
        "changed_paths": changed_paths,
        "resume_coordinates": {
            "attempt_id": "cf10-u180j-a020",
            "handoff_manifest_sha256": "a" * 64,
            "source_state_fingerprint": "b" * 64,
            "lifecycle_roadmap_cursor": {"event_sequence": 1},
        },
    }


def work_front(changed_paths: list[str]) -> dict:
    return {
        "work_front_id": "wf-test",
        "scope": changed_paths,
    }


def test_plan_supports_modify_create_delete(tmp_path: Path) -> None:
    canonical, candidate, source_head = fixture_repo(tmp_path)
    changed = ["delete.txt", "existing.txt", "new.txt"]

    plan = promotion.build_candidate_promotion_plan(
        root=canonical,
        candidate_root=candidate,
        source_head=source_head,
        attempt_id="cf10-u180j-a020",
        changed_paths=changed,
        work_front=work_front(changed),
        origin_handoff_manifest=origin(),
        handoff_result=handoff(changed),
        expected_profile_ref="light-maintenance@r1",
        expected_procedure_id="governed_canonical_mutation",
        operator_review=True,
        contract=contract(),
    )

    operations = {row["path"]: row["operation"] for row in plan["operations"]}
    assert operations == {
        "delete.txt": "DELETE",
        "existing.txt": "MODIFY",
        "new.txt": "CREATE",
    }
    assert plan["canonical_continuity_fingerprint_compared_to_handoff_composite"] is False


def test_operator_review_is_required(tmp_path: Path) -> None:
    canonical, candidate, source_head = fixture_repo(tmp_path)
    changed = ["existing.txt"]

    with pytest.raises(promotion.CandidatePromotionError, match="operator review"):
        promotion.build_candidate_promotion_plan(
            root=canonical,
            candidate_root=candidate,
            source_head=source_head,
            attempt_id="cf10-u180j-a020",
            changed_paths=changed,
            work_front=work_front(changed),
            origin_handoff_manifest=origin(),
            handoff_result=handoff(changed),
            expected_profile_ref="light-maintenance@r1",
            expected_procedure_id="governed_canonical_mutation",
            operator_review=False,
            contract=contract(),
        )


def test_target_freshness_fails_closed(tmp_path: Path) -> None:
    canonical, candidate, source_head = fixture_repo(tmp_path)
    (canonical / "existing.txt").write_text("drift\n", encoding="utf-8")
    changed = ["existing.txt"]

    with pytest.raises(
        promotion.CandidatePromotionError,
        match="TARGET_FRESHNESS_DRIFT",
    ):
        promotion.build_candidate_promotion_plan(
            root=canonical,
            candidate_root=candidate,
            source_head=source_head,
            attempt_id="cf10-u180j-a020",
            changed_paths=changed,
            work_front=work_front(changed),
            origin_handoff_manifest=origin(),
            handoff_result=handoff(changed),
            expected_profile_ref="light-maintenance@r1",
            expected_procedure_id="governed_canonical_mutation",
            operator_review=True,
            contract=contract(),
        )


def test_apply_is_exact_and_never_stages(tmp_path: Path) -> None:
    canonical, candidate, source_head = fixture_repo(tmp_path)
    changed = ["delete.txt", "existing.txt", "new.txt"]
    plan = promotion.build_candidate_promotion_plan(
        root=canonical,
        candidate_root=candidate,
        source_head=source_head,
        attempt_id="cf10-u180j-a020",
        changed_paths=changed,
        work_front=work_front(changed),
        origin_handoff_manifest=origin(),
        handoff_result=handoff(changed),
        expected_profile_ref="light-maintenance@r1",
        expected_procedure_id="governed_canonical_mutation",
        operator_review=True,
        contract=contract(),
    )

    result = promotion.apply_candidate_promotion(
        plan=plan,
        root=canonical,
        candidate_root=candidate,
        recovery_root=tmp_path / "recovery",
        post_apply_validator=lambda paths: {
            "result": "PASS",
            "paths": paths,
        },
    )

    assert (canonical / "existing.txt").read_text() == "new\n"
    assert (canonical / "new.txt").read_text() == "created\n"
    assert not (canonical / "delete.txt").exists()
    assert result["candidate_promoted"] is True
    assert result["staging_performed"] is False
    assert git(canonical, "diff", "--cached", "--name-only") == ""




def test_mid_apply_failure_rolls_back_earlier_target(tmp_path: Path) -> None:
    canonical, candidate, source_head = fixture_repo(tmp_path)
    changed = ["existing.txt", "new.txt"]

    plan = promotion.build_candidate_promotion_plan(
        root=canonical,
        candidate_root=candidate,
        source_head=source_head,
        attempt_id="cf10-u180j-a020",
        changed_paths=changed,
        work_front=work_front(changed),
        origin_handoff_manifest=origin(),
        handoff_result=handoff(changed),
        expected_profile_ref="light-maintenance@r1",
        expected_procedure_id="governed_canonical_mutation",
        operator_review=True,
        contract=contract(),
    )

    # Force a failure after the first sorted path (existing.txt) has already
    # been modified. The runtime must restore that earlier mutation.
    (candidate / "new.txt").unlink()

    with pytest.raises(
        promotion.CandidatePromotionError,
        match="candidate file missing during apply: new.txt",
    ):
        promotion.apply_candidate_promotion(
            plan=plan,
            root=canonical,
            candidate_root=candidate,
            recovery_root=tmp_path / "recovery-mid-apply",
        )

    assert (canonical / "existing.txt").read_text() == "old\n"
    assert not (canonical / "new.txt").exists()
    assert (canonical / "delete.txt").read_text() == "delete-me\n"

def test_failed_post_apply_validation_rolls_back(tmp_path: Path) -> None:
    canonical, candidate, source_head = fixture_repo(tmp_path)
    changed = ["delete.txt", "existing.txt", "new.txt"]
    plan = promotion.build_candidate_promotion_plan(
        root=canonical,
        candidate_root=candidate,
        source_head=source_head,
        attempt_id="cf10-u180j-a020",
        changed_paths=changed,
        work_front=work_front(changed),
        origin_handoff_manifest=origin(),
        handoff_result=handoff(changed),
        expected_profile_ref="light-maintenance@r1",
        expected_procedure_id="governed_canonical_mutation",
        operator_review=True,
        contract=contract(),
    )

    with pytest.raises(
        promotion.CandidatePromotionError,
        match="post-apply canonical validation",
    ):
        promotion.apply_candidate_promotion(
            plan=plan,
            root=canonical,
            candidate_root=candidate,
            recovery_root=tmp_path / "recovery",
            post_apply_validator=lambda _paths: {"result": "FAIL"},
        )

    assert (canonical / "existing.txt").read_text() == "old\n"
    assert not (canonical / "new.txt").exists()
    assert (canonical / "delete.txt").read_text() == "delete-me\n"
