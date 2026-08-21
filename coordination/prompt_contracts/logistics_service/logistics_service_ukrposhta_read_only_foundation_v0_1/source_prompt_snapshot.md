---
schema_version: outgoing_prompt_artifact_v0_1
prompt_id: logistics_service_ukrposhta_read_only_foundation_v0_1
target_module: logistics_service
roadmap_step_id: logistics_service_ukrposhta_read_only_foundation_v0_1
title: Logistics Ukrposhta Read-only Foundation v0.1
phase: ukrposhta_read_only_foundation_v0_1
priority: high
created_at: '2026-08-21'
source_change: owner_intent_commercial_delivery_automation_horizon_2026_08_21
lifecycle_state: prepared
lineage:
  supersedes: null
prepared_at: '2026-08-21T09:50:26.493147Z'
prepared_from_sha256: 0e4e53c78845cbb64a1a4908967890b8f1ee3dcee77dbfbbfa05f884f7f029da
---

# ForPrint machine prompt

```yaml
machine_prompt_version: forprint_machine_prompt_v0_1
module: logistics_service
roadmap_step_id: logistics_service_ukrposhta_read_only_foundation_v0_1
objective: Implement Ukrposhta through the same normalized provider contracts in read-only/dry-run mode
  and prove cross-provider interchangeability.
authority:
  module_repo_only: true
  blueprint_repo_writes: false
  live_provider_write: false
  automatic_cross_repository_write: false
implementation_obligations:
- id: IMP-001
  requirement: Create Ukrposhta runtime profile and capability mapping from current official provider
    documentation available to the module.
  blocking: true
- id: IMP-002
  requirement: Implement sanitized configuration with no secret material.
  blocking: true
- id: IMP-003
  requirement: Implement address/branch/service lookup boundaries when supported.
  blocking: true
- id: IMP-004
  requirement: Implement tracking read path and normalized status/event mapping.
  blocking: true
- id: IMP-005
  requirement: Implement shipment/quote preview mappings where supported.
  blocking: true
- id: IMP-006
  requirement: Normalize provider-specific errors and unsupported operations.
  blocking: true
- id: IMP-007
  requirement: Add parity tests comparing the same public contracts with Nova Poshta fixtures.
  blocking: true
- id: IMP-B01
  requirement: Preserve all prompt authority, ownership, forbidden-output, no-live-write and no-cross-repository
    boundaries.
  blocking: true
verification_obligations:
- id: VER-001
  verification: No provider write is enabled.
  blocking: true
- id: VER-002
  verification: No real credential exists in git.
  blocking: true
- id: VER-003
  verification: Common provider contract tests pass for both parcel/postal adapters.
  blocking: true
- id: VER-004
  verification: Provider-specific types do not escape the adapter.
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
  evidence: capability matrix
  blocking: true
- id: CE-002
  evidence: cross-provider parity tests
  blocking: true
- id: CE-003
  evidence: sanitized configuration
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
- real shipment creation
- real credentials
- provider-specific orchestration branches
- Blueprint repository writes
completion_protocol:
  produce_module_side_completion_report: true
  produce_module_side_completion_packet: true
  report_exact_commit_and_test_results: true
  do_not_claim_blueprint_acceptance: true
  do_not_release_next_prompt: true
acceptance_handoff:
  oracle_required: true
  prompt_contract_path: coordination/prompt_contracts/logistics_service/logistics_service_ukrposhta_read_only_foundation_v0_1/logistics_service_ukrposhta_read_only_foundation_v0_1__contract_v0_4_h7_v0_1.yaml
  acceptance_oracle_path: coordination/acceptance_oracles/logistics_service/logistics_service_ukrposhta_read_only_foundation_v0_1__acceptance_oracle_v0_1.yaml
  criteria:
  - criterion_id: AC-001
    step_id: logistics_service_ukrposhta_read_only_foundation_v0_1
    substep_id: logistics_service_ukrposhta_read_only_foundation_v0_1__01
    requirement_refs:
    - IMP-001
    - VER-001
    summary: 'Verify blocking substep: Map Ukrposhta provider profile and capabilities'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_ukrposhta_read_only_foundation_v0_1__01
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-002
    step_id: logistics_service_ukrposhta_read_only_foundation_v0_1
    substep_id: logistics_service_ukrposhta_read_only_foundation_v0_1__02
    requirement_refs:
    - IMP-002
    - VER-002
    summary: 'Verify blocking substep: Implement address branch and service lookup boundary'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_ukrposhta_read_only_foundation_v0_1__02
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-003
    step_id: logistics_service_ukrposhta_read_only_foundation_v0_1
    substep_id: logistics_service_ukrposhta_read_only_foundation_v0_1__03
    requirement_refs:
    - IMP-003
    - VER-003
    summary: 'Verify blocking substep: Implement tracking read path and normalized status mapping'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_ukrposhta_read_only_foundation_v0_1__03
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-004
    step_id: logistics_service_ukrposhta_read_only_foundation_v0_1
    substep_id: logistics_service_ukrposhta_read_only_foundation_v0_1__04
    requirement_refs:
    - IMP-004
    - VER-004
    summary: 'Verify blocking substep: Implement shipment and quote preview mapping where supported'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_ukrposhta_read_only_foundation_v0_1__04
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-005
    step_id: logistics_service_ukrposhta_read_only_foundation_v0_1
    substep_id: logistics_service_ukrposhta_read_only_foundation_v0_1__05
    requirement_refs:
    - IMP-005
    - VER-005
    summary: 'Verify blocking substep: Add sanitized configuration and contract parity tests'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_ukrposhta_read_only_foundation_v0_1__05
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-900
    step_id: logistics_service_ukrposhta_read_only_foundation_v0_1
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
    step_id: logistics_service_ukrposhta_read_only_foundation_v0_1
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
  - criterion_id: AC-902
    step_id: logistics_service_ukrposhta_read_only_foundation_v0_1
    requirement_refs:
    - IMP-001
    summary: Verify provider capability claims are grounded in current official documentation or are explicitly
      marked unavailable/unknown.
    blocking: true
    verification:
      kind: artifact
      locator: EV-PROVIDER-RESEARCH
      expected_observation: Provider capability evidence cites current official documentation available
        during implementation. Any unavailable or unverified capability is recorded as unknown/unsupported
        and fails closed; no behavior is invented from assumptions.
    evidence_required:
    - EV-PROVIDER-RESEARCH
    - EV-COMPLETION-REPORT
  completion_packet:
    required_schema: module_completion_packet_v0_4
    all_contract_obligations_must_have_requirement_results: true
    required_evidence_ids:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
    - EV-FULL-GATE
    - EV-BOUNDARY
    - EV-PROVIDER-RESEARCH
    evidence_manifest_kinds:
    - report
    - test_output
    - governance_check
    - artifact
  operator_boundary:
    module_completion_does_not_equal_blueprint_acceptance: true
    automatic_accept: false
    automatic_release_next_prompt: false
provider_research_policy:
  official_documentation_preferred: true
  capture_research_evidence: true
  evidence_id: EV-PROVIDER-RESEARCH
  fail_closed_when_official_evidence_unavailable: true
  invent_capabilities_from_assumptions: false
  unverified_capability_state: unknown_or_unsupported
  live_write_from_unverified_capability: false
  record_blocker_or_limitation_in_completion_report: true
```
