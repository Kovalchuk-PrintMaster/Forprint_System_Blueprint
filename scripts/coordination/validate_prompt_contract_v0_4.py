from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

EXPECTED_SCHEMA = "module_prompt_contract_v0_4"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return data


def canonical_payload_sha256(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    integrity = payload.get("integrity")
    if not isinstance(integrity, dict):
        return ""
    integrity.pop("payload_sha256", None)
    raw = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in values:
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return sorted(dupes)


def obligation_ids(items: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(items, list):
        errors.append(f"{label} must be a list")
        return []
    result: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}] must be a mapping")
            continue
        obligation_id = item.get("obligation_id")
        if not isinstance(obligation_id, str) or not obligation_id:
            errors.append(f"{label}[{index}] obligation_id missing")
            continue
        result.append(obligation_id)
    return result


def validate_contract(
    root: Path,
    contract_path: Path,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    contract = data if data is not None else load_yaml(contract_path)

    if contract.get("schema_version") != EXPECTED_SCHEMA:
        errors.append("schema_version mismatch")

    metadata = contract.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("metadata missing")
        metadata = {}

    contract_id = metadata.get("contract_id")
    module_id = metadata.get("module_id")
    prompt_id = metadata.get("prompt_id")
    status = metadata.get("status")

    for field, value in (
        ("contract_id", contract_id),
        ("module_id", module_id),
        ("prompt_id", prompt_id),
    ):
        if not isinstance(value, str) or not value:
            errors.append(f"metadata.{field} missing")

    if metadata.get("immutable") is not True:
        errors.append("metadata.immutable must be true")
    if status != "candidate_reference_only":
        errors.append("metadata.status must remain candidate_reference_only")

    if all(isinstance(value, str) and value for value in (module_id, prompt_id, contract_id)):
        expected = (
            root / "coordination/prompt_contracts" / module_id / prompt_id / f"{contract_id}.yaml"
        ).resolve()
        if contract_path.resolve() != expected:
            errors.append("immutable instance path mismatch")

    source = contract.get("source_prompt")
    if not isinstance(source, dict):
        errors.append("source_prompt missing")
        source = {}
    source_path_value = source.get("path")
    source_hash = source.get("sha256")
    if not isinstance(source_path_value, str) or not source_path_value:
        errors.append("source_prompt.path missing")
    else:
        source_path = root / source_path_value
        expected_snapshot = contract_path.parent / "source_prompt_snapshot.md"
        if source_path.resolve() != expected_snapshot.resolve():
            errors.append("source prompt snapshot path mismatch")
        if not source_path.is_file():
            errors.append("source prompt snapshot missing")
        elif not isinstance(source_hash, str) or len(source_hash) != 64:
            errors.append("source_prompt.sha256 invalid")
        else:
            actual = hashlib.sha256(source_path.read_bytes()).hexdigest()
            if actual != source_hash:
                errors.append("source prompt SHA-256 mismatch")

    origin_path = source.get("origin_path_at_capture")
    origin_hash = source.get("origin_sha256_at_capture")
    if not isinstance(origin_path, str) or not origin_path:
        errors.append("source_prompt.origin_path_at_capture missing")
    if not isinstance(origin_hash, str) or origin_hash != source_hash:
        errors.append("source_prompt.origin_sha256_at_capture mismatch")

    integrity = contract.get("integrity")
    if not isinstance(integrity, dict):
        errors.append("integrity missing")
        integrity = {}
    if integrity.get("algorithm") != "sha256":
        errors.append("integrity.algorithm must be sha256")
    expected_payload_hash = integrity.get("payload_sha256")
    if not isinstance(expected_payload_hash, str) or len(expected_payload_hash) != 64:
        errors.append("integrity.payload_sha256 invalid")
    elif canonical_payload_sha256(contract) != expected_payload_hash:
        errors.append("contract payload SHA-256 mismatch")

    source_ids = obligation_ids(contract.get("source_obligations"), "source_obligations", errors)
    implementation_ids = obligation_ids(
        contract.get("implementation_obligations"), "implementation_obligations", errors
    )
    verification_ids = obligation_ids(
        contract.get("verification_obligations"), "verification_obligations", errors
    )
    completion_ids = obligation_ids(
        contract.get("completion_evidence_obligations"), "completion_evidence_obligations", errors
    )

    all_ids = source_ids + implementation_ids + verification_ids + completion_ids
    duplicate_ids = duplicates(all_ids)
    if duplicate_ids:
        errors.append("duplicate obligation IDs: " + ",".join(duplicate_ids))

    target_ids = set(implementation_ids + verification_ids + completion_ids)
    source_by_id = {
        item.get("obligation_id"): item
        for item in contract.get("source_obligations", [])
        if isinstance(item, dict) and isinstance(item.get("obligation_id"), str)
    }

    ledger = contract.get("source_obligation_fidelity_ledger")
    if not isinstance(ledger, list):
        errors.append("source_obligation_fidelity_ledger must be a list")
        ledger = []

    mapped_source_ids: set[str] = set()
    for index, entry in enumerate(ledger):
        if not isinstance(entry, dict):
            errors.append(f"fidelity ledger entry {index} must be a mapping")
            continue
        source_id = entry.get("source_obligation_id")
        targets = entry.get("target_obligation_ids")
        if not isinstance(source_id, str) or source_id not in source_by_id:
            errors.append(f"unknown source obligation in mapping: {source_id}")
            continue
        if source_id in mapped_source_ids:
            errors.append(f"duplicate source mapping: {source_id}")
        mapped_source_ids.add(source_id)

        if not isinstance(targets, list) or not targets:
            errors.append(f"mapping targets missing for {source_id}")
            continue
        for target in targets:
            if not isinstance(target, str) or target not in target_ids:
                errors.append(f"unknown mapping target: {target}")

    required_source_ids = {
        source_id for source_id, item in source_by_id.items() if item.get("required") is True
    }
    unmapped = sorted(required_source_ids - mapped_source_ids)
    if unmapped:
        errors.append("required source obligations unmapped: " + ",".join(unmapped))

    semantic = contract.get("semantic_fidelity")
    if not isinstance(semantic, dict):
        errors.append("semantic_fidelity missing")
        semantic = {}
    if semantic.get("human_review_required") is not True:
        errors.append("human semantic fidelity review must be required")
    if semantic.get("execution_fingerprint_sufficient") is not False:
        errors.append("execution fingerprint must not be complete fidelity proof")

    promotion = contract.get("promotion")
    if not isinstance(promotion, dict):
        errors.append("promotion missing")
        promotion = {}
    if promotion.get("state") != "candidate_reference_only":
        errors.append("promotion.state must remain candidate_reference_only")
    if promotion.get("normal_acceptance_allowed") is not False:
        errors.append("normal_acceptance_allowed must remain false")
    if promotion.get("explicit_promotion_required") is not True:
        errors.append("explicit promotion gate missing")
    if promotion.get("promotion_performed") is not False:
        errors.append("STEP21 must not perform promotion")

    return {
        "schema_version": "prompt_contract_v0_4_validation_report_v0_1",
        "contract_path": str(contract_path.relative_to(root)),
        "result": "PASSED" if not errors else "FAILED",
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "source_obligations": len(source_ids),
            "implementation_obligations": len(implementation_ids),
            "verification_obligations": len(verification_ids),
            "completion_evidence_obligations": len(completion_ids),
            "fidelity_mappings": len(ledger),
        },
    }



