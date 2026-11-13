# ForPrint Portfolio Module Inventory Program v0.1

Status: ACTIVE_PLANNING_CONTEXT / BLUEPRINT_INTERNAL
Date: 2026-09-04
Authority: Blueprint planning and governance only
Implementation authority: none
Assistant distribution: closed

## Purpose

The next portfolio phase is inventory-first. Before normal autonomous assistants receive real implementation work, Blueprint will build a trustworthy evidence baseline for module repositories, reconcile legacy and contradictory material, enrich roadmaps, and prepare each repository for fresh-context autonomous operation.

## Canonical sequence

1. Blueprint continuity and governance check.
2. Portfolio triage.
3. Logical repository partition.
4. Archive-batch analysis.
5. Module consolidation.
6. Blueprint portfolio enrichment.
7. Module roadmap enrichment.
8. Module-local index and AGENTS.md bootstrap.
9. Coordination/reporting v0.4.1 and local inventory-tooling readiness.
10. Readiness verification.
11. Bounded implementation only after explicit human approval.

## Archive workflow

Large repositories are analyzed through bounded logical ZIP batches instead of repeatedly traversing every file in chat. Each batch produces one durable report. Reports are consolidated only after the required batches are complete. Re-open source archives only when conflicts or evidence gaps require it.

## Evidence discipline

Repository presence is evidence, not automatic canonical truth. Use:
`VERIFIED_LOCAL_REPOSITORY`, `VERIFIED_RUNTIME`, `BLUEPRINT_CANONICAL_DOCUMENTATION`,
`HUMAN_CONFIRMED`, `PROPOSED`, `UNKNOWN`, `HISTORICAL_ONLY`, `DEPRECATED`,
and `CONFLICTING_EVIDENCE`.

## Legacy and contradiction discipline

Calculator and Telegram Bot are high-risk legacy repositories. Multiple implementation generations must be mapped by entrypoints, imports, tests, configuration, runtime evidence, and current ownership. Modification time alone is not authority.

No automatic deletion is allowed. Prefer classification, isolation, deprecation, historical marking, ownership review, and lifecycle-governed retirement.

Contradictory active documentation is a readiness blocker because an autonomous assistant must not choose arbitrarily between incompatible instructions.

## Existing canonical standards reused

u108 is integrated as a program overlay and working package. It does not replace or duplicate current standards:

- `coordination/standards/knowledge/parallel_initial_inventory_map_reduce_reconcile_playbook_v0_1.md`
- `coordination/standards/governance/module_current_state_evidence_standard_v0_1.yaml`
- `coordination/standards/governance/safe_mutation_pipeline_v0_1.yaml`
- `coordination/standards/governance/asset_lifecycle_retirement_policy_v0_1.yaml`
- `coordination/standards/module_prompt_completion_protocol.md`
- `coordination/standards/module_outgoing_prompt_pull_protocol.md`
- `coordination/standards/module_assistant_start_protocol.md`
- `coordination/standards/module_make_target_contract.md`
- `coordination/standards/module_governance_protocol.md`

The staged u108 source package remains at:
`coordination/internal_work/blueprint/module_inventory_program/2026-09-03__u108/`

## Module readiness direction

Before bounded autonomous work, a module should have:
- consolidated inventory/evidence;
- clear active vs historical implementation lineage;
- explicit owned and forbidden semantics;
- current roadmap;
- canonical documentation read path;
- module-local repository index;
- effective AGENTS.md;
- current v0.4.1 prompt/report coordination support;
- deterministic local inventory/index maintenance tooling;
- known validation commands and stop/escalation conditions.

## Fresh-context continuity

Root `AGENTS.md` is the primary navigation entry for a fresh Blueprint assistant. It must point to this program, current release, identity registry, Human Intent, roadmap/evidence surfaces, and the exact next action.

## Historical integration gates captured on 2026-09-04

- assistant distribution allowed: false
- module implementation started: false
- prompt activation: false
- automatic acceptance: false
- automatic release next prompt: false
- H10 widened: false
- cross-repository diagnostics: not broadly started
- commit/push: not performed by this integration

## Historical next action captured on 2026-09-04

Build the module inventory triage/partition plan, select the first legacy pilot between Calculator and Telegram Bot based on repository size/risk, then prepare the first bounded archive manifest. Do not issue real implementation prompts yet.

<!-- module-inventory-program-vnext-extension-20260906:start -->
## Current extension direction — 2026-09-06

The original dated program remains the evidence baseline for inventory-first rollout, but
the current H10 continuation has advanced beyond the original first triage action.

The evidence-backed vNext assessment is:

`coordination/internal_work/blueprint/module_inventory/2026-09-06__module_inventory_program_vnext_gap_assessment_v0_1.yaml`

The shared Inventory Program is now explicitly interpreted as long-lived **Module Memory**,
not merely repository file enumeration. Its mature target includes purpose/provenance,
lifecycle, implementation lineage, interfaces, dependencies/consumers, evidence, duplicate
and coexistence review, roadmap linkage, retirement impact and freshness.

Do not replace the existing RCI, current-state evidence, cleanliness pack, repository
knowledge freshness or lineage primitives. Extend and reconcile them into one reusable
module-memory contract.

The Logistics H10 reference prompt remains allowed to establish the first significant
self-knowledge/lineage baseline without waiting for full portfolio-wide vNext tooling.
<!-- module-inventory-program-vnext-extension-20260906:end -->

## P6/P7 roadmap reconciliation boundary — 2026-09-08

Roadmap reconciliation is a mandatory P6/P7 boundary.

After module consolidation / Blueprint enrichment and before the module-local bootstrap
substrate is treated as semantically complete:

1. compare implementation evidence with inventory, lineage and document authority;
2. compare that evidence-backed view with the canonical module roadmap;
3. identify already-implemented roadmap work, missing roadmap capabilities, stale directions
   and Blueprint-derived responsibility gaps;
4. create an evidence-bound reconciliation report;
5. apply canonical roadmap changes only after semantic review;
6. then proceed with bootstrap/self-maintenance/readiness work.

Reusable read-only analyzer:

`scripts/coordination/build_module_roadmap_reconciliation.py`

For Logistics the first report is:

`coordination/internal_work/blueprint/module_inventory/logistics_service/2026-09-08__logistics_service__roadmap_reconciliation_report_v0_1.yaml`
