from __future__ import annotations

from scripts.validation.validate_module_continuity_transfer_v0_1 import (
    EXPECTED_HISTORICAL_CORE_HASHES,
    REQUIRED_PROFILE_FIELDS,
    REQUIRED_SURFACES,
    run_validation,
    validate_contract,
    validate_core_hashes,
)


def test_transfer_contract_is_authority_neutral_and_module_agnostic() -> None:
    contract = validate_contract()
    assert contract["authority"] == "none"
    assert contract["mutation_authority_conferred"] is False
    assert contract["release_authority_conferred"] is False
    assert contract["worker_dispatch_authority_conferred"] is False
    assert contract["foreign_repository_write_authority_conferred"] is False
    assert contract["required_profile_fields"] == REQUIRED_PROFILE_FIELDS
    assert {row["id"] for row in contract["portable_surfaces"]} == REQUIRED_SURFACES


def test_historical_core_baseline_and_current_validated_core_are_both_bound() -> None:
    result = validate_core_hashes()
    assert len(EXPECTED_HISTORICAL_CORE_HASHES) == 4
    assert result["historical_accepted_core_sha256"] == EXPECTED_HISTORICAL_CORE_HASHES
    assert result["historical_reference_acceptance_rewritten"] is False
    assert result["current_core_byte_identity_to_reference_required"] is False
    assert isinstance(result["current_validated_under_work_id"], str)
    assert result["current_validated_under_work_id"].strip()
    assert set(result["current_validated_core_sha256"]) == set(EXPECTED_HISTORICAL_CORE_HASHES)
    assert result["actual_current_core_sha256"] == result["current_validated_core_sha256"]


def test_sterile_catalog_and_warehouse_topologies_prove_portable_surfaces() -> None:
    result = run_validation()
    assert result["portable_event_store"] is True
    assert result["portable_lifecycle"] is True
    assert result["portable_projections"] is True
    assert result["portable_handoff"] is True
    assert result["sterile_catalog_fixture"] == "PASS"
    assert result["sterile_warehouse_fixture"] == "PASS"
    assert result["blueprint_specific_paths_in_portable_contract"] == 0


def test_invalid_transition_fails_without_event_or_source_mutation() -> None:
    result = run_validation()
    assert result["invalid_transition_event_appended"] is False
    assert result["invalid_transition_mutation_performed"] is False
