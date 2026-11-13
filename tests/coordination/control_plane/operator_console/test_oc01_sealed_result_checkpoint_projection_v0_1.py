from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.operator_console.assistant_dev_sandbox import (
    create_sandbox,
)
from scripts.coordination.control_plane.operator_console.sealed_result import (
    PAUSE_RESUME_STATE,
    SealedResultError,
    build_sealed_result_package,
    sealed_result_status,
    write_checkpoint_projection,
    write_sealed_result_package,
)
from scripts.coordination.control_plane.operator_console.session_projection import (
    build_session_projection,
)


def git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return cp.stdout.strip()


def canonical_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "canonical"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "oc01@example.invalid")
    git(repo, "config", "user.name", "OC01 Test")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(repo, "add", "tracked.txt")
    git(repo, "commit", "-q", "-m", "baseline")
    return repo.resolve()


def session() -> dict:
    return build_session_projection(
        launch_request={
            "identity": {
                "module_id": "forprint_system_blueprint",
                "prompt_id": "oc01-mini4-test",
            }
        },
        worker_invocation={
            "attempt_id": "sandbox-attempt",
            "worker_id": "operator-assistant",
            "workspace_repo": "/tmp/not-yet-bound",
        },
        actor_type="operator_assistant",
        actor_id="assistant-01",
    )


def create(tmp_path: Path) -> tuple[Path, dict]:
    repo = canonical_repo(tmp_path)
    result = create_sandbox(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="operator-assistant",
        attempt_id="sandbox-attempt",
        expected_base_head=git(repo, "rev-parse", "HEAD"),
        session_projection=session(),
    )
    return repo, result


def test_checkpoint_reuses_shared_exact_worker_delta(tmp_path: Path) -> None:
    _, created = create(tmp_path)
    manifest = Path(created["sandbox"]["manifest"])
    workspace = Path(created["sandbox"]["workspace_repo"])
    (workspace / "tracked.txt").write_text("sandbox change\n", encoding="utf-8")

    checkpoint = write_checkpoint_projection(
        manifest_path=manifest,
        session_projection=session(),
    )

    assert checkpoint["worker_delta"]["worker_delta_exact"] is True
    assert checkpoint["worker_delta"]["changed_paths"] == ["tracked.txt"]
    assert checkpoint["recommended_canonical_write_set"] == ["tracked.txt"]
    assert checkpoint["authority"]["pause_resume_authority"] is False
    assert checkpoint["actions_performed"]["canonical_write"] is False


