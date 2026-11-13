#!/usr/bin/env python3
"""Deterministic Project Constitution loader and authority resolver."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import yaml

CONSTITUTION_PATH = Path("coordination/standards/governance/project_constitution_v0_1.yaml")
EXPECTED_PRECEDENCE = (
    "PROJECT_CONSTITUTION",
    "MODULE_POLICY",
    "EXECUTION_PROFILE",
    "WORK_FRONT",
)


class AuthorityError(RuntimeError):
    pass


@dataclass(frozen=True)
class WideningGate:
    approved: bool
    approver_class: str
    evidence_ref: str


def load_constitution(root: Path) -> dict:
    path = root / CONSTITUTION_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AuthorityError("Project Constitution must be a YAML mapping")
    validate_constitution_shape(data)
    return data


def validate_constitution_shape(data: dict) -> None:
    if data.get("schema_version") != "forprint_project_constitution_v0_1":
        raise AuthorityError("invalid constitution schema_version")
    if data.get("status") != "CANONICAL":
        raise AuthorityError("constitution status must be CANONICAL")
    if data.get("authority") != "PROJECT_CONSTITUTION":
        raise AuthorityError("constitution authority must be PROJECT_CONSTITUTION")

    precedence = data.get("authority_precedence") or {}
    if tuple(precedence.get("order") or ()) != EXPECTED_PRECEDENCE:
        raise AuthorityError("authority precedence order drift")
    if precedence.get("lower_layer_may_narrow") is not True:
        raise AuthorityError("lower-layer narrowing must be allowed")
    if precedence.get("lower_layer_may_widen_without_explicit_gate") is not False:
        raise AuthorityError("silent authority widening must be forbidden")

    laws = data.get("project_laws")
    if not isinstance(laws, list):
        raise AuthorityError("project_laws must be a list")
    ids = [row.get("id") for row in laws if isinstance(row, dict)]
    required = {
        "LAW_CANONICAL_OVER_GENERATED",
        "LAW_IMMUTABLE_HISTORY",
        "LAW_CHAT_NOT_AUTHORITY",
        "LAW_REUSE_BEFORE_NEW",
        "LAW_NO_FOREIGN_WRITE_WITHOUT_AUTHORITY",
        "LAW_CRITICAL_PROCEDURE_EVIDENCE",
        "LAW_NO_SILENT_BYPASS",
        "LAW_BREAKING_CHANGE_OPERATOR_GATE",
        "LAW_RAW_CONVERSATION_IS_EVIDENCE_ONLY",
        "LAW_FRESH_AGENT_ACCEPTED_STATE",
        "LAW_INDEPENDENT_VALIDATION_BEFORE_COMPLETION",
        "LAW_AUTONOMY_BY_CAPABILITY_AND_BLAST_RADIUS",
        "LAW_AI_CANNOT_SELF_CERTIFY_GUARDRAILS",
    }
    if set(ids) != required or len(ids) != len(required):
        raise AuthorityError("project law set drift")


def resolve_effective_permissions(
    layers: Iterable[tuple[str, set[str]]],
    *,
    widening_gate: WideningGate | None = None,
) -> set[str]:
    rows = list(layers)
    if not rows:
        raise AuthorityError("at least one authority layer is required")

    names = tuple(name for name, _permissions in rows)
    expected_prefix = EXPECTED_PRECEDENCE[: len(names)]
    if names != expected_prefix:
        raise AuthorityError(f"authority layers must follow precedence order; got={names}")

    effective = set(rows[0][1])
    for name, declared in rows[1:]:
        declared = set(declared)
        widened = declared - effective
        if widened:
            gate_ok = (
                widening_gate is not None
                and widening_gate.approved
                and widening_gate.approver_class == "OPERATOR_OR_HIGHER_CANONICAL_AUTHORITY"
                and bool(widening_gate.evidence_ref.strip())
            )
            if not gate_ok:
                raise AuthorityError(
                    f"{name} attempts authority widening without explicit gate: "
                    + ",".join(sorted(widened))
                )
            effective = declared
        else:
            effective &= declared
    return effective


def assert_guardrail_change_allowed(
    *,
    actor: str,
    modifies_own_guardrails: bool,
    self_certifies_acceptance: bool,
    external_acceptance_evidence: str | None,
) -> None:
    if modifies_own_guardrails and self_certifies_acceptance:
        raise AuthorityError(f"{actor} may not modify and self-certify its own guardrails")
    if modifies_own_guardrails and not (external_acceptance_evidence or "").strip():
        raise AuthorityError(
            "guardrail modification requires explicit external acceptance evidence"
        )


def assert_foreign_write_allowed(*, explicit_authority: bool) -> None:
    if not explicit_authority:
        raise AuthorityError("foreign repository/module write forbidden without explicit authority")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    load_constitution(args.root.resolve())
    print("PROJECT_AUTHORITY_CONSTITUTION_LOAD=PASS")
