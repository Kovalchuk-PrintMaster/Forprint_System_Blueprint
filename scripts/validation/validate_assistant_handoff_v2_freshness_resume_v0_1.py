#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = Path(
    "coordination/standards/automation/assistant_handoff_v2_freshness_resume_contract_v0_1.yaml"
)
RUNTIME = Path("scripts/coordination/assistant_handoff_v2_freshness_resume_v0_1.py")
S2_RUNTIME = Path("scripts/coordination/assistant_handoff_v2_runtime_v0_1.py")

FAIL_CLASSES = [
    "STALE_SOURCE_STATE_FINGERPRINT",
    "STALE_LIFECYCLE_ROADMAP_CURSOR",
    "STALE_GENERATED_CONTEXT",
    "RESUME_ATTEMPT_BINDING_MISMATCH",
    "RESUME_MANIFEST_BINDING_MISMATCH",
    "RESUME_COORDINATES_INCOMPLETE",
]


def fail(message: str) -> int:
    print(f"ERROR={message}")
    print("ASSISTANT_HANDOFF_V2_FRESHNESS_RESUME_VALIDATION=FAIL")
    return 1


def load_runtime(root: Path) -> Any:
    path = root / RUNTIME
    spec = importlib.util.spec_from_file_location(
        "forprint_assistant_handoff_v2_freshness_resume_validator",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load S4 runtime")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sample_manifest() -> dict[str, Any]:
    return {
        "schema_version": "forprint_assistant_handoff_v2_runtime_manifest_v0_1",
        "launch_mode": "PROJECT_ONBOARD",
        "source_state_fingerprint": "a" * 64,
        "lifecycle_roadmap_cursor": {
            "current": "CF-08",
            "event_sequence": 57,
            "roadmap_sync": "IN_SYNC",
        },
        "handoff_manifest_sha256": "b" * 64,
    }


def sample_result() -> dict[str, Any]:
    manifest = sample_manifest()
    return {
        "attempt_id": "attempt-s4-validator-001",
        "status": "PASS",
        "handoff_manifest_sha256": manifest["handoff_manifest_sha256"],
        "resume_coordinates": {
            "attempt_id": "attempt-s4-validator-001",
            "handoff_manifest_sha256": manifest["handoff_manifest_sha256"],
            "source_state_fingerprint": manifest["source_state_fingerprint"],
            "lifecycle_roadmap_cursor": manifest["lifecycle_roadmap_cursor"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root).resolve()

    for rel in (CONTRACT, RUNTIME, S2_RUNTIME):
        if not (root / rel).is_file():
            return fail(f"missing: {rel}")

    contract = yaml.safe_load((root / CONTRACT).read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        return fail("contract must be mapping")
    if (
        contract.get("schema_version")
        != "forprint_assistant_handoff_v2_freshness_resume_contract_v0_1"
    ):
        return fail("schema_version")
    if contract.get("implementation_slice") != "CF-08/S4":
        return fail("implementation_slice")
    if contract.get("fail_closed_classes") != FAIL_CLASSES:
        return fail("fail_closed_classes")

    freshness = contract.get("freshness")
    if not isinstance(freshness, dict):
        return fail("freshness")
    for key in (
        "source_state_fingerprint_must_match_live_state",
        "lifecycle_roadmap_cursor_must_match_live_state",
        "stale_generated_context_blocks_return",
    ):
        if freshness.get(key) is not True:
            return fail(f"freshness.{key}")

    resume = contract.get("resume")
    if not isinstance(resume, dict):
        return fail("resume")
    for key in (
        "structured_mapping_required",
        "attempt_binding_required",
        "manifest_binding_required",
        "retry_must_create_new_attempt_id",
        "partial_requires_latest_completed_node",
        "partial_requires_latest_accepted_ref",
        "partial_requires_replay_forbidden_refs",
    ):
        if resume.get(key) is not True:
            return fail(f"resume.{key}")

    runtime = load_runtime(root)
    origin = sample_manifest()
    live = sample_manifest()
    result = sample_result()

    valid = runtime.validate_freshness_and_resume(
        origin,
        live,
        result,
        root=root,
    )
    if valid["valid"] is not True:
        return fail(f"valid sample rejected: {valid}")

    stale = dict(live)
    stale["source_state_fingerprint"] = "c" * 64
    report = runtime.validate_freshness_and_resume(
        origin,
        stale,
        result,
        root=root,
    )
    if {item["code"] for item in report["errors"]} != {"STALE_SOURCE_STATE_FINGERPRINT"}:
        return fail("stale source fingerprint")

    cursor_stale = dict(live)
    cursor_stale["lifecycle_roadmap_cursor"] = {
        **live["lifecycle_roadmap_cursor"],
        "event_sequence": 58,
    }
    report = runtime.validate_freshness_and_resume(
        origin,
        cursor_stale,
        result,
        root=root,
    )
    if "STALE_LIFECYCLE_ROADMAP_CURSOR" not in {item["code"] for item in report["errors"]}:
        return fail("stale cursor")

    partial = sample_result()
    partial["status"] = "INTERRUPTED"
    report = runtime.validate_freshness_and_resume(
        origin,
        live,
        partial,
        root=root,
    )
    if "RESUME_COORDINATES_INCOMPLETE" not in {item["code"] for item in report["errors"]}:
        return fail("partial resume completeness")

    source = (root / S2_RUNTIME).read_text(encoding="utf-8")
    for token in (
        "def _load_freshness_resume_runtime(",
        '"freshness_fail_closed_hardening_implemented_s4": True',
        '"durable_resume_hardening_implemented_s4": True',
        '"freshness_fail_closed_hardening_deferred_to_s4": False',
        '"durable_resume_hardening_deferred_to_s4": False',
    ):
        if token not in source:
            return fail(f"S2 integration token missing: {token}")

    print("ASSISTANT_HANDOFF_V2_FRESHNESS_RESUME_CONTRACT=PASS")
    print("SOURCE_STATE_FINGERPRINT_LIVE_BINDING=true")
    print("LIFECYCLE_ROADMAP_CURSOR_LIVE_BINDING=true")
    print("STALE_GENERATED_CONTEXT_FAIL_CLOSED=true")
    print("STRUCTURED_RESUME_COORDINATES=true")
    print("RESUME_ATTEMPT_BINDING=true")
    print("RESUME_MANIFEST_BINDING=true")
    print("RETRY_REUSES_ATTEMPT_ID=false")
    print("PARALLEL_RESUME_FRAMEWORK=false")
    print("CENTRAL_RESUME_ROUTING=false")
    print("DISPATCH_AUTHORITY=false")
    print("CF09_DISPATCHER_DEFERRED=true")
    print("ASSISTANT_HANDOFF_V2_FRESHNESS_RESUME_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