def test_checkpoint_projects_resume_evidence_without_authority(
    tmp_path: Path,
) -> None:
    _, created = create(tmp_path)
    manifest = Path(created["sandbox"]["manifest"])
    resume_path = manifest.parent / "evidence" / "resume_projection_source.yaml"
    resume_path.write_text(
        yaml.safe_dump(
            {
                "resume_coordinates": {
                    "attempt_id": "sandbox-attempt",
                    "latest_completed_node": "sandbox-edit",
                },
                "freshness_resume": {"valid": True, "errors": []},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    checkpoint = write_checkpoint_projection(
        manifest_path=manifest,
        session_projection=session(),
        resume_evidence_path=resume_path,
    )
    assert checkpoint["resume_projection"]["resume_coordinates"]["attempt_id"] == (
        "sandbox-attempt"
    )
    assert checkpoint["resume_projection"]["pause_resume_authority"] is False
    assert checkpoint["dependency_state"]["canonical_pause_resume"] == (
        PAUSE_RESUME_STATE
    )


def test_resume_evidence_outside_attempt_is_rejected(tmp_path: Path) -> None:
    _, created = create(tmp_path)
    manifest = Path(created["sandbox"]["manifest"])
    outside = tmp_path / "outside.yaml"
    outside.write_text("resume_coordinates: {}\n", encoding="utf-8")

    with pytest.raises(SealedResultError, match="bound attempt"):
        write_checkpoint_projection(
            manifest_path=manifest,
            session_projection=session(),
            resume_evidence_path=outside,
        )


def test_sealed_result_is_deterministic_and_immutable(tmp_path: Path) -> None:
    _, created = create(tmp_path)
    manifest = Path(created["sandbox"]["manifest"])
    workspace = Path(created["sandbox"]["workspace_repo"])
    (workspace / "tracked.txt").write_text("sandbox change\n", encoding="utf-8")

    write_checkpoint_projection(
        manifest_path=manifest,
        session_projection=session(),
    )

    first_payload = build_sealed_result_package(
        manifest_path=manifest,
        session_projection=session(),
        validation_evidence=["pytest:PASS", "make-check:PASS"],
        artifacts=["artifacts/candidate/output.txt"],
        open_issues=["local commits remain CF10 dependency"],
    )
    second_payload = build_sealed_result_package(
        manifest_path=manifest,
        session_projection=session(),
        validation_evidence=["make-check:PASS", "pytest:PASS"],
        artifacts=["artifacts/candidate/output.txt"],
        open_issues=["local commits remain CF10 dependency"],
    )
    assert first_payload == second_payload
    assert len(first_payload["package_sha256"]) == 64
    assert first_payload["changed_paths"] == ["tracked.txt"]

    written = write_sealed_result_package(
        manifest_path=manifest,
        session_projection=session(),
        validation_evidence=["pytest:PASS", "make-check:PASS"],
        artifacts=["artifacts/candidate/output.txt"],
        open_issues=["local commits remain CF10 dependency"],
    )
    assert Path(written["result_path"]).is_file()

    with pytest.raises(SealedResultError, match="overwrite"):
        write_sealed_result_package(
            manifest_path=manifest,
            session_projection=session(),
            validation_evidence=["pytest:PASS"],
        )


def test_seal_requires_validation_evidence(tmp_path: Path) -> None:
    _, created = create(tmp_path)
    manifest = Path(created["sandbox"]["manifest"])
    write_checkpoint_projection(
        manifest_path=manifest,
        session_projection=session(),
    )
    with pytest.raises(SealedResultError, match="validation_evidence"):
        build_sealed_result_package(
            manifest_path=manifest,
            session_projection=session(),
            validation_evidence=[],
        )


def test_local_commit_remains_fail_closed(tmp_path: Path) -> None:
    _, created = create(tmp_path)
    manifest = Path(created["sandbox"]["manifest"])
    workspace = Path(created["sandbox"]["workspace_repo"])
    git(workspace, "config", "user.email", "oc01@example.invalid")
    git(workspace, "config", "user.name", "OC01 Test")
    (workspace / "tracked.txt").write_text("local commit\n", encoding="utf-8")
    git(workspace, "add", "tracked.txt")
    git(workspace, "commit", "-q", "-m", "local sandbox commit")
    with pytest.raises(SealedResultError, match="HEAD"):
        write_checkpoint_projection(
            manifest_path=manifest,
            session_projection=session(),
        )


def test_sealed_result_does_not_mutate_canonical_repo(tmp_path: Path) -> None:
    repo, created = create(tmp_path)
    manifest = Path(created["sandbox"]["manifest"])
    workspace = Path(created["sandbox"]["workspace_repo"])
    before = git(repo, "status", "--porcelain=v1")
    (workspace / "tracked.txt").write_text("sandbox only\n", encoding="utf-8")
    write_checkpoint_projection(
        manifest_path=manifest,
        session_projection=session(),
    )
    write_sealed_result_package(
        manifest_path=manifest,
        session_projection=session(),
        validation_evidence=["pytest:PASS"],
    )
    assert git(repo, "status", "--porcelain=v1") == before
    assert (repo / "tracked.txt").read_text(encoding="utf-8") == "base\n"


def test_status_reports_checkpoint_and_sealed_result(tmp_path: Path) -> None:
    _, created = create(tmp_path)
    manifest = Path(created["sandbox"]["manifest"])
    initial = sealed_result_status(manifest_path=manifest)
    assert initial["checkpoint"]["exists"] is False
    assert initial["sealed_result"]["exists"] is False

    write_checkpoint_projection(
        manifest_path=manifest,
        session_projection=session(),
    )
    write_sealed_result_package(
        manifest_path=manifest,
        session_projection=session(),
        validation_evidence=["pytest:PASS"],
    )
    final = sealed_result_status(manifest_path=manifest)
    assert final["checkpoint"]["exists"] is True
    assert final["sealed_result"]["exists"] is True
    assert final["authority"]["canonical_write_authority"] is False
    assert final["canonical_promotion"] == "NEXT_SLICE_OC01_MINI_5"
