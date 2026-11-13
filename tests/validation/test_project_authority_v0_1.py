from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/coordination/project_authority_v0_1.py"

spec = importlib.util.spec_from_file_location("_project_authority_test", SOURCE)
assert spec is not None and spec.loader is not None
pa = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pa
spec.loader.exec_module(pa)


def test_constitution_loads_and_has_exact_precedence() -> None:
    data = pa.load_constitution(ROOT)
    assert tuple(data["authority_precedence"]["order"]) == pa.EXPECTED_PRECEDENCE


def test_lower_layers_may_narrow() -> None:
    effective = pa.resolve_effective_permissions(
        [
            ("PROJECT_CONSTITUTION", {"read", "write", "dispatch"}),
            ("MODULE_POLICY", {"read", "write"}),
            ("EXECUTION_PROFILE", {"read"}),
            ("WORK_FRONT", {"read"}),
        ]
    )
    assert effective == {"read"}


def test_lower_layer_widening_fails_without_explicit_gate() -> None:
    with pytest.raises(pa.AuthorityError, match="authority widening"):
        pa.resolve_effective_permissions(
            [
                ("PROJECT_CONSTITUTION", {"read"}),
                ("MODULE_POLICY", {"read", "write"}),
            ]
        )


def test_evidence_bound_operator_gate_can_explicitly_widen() -> None:
    gate = pa.WideningGate(
        approved=True,
        approver_class="OPERATOR_OR_HIGHER_CANONICAL_AUTHORITY",
        evidence_ref="decision:test-explicit-widening",
    )
    effective = pa.resolve_effective_permissions(
        [
            ("PROJECT_CONSTITUTION", {"read"}),
            ("MODULE_POLICY", {"read", "write"}),
        ],
        widening_gate=gate,
    )
    assert effective == {"read", "write"}


def test_wrong_precedence_order_fails() -> None:
    with pytest.raises(pa.AuthorityError, match="precedence order"):
        pa.resolve_effective_permissions(
            [
                ("PROJECT_CONSTITUTION", {"read"}),
                ("WORK_FRONT", {"read"}),
            ]
        )


def test_ai_cannot_modify_and_self_certify_guardrail() -> None:
    with pytest.raises(pa.AuthorityError, match="self-certify"):
        pa.assert_guardrail_change_allowed(
            actor="blueprint_ai",
            modifies_own_guardrails=True,
            self_certifies_acceptance=True,
            external_acceptance_evidence="operator:later",
        )


def test_guardrail_change_requires_external_evidence() -> None:
    with pytest.raises(pa.AuthorityError, match="external acceptance evidence"):
        pa.assert_guardrail_change_allowed(
            actor="blueprint_ai",
            modifies_own_guardrails=True,
            self_certifies_acceptance=False,
            external_acceptance_evidence=None,
        )


def test_foreign_write_is_fail_closed() -> None:
    with pytest.raises(pa.AuthorityError, match="foreign"):
        pa.assert_foreign_write_allowed(explicit_authority=False)
