#!/usr/bin/env python3
"""Validate the ForPrint execution progress visibility foundation."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT / "coordination/standards/automation/execution_progress_visibility_contract_v0_1.yaml"
)
AGENTS = ROOT / "AGENTS.md"
MAKEFILE = ROOT / "Makefile"
HELPER = ROOT / "scripts/coordination/execution_progress.py"


def fail(message: str) -> int:
    print(f"EXECUTION_PROGRESS_VISIBILITY=FAIL {message}")
    return 1


def main() -> int:
    for path in (CONTRACT, AGENTS, MAKEFILE, HELPER):
        if not path.is_file():
            return fail(f"missing={path.relative_to(ROOT)}")

    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    if data.get("status") != "current_standard":
        return fail("contract_status")
    defaults = data.get("defaults", {})
    if defaults.get("progress_mode") != "always":
        return fail("default_progress_mode")
    if int(defaults.get("heartbeat_seconds", 0)) != 15:
        return fail("default_heartbeat")
    if defaults.get("child_output") != "failures":
        return fail("default_child_output")

    agents = AGENTS.read_text(encoding="utf-8")
    if "<!-- FORPRINT_EXECUTION_PROGRESS_VISIBILITY_START -->" not in agents:
        return fail("agents_marker")
    if "execution_progress_visibility_contract_v0_1.yaml" not in agents:
        return fail("agents_contract_reference")

    makefile = MAKEFILE.read_text(encoding="utf-8")
    required_make_tokens = (
        "FORPRINT_PROGRESS ?= always",
        "FORPRINT_PROGRESS_HEARTBEAT_SECONDS ?= 15",
        "FORPRINT_PROGRESS_CHILD_OUTPUT ?= failures",
        ".PHONY: execution-progress-check",
        ".PHONY: execution-progress-demo",
    )
    for token in required_make_tokens:
        if token not in makefile:
            return fail(f"makefile_token={token}")

    spec = importlib.util.spec_from_file_location(
        "forprint_execution_progress_contract_check",
        HELPER,
    )
    if spec is None or spec.loader is None:
        return fail("helper_import_spec")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves annotation/module metadata through sys.modules.
    # A module created with module_from_spec() is not registered automatically.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    config = module.ProgressConfig()
    if config.mode != "always":
        return fail("helper_default_mode")
    if config.heartbeat_seconds != 15.0:
        return fail("helper_default_heartbeat")
    if config.child_output != "failures":
        return fail("helper_default_child_output")

    print("EXECUTION_PROGRESS_VISIBILITY=PASS")
    print("DEFAULT_PROGRESS_MODE=always")
    print("DEFAULT_HEARTBEAT_SECONDS=15")
    print("DEFAULT_CHILD_OUTPUT=failures")
    print("PROGRESS_STREAM=stderr")
    print("MACHINE_SUMMARY_STREAM=stdout")
    print("ASSISTANT_POLICY_BOUND=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
