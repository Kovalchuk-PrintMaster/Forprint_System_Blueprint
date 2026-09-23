from __future__ import annotations

import copy
import os
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
    assert [step["kind"] for step in suite["steps"]] == [
        "python_script",
        "python_script",
        "pytest",
    ]


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
    assert len(commands[2][4:]) == 4
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
