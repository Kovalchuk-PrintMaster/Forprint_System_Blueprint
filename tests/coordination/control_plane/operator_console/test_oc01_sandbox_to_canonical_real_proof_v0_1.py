from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.operator_console.promotion_surface import (
    EXPLICIT_APPLY_TOKEN,
)
from scripts.coordination.control_plane.operator_console.sandbox_to_canonical_proof import (
    PROBE_RELATIVE,
    SandboxToCanonicalProofError,
    run_sandbox_to_canonical_real_proof,
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
        "schema_version": "forprint_worker_candidate_promotion_contract_v0_1",
        "contract_id": "worker_candidate_promotion_contract",
        "revision": "0.1.0",
        "status": "ACTIVE_CF10_PROMOTION_RUNTIME_V0_1",
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


def fixture_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "canonical"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "oc01@example.invalid")
    git(repo, "config", "user.name", "OC01 Test")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    contract = (
        repo
        / "coordination/standards/automation/"
        / "worker_candidate_promotion_contract_v0_1.yaml"
    )
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(
        yaml.safe_dump(
            promotion_contract(),
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "baseline")
    return repo.resolve(), git(repo, "rev-parse", "HEAD")


def test_real_proof_promotes_only_probe_without_git_publication(
    tmp_path: Path,
) -> None:
    repo, base = fixture_repo(tmp_path)
    before_head = git(repo, "rev-parse", "HEAD")
    before_staged = git(repo, "diff", "--cached", "--name-only")

    result = run_sandbox_to_canonical_real_proof(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        expected_base_head=base,
        explicit_authorization=EXPLICIT_APPLY_TOKEN,
    )

    probe = repo / PROBE_RELATIVE
    assert result["state"] == "PASS"
    assert probe.is_file()
    assert result["checkpoint"]["changed_paths"] == [PROBE_RELATIVE]
    assert result["sealed_result"]["recommended_canonical_write_set"] == [
        PROBE_RELATIVE
    ]
    assert result["promotion_apply"]["candidate_promoted"] is True
    assert result["promotion_apply"]["canonical_write_performed"] is True
    assert result["promotion_apply"]["staging_performed"] is False
    assert result["promotion_apply"]["commit_performed"] is False
    assert result["promotion_apply"]["push_performed"] is False
    assert result["promotion_apply"]["merge_performed"] is False
    assert result["promotion_apply"]["release_performed"] is False
    assert git(repo, "rev-parse", "HEAD") == before_head
    assert git(repo, "diff", "--cached", "--name-only") == before_staged


def test_real_proof_requires_explicit_promotion_token(tmp_path: Path) -> None:
    repo, base = fixture_repo(tmp_path)

    with pytest.raises(
        SandboxToCanonicalProofError,
        match="authorization",
    ):
        run_sandbox_to_canonical_real_proof(
            canonical_repo=repo,
            runtime_root=tmp_path / "runtime",
            expected_base_head=base,
            explicit_authorization="NO",
        )

    assert not (repo / PROBE_RELATIVE).exists()
    assert git(repo, "rev-parse", "HEAD") == base
    assert git(repo, "diff", "--cached", "--name-only") == ""


def test_real_proof_runtime_must_be_outside_canonical(tmp_path: Path) -> None:
    repo, base = fixture_repo(tmp_path)
    with pytest.raises(
        SandboxToCanonicalProofError,
        match="outside canonical",
    ):
        run_sandbox_to_canonical_real_proof(
            canonical_repo=repo,
            runtime_root=repo / "runtime",
            expected_base_head=base,
            explicit_authorization=EXPLICIT_APPLY_TOKEN,
        )


def test_real_proof_replay_is_rejected(tmp_path: Path) -> None:
    repo, base = fixture_repo(tmp_path)
    runtime = tmp_path / "runtime"
    run_sandbox_to_canonical_real_proof(
        canonical_repo=repo,
        runtime_root=runtime,
        expected_base_head=base,
        explicit_authorization=EXPLICIT_APPLY_TOKEN,
    )

    with pytest.raises(
        SandboxToCanonicalProofError,
        match="runtime_root already exists|proof target must be absent",
    ):
        run_sandbox_to_canonical_real_proof(
            canonical_repo=repo,
            runtime_root=runtime,
            expected_base_head=base,
            explicit_authorization=EXPLICIT_APPLY_TOKEN,
        )


def test_real_proof_preserves_preexisting_dirty_bytes(tmp_path: Path) -> None:
    repo, base = fixture_repo(tmp_path)
    dirty = repo / "tracked.txt"
    dirty.write_text("preexisting dirty\n", encoding="utf-8")
    before = dirty.read_bytes()

    result = run_sandbox_to_canonical_real_proof(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        expected_base_head=base,
        explicit_authorization=EXPLICIT_APPLY_TOKEN,
    )

    assert dirty.read_bytes() == before
    assert result["canonical_invariants"][
        "preexisting_dirty_path_bytes_unchanged"
    ] is True


def test_real_proof_package_keeps_completion_boundary_partial(
    tmp_path: Path,
) -> None:
    repo, base = fixture_repo(tmp_path)
    result = run_sandbox_to_canonical_real_proof(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        expected_base_head=base,
        explicit_authorization=EXPLICIT_APPLY_TOKEN,
    )

    assert result["completion_boundary"]["mini8_real_proof"] == "PASS"
    assert result["completion_boundary"]["after_publication"] == (
        "USEFUL_MINIMUM_PROVEN_PARTIAL_OC01"
    )
    assert result["completion_boundary"]["must_not_claim"] == "OC01_FULL_COMPLETE"
    assert all(
        result["authority"][key] is False
        for key in (
            "console_is_state_authority",
            "new_execution_truth_created",
            "new_lease_authority_created",
            "sandbox_direct_canonical_write_authority",
            "commit_authority",
            "push_authority",
            "merge_authority",
            "release_authority",
        )
    )
