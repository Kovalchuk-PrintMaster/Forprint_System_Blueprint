#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = Path("coordination/standards/automation/assistant_handoff_v2_result_contract_v0_1.yaml")
RUNTIME = Path("scripts/coordination/assistant_handoff_v2_result_v0_1.py")
S2_RUNTIME = Path("scripts/coordination/assistant_handoff_v2_runtime_v0_1.py")

RESULT_FIELDS = [
    "schema_version",
    "handoff_manifest_sha256",
    "attempt_id",
    "status",
    "changed_paths",
    "validation_evidence",
    "self_repair_attempts",
    "resume_coordinates",
    "unresolved_findings",
]


def fail(message: str) -> int:
    print(f"ERROR={message}")
    print("ASSISTANT_HANDOFF_V2_RESULT_CONTRACT_VALIDATION=FAIL")
    return 1


def load_runtime(root: Path) -> Any:
    path = root / RUNTIME
    spec = importlib.util.spec_from_file_location(
        "forprint_assistant_handoff_v2_result_validator",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load result runtime")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sample_result(runtime: Any, digest: str) -> dict[str, Any]:
    return {
        "schema_version": runtime.RESULT_SCHEMA_VERSION,
        "handoff_manifest_sha256": digest,
        "attempt_id": "attempt-s3-validator-001",
        "status": "PASS",
        "changed_paths": ["a.txt"],
        "validation_evidence": [{"name": "pytest", "result": "PASS"}],
        "self_repair_attempts": [],
        "resume_coordinates": {"step": "return-result"},
        "unresolved_findings": [],
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
    if contract.get("schema_version") != "forprint_assistant_handoff_v2_result_contract_v0_1":
        return fail("schema_version")
    if contract.get("implementation_slice") != "CF-08/S3":
        return fail("implementation_slice")

    envelope = contract.get("result_envelope")
    if not isinstance(envelope, dict):
        return fail("result_envelope")
    if envelope.get("exact_fields") != RESULT_FIELDS:
        return fail("exact result fields")
    if envelope.get("aliases_allowed") is not False:
        return fail("aliases")
    if envelope.get("additional_fields_allowed") is not False:
        return fail("additional fields")

    repair = contract.get("bounded_self_repair")
    if not isinstance(repair, dict):
        return fail("bounded_self_repair")
    required_repair = {
        "local_only": True,
        "authority_widening": False,
        "project_source_writes": False,
        "manifest_hash_rewrite_allowed": False,
        "attempt_id_rewrite_allowed": False,
        "field_alias_repair_allowed": False,
        "max_attempts_hard_ceiling": 3,
    }
    for key, value in required_repair.items():
        if repair.get(key) != value:
            return fail(f"bounded_self_repair.{key}")

    runtime = load_runtime(root)
    digest = "a" * 64
    manifest = {
        "handoff_manifest_sha256": digest,
        "expected_result_schema_revision": "0.1.0",
    }
    valid = sample_result(runtime, digest)
    errors = runtime.validate_result_envelope(valid, manifest, root=root)
    if errors:
        return fail(f"valid sample rejected: {errors}")

    missing = dict(valid)
    missing.pop("status")
    if not any(
        item["code"] == "MISSING_FIELDS"
        for item in runtime.validate_result_envelope(
            missing,
            manifest,
            root=root,
        )
    ):
        return fail("missing field did not fail closed")

    mismatch = dict(valid)
    mismatch["handoff_manifest_sha256"] = "b" * 64
    if not any(
        item["code"] == "RESULT_MANIFEST_BINDING_MISMATCH"
        for item in runtime.validate_result_envelope(
            mismatch,
            manifest,
            root=root,
        )
    ):
        return fail("manifest mismatch did not fail closed")

    duplicate = sample_result(runtime, digest)
    duplicate["changed_paths"] = ["a.txt", "a.txt"]
    repaired = runtime.validate_with_bounded_self_repair(
        duplicate,
        manifest,
        root=root,
        max_self_repair_attempts=1,
    )
    if not repaired["valid"] or repaired["repair_attempt_count"] != 1:
        return fail("bounded duplicate-path repair")
    if repaired["result"]["changed_paths"] != ["a.txt"]:
        return fail("duplicate-path repair output")
    if not repaired["result"]["self_repair_attempts"]:
        return fail("repair attempt not recorded")

    s2_source = (root / S2_RUNTIME).read_text(encoding="utf-8")
    for token in (
        "def validate_result_for_return(",
        '"exact_result_validation_implemented_s3": True',
        '"bounded_self_repair_execution_implemented_s3": True',
        '"exact_result_validation_deferred_to_s3": False',
        '"bounded_self_repair_execution_deferred_to_s3": False',
    ):
        if token not in s2_source:
            return fail(f"S2 runtime integration token missing: {token}")

    print("ASSISTANT_HANDOFF_V2_RESULT_CONTRACT=PASS")
    print("EXACT_RESULT_FIELDS=true")
    print("ALIASES_ALLOWED=false")
    print("MANIFEST_HASH_REWRITE_ALLOWED=false")
    print("ATTEMPT_ID_REWRITE_ALLOWED=false")
    print("SAFE_REPAIR_CODES=DEDUPLICATE_IDENTICAL_CHANGED_PATHS")
    print("MAX_SELF_REPAIR_ATTEMPTS=3")
    print("PROJECT_SOURCE_WRITES=false")
    print("DISPATCH_AUTHORITY=false")
    print("CENTRAL_RETRY_ORCHESTRATION=false")
    print("CF09_DISPATCHER_DEFERRED=true")
    print("ASSISTANT_HANDOFF_V2_RESULT_CONTRACT_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
