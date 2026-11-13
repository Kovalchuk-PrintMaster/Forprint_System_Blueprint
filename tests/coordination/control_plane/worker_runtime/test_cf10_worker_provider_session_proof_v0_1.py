from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[4]
MODULE_NAME = (
    "scripts.coordination.control_plane.worker_runtime.provider_session_proof"
)
MAKEFILE = ROOT / "Makefile"

MODEL_TOOL_ID = "ForPrintValidation-run_validation_suite"
PERMISSION_PATTERN = "ForPrintValidation(run_validation_suite)"


def _module() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def _git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    return cp.stdout


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "canonical"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "cf10@example.invalid")
    _git(repo, "config", "user.name", "CF10 Test")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-q", "-m", "baseline")
    (repo / "tracked.txt").write_text("inherited-dirty\n", encoding="utf-8")
    return repo.resolve()


def _snapshot(repo: Path) -> dict[str, str]:
    return {
        "head": _git(repo, "rev-parse", "HEAD").strip(),
        "status": _git(
            repo,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ),
        "unstaged": _git(repo, "diff", "--binary"),
        "staged": _git(repo, "diff", "--cached", "--binary"),
    }


def _runtime_config(executable: str) -> dict[str, Any]:
    return {
        "module_id": "forprint_system_blueprint",
        "provider_adapter": "CONSOLE_COMMAND",
        "working_directory": "ATTEMPT_WORKSPACE_REPO",
        "timeout_seconds": 900,
        "budget": {"provider_specific": {"max_ai_credits": 30}},
        "command": {
            "representation": "ARGV_NO_SHELL",
            "provider_id": "github_copilot_cli",
            "runtime_id": "github_copilot_cli",
            "executable": executable,
            "base_argv": [executable],
            "prompt_transport": "provider_adapter_owned",
            "shell": False,
        },
        "tool_policy": {
            "exact_runtime_argv_deferred_to_launch_adapter": True,
            "canonical_repository_write_allowed": False,
            "foreign_repository_write_allowed": False,
            "git_commit_allowed": False,
            "git_push_allowed": False,
            "merge_allowed": False,
            "release_allowed": False,
            "automatic_accept_allowed": False,
        },
    }


def _resolved_runtime(executable: str) -> dict[str, Any]:
    return {
        "provider_id": "github_copilot_cli",
        "runtime_id": "github_copilot_cli",
        "model_id": "auto",
        "executable": executable,
        "command_representation": "ARGV_NO_SHELL",
        "working_directory": "ATTEMPT_WORKSPACE_REPO",
        "timeout_seconds": 900,
        "network_policy": "ALLOW",
        "budget": {"provider_specific": {"max_ai_credits": 30}},
        "authority_granted": False,
    }


def test_makefile_exposes_project_native_provider_session_proof_targets() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")

    assert ".PHONY: cf10-worker-provider-session-proof-check" in text
    assert "cf10-worker-provider-session-proof-check:" in text
    assert ".PHONY: cf10-worker-provider-session-proof" in text
    assert "cf10-worker-provider-session-proof:" in text
    assert (
        "scripts/coordination/control_plane/worker_runtime/"
        "provider_session_proof.py"
    ) in text
    assert "CF10_WORKER_PROVIDER_PROOF_RUNTIME_ROOT" in text


