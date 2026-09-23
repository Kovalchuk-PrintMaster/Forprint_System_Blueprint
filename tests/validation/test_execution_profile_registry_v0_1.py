from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/coordination/execution_profiles_v0_1.py"
spec = importlib.util.spec_from_file_location(
    "_execution_profiles_test_runtime",
    SOURCE,
)
assert spec is not None and spec.loader is not None
profiles = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = profiles
spec.loader.exec_module(profiles)


def test_registry_contains_exact_initial_profiles() -> None:
    assert set(profiles.list_profile_refs(ROOT)) == {
        "deep-readonly-analysis@r1",
        "deep-dev@r1",
        "standard-dev@r1",
        "light-maintenance@r1",
    }


def test_deep_readonly_profile_cannot_write() -> None:
    profile = profiles.get_profile(
        ROOT,
        "deep-readonly-analysis@r1",
    )
    assert set(profile["authority_policy"]["capability_ceiling"]) == {"read"}


def test_model_backend_is_replaceable_and_unbound() -> None:
    for ref in profiles.list_profile_refs(ROOT):
        profile = profiles.get_profile(ROOT, ref)
        reasoning = profile["reasoning_policy"]
        assert reasoning["backend"] == "replaceable"
        assert "provider" not in reasoning
        assert "model" not in reasoning
        assert "model_id" not in reasoning


def test_effective_authority_is_intersection() -> None:
    resolved = profiles.resolve_profile(
        ROOT,
        "deep-dev@r1",
        higher_authority_permissions={"read"},
        higher_budget_tier="HIGH",
        work_front_permissions={"read", "write_blueprint"},
        work_front_budget_tier="HIGH",
    )
    assert resolved["effective_authority_permissions"] == ["read"]
    assert resolved["dispatch_authority"] is False


def test_work_front_can_narrow_profile() -> None:
    resolved = profiles.resolve_profile(
        ROOT,
        "deep-dev@r1",
        higher_authority_permissions={"read", "write_blueprint"},
        higher_budget_tier="HIGH",
        work_front_permissions={"read"},
        work_front_budget_tier="HIGH",
    )
    assert resolved["effective_authority_permissions"] == ["read"]


def test_budget_uses_most_restrictive_tier() -> None:
    resolved = profiles.resolve_profile(
        ROOT,
        "deep-dev@r1",
        higher_authority_permissions={"read", "write_blueprint"},
        higher_budget_tier="STANDARD",
        work_front_permissions={"read", "write_blueprint"},
        work_front_budget_tier="HIGH",
    )
    assert resolved["effective_budget_tier"] == "STANDARD"


def test_profile_ref_is_attempt_ledger_compatible_string() -> None:
    profile = profiles.get_profile(ROOT, "standard-dev@r1")
    assert profiles.profile_ref(profile) == "standard-dev@r1"


def test_recommendation_is_not_dispatch_authority() -> None:
    result = profiles.recommend_profile(
        ROOT,
        mutation_expected=False,
        complexity="DEEP",
    )
    assert result["recommended_profile_ref"] == "deep-readonly-analysis@r1"
    assert result["recommendation_only"] is True
    assert result["dispatch_authority"] is False


def test_non_widening_operator_override_is_allowed() -> None:
    result = profiles.select_profile(
        ROOT,
        "deep-dev@r1",
        operator_override_ref="standard-dev@r1",
    )
    assert result["selected_profile_ref"] == "standard-dev@r1"
    assert result["selection_basis"] == "OPERATOR_OVERRIDE_NON_WIDENING"
    assert result["dispatch_authority"] is False


def test_widening_operator_override_requires_escalation() -> None:
    with pytest.raises(
        profiles.ExecutionProfileError,
        match="explicit escalation evidence required",
    ):
        profiles.select_profile(
            ROOT,
            "light-maintenance@r1",
            operator_override_ref="deep-dev@r1",
        )

    result = profiles.select_profile(
        ROOT,
        "light-maintenance@r1",
        operator_override_ref="deep-dev@r1",
        escalation_evidence="operator:test-approved",
    )
    assert result["selection_basis"] == "OPERATOR_OVERRIDE_WITH_ESCALATION_EVIDENCE"
    assert result["dispatch_authority"] is False


def test_unknown_profile_fails_closed() -> None:
    with pytest.raises(
        profiles.ExecutionProfileError,
        match="profile ref not found",
    ):
        profiles.get_profile(ROOT, "missing-profile@r1")
