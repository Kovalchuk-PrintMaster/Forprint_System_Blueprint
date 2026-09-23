from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import yaml

from scripts.coordination import build_launch_request as gate

MODULE = "logistics_service"
PROMPT_ID = "prompt-v0-1"
FINGERPRINT = "a" * 64


def _manifest(*, fingerprint: str = FINGERPRINT) -> dict:
    return {
        "schema_version": "forprint_task_context_manifest_v0_1",
        "task_context_id": "ctx-test",
        "identity": {
            "module_id": MODULE,
            "prompt_id": PROMPT_ID,
            "context_fingerprint_sha256": fingerprint,
        },
        "repository_baseline": {
            "blueprint": {"head": "blueprint-head"},
            "module": {"head": "module-head"},
        },
        "task_prompt": {"sha256": "prompt-sha"},
        "prompt_contract": {"sha256": "contract-sha"},
        "acceptance_oracle": {"sha256": "oracle-sha"},
        "module_self_knowledge": {
            "fresh_context_state": "PASS",
            "unclassified_dirty_paths": [],
        },
    }


def _archive(path: Path, manifest: dict) -> Path:
    with zipfile.ZipFile(path, "w") as payload:
        payload.writestr(
            "TASK_CONTEXT_MANIFEST.yaml",
            yaml.safe_dump(manifest, sort_keys=False),
        )
    return path


def _dependency(path: Path, *, status: str = "READY") -> Path:
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "forprint_dependency_readiness_snapshot_v0_1",
                "module_id": MODULE,
                "prompt_id": PROMPT_ID,
                "context_fingerprint_sha256": FINGERPRINT,
                "status": status,
                "blocking_dependencies": [] if status == "READY" else ["x"],
                "evidence": ["fixture"],
                "authority": "TEST_FIXTURE",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def test_ready_dependency_reaches_awaiting_operator_approval(
    tmp_path: Path,
    monkeypatch,
) -> None:
    archived = _manifest()
    archive = _archive(tmp_path / "context.zip", archived)
    dependency = _dependency(tmp_path / "dependency.yaml")
    monkeypatch.setattr(
        gate,
        "_recompile_current_task_context",
        lambda **_: archived,
    )

    result = gate.build_launch_request(
        root=tmp_path,
        module_root=tmp_path,
        task_context_archive=archive,
        dependency_readiness_path=dependency,
    )

    assert result.state == gate.STATE_AWAITING_APPROVAL
    assert result.blocker_codes == ()
    assert result.document["operator_approval"]["decision"] == "NOT_DECIDED"
    assert result.document["execution_boundaries"]["worker_dispatch_allowed"] is False
    assert result.document["execution_boundaries"]["prompt_claim_allowed"] is False


def test_missing_dependency_readiness_blocks_without_approval(
    tmp_path: Path,
    monkeypatch,
) -> None:
    archived = _manifest()
    archive = _archive(tmp_path / "context.zip", archived)
    monkeypatch.setattr(
        gate,
        "_recompile_current_task_context",
        lambda **_: archived,
    )

    result = gate.build_launch_request(
        root=tmp_path,
        module_root=tmp_path,
        task_context_archive=archive,
    )

    assert result.state == gate.STATE_BLOCKED
    assert gate.BLOCKER_DEPENDENCY_MISSING in result.blocker_codes
    assert result.document["operator_approval"]["decision"] == "NOT_DECIDED"


def test_context_fingerprint_drift_blocks_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    archived = _manifest()
    current = _manifest(fingerprint="b" * 64)
    archive = _archive(tmp_path / "context.zip", archived)
    dependency = _dependency(tmp_path / "dependency.yaml")
    monkeypatch.setattr(
        gate,
        "_recompile_current_task_context",
        lambda **_: current,
    )

    result = gate.build_launch_request(
        root=tmp_path,
        module_root=tmp_path,
        task_context_archive=archive,
        dependency_readiness_path=dependency,
    )

    assert result.state == gate.STATE_BLOCKED
    assert gate.BLOCKER_CONTEXT_DRIFT in result.blocker_codes


def test_dependency_snapshot_is_bound_to_context_fingerprint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    archived = _manifest()
    archive = _archive(tmp_path / "context.zip", archived)
    bad = tmp_path / "dependency.yaml"
    bad.write_text(
        yaml.safe_dump(
            {
                "schema_version": "forprint_dependency_readiness_snapshot_v0_1",
                "module_id": MODULE,
                "prompt_id": PROMPT_ID,
                "context_fingerprint_sha256": "c" * 64,
                "status": "READY",
                "blocking_dependencies": [],
                "evidence": ["fixture"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        gate,
        "_recompile_current_task_context",
        lambda **_: archived,
    )

    result = gate.build_launch_request(
        root=tmp_path,
        module_root=tmp_path,
        task_context_archive=archive,
        dependency_readiness_path=bad,
    )

    assert result.state == gate.STATE_BLOCKED
    assert gate.BLOCKER_DEPENDENCY_INVALID in result.blocker_codes

def test_real_context_compiler_loader_registers_module_before_exec() -> None:
    root = Path(__file__).resolve().parents[2]

    compiler = gate._load_context_compiler(root)

    assert compiler.__name__ in sys.modules
    assert sys.modules[compiler.__name__] is compiler
    assert callable(compiler.build_task_context)

