# GDL empirical-learning horizon — Blueprint reconciliation v0.1

Status: **BLUEPRINT_RECONCILED_WITH_ONE_NEXT_PROMPT_PREPARED**

## Decision

The Prepress-owned package is accepted as a governed GDL horizon with reconciliation.

The already accepted Guided Intake / Creator Handoff foundation remains the reusable base.
The next executable contour is:

`prepress_gdl_creator_empirical_learning_foundation_v0_1`

Only this first contour is prepared for publication. Contours 2–10 remain planning-only.

## Why this is next

The package intentionally shifts the immediate priority from accumulating more automation
toward learning from real customer requests, Creator prompts, Creator outputs, revision
cycles, operator assessment and customer acceptance.

The empirical layer is therefore inserted before broader Creator-result/evaluation/prompt
automation.

## Existing verified base

The live Prepress reconciliation observed:

- `GDL-N07`: `PARTIAL_IMPLEMENTED_VERIFIED`
- `GDL-F07`: `PARTIAL_IMPLEMENTED_VERIFIED`
- `GDL-F06`: `PARTIAL_IMPLEMENTED_VERIFIED`
- `creator_result_package`: `PLANNED_NEAR_TERM`
- GDL runtime initialized: `false`
- production write enabled: `false`
- previous prompt accepted/completed: `true`
- active Prepress prompt before publication: `null`
- empirical-learning planning/evidence baseline: `PRESENT` at Prepress commit `2039f48`
- empirical-learning planning/evidence file count observed: `34`
- GDL authority remains: `PLANNED_NOT_INITIALIZED`

The existing `planning_evidence/empirical_learning/` surface already contains an
empirical case template, experiment lifecycle, menu/business-card/flyer loaders,
failure-mode starter, methodology/index surfaces and the real
`GDL-EXP-20261001-MENU-001` experiment.

This is planning/evidence, not GDL runtime authority. The first executable contour
must therefore REUSE/EXTEND that committed surface rather than create a parallel
empirical-learning system.

The first contour must also reuse, not rebuild, Product Playbook, Guided Intake,
Creator Handoff and asset-reference provenance.

## First contour

The first contour may reconcile/commission the existing empirical-learning
planning surface and add only missing governed mechanics. It must not duplicate the
already committed case template, experiment lifecycle, loaders or menu experiment.

The first contour may add/reconcile:

- Creator interaction empirical case semantics only where the existing planning surface has a real gap;
- prompt/result/outcome metadata;
- separate operator/customer/satisfaction outcomes;
- first-attempt / accepted-attempt / revision-count observations;
- strengths, weaknesses, failure modes and lessons;
- candidate-local-automation observations;
- external artifact references without heavy Git storage;
- no customer PII in Git;
- manual operator intake experiment protocol;
- sanitized menu, business-card and flyer examples;
- deterministic validation/indexing;
- human-readable case summary;
- Makefile operator workflow;
- focused tests and module-owned completion evidence.

The menu/business-card/flyer examples are empirical fixtures, not authorization for a full
product wizard or production runtime.

## Future queue

All ten source contours are preserved.

Sequence 2 remains:

`prepress_gdl_creator_result_package_foundation_v0_1`

but is **not executable now**.

Every later contour requires fresh inspection of current Prepress state, empirical findings,
current Human Intent, completed contours and pending amendments. The source queue's sequence
is a default ordering, not an unconditional command.

## Authority boundary

- Blueprint owns horizon registration, dependency ordering, reconciliation and outgoing prompt publication.
- Prepress owns module implementation and local completion evidence.
- `SYSTEM_BLUEPRINT_ACCESS_FROM_PREPRESS=READ_ONLY_STRICT`
- no provider selection/execution;
- no GDL runtime initialization;
- no production write;
- no automatic customer messaging/order creation/design approval;
- no automatic next-contour activation.

## Source package

`coordination/internal_work/blueprint/roadmap_enrichment/prepress_gdl/2026-10-01__gdl_empirical_learning_horizon_v0_1/source_package`

## Prepared prompt

`coordination/outgoing_prompts/forprint_prepress_hub/approved/2026-10-01__forprint_prepress_hub__gdl_creator_empirical_learning_foundation_v0_1.md`
