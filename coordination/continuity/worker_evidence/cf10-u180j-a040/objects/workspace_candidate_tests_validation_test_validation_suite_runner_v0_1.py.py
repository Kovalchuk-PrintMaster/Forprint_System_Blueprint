from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.validation import run_validation_suite_v0_1 as suite_runner

ROOT = Path(__file__).resolve().parents[2]


def _registry_data() -> dict:
    return yaml.safe_load(
        (ROOT / suite_runner.REGISTRY).read_text(encoding="utf-8")
    )


def test_live_registry_is_valid_and_contains_cf10_suite() -> None:
    registry = suite_runner.load_registry(ROOT)
    suite = suite_runner.resolve_suite(registry, "cf10-worker-pipeline")

    assert suite["safety"] == "read_only_synthetic_validation"
    assert suite["verification_tier"] == "LOCAL_FOCUSED"
    assert [step["kind"] for step in suite["steps"]] == [
        "python_script",
        "python_script",
        "pytest",
    ]


@pytest.mark.parametrize("tier", [None, "UNSUPPORTED"])
def test_registry_rejects_missing_or_invalid_verification_tier(
    tier: str | None,
) -> None:
    data = copy.deepcopy(_registry_data())
    if tier is None:
        del data["suites"]["cf10-worker-pipeline"]["verification_tier"]
    else:
        data["suites"]["cf10-worker-pipeline"]["verification_tier"] = tier

    with pytest.raises(suite_runner.SuiteError, match="verification_tier"):
        suite_runner.validate_registry_data(
            data,
            root=ROOT,
            require_paths=False,
        )


def test_registry_rejects_arbitrary_command_key() -> None:
    data = copy.deepcopy(_registry_data())
    data["suites"]["cf10-worker-pipeline"]["steps"][0]["command"] = "rm -rf ."

    with pytest.raises(suite_runner.SuiteError, match="unsupported keys"):
        suite_runner.validate_registry_data(
            data,
            root=ROOT,
            require_paths=False,
        )


def test_registry_rejects_parent_traversal() -> None:
    data = copy.deepcopy(_registry_data())
    data["suites"]["cf10-worker-pipeline"]["steps"][0]["path"] = "../escape.py"

    with pytest.raises(suite_runner.SuiteError, match="escapes repository root"):
        suite_runner.validate_registry_data(
            data,
            root=ROOT,
            require_paths=False,
        )


def test_unknown_suite_fails_closed() -> None:
    registry = suite_runner.load_registry(ROOT)

    with pytest.raises(suite_runner.SuiteError, match="unknown validation suite"):
        suite_runner.resolve_suite(registry, "not-registered")


def test_cf10_commands_are_typed_argv_without_shell() -> None:
    registry = suite_runner.load_registry(ROOT)
    suite = suite_runner.resolve_suite(registry, "cf10-worker-pipeline")

    commands = suite_runner.build_suite_commands(
        suite=suite,
        python_executable=sys.executable,
    )

    assert commands[0] == [
        sys.executable,
        "scripts/validation/validate_cf10_worker_delta_governance_reconciliation_v0_1.py",
    ]
    assert commands[1] == [
        sys.executable,
        "scripts/validation/validate_cf10_post_worker_result_collection_v0_1.py",
    ]
    assert commands[2][:4] == [sys.executable, "-m", "pytest", "-q"]
    assert len(commands[2][4:]) == 5
    assert (
        "tests/validation/test_validation_suite_runner_v0_1.py"
        in commands[2][4:]
    )
    assert all(isinstance(command, list) for command in commands)


def test_outer_run_reuses_existing_isolation_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(suite_runner.ISOLATION_ENV, raising=False)
    monkeypatch.delenv(suite_runner.SUITE_BINDING_ENV, raising=False)
    observed: dict[str, object] = {}

    def fake_isolated_check(
        *,
        root: Path,
        target: str,
        module_root: Path | None,
        keep_workspace: bool,
    ) -> int:
        observed["root"] = root
        observed["target"] = target
        observed["module_root"] = module_root
        observed["keep_workspace"] = keep_workspace
        observed["binding"] = os.environ.get(suite_runner.SUITE_BINDING_ENV)
        return 0

    monkeypatch.setattr(
        suite_runner,
        "run_isolated_check",
        fake_isolated_check,
    )

    rc = suite_runner.run_suite(
        root=ROOT,
        suite_id="cf10-worker-pipeline",
        module_root=None,
        keep_workspace=False,
    )

    assert rc == 0
    assert observed["target"] == "validation-suite"
    assert observed["binding"] == "cf10-worker-pipeline"
    assert suite_runner.SUITE_BINDING_ENV not in os.environ


def test_matching_required_tier_reuses_existing_isolation_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(suite_runner.ISOLATION_ENV, raising=False)
    observed: dict[str, object] = {}

    def fake_isolated_check(
        *,
        root: Path,
        target: str,
        module_root: Path | None,
        keep_workspace: bool,
    ) -> int:
        observed["target"] = target
        return 0

    monkeypatch.setattr(suite_runner, "run_isolated_check", fake_isolated_check)

    rc = suite_runner.run_suite(
        root=ROOT,
        suite_id="cf10-worker-pipeline",
        module_root=None,
        keep_workspace=False,
        require_tier="LOCAL_FOCUSED",
    )

    assert rc == 0
    assert observed["target"] == "validation-suite"


