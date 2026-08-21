---
schema_version: outgoing_prompt_artifact_v0_1
prompt_id: logistics_service_local_persistence_and_migration_boundary_v0_1
target_module: logistics_service
roadmap_step_id: logistics_service_local_persistence_and_migration_boundary_v0_1
title: Logistics Local Persistence and Migration Boundary v0.1
phase: local_persistence_and_migration_boundary_v0_1
priority: critical
created_at: '2026-08-21'
source_change: owner_intent_commercial_delivery_automation_horizon_2026_08_21
lifecycle_state: prepared
lineage:
  supersedes: null
prepared_at: '2026-08-21T09:50:25.116465Z'
prepared_from_sha256: 14ae1401b7fb8f267519f399e74d7c66c2e04b7126823728e745ec292ea3e246
---

# ForPrint machine prompt

```yaml
machine_prompt_version: forprint_machine_prompt_v0_1
module: logistics_service
roadmap_step_id: logistics_service_local_persistence_and_migration_boundary_v0_1
objective: Implement restart-safe module-local SQLite persistence behind the existing LogisticsRepository
  boundary without creating canonical ecosystem storage.
authority:
  module_repo_only: true
  blueprint_repo_writes: false
  live_provider_write: false
  automatic_cross_repository_write: false
implementation_obligations:
- id: IMP-001
  requirement: Preserve existing domain/public contracts; storage implementation stays behind repository
    interfaces.
  blocking: true
- id: IMP-002
  requirement: Add deterministic schema versioning and ordered migrations.
  blocking: true
- id: IMP-003
  requirement: Persist shipment drafts, tracking events, notification outbox, correlation/idempotency
    state and required audit metadata.
  blocking: true
- id: IMP-004
  requirement: Define transaction boundaries so partial writes cannot create contradictory workflow state.
  blocking: true
- id: IMP-005
  requirement: Provide storage-neutral export/import fixture for future central-storage migration.
  blocking: true
- id: IMP-006
  requirement: Add restart, migration-forward, migration-idempotency and repository-parity tests.
  blocking: true
- id: IMP-007
  requirement: Document local/non-canonical data classification, cleanup and migration boundary.
  blocking: true
- id: IMP-B01
  requirement: Preserve all prompt authority, ownership, forbidden-output, no-live-write and no-cross-repository
    boundaries.
  blocking: true
verification_obligations:
- id: VER-001
  verification: Run the module canonical make check and require zero blockers.
  blocking: true
- id: VER-002
  verification: Run focused persistence/migration tests twice against a fresh database.
  blocking: true
- id: VER-003
  verification: Restart/reopen the repository and prove persisted workflow state is restored deterministically.
  blocking: true
- id: VER-004
  verification: Apply migrations repeatedly and prove no duplicate/destructive side effects.
  blocking: true
- id: VER-005
  verification: Prove no provider network call or cross-repository write occurs.
  blocking: true
- id: VER-B01
  verification: Verify boundary confirmations, changed paths and execution evidence show no forbidden
    live provider write, secret leak, Blueprint write or cross-repository mutation.
  blocking: true
completion_evidence_obligations:
- id: CE-001
  evidence: exact implementation commit
  blocking: true
- id: CE-002
  evidence: exact test command and pass count
  blocking: true
- id: CE-003
  evidence: migration/restart verification output
  blocking: true
- id: CE-004
  evidence: changed-file inventory
  blocking: true
- id: CE-005
  evidence: module-side completion report and completion packet
  blocking: true
- id: CE-B01
  evidence: boundary confirmation evidence bound into the completion packet
  blocking: true
forbidden:
- canonical client/order database
- production provider credentials
- provider API writes
- SQLite-specific types in public domain contracts
- Blueprint repository writes
completion_protocol:
  produce_module_side_completion_report: true
  produce_module_side_completion_packet: true
  report_exact_commit_and_test_results: true
  do_not_claim_blueprint_acceptance: true
  do_not_release_next_prompt: true
acceptance_handoff:
  oracle_required: true
  prompt_contract_path: coordination/prompt_contracts/logistics_service/logistics_service_local_persistence_and_migration_boundary_v0_1/logistics_service_local_persistence_and_migration_boundary_v0_1__contract_v0_4_h7_v0_1.yaml
  acceptance_oracle_path: coordination/acceptance_oracles/logistics_service/logistics_service_local_persistence_and_migration_boundary_v0_1__acceptance_oracle_v0_1.yaml
  criteria:
  - criterion_id: AC-001
    step_id: logistics_service_local_persistence_and_migration_boundary_v0_1
    substep_id: logistics_service_local_persistence_and_migration_boundary_v0_1__01
    requirement_refs:
    - IMP-001
    - VER-001
    summary: 'Verify blocking substep: Define SQLite schema ownership and migration version contract'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_local_persistence_and_migration_boundary_v0_1__01
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-002
    step_id: logistics_service_local_persistence_and_migration_boundary_v0_1
    substep_id: logistics_service_local_persistence_and_migration_boundary_v0_1__02
    requirement_refs:
    - IMP-002
    - VER-002
    summary: 'Verify blocking substep: Implement repository adapter without leaking SQLite into domain
      services'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_local_persistence_and_migration_boundary_v0_1__02
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-003
    step_id: logistics_service_local_persistence_and_migration_boundary_v0_1
    substep_id: logistics_service_local_persistence_and_migration_boundary_v0_1__03
    requirement_refs:
    - IMP-003
    - VER-003
    summary: 'Verify blocking substep: Persist shipment drafts tracking events notification outbox and
      idempotency state'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_local_persistence_and_migration_boundary_v0_1__03
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-004
    step_id: logistics_service_local_persistence_and_migration_boundary_v0_1
    substep_id: logistics_service_local_persistence_and_migration_boundary_v0_1__04
    requirement_refs:
    - IMP-004
    - VER-004
    summary: 'Verify blocking substep: Add deterministic migration rollback/restart/export-import verification'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_local_persistence_and_migration_boundary_v0_1__04
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-005
    step_id: logistics_service_local_persistence_and_migration_boundary_v0_1
    substep_id: logistics_service_local_persistence_and_migration_boundary_v0_1__05
    requirement_refs:
    - IMP-005
    - VER-005
    summary: 'Verify blocking substep: Document local non-canonical data classification and central-storage
      handoff boundary'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_local_persistence_and_migration_boundary_v0_1__05
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-900
    step_id: logistics_service_local_persistence_and_migration_boundary_v0_1
    requirement_refs:
    - CE-001
    - CE-002
    - CE-003
    - CE-004
    - CE-005
    - IMP-006
    - IMP-007
    summary: Verify remaining prompt-contract obligations and the canonical full module gate.
    blocking: true
    verification:
      kind: command
      locator: make check
      expected_observation: Canonical module check exits successfully with zero blockers and the completion
        packet records the exact command/result.
    evidence_required:
    - EV-FULL-GATE
    - EV-COMPLETION-REPORT
  - criterion_id: AC-901
    step_id: logistics_service_local_persistence_and_migration_boundary_v0_1
    requirement_refs:
    - IMP-B01
    - VER-B01
    - CE-B01
    summary: Verify authority, ownership and no-live-write boundaries.
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet boundary_confirmations + changed-file inventory + completion report
      expected_observation: No forbidden provider write, production activation, secret leak, Blueprint
        repository write or cross-repository mutation occurred.
    evidence_required:
    - EV-BOUNDARY
    - EV-COMPLETION-REPORT
  completion_packet:
    required_schema: module_completion_packet_v0_4
    all_contract_obligations_must_have_requirement_results: true
    required_evidence_ids:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
    - EV-FULL-GATE
    - EV-BOUNDARY
    evidence_manifest_kinds:
    - report
    - test_output
    - governance_check
    - artifact
  operator_boundary:
    module_completion_does_not_equal_blueprint_acceptance: true
    automatic_accept: false
    automatic_release_next_prompt: false
```
