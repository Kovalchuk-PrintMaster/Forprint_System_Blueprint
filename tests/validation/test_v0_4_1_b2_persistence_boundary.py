from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "coordination"
    / "standards"
    / "governance"
    / "coordination_data_classification_and_persistence_boundary_v0_1.yaml"
)
DOC = CONTRACT.with_suffix(".md")
VALIDATOR = ROOT / "scripts/validation/validate_b2_persistence_boundary.py"


def load_contract() -> dict:
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


def test_b2_source_of_truth_matrix_is_explicit() -> None:
    data = load_contract()
    matrix = data["source_of_truth_matrix"]

    assert matrix["declarative_governance"]["canonical_store"] == "blueprint_git"
    assert matrix["coordination_runtime"]["canonical_store"] == ("future_coordination_store")
    assert matrix["bulky_evidence"]["canonical_store"] == ("filesystem_artifact_store")
    assert matrix["secrets"]["canonical_store"] == "dedicated_secret_storage"
    assert matrix["business_domain"]["canonical_store"] == ("forprint_business_storage")
    assert matrix["generated_projections"]["authority"] == ("rebuildable_noncanonical")


def test_b2_forbids_dual_mutable_truth_and_binds_git_identity() -> None:
    data = load_contract()
    policy = data["dual_truth_policy"]

    assert policy["independently_mutable_duplicate_of_git_authority_allowed"] is False
    assert set(policy["runtime_reference_to_git_requires"]) == {
        "stable_id",
        "git_path",
        "git_commit",
        "sha256",
        "schema_version",
    }


def test_b2_coordination_store_is_migration_ready_but_not_activated() -> None:
    data = load_contract()
    store = data["future_coordination_store_contract"]
    candidate = store["initial_backend_candidate"]

    assert store["interface_name"] == "CoordinationStore"
    assert store["backend_specific_calls_outside_adapter_allowed"] is False
    assert "schema_migrations" in store["conceptual_schema_families"]
    assert "idempotency_keys" in store["conceptual_schema_families"]
    assert candidate["technology"] == "sqlite"
    assert candidate["wal_mode"] == "required_if_activated"
    assert candidate["activation_authorized_by_b2"] is False
    assert candidate["database_binary_committed_to_git"] is False


def test_b2_retention_backup_restore_and_business_separation() -> None:
    data = load_contract()
    retention = data["retention_backup_restore"]
    separation = data["business_storage_separation"]

    assert retention["runtime_projections"]["retention"] == "rebuildable"
    assert retention["append_only_runtime_audit"]["projection_cleanup_may_delete"] is False
    assert retention["future_sqlite_backup"]["sqlite_safe_backup_required"] is True
    assert retention["future_sqlite_backup"]["naive_live_file_copy_allowed"] is False
    assert retention["future_sqlite_backup"]["restore_test_required"] is True
    assert separation["coordination_depends_on_business_database"] is False
    assert separation["separate_ownership_required"] is True


def test_b2_current_runtime_capabilities_remain_disabled() -> None:
    data = load_contract()
    capabilities = data["current_capabilities"]

    assert capabilities
    assert all(value is False for value in capabilities.values())


def test_b2_human_contract_states_non_goals_and_acceptance_gate() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "B2 acceptance gates" in text
    assert "No dual mutable truth" in text
    assert "live SQLite, daemon, systemd, autonomous execution" in text
    assert "create a `.sqlite`, `.sqlite3` or `.db` runtime file" in text


def test_b2_validator_passes() -> None:
    cp = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout + cp.stderr
    assert "B2 persistence boundary validation PASSED" in cp.stdout
