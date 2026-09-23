# Development Environment Architecture v0.1

Status: PROPOSED_FOR_CANONICAL_RECONCILIATION

## Core decision

ForPrint will not choose between:
- unrestricted AI that can mutate a live production system, and
- a safe but nearly powerless AI.

Instead, each logical module may operate through distinct execution profiles:

`DEVELOPMENT → VERIFICATION → RELEASE → RUNTIME`

The same logical module may propose, implement and test its own improvement in Development, while the deployed Runtime remains immutable between releases.

## Architectural invariant

**Broad capability, narrow blast radius.**

A development agent may have broad shell and package-management capability inside its own development boundary. Broad development rights do not imply:
- write access to unrelated module repositories;
- write access to production data;
- access to production secrets;
- authority to deploy directly;
- authority to bypass IAM/policy gates.

## Recommended filesystem model

Do not move existing repositories merely to satisfy this proposal. Adopt the separation gradually.

### Source repositories

Existing source repositories remain Git-controlled under the established development root, for example:

`/srv/software_development/forprint-project/<module-repository>/`

Repository content should contain:
- source;
- tests;
- migrations;
- manifests;
- lock files;
- small fixtures;
- governance/coordination metadata.

Repository content should not become the long-term store for:
- large installers;
- driver banks;
- production backups;
- large AI/model caches;
- persistent runtime queues;
- production secrets;
- large generated temporary artifacts.

### Mutable development state

Proposed sibling root:

`/srv/software_development/forprint-devstate/<module_id>/`

Recommended children:

- `venv/` — module-specific virtual environment;
- `tmp/` — disposable work;
- `cache/` — package/model/tool cache;
- `build/` — local build outputs;
- `scratch/` — experiments;
- `logs/` — development execution logs;
- `downloads/` — temporary development downloads, lifecycle-controlled.

This keeps mutable state outside Git repositories while retaining per-module isolation.

Existing in-repository `.venv_*` environments may remain during migration. Do not mass-move them until module-by-module readiness is proven.

### Shared immutable release artifacts

Proposed root:

`/srv/software_development/forprint-artifacts/<module_id>/<version>/`

Properties:
- immutable after build;
- versioned;
- checksum/provenance recorded;
- dependencies locked;
- built from a known source revision;
- promoted, not edited in place.

### Isolated Test Plane

Proposed root:

`/srv/software_development/forprint-test/`

A test run gets an isolated namespace, for example:

`/srv/software_development/forprint-test/runs/<test_run_id>/`

The Test Plane may contain:
- test database/schema;
- test filesystem;
- synthetic users;
- fake printers;
- fake taxi/payment/email/SMS/cloud adapters;
- replay fixtures;
- generated adversarial data;
- temporary queues/caches;
- disposable artifacts.

No live external side effects by default.

### Production runtime

Production is separate from source workspaces.

Illustrative root:

`/srv/forprint-runtime/`

Suggested split:

- `releases/<module_id>/<version>/` — deployed immutable release;
- `current/<module_id>` — controlled pointer to active version;
- `var/<module_id>/` — module-owned runtime mutable state;
- `logs/<module_id>/` — runtime logs/traces;
- `staging/` — promotion candidate runtime;
- configuration/secrets via protected configuration/secrets mechanisms, not committed repository files.

Exact physical paths remain implementation-time decisions. The separation itself is the invariant.

## Identity and permission model

Use distinct service/development identities where practical.

### Development identity: `fpdev_<module_id>`

May:
- read/write own module development repository/worktree;
- read/write own devstate;
- create venv;
- install development dependencies in own environment;
- run tests/builds;
- read approved Blueprint authority;
- access synthetic/test data.

Must not by default:
- write unrelated module repositories;
- write production DB;
- read production secrets;
- activate releases;
- mutate production filesystem.

### Runtime identity: `fprun_<module_id>`

May:
- execute deployed release;
- read its immutable package;
- access only approved runtime APIs/data;
- write only module-owned runtime state;
- perform capability-shaped actions allowed by IAM/policy.

Must not:
- modify source;
- `pip install` into live environment;
- `git pull` into production;
- rewrite its own deployed code;
- obtain arbitrary cross-module filesystem write;
- bypass release controller.

