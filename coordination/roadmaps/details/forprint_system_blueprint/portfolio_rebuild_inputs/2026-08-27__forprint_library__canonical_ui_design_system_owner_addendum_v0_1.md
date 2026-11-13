# ForPrint Library — Canonical UI Design System Owner Addendum v0.1

Date: 2026-08-27

Status: OWNER-REVIEWED TARGET DIRECTION / PORTFOLIO REBUILD INPUT / NOT RUNTIME AUTHORITY

## Decision direction

ForPrint needs one reusable cross-module visual/design-system foundation so independently
developed web/admin/mobile-web interfaces do not diverge in buttons, warnings, cards, forms,
spacing, typography, colors, interaction states, responsive behavior or accessibility.

A separate permanent "UI assistant/module" is not required solely to own this truth.

Recommended ownership boundary:

- **Blueprint** owns the cross-module policy, adoption contract, authority boundaries and rollout rules.
- **ForPrint Library** owns the canonical design-system knowledge/artifacts: design tokens, semantic
  roles, themes, component catalog, component contracts, design-system version metadata and
  platform export definitions.
- **Consumer modules** consume the shared design system and may add domain-specific composition,
  but must not silently redefine shared primitives.
- **Inspector** detects drift, direct hard-coded values where prohibited, stale design-system
  versions, component divergence, accessibility/visual regression findings and missing adoption
  evidence. Inspector is not the semantic or visual design owner.

## Technical model

Use a layered token/component architecture:

1. reference/primitive tokens;
2. semantic/system tokens;
3. component tokens/contracts;
4. themes that override tokens rather than component logic;
5. application composition on top of shared primitives.

The target is "one source of truth, controlled rollout", not an unversioned global live CSS blast
radius. Library should publish versioned artifacts/packages; consumer modules should declare which
version they use; upgrades should be testable and rollbackable.

## Theme direction

The system must support an open-ended number of visual themes/variants. An initial demonstration
set may include light, dark, soft-light, soft-dark and seasonal/holiday variants, but exact count
and naming are not final requirements.

Operational semantics (warning/error/success/info/focus/disabled) must remain recognizable and
accessible across all themes.

## Existing ForPrint reference inputs

### Website

The existing Website already has its own established production visual language. That existing
visual language remains the active Website baseline until a separate operator-approved migration
decision is made.

Website's existing frontend visual-system documentation remains important source material to
inventory and reconcile, but the shared Design System does NOT authorize an automatic visual
rewrite of the current Website.

### Cloud Backup Manager

Cloud Backup Manager is an implementation reference candidate. Its UI structure/components may be
reused selectively after inventory.

Known project location from existing evidence:
`/opt/forprint-utils/cloud_backup_manager`

Its current blue-oriented styling is a reference implementation detail, not the future mandatory
ForPrint brand/theme.

## Library roadmap slice

### UI-DS-R0 — inventory and authority reconciliation
- inventory Website visual-system documentation and current implementation;
- inventory Cloud Backup Manager UI foundation;
- inventory other ForPrint UI styles/components;
- classify reusable / legacy / conflicting / missing;
- confirm Blueprint/Library/Inspector/consumer boundaries.

### UI-DS-R1 — token foundation
- primitive/reference tokens;
- semantic/system tokens;
- naming/alias rules;
- theme schema;
- accessibility/contrast;
- generated platform outputs.

### UI-DS-R2 — shared component catalog
- buttons, forms, cards, alerts/warnings, dialogs, navigation, tables, badges, loaders and other
  shared primitives;
- states/variants/responsive behavior;
- domain-extension rules.

### UI-DS-R3 — reference implementation and documentation
- component showcase/workbench;
- component states and usage rules;
- accessibility and visual-regression baselines;
- initial theme variants.

### UI-DS-R4 — controlled adoption
- NEW UI-bearing modules/tools should adopt the shared system from their initial implementation
  unless a reviewed exception exists;
- EXISTING UI-bearing modules migrate only through explicit module-specific migration plans;
- start with low-risk/internal consumers before broad rollout.

### UI-DS-R5 — portfolio enforcement and evolution
- Inspector observes drift/stale versions;
- Blueprint tracks adoption/dependencies;
- Library maintains canonical versions;
- modules migrate gradually, never via blind cross-repository rewrites.

No design-system decision in this addendum activates cross-repository writes or changes H10,
Logistics-only automation scope, current release authority or prompt lifecycle authority.

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
