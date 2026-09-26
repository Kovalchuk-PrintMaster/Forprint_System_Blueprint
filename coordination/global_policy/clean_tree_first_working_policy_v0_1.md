---
document_id: forprint_clean_tree_first_working_policy_v0_1
status: ACTIVE_FORWARD_DEFAULT_WITH_GRANDFATHERED_PARALLEL_WORK
owner: forprint_system_blueprint
effective_date: 2026-09-26
supersedes_as_default: broad_dirty_tree_tolerance_as_normal_working_style
preserves_for_compatibility: execution_workspace_compatibility_semantics_for_existing_contracts
---

# ForPrint Clean-Tree-First Working Policy v0.1

## 1. Decision

ForPrint returns to a **clean-tree-first** working discipline.

The previously introduced dirty-tree compatibility model solved real execution and parallel-work
problems, but it must no longer be interpreted as the preferred normal way to perform assistant
or operator development.

New default:

```text
bounded work
-> validate
-> commit owned files
-> push
-> return owned scope to clean/attributable state
-> begin next unrelated mutation
```

## 2. What remains true from the earlier compatibility policy

The following lessons remain valid:

- repository freshness is not identical to task compatibility;
- a sender repository may advance after an immutable task is published;
- unrelated operator/assistant work must never be destroyed merely to manufacture cleanliness;
- execution ownership must stay attributable;
- multiple writers must not silently share one dirty mutation surface;
- real parallelism should prefer isolated workspaces.

These semantics remain useful for compatibility and already-active execution contracts.

## 3. What changes

Broad dirty Blueprint state is no longer the routine preferred operator state.

Instead:

- global cleanliness is the target when practical;
- each assistant starts with a clean/attributable owned write set;
- each assistant finishes, validates, commits and pushes bounded owned changes promptly;
- unrelated foreign dirty paths are a temporary parallel-work exception;
- long-lived accumulation of unrelated uncommitted work is discouraged;
- exact-scope collision guards are safety mechanisms, not a replacement for good Git hygiene.

## 4. Current parallel-assistant transition

At policy introduction more than one assistant is active in Blueprint.

The transition must be non-destructive.

Therefore:

- existing CF-10 work is grandfathered until safe commit boundaries;
- no reset/stash/clean of CF-10 work;
- no rewriting CF-10 execution baseline;
- no staging CF-10-owned files in module-analysis commits;
- module-analysis work commits only its owned targets;
- each active workstream progressively returns its own scope to clean state.

This policy does not retroactively invalidate an already active immutable execution contract.

## 5. Shared checkout rule

If foreign dirty paths exist:

```text
foreign dirty path
    -> read-only context

exact target collision
    -> STOP / reconcile

owned clean target
    -> bounded mutation permitted after precondition check
```

Never use as a normal staging shortcut:

- `git add .`
- `git add -A`

Stage exact owned paths.

## 6. Module-analysis rule

Read-only reconstruction may inspect a dirty repository because dirty state may itself be evidence.

Durable mutation and closeout should follow clean-tree-first discipline.

A module audit records:

- dirty state at observation time;
- ownership of pre-existing changes;
- whether analysis itself mutated the module;
- exact commit that becomes the durable snapshot baseline.

## 7. Historical policy preservation

Do not delete the earlier execution-workspace compatibility text.

Preserve it as lineage and compatibility evidence.

Add a clear supersession/current-default note so future assistants understand:

- why the old rule existed;
- which compatibility semantics remain valid;
- why clean-tree-first is now preferred.

## 8. Parallelism target

When genuine concurrent mutation is needed:

`isolated Git worktrees / equivalent attributable execution workspaces`

are preferred over multiple writers sharing one dirty checkout.

## 9. Closeout rule

A bounded assistant task should normally end with:

```text
owned diff reviewed
-> relevant checks pass
-> exact owned paths staged
-> commit
-> push
-> remote containment verified
-> owned scope clean
```

If foreign work remains dirty, record it as foreign parallel context rather than absorbing it into
the current commit.

## 10. Forbidden cleanup shortcuts

Never use these merely to satisfy cleanliness policy:

- broad `git reset --hard`;
- broad `git clean`;
- automatic stash/pop of operator or another assistant's work;
- staging all dirty files;
- deleting unrecognized foreign temporary evidence.

Clean-tree-first means attributable history, not destructive cleanup.
