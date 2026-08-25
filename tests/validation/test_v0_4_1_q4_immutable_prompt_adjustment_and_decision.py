from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from scripts.run_blueprint_checks import build_checks

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/immutable_prompt_adjustment_and_decision_v0_1.yaml"
DOC = CONTRACT.with_suffix(".md")
VALIDATOR = ROOT / "scripts/validation/validate_q4_immutable_prompt_adjustment_and_decision.py"


def load_contract() -> dict:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_released_prompt_is_immutable_and_changes_are_separate_artifacts() -> None:
    immutable = load_contract()["released_prompt_immutability"]
    assert immutable["released_prompt_is_immutable_execution_contract"] is True
    assert immutable["edit_released_requirements_allowed"] is False
    assert immutable["delete_released_requirements_allowed"] is False
    assert immutable["silent_rewrite_allowed"] is False
    assert immutable["post_release_change_requires_correlated_artifact"] is True
    assert immutable["unexecuted_requirement_may_disappear"] is False


def test_q4_artifact_type_vocabulary_is_exact() -> None:
    model = load_contract()["artifact_model"]
    assert set(model["canonical_artifact_types"]) == {
        "operator_decision",
        "scope_adjustment",
        "waiver",
        "skip_optional",
        "clarification_resolution",
        "blocker_resolution",
        "cancellation",
        "follow_up_prompt",
        "superseding_prompt",
    }
    assert model["published_artifacts_append_only"] is True
    assert model["correction_rewrites_prior_artifact"] is False
    assert model["correction_uses_superseding_artifact"] is True


def test_q4_artifacts_require_correlation_target_effects_and_evidence() -> None:
    model = load_contract()["artifact_model"]
    for field in (
        "decision_id",
        "prompt_id",
        "module_id",
        "roadmap_step_id",
        "correlation_id",
        "target_refs",
        "execution_effect",
        "acceptance_effect",
        "evidence_refs",
    ):
        assert field in model["required_fields"]
    assert model["target_refs_min_items"] == 1
    assert model["evidence_refs_required"] is True
    assert model["whole_prompt_effect_requires_explicit_whole_prompt_target"] is True


def test_scope_change_waiver_and_project_truth_changes_preserve_manual_authority() -> None:
    authority = load_contract()["authority_boundary"]
    assert authority["scope_adjustment_manual"] is True
    assert authority["waiver_manual"] is True
    assert authority["waiver_inferred_from_omission"] is False
    assert authority["waiver_inferred_from_unable_to_execute"] is False
    assert authority["clarification_resolution_may_bypass_manual_scope_change"] is False
    assert authority["blocker_resolution_may_bypass_manual_scope_change"] is False
    assert authority["follow_up_prompt_auto_release"] is False


def test_skip_optional_and_resolutions_cannot_silently_change_requirements() -> None:
    semantics = load_contract()["artifact_semantics"]
    assert semantics["skip_optional_required_target_allowed"] is False
    assert semantics["clarification_resolution_rewrites_q1_q2_history"] is False
    assert semantics["material_clarification_change_requires_additional_adjustment_artifact"] is True
    assert semantics["blocker_resolution_rewrites_q3_history"] is False
    assert semantics["superseded_prompt_history_deleted"] is False


def test_execution_and_acceptance_effects_are_bounded_not_auto_accept() -> None:
    data = load_contract()
    assert set(data["execution_effects"]["values"]) == {
        "no_execution_change",
        "clarify_only",
        "apply_scope_adjustment",
        "skip_optional",
        "resume_affected_scope",
        "cancel_affected_scope",
        "cancel_prompt",
        "require_follow_up_prompt",
        "supersede_prompt",
    }
    assert data["execution_effects"]["effect_is_authority_grant"] is False
    assert set(data["acceptance_effects"]["values"]) == {
        "no_acceptance_change",
        "acceptance_scope_adjusted",
        "waived_requirement",
        "optional_item_excluded",
        "completion_requires_follow_up",
        "prompt_cancelled",
        "prompt_superseded",
    }
    assert data["acceptance_effects"]["effect_is_automatic_prompt_acceptance"] is False


def test_completion_report_must_expose_deviations_or_none() -> None:
    completion = load_contract()["completion_reporting"]
    assert completion["required_section"] == "Execution deviations / operator decisions"
    assert completion["section_omission_allowed"] is False
    assert completion["explicit_none_allowed"] is True
    assert completion["decision_ids_required_when_present"] is True
    assert completion["target_refs_required_when_present"] is True


def test_q4_correlation_does_not_consume_q5_event_envelope() -> None:
    correlation = load_contract()["correlation"]
    assert correlation["correlation_id_required"] is True
    assert correlation["q5_causation_id_defined_by_q4"] is False
    assert correlation["event_envelope_defined_by_q4"] is False


def test_q5_q8_and_runtime_remain_deferred() -> None:
    data = load_contract()
    assert all(data["deferred_boundaries"].values())
    assert all(value is False for value in data["current_capabilities"].values())


def test_human_standard_contains_required_q4_semantics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for fragment in (
        "A released prompt is an immutable execution contract.",
        "Canonical correlated artifact types",
        "`scope_adjustment`",
        "`waiver`",
        "`clarification_resolution`",
        "`blocker_resolution`",
        "No disappearing requirements",
        "Append-only correction model",
        "Manual authority boundary",
        "Execution deviations / operator decisions",
        "explicitly state `none`",
        "does not itself release another prompt",
        "Separation from Q5-Q8",
        "Runtime boundary",
    ):
        assert fragment in text


def test_q4_validator_passes() -> None:
    cp = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "Q4 immutable prompt adjustment and operator decision validation PASSED" in cp.stdout


def test_q4_validator_is_in_canonical_check_catalog() -> None:
    checks = {check.check_id: check for check in build_checks()}
    check = checks["q4_immutable_prompt_adjustment_and_decision_validation"]
    assert check.title == "Q4 immutable prompt decisions"
    assert check.command[-1] == "scripts/validation/validate_q4_immutable_prompt_adjustment_and_decision.py"
