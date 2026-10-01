# CF10 Worker self-hardening intake reconciliation v0.1

Status: **PLANNING_RECONCILED_NON_EXECUTING**

This record reconciles the 2026-10-01 self-hardening intake against the live CF10
architecture. It deliberately does **not** mutate the training queue, roadmap,
execution authority, Worker state, promotion state or publication state.

## Live baseline

- branch: `audit/blueprint-inventory-refresh-2026-07-29`
- HEAD: `82939818a1ed9e1942878b179141081a0718cc64`
- upstream: `82939818a1ed9e1942878b179141081a0718cc64`
- HEAD == upstream: `true`

## Phase B reserved semantics

- Task110: candidate promotion and separate acceptance
- Task120: **UNRESOLVED — DO NOT INVENT**
- Task130: resolved execution context / readiness capsule
- Task140: progression gates, readiness, validation debt and manual checkpoint
- Task150: final CF10 stability / exit proof

The new intake does not claim any of those numbers.

## Observed canonical GWC CLI

Present:

`status`, `prepare`, `ack`, `authorize-dispatch`

Desired complete operator lifecycle commands such as launch/validate/review/promote/finalize/resume
are not currently exposed by the canonical GWC `--help` surface.

## Reconciliation matrix

| Intake item | Disposition | Existing owner / parent | Planning action |
|---|---|---|---|
| `candidate_review_surface_and_pre_promotion_review_policy` | EXTEND | Phase B Task110 candidate promotion / separate acceptance, worker_candidate_promotion contract, Task85 review/freshness semantics | Extend Task110 semantics with explicit isolated candidate review modes and REWORK-before-promotion behavior; do not create a second acceptance authority. |
| `canonical_worker_cycle_operator_dispatcher_entrypoint` | EXTEND_WITH_BOUNDED_SELF_HARDENING_TASK | scripts/coordination/control_plane/governed_worker_cycle.py, Makefile 08A/08B, existing runtime/launcher/workspace components | Build a stable operator/Dispatcher entrypoint over existing GWC primitives. Current CLI stops at status/prepare/ack/authorize-dispatch. |
| `runtime_preflight_and_source_freeze_hardening` | EXTEND | v0.4.1 execution-workspace policy, Phase B Task130 readiness capsule, GWC workspace/provision/runtime | Add deterministic environment/quota/source-freeze/dirty-overlap preflight using live state at attempt start; preserve existing durable-dirty semantics. |
| `structured_worker_result_and_error_contract` | ADAPT_EXTEND | Handoff v2 result/freshness-resume, attempt ledger, GWC result handling | Define Dispatcher-stable error taxonomy, retryability, operator-required and prescribed-action fields without creating a second result authority. |
| `execution_event_logging_and_operational_metrics` | EXTEND | control_plane/events.py, execution attempt ledger, Task40 watchdog observability, dispatcher telemetry | Record derived execution events/metrics while preserving Ledger/canonical facts as authority. |
| `cf10_cli_contract_normalization` | EXTEND | Makefile operator functional map, GWC CLI, control-plane command surfaces | Normalize supported --help/argument/output contracts as part of canonical entrypoint hardening, not as a parallel CLI framework. |
| `dispatcher_gate_and_notification_policy` | EXTEND | CF10 transition_policy, Phase B Task140 progression gates, Task50 Telegram operator surface, Task60 human dashboard | Allow automatic micro-transitions only under explicit contracts; keep next meaningful Work Front human-gated by default and notify at meaningful boundaries. |
| `exchange_protocol_04_041_reconciliation` | RECONCILE | v0.4 closed-loop stack, v0.4.1 prompt/report bootstrap requirements | Audit producer/consumer/wrapper/payload revision roles before any rename; establish one coherent exchange/reporting chain for modules. |
| `canonical_module_bootstrap_package` | EXTEND_CONSOLIDATE | adopted module bootstrap execution policy, v0.4.1 bootstrap requirements, Task85 bootstrap freshness gate | Consolidate existing bootstrap fragments into a canonical package covering roadmap, prompt/report, continuity, manual and Dispatcher-ready operation. |
| `module_bootstrap_conformance_and_reference_implementation` | ABSORB_OR_EXTEND | module inventory/bootstrap program, Task85 new-module bootstrap safety demonstration | Prefer acceptance/demo slice of canonical bootstrap work unless current-state refresh proves an independent Work Front is needed. |
| `ad_hoc_orchestration_defect_conversion_policy` | GOVERNANCE_EXTENSION | CF10 discovered-gap register, worker-first gap policy, future canonical entrypoint acceptance | Treat normal-cycle ad-hoc helper recovery as control-plane defect evidence; migrate reusable fix into canonical implementation + regression coverage. |
| `governed_cross_repo_prompt_publication_and_activation_runner` | NEW_BOUNDED_TASK_REUSING_EXISTING_PRIMITIVES | existing CF10 control plane, prompt lifecycle contracts, canonical Worker entrypoint/error/resume primitives | Phase 1 implements plan/preflight/state-machine/resume/dry-run without cross-repo write authority. Phase 2 real GDL/Prepress regression requires a separate bounded cross-repo authority decision. |

## Recommended execution clustering

A. Foundation: structured errors/results → preflight/source freeze → canonical entrypoint → CLI normalization.

B. Review/operator: pre-promotion review surface → Dispatcher gate/notifications → derived event metrics.

C. Coordination/bootstrap: 0.4/0.4.1 reconciliation → canonical bootstrap consolidation → conformance proof.

D. Real workflow automation: governed cross-repo prompt publication/activation runner, reusing A/B/C primitives.

E. Exit: extend existing Task150 proof after current-state refresh; do not create a second final-control authority.

## Global rule

Every future architecture task must be refreshed against the current project state immediately
before materialization. Planning intent is durable; stale implementation assumptions are not.

Task120 remains unresolved. This record does not invent its semantics.
