#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULT_SCHEMA_VERSION = "forprint_assistant_handoff_v2_result_v0_1"
RESULT_FIELDS = (
    "schema_version",
    "handoff_manifest_sha256",
    "attempt_id",
    "status",
    "changed_paths",
    "validation_evidence",
    "self_repair_attempts",
    "resume_coordinates",
    "unresolved_findings",
)
MAX_SELF_REPAIR_ATTEMPTS = 3
DEFAULT_SELF_REPAIR_ATTEMPTS = 2
SAFE_REPAIR_CODES = ("DEDUPLICATE_IDENTICAL_CHANGED_PATHS",)
ATTEMPT_LEDGER = Path("scripts/coordination/execution_attempt_ledger_v0_1.py")


class ResultValidationError(RuntimeError):
    pass


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _sha_value(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _error(code: str, field: str, message: str) -> dict[str, str]:
    return {"code": code, "field": field, "message": message}


def _load_attempt_ledger(root: Path) -> Any:
    path = root / ATTEMPT_LEDGER
    if not path.is_file():
        raise ResultValidationError(f"attempt ledger runtime missing: {ATTEMPT_LEDGER}")
    spec = importlib.util.spec_from_file_location(
        "forprint_execution_attempt_ledger_v0_1",
        path,
    )
    if spec is None or spec.loader is None:
        raise ResultValidationError("cannot load execution attempt ledger")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_attempt_id(root: Path, value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    module = _load_attempt_ledger(root)
    pattern = getattr(module, "ID_RE", None)
    return bool(pattern is not None and pattern.fullmatch(value))


def _expected_manifest_hash(manifest: dict[str, Any]) -> str:
    value = manifest.get("handoff_manifest_sha256")
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value.lower())
    ):
        raise ResultValidationError("origin manifest handoff_manifest_sha256 is invalid")
    return value.lower()


def _valid_changed_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if "\\" in value:
        return False
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return False
    return value == path.as_posix()


def _valid_evidence_item(value: Any) -> bool:
    return (isinstance(value, str) and bool(value.strip())) or isinstance(value, dict)


def _valid_finding_item(value: Any) -> bool:
    return (isinstance(value, str) and bool(value.strip())) or isinstance(value, dict)


def _valid_resume_coordinates(value: Any) -> bool:
    if isinstance(value, dict):
        return True
    if isinstance(value, list):
        return all(isinstance(item, str) and bool(item.strip()) for item in value)
    return False


def _valid_self_repair_attempt(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    required = {
        "attempt_no",
        "repair_code",
        "authority_scope",
        "before_sha256",
        "repaired_payload_sha256",
        "outcome",
    }
    if not required.issubset(value):
        return False
    if not isinstance(value["attempt_no"], int) or value["attempt_no"] < 1:
        return False
    if value["repair_code"] not in SAFE_REPAIR_CODES:
        return False
    if value["authority_scope"] != "RESULT_ENVELOPE_MECHANICAL_ONLY":
        return False
    for key in ("before_sha256", "repaired_payload_sha256"):
        digest = value.get(key)
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest.lower())
        ):
            return False
    return value.get("outcome") in {"APPLIED", "NO_CHANGE", "FAILED"}


