# ForPrint New Module / Experimental Capability Bootstrap Protocol v0.1

Status: **candidate for Blueprint reconciliation**
Date: 2026-09-27
Owner candidate: ForPrint System Blueprint
Authority: navigation / initialization policy candidate; **does not authorize implementation by itself**

## 1. Why this protocol exists

ForPrint is creating more modules, laboratories, helpers and experimental capability
boundaries. A fresh assistant must be able to enter any repository without the human
re-explaining:

- how ForPrint governance works;
- where architecture truth lives;
- what the module owns and must not own;
- how the repository is structured;
- which Make targets are canonical;
- where current status, reports and questions live;
- how to recover after context loss;
- how to package bounded context for the next assistant.

The protocol is intentionally **routing-first**. It does not copy the complete System
Blueprint into every module. Live Blueprint remains the ecosystem source of truth.

## 2. First decision: module, sub-capability, or experiment?

Before creating a repository or large tree, classify the requested work as exactly one:

1. `EXISTING_REGISTERED_MODULE`
2. `NEW_TOP_LEVEL_MODULE_CANDIDATE`
3. `EXPERIMENTAL_CAPABILITY_INSIDE_EXISTING_MODULE`
4. `HELPER_OR_LAB_NOT_YET_A_MODULE`

A convenient new name is not sufficient evidence for a new top-level module.

Use:

```text
REUSE -> EXTEND -> ADAPT -> REPLACE -> NEW
```

Before `NEW`, inspect existing module ownership, current implementation, roadmap, contracts,
operator workflows, reusable tools and current experimental boundaries.

### Decision rule

Prefer an experimental capability inside its likely owner module when:

- canonical ownership already points to that module;
- the work needs to share domain context/tooling;
- contracts are still being learned;
- retirement/absorption should be easy;
- no separate persistence/deployment/security/operational owner has been proven.

Create or propose a new top-level module only when a durable independent ownership/runtime
boundary is supported by evidence.

## 3. Live truth order

A fresh assistant must establish current state in this order:

```text
1. live Git branch / HEAD / worktree
2. live Blueprint global policy + active directives
3. live Blueprint module policy
4. explicit prompt/task/work authority
5. relevant Blueprint standards
6. current module coordination state/reports/questions
7. local docs, tests and implementation
8. historical evidence and generated context packs
```

Generated assistant packages, historical handoffs and module-local Blueprint snapshots are
navigation/evidence. They do not silently outrank live canonical sources.

## 4. Blueprint access boundary

From a module repository, Blueprint is **read-only source context**.

Allowed:

- inspect live Blueprint files;
- verify Blueprint checkout freshness through the standard read-only gate;
- read global policy, standards, module policy, prompt/work records and roadmap evidence;
- create module-local snapshots only through module-owned synchronization tooling.

Forbidden:

- module-side `git pull` / `git fetch` against Blueprint;
- write/delete/rename files inside Blueprint;
- invoke Blueprint-owned mutation commands through module Makefile aliases;
- commit/push Blueprint from module work;
- infer architecture/acceptance/release authority from a context file.

If Blueprint is stale, the dependent work scope stops until Blueprint is updated from its own
repository.

## 5. Required live Blueprint reading routes

New-module bootstrap should route to, not duplicate, at least:

```text
coordination/instruction_intake/assistant_reading_order.md
coordination/instruction_intake/instruction_sources.yaml

coordination/global_policy/forprint_project_doctrine.md
coordination/global_policy/clean_tree_first_working_policy_v0_1.md

coordination/standards/index.yaml
coordination/standards/module_assistant_start_protocol.md
coordination/standards/project_structure_standard.md
coordination/standards/repository_structure_baseline.md
coordination/standards/make_command_standard.md
coordination/standards/module_make_target_contract.md
coordination/standards/module_standards_awareness_protocol.md

coordination/standards/governance/folder_architecture_policy.md
coordination/standards/governance/documentation_and_recovery_gate.md
coordination/standards/governance/module_workflow_automation_and_external_input_policy.md
coordination/standards/governance/module_workflow_command_architecture_v0_1.md

coordination/standards/modular_topology_and_resilience/module_global_context_policy.md
coordination/standards/modular_topology_and_resilience/data_ownership_and_storage_policy.md
```

Task-specific standards are added from `coordination/standards/index.yaml`.

## 6. Repository bootstrap surface

### 6.1 Minimal new-module tree

The starting shape should be small:

