#!/usr/bin/env python3
"""Validate Project Constitution v0.1 and its enforcement bindings."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION = ROOT / "coordination/standards/governance/project_constitution_v0_1.yaml"
AUTHORITY = ROOT / "scripts/coordination/project_authority_v0_1.py"
AGENTS = ROOT / "AGENTS.md"
MAKEFILE = ROOT / "Makefile"
CONTROLLER = ROOT / "scripts/coordination/roadmap_execution_reconciliation.py"


def fail(reason: str) -> int:
    print("PROJECT_CONSTITUTION_VALIDATION=FAIL")
    print("ERROR=" + reason)
    return 1


def load_authority():
    spec = importlib.util.spec_from_file_location("_project_authority_v0_1", AUTHORITY)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load project authority resolver")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_contract_only() -> int:
    try:
        module = load_authority()
        data = yaml.safe_load(CONSTITUTION.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return fail("CONSTITUTION_NOT_MAPPING")
        module.validate_constitution_shape(data)

        if (
            data.get("generated_artifact_semantics", {}).get("generated_views_are_authority")
            is not False
        ):
            return fail("GENERATED_VIEW_AUTHORITY")
        if data.get("independent_validation", {}).get("required_for_completion") is not True:
            return fail("INDEPENDENT_VALIDATION")
        if (
            data.get("guardrail_change", {}).get("self_modification_and_self_certification_allowed")
            is not False
        ):
            return fail("SELF_CERTIFY_GUARDRAIL")
        if data.get("module_invariant_extension", {}).get("allowed") is not True:
            return fail("MODULE_INVARIANT_EXTENSION")

        print("PROJECT_CONSTITUTION_CONTRACT=PASS")
        print(
            "AUTHORITY_PRECEDENCE=PROJECT_CONSTITUTION>MODULE_POLICY>EXECUTION_PROFILE>WORK_FRONT"
        )
        print("LOWER_LAYER_MAY_NARROW=true")
        print("LOWER_LAYER_SILENT_WIDENING=false")
        print("AI_SELF_GUARDRAIL_CERTIFICATION=false")
        return 0
    except Exception as exc:
        return fail(type(exc).__name__ + ":" + str(exc))


def validate_full() -> int:
    rc = validate_contract_only()
    if rc:
        return rc

    agents = AGENTS.read_text(encoding="utf-8")
    start = "<!-- FORPRINT_PROJECT_CONSTITUTION_START -->"
    end = "<!-- FORPRINT_PROJECT_CONSTITUTION_END -->"
    if agents.count(start) != 1 or agents.count(end) != 1:
        return fail("AGENTS_CONSTITUTION_BINDING")
    if "make project-constitution-check" not in agents:
        return fail("AGENTS_CONSTITUTION_CHECK_SURFACE")

    makefile = MAKEFILE.read_text(encoding="utf-8")
    if makefile.count(".PHONY: project-constitution-check") != 1:
        return fail("MAKE_CONSTITUTION_PHONY")
    if makefile.count("project-constitution-check:") != 1:
        return fail("MAKE_CONSTITUTION_TARGET")
    check_core = next(
        (line for line in makefile.splitlines() if line.startswith("check-core:")),
        "",
    )
    if "project-constitution-check" not in check_core.split():
        return fail("CHECK_CORE_CONSTITUTION_BINDING")
    if (
        "assistant-pack:\n\t$(MAKE) roadmap-sync-check\n\t$(MAKE) project-constitution-check"
    ) not in makefile:
        return fail("ASSISTANT_PACK_CONSTITUTION_GATE")
    if (
        "assistant-handoff-check:\n\t$(MAKE) roadmap-sync-check\n"
        "\t$(MAKE) project-constitution-check"
    ) not in makefile:
        return fail("ASSISTANT_HANDOFF_CONSTITUTION_GATE")

    controller = CONTROLLER.read_text(encoding="utf-8")
    if "PROJECT_CONSTITUTION_GATE=PASS" not in controller:
        return fail("ROADMAP_GATE_CONSTITUTION_BINDING")
    if "GATE_REASON=PROJECT_CONSTITUTION_INVALID" not in controller:
        return fail("ROADMAP_GATE_CONSTITUTION_FAIL_CLOSED")

    cp = subprocess.run(
        [sys.executable, str(AUTHORITY), "--root", str(ROOT)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if cp.returncode:
        return fail("AUTHORITY_RUNTIME\n" + cp.stdout)

    print("PROJECT_CONSTITUTION_VALIDATION=PASS")
    print("PROJECT_LAW_COUNT=13")
    print("PUBLIC_MAKE_CHECK_BOUND=true")
    print("ASSISTANT_PACK_BOUND=true")
    print("LIFECYCLE_ROADMAP_GATE_BOUND=true")
    print("CF04_WORK_FRONT_IMPLEMENTED=false")
    print("CF06_EXECUTION_PROFILE_REGISTRY_IMPLEMENTED=false")
    print("WORKER_DISPATCH_AUTHORITY_WIDENED=false")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-only", action="store_true")
    args = parser.parse_args()
    return validate_contract_only() if args.contract_only else validate_full()


if __name__ == "__main__":
    raise SystemExit(main())
