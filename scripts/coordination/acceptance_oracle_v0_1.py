from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.validate_completion_packet_v0_4 import validate_packet
from scripts.coordination.validate_prompt_contract_v0_4 import validate_contract

ORACLE_SCHEMA = "blueprint_acceptance_oracle_v0_1"
BLUEPRINT_OWNER = "forprint_system_blueprint"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
RESULTS = {"PASS", "FAIL", "NOT_EVALUATED"}
VERIFICATION_KINDS = {"command", "query", "artifact", "semantic_review"}
CONTRACT_CATEGORIES = (
    "implementation_obligations",
    "verification_obligations",
    "completion_evidence_obligations",
)
EVIDENCE_BASIS_FIELDS = (
    "event_sha256",
    "packet_sha256",
    "discovery_fingerprint_sha256",
)


class AcceptanceOracleError(RuntimeError):
    pass


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise AcceptanceOracleError(f"cannot load YAML: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise AcceptanceOracleError(f"expected YAML mapping: {path}")
    return data


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _candidate_evidence_basis(candidate: dict[str, Any]) -> dict[str, str]:
    basis: dict[str, str] = {}
    for field in EVIDENCE_BASIS_FIELDS:
        value = candidate.get(field)
        if not isinstance(value, str) or not HEX64.fullmatch(value):
            raise AcceptanceOracleError(
                f"review candidate {field} must be a lowercase SHA-256 "
                "for oracle-gated ACCEPT"
            )
        basis[field] = value
    return basis


def acceptance_evaluation_request_fingerprint(
    evaluation: Any,
    candidate: dict[str, Any],
) -> str | None:
    if evaluation is None:
        return None
    payload = {
        "candidate_evidence_basis": {
            field: candidate.get(field)
            for field in EVIDENCE_BASIS_FIELDS
        },
        "acceptance_oracle_evaluation": evaluation,
    }
    try:
        return _canonical_sha256(payload)
    except (TypeError, ValueError) as exc:
        raise AcceptanceOracleError(
            "acceptance oracle evaluation must be canonically JSON-serializable"
        ) from exc


def _safe_contained_path(
    root: Path,
    relative: str,
    *,
    parent: str,
    label: str,
) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise AcceptanceOracleError(f"{label} must be a non-empty path")
    candidate = (root / relative).resolve()
    parent_path = (root / parent).resolve()
    try:
        candidate.relative_to(parent_path)
    except ValueError as exc:
        raise AcceptanceOracleError(
            f"{label} must stay under {parent}/"
        ) from exc
    return candidate


def validate_roadmap_acceptance_binding(
    step: dict[str, Any],
    *,
    prefix: str,
) -> list[str]:
    acceptance = step.get("acceptance")
    if acceptance is None:
        return []
    if not isinstance(acceptance, dict):
        return [f"{prefix}.acceptance must be a mapping"]

    errors: list[str] = []
    required = acceptance.get("oracle_required")
    if not isinstance(required, bool):
        return [f"{prefix}.acceptance.oracle_required must be a boolean"]

    oracle_path = acceptance.get("oracle_path")
    oracle_sha = acceptance.get("oracle_sha256")
    if required:
        if not isinstance(oracle_path, str) or not oracle_path.strip():
            errors.append(
                f"{prefix}.acceptance.oracle_path must be a non-empty string "
                "when oracle_required=true"
            )
        if not isinstance(oracle_sha, str) or not HEX64.fullmatch(oracle_sha):
            errors.append(
                f"{prefix}.acceptance.oracle_sha256 must be a lowercase SHA-256 "
                "when oracle_required=true"
            )
    elif oracle_path is not None or oracle_sha is not None:
        errors.append(
            f"{prefix}.acceptance oracle_path/oracle_sha256 require "
            "oracle_required=true"
        )
    return errors


def _validated_contract_obligation_ids(
    contract: dict[str, Any],
) -> set[str]:
    return {
        item["obligation_id"]
        for category in CONTRACT_CATEGORIES
        for item in contract[category]
    }


def _validate_contract_binding(
    root: Path,
    oracle: dict[str, Any],
    *,
    module_id: str,
    prompt_id: str,
) -> tuple[str, str, set[str]]:
    source = oracle.get("source_prompt_contract")
    if not isinstance(source, dict):
        raise AcceptanceOracleError(
            "oracle source_prompt_contract must be a mapping"
        )

    contract_rel = source.get("path")
    contract_sha = source.get("sha256")
    if not isinstance(contract_sha, str) or not HEX64.fullmatch(contract_sha):
        raise AcceptanceOracleError(
            "source_prompt_contract.sha256 must be a lowercase SHA-256"
        )

    contract_path = _safe_contained_path(
        root,
        contract_rel,
        parent="coordination/prompt_contracts",
        label="source_prompt_contract.path",
    )
    if not contract_path.is_file():
        raise AcceptanceOracleError(
            f"source prompt contract missing: {contract_rel}"
        )
    actual_sha = file_sha256(contract_path)
    if actual_sha != contract_sha:
        raise AcceptanceOracleError(
            "source prompt contract SHA mismatch: "
            f"expected={contract_sha} actual={actual_sha}"
        )

    contract = load_yaml(contract_path)
    try:
        report = validate_contract(root, contract_path, contract)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AcceptanceOracleError(
            f"source prompt contract canonical validation errored: {exc}"
        ) from exc
    if report.get("result") != "PASSED":
        errors = report.get("errors")
        if not isinstance(errors, list):
            errors = ["unknown canonical validator failure"]
        raise AcceptanceOracleError(
            "source prompt contract canonical validation failed: "
            + "; ".join(str(item) for item in errors)
        )

    metadata = contract["metadata"]
    if metadata.get("module_id") != module_id:
        raise AcceptanceOracleError(
            "source prompt contract module_id does not match oracle subject"
        )
    if metadata.get("prompt_id") != prompt_id:
        raise AcceptanceOracleError(
            "source prompt contract prompt_id does not match oracle subject"
        )

    return (
        contract_rel,
        contract_sha,
        _validated_contract_obligation_ids(contract),
    )


def _substep_ids(step: dict[str, Any]) -> set[str]:
    values = step.get("substeps")
    if not isinstance(values, list):
        return set()
    return {
        item["substep_id"]
        for item in values
        if isinstance(item, dict)
        and isinstance(item.get("substep_id"), str)
        and item.get("substep_id")
    }


def load_and_validate_oracle(
    root: Path,
    *,
    oracle_path: str,
    oracle_sha256: str,
    module_id: str,
    prompt_id: str,
    step_id: str,
    roadmap_step: dict[str, Any],
) -> dict[str, Any]:
    root = root.resolve()
    if not HEX64.fullmatch(oracle_sha256):
        raise AcceptanceOracleError(
            "roadmap acceptance oracle_sha256 must be a lowercase SHA-256"
        )

    path = _safe_contained_path(
        root,
        oracle_path,
        parent="coordination/acceptance_oracles",
        label="acceptance.oracle_path",
    )
    if not path.is_file():
        raise AcceptanceOracleError(
            f"acceptance oracle file missing: {oracle_path}"
        )
    actual_sha = file_sha256(path)
    if actual_sha != oracle_sha256:
        raise AcceptanceOracleError(
            "acceptance oracle SHA mismatch: "
            f"expected={oracle_sha256} actual={actual_sha}"
        )

    oracle = load_yaml(path)
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        raise AcceptanceOracleError(
            f"acceptance oracle schema must be {ORACLE_SCHEMA}"
        )

    metadata = oracle.get("metadata")
    if not isinstance(metadata, dict):
        raise AcceptanceOracleError("acceptance oracle metadata must be a mapping")
    if metadata.get("owner") != BLUEPRINT_OWNER:
        raise AcceptanceOracleError(
            f"acceptance oracle metadata.owner must equal {BLUEPRINT_OWNER!r}"
        )
    if metadata.get("immutable") is not True:
        raise AcceptanceOracleError(
            "acceptance oracle metadata.immutable must be true"
        )
    for field, expected in {
        "module_id": module_id,
        "prompt_id": prompt_id,
        "step_id": step_id,
    }.items():
        if metadata.get(field) != expected:
            raise AcceptanceOracleError(
                f"acceptance oracle metadata.{field} must equal {expected!r}"
            )

    oracle_id = metadata.get("oracle_id")
    if (
        not isinstance(oracle_id, str)
        or not oracle_id
        or not SAFE_ID.fullmatch(oracle_id)
    ):
        raise AcceptanceOracleError(
            "acceptance oracle metadata.oracle_id must be a safe non-empty id"
        )

    contract_rel, contract_sha, known_refs = _validate_contract_binding(
        root,
        oracle,
        module_id=module_id,
        prompt_id=prompt_id,
    )

    criteria = oracle.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise AcceptanceOracleError(
            "acceptance oracle criteria must be a non-empty list"
        )

    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    substeps = _substep_ids(roadmap_step)

    for index, criterion in enumerate(criteria, start=1):
        prefix = f"criteria[{index}]"
        if not isinstance(criterion, dict):
            raise AcceptanceOracleError(f"{prefix} must be a mapping")

        criterion_id = criterion.get("criterion_id")
        if (
            not isinstance(criterion_id, str)
            or not criterion_id
            or not SAFE_ID.fullmatch(criterion_id)
        ):
            raise AcceptanceOracleError(
                f"{prefix}.criterion_id must be a safe non-empty id"
            )
        if criterion_id in seen:
            raise AcceptanceOracleError(
                f"duplicate acceptance criterion_id: {criterion_id}"
            )
        seen.add(criterion_id)

        if criterion.get("step_id") != step_id:
            raise AcceptanceOracleError(
                f"{prefix}.step_id must equal {step_id!r}"
            )

        substep_id = criterion.get("substep_id")
        if substep_id is not None and (
            not isinstance(substep_id, str) or substep_id not in substeps
        ):
            raise AcceptanceOracleError(
                f"{prefix}.substep_id does not match a roadmap substep"
            )

        refs = criterion.get("requirement_refs")
        if not isinstance(refs, list) or not refs:
            raise AcceptanceOracleError(
                f"{prefix}.requirement_refs must be a non-empty list"
            )
        if any(not isinstance(ref, str) for ref in refs):
            raise AcceptanceOracleError(
                f"{prefix}.requirement_refs must contain strings"
            )
        if len(refs) != len(set(refs)):
            raise AcceptanceOracleError(
                f"{prefix}.requirement_refs contains duplicates"
            )
        unknown = [ref for ref in refs if ref not in known_refs]
        if unknown:
            raise AcceptanceOracleError(
                f"{prefix}.requirement_refs contains unknown contract refs: "
                f"{unknown}"
            )

        summary = criterion.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            raise AcceptanceOracleError(
                f"{prefix}.summary must be a non-empty string"
            )

        blocking = criterion.get("blocking", True)
        if not isinstance(blocking, bool):
            raise AcceptanceOracleError(
                f"{prefix}.blocking must be a boolean"
            )

        verification = criterion.get("verification")
        if not isinstance(verification, dict):
            raise AcceptanceOracleError(
                f"{prefix}.verification must be a mapping"
            )
        kind = verification.get("kind")
        if kind not in VERIFICATION_KINDS:
            raise AcceptanceOracleError(
                f"{prefix}.verification.kind must be one of "
                f"{sorted(VERIFICATION_KINDS)}"
            )
        for field in ("locator", "expected_observation"):
            value = verification.get(field)
            if not isinstance(value, str) or not value.strip():
                raise AcceptanceOracleError(
                    f"{prefix}.verification.{field} must be non-empty"
                )

        evidence_required = criterion.get("evidence_required")
        if not isinstance(evidence_required, list) or not evidence_required:
            raise AcceptanceOracleError(
                f"{prefix}.evidence_required must be a non-empty list"
            )
        if any(
            not isinstance(value, str) or not value.strip()
            for value in evidence_required
        ):
            raise AcceptanceOracleError(
                f"{prefix}.evidence_required values must be non-empty strings"
            )
        if len(evidence_required) != len(set(evidence_required)):
            raise AcceptanceOracleError(
                f"{prefix}.evidence_required contains duplicates"
            )

        normalized.append(
            {
                "criterion_id": criterion_id,
                "step_id": step_id,
                "substep_id": substep_id,
                "requirement_refs": list(refs),
                "summary": summary,
                "blocking": blocking,
                "verification": {
                    "kind": kind,
                    "locator": verification["locator"],
                    "expected_observation": verification[
                        "expected_observation"
                    ],
                },
                "evidence_required": list(evidence_required),
            }
        )

    return {
        "oracle_id": oracle_id,
        "oracle_path": oracle_path,
        "oracle_sha256": oracle_sha256,
        "source_prompt_contract": {
            "path": contract_rel,
            "sha256": contract_sha,
            "canonical_validation": "PASSED",
        },
        "criteria": normalized,
    }


def _validated_candidate_packet_evidence(
    root: Path,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    packet_rel = candidate.get("packet_path")
    packet_sha = candidate.get("packet_sha256")
    if not isinstance(packet_sha, str) or not HEX64.fullmatch(packet_sha):
        raise AcceptanceOracleError(
            "review candidate packet_sha256 must be a lowercase SHA-256"
        )

    packet_path = _safe_contained_path(
        root,
        packet_rel,
        parent="coordination/completion_packets/records",
        label="review candidate packet_path",
    )
    if not packet_path.is_file():
        raise AcceptanceOracleError(
            f"review candidate completion packet missing: {packet_rel}"
        )
    actual_sha = file_sha256(packet_path)
    if actual_sha != packet_sha:
        raise AcceptanceOracleError(
            "review candidate completion packet SHA mismatch: "
            f"expected={packet_sha} actual={actual_sha}"
        )

    try:
        report = validate_packet(root, packet_path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AcceptanceOracleError(
            f"completion packet canonical validation errored: {exc}"
        ) from exc
    if report.get("result") != "PASSED":
        errors = report.get("errors")
        if not isinstance(errors, list):
            errors = ["unknown canonical validator failure"]
        raise AcceptanceOracleError(
            "completion packet canonical validation failed: "
            + "; ".join(str(item) for item in errors)
        )

    packet = load_yaml(packet_path)
    manifest = packet.get("evidence_manifest")
    requirement_results = packet.get("requirement_results")
    if not isinstance(manifest, list) or not isinstance(
        requirement_results,
        list,
    ):
        raise AcceptanceOracleError(
            "validated completion packet evidence structure is unavailable"
        )

    evidence_by_id = {
        item["evidence_id"]: {
            "kind": item.get("kind"),
            "path": item.get("path"),
            "sha256": item.get("sha256"),
        }
        for item in manifest
        if isinstance(item, dict)
        and isinstance(item.get("evidence_id"), str)
    }
    requirement_evidence: dict[str, list[str]] = {}
    for item in requirement_results:
        if not isinstance(item, dict):
            continue
        obligation_id = item.get("obligation_id")
        evidence_ids = item.get("evidence_ids")
        if isinstance(obligation_id, str) and isinstance(evidence_ids, list):
            requirement_evidence[obligation_id] = [
                value
                for value in evidence_ids
                if isinstance(value, str)
            ]

    return {
        "packet_path": packet_rel,
        "packet_sha256": packet_sha,
        "canonical_validation": "PASSED",
        "evidence_by_id": evidence_by_id,
        "requirement_evidence": requirement_evidence,
    }


def evaluate_acceptance_oracle(
    root: Path,
    *,
    roadmap_step: dict[str, Any],
    module_id: str,
    prompt_id: str,
    step_id: str,
    operator_decision: str,
    evaluation: Any,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    acceptance = roadmap_step.get("acceptance")

    if operator_decision != "ACCEPT":
        return {
            "required": False,
            "gate": "NOT_APPLICABLE_TO_RETURN_HOLD",
        }

    if (
        not isinstance(acceptance, dict)
        or acceptance.get("oracle_required") is not True
    ):
        if evaluation is not None:
            raise AcceptanceOracleError(
                "acceptance oracle evaluation supplied for a step that does "
                "not require an oracle"
            )
        return {
            "required": False,
            "gate": "LEGACY_NOT_REQUIRED",
        }

    request_fingerprint = acceptance_evaluation_request_fingerprint(
        evaluation,
        candidate,
    )

    binding_errors = validate_roadmap_acceptance_binding(
        roadmap_step,
        prefix=f"roadmap_step[{step_id}]",
    )
    if binding_errors:
        raise AcceptanceOracleError("; ".join(binding_errors))

    oracle_path = acceptance["oracle_path"]
    oracle_sha = acceptance["oracle_sha256"]
    oracle = load_and_validate_oracle(
        root,
        oracle_path=oracle_path,
        oracle_sha256=oracle_sha,
        module_id=module_id,
        prompt_id=prompt_id,
        step_id=step_id,
        roadmap_step=roadmap_step,
    )

    if not isinstance(evaluation, dict):
        raise AcceptanceOracleError(
            "acceptance oracle evaluation is required for ACCEPT"
        )
    if evaluation.get("oracle_path") != oracle_path:
        raise AcceptanceOracleError(
            "acceptance oracle evaluation oracle_path mismatch"
        )
    if evaluation.get("oracle_sha256") != oracle_sha:
        raise AcceptanceOracleError(
            "acceptance oracle evaluation oracle_sha256 mismatch"
        )

    expected_basis = _candidate_evidence_basis(candidate)
    if evaluation.get("evidence_basis") != expected_basis:
        raise AcceptanceOracleError(
            "acceptance oracle evaluation evidence_basis does not match "
            "the exact review completion candidate"
        )
    if request_fingerprint is None:
        raise AcceptanceOracleError(
            "acceptance oracle request fingerprint is unexpectedly absent"
        )

    packet_evidence = _validated_candidate_packet_evidence(
        root,
        candidate,
    )
    packet_evidence_ids = set(packet_evidence["evidence_by_id"])

    results = evaluation.get("criteria_results")
    if not isinstance(results, list):
        raise AcceptanceOracleError(
            "acceptance oracle criteria_results must be a list"
        )

    by_id = {item["criterion_id"]: item for item in oracle["criteria"]}
    result_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(results, start=1):
        if not isinstance(item, dict):
            raise AcceptanceOracleError(
                f"criteria_results[{index}] must be a mapping"
            )
        criterion_id = item.get("criterion_id")
        if criterion_id not in by_id:
            raise AcceptanceOracleError(
                f"criteria_results[{index}] has unknown criterion_id"
            )
        if criterion_id in result_by_id:
            raise AcceptanceOracleError(
                f"duplicate criterion result: {criterion_id}"
            )
        result = item.get("result")
        if result not in RESULTS:
            raise AcceptanceOracleError(
                f"criterion {criterion_id} result must be one of "
                f"{sorted(RESULTS)}"
            )
        observed = item.get("observed")
        if result in {"PASS", "FAIL"} and (
            not isinstance(observed, str) or not observed.strip()
        ):
            raise AcceptanceOracleError(
                f"criterion {criterion_id} requires non-empty observed text"
            )
        evidence_refs = item.get("evidence_refs", [])
        if not isinstance(evidence_refs, list) or any(
            not isinstance(value, str) or not value.strip()
            for value in evidence_refs
        ):
            raise AcceptanceOracleError(
                f"criterion {criterion_id} evidence_refs must be a list "
                "of non-empty strings"
            )
        if len(evidence_refs) != len(set(evidence_refs)):
            raise AcceptanceOracleError(
                f"criterion {criterion_id} evidence_refs contains duplicates"
            )
        unknown_packet_refs = sorted(
            set(evidence_refs) - packet_evidence_ids
        )
        if unknown_packet_refs:
            raise AcceptanceOracleError(
                f"criterion {criterion_id} evidence_refs are not present "
                "in the validated completion packet evidence_manifest: "
                f"{unknown_packet_refs}"
            )
        result_by_id[criterion_id] = {
            "criterion_id": criterion_id,
            "result": result,
            "observed": observed,
            "evidence_refs": list(evidence_refs),
        }

    missing = sorted(set(by_id) - set(result_by_id))
    if missing:
        raise AcceptanceOracleError(
            f"acceptance oracle missing criterion results: {missing}"
        )

    waivers = evaluation.get("waivers", [])
    if not isinstance(waivers, list):
        raise AcceptanceOracleError("acceptance oracle waivers must be a list")

    waiver_by_id: dict[str, dict[str, Any]] = {}
    for index, waiver in enumerate(waivers, start=1):
        if not isinstance(waiver, dict):
            raise AcceptanceOracleError(
                f"waivers[{index}] must be a mapping"
            )
        criterion_id = waiver.get("criterion_id")
        criterion = by_id.get(criterion_id)
        if criterion is None:
            raise AcceptanceOracleError(
                f"waivers[{index}] has unknown criterion_id"
            )
        if criterion_id in waiver_by_id:
            raise AcceptanceOracleError(
                f"duplicate criterion waiver: {criterion_id}"
            )
        if criterion.get("blocking") is not True:
            raise AcceptanceOracleError(
                f"waiver may only target blocking criterion {criterion_id}"
            )
        if waiver.get("explicit_operator_authorization") is not True:
            raise AcceptanceOracleError(
                f"waiver {criterion_id} requires "
                "explicit_operator_authorization=true"
            )
        reason = waiver.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise AcceptanceOracleError(
                f"waiver {criterion_id} requires a non-empty reason"
            )
        waiver_by_id[criterion_id] = {
            "criterion_id": criterion_id,
            "explicit_operator_authorization": True,
            "reason": reason,
        }

    normalized: list[dict[str, Any]] = []
    blocked: list[str] = []
    pass_count = 0
    fail_count = 0
    not_evaluated_count = 0
    waived_count = 0

    for criterion in oracle["criteria"]:
        criterion_id = criterion["criterion_id"]
        result = result_by_id[criterion_id]
        state = result["result"]
        pass_count += int(state == "PASS")
        fail_count += int(state == "FAIL")
        not_evaluated_count += int(state == "NOT_EVALUATED")

        required_evidence = set(criterion["evidence_required"])
        supplied_evidence = set(result["evidence_refs"])
        required_evidence_manifested = required_evidence.issubset(
            packet_evidence_ids
        )
        required_evidence_cited = required_evidence.issubset(
            supplied_evidence
        )

        requirement_evidence_complete = True
        requirement_evidence_refs: dict[str, list[str]] = {}
        for requirement_ref in criterion["requirement_refs"]:
            known_refs = packet_evidence["requirement_evidence"].get(
                requirement_ref,
                [],
            )
            requirement_evidence_refs[requirement_ref] = list(known_refs)
            if not set(known_refs).intersection(supplied_evidence):
                requirement_evidence_complete = False

        evidence_complete = (
            required_evidence_manifested
            and required_evidence_cited
            and requirement_evidence_complete
        )
        satisfied = state == "PASS" and evidence_complete
        waived = criterion_id in waiver_by_id

        if waived:
            waived_count += 1
            if satisfied:
                raise AcceptanceOracleError(
                    f"waiver {criterion_id} is unnecessary because criterion "
                    "already PASSes with required evidence"
                )

        if criterion["blocking"] and not satisfied and not waived:
            blocked.append(criterion_id)

        normalized.append(
            {
                "criterion_id": criterion_id,
                "blocking": criterion["blocking"],
                "result": state,
                "observed": result["observed"],
                "evidence_required": list(criterion["evidence_required"]),
                "evidence_refs": list(result["evidence_refs"]),
                "required_evidence_manifested": (
                    required_evidence_manifested
                ),
                "required_evidence_cited": required_evidence_cited,
                "requirement_evidence_refs": requirement_evidence_refs,
                "requirement_evidence_complete": (
                    requirement_evidence_complete
                ),
                "evidence_complete": evidence_complete,
                "waived": waived,
            }
        )

    if blocked:
        raise AcceptanceOracleError(
            "ACCEPT blocked by unsatisfied blocking acceptance criteria: "
            f"{sorted(blocked)}"
        )

    return {
        "required": True,
        "gate": "PASS",
        "oracle_id": oracle["oracle_id"],
        "oracle_path": oracle["oracle_path"],
        "oracle_sha256": oracle["oracle_sha256"],
        "source_prompt_contract": oracle["source_prompt_contract"],
        "evidence_basis": expected_basis,
        "completion_packet": {
            "path": packet_evidence["packet_path"],
            "sha256": packet_evidence["packet_sha256"],
            "canonical_validation": packet_evidence[
                "canonical_validation"
            ],
        },
        "request_fingerprint_sha256": request_fingerprint,
        "criteria_total": len(oracle["criteria"]),
        "blocking_total": sum(
            1 for item in oracle["criteria"] if item["blocking"]
        ),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "not_evaluated_count": not_evaluated_count,
        "waived_count": waived_count,
        "criteria_results": normalized,
        "waivers": [
            waiver_by_id[key] for key in sorted(waiver_by_id)
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Blueprint acceptance oracle v0.1.",
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--sha256")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    path = _safe_contained_path(
        root,
        args.oracle,
        parent="coordination/acceptance_oracles",
        label="oracle",
    )
    if not path.is_file():
        raise SystemExit(f"ERROR: oracle file missing: {args.oracle}")
    actual_sha = file_sha256(path)
    if args.sha256 and actual_sha != args.sha256:
        raise SystemExit(
            f"ERROR: oracle SHA mismatch: expected={args.sha256} actual={actual_sha}"
        )

    data = load_yaml(path)
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise SystemExit("ERROR: oracle metadata missing")

    module_id = metadata.get("module_id")
    prompt_id = metadata.get("prompt_id")
    step_id = metadata.get("step_id")
    if not all(
        isinstance(value, str) and value
        for value in (module_id, prompt_id, step_id)
    ):
        raise SystemExit("ERROR: oracle identity fields are invalid")

    synthetic_step: dict[str, Any] = {"step_id": step_id}
    for criterion in data.get("criteria", []):
        if (
            isinstance(criterion, dict)
            and isinstance(criterion.get("substep_id"), str)
        ):
            synthetic_step.setdefault("substeps", []).append(
                {"substep_id": criterion["substep_id"]}
            )

    load_and_validate_oracle(
        root,
        oracle_path=args.oracle,
        oracle_sha256=actual_sha,
        module_id=module_id,
        prompt_id=prompt_id,
        step_id=step_id,
        roadmap_step=synthetic_step,
    )
    print("ForPrint Acceptance Oracle v0.1")
    print(f"oracle: {args.oracle}")
    print(f"sha256: {actual_sha}")
    print("result: VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
