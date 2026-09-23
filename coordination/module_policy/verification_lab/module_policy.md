# Module Policy — ForPrint Verification Lab

## Module ID

```text
verification_lab
```

## Priority

```text
p0
```

## Development status

```text
planned_bootstrap_pending_distribution_closed
```

## Strategic role

Independent isolated verification/adversarial/fault/concurrency test service and deterministic regression evidence owner; not project conformance or runtime truth.

## Main goals

- `Build Test Plane and synthetic side-effect adapters before implementation.`
- `Challenge normal, invalid, boundary, adversarial, concurrency and recovery behavior.`
- `Convert useful exploratory findings into deterministic regression corpus.`
- `Provide reproducible verification evidence for release/staging/canary decisions.`
- `Remain separated from Project Inspector and Production Runtime Inspector.`

## Owns

- `verification_campaign_definition`
- `synthetic_test_case_corpus`
- `test_plane_scenario`
- `adversarial_test_execution`
- `deterministic_regression_corpus`
- `verification_finding_evidence`
- `release_candidate_verification_result`
- `fault_injection_profile`

## Must not own

- `architecture_policy`
- `business_domain_truth`
- `production_runtime_control`
- `deployment_approval`
- `live_external_side_effects`
- `unrestricted_shell_authority`
- `secrets`
- `foreign_module_semantic_rewrite`

## Next focus

- `Keep implementation NOT STARTED and assistant distribution CLOSED.`
- `Complete portfolio dependencies, Test Plane contract and Execution Policy Gate design.`
- `Define deterministic regression/evidence interfaces with Contract Registry and Project Inspector.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