### Verification Lab identities

Use at least three conceptual profiles:

- BLACK_BOX_ACTOR — sees only the public/user-facing surface appropriate to the simulated actor.
- GRAY_BOX_TESTER — sees declared contracts/capabilities but not all internal implementation details.
- WHITE_BOX_ANALYZER — read-only access to source/contracts/traces necessary for diagnosis.

The Verification Lab may have broad rights inside Test Plane and no direct production mutation rights.

### Release Controller identity

Deterministic infrastructure identity.

May:
- read signed/approved build artifacts;
- deploy/promote versioned releases;
- switch active version;
- execute approved migration plans;
- perform health checks;
- rollback.

Must not be an AI authority and must not invent policy.

## Dependency installation policy

Development:
- package install is permitted inside module-owned development environment;
- newly used dependencies become pinned/locked and documented;
- experiments do not automatically become production dependencies.

Production:
- dependencies are part of a versioned artifact;
- runtime does not install/update libraries ad hoc;
- new library requires a new tested artifact.

## Runtime self-improvement model

Allowed:

`runtime evidence → improvement candidate → development change → tests → Verification Lab → release candidate → promotion`

Disallowed:

`runtime AI → arbitrary shell → mutate live source/dependencies → continue serving traffic`

This preserves self-improvement while controlling blast radius.

## State survival across releases

Durable business/runtime state is not owned by a release directory.

Examples:
- PostgreSQL data;
- queues/outbox/inbox;
- persistent workflow state;
- object storage;
- approved runtime state directories.

Version each in-flight record where needed:
- workflow version;
- payload schema;
- contract version;
- producer version.

A release may:
- drain old workers;
- remain backward compatible;
- migrate using an explicit migration plan.

It must not assume that replacing code deletes or resets durable state.

## Database change pattern

Prefer `expand → migrate → contract`.

1. Add backward-compatible schema.
2. Keep old consumers working.
3. deploy new code;
4. migrate/backfill;
5. switch reads/writes;
6. verify consumers;
7. remove legacy structure only after adoption and governance pass.

## Development risk classes

### DEV_LOCAL
Examples:
- modify own code/tests;
- create/delete own temporary files;
- rebuild venv;
- install package in own venv;
- generate fixtures.

Default: autonomous inside development boundary.

### SAFE_REVERSIBLE
Examples:
- build release artifact;
- stage feature flag;
- run synthetic test campaign.

Default: automated pipeline, auditable.

### CROSS_MODULE
Examples:
- contract/schema/interface change;
- ownership change;
- shared data semantics.

Default: governance/contract gate.

### PROD_HIGH_IMPACT
Examples:
- destructive migration;
- production data deletion;
- external payment/order/taxi side effect;
- broad credential/permission change.

Default: deterministic policy evaluation + explicit operator approval where required.

### FORBIDDEN
Examples:
- bypass IAM;
- extract secrets without an authorized purpose;
- uncontrolled cross-repository destruction;
- disable audit controls to complete a task.

Default: deny.

## Production entry prerequisites

A module does not enter unrestricted production merely because its feature works.

Minimum production readiness:
- explicit owner/boundary;
- current-state evidence;
- roadmap/target state;
- deterministic tests;
- Verification Lab coverage appropriate to risk;
- versioned artifact;
- dependency lock/provenance;
- environment configuration separation;
- service identity/least privilege;
- runtime health telemetry;
- context/cost monitoring if AI-backed;
- rollback plan;
- migration plan where applicable;
- no live external test side effects;
- approval state explicitly satisfied.

## Migration strategy from current development

Do not stop current development to redesign everything.

Phase 1:
- preserve current repository layout;
- standardize ownership and paths;
- introduce devstate root gradually;
- keep broad development shell.

Phase 2:
- create Test Plane before adversarial automation;
- introduce fake external adapters;
- add Verification Lab.

Phase 3:
- introduce immutable versioned artifacts and deterministic release controller.

Phase 4:
- restrict production runtime identities and tool surfaces.

Phase 5:
- enable managed self-evolution based on evidence and risk classes.
