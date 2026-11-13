#!/usr/bin/env python3
# Validate the v0.4.1 B2 persistence-boundary machine contract.

from __future__ import annotations

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

EXPECTED_CLASSES = {
    "declarative_governance",
    "coordination_runtime",
    "bulky_evidence",
    "secrets",
    "business_domain",
    "generated_projections",
}

EXPECTED_RUNTIME_FAMILIES = {
    "event_journal",
    "execution_runs",
    "execution_revalidations",
    "question_threads",
    "question_messages",
    "attention_events",
    "operator_decisions",
    "notification_deliveries",
    "worker_leases",
    "prompt_runtime_state",
    "module_runtime_state",
    "artifact_index",
    "idempotency_keys",
    "schema_migrations",
}

REQUIRED_GIT_REFERENCE_FIELDS = {
    "stable_id",
    "git_path",
    "git_commit",
    "sha256",
    "schema_version",
}


def load_contract() -> dict:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("B2 contract root must be a mapping")
    return data


def validate(data: dict) -> list[str]:
    errors: list[str] = []

    matrix = data.get("source_of_truth_matrix", {})
    if set(matrix) != EXPECTED_CLASSES:
        errors.append("source_of_truth_matrix classes are not exact")

    declarative = matrix.get("declarative_governance", {})
    if declarative.get("canonical_store") != "blueprint_git":
        errors.append("declarative governance must remain canonical in Blueprint Git")

    runtime = matrix.get("coordination_runtime", {})
    if runtime.get("canonical_store") != "future_coordination_store":
        errors.append("runtime class must target future CoordinationStore")

    secrets = matrix.get("secrets", {})
    for key in (
        "secret_values_allowed_in_git",
        "secret_values_allowed_in_prompt_text",
        "secret_values_allowed_in_coordination_event_payloads",
    ):
        if secrets.get(key) is not False:
            errors.append(f"{key} must be false")

    business = matrix.get("business_domain", {})
    if business.get("coordination_store_must_not_absorb_business_truth") is not True:
        errors.append("coordination store must not absorb business truth")

    dual = data.get("dual_truth_policy", {})
    if dual.get("independently_mutable_duplicate_of_git_authority_allowed") is not False:
        errors.append("dual mutable Git/DB truth must be forbidden")
    if set(dual.get("runtime_reference_to_git_requires", [])) != REQUIRED_GIT_REFERENCE_FIELDS:
        errors.append("Git runtime-reference fields are incomplete")

    store = data.get("future_coordination_store_contract", {})
    if store.get("interface_name") != "CoordinationStore":
        errors.append("future store interface must be CoordinationStore")
    if store.get("backend_specific_calls_outside_adapter_allowed") is not False:
        errors.append("backend-specific calls must remain behind adapter")
    if set(store.get("conceptual_schema_families", [])) != EXPECTED_RUNTIME_FAMILIES:
        errors.append("conceptual runtime schema families are incomplete")
    candidate = store.get("initial_backend_candidate", {})
    if candidate.get("technology") != "sqlite":
        errors.append("single-server backend candidate must remain SQLite")
    if candidate.get("activation_authorized_by_b2") is not False:
        errors.append("B2 must not authorize SQLite runtime activation")
    if candidate.get("database_binary_committed_to_git") is not False:
        errors.append("database binary must not be committed to Git")
    if store.get("migration_trigger_is_file_count") is not False:
        errors.append("file count must not trigger DB migration")

    retention = data.get("retention_backup_restore", {})
    sqlite_backup = retention.get("future_sqlite_backup", {})
    if sqlite_backup.get("sqlite_safe_backup_required") is not True:
        errors.append("future SQLite backup must use SQLite-safe mechanism")
    if sqlite_backup.get("naive_live_file_copy_allowed") is not False:
        errors.append("naive live SQLite file copy must be forbidden")
    if sqlite_backup.get("restore_test_required") is not True:
        errors.append("future restore tests must be required")

    separation = data.get("business_storage_separation", {})
    if separation.get("coordination_depends_on_business_database") is not False:
        errors.append("coordination must not depend on business DB")
    if separation.get("separate_ownership_required") is not True:
        errors.append("coordination/business ownership must remain separate")

    capabilities = data.get("current_capabilities", {})
    for key, value in capabilities.items():
        if value is not False:
            errors.append(f"current capability must remain false: {key}")

    acceptance = data.get("acceptance", {})
    if not acceptance or not all(value is True for value in acceptance.values()):
        errors.append("all B2 acceptance contract declarations must be true")

    return errors


def main() -> int:
    try:
        data = load_contract()
        errors = validate(data)
    except Exception as exc:
        print(f"B2 persistence boundary validation FAILED: {exc}")
        return 1

    if errors:
        print("B2 persistence boundary validation FAILED")
        for item in errors:
            print(f"- {item}")
        return 1

    print("B2 persistence boundary validation PASSED")
    print(f"contract={CONTRACT.relative_to(ROOT)}")
    print("source_of_truth_classes=6")
    print("runtime_schema_families=14")
    print("live_sqlite_runtime_enabled=false")
    print("daemon_enabled=false")
    print("autonomous_execution_enabled=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
