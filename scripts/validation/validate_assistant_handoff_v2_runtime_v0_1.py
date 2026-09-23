#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = Path("coordination/standards/automation/assistant_handoff_v2_runtime_contract_v0_1.yaml")
RUNTIME = Path("scripts/coordination/assistant_handoff_v2_runtime_v0_1.py")
S1 = Path("coordination/standards/automation/assistant_handoff_v2_contract_v0_1.yaml")


def fail(message: str) -> int:
    print(f"ERROR={message}")
    print("ASSISTANT_HANDOFF_V2_RUNTIME_VALIDATION=FAIL")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root).resolve()
    for rel in (CONTRACT, RUNTIME, S1):
        if not (root / rel).is_file():
            return fail(f"missing: {rel}")
    contract = yaml.safe_load((root / CONTRACT).read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        return fail("runtime contract must be mapping")
    if contract.get("schema_version") != "forprint_assistant_handoff_v2_runtime_contract_v0_1":
        return fail("schema_version")
    if contract.get("implementation_slice") != "CF-08/S2":
        return fail("implementation_slice")
    architecture = contract.get("architecture")
    if (
        not isinstance(architecture, dict)
        or architecture.get("parallel_framework") is not False
        or architecture.get("adapter_delegates_to_existing_builders") is not True
    ):
        return fail("architecture")
    authority = contract.get("authority")
    if not isinstance(authority, dict) or any(
        authority.get(k) is not False
        for k in (
            "grants_execution_authority",
            "grants_dispatch_authority",
            "grants_release_authority",
            "grants_cross_repository_write_authority",
        )
    ):
        return fail("authority widening")
    if set(contract.get("launch_modes", {})) != {"PROJECT_ONBOARD", "TASK_EXECUTION"}:
        return fail("launch modes")
    source = (root / RUNTIME).read_text(encoding="utf-8")
    for token in (
        "HANDOFF_V1_PATH",
        "HANDOFF_V1_SPEC = importlib.util.spec_from_file_location",
        "HANDOFF_V1_SPEC.loader.exec_module(handoff_v1)",
        "build_context_bundle.py --task-context",
        "TASK_EXECUTION requires --front",
        "TASK_EXECUTION requires --profile-id",
        "dispatch_authority_granted",
        "_manifest_hash",
    ):
        if token not in source:
            return fail(f"runtime token missing: {token}")
    py = root / ".venv_blueprint/bin/python"
    cp = subprocess.run(
        [
            str(py),
            str(root / RUNTIME),
            "--root",
            str(root),
            "--launch-mode",
            "PROJECT_ONBOARD",
            "--no-write",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=1800,
    )
    if (
        cp.returncode
        or "ASSISTANT_HANDOFF_V2_RUNTIME=PASS" not in cp.stdout
        or "DISPATCH_AUTHORITY_GRANTED=false" not in cp.stdout
    ):
        print(cp.stdout)
        return fail("PROJECT_ONBOARD runtime dry-run")
    task = subprocess.run(
        [
            str(py),
            str(root / RUNTIME),
            "--root",
            str(root),
            "--launch-mode",
            "TASK_EXECUTION",
            "--no-write",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=300,
    )
    if task.returncode == 0 or "TASK_EXECUTION requires --front" not in task.stdout:
        print(task.stdout)
        return fail("TASK_EXECUTION fail-closed")
    print("ASSISTANT_HANDOFF_V2_RUNTIME_CONTRACT=PASS")
    print("PROJECT_ONBOARD_DELEGATES_HANDOFF_V1=true")
    print("TASK_EXECUTION_DELEGATES_TASK_CONTEXT=true")
    print("PARALLEL_FRAMEWORK=false")
    print("DISPATCH_AUTHORITY=false")
    print("CF09_DISPATCHER_DEFERRED=true")
    print("ASSISTANT_HANDOFF_V2_RUNTIME_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