```text
<module_root>/
├── AGENTS.md
├── app/
├── config/
├── coordination/
│   ├── bootstrap/
│   │   ├── START_HERE.md
│   │   └── module_bootstrap_manifest.yaml
│   ├── prompts/
│   │   └── index.yaml
│   ├── reports/
│   │   └── index.yaml
│   └── status/
│       ├── current_status.yaml
│       ├── current_status.md
│       └── next_questions_for_blueprint.md
├── docs/
├── examples/
├── reports/
├── scripts/
│   └── coordination/
│       └── module_assistant_context.py
├── tests/
├── Makefile
├── README.md
├── pyproject.toml
└── forprint_module_manifest.yaml
```

Add `contracts/` when real interface contracts or explicit placeholder-contract evidence exists.
Add deeper app/scripts/test directories only when implementation responsibilities justify them.

### 6.2 Directory discipline

Prefer shallow thematic grouping.

Good:

```text
scripts/coordination/
scripts/validation/
scripts/reports/
scripts/diagnostics/
scripts/adapters/
scripts/previews/
```

Bad:

```text
scripts/final.py
scripts/fix2.py
scripts/helper_new.py
scripts/temp.py
scripts/another_script.py
```

Do not pre-create a speculative filesystem representation of the entire future roadmap.

Planned capability horizons belong primarily in architecture/roadmap documentation until real
source/tests/config/artifacts need a directory.

## 7. Agent and recovery entrypoints

### AGENTS.md

Every newly initialized module gets a small root `AGENTS.md`.

It contains stable cross-agent instructions only:

- read START_HERE;
- verify Git and live Blueprint;
- Make-first workflow;
- module/Blueprint ownership boundaries;
- safe Git rules;
- assistant package semantics.

It must **not** become a changing status document.

### coordination/bootstrap/START_HERE.md

This is the canonical module-local recovery/navigation document.

It answers:

- what the module is;
- what it owns / must not own;
- how to read current Blueprint;
- where current state/reports/questions live;
- canonical operator commands;
- how fresh assistants build/consume context;
- what to do after interruption.

### Optional GitHub-native instructions

`.github/copilot-instructions.md` may point GitHub Copilot to AGENTS.md and START_HERE.
Path-specific instructions may be used for special subtrees.

Do not copy the full governance corpus into Copilot instructions.

## 8. Assistant continuity contract

New modules implement from first usable bootstrap:

```text
make assistant-handoff-check
make assistant-pack
make assistant-context-pack
```

### 8.1 assistant-handoff-check

Read-only.

Verifies:

- module Git identity/state;
- AGENTS.md;
- START_HERE;
- module manifest;
- Makefile;
- current coordination state;
- readable Blueprint root;
- canonical Blueprint reading routes;
- registered module policy when applicable.

### 8.2 assistant-pack

Builds onboarding for the repository in which it runs.

Semantic identity:

```text
System Blueprint -> PROJECT_ONBOARD
module repository -> MODULE_ONBOARD
```

A module pack is authoritative only for the bounded captured module evidence. It is not
project-wide authority.

### 8.3 assistant-context-pack

Builds a narrower package:

```text
package_type: MODULE_CONTEXT
```

It may accept:

```text
SCOPE=...
TOPICS=...
```

Domain workflows may later add bounded selectors such as `CASE` / `REVISION`.

### 8.4 Package minimum identity

Every package states:

```text
package_type
target_module_or_portfolio_scope
purpose
intended_use
module branch + HEAD
Blueprint branch + HEAD observation
selected module files + hashes
live Blueprint source references + hashes
limits / skipped files
authority boundary
```

Archive integrity is not authority.

### 8.5 Package exclusions

Default-exclude:

- `.git/`
- virtualenvs
- caches
- `node_modules`
- secrets / `.env`
- credentials / private keys
- huge customer assets
- bulk production outputs
- unrelated runtime logs
- unrelated temporary evidence.

## 9. Makefile as operator functional map

The Makefile is not a shell shortcut collection.

Public targets belong in the closest canonical zone and document:

```text
Purpose
Safety
Inputs
Result
```

Newly initialized modules use the current standard template and provide real implementations
for the baseline commands they expose.

The continuity targets live with document/context awareness, because they build navigation and
handoff evidence rather than business runtime.

Do not overload zone `90` with standard functionality. Zone `90` is for genuinely module-
specific helpers.

## 10. Module startup states

