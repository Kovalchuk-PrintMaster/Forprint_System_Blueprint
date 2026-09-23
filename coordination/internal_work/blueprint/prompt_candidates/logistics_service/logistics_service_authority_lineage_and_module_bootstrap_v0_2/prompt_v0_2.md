# Logistics Service — Authority, Lineage and Module Bootstrap v0.2

Status: RELEASE CANDIDATE — NOT RELEASED
Execution class: `MODULE_BOOTSTRAP`
Module: `logistics_service`
Predecessor: `logistics_service_authority_lineage_and_module_bootstrap_v0_1`

## Purpose

Reconcile the existing Logistics self-knowledge baseline and convert it into a
self-maintaining, development-ready module baseline without introducing a second
orchestration framework.

The module already contains substantial self-knowledge. Do not rebuild it from
scratch. Verify, reconcile, complete, automate maintenance, and preserve compatible
paths and behavior.

## Stage 0 — mandatory module-local hygiene

Before bootstrap implementation:

1. Read root `AGENTS.md` and all available Module Memory/self-knowledge surfaces.
2. Inspect branch, HEAD, upstream and full git status.
3. Classify every pre-existing local change. Do not discard unknown work.
4. Reconcile intentional valid preparation changes.
5. Run the module validation/check path before beginning assigned implementation.
6. Commit intentional module-local preparation changes.
7. Push the current module branch.
8. Verify upstream synchronization.
9. Only then begin bootstrap implementation.

Forbidden during Stage 0 and the whole task:

- force push;
- `git reset --hard`;
- `git clean` used to manufacture cleanliness;
- blind revert;
- rebase without explicit prompt authority;
- cross-repository writes;
- Blueprint repository mutation;
- production provider writes unless separately authorized.

## Bootstrap implementation

### 1. Reconcile self-knowledge

Verify and complete, without duplicating frameworks:

- root `AGENTS.md`;
- Module Memory;
- deterministic inventory/index;
- implementation lineage/evolution chains;
- documentation authority;
- roadmap state;
- compatibility/legacy mapping;
- fresh-context validation.

Preserve the existing `scripts/knowledge/build_module_memory_index.py` / Makefile
maintenance path unless an evidence-backed evolution is required.

### 2. Resolve HEAD-bound generated freshness self-reference

The compatibility paths:

- `coordination/module_memory/current_state.yaml`
- `coordination/module_memory/fresh_context_manifest.yaml`

are runtime-generated HEAD-bound freshness surfaces. They must exist after generation
but must not create a tracked commit/HEAD self-reference cycle.

Required target model:

- `current_state.yaml` = generated runtime, untracked + gitignored;
- `fresh_context_manifest.yaml` = generated runtime, untracked + gitignored;
- `inventory_index.yaml` remains tracked and deterministic.

Do not remove the strict HEAD equality guard. Do not relax clean-worktree semantics.
Do not make Blueprint write these module files.

### 3. Automatic maintenance

Make the module able to deterministically rebuild and validate:

- inventory/index;
- lineage and authority relationships where applicable;
- runtime-generated current state;
- fresh-context manifest;
- module self-knowledge freshness.

Existing compatibility entrypoints should remain stable.

### 4. Module-owned worker runtime

Create/reconcile `config/worker_runtime.yaml` as the non-secret module-owned runtime
profile required before normal roadmap development.

Do not store provider credentials or secrets in git.

### 5. Validation and finalization

Run the complete module validation suite.

Commit and push the bootstrap implementation within the Logistics repository.
After the final commit:

1. regenerate ignored runtime-generated freshness surfaces;
2. verify they bind the final module HEAD;
3. run fresh-context validation;
4. run the full module check;
5. verify the git worktree is clean;
6. verify upstream is synchronized.

## Completion evidence

Publish a completion report containing:

- module identity, branch, HEAD and upstream;
- Stage 0 actions and evidence;
- requirements/results;
- changed files;
- validation evidence;
- inventory/lineage/authority impact;
- generated freshness status;
- worker runtime status;
- repo cleanliness/upstream status;
- boundaries and prohibited actions respected;
- gaps/risks/unknowns;
- evidence manifest.

Inspector conformance review is read-only and is performed by
`forprint_project_inspector`.

The Inspector does not own human `ACCEPT / RETURN / HOLD`.
Do not claim Blueprint ACCEPT and do not release the next prompt.
