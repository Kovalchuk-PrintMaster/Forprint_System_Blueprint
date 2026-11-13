# Blueprint repository structure and architecture hygiene consolidation

Status: `PLANNED_NON_BLOCKING`.

This bounded cleanup is intentionally not a blocker for the current Logistics reference pilot.

## Structural rule now

New Control Plane runtime internals belong under `scripts/coordination/control_plane/`;
validation under `scripts/validation/control_plane/`; tests under
`tests/coordination/control_plane/`; durable runtime standards under
`coordination/standards/automation/control_plane/`.

Existing stable flat entrypoints are not mass-moved while the activation path is still being
proven. They remain compatibility facades.

## Scheduled gate

Run the complete tracked-tree review after completion/Inspector integration and before broad
multi-module AI-worker rollout. The review must classify project anchors, public facades,
internal packages, generated/curated/runtime/evidence areas, stale transitional surfaces,
duplicate frameworks, test/validator placement and root-level ownership. Any move must
preserve lineage and compatibility shims rather than use bulk rename.
