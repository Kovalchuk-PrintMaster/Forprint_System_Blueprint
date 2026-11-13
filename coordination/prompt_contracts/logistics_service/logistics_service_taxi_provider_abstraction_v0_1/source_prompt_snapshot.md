---
schema_version: outgoing_prompt_artifact_v0_1
prompt_id: logistics_service_taxi_provider_abstraction_v0_1
target_module: logistics_service
roadmap_step_id: logistics_service_taxi_provider_abstraction_v0_1
title: Logistics On-demand Courier Abstraction v0.1
phase: taxi_provider_abstraction_v0_1
priority: high
created_at: '2026-08-21'
source_change: owner_intent_commercial_delivery_automation_horizon_2026_08_21
lifecycle_state: prepared
lineage:
  supersedes: null
prepared_at: '2026-08-21T09:50:26.772244Z'
prepared_from_sha256: c128cf06cf37c7a6c5c3baccc56295e6a163c3b2d94142346ea69b7e2701cabe
---

# ForPrint machine prompt

```yaml
machine_prompt_version: forprint_machine_prompt_v0_1
module: logistics_service
roadmap_step_id: logistics_service_taxi_provider_abstraction_v0_1
objective: Model taxi/local-courier delivery as an on-demand provider family without forcing postal parcel/TTN
  assumptions.
authority:
  module_repo_only: true
  blueprint_repo_writes: false
  live_provider_write: false
  automatic_cross_repository_write: false
implementation_obligations:
- id: IMP-001
  requirement: Define pickup and dropoff snapshots with contact and location hints.
  blocking: true
- id: IMP-002
  requirement: Define cargo snapshot independent from postal parcel identifiers.
  blocking: true
- id: IMP-003
  requirement: Define on-demand service option including quote/ETA capability fields.
  blocking: true
- id: IMP-004
  requirement: Define booking-preview contract mapping onto normalized provider operations.
  blocking: true
- id: IMP-005
  requirement: Define pickup-arrived, courier-assigned and delivery-arrived normalized event semantics
    where evidence exists.
  blocking: true
- id: IMP-006
  requirement: Represent provider capability differences rather than assuming Uklon/Bolt/Uber parity.
  blocking: true
- id: IMP-007
  requirement: Add synthetic providers showing different capability sets and fallback behavior.
  blocking: true
- id: IMP-B01
  requirement: Preserve all prompt authority, ownership, forbidden-output, no-live-write and no-cross-repository
    boundaries.
  blocking: true
verification_obligations:
- id: VER-001
  verification: Postal-only fields are not mandatory for on-demand providers.
  blocking: true
- id: VER-002
  verification: Synthetic providers with missing quote/tracking/cancel capability fail or degrade predictably.
  blocking: true
- id: VER-003
  verification: No concrete provider is hard-coded as mandatory.
  blocking: true
- id: VER-004
  verification: No live courier order is created.
  blocking: true
- id: VER-005
  verification: Module canonical check is green.
  blocking: true
- id: VER-B01
  verification: Verify boundary confirmations, changed paths and execution evidence show no forbidden
    live provider write, secret leak, Blueprint write or cross-repository mutation.
  blocking: true
completion_evidence_obligations:
- id: CE-001
  evidence: on-demand domain contract
  blocking: true
- id: CE-002
  evidence: capability-difference fixture matrix
  blocking: true
- id: CE-003
  evidence: preview tests
  blocking: true
- id: CE-004
  evidence: no-live-write proof
  blocking: true
- id: CE-005
  evidence: completion report/packet
  blocking: true
- id: CE-B01
  evidence: boundary confirmation evidence bound into the completion packet
  blocking: true
forbidden:
- live taxi/courier booking
- mandatory TTN semantics
- hard-coded provider priority in adapter
- Blueprint repository writes
completion_protocol:
  produce_module_side_completion_report: true
  produce_module_side_completion_packet: true
  report_exact_commit_and_test_results: true
  do_not_claim_blueprint_acceptance: true
  do_not_release_next_prompt: true
acceptance_handoff:
  oracle_required: true
  prompt_contract_path: coordination/prompt_contracts/logistics_service/logistics_service_taxi_provider_abstraction_v0_1/logistics_service_taxi_provider_abstraction_v0_1__contract_v0_4_h7_v0_1.yaml
  acceptance_oracle_path: coordination/acceptance_oracles/logistics_service/logistics_service_taxi_provider_abstraction_v0_1__acceptance_oracle_v0_1.yaml
  criteria:
  - criterion_id: AC-001
    step_id: logistics_service_taxi_provider_abstraction_v0_1
    substep_id: logistics_service_taxi_provider_abstraction_v0_1__01
    requirement_refs:
    - IMP-001
    - VER-001
    summary: 'Verify blocking substep: Define pickup dropoff cargo and contact snapshots'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_taxi_provider_abstraction_v0_1__01
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-002
    step_id: logistics_service_taxi_provider_abstraction_v0_1
    substep_id: logistics_service_taxi_provider_abstraction_v0_1__02
    requirement_refs:
    - IMP-002
    - VER-002
    summary: 'Verify blocking substep: Define on-demand service option quote and ETA semantics'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_taxi_provider_abstraction_v0_1__02
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-003
    step_id: logistics_service_taxi_provider_abstraction_v0_1
    substep_id: logistics_service_taxi_provider_abstraction_v0_1__03
    requirement_refs:
    - IMP-003
    - VER-003
    summary: 'Verify blocking substep: Define courier-arrival pickup and delivery lifecycle events'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_taxi_provider_abstraction_v0_1__03
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-004
    step_id: logistics_service_taxi_provider_abstraction_v0_1
    substep_id: logistics_service_taxi_provider_abstraction_v0_1__04
    requirement_refs:
    - IMP-004
    - VER-004
    summary: 'Verify blocking substep: Define capability differences from parcel providers'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_taxi_provider_abstraction_v0_1__04
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-005
    step_id: logistics_service_taxi_provider_abstraction_v0_1
    substep_id: logistics_service_taxi_provider_abstraction_v0_1__05
    requirement_refs:
    - IMP-005
    - VER-005
    summary: 'Verify blocking substep: Add synthetic multi-provider booking-preview fixtures'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_taxi_provider_abstraction_v0_1__05
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-900
    step_id: logistics_service_taxi_provider_abstraction_v0_1
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
    step_id: logistics_service_taxi_provider_abstraction_v0_1
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
