from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.workspace import (
    build_workspace_layout,
    workspace_manifest,
)

ROOT = Path(__file__).resolve().parents[4]


def test_workspace_layout_is_partitioned() -> None:
    layout = build_workspace_layout(
        runtime_root="/srv/software_development/forprint-worker-runtime",
        canonical_repo=ROOT,
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-001",
    )
    assert layout.attempt_root.as_posix().endswith(
        "/forprint_system_blueprint/worker-01/attempt-001"
    )
    assert layout.workspace_repo == layout.attempt_root / "workspace/repo"
    assert layout.candidate == layout.attempt_root / "artifacts/candidate"


def test_workspace_layout_does_not_mutate_filesystem(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    layout = build_workspace_layout(
        runtime_root=runtime,
        canonical_repo=canonical,
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-001",
    )
    assert not layout.attempt_root.exists()


def test_workspace_cannot_live_inside_canonical_repository(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    with pytest.raises(ValueError, match="isolated"):
        build_workspace_layout(
            runtime_root=canonical / "runtime",
            canonical_repo=canonical,
            module_id="forprint_system_blueprint",
            worker_id="worker-01",
            attempt_id="attempt-001",
        )


def test_workspace_manifest_is_non_executing(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    layout = build_workspace_layout(
        runtime_root=tmp_path / "runtime",
        canonical_repo=canonical,
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-001",
    )
    manifest = workspace_manifest(
        layout=layout,
        canonical_repo=canonical,
        source_head="abc123",
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id="attempt-001",
    )
    assert manifest["canonical_write_allowed"] is False
    assert manifest["provisioning_performed"] is False
    assert manifest["worker_launch_performed"] is False


def test_promotion_contract_is_operator_controlled() -> None:
    contract = yaml.safe_load(
        (
            ROOT
            / "coordination/standards/automation/"
            "worker_candidate_promotion_contract_v0_1.yaml"
        ).read_text(encoding="utf-8")
    )
    authority = contract["authority_semantics"]
    assert authority["worker_can_promote"] is False
    assert authority["worker_can_commit_canonical"] is False
    assert authority["worker_can_push"] is False
    assert authority["worker_can_merge"] is False
    assert authority["worker_can_release"] is False
    assert authority["worker_can_auto_accept"] is False
    assert authority["promotion_authority"] == "OPERATOR_CONTROLLED_CF10"
