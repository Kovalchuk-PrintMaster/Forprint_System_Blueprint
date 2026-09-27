# START_HERE — ForPrint Module Bootstrap / Recovery Entry

Status: template for newly initialized or newly aligned ForPrint modules.

This document is a stable navigation surface. It must remain short. Changing task
state belongs in `coordination/status/`, prompt/work records and reports.

## 1. Module identity

- Module ID: `__MODULE_ID__`
- Display name: `__MODULE_NAME__`
- Registration state: `__REGISTRATION_STATE__`
- Module root: repository root
- System Blueprint root: normally configured by `BLUEPRINT_ROOT`
- Module owns: describe only the bounded domain approved by Blueprint/module policy.
- Module must not own: list foreign canonical domains explicitly.

For an existing registered module, live Blueprint module policy is required.
For a genuinely new module in `bootstrap_unregistered`, do not invent cross-module
ownership. Prepare a registration/alignment request instead.

## 2. Truth and instruction order

At every fresh assistant session, read current state in this order:

1. current Git branch / HEAD / worktree;
2. live Blueprint `coordination/instruction_intake/assistant_reading_order.md`;
3. live Blueprint global policy and active directives;
4. live Blueprint module policy for `__MODULE_ID__` when registered;
5. direct outgoing prompt/work authority when present;
6. Blueprint standards index and task-relevant standards;
7. module current status, reports, questions and local architecture docs;
8. local implementation details.

Module-local Blueprint snapshots and assistant packages are navigation/audit evidence,
not permanent project-wide source of truth.

## 3. Canonical recovery commands

```text
make help
make assistant-handoff-check
make module-start
make module-status
make governance-check
make module-validate
```

Fresh assistant handoff:

```text
make assistant-pack
make assistant-context-pack TOPICS=<topic[,topic...]>
```

`assistant-pack` in a module repository means `MODULE_ONBOARD`.
The Blueprint repository uses the same operator idea at project scope and produces
`PROJECT_ONBOARD`.

## 4. Required local recovery surfaces

A new module should maintain at least:

```text
AGENTS.md
README.md
forprint_module_manifest.yaml
Makefile
pyproject.toml

coordination/bootstrap/START_HERE.md
coordination/bootstrap/module_bootstrap_manifest.yaml
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
coordination/prompts/index.yaml
coordination/reports/index.yaml
```

Add deeper structure only when real responsibilities require it.

## 5. Blueprint is read-only from module work

Module workflows may:

- verify Blueprint freshness;
- read Blueprint policies, standards, module policy and prompt records;
- synchronize approved source information into module-local snapshots where the
  module's canonical tooling supports that operation.

Module workflows must not:

- `git pull` / `git fetch` Blueprint as an implicit side effect;
- write or commit in Blueprint;
- execute Blueprint-owned mutation commands from the module;
- infer global architecture authority locally.

If the Blueprint checkout is stale, stop the dependent scope and have the operator
update Blueprint from the Blueprint repository.

## 6. Repository structure

Use the live canonical structure standards. Baseline direction:

```text
app/
config/
coordination/
contracts/          # when real interface contracts exist
docs/
examples/
reports/
scripts/
tests/
Makefile
README.md
pyproject.toml
forprint_module_manifest.yaml
```

Keep the tree shallow and thematic. `scripts/` is not a dumping ground. As it grows,
prefer responsibility groups such as `coordination/`, `validation/`, `reports/`,
`diagnostics/`, `adapters/`, `previews/`, `migrations/`.

Do not create hundreds of speculative empty directories.

## 7. Operator surface

The Makefile is the module's operator-facing functional map.

Supported functionality belongs in the closest existing Make zone and must document:

- Purpose
- Safety
- Inputs
- Result

Newly initialized modules should provide working assistant continuity targets from
their first usable bootstrap:

```text
make assistant-handoff-check
make assistant-pack
make assistant-context-pack
```

Do not fake success for missing core behavior. Report `DEFERRED` or fail closed as
appropriate.

## 8. Context packages

Context packages must identify:

- package type;
- target module/scope;
- purpose;
- intended use;
- module and Blueprint Git observation;
- selected file list/hashes;
- limits/skipped files;
- explicit zero-authority declaration.

Default exclusions include secrets, customer/production bulk assets, `.git`, virtualenvs,
caches, logs and temporary outputs.

## 9. Closeout

Normal bounded work:

```text
owned diff reviewed
-> relevant checks pass
-> exact owned paths staged
-> commit
-> push
-> remote containment verified
-> owned scope returns to clean/attributable state
```

Do not destroy or absorb foreign parallel work to manufacture cleanliness.

## 10. Recovery questions

A replacement assistant must be able to answer from repository evidence:

- What is this module for?
- What does it own and explicitly not own?
- What is implemented vs planned?
- What task/prompt, if any, is authorized now?
- What is the current Git state?
- Which Blueprint documents govern this work?
- Which commands are safe?
- Which artifacts/reports are current?
- What is blocked or undecided?
- What is the next safe action?
