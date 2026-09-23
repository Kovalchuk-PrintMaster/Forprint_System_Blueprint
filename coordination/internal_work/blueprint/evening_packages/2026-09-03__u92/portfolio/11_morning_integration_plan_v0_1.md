# Morning Integration Plan — u92

## Objective

Reconcile the evening package into the live Blueprint without guessing or breaking current registry/index schemas.

## Priority order

### P0 — Preserve current authority and gates

Before mutation:
- read current release authority;
- read current module identity registry;
- confirm assistant distribution remains false;
- confirm implementation remains false;
- record branch/HEAD/status;
- preserve existing uncommitted work.

### P1 — Human Intent / Decision Capture

Integrate all u92 decisions into the existing Human Intent and append-only decision/coverage mechanisms.

No semantic invention during integration.

### P2 — New Verification Lab formalization

If live registry conventions support the proposed module:
- assign canonical module id/name;
- register as proposed/not implemented;
- create current-state evidence profile;
- create roadmap/portfolio entry;
- add ownership/dependency boundaries;
- do not create implementation prompt.

If current schema or module count invariants require additional migration, keep it as a formally tracked candidate and do not force partial registration.

### P3 — Cross-module governance

Reconcile, without duplicate standards:
- Development → Verification → Release → Runtime separation;
- Module Delivery/Maturity Sequence;
- Managed Assistant Autonomy;
- Context Budget/Episode Handoff;
- AI Cost/Credit/Runway;
- Verification/Adversarial Testing;
- Execution Policy Gate;
- Shared Resource Concurrency/Availability.

Prefer extending existing standards where semantics already exist rather than creating near-duplicates.

### P4 — Module roadmaps

Merge the roadmap deltas into the appropriate canonical module roadmaps/details:
- Website
- Mobile App
- SysAdmin
- Cloud Backup Manager
- Gateway
- Runtime Inspector
- Project Inspector
- Strategic Control Plane
- Marketing Orchestrator
- Operations Assistant
- Calculator
- CRM
- Blueprint
- Verification Lab candidate/new module

Preserve AGREED/HUMAN-CONFIRMED vs PROPOSED distinctions.

### P5 — Portfolio dependencies/readiness

Update:
- current→target descriptions;
- dependency edges;
- distribution readiness;
- Verification/Test Plane prerequisite;
- production entry prerequisites;
- paused status for Mobile App;
- no change to Logistics sole H10 pilot.

### P6 — Indexes / registrations

Refresh canonical indexes only after source-of-truth documents are reconciled.

Do not manually edit derived artifacts when generators exist.

### P7 — Validation

Run:
- affected targeted validators/tests;
- safe mutation plan/check if applicable;
- index build/check;
- Ruff;
- full pytest;
- `make check`;
- `git diff --check`;
- release guard.

Expected existing baseline before u92 integration:
- full pytest: 1010 passed, 32 skipped
- make check: 40/40
- release authority unchanged
- distribution false

Do not assume the exact pass count remains identical if new tests are deliberately added; explain deltas.

### P8 — Review report

Report:
- files added/modified;
- canonical vs proposed status;
- new module count if formally registered;
- tests/checks;
- unresolved schema/reconciliation issues;
- gates;
- no commit/push unless explicitly authorized.

## Explicit non-goals

- no cross-repo module implementation;
- no broad u80 evidence diagnostics;
- no assistant prompt distribution;
- no production environment creation;
- no Docker/Kubernetes migration;
- no OPA deployment;
- no live shell restriction rollout yet;
- no Verification Lab implementation yet.
