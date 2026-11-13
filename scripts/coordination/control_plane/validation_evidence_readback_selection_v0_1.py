"""CF10 B3 P0/P1: exact task/front readback selector, never an execution grant.

This module only freezes evidence-readback policy provenance in the governed
prepare / ACK / explicit dispatch lifecycle. Invocation activation is NOT here.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

POLICY_REF = "coordination/registry/cf10_validation_evidence_readback_policy_v0_1.yaml"
POLICY_SCHEMA = "forprint_cf10_validation_evidence_readback_policy_v0_1"
SELECTION_SCHEMA = "forprint_cf10_validation_evidence_readback_selection_v0_1"
CAPABILITY_ID = "validation_evidence_readback"
POLICY_REVISION = "0.1.0"
IDENTITY = ("task_prompt_id", "work_front_id", "work_front_ref")


class ReadbackSelectionError(RuntimeError):
    """Invalid or changed Blueprint-owned readback selection."""


def _identity(source: Any) -> dict[str, str]:
    if not isinstance(source, dict):
        raise ReadbackSelectionError("readback identity mapping required")
    selected: dict[str, str] = {}
    for key in IDENTITY:
        value = source.get(key)
        if (not isinstance(value, str) or not value or value != value.strip()
                or any(ord(c) < 32 for c in value) or "*" in value or "?" in value):
            raise ReadbackSelectionError("readback identity invalid: " + key)
        selected[key] = value
    ref = selected["work_front_ref"]
    path = Path(ref)
    if (path.is_absolute() or ".." in path.parts or path.as_posix() != ref
            or not ref.startswith("coordination/work_fronts/")
            or not ref.endswith(".yaml")):
        raise ReadbackSelectionError("readback work front path invalid")
    return selected


def validate_policy(value: Any) -> dict[str, Any]:
    keys = {"schema_version", "status", "revision", "grants_authority",
            "default_enabled", "capability_id", "opt_in_bindings"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ReadbackSelectionError("readback policy field mismatch")
    if (value["schema_version"] != POLICY_SCHEMA
            or value["status"] != "current_standard"
            or value["revision"] != POLICY_REVISION
            or value["grants_authority"] is not False
            or value["default_enabled"] is not False
            or value["capability_id"] != CAPABILITY_ID):
        raise ReadbackSelectionError("readback policy authority or schema invalid")
    optins = value["opt_in_bindings"]
    if not isinstance(optins, list):
        raise ReadbackSelectionError("readback opt-in must be list")
    seen: set[tuple[str, ...]] = set()
    for entry in optins:
        if not isinstance(entry, dict) or set(entry) != set(IDENTITY) | {"enabled"}:
            raise ReadbackSelectionError("readback opt-in fields invalid")
        if entry["enabled"] is not True:
            raise ReadbackSelectionError("readback opt-in must explicitly enable")
        identity = _identity(entry)
        key = tuple(identity[field] for field in IDENTITY)
        if key in seen:
            raise ReadbackSelectionError("duplicate readback opt-in")
        seen.add(key)
    return value


def load_policy(root: Path) -> tuple[dict[str, Any], str]:
    root = Path(root).resolve()
    policy = root / POLICY_REF
    if not policy.is_file() or policy.is_symlink():
        raise ReadbackSelectionError("readback policy missing or unsafe")
    raw = policy.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    class UniqueKeys(yaml.SafeLoader):
        pass
    def mapping(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode) -> dict:
        value = {}
        for k, v in node.value:
            name = loader.construct_object(k, deep=True)
            if not isinstance(name, str) or name in value:
                raise ReadbackSelectionError("readback policy duplicate/invalid key")
            value[name] = loader.construct_object(v, deep=True)
        return value
    UniqueKeys.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    try:
        doc = yaml.load(raw.decode("utf-8"), Loader=UniqueKeys)
    except (yaml.YAMLError, UnicodeDecodeError) as exc:
        raise ReadbackSelectionError("readback policy YAML invalid") from exc
    return validate_policy(doc), digest


def resolve_selection(*, root: Path, task_binding: dict[str, Any]) -> dict[str, Any]:
    identity = _identity(task_binding)
    policy, digest = load_policy(root)
    enabled = False
    for entry in policy["opt_in_bindings"]:
        matching = [field for field in IDENTITY if identity[field] == entry[field]]
        if len(matching) == len(IDENTITY):
            enabled = True
        elif matching:
            raise ReadbackSelectionError("partial readback opt-in identity mismatch")
    return {
        "schema_version": SELECTION_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "enabled": enabled,
        "policy_ref": POLICY_REF,
        "policy_sha256": digest,
        "policy_revision": policy["revision"],
        **identity,
    }


def resolve_if_registered(*, root: Path, task_binding: dict[str, Any]) -> dict[str, Any] | None:
    """Historical/unmigrated roots stay OFF without introducing new authority.

    An explicitly declared selection always requires the policy at verify time.
    """
    path = Path(root).resolve() / POLICY_REF
    if not path.exists() and not path.is_symlink():
        return None
    return resolve_selection(root=root, task_binding=task_binding)


def verify_frozen_selection(
    *, root: Path, execution: dict[str, Any], task_binding: dict[str, Any],
) -> dict[str, Any] | None:
    """Legacy selector absence stays OFF; partial or altered provenance fails."""
    if not isinstance(execution, dict):
        raise ReadbackSelectionError("readback execution mapping required")
    a = "validation_readback_selection"
    b = "validation_readback_policy_sha256"
    present_a, present_b = a in execution, b in execution
    if not present_a and not present_b:
        return None  # historical, no readback permission
    if present_a != present_b:
        raise ReadbackSelectionError("readback selector/provenance partial")
    expected = resolve_selection(root=root, task_binding=task_binding)
    if execution[a] != expected or execution[b] != expected["policy_sha256"]:
        raise ReadbackSelectionError("readback selection/policy provenance drift")
    return expected
