# Portfolio Roadmap Rebuild Program v0.1

## Objective

Rebuild every non-Blueprint module roadmap into a common, traceable structure before broad systematic
automated execution.

## Important authority distinction

The current Blueprint Q-series roadmap remains current.

Other module roadmaps are preserved as historical/current-state evidence but are not assumed complete
enough for the new portfolio operating model.

## Rebuild sequence per module

1. collect existing policy/prompts/roadmaps/code evidence;
2. confirm module identity and aliases;
3. build/repair Module Charter;
4. build Capability Catalog;
5. define target scope and finish condition;
6. map current implementation to capability/roadmap outcomes;
7. construct full provisional roadmap;
8. perform end-to-end completeness/gray-zone review;
9. identify dependencies and dependency timing;
10. assign provisional work weights;
11. assign portfolio value/blocking class;
12. create baseline progress estimate + confidence;
13. semantic review with owner where required;
14. publish canonical rebuilt roadmap;
15. mark superseded roadmap authority explicitly.

## Discussion depth

Not all modules require equal owner conversation before portfolio work starts.

Classify:

- `OWNER_REVIEW_BLOCKING`
- `SYNTHETIC_FIRST_REVIEW_LATER`
- `NON_BLOCKING_SUPPORT`

Strong/central modules should receive deeper semantic review first.

Peripheral modules may start with a synthetic roadmap so their existence and likely dependencies are
visible, then be refined before execution.

## Known concept-review priorities from current audit/conversation

High-value historical conversation recovery if available:

1. `forprint_prepress_hub`
2. `forprint_crm`
3. `forprint_accounting_registry_service`

`forprint_library` already has comparatively rich project evidence and can initially be rebuilt from
existing Blueprint material, then enriched later.

## Completion

The program is complete when:

- all known modules have a canonical charter/capability/roadmap/dependency position;
- no module is activated from a vague or orphan roadmap;
- dependency graph supports portfolio prioritization;
- baseline progress can be rendered;
- dashboard can project current state from durable data.

<!-- synthetic-roadmap-refinement-v0-1:start -->
## Synthetic target-state refinement rule — 2026-08-26

Every known logical module must have an honest Target State and a full synthetic roadmap toward it.

When evidence is insufficient, use explicit states:
`UNKNOWN`, `UNCONFIRMED`, `PROVISIONAL`, `TBD`, `OPEN_QUESTION`.

Do not create false precision.

Refinement loop:

`Target State -> synthetic full roadmap -> owner/theory review -> revised roadmap -> cross-module dependency analysis -> execution-ready detail for priority modules`

Core modules receive deeper refinement first. Peripheral modules may remain synthetic until their
dependencies/execution timing justify deeper design.

If an immature module blocks a critical module, define the minimum dependency-ready slice that
unblocks the critical path rather than fully completing the blocker.

Unplanned evening theory discussion is preserved as Design/Theory Decision evidence and later merged
into canonical docs; it is not a second competing roadmap.
<!-- synthetic-roadmap-refinement-v0-1:end -->

<!-- theory-review-r2-deep-review-method:start -->
## Deep review method and target-milestone model — 2026-08-27

Portfolio roadmap review is iterative rather than one giant one-pass design.

- First pass: role, business value, target direction and obvious dependencies.
- Second pass: expand unresolved major steps into whatever micro-step depth is necessary.
- Later passes: reconcile contracts, dependencies, Knowledge Inventory and implementation evidence.
- Once a step is explicitly understood/accepted, keep its detailed historical decomposition but
  collapse it in ordinary review views.
- Keep unresolved, changed, blocked and ambiguous steps expanded.
- Mature/old modules may require inventory-first reconstruction before a final execution roadmap.
- Every pass must expose gray zones rather than convert uncertainty into false precision.

Roadmaps distinguish `TARGET_MILESTONE` from `STEADY_STATE_EVOLUTION`. ForPrint is expected to move
from heavy build-out to recurring optimization/evolution, not to a permanent “finished forever”
state.

The module inventory used for portfolio automation must be explicitly reconciled. Historical review
views may omit module identities; omission is never retirement authority.
<!-- theory-review-r2-deep-review-method:end -->

<!-- portfolio-ui-design-system-adoption-v0-1:start -->

## Cross-module UI design-system adoption dependency

Modules that introduce new UI capability should use the ForPrint Design System capability rather
than inventing a new local visual baseline.

Portfolio rebuild must distinguish:
- new UI implementation;
- existing UI already in production/use;
- legacy UI needing gradual migration;
- explicit exceptions.

The Library roadmap receives a Design System slice covering inventory, tokens, shared components,
themes, reference implementation, controlled adoption and drift management.

<!-- portfolio-ui-design-system-adoption-v0-1:end -->

<!-- website-design-system-migration-guard-v0-2:start -->

## Website migration guard — explicit owner rule — 2026-08-27

The current Website is an existing, already-formed UI product and is a special migration case.

The shared ForPrint Design System **does not authorize an immediate Website redesign**.

Required Website transition sequence:

1. Keep the current Website visual design as the active production baseline.
2. Do not automatically replace existing Website styling/components merely because the shared
   Design System becomes available.
3. A new Website visual variant/theme may enter development only after explicit operator approval
   and a separate Website work package/prompt.
4. Develop the new Website visual variant in parallel with the existing design rather than
   destructively rewriting the active production presentation.
5. Validate the new variant on the Website's local development/test server first.
6. Do not publish the new design to hosting as a side effect of local development, design-system
   publication, Library updates or portfolio adoption.
7. Hosting deployment requires a separate explicit operator decision after local testing/review.
8. During transition, the current and new Website visual variants may coexist where the Website
   architecture permits, so rollback/comparison remains possible.
9. Migration may proceed gradually by components/pages/surfaces rather than as one all-at-once
   visual rewrite.
10. Only after the operator accepts the tested target presentation should the new design become
    the Website production default.

General portfolio rule:

- **newly created UI-bearing tools/modules** should use the canonical Design System from the start
  unless a reviewed exception exists;
- **already existing UI-bearing tools/modules** keep their current working presentation until
  their own explicit migration plan is approved;
- no assistant may infer "shared Design System exists" => "rewrite every existing interface now".

Cloud Backup Manager remains a reusable reference/seed for shared components and layout patterns,
not a command to make Website visually identical to Cloud Backup Manager.

<!-- website-design-system-migration-guard-v0-2:end -->

<!-- iterative-portfolio-roadmap-review-v0-1:start -->
## Iterative portfolio roadmap review method — owner direction 2026-08-28

Pass 1 records role, business value, target state, ownership/non-ownership, dependencies, representative scenarios, gray zones and candidate microsteps.

Pass 2 expands large steps into implementable microsteps with concrete artifacts, contracts, dependency gates, acceptance evidence, rollback/compatibility and explicit human/automation boundaries.

Repeat further passes as needed; a module may need 10, 20, 50+ microsteps. The goal is substantial autonomous work packages while tightly-coupled modules remain synchronized.

Do not invent work merely to justify an existing module. Modules with unclear independent value may remain deferred until the full capability/dependency map is visible.
<!-- iterative-portfolio-roadmap-review-v0-1:end -->