# ---------------------------------------------------------------------------
# B1 v0.4.1 backward-compatible execution-baseline extension
# ---------------------------------------------------------------------------
B1_POLICY_SCHEMA = "module_execution_baseline_policy_v0_1"
B1_HEX40 = __import__("re").compile(r"^[0-9a-f]{40}$")
B1_HEX64 = __import__("re").compile(r"^[0-9a-f]{64}$")
B1_SAFE_ID = __import__("re").compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")


def _b1_non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _b1_safe_relative_path(value: Any) -> bool:
    if not _b1_non_empty(value):
        return False
    path = Path(str(value))
    return not path.is_absolute() and ".." not in path.parts


def _validate_b1_execution_baseline_policy(
    contract: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate optional B1 extension without invalidating historical v0.4 contracts."""

    policy = contract.get("execution_baseline_policy")
    if policy is None:
        return
    if not isinstance(policy, dict):
        errors.append("execution_baseline_policy must be a mapping")
        return

    if policy.get("schema_version") != B1_POLICY_SCHEMA:
        errors.append(
            "execution_baseline_policy.schema_version must be "
            + B1_POLICY_SCHEMA
        )

    release = policy.get("release_baseline")
    if not isinstance(release, dict):
        errors.append("execution_baseline_policy.release_baseline must be a mapping")
        release = {}

    for key in ("blueprint_commit", "module_commit"):
        value = release.get(key)
        if not isinstance(value, str) or B1_HEX40.fullmatch(value) is None:
            errors.append(
                f"execution_baseline_policy.release_baseline.{key} "
                "must be a full 40-character lowercase Git hash"
            )

    if not _b1_non_empty(release.get("module_branch")):
        errors.append(
            "execution_baseline_policy.release_baseline.module_branch missing"
        )

    authority = release.get("release_authority")
    if not isinstance(authority, dict):
        errors.append(
            "execution_baseline_policy.release_baseline.release_authority "
            "must be a mapping"
        )
        authority = {}

    if not _b1_safe_relative_path(authority.get("path")):
        errors.append(
            "execution_baseline_policy.release_baseline.release_authority.path "
            "must be a safe repository-relative path"
        )

    authority_sha = authority.get("sha256")
    if (
        not isinstance(authority_sha, str)
        or B1_HEX64.fullmatch(authority_sha) is None
    ):
        errors.append(
            "execution_baseline_policy.release_baseline.release_authority.sha256 "
            "must be a 64-character lowercase sha256"
        )

    if not _b1_non_empty(authority.get("hardening_release")):
        errors.append(
            "execution_baseline_policy.release_baseline.release_authority."
            "hardening_release missing"
        )

    required_inputs = policy.get("required_inputs")
    if not isinstance(required_inputs, list) or not required_inputs:
        errors.append(
            "execution_baseline_policy.required_inputs must be a non-empty list"
        )
        required_inputs = []

    seen_ids: set[str] = set()
    for index, item in enumerate(required_inputs):
        label = f"execution_baseline_policy.required_inputs[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be a mapping")
            continue

        input_id = item.get("input_id")
        if (
            not isinstance(input_id, str)
            or B1_SAFE_ID.fullmatch(input_id) is None
        ):
            errors.append(f"{label}.input_id must be a safe stable id")
        elif input_id in seen_ids:
            errors.append(f"{label}.input_id duplicate: {input_id}")
        else:
            seen_ids.add(input_id)

        if item.get("repository") not in {"blueprint", "module"}:
            errors.append(f"{label}.repository must be blueprint or module")

        if not _b1_safe_relative_path(item.get("path")):
            errors.append(f"{label}.path must be a safe repository-relative path")

        value = item.get("sha256")
        if not isinstance(value, str) or B1_HEX64.fullmatch(value) is None:
            errors.append(f"{label}.sha256 must be a 64-character lowercase sha256")

        if item.get("material") is not True:
            errors.append(f"{label}.material must be true")

    compatibility = policy.get("compatibility")
    if not isinstance(compatibility, dict):
        errors.append(
            "execution_baseline_policy.compatibility must be a mapping"
        )
        compatibility = {}

    required_true = (
        "allow_blueprint_forward_descendant",
        "allow_module_forward_descendant",
        "material_inputs_must_match",
        "require_clean_module_worktree",
        "require_module_upstream_synced",
    )
    for key in required_true:
        if compatibility.get(key) is not True:
            errors.append(
                f"execution_baseline_policy.compatibility.{key} must be true"
            )


_validate_contract_v0_4_without_b1 = validate_contract


def validate_contract(
    root: Path,
    contract_path: Path,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preserve v0.4 validation and add optional B1 execution-baseline validation."""

    report = _validate_contract_v0_4_without_b1(root, contract_path, data)
    contract = data if data is not None else load_yaml(contract_path)
    _validate_b1_execution_baseline_policy(contract, report["errors"])
    report["result"] = "PASSED" if not report["errors"] else "FAILED"
    # Backward-compatibility invariant: keep the stable v0.4
    # validation-report summary shape unchanged. B1 validation
    # affects only result/errors, not legacy consumer-visible keys.
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--output-format", choices=("text", "yaml"), default="text")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    contract_path = (root / args.contract).resolve()
    report = validate_contract(root, contract_path)

    if args.output_format == "yaml":
        print(yaml.safe_dump(report, sort_keys=False, allow_unicode=True).rstrip())
    else:
        print("ForPrint Prompt Contract v0.4 validation")
        print(f"contract: {report['contract_path']}")
        print(f"result: {report['result']}")
        print(f"errors: {','.join(report['errors']) or '-'}")
        print(f"warnings: {','.join(report['warnings']) or '-'}")
        for key, value in report["summary"].items():
            print(f"{key}: {value}")

    return 0 if report["result"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
