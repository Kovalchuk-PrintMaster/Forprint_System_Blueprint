from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.coordination.control_plane.workspace import (
    WorkspaceProvisionError,
    capture_worker_baseline,
    derive_worker_delta,
    derive_worker_delta_from_manifest,
    load_workspace_plan_from_manifest,
    plan_workspace,
    provision_workspace,
    verify_workspace_equivalence,
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


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "canonical"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.email", "cf10@example.invalid")
    git(repo, "config", "user.name", "CF10 Test")
    (repo / "modified.txt").write_text("base\n", encoding="utf-8")
    (repo / "deleted.txt").write_text("delete-me\n", encoding="utf-8")
    (repo / "keep.txt").write_text("keep\n", encoding="utf-8")
    (repo / "target_a.py").write_text("a = 1\n", encoding="utf-8")
    (repo / "target_b.py").write_text("b = 1\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "baseline")
    return repo


def supplied_state(repo: Path, paths: list[str]) -> dict:
    return {
        "git_head": git(repo, "rev-parse", "HEAD"),
        "git_branch": git(repo, "branch", "--show-current") or None,
        "fingerprint_sha256": "f" * 64,
        "durable_dirty_paths": paths,
    }


def test_provision_materializes_modified_untracked_deleted_and_symlink(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    (repo / "modified.txt").write_text("changed\n", encoding="utf-8")
    (repo / "deleted.txt").unlink()
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    os.symlink("keep.txt", repo / "link.txt")
    runtime_noise = repo / "tmp/runtime.log"
    runtime_noise.parent.mkdir()
    runtime_noise.write_text("noise\n", encoding="utf-8")

    paths = ["modified.txt", "deleted.txt", "new.txt", "link.txt"]
    plan = plan_workspace(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-001",
        source_state=supplied_state(repo, paths),
    )
    manifest = provision_workspace(plan)
    evidence = verify_workspace_equivalence(plan)

    workspace = plan.layout.workspace_repo
    assert manifest["provisioning_performed"] is True
    assert manifest["worker_launch_performed"] is False
    assert evidence["equivalent"] is True
    assert evidence["branch_identity_compared"] is False
    assert (workspace / "modified.txt").read_text(encoding="utf-8") == "changed\n"
    assert not (workspace / "deleted.txt").exists()
    assert (workspace / "new.txt").read_text(encoding="utf-8") == "new\n"
    assert (workspace / "link.txt").is_symlink()
    assert os.readlink(workspace / "link.txt") == "keep.txt"
    assert not (workspace / "tmp/runtime.log").exists()


def test_plan_is_no_write(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "modified.txt").write_text("changed\n", encoding="utf-8")
    plan = plan_workspace(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-plan",
        source_state=supplied_state(repo, ["modified.txt"]),
    )
    assert not plan.layout.attempt_root.exists()


def test_workspace_is_independent_git_repository(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    plan = plan_workspace(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-002",
        source_state=supplied_state(repo, ["new.txt"]),
    )
    provision_workspace(plan)

    canonical_git = git(repo, "rev-parse", "--git-dir")
    workspace_git = git(plan.layout.workspace_repo, "rev-parse", "--git-dir")
    assert canonical_git
    assert workspace_git
    assert (plan.layout.workspace_repo / ".git").exists()
    assert plan.layout.workspace_repo != repo


def test_unsafe_durable_path_is_rejected(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    with pytest.raises(WorkspaceProvisionError, match="escapes repository"):
        plan_workspace(
            canonical_repo=repo,
            runtime_root=tmp_path / "runtime",
            module_id="forprint_system_blueprint",
            worker_id="worker-01",
            attempt_id="attempt-bad",
            source_state=supplied_state(repo, ["../escape.txt"]),
        )


def test_runtime_root_inside_canonical_is_rejected(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    with pytest.raises(ValueError, match="isolated"):
        plan_workspace(
            canonical_repo=repo,
            runtime_root=repo / "runtime",
            module_id="forprint_system_blueprint",
            worker_id="worker-01",
            attempt_id="attempt-bad-root",
            source_state=supplied_state(repo, []),
        )


def test_worker_delta_excludes_inherited_dirty_baseline(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    (repo / "modified.txt").write_text(
        "inherited-dirty\n", encoding="utf-8"
    )
    plan = plan_workspace(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-worker-delta",
        source_state=supplied_state(repo, ["modified.txt"]),
    )
    provision_workspace(plan)
    baseline = capture_worker_baseline(plan)

    before = derive_worker_delta(plan)
    assert before["changed_paths"] == []
    assert "modified.txt" in before["inherited_dirty_paths"]
    assert Path(baseline["evidence_path"]).is_file()

    workspace = plan.layout.workspace_repo
    (workspace / "target_a.py").write_text("a = 2\n", encoding="utf-8")
    (workspace / "target_b.py").write_text("b = 2\n", encoding="utf-8")

    delta = derive_worker_delta(plan)
    assert delta["worker_delta_exact"] is True
    assert delta["changed_paths"] == ["target_a.py", "target_b.py"]
    assert "modified.txt" not in delta["changed_paths"]


def test_worker_delta_detects_change_inside_inherited_dirty_path(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    (repo / "modified.txt").write_text(
        "inherited-dirty\n", encoding="utf-8"
    )
    plan = plan_workspace(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-worker-dirty-edit",
        source_state=supplied_state(repo, ["modified.txt"]),
    )
    provision_workspace(plan)
    capture_worker_baseline(plan)

    workspace = plan.layout.workspace_repo
    (workspace / "modified.txt").write_text(
        "worker-changed-inherited-dirty\n", encoding="utf-8"
    )
    delta = derive_worker_delta(plan)
    assert delta["changed_paths"] == ["modified.txt"]


def test_worker_delta_fails_closed_when_workspace_head_changes(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    plan = plan_workspace(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-worker-head-drift",
        source_state=supplied_state(repo, []),
    )
    provision_workspace(plan)
    capture_worker_baseline(plan)

    workspace = plan.layout.workspace_repo
    git(workspace, "config", "user.email", "worker@example.invalid")
    git(workspace, "config", "user.name", "Worker Test")
    (workspace / "target_a.py").write_text("a = 3\n", encoding="utf-8")
    git(workspace, "add", "target_a.py")
    git(workspace, "commit", "-m", "worker must not hide delta in commit")

    with pytest.raises(
        WorkspaceProvisionError,
        match="HEAD changed after worker baseline",
    ):
        derive_worker_delta(plan)


def test_worker_baseline_cannot_be_recaptured_after_mutation(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    plan = plan_workspace(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-baseline-immutable",
        source_state=supplied_state(repo, []),
    )
    provision_workspace(plan)
    baseline = capture_worker_baseline(plan)

    evidence_path = Path(baseline["evidence_path"])
    evidence_before = evidence_path.read_bytes()

    workspace = plan.layout.workspace_repo
    (workspace / "target_a.py").write_text(
        "a = 99\n",
        encoding="utf-8",
    )

    with pytest.raises(
        WorkspaceProvisionError,
        match="recapture is forbidden",
    ):
        capture_worker_baseline(plan)

    assert evidence_path.read_bytes() == evidence_before
    delta = derive_worker_delta(plan)
    assert delta["changed_paths"] == ["target_a.py"]


def test_workspace_plan_reloads_from_manifest_and_derives_delta(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    (repo / "modified.txt").write_text(
        "inherited-dirty\n",
        encoding="utf-8",
    )
    plan = plan_workspace(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-manifest-delta",
        source_state=supplied_state(repo, ["modified.txt"]),
    )
    provision_workspace(plan)
    capture_worker_baseline(plan)

    workspace = plan.layout.workspace_repo
    (workspace / "target_a.py").write_text(
        "a = 42\n",
        encoding="utf-8",
    )

    reloaded = load_workspace_plan_from_manifest(
        plan.layout.manifest
    )
    assert reloaded.layout.workspace_repo == workspace
    assert reloaded.source_head == plan.source_head
    assert reloaded.durable_dirty_paths == ("modified.txt",)

    delta = derive_worker_delta_from_manifest(
        plan.layout.manifest
    )
    assert delta["attempt_id"] == "attempt-manifest-delta"
    assert delta["workspace_repo"] == str(workspace)
    assert delta["changed_paths"] == ["target_a.py"]
    assert delta["worker_delta_exact"] is True
    assert delta["workspace_manifest"] == str(
        plan.layout.manifest.resolve()
    )


def test_workspace_manifest_loader_rejects_path_binding_tamper(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    plan = plan_workspace(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-manifest-tamper",
        source_state=supplied_state(repo, []),
    )
    provision_workspace(plan)

    yaml = __import__("yaml")
    manifest = yaml.safe_load(
        plan.layout.manifest.read_text(encoding="utf-8")
    )
    manifest["workspace_repo"] = str(
        tmp_path / "other" / "workspace" / "repo"
    )
    plan.layout.manifest.write_text(
        yaml.safe_dump(
            manifest,
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        WorkspaceProvisionError,
        match="path binding mismatch: workspace_repo",
    ):
        load_workspace_plan_from_manifest(
            plan.layout.manifest
        )
