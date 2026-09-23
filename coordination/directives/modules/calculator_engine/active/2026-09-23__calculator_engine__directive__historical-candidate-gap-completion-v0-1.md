# Calculator Engine Directive: Historical Candidate Gap Completion v0.1

## Status

Active module directive.

## Purpose

Resume Calculator work only for the bounded implementation gaps confirmed by the
2026-09-23 current-state reconciliation.

This directive narrows and supersedes the earlier temporary pause only for the
approved prompt below. It does not authorize unrelated Calculator development.

## Approved prompt

- prompt id: `calculator_engine_historical_candidate_gap_completion_v0_1`
- Blueprint path: `coordination/outgoing_prompts/calculator_engine/approved/2026-09-23__calculator_engine__historical_candidate_gap_completion_v0_1.md`
- execution state: `ready_for_module_pull`
- reconciled Calculator HEAD: `457d1a70cf9fe39351201c6452104b3d6b87a6b5`

## Required operator flow

1. Run `make blueprint-pull`.
2. Run `make blueprint-check`.
3. Run `make blueprint-sync-directives`.
4. Inspect the local prompt intake:
   - `coordination/prompts/received/`
   - `coordination/prompts/active/`
   - `coordination/prompts/archived/`
   - `coordination/prompts/index.yaml`
5. Synchronize the approved prompt into the local prompt intake using the
   module's established prompt-state workflow.
6. Verify exactly one active prompt.
7. Only then begin implementation.

If the prompt cannot be synchronized, stop and report the intake gap. The
directive itself is not a substitute for formal prompt intake.

## Scope guard

Implementation scope is exactly:

- pricing/admin runtime gap: `filtered_bulk_policy_update`;
- quote runtime gap: `provenance_reference_versions`;
- seven focused test gaps listed in the approved prompt.

Preserve current architecture and ownership boundaries.

## Prohibited expansion

No:

- canonical catalog ownership in Calculator;
- CRM/customer identity ownership;
- Gateway transport/routing ownership;
- direct Telegram/Website runtime coupling;
- broad architecture redesign;
- unrelated refactor;
- Blueprint lifecycle/release mutation from the module.

## Completion

Return the module completion report to Blueprint for separate review and
acceptance.
