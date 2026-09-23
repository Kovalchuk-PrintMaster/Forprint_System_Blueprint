# Governed change and acceptance policy direction v0.1

Status: active long-lived policy direction.

## Core principle

The system must distinguish implementation/functionality changes from managed content/data changes and must explain both *what changed* and, for established operations, *through which authorized adapter/tool/capability it changed*.

For eligible established content/data surfaces, acceptance should reconcile:

declared authorized mutation evidence ↔ observed resulting diff.

If two catalog items appear in the observed diff but the registered adapter/tool ledger records only one item addition, the unexplained second mutation is a provenance gap and acceptance must stop for investigation.

## Development

During active development workers may require broad writes because modules are still being built. Broad does not mean invisible: attempts, changed paths, tools and procedures, retries and evidence are attributable. Adapter/tool provenance checks apply where the functionality is already established, while implementation edits remain separately classified.

The early goal is learning and visibility, not aggressive locking.

## Stabilization

As modules mature, more established surfaces move behind registered capabilities; direct writes become discouraged and then technically protected. Retry budgets tighten from statistics. Provenance reconciliation becomes a required acceptance signal for eligible surfaces.

## Production

Workers do not freely edit established production functionality. Optimizations/defects become structured change proposals for Dispatcher/operator review. An approved package may receive temporary scoped authority, bounded by time and/or attempts and automatically expiring.

Production data/content operations continue through approved capabilities/tools with mutation provenance.

## Acceptance

The target is high-confidence automatic acceptance of routine steps inside a wave once result contracts, validators and provenance are strong enough.

Wave/phase boundaries remain human-controlled. A completed wave never automatically authorizes the next wave.

## Reporting target

Reporting should evolve toward: attempt/worker/profile/procedure identity; declared tools; adapter/tool mutation records; observed changed paths and semantic/data diff; declared-vs-observed reconciliation; validators/tests; retries/repairs; unresolved provenance gaps; acceptance state; human phase-boundary attention.

Machine-readable companion: `coordination/global_policy/governed_change_and_acceptance_policy_direction_v0_1.yaml`.
