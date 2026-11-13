---
schema_version: outgoing_prompt_artifact_v0_1
prompt_id: logistics_service_uklon_delivery_read_only_foundation_v0_1
target_module: logistics_service
roadmap_step_id: logistics_service_uklon_delivery_read_only_foundation_v0_1
title: Logistics Uklon Delivery Read-only Foundation v0.1
phase: uklon_delivery_read_only_foundation_v0_1
priority: high
created_at: '2026-08-21'
source_change: owner_intent_commercial_delivery_automation_horizon_2026_08_21
lifecycle_state: prepared
lineage:
  supersedes: null
prepared_at: '2026-08-21T09:50:27.058842Z'
prepared_from_sha256: cb02644be329f8cf23510bd38b580629dd0a9ec34684f74e07a5d410d550caa8
---

# ForPrint machine prompt

```yaml
machine_prompt_version: forprint_machine_prompt_v0_1
module: logistics_service
roadmap_step_id: logistics_service_uklon_delivery_read_only_foundation_v0_1
objective: Implement one concrete on-demand delivery adapter in read-only/dry-run mode, mapping only capabilities
  actually available from the provider environment.
authority:
  module_repo_only: true
  blueprint_repo_writes: false
  live_provider_write: false
  automatic_cross_repository_write: false
implementation_obligations:
- id: IMP-001
  requirement: Inspect current official Uklon Delivery integration documentation available to the module
    and record supported capabilities/environment assumptions.
  blocking: true
- id: IMP-002
  requirement: Map Uklon provider profile and service/product capabilities into the generic on-demand
    contract.
  blocking: true
- id: IMP-003
  requirement: Implement sanitized environment configuration with no real credentials.
  blocking: true
- id: IMP-004
  requirement: Implement dry-run quote/payload preview surface only for supported operations.
  blocking: true
- id: IMP-005
  requirement: Implement read/status/tracking normalization only when supported by the provider contract.
  blocking: true
- id: IMP-006
  requirement: Return normalized unsupported-capability errors for unavailable operations.
  blocking: true
- id: IMP-007
  requirement: Add adapter contract fixtures proving Logistics core is unchanged if this provider is disabled.
  blocking: true
- id: IMP-B01
  requirement: Preserve all prompt authority, ownership, forbidden-output, no-live-write and no-cross-repository
    boundaries.
  blocking: true
verification_obligations:
- id: VER-001
  verification: Provider can be disabled in registry without core code changes.
  blocking: true
- id: VER-002
  verification: Unsupported operations fail closed.
  blocking: true
- id: VER-003
  verification: No production booking or provider mutation is performed.
  blocking: true
- id: VER-004
  verification: No real secrets are committed.
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
  evidence: provider capability record
  blocking: true
- id: CE-002
  evidence: adapter mapping inventory
  blocking: true
- id: CE-003
  evidence: disabled-provider test
  blocking: true
- id: CE-004
  evidence: no-live-write/secret confirmation
  blocking: true
- id: CE-005
  evidence: completion report/packet
  blocking: true
- id: CE-B01
  evidence: boundary confirmation evidence bound into the completion packet
  blocking: true
forbidden:
- production courier booking
- real credentials
- assumption of feature parity with other taxi/courier providers
- Blueprint repository writes
completion_protocol:
  produce_module_side_completion_report: true
  produce_module_side_completion_packet: true
  report_exact_commit_and_test_results: true
  do_not_claim_blueprint_acceptance: true
  do_not_release_next_prompt: true
acceptance_handoff:
  oracle_required: true
  prompt_contract_path: coordination/prompt_contracts/logistics_service/logistics_service_uklon_delivery_read_only_foundation_v0_1/logistics_service_uklon_delivery_read_only_foundation_v0_1__contract_v0_4_h7_v0_1.yaml
  acceptance_oracle_path: coordination/acceptance_oracles/logistics_service/logistics_service_uklon_delivery_read_only_foundation_v0_1__acceptance_oracle_v0_1.yaml
  criteria:
  - criterion_id: AC-001
    step_id: logistics_service_uklon_delivery_read_only_foundation_v0_1
    substep_id: logistics_service_uklon_delivery_read_only_foundation_v0_1__01
    requirement_refs:
    - IMP-001
    - VER-001
    summary: 'Verify blocking substep: Map provider runtime profile and environment boundary'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_uklon_delivery_read_only_foundation_v0_1__01
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-002
    step_id: logistics_service_uklon_delivery_read_only_foundation_v0_1
    substep_id: logistics_service_uklon_delivery_read_only_foundation_v0_1__02
    requirement_refs:
    - IMP-002
    - VER-002
    summary: 'Verify blocking substep: Map supported service/product capabilities into generic on-demand
      contract'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_uklon_delivery_read_only_foundation_v0_1__02
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-003
    step_id: logistics_service_uklon_delivery_read_only_foundation_v0_1
    substep_id: logistics_service_uklon_delivery_read_only_foundation_v0_1__03
    requirement_refs:
    - IMP-003
    - VER-003
    summary: 'Verify blocking substep: Implement dry-run quote/payload preview surface where supported'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_uklon_delivery_read_only_foundation_v0_1__03
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-004
    step_id: logistics_service_uklon_delivery_read_only_foundation_v0_1
    substep_id: logistics_service_uklon_delivery_read_only_foundation_v0_1__04
    requirement_refs:
    - IMP-004
    - VER-004
    summary: 'Verify blocking substep: Map provider status/tracking data into normalized events where
      supported'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_uklon_delivery_read_only_foundation_v0_1__04
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-005
    step_id: logistics_service_uklon_delivery_read_only_foundation_v0_1
    substep_id: logistics_service_uklon_delivery_read_only_foundation_v0_1__05
    requirement_refs:
    - IMP-005
    - VER-005
    summary: 'Verify blocking substep: Prove unsupported capabilities fail closed without provider-specific
      core branches'
    blocking: true
    verification:
      kind: semantic_review
      locator: completion packet requirement_results + evidence_manifest for logistics_service_uklon_delivery_read_only_foundation_v0_1__05
      expected_observation: The substep is implemented as specified, cited contract obligations are satisfied,
        and completion evidence is concrete and internally consistent.
    evidence_required:
    - EV-COMPLETION-REPORT
    - EV-FOCUSED-TESTS
  - criterion_id: AC-900
    step_id: logistics_service_uklon_delivery_read_only_foundation_v0_1
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
    step_id: logistics_service_uklon_delivery_read_only_foundation_v0_1
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
    step_id: logistics_service_uklon_delivery_read_only_foundation_v0_1
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