def test_mismatched_required_tier_refuses_before_isolation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(suite_runner.ISOLATION_ENV, raising=False)
    isolated = False

    def fake_isolated_check(**_: object) -> int:
        nonlocal isolated
        isolated = True
        return 0

    monkeypatch.setattr(suite_runner, "run_isolated_check", fake_isolated_check)

    with pytest.raises(suite_runner.SuiteError, match="does not match required tier"):
        suite_runner.run_suite(
            root=ROOT,
            suite_id="cf10-worker-pipeline",
            module_root=None,
            keep_workspace=False,
            require_tier="CORE",
        )

    assert isolated is False


def test_direct_execution_requires_isolated_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(suite_runner.ISOLATION_ENV, raising=False)
    monkeypatch.delenv(suite_runner.SUITE_BINDING_ENV, raising=False)

    with pytest.raises(suite_runner.SuiteError, match="isolated mirror marker"):
        suite_runner.execute_registered_suite(
            root=ROOT,
            suite_id="cf10-worker-pipeline",
        )


@pytest.mark.parametrize(
    ("profile", "expected_profile_arg"),
    [(0, False), (1, True)],
)
def test_make_validation_suite_handles_absent_optional_environment(
    tmp_path: Path,
    profile: int,
    expected_profile_arg: bool,
) -> None:
    fake_python = tmp_path / "fake-python"
    fake_python.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "print(json.dumps(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    env = os.environ.copy()
    env.pop("FORPRINT_VALIDATION_SUITE_ID", None)
    env.pop("FORPRINT_VALIDATION_SUITE_PROFILE", None)

    result = subprocess.run(
        [
            "make",
            "--no-print-directory",
            "validation-suite",
            "SUITE=cf10-worker-pipeline",
            f"PROFILE={profile}",
            f"PYTHON={fake_python}",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    args = json.loads(result.stdout)
    assert args[:2] == [
        "scripts/validation/run_validation_suite_v0_1.py",
        "--suite",
    ]
    assert args[2] == "cf10-worker-pipeline"
    assert ("--profile" in args[3:]) is expected_profile_arg


def test_profile_reports_controlled_step_and_total_timings(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    steps = [
        {"id": "quick-check", "kind": "python_script", "path": "check.py"},
        {"id": "focused-tests", "kind": "pytest", "paths": ["test_check.py"]},
    ]
    suite = {
        "verification_tier": "LOCAL_FOCUSED",
        "steps": steps,
    }
    monkeypatch.setenv(suite_runner.ISOLATION_ENV, "1")
    monkeypatch.setenv(suite_runner.SUITE_BINDING_ENV, "test-suite")
    monkeypatch.setattr(
        suite_runner,
        "load_registry",
        lambda _root: {"suites": {"test-suite": suite}},
    )
    clock = iter([0.0, 1.0, 2.0, 3.0, 5.0, 8.0])
    monkeypatch.setattr(suite_runner.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(
        suite_runner.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=""
        ),
    )

    result = suite_runner.execute_registered_suite(
        root=ROOT,
        suite_id="test-suite",
        profile=True,
    )

    output = capsys.readouterr()
    assert result == 0
    profile_line = next(
        line for line in output.out.splitlines()
        if line.startswith("VALIDATION_SUITE_PROFILE_JSON=")
    )
    summary = json.loads(profile_line.split("=", 1)[1])
    assert summary == {
        "suite_id": "test-suite",
        "verification_tier": "LOCAL_FOCUSED",
        "steps": [
            {
                "step_id": "quick-check",
                "kind": "python_script",
                "elapsed_seconds": 1.0,
                "return_code": 0,
            },
            {
                "step_id": "focused-tests",
                "kind": "pytest",
                "elapsed_seconds": 2.0,
                "return_code": 0,
            },
        ],
        "total_elapsed_seconds": 8.0,
        "critical_step": "focused-tests",
    }
    assert "VALIDATION_SUITE_STEP_TIME=quick-check elapsed_seconds=1.000000" in output.err
    assert "VALIDATION_SUITE_TOTAL_TIME=elapsed_seconds=8.000000" in output.err


def test_profile_preserves_fail_fast_and_reports_partial_evidence(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    steps = [
        {"id": "first", "kind": "python_script", "path": "first.py"},
        {"id": "fails", "kind": "python_script", "path": "fails.py"},
        {"id": "not-run", "kind": "pytest", "paths": ["not_run.py"]},
    ]
    suite = {"verification_tier": "LOCAL_FOCUSED", "steps": steps}
    monkeypatch.setenv(suite_runner.ISOLATION_ENV, "1")
    monkeypatch.setenv(suite_runner.SUITE_BINDING_ENV, "test-suite")
    monkeypatch.setattr(
        suite_runner,
        "load_registry",
        lambda _root: {"suites": {"test-suite": suite}},
    )
    clock = iter([0.0, 1.0, 2.0, 4.0, 6.0, 7.0])
    monkeypatch.setattr(suite_runner.time, "monotonic", lambda: next(clock))
    calls = 0

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(
            args=[],
            returncode=7 if calls == 2 else 0,
            stdout="",
        )

    monkeypatch.setattr(suite_runner.subprocess, "run", fake_run)

    result = suite_runner.execute_registered_suite(
        root=ROOT,
        suite_id="test-suite",
        profile=True,
    )

    output = capsys.readouterr()
    assert result == 7
    assert calls == 2
    profile_line = next(
        line for line in output.out.splitlines()
        if line.startswith("VALIDATION_SUITE_PROFILE_JSON=")
    )
    summary = json.loads(profile_line.split("=", 1)[1])
    assert [step["step_id"] for step in summary["steps"]] == ["first", "fails"]
    assert summary["steps"][-1]["return_code"] == 7
    assert summary["critical_step"] == "fails"