### REGISTERED

`MODULE_REGISTRATION_STATE=registered`

Requirements:

- Blueprint module policy exists;
- canonical module identity exists;
- assistant-handoff-check fails if the policy route disappears.

### BOOTSTRAP_UNREGISTERED

`MODULE_REGISTRATION_STATE=bootstrap_unregistered`

Allowed only for genuine new-module incubation.

It may:

- read global Blueprint governance;
- build local bootstrap files;
- inspect ecosystem ownership;
- prepare a module-registration/alignment request;
- perform explicitly authorized local experiments that do not claim foreign ownership.

It may not:

- invent a canonical module role;
- claim production authority;
- create live cross-module contracts as accepted truth;
- mutate Blueprint;
- treat lack of module policy as permission.

## 11. Coordination minimum

New active modules should establish machine-readable coordination early:

```text
coordination/status/current_status.yaml
coordination/prompts/index.yaml
coordination/reports/index.yaml
coordination/status/next_questions_for_blueprint.md
```

No unresolved `{now}`, `{branch}`, `{commit}` or similar runtime placeholders in live records.

Human-readable current status may live beside YAML.

## 12. Configuration / secret boundary

Committed configuration contains safe defaults, schemas and examples.

Secrets never live in committed config or assistant packs.

Paths should be logical/configurable rather than scattered absolute `/srv/...` literals in
business logic.

Early-stage experiments may use local filesystem/SQLite/fixtures, but must not claim production
truth unless explicitly approved.

## 13. Testing and verification

A new module should reach a minimal testable state early.

Baseline direction:

```text
make env-check
make tooling-check
make config-check
make secrets-check
make lint
make test
make check
make check-report
make governance-check
make module-validate
```

Only implement targets that have real behavior; a missing required target fails or reports an
explicit documented deferral.

Verification is not acceptance.

## 14. Git / parallel-work discipline

Default development flow:

```text
bounded work
-> validate
-> exact owned staging
-> commit
-> push
-> remote containment
-> clean/attributable state
```

Never manufacture cleanliness by deleting, resetting, stashing or absorbing another assistant's
work.

Exact collision in the intended write set is a STOP condition.

## 15. Documentation and recovery definition of done

A meaningful workflow is not done because code exists.

Another assistant must be able to recover:

- what changed and why;
- source of truth;
- operator commands;
- generated artifacts;
- verification path;
- architecture/ownership boundary;
- current work state;
- next safe action.

Do not create a new permanent document for every tiny step. Update existing authoritative
documents unless semantics materially require a new revision.

## 16. New module initialization sequence

### Phase 0 — read-only classification

1. Inspect target repo/current tree if it exists.
2. Read live Blueprint policy/module/roadmap/machine evidence.
3. Classify module vs sub-capability vs lab/helper.
4. Produce REUSE/EXTEND/ADAPT/REPLACE/NEW map.
5. Identify exact ownership and non-ownership.
6. Stop on unresolved architectural collision.

### Phase 1 — minimal skeleton

1. Create only justified root/directories.
2. Create manifest, README, AGENTS, START_HERE and coordination minimum.
3. Adapt Makefile template.
4. Install module assistant-context helper.
5. Add safe environment/config templates.
6. Add first tests for structural/governance invariants.

### Phase 2 — assistant continuity

1. `make assistant-handoff-check`
2. `make assistant-pack`
3. inspect package manifest
4. `make assistant-context-pack TOPICS=bootstrap`
5. prove no Blueprint/Git mutation occurred.

### Phase 3 — first useful business/technical loop

Implement the smallest explicitly authorized capability. Avoid speculative platform work.

### Phase 4 — closeout

1. relevant tests/checks;
2. current status/report update;
3. exact-path stage/commit/push;
4. remote containment;
5. record open Blueprint questions.

## 17. Required Blueprint-side follow-up for this candidate

If adopted, update/reconcile together:

1. `coordination/standards/module_assistant_start_protocol.md`
2. `coordination/standards/make_command_standard.md`
3. `coordination/standards/module_make_target_contract.md`
4. `coordination/templates/module_makefile_standard.template.mk`
5. `coordination/standards/module_pre_commit_protocol.md`
6. `coordination/standards/index.yaml`
7. add a canonical new-module bootstrap standard/pointer
8. add/reference generic module assistant-context implementation
9. add template tests for required targets and zero-authority package metadata.

Do not make only a Makefile change and leave the standards behind.
