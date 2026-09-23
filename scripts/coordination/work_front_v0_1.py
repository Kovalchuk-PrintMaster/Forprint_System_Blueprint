from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

CONTRACT_PATH = Path("coordination/standards/automation/work_front_contract_v0_1.yaml")
REUSE_DISPOSITIONS = ("REUSE", "EXTEND", "ADAPT", "REPLACE", "NEW")
TARGET_REQUIRED = {"REUSE", "EXTEND", "ADAPT", "REPLACE"}
REQUIRED_FIELDS = (
    "work_front_id",
    "objective",
    "scope",
    "exclusions",
    "provenance",
    "dependencies",
    "outputs",
    "acceptance",
    "stop_conditions",
    "authority",
    "capability_reuse",
)


class WorkFrontError(RuntimeError):
    pass


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, *, non_empty: bool = False) -> bool:
    if not isinstance(value, list):
        return False
    if non_empty and not value:
        return False
    return all(_non_empty_string(item) for item in value)


def load_contract(root: Path) -> dict[str, Any]:
    path = root / CONTRACT_PATH
    if not path.is_file():
        raise WorkFrontError(f"contract missing: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise WorkFrontError("contract root must be a mapping")
    validate_contract_shape(value)
    return value


def validate_contract_shape(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "forprint_work_front_contract_v0_1":
        raise WorkFrontError("contract schema_version")
    if contract.get("status") != "active_standard":
        raise WorkFrontError("contract status")
    if contract.get("authority") != "WORK_FRONT_CONTRACT":
        raise WorkFrontError("contract authority")

    model = contract.get("authority_model")
    if not isinstance(model, dict):
        raise WorkFrontError("authority_model")
    if model.get("precedence_layer") != "WORK_FRONT":
        raise WorkFrontError("precedence layer")
    if model.get("chat_is_authority") is not False:
        raise WorkFrontError("chat authority")
    if model.get("human_intent_is_execution_authority") is not False:
        raise WorkFrontError("intent authority")
    if model.get("work_front_is_execution_authority") is not True:
        raise WorkFrontError("work front authority")
    if model.get("may_narrow_higher_authority") is not True:
        raise WorkFrontError("narrowing")
    if model.get("may_widen_without_explicit_gate") is not False:
        raise WorkFrontError("silent widening")

    if tuple(contract.get("required_fields") or ()) != REQUIRED_FIELDS:
        raise WorkFrontError("required fields")

    reuse = contract.get("capability_reuse")
    if not isinstance(reuse, dict):
        raise WorkFrontError("capability_reuse")
    if tuple(reuse.get("dispositions") or ()) != REUSE_DISPOSITIONS:
        raise WorkFrontError("reuse dispositions")
    if reuse.get("search_before_new_required") is not True:
        raise WorkFrontError("reuse search")
    if reuse.get("new_requires_rationale") is not True:
        raise WorkFrontError("new rationale")

    gates = contract.get("gates")
    if not isinstance(gates, dict):
        raise WorkFrontError("gates")
    assistant = gates.get("assistant_pack")
    dispatch = gates.get("dispatch")
    if not isinstance(assistant, dict) or not isinstance(dispatch, dict):
        raise WorkFrontError("gate mappings")
    if assistant.get("work_front_validation_required_for_task_execution") is not True:
        raise WorkFrontError("assistant pack gate")
    if dispatch.get("work_front_required") is not True:
        raise WorkFrontError("dispatch front required")
    if dispatch.get("dispatch_authority_conferred") is not False:
        raise WorkFrontError("dispatch authority widened")


def resolve_front_path(root: Path, front: str | Path) -> Path:
    value = Path(front)
    path = value if value.is_absolute() else root / value
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise WorkFrontError("work front path escapes repository root") from exc
    return resolved


def load_work_front(root: Path, front: str | Path) -> dict[str, Any]:
    path = resolve_front_path(root, front)
    if not path.is_file():
        raise WorkFrontError(f"work front missing: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise WorkFrontError("work front root must be a mapping")
    return value


def validate_work_front_data(
    data: dict[str, Any],
    contract: dict[str, Any],
) -> list[str]:
    validate_contract_shape(contract)
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing field: {field}")

    if errors:
        return errors

    if not _non_empty_string(data.get("work_front_id")):
        errors.append("work_front_id must be a non-empty string")
    if not _non_empty_string(data.get("objective")):
        errors.append("objective must be a non-empty string")
    if not _string_list(data.get("scope"), non_empty=True):
        errors.append("scope must be a non-empty string list")
    if not _string_list(data.get("exclusions")):
        errors.append("exclusions must be a string list")
    if not _string_list(data.get("dependencies")):
        errors.append("dependencies must be a string list")
    if not _string_list(data.get("outputs"), non_empty=True):
        errors.append("outputs must be a non-empty string list")
    if not _string_list(data.get("acceptance"), non_empty=True):
        errors.append("acceptance must be a non-empty string list")
    if not _string_list(data.get("stop_conditions"), non_empty=True):
        errors.append("stop_conditions must be a non-empty string list")

    provenance = data.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be a mapping")
    else:
        if not _string_list(provenance.get("source_refs"), non_empty=True):
            errors.append("provenance.source_refs must be a non-empty string list")
        if provenance.get("chat_is_authority") is not False:
            errors.append("provenance.chat_is_authority must be false")

    authority = data.get("authority")
    if not isinstance(authority, dict):
        errors.append("authority must be a mapping")
    else:
        if authority.get("layer") != "WORK_FRONT":
            errors.append("authority.layer must be WORK_FRONT")
        if not _string_list(authority.get("permissions")):
            errors.append("authority.permissions must be a string list")
        widening = authority.get("widening_requested")
        if not isinstance(widening, bool):
            errors.append("authority.widening_requested must be boolean")
        elif widening and not _non_empty_string(authority.get("widening_gate_evidence")):
            errors.append("authority.widening_gate_evidence required when widening_requested=true")

    reuse = data.get("capability_reuse")
    if not isinstance(reuse, dict):
        errors.append("capability_reuse must be a mapping")
    else:
        if reuse.get("search_performed") is not True:
            errors.append("capability_reuse.search_performed must be true")
        if not _string_list(reuse.get("searched_surfaces"), non_empty=True):
            errors.append("capability_reuse.searched_surfaces must be a non-empty string list")
        disposition = reuse.get("disposition")
        if disposition not in REUSE_DISPOSITIONS:
            errors.append("capability_reuse.disposition invalid")
        target_refs = reuse.get("target_refs")
        if not _string_list(target_refs):
            errors.append("capability_reuse.target_refs must be a string list")
        elif disposition in TARGET_REQUIRED and not target_refs:
            errors.append(f"capability_reuse.target_refs required for {disposition}")
        if disposition == "NEW" and not _non_empty_string(reuse.get("rationale")):
            errors.append("capability_reuse.rationale required for NEW")

    return errors


def assert_authority_narrowing(
    front_permissions: set[str],
    higher_permissions: set[str],
    *,
    widening_gate_evidence: str | None = None,
) -> set[str]:
    widened = front_permissions - higher_permissions
    if widened and not _non_empty_string(widening_gate_evidence):
        raise WorkFrontError(
            "work front authority widens higher authority without explicit gate evidence"
        )
    return set(front_permissions)


def validate_work_front(
    root: Path,
    front: str | Path,
    *,
    action: str = "validate",
) -> dict[str, Any]:
    contract = load_contract(root)
    path = resolve_front_path(root, front)
    data = load_work_front(root, path)
    errors = validate_work_front_data(data, contract)
    if errors:
        raise WorkFrontError("; ".join(errors))

    return {
        "status": "PASS",
        "action": action,
        "work_front_id": data["work_front_id"],
        "front_path": str(path.relative_to(root.resolve())),
        "capability_reuse_disposition": data["capability_reuse"]["disposition"],
        "dispatch_authority_conferred": False,
        "release_authority_conferred": False,
        "foreign_write_authority_conferred": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--front")
    parser.add_argument(
        "--action",
        choices=["validate", "assistant-pack", "dispatch"],
        default="validate",
    )
    parser.add_argument("--contract-only", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        contract = load_contract(root)
        if args.contract_only:
            validate_contract_shape(contract)
            print("WORK_FRONT_CONTRACT=PASS")
            print("MUTATION_PERFORMED=false")
            return 0
        if not args.front:
            raise WorkFrontError("front is required")
        result = validate_work_front(root, args.front, action=args.action)
    except WorkFrontError as exc:
        print("WORK_FRONT_VALIDATION=FAIL")
        print("ERROR=" + str(exc))
        return 4

    print("WORK_FRONT_VALIDATION=PASS")
    print("ACTION=" + result["action"])
    print("WORK_FRONT_ID=" + result["work_front_id"])
    print("WORK_FRONT_PATH=" + result["front_path"])
    print("CAPABILITY_REUSE_DISPOSITION=" + result["capability_reuse_disposition"])
    print("DISPATCH_AUTHORITY_CONFERRED=false")
    print("RELEASE_AUTHORITY_CONFERRED=false")
    print("FOREIGN_WRITE_AUTHORITY_CONFERRED=false")
    print("MUTATION_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
