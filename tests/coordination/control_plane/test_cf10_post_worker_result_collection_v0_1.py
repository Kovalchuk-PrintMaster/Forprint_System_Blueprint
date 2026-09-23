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

def test_full_internal_pipeline_uses_real_isolated_workspace_delta(
    tmp_path: Path,
) -> None:
    import subprocess
    from types import SimpleNamespace

    import yaml

    from scripts.coordination.control_plane.workspace import (
        capture_worker_baseline,
        plan_workspace,
        provision_workspace,
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

    canonical = tmp_path / "canonical"
    canonical.mkdir()
    git(canonical, "init")
    git(canonical, "config", "user.email", "cf10-proof@example.invalid")
    git(canonical, "config", "user.name", "CF10 Proof")
    (canonical / "inherited.txt").write_text("base\n", encoding="utf-8")
    (canonical / "target.txt").write_text("target = 1\n", encoding="utf-8")
    git(canonical, "add", ".")
    git(canonical, "commit", "-m", "baseline")

    # Canonical inherited dirty state must not become worker delta.
    (canonical / "inherited.txt").write_text(
        "inherited-dirty\n",
        encoding="utf-8",
    )

    attempt_id = "cf10-u180j-proof-e2e"
    source_state = {
        "git_head": git(canonical, "rev-parse", "HEAD"),
        "git_branch": git(canonical, "branch", "--show-current") or None,
        "fingerprint_sha256": "f" * 64,
        "durable_dirty_paths": ["inherited.txt"],
    }
    plan = plan_workspace(
        canonical_repo=canonical,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="worker-01",
        attempt_id=attempt_id,
        source_state=source_state,
    )
    provision_workspace(plan)
    capture_worker_baseline(plan)

    workspace = plan.layout.workspace_repo
    (workspace / "target.txt").write_text(
        "target = 2\n",
        encoding="utf-8",
    )

    plan.layout.result.mkdir(parents=True, exist_ok=True)
    digest = "a" * 64
    result = {
        "schema_version": "forprint_assistant_handoff_v2_result_v0_1",
        "handoff_manifest_sha256": digest,
        "attempt_id": attempt_id,
        "status": "PASS",
        "changed_paths": ["target.txt"],
        "validation_evidence": [
            {"name": "synthetic-e2e-proof", "result": "PASS"}
        ],
        "self_repair_attempts": [],
        "resume_coordinates": {
            "attempt_id": attempt_id,
            "step": "return-result",
        },
        "unresolved_findings": [],
    }
    artifact = plan.layout.result / "worker_result.yaml"
    artifact.write_text(
        yaml.safe_dump(result, sort_keys=False),
        encoding="utf-8",
    )

    decision = {
        "schema_version": (
            "forprint_cf10_internal_explicit_dispatch_decision_v0_1"
        ),
        "binding": {
            "attempt_id": attempt_id,
            "worker_id": "worker-01",
            "workspace_repo": str(workspace),
        },
        "explicit_dispatch_decision_recorded": True,
        "worker_process_launch_allowed": True,
        "canonical_attempt_ledger_append_allowed": True,
        "external_dispatch_allowed": False,
        "release_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "foreign_repository_write_allowed": False,
        "automatic_accept_allowed": False,
    }

    def validate_result_for_return(
        root,
        manifest,
        supplied_result,
        *,
        max_self_repair_attempts=2,
    ):
        assert root == ROOT
        assert manifest["handoff_manifest_sha256"] == digest
        assert max_self_repair_attempts == 2
        return {
            "valid": True,
            "result": dict(supplied_result),
            "errors": [],
            "repair_attempt_count": 0,
            "freshness_resume": {"valid": True, "errors": []},
        }

    class Ledger:
        def __init__(self) -> None:
            self.rows: list[dict] = []

        def load_contract(self, root):
            assert root == ROOT
            return {"schema_version": "synthetic"}

        def validate_record_data(self, record, contract):
            assert contract["schema_version"] == "synthetic"
            return []

        def append_record(self, root, record, *, store_override=None):
            assert root == ROOT
            assert store_override is not None
            self.rows.append(dict(record))
            output = Path(store_override) / "proof.yaml"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                yaml.safe_dump(record, sort_keys=False),
                encoding="utf-8",
            )
            return output

    ledger = Ledger()
    attempt_record = {
        "attempt_id": attempt_id,
        "work_front_id": "wf-cf10-worker-delta-pipeline-completion-v0-1",
    }

    final = dispatch.finalize_cf10_workspace_result_artifact(
        root=ROOT,
        explicit_dispatch_decision=decision,
        result_artifact_path=artifact,
        origin_manifest={"handoff_manifest_sha256": digest},
        attempt_record=attempt_record,
        attempt_number=1,
        ledger_store_override=tmp_path / "ledger",
        telemetry_root_override=tmp_path / "telemetry",
        runtime_loader=lambda: SimpleNamespace(
            validate_result_for_return=validate_result_for_return,
        ),
        ledger_loader=lambda: ledger,
    )

    assert final["state"] == "ATTEMPT_RECORDED"
    assert final["canonical_attempt_record_written"] is True
    verification = final["worker_delta_verification"]
    assert verification["valid"] is True
    assert verification["match"] is True
    assert verification["reported_changed_paths"] == ["target.txt"]
    assert verification["derived_changed_paths"] == ["target.txt"]
    assert len(ledger.rows) == 1

    # The worker changed only the isolated workspace.
    assert (canonical / "target.txt").read_text(encoding="utf-8") == (
        "target = 1\n"
    )
    assert (canonical / "inherited.txt").read_text(encoding="utf-8") == (
        "inherited-dirty\n"
    )
