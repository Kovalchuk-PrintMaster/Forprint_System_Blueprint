#!/usr/bin/env python3
"""Run one registered Blueprint validation suite through existing isolation."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    from scripts.validation.run_non_mutating_make_check import (
        IsolationError,
        run_isolated_check,
    )
except ModuleNotFoundError:
    from run_non_mutating_make_check import IsolationError, run_isolated_check


SCHEMA = "forprint_validation_suite_registry_v0_1"
REGISTRY = Path(
    "coordination/standards/automation/validation_suite_registry_v0_1.yaml"
)
ALLOWED_STEP_KINDS = {"python_script", "pytest"}
ALLOWED_VERIFICATION_TIERS = {"LOCAL_FOCUSED", "RELATED", "CORE", "FULL"}
SUITE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
STEP_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ISOLATION_ENV = "FORPRINT_NON_MUTATING_CHECK_ISOLATED"
SUITE_BINDING_ENV = "FORPRINT_VALIDATION_SUITE_ID"


class SuiteError(RuntimeError):
    """Raised when suite configuration or execution fails closed."""


def _safe_relative_path(raw: Any) -> Path:
    if not isinstance(raw, str) or not raw:
        raise SuiteError("registry path must be a non-empty string")
    if "\\" in raw:
        raise SuiteError(f"registry path must use repository separators: {raw!r}")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise SuiteError(f"registry path escapes repository root: {raw!r}")
    if path.as_posix() != raw or raw.startswith("./"):
        raise SuiteError(f"registry path must be normalized: {raw!r}")
    return path


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SuiteError(f"{label} must be a mapping")
    return value


def _reject_unknown_keys(
    mapping: dict[str, Any],
    *,
    allowed: set[str],
    label: str,
) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise SuiteError(f"{label} contains unsupported keys: {unknown}")


def _validate_existing_path(root: Path, path: Path, *, label: str) -> None:
    candidate = root / path
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise SuiteError(f"{label} escapes repository root: {path}") from exc
    if not candidate.is_file():
        raise SuiteError(f"{label} does not exist as a file: {path}")
    if candidate.is_symlink():
        raise SuiteError(f"{label} must not be a symlink: {path}")


def _validate_verification_tier(value: Any, *, label: str) -> str:
    if value not in ALLOWED_VERIFICATION_TIERS:
        raise SuiteError(
            f"{label} must be one of {sorted(ALLOWED_VERIFICATION_TIERS)}"
        )
    return value


def validate_registry_data(
    data: Any,
    *,
    root: Path,
    require_paths: bool = True,
) -> dict[str, Any]:
    """Validate registry schema and return the normalized mapping."""

    root = root.resolve()
    registry = _require_mapping(data, "registry")
    _reject_unknown_keys(
        registry,
        allowed={"schema_version", "status", "authority", "suites"},
        label="registry",
    )
    if registry.get("schema_version") != SCHEMA:
        raise SuiteError(f"unexpected registry schema: {registry.get('schema_version')!r}")
    if registry.get("status") != "current_standard":
        raise SuiteError("registry status must be current_standard")
    if registry.get("authority") != "forprint_system_blueprint":
        raise SuiteError("registry authority must be forprint_system_blueprint")

    suites = _require_mapping(registry.get("suites"), "registry.suites")
    if not suites:
        raise SuiteError("registry.suites must not be empty")

    for suite_id, raw_suite in suites.items():
        if not isinstance(suite_id, str) or not SUITE_ID_RE.fullmatch(suite_id):
            raise SuiteError(f"invalid suite id: {suite_id!r}")
        suite = _require_mapping(raw_suite, f"suite {suite_id}")
        _reject_unknown_keys(
            suite,
            allowed={"description", "safety", "verification_tier", "steps"},
            label=f"suite {suite_id}",
        )
        if not isinstance(suite.get("description"), str) or not suite["description"].strip():
            raise SuiteError(f"suite {suite_id} requires description")
        if suite.get("safety") != "read_only_synthetic_validation":
            raise SuiteError(
                f"suite {suite_id} safety must be read_only_synthetic_validation"
            )
        _validate_verification_tier(
            suite.get("verification_tier"),
            label=f"suite {suite_id} verification_tier",
        )
        steps = suite.get("steps")
        if not isinstance(steps, list) or not steps:
            raise SuiteError(f"suite {suite_id} requires non-empty steps")

        seen_step_ids: set[str] = set()
        for index, raw_step in enumerate(steps, start=1):
            step = _require_mapping(raw_step, f"suite {suite_id} step {index}")
            kind = step.get("kind")
            if kind not in ALLOWED_STEP_KINDS:
                raise SuiteError(
                    f"suite {suite_id} step {index} has unsupported kind: {kind!r}"
                )
            step_id = step.get("id")
            if not isinstance(step_id, str) or not STEP_ID_RE.fullmatch(step_id):
                raise SuiteError(
                    f"suite {suite_id} step {index} has invalid id: {step_id!r}"
                )
            if step_id in seen_step_ids:
                raise SuiteError(f"suite {suite_id} duplicates step id: {step_id}")
            seen_step_ids.add(step_id)

            if kind == "python_script":
                _reject_unknown_keys(
                    step,
                    allowed={"id", "kind", "path"},
                    label=f"suite {suite_id} step {step_id}",
                )
                path = _safe_relative_path(step.get("path"))
                if path.suffix != ".py":
                    raise SuiteError(f"python_script must reference .py: {path}")
                if require_paths:
                    _validate_existing_path(root, path, label=f"suite {suite_id} step {step_id}")
            else:
                _reject_unknown_keys(
                    step,
                    allowed={"id", "kind", "paths"},
                    label=f"suite {suite_id} step {step_id}",
                )
                paths = step.get("paths")
                if not isinstance(paths, list) or not paths:
                    raise SuiteError(
                        f"suite {suite_id} pytest step {step_id} requires paths"
                    )
                if len(paths) != len(set(paths)):
                    raise SuiteError(
                        f"suite {suite_id} pytest step {step_id} duplicates paths"
                    )
                for raw_path in paths:
                    path = _safe_relative_path(raw_path)
                    if path.suffix != ".py":
                        raise SuiteError(f"pytest path must reference .py: {path}")
                    if require_paths:
                        _validate_existing_path(root, path, label=f"suite {suite_id} step {step_id}")

    return registry


def load_registry(root: Path, *, require_paths: bool = True) -> dict[str, Any]:
    """Load and validate the canonical registry from ``root``."""

    registry_path = root.resolve() / REGISTRY
    if not registry_path.is_file():
        raise SuiteError(f"validation suite registry missing: {REGISTRY}")
    if registry_path.is_symlink():
        raise SuiteError(f"validation suite registry must not be a symlink: {REGISTRY}")
    try:
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SuiteError(f"invalid validation suite registry YAML: {exc}") from exc
    return validate_registry_data(data, root=root, require_paths=require_paths)


def resolve_suite(registry: dict[str, Any], suite_id: str) -> dict[str, Any]:
    """Resolve one exact registered suite or fail closed."""

    if not SUITE_ID_RE.fullmatch(suite_id):
        raise SuiteError(f"invalid suite id: {suite_id!r}")
    suites = registry["suites"]
    if suite_id not in suites:
        raise SuiteError(f"unknown validation suite: {suite_id}")
    return suites[suite_id]


def build_suite_commands(
    *,
    suite: dict[str, Any],
    python_executable: str,
) -> list[list[str]]:
    """Build typed argv lists for a validated suite; never return shell text."""

    commands: list[list[str]] = []
    for step in suite["steps"]:
        if step["kind"] == "python_script":
            commands.append([python_executable, step["path"]])
        elif step["kind"] == "pytest":
            commands.append([python_executable, "-m", "pytest", "-q", *step["paths"]])
        else:
            raise SuiteError(f"unsupported validated step kind: {step['kind']!r}")
    return commands


def execute_registered_suite(
    *,
    root: Path,
    suite_id: str,
    require_tier: str | None = None,
) -> int:
    """Execute a registered suite only inside the bound isolated mirror."""

    if os.environ.get(ISOLATION_ENV) != "1":
        raise SuiteError("registered suite execution requires isolated mirror marker")
    if os.environ.get(SUITE_BINDING_ENV) != suite_id:
        raise SuiteError("isolated suite binding does not match requested suite")

    registry = load_registry(root)
    suite = resolve_suite(registry, suite_id)
    resolved_tier = _validate_verification_tier(
        suite["verification_tier"],
        label=f"suite {suite_id} verification_tier",
    )
    if require_tier is not None:
        required_tier = _validate_verification_tier(
            require_tier,
            label="required verification tier",
        )
        if resolved_tier != required_tier:
            raise SuiteError(
                f"suite {suite_id} verification tier {resolved_tier} "
                f"does not match required tier {required_tier}"
            )
    commands = build_suite_commands(suite=suite, python_executable=sys.executable)

    print(f"VALIDATION_SUITE_ID={suite_id}")
    print(f"VALIDATION_SUITE_VERIFICATION_TIER={resolved_tier}")
    print(f"VALIDATION_SUITE_STEP_COUNT={len(commands)}")
    for index, command in enumerate(commands, start=1):
        print(f"VALIDATION_SUITE_STEP={index}/{len(commands)}")
        print("$ " + " ".join(command))
        cp = subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if cp.stdout:
            sys.stdout.write(cp.stdout)
        if cp.returncode:
            print(
                f"VALIDATION_SUITE=FAIL suite={suite_id} step={index} rc={cp.returncode}",
                file=sys.stderr,
            )
            return cp.returncode

    print(f"VALIDATION_SUITE=PASS suite={suite_id}")
    return 0


def _resolve_module_root(root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def run_suite(
    *,
    root: Path,
    suite_id: str,
    module_root: Path | None,
    keep_workspace: bool,
    require_tier: str | None = None,
) -> int:
    """Validate binding then run the suite through existing isolation."""

    root = root.resolve()
    registry = load_registry(root)
    suite = resolve_suite(registry, suite_id)
    resolved_tier = _validate_verification_tier(
        suite["verification_tier"],
        label=f"suite {suite_id} verification_tier",
    )
    if require_tier is not None:
        required_tier = _validate_verification_tier(
            require_tier,
            label="required verification tier",
        )
        if resolved_tier != required_tier:
            raise SuiteError(
                f"suite {suite_id} verification tier {resolved_tier} "
                f"does not match required tier {required_tier}"
            )

    if os.environ.get(ISOLATION_ENV) == "1":
        return execute_registered_suite(
            root=root,
            suite_id=suite_id,
            require_tier=require_tier,
        )

    previous_binding = os.environ.get(SUITE_BINDING_ENV)
    os.environ[SUITE_BINDING_ENV] = suite_id
    try:
        return run_isolated_check(
            root=root,
            target="validation-suite",
            module_root=module_root,
            keep_workspace=keep_workspace,
        )
    finally:
        if previous_binding is None:
            os.environ.pop(SUITE_BINDING_ENV, None)
        else:
            os.environ[SUITE_BINDING_ENV] = previous_binding


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--module-root", default=None)
    parser.add_argument("--keep-workspace", action="store_true")
    parser.add_argument("--require-tier", choices=sorted(ALLOWED_VERIFICATION_TIERS))
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    module_root = _resolve_module_root(root, args.module_root)

    try:
        return run_suite(
            root=root,
            suite_id=args.suite,
            module_root=module_root,
            keep_workspace=args.keep_workspace,
            require_tier=args.require_tier,
        )
    except (SuiteError, IsolationError) as exc:
        print(f"VALIDATION_SUITE=FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
