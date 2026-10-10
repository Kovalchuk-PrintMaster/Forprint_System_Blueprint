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

<!-- forprint-project-wide-closed-loop-policy-v0-1:start -->
## Project-wide closed-loop execution policy direction

ForPrint should progressively convert stable repeatable engineering and
operational work into repository-owned, tested, resumable and machine-readable
closed loops. This is a project-wide direction for all current and future
modules.

A mature module execution loop should:

1. resolve live current state and the governing roadmap position;

2. select only currently admissible work;

3. inventory the nearest existing capability and apply
   `REUSE → EXTEND → ADAPT → REPLACE → NEW`;

4. prepare through project-owned tooling;

5. stop at any explicit authority/ACK boundary not already granted;

6. execute through a repository-owned CLI, Make target or stable service
   entrypoint;

7. require a strict machine-readable result/Handoff rather than infer success
   from process exit alone;

8. validate the affected surface and reconcile declared versus observed
   mutation/provenance;

9. persist durable append-only or otherwise governed terminal evidence;

10. derive and report the next admissible action;

11. continue automatically only when that transition is already within granted
    authority;

12. stop or escalate on failure, ambiguity, unresolved provenance,
    architectural choice or a governance boundary.

A passing test suite is evidence, not lifecycle closure by itself. A successful
engineering cycle should also make its terminal state, evidence, unresolved
blockers and next admissible action machine-readable.

Automation reduces repetitive operator work; it does not silently widen
authority. Acceptance, roadmap advancement, promotion, cross-repository
mutation, commit/push/merge, release and other protected transitions remain
governed boundaries according to their owning contracts.

Specific implementations may be modernized, adapted, replaced or retired when
evidence supports it. Canonicality belongs primarily to ownership, authority,
contracts, provenance and safety invariants, not to preserving an old function
or script merely because it already exists.

CF-10 is currently a proving ground for reusable governed execution primitives.
That fact is a live roadmap implementation detail, not the normative scope of
this policy.

The later cross-module Dispatcher horizon may coordinate queues, dependencies,
priorities, workers and resources only after reliable individual module loops
exist. This policy creates no Dispatcher authority.
<!-- forprint-project-wide-closed-loop-policy-v0-1:end -->
