from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts/coordination/control_plane/dispatch_intent.py"

spec = importlib.util.spec_from_file_location(
    "_cf10_post_worker_result_collection_test",
    SOURCE,
)
assert spec is not None and spec.loader is not None
dispatch = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dispatch
spec.loader.exec_module(dispatch)


def result_text(attempt_id: str, *, schema: str | None = None) -> str:
    schema_value = (
        "forprint_assistant_handoff_v2_result_v0_1"
        if schema is None
        else schema
    )
    return "\n".join(
        [
            f"schema_version: {schema_value}",
            f"attempt_id: {attempt_id}",
            "changed_paths:",
            "  - a.txt",
            "",
        ]
    )


def setup_attempt(tmp_path: Path, attempt_id: str = "cf10-u180j-a004"):
    workspace = (
        tmp_path
        / "forprint_system_blueprint"
        / "worker-01"
        / attempt_id
        / "workspace"
        / "repo"
    )
    workspace.mkdir(parents=True)
    result_dir = workspace.parent.parent / "result"
    result_dir.mkdir()
    decision = {
        "binding": {
            "attempt_id": attempt_id,
            "workspace_repo": str(workspace),
        }
    }
    return workspace, result_dir, decision


def raises_value_error(callable_obj, expected: str) -> None:
    try:
        callable_obj()
    except ValueError as exc:
        assert expected in str(exc)
    else:
        raise AssertionError(f"expected ValueError containing: {expected}")


def test_collects_handoff_v2_result_from_bound_result_directory(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    _, result_dir, decision = setup_attempt(tmp_path, attempt_id)
    artifact = result_dir / "cf10_worker_result_v0_1.yaml"
    artifact.write_text(result_text(attempt_id), encoding="utf-8")

    result = dispatch.collect_cf10_post_worker_result_artifact(
        explicit_dispatch_decision=decision,
        result_artifact_path=artifact,
    )

    assert result["schema_version"] == (
        "forprint_assistant_handoff_v2_result_v0_1"
    )
    assert result["attempt_id"] == attempt_id
    assert result["changed_paths"] == ["a.txt"]


def test_relative_result_name_is_resolved_inside_bound_result_directory(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    _, result_dir, decision = setup_attempt(tmp_path, attempt_id)
    artifact = result_dir / "worker_result.yaml"
    artifact.write_text(result_text(attempt_id), encoding="utf-8")

    result = dispatch.collect_cf10_post_worker_result_artifact(
        explicit_dispatch_decision=decision,
        result_artifact_path="worker_result.yaml",
    )
    assert result["attempt_id"] == attempt_id


def test_result_artifact_outside_bound_result_directory_is_rejected(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    _, _, decision = setup_attempt(tmp_path, attempt_id)
    outside = tmp_path / "outside.yaml"
    outside.write_text(result_text(attempt_id), encoding="utf-8")

    raises_value_error(
        lambda: dispatch.collect_cf10_post_worker_result_artifact(
            explicit_dispatch_decision=decision,
            result_artifact_path=outside,
        ),
        "escapes bound attempt result directory",
    )


def test_result_artifact_attempt_mismatch_is_rejected(
    tmp_path: Path,
) -> None:
    _, result_dir, decision = setup_attempt(tmp_path, "cf10-u180j-a004")
    artifact = result_dir / "worker_result.yaml"
    artifact.write_text(
        result_text("cf10-u180j-a999"),
        encoding="utf-8",
    )

    raises_value_error(
        lambda: dispatch.collect_cf10_post_worker_result_artifact(
            explicit_dispatch_decision=decision,
            result_artifact_path=artifact,
        ),
        "attempt_id does not match bound attempt",
    )


def test_result_artifact_schema_mismatch_is_rejected(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    _, result_dir, decision = setup_attempt(tmp_path, attempt_id)
    artifact = result_dir / "worker_result.yaml"
    artifact.write_text(
        result_text(attempt_id, schema="other_schema"),
        encoding="utf-8",
    )

    raises_value_error(
        lambda: dispatch.collect_cf10_post_worker_result_artifact(
            explicit_dispatch_decision=decision,
            result_artifact_path=artifact,
        ),
        "Handoff v2 schema mismatch",
    )


def test_result_artifact_symlink_is_rejected(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    _, result_dir, decision = setup_attempt(tmp_path, attempt_id)
    outside = tmp_path / "outside.yaml"
    outside.write_text(result_text(attempt_id), encoding="utf-8")
    link = result_dir / "worker_result.yaml"
    link.symlink_to(outside)

    raises_value_error(
        lambda: dispatch.collect_cf10_post_worker_result_artifact(
            explicit_dispatch_decision=decision,
            result_artifact_path=link,
        ),
        "cannot be a symlink",
    )


def test_finalize_result_artifact_delegates_to_existing_workspace_finalizer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt_id = "cf10-u180j-a004"
    workspace, result_dir, decision = setup_attempt(tmp_path, attempt_id)
    artifact = result_dir / "worker_result.yaml"
    artifact.write_text(result_text(attempt_id), encoding="utf-8")

    observed: dict = {}

    def fake_finalizer(**kwargs):
        observed.update(kwargs)
        return {"state": "PROOF_FINALIZER_CALLED"}

    monkeypatch.setattr(
        dispatch,
        "finalize_cf10_workspace_task_execution",
        fake_finalizer,
    )

    final = dispatch.finalize_cf10_workspace_result_artifact(
        root=ROOT,
        explicit_dispatch_decision=decision,
        result_artifact_path=artifact,
        origin_manifest={"handoff_manifest_sha256": "a" * 64},
        attempt_record={"attempt_id": attempt_id},
        attempt_number=1,
        worker_delta_loader=lambda path: {
            "attempt_id": attempt_id,
            "workspace_repo": str(workspace),
        },
    )

    assert final["state"] == "PROOF_FINALIZER_CALLED"
    assert observed["result"]["attempt_id"] == attempt_id
    assert observed["explicit_dispatch_decision"] is decision
    assert observed["worker_delta_loader"] is not None