def validate_result_envelope(
    result: Any,
    manifest: dict[str, Any],
    *,
    root: Path = PROJECT_ROOT,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    if not isinstance(result, dict):
        return [
            _error(
                "RESULT_NOT_MAPPING",
                "$",
                "result envelope must be a mapping",
            )
        ]

    actual = set(result)
    expected = set(RESULT_FIELDS)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        errors.append(_error("MISSING_FIELDS", "$", ",".join(missing)))
    if unexpected:
        errors.append(_error("UNEXPECTED_FIELDS", "$", ",".join(unexpected)))
    if missing or unexpected:
        return errors

    if result["schema_version"] != RESULT_SCHEMA_VERSION:
        errors.append(
            _error(
                "SCHEMA_VERSION_MISMATCH",
                "schema_version",
                f"expected {RESULT_SCHEMA_VERSION}",
            )
        )

    try:
        expected_manifest_hash = _expected_manifest_hash(manifest)
    except ResultValidationError as exc:
        errors.append(
            _error(
                "ORIGIN_MANIFEST_INVALID",
                "handoff_manifest_sha256",
                str(exc),
            )
        )
        expected_manifest_hash = None

    actual_manifest_hash = result["handoff_manifest_sha256"]
    if not isinstance(actual_manifest_hash, str):
        errors.append(
            _error(
                "RESULT_MANIFEST_HASH_INVALID",
                "handoff_manifest_sha256",
                "must be a lowercase SHA-256 string",
            )
        )
    elif len(actual_manifest_hash) != 64 or any(
        ch not in "0123456789abcdef" for ch in actual_manifest_hash.lower()
    ):
        errors.append(
            _error(
                "RESULT_MANIFEST_HASH_INVALID",
                "handoff_manifest_sha256",
                "must be a SHA-256 string",
            )
        )
    elif (
        expected_manifest_hash is not None
        and actual_manifest_hash.lower() != expected_manifest_hash
    ):
        errors.append(
            _error(
                "RESULT_MANIFEST_BINDING_MISMATCH",
                "handoff_manifest_sha256",
                "result hash does not match origin manifest",
            )
        )

    if not _valid_attempt_id(root, result["attempt_id"]):
        errors.append(
            _error(
                "ATTEMPT_ID_INVALID",
                "attempt_id",
                "must satisfy Execution Attempt Ledger ID semantics",
            )
        )

    if not isinstance(result["status"], str) or not result["status"].strip():
        errors.append(
            _error(
                "STATUS_INVALID",
                "status",
                "must be a non-empty string",
            )
        )

    changed_paths = result["changed_paths"]
    if not isinstance(changed_paths, list):
        errors.append(
            _error(
                "CHANGED_PATHS_INVALID",
                "changed_paths",
                "must be a list",
            )
        )
    else:
        invalid = [value for value in changed_paths if not _valid_changed_path(value)]
        if invalid:
            errors.append(
                _error(
                    "CHANGED_PATH_INVALID",
                    "changed_paths",
                    "paths must be normalized project-relative POSIX paths",
                )
            )
        if len(changed_paths) != len(set(changed_paths)):
            errors.append(
                _error(
                    "CHANGED_PATH_DUPLICATE",
                    "changed_paths",
                    "identical changed paths must not repeat",
                )
            )

    evidence = result["validation_evidence"]
    if (
        not isinstance(evidence, list)
        or not evidence
        or not all(_valid_evidence_item(item) for item in evidence)
    ):
        errors.append(
            _error(
                "VALIDATION_EVIDENCE_INVALID",
                "validation_evidence",
                "must be a non-empty list of strings or mappings",
            )
        )

    attempts = result["self_repair_attempts"]
    if not isinstance(attempts, list) or not all(
        _valid_self_repair_attempt(item) for item in attempts
    ):
        errors.append(
            _error(
                "SELF_REPAIR_ATTEMPTS_INVALID",
                "self_repair_attempts",
                "must be a list of governed repair-attempt mappings",
            )
        )

    if not _valid_resume_coordinates(result["resume_coordinates"]):
        errors.append(
            _error(
                "RESUME_COORDINATES_INVALID",
                "resume_coordinates",
                "must be a mapping or string list; S4 hardens freshness/resume",
            )
        )

    findings = result["unresolved_findings"]
    if not isinstance(findings, list) or not all(_valid_finding_item(item) for item in findings):
        errors.append(
            _error(
                "UNRESOLVED_FINDINGS_INVALID",
                "unresolved_findings",
                "must be a list of strings or mappings",
            )
        )

    return errors


def _dedupe_changed_paths(result: dict[str, Any]) -> bool:
    paths = result.get("changed_paths")
    if not isinstance(paths, list):
        return False
    deduped = list(dict.fromkeys(paths))
    if deduped == paths:
        return False
    result["changed_paths"] = deduped
    return True


def _repairable(errors: list[dict[str, str]]) -> bool:
    return bool(errors) and {item["code"] for item in errors} <= {"CHANGED_PATH_DUPLICATE"}


def validate_with_bounded_self_repair(
    result: dict[str, Any],
    manifest: dict[str, Any],
    *,
    root: Path = PROJECT_ROOT,
    max_self_repair_attempts: int = DEFAULT_SELF_REPAIR_ATTEMPTS,
) -> dict[str, Any]:
    if (
        not isinstance(max_self_repair_attempts, int)
        or max_self_repair_attempts < 0
        or max_self_repair_attempts > MAX_SELF_REPAIR_ATTEMPTS
    ):
        raise ResultValidationError(
            f"max_self_repair_attempts must be 0..{MAX_SELF_REPAIR_ATTEMPTS}"
        )

    working = deepcopy(result)
    initial_findings = deepcopy(working.get("unresolved_findings"))
    original_repair_count = (
        len(working.get("self_repair_attempts", []))
        if isinstance(working.get("self_repair_attempts"), list)
        else 0
    )

    errors = validate_result_envelope(working, manifest, root=root)
    if not errors:
        return {
            "valid": True,
            "result": working,
            "errors": [],
            "repair_attempt_count": 0,
            "repair_exhausted": False,
        }

    for attempt_no in range(1, max_self_repair_attempts + 1):
        if not _repairable(errors):
            break

        before_sha = _sha_value(working)
        repaired = _dedupe_changed_paths(working)
        repaired_payload_sha = _sha_value(working)

        record = {
            "attempt_no": attempt_no,
            "repair_code": "DEDUPLICATE_IDENTICAL_CHANGED_PATHS",
            "authority_scope": "RESULT_ENVELOPE_MECHANICAL_ONLY",
            "before_sha256": before_sha,
            "repaired_payload_sha256": repaired_payload_sha,
            "outcome": "APPLIED" if repaired else "NO_CHANGE",
        }
        attempts = working.get("self_repair_attempts")
        if not isinstance(attempts, list):
            break
        attempts.append(record)

        evidence = working.get("validation_evidence")
        if isinstance(evidence, list):
            evidence.append(
                {
                    "kind": "self_repair",
                    "repair_code": record["repair_code"],
                    "attempt_no": attempt_no,
                    "result": record["outcome"],
                }
            )

        if working.get("unresolved_findings") != initial_findings:
            raise ResultValidationError("bounded repair altered unresolved_findings")

        errors = validate_result_envelope(working, manifest, root=root)
        if not errors:
            return {
                "valid": True,
                "result": working,
                "errors": [],
                "repair_attempt_count": attempt_no,
                "repair_exhausted": False,
            }

    return {
        "valid": False,
        "result": working,
        "errors": errors,
        "repair_attempt_count": max(
            0,
            len(working.get("self_repair_attempts", [])) - original_repair_count,
        ),
        "repair_exhausted": bool(max_self_repair_attempts and _repairable(errors)),
    }


def _load_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ResultValidationError(f"mapping required: {path}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(PROJECT_ROOT))
    parser.add_argument("--result", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--repair", action="store_true")
    parser.add_argument(
        "--max-self-repair-attempts",
        type=int,
        default=DEFAULT_SELF_REPAIR_ATTEMPTS,
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        result = _load_mapping(Path(args.result))
        manifest = _load_mapping(Path(args.manifest))

        if args.repair:
            report = validate_with_bounded_self_repair(
                result,
                manifest,
                root=root,
                max_self_repair_attempts=args.max_self_repair_attempts,
            )
        else:
            errors = validate_result_envelope(result, manifest, root=root)
            report = {
                "valid": not errors,
                "result": result,
                "errors": errors,
                "repair_attempt_count": 0,
                "repair_exhausted": False,
            }

        if report["valid"] and args.output:
            output = Path(args.output)
            if not output.is_absolute():
                output = root / output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                yaml.safe_dump(
                    report["result"],
                    sort_keys=False,
                    allow_unicode=True,
                    width=140,
                ),
                encoding="utf-8",
            )
            print("REPAIRED_RESULT=" + str(output))

        print("ASSISTANT_HANDOFF_V2_RESULT_VALIDATION=" + ("PASS" if report["valid"] else "FAIL"))
        print("RESULT_SCHEMA_VERSION=" + RESULT_SCHEMA_VERSION)
        print("REPAIR_ATTEMPT_COUNT=" + str(report["repair_attempt_count"]))
        print("DISPATCH_AUTHORITY=false")
        print("WORKER_DISPATCH_PERFORMED=false")
        print("PROJECT_SOURCE_MUTATION_PERFORMED=false")
        if report["errors"]:
            print(
                yaml.safe_dump(
                    {"errors": report["errors"]},
                    sort_keys=False,
                    allow_unicode=True,
                ).rstrip()
            )
        return 0 if report["valid"] else 1
    except Exception as exc:
        print("ASSISTANT_HANDOFF_V2_RESULT_VALIDATION=FAIL")
        print(f"ERROR={type(exc).__name__}: {exc}")
        print("DISPATCH_AUTHORITY=false")
        print("WORKER_DISPATCH_PERFORMED=false")
        print("PROJECT_SOURCE_MUTATION_PERFORMED=false")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