def test_build_plan_uses_repaired_provider_identities_and_exact_venv_python(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proof = _module()
    repo = _fixture_repo(tmp_path)
    runtime_root = tmp_path / "runtime"
    fake_copilot = tmp_path / "copilot"
    fake_copilot.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_copilot.chmod(0o755)

    monkeypatch.setattr(
        proof.registry,
        "load_module_runtime_config",
        lambda _root: _runtime_config(str(fake_copilot)),
    )
    monkeypatch.setattr(
        proof.registry,
        "resolve_default_runtime",
        lambda _root: _resolved_runtime(str(fake_copilot)),
    )
    monkeypatch.setattr(proof.sys, "executable", "/venv/.venv_blueprint/bin/python")

    plan = proof.build_provider_session_plan(
        canonical_repo=repo,
        runtime_root=runtime_root,
        suite_id="cf10-worker-pipeline",
        require_tier="LOCAL_FOCUSED",
        profile=False,
    )

    assert plan["provider_id"] == "github_copilot_cli"
    assert plan["command_representation"] == "ARGV_NO_SHELL"
    assert plan["model_visible_tool_id"] == MODEL_TOOL_ID
    assert plan["permission_pattern"] == PERMISSION_PATTERN
    assert plan["mcp_python_executable"] == "/venv/.venv_blueprint/bin/python"
    assert plan["mcp_python_path_resolved"] is False
    assert plan["available_tools"] == [MODEL_TOOL_ID]
    assert plan["allow_tools"] == [PERMISSION_PATTERN]
    assert plan["allow_all_tools"] is False
    assert plan["persistent_mcp_config_written"] is False
    assert plan["profile"] is False

    argv = plan["argv"]
    assert argv[argv.index("--available-tools") + 1] == MODEL_TOOL_ID
    assert argv[argv.index("--allow-tool") + 1] == PERMISSION_PATTERN
    assert "--allow-all-tools" not in argv
    assert "--no-ask-user" in argv
    assert "--additional-mcp-config" in argv

    config_raw = argv[argv.index("--additional-mcp-config") + 1]
    config = json.loads(config_raw)
    server = config["mcpServers"]["ForPrintValidation"]
    assert server["command"] == "/venv/.venv_blueprint/bin/python"
    assert server["tools"] == ["run_validation_suite"]
    assert server["cwd"] == str(repo)
    assert ".mcp.json" not in json.dumps(config)
    assert ".github/mcp.json" not in json.dumps(config)


def test_build_plan_rejects_runtime_root_inside_canonical_repo(
    tmp_path: Path,
) -> None:
    proof = _module()
    repo = _fixture_repo(tmp_path)

    with pytest.raises(
        proof.WorkerProviderSessionProofError,
        match="outside canonical",
    ):
        proof.build_provider_session_plan(
            canonical_repo=repo,
            runtime_root=repo / "runtime",
            suite_id="cf10-worker-pipeline",
            require_tier="LOCAL_FOCUSED",
            profile=False,
        )


def test_build_plan_rejects_profile_true_for_baseline_provider_proof(
    tmp_path: Path,
) -> None:
    proof = _module()
    repo = _fixture_repo(tmp_path)

    with pytest.raises(
        proof.WorkerProviderSessionProofError,
        match="profile=false",
    ):
        proof.build_provider_session_plan(
            canonical_repo=repo,
            runtime_root=tmp_path / "runtime",
            suite_id="cf10-worker-pipeline",
            require_tier="LOCAL_FOCUSED",
            profile=True,
        )


def test_validate_structured_execution_requires_hash_bound_suite_and_tier(
    tmp_path: Path,
) -> None:
    proof = _module()
    execution_dir = tmp_path / "structured-exec-0123456789abcdef0123"
    execution_dir.mkdir(parents=True)

    stdout = execution_dir / "stdout.log"
    stderr = execution_dir / "stderr.log"
    stdout.write_text(
        "\n".join(
            [
                "VALIDATION_SUITE_ID=cf10-worker-pipeline",
                "VALIDATION_SUITE_VERIFICATION_TIER=LOCAL_FOCUSED",
                "VALIDATION_SUITE_STEP_COUNT=3",
                "VALIDATION_SUITE=PASS suite=cf10-worker-pipeline",
                "",
            ]
        ),
        encoding="utf-8",
    )
    stderr.write_text("", encoding="utf-8")

    result = {
        "schema_version": "forprint_structured_execution_result_v0_1",
        "request_id": "cf10-provider-proof:validation:0001",
        "capability_id": "validation_suite",
        "capability_version": "0.2.0",
        "execution_id": execution_dir.name,
        "execution_identity": {
            "attempt_id": "cf10-provider-session-proof",
            "task_id": "cf10-validation-check-pipeline-profile-and-optimization-v0-1",
            "work_front_id": "wf-cf10-project-native-provider-session-proof-v0-1",
            "explicit_dispatch_decision_id": "cf10-provider-session-proof",
        },
        "consumer_id": "cf10_worker_validation_mcp",
        "exact_cwd": str(tmp_path),
        "argv_digest": "1" * 64,
        "elapsed_seconds": 5.25,
        "return_code": 0,
        "outcome": "completed",
        "timed_out": False,
        "shell": False,
        "stdout_evidence": {
            "path": str(stdout),
            "sha256": hashlib.sha256(stdout.read_bytes()).hexdigest(),
            "size_bytes": stdout.stat().st_size,
        },
        "stderr_evidence": {
            "path": str(stderr),
            "sha256": hashlib.sha256(stderr.read_bytes()).hexdigest(),
            "size_bytes": 0,
        },
        "authority": {
            "executor_grants_authority": False,
            "canonical_write_allowed": False,
            "safe_write_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
            "release_allowed": False,
            "promotion_allowed": False,
            "arbitrary_shell_allowed": False,
        },
        "result_evidence_path": str(
            execution_dir / "execution_result_v0_1.yaml"
        ),
    }
    material = dict(result)
    result["evidence_digest"] = hashlib.sha256(
        json.dumps(
            material,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()

    result_path = execution_dir / "execution_result_v0_1.yaml"
    result_path.write_text(
        yaml.safe_dump(result, sort_keys=False),
        encoding="utf-8",
    )

    validated = proof.validate_structured_execution_evidence(
        result_path=result_path,
        expected_suite_id="cf10-worker-pipeline",
        expected_tier="LOCAL_FOCUSED",
    )

    assert validated["capability_id"] == "validation_suite"
    assert validated["capability_version"] == "0.2.0"
    assert validated["execution_id"] == execution_dir.name
    assert validated["return_code"] == 0
    assert validated["timed_out"] is False
    assert validated["shell"] is False
    assert validated["suite_id"] == "cf10-worker-pipeline"
    assert validated["require_tier"] == "LOCAL_FOCUSED"
    assert validated["suite_pass"] is True
    assert validated["stdout_sha256"] == hashlib.sha256(
        stdout.read_bytes()
    ).hexdigest()


def test_validate_structured_execution_rejects_tampered_stdout(
    tmp_path: Path,
) -> None:
    proof = _module()
    execution_dir = tmp_path / "structured-exec-abcdefabcdefabcdefab"
    execution_dir.mkdir(parents=True)
    stdout = execution_dir / "stdout.log"
    stdout.write_text(
        "VALIDATION_SUITE_ID=cf10-worker-pipeline\n"
        "VALIDATION_SUITE_VERIFICATION_TIER=LOCAL_FOCUSED\n"
        "VALIDATION_SUITE=PASS suite=cf10-worker-pipeline\n",
        encoding="utf-8",
    )
    stderr = execution_dir / "stderr.log"
    stderr.write_text("", encoding="utf-8")

    result = {
        "capability_id": "validation_suite",
        "capability_version": "0.2.0",
        "execution_id": execution_dir.name,
        "elapsed_seconds": 1.0,
        "return_code": 0,
        "outcome": "completed",
        "timed_out": False,
        "shell": False,
        "stdout_evidence": {
            "path": str(stdout),
            "sha256": hashlib.sha256(stdout.read_bytes()).hexdigest(),
            "size_bytes": stdout.stat().st_size,
        },
        "stderr_evidence": {
            "path": str(stderr),
            "sha256": hashlib.sha256(stderr.read_bytes()).hexdigest(),
            "size_bytes": 0,
        },
        "evidence_digest": "a" * 64,
        "authority": {
            "executor_grants_authority": False,
            "canonical_write_allowed": False,
            "safe_write_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
            "release_allowed": False,
            "promotion_allowed": False,
            "arbitrary_shell_allowed": False,
        },
    }
    result_path = execution_dir / "execution_result_v0_1.yaml"
    result_path.write_text(
        yaml.safe_dump(result, sort_keys=False),
        encoding="utf-8",
    )
    stdout.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(
        proof.WorkerProviderSessionProofError,
        match="stdout.*sha256",
    ):
        proof.validate_structured_execution_evidence(
            result_path=result_path,
            expected_suite_id="cf10-worker-pipeline",
            expected_tier="LOCAL_FOCUSED",
        )


def test_repo_snapshot_preserves_inherited_dirty_state(tmp_path: Path) -> None:
    proof = _module()
    repo = _fixture_repo(tmp_path)

    observed = proof.capture_repository_snapshot(repo)

    assert observed["head"] == _snapshot(repo)["head"]
    assert observed["status"] == _snapshot(repo)["status"]
    assert observed["unstaged_diff_sha256"] == hashlib.sha256(
        _snapshot(repo)["unstaged"].encode("utf-8")
    ).hexdigest()
    assert observed["staged_diff_sha256"] == hashlib.sha256(
        _snapshot(repo)["staged"].encode("utf-8")
    ).hexdigest()


def test_provider_proof_module_does_not_define_attempt_or_release_authority() -> None:
    proof = _module()

    forbidden = (
        "append_attempt",
        "create_attempt",
        "authorize_dispatch",
        "promote_candidate",
        "git_commit",
        "git_push",
        "merge",
        "release",
    )
    exported = set(dir(proof))
    assert not exported.intersection(forbidden)


def test_run_provider_session_proof_uses_shared_launcher_and_preserves_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proof = _module()
    repo = _fixture_repo(tmp_path)
    runtime_root = tmp_path / "provider-proof-runtime"
    fake_copilot = tmp_path / "copilot"
    fake_copilot.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_copilot.chmod(0o755)

    mcp_script = (
        repo
        / "scripts/coordination/control_plane/worker_runtime/"
        "worker_validation_mcp.py"
    )
    mcp_script.parent.mkdir(parents=True)
    mcp_script.write_text("# proof fixture\n", encoding="utf-8")

    monkeypatch.setattr(
        proof.registry,
        "load_module_runtime_config",
        lambda _root: _runtime_config(str(fake_copilot)),
    )
    monkeypatch.setattr(
        proof.registry,
        "resolve_default_runtime",
        lambda _root: _resolved_runtime(str(fake_copilot)),
    )
    monkeypatch.setattr(
        proof,
        "_preflight_mcp_python",
        lambda _python, _cwd: {
            "python_executable": str(_python),
            "mcp_import": "PASS",
        },
    )

    calls: list[dict[str, Any]] = []

    def fake_launch_process(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        evidence_root = runtime_root / "structured_execution"
        execution_dir = evidence_root / "structured-exec-feedfacefeedfacefeed"
        execution_dir.mkdir(parents=True)

        stdout = execution_dir / "stdout.log"
        stderr = execution_dir / "stderr.log"
        stdout.write_text(
            "\n".join(
                [
                    "VALIDATION_SUITE_ID=cf10-worker-pipeline",
                    "VALIDATION_SUITE_VERIFICATION_TIER=LOCAL_FOCUSED",
                    "VALIDATION_SUITE_STEP_COUNT=3",
                    "VALIDATION_SUITE=PASS suite=cf10-worker-pipeline",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        stderr.write_text("", encoding="utf-8")

        result: dict[str, Any] = {
            "schema_version": "forprint_structured_execution_result_v0_1",
            "request_id": "cf10-provider-session-proof:validation:0001",
            "capability_id": "validation_suite",
            "capability_version": "0.2.0",
            "execution_id": execution_dir.name,
            "execution_identity": {
                "attempt_id": "cf10-provider-session-proof",
                "task_id": (
                    "cf10-validation-check-pipeline-profile-and-"
                    "optimization-v0-1"
                ),
                "work_front_id": (
                    "wf-cf10-project-native-provider-session-proof-v0-1"
                ),
                "explicit_dispatch_decision_id": (
                    "cf10-provider-session-proof"
                ),
            },
            "consumer_id": "cf10_worker_validation_mcp",
            "exact_cwd": str(repo),
            "argv_digest": "2" * 64,
            "elapsed_seconds": 4.0,
            "return_code": 0,
            "outcome": "completed",
            "timed_out": False,
            "shell": False,
            "stdout_evidence": {
                "path": str(stdout),
                "sha256": hashlib.sha256(stdout.read_bytes()).hexdigest(),
                "size_bytes": stdout.stat().st_size,
            },
            "stderr_evidence": {
                "path": str(stderr),
                "sha256": hashlib.sha256(stderr.read_bytes()).hexdigest(),
                "size_bytes": 0,
            },
            "authority": {
                "executor_grants_authority": False,
                "canonical_write_allowed": False,
                "safe_write_allowed": False,
                "commit_allowed": False,
                "push_allowed": False,
                "merge_allowed": False,
                "release_allowed": False,
                "promotion_allowed": False,
                "arbitrary_shell_allowed": False,
            },
            "result_evidence_path": str(
                execution_dir / "execution_result_v0_1.yaml"
            ),
        }
        result["evidence_digest"] = hashlib.sha256(
            json.dumps(
                result,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        result_path = execution_dir / "execution_result_v0_1.yaml"
        result_path.write_text(
            yaml.safe_dump(result, sort_keys=False),
            encoding="utf-8",
        )

        provider_stdout = Path(kwargs["stdout_path"])
        provider_stderr = Path(kwargs["stderr_path"])
        provider_stdout.parent.mkdir(parents=True, exist_ok=True)
        provider_stdout.write_text(
            f"EXECUTION_ID={execution_dir.name}\n"
            f"EVIDENCE_DIGEST={result['evidence_digest']}\n",
            encoding="utf-8",
        )
        provider_stderr.write_text("", encoding="utf-8")

        return {
            "pid": 12345,
            "started_at": "2026-10-07T00:00:00Z",
            "finished_at": "2026-10-07T00:00:04Z",
            "elapsed_seconds": 4.0,
            "return_code": 0,
            "timed_out": False,
            "outcome": "completed",
            "shell": False,
            "stdout_path": str(provider_stdout),
            "stderr_path": str(provider_stderr),
            "process_started": True,
            "argv_sha256": "3" * 64,
            "heartbeat_observations": [],
            "stall_detected": False,
            "stall_evidence": [],
            "cwd": str(repo),
        }

    monkeypatch.setattr(proof, "launch_process", fake_launch_process)

    before = _snapshot(repo)
    result = proof.run_provider_session_proof(
        canonical_repo=repo,
        runtime_root=runtime_root,
        suite_id="cf10-worker-pipeline",
        require_tier="LOCAL_FOCUSED",
        profile=False,
    )

    assert result["state"] == "PASS"
    assert result["real_mcp_tool_invocation_proven"] is True
    assert result["repository_state_unchanged"] is True
    assert result["persistent_mcp_config_written"] is False
    assert result["authority_widened"] is False
    assert result["structured_execution"]["capability_id"] == "validation_suite"
    assert result["structured_execution"]["capability_version"] == "0.2.0"
    assert result["structured_execution"]["suite_id"] == "cf10-worker-pipeline"
    assert result["structured_execution"]["require_tier"] == "LOCAL_FOCUSED"
    assert result["structured_execution"]["suite_pass"] is True
    assert Path(result["evidence_path"]).is_file()
    assert len(calls) == 1
    assert calls[0]["argv"] == result["provider"]["argv"]
    assert calls[0]["cwd"] == str(repo)
    assert _snapshot(repo) == before


def test_run_provider_session_proof_refuses_existing_runtime_evidence(
    tmp_path: Path,
) -> None:
    proof = _module()
    repo = _fixture_repo(tmp_path)
    runtime_root = tmp_path / "provider-proof-runtime"
    runtime_root.mkdir()
    (runtime_root / "existing.txt").write_text("immutable\n", encoding="utf-8")

    with pytest.raises(
        proof.WorkerProviderSessionProofError,
        match="immutable|empty|already",
    ):
        proof.run_provider_session_proof(
            canonical_repo=repo,
            runtime_root=runtime_root,
            suite_id="cf10-worker-pipeline",
            require_tier="LOCAL_FOCUSED",
            profile=False,
        )
