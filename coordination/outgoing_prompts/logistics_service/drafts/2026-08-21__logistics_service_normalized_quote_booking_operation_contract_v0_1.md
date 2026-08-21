---
schema_version: outgoing_prompt_artifact_v0_1
prompt_id: logistics_service_normalized_quote_booking_operation_contract_v0_1
target_module: logistics_service
roadmap_step_id: logistics_service_normalized_quote_booking_operation_contract_v0_1
title: Logistics Normalized Provider Operation Contract v0.1
phase: normalized_quote_booking_operation_contract_v0_1
priority: critical
created_at: '2026-08-21'
source_change: owner_intent_commercial_delivery_automation_horizon_2026_08_21
lifecycle_state: prepared
lineage:
  supersedes: null
prepared_at: '2026-08-21T09:50:25.962683Z'
prepared_from_sha256: 8f1531fe4baa2080c827ccd1d99f77b27c0997d157e32288cd4ab37e95f817e8
---

# ForPrint machine prompt

```yaml
machine_prompt_version: forprint_machine_prompt_v0_1
module: logistics_service
roadmap_step_id: logistics_service_normalized_quote_booking_operation_contract_v0_1
objective: Define storage/provider-neutral operation contracts for quote, booking preview, tracking and
  cancellation before implementing provider-specific adapters.
authority:
  module_repo_only: true
  blueprint_repo_writes: false
  live_provider_write: false
  automatic_cross_repository_write: false
implementation_obligations:
- id: IMP-001
  requirement: Define normalized quote request/result including service option, cost boundary, ETA boundary
    and provider metadata.
  blocking: true
- id: IMP-002
  requirement: Define booking preview and booking request/result with idempotency and dry_run fields.
  blocking: true
- id: IMP-003
  requirement: Define tracking request/result and normalized provider snapshot.
  blocking: true
- id: IMP-004
  requirement: Define cancellation request/result and unsupported-operation behavior.
  blocking: true
- id: IMP-005
  requirement: Define capability preflight before adapter operation dispatch.
  blocking: true
- id: IMP-006
  requirement: Extend normalized provider error taxonomy for validation, auth-not-ready, rate-limit, unavailable,
    timeout, unknown-result and unsupported capability.
  blocking: true
- id: IMP-007
  requirement: Keep provider raw payload only as safe adapter-local diagnostic metadata.
  blocking: true
- id: IMP-008
  requirement: Add contract fixtures for parcel, postal and on-demand courier families.
  blocking: true
- id: IMP-B01
  requirement: Preserve all prompt authority, ownership, forbidden-output, no-live-write and no-cross-repository
    boundaries.
  blocking: true
verification_obligations:
- id: VER-001
  verification: All provider-family fixtures satisfy the same public operation contracts.
  blocking: true
- id: VER-002
  verification: Unsupported operation fails before adapter mutation.
  blocking: true
- id: VER-003
  verification: dry_run cannot be silently converted to write mode.
  blocking: true
- id: VER-004
  verification: Idempotency key is mandatory for future mutation-capable operation contracts.
  blocking: true
- id: VER-005
  verification: No live network call exists in this step.
  blocking: true
- id: VER-B01
  verification: Verify boundary confirmations, changed paths and execution evidence show no forbidden
    live provider write, secret leak, Blueprint write or cross-repository mutation.
  blocking: true
completion_evidence_obligations:
- id: CE-001
  evidence: operation contract inventory
  blocking: true
- id: CE-002
  evidence: provider-family fixture matrix
  blocking: true
- id: CE-003
  evidence: contract-test output
  blocking: true
- id: CE-004
  evidence: no-live-call confirmation
  blocking: true
- id: CE-005
  evidence: completion report/packet
  blocking: true
- id: CE-B01
  evidence: boundary confirmation evidence bound into the completion packet
  blocking: true
forbidden:
- live provider calls
- provider payload as public domain model
- automatic provider booking
- Calculator final-price ownership
- Blueprint repository writes
completion_protocol:
  produce_module_side_completion_report: true
  produce_module_side_completion_packet: true
  report_exact_commit_and_test_results: true
  do_not_claim_blueprint_acceptance: true
  do_not_release_next_prompt: true
acceptance_handoff:
  oracle_required: true
  prompt_contract_path: coordination/prompt_contracts/logistics_service/logistics_service_normalized_quote_booking_operation_contract_v0_1/logistics_service_normalized_quote_booking_operation_contract_v0_1__contract_v0_4_h7_v0_1.yaml
  acceptance_oracle_path: coordination/acceptance_oracles/logistics_service/logistics_service_normalized_quote_booking_operation_contract_v0_1__acceptance_oracle_v0_1.yaml
  criteria:
  - criterion_id: AC-001
    step_id: logistics_service_normalized_quote_booking_operation_contract_v0_1
    substep_id: logistics_service_normalized_quote_booking_operation_contract_v0_1__01
    requirement_refs:
    - IMP-001
    - VER-001
    summary: 'Verify blocking substep: Define normalized quote request/result contracts'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_normalized_quote_booking_operation_contract_v0_1__01
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-002
    step_id: logistics_service_normalized_quote_booking_operation_contract_v0_1
    substep_id: logistics_service_normalized_quote_booking_operation_contract_v0_1__02
    requirement_refs:
    - IMP-002
    - VER-002
    summary: 'Verify blocking substep: Define booking preview/request/result contracts with idempotency'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_normalized_quote_booking_operation_contract_v0_1__02
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-003
    step_id: logistics_service_normalized_quote_booking_operation_contract_v0_1
    substep_id: logistics_service_normalized_quote_booking_operation_contract_v0_1__03
    requirement_refs:
    - IMP-003
    - VER-003
    summary: 'Verify blocking substep: Define tracking and cancellation operation contracts'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_normalized_quote_booking_operation_contract_v0_1__03
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-004
    step_id: logistics_service_normalized_quote_booking_operation_contract_v0_1
    substep_id: logistics_service_normalized_quote_booking_operation_contract_v0_1__04
    requirement_refs:
    - IMP-004
    - VER-004
    summary: 'Verify blocking substep: Define capability preflight and provider error normalization'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_normalized_quote_booking_operation_contract_v0_1__04
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-005
    step_id: logistics_service_normalized_quote_booking_operation_contract_v0_1
    substep_id: logistics_service_normalized_quote_booking_operation_contract_v0_1__05
    requirement_refs:
    - IMP-005
    - VER-005
    summary: 'Verify blocking substep: Define dry-run semantics and contract-test fixtures'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_normalized_quote_booking_operation_contract_v0_1__05
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-900
    step_id: logistics_service_normalized_quote_booking_operation_contract_v0_1
    requirement_refs:
    - CE-001
    - CE-002
    - CE-003
    - CE-004
    - CE-005
    - IMP-006
    - IMP-007
    - IMP-008
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
    step_id: logistics_service_normalized_quote_booking_operation_contract_v0_1
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
