# Module Workflow Command Architecture v0.1

Status: Draft for Blueprint review
Owner: ForPrint System Blueprint
Target scope: Blueprint and every current or future ForPrint module repository admitted through Blueprint-owned registration or onboarding control
External rollout: Gated
Version: 0.1
Date: 2026-08-01
Draft authority: Reference only. This document becomes normative only after
explicit Blueprint approval. Until approval, MUST and MUST NOT statements
describe the proposed target architecture and do not authorize rollout or
repository mutation.

## 1. Purpose

This standard defines the command architecture for coordinated work between
ForPrint System Blueprint and autonomous module repositories.

The architecture separates:

- read-only validation from mutation;
- module completion from Blueprint acceptance;
- local module execution from Blueprint review;
- preparation from release;
- preview from apply;
- local publication from merge;
- canonical coordination state from generated runtime views.

The goal is to make every operator command predictable, auditable,
repository-bounded, and suitable for automation.

## 2. Scope

This document controls the semantics of workflow commands exposed through
Make or an equivalent operator interface.

It defines:

- command naming rules;
- read/write behavior;
- repository ownership boundaries;
- completion packet lifecycle;
- Blueprint intake lifecycle;
- Git behavior;
- idempotency requirements;
- migration order;
- acceptance criteria.

This version documents the target architecture first. Existing Makefiles,
templates, and module implementations may temporarily differ until migrated.

Scope membership is not defined by a hard-coded module list or by every
directory under a local filesystem root. A runtime project root may contain
temporary worktrees, tooling, archives, and experiments. A repository enters
scope through Blueprint-owned registration or onboarding metadata and then
inherits this architecture by repository class without changing this standard.
Planned, onboarding, active, and paused modules remain in scope unless an
explicit lifecycle decision excludes them.

## 3. Normative terms

The words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative.

Read-only means:

- no tracked or untracked repository file changes;
- no changes to Git index, refs, worktree, branches, tags, or repository configuration;
- no changes to prompt, roadmap, status, report, or completion indexes;
- no writes to another repository;
- output only to stdout, stderr, or temporary storage outside the repository root;
- ignored runtime artifacts are generated output and therefore MUST NOT be
  produced by commands classified as read-only.

Mutation means an intentional state change performed by a command whose name
clearly communicates the mutation.

## 4. Core design rules

### 4.1 Semantic command names

Commands containing any of the following terms MUST be read-only:

```text
check
validate
preview
status
show
list
```

A command that mutates state MUST use an explicit mutation verb, such as:

```text
prepare
release
apply
finish
publish
accept
return
update
fix
```

A read-only command MUST NOT hide an apply operation.

### 4.2 Preview before apply

Where mutation is material, the workflow SHOULD provide a read-only preview
before the mutating command.

The preview and apply commands MUST use the same normalized input contract.

### 4.3 Repository autonomy

Each repository owns and executes its own automation.

A module:

- reads published Blueprint prompts, standards, and contracts;
- executes module-owned scripts from the module repository;
- writes only module-owned coordination and implementation files;
- does not mutate Blueprint;
- does not mark Blueprint acceptance.

Blueprint:

- reviews module evidence from the Blueprint repository;
- executes Blueprint-owned review and intake scripts;
- writes only Blueprint-owned review, queue, roadmap, and acceptance metadata;
- does not execute module-owned mutation commands;
- does not mutate the module worktree.

The final target architecture MUST NOT require a module to execute Blueprint
executables as its normal workflow, and MUST NOT require Blueprint to execute
module executables during review.

### 4.4 Completion is not acceptance

The module state:

```text
completed_in_module
```

is distinct from the Blueprint state:

```text
accepted_by_blueprint
```

A module may complete and publish its work while Blueprint review remains
pending.

### 4.5 Publication is not merge

`module-publish` may commit and push module-local work.

It MUST NOT merge the module branch into a protected or integration branch.
Merge remains a separate operator or repository-governance decision.

## 5. Command taxonomy

| Command class | Expected behavior | Persistent writes |
| --- | --- | --- |
| Navigation | Read instructions and state | No |
| Validation | Check contracts and evidence | No |
| Preview | Produce a mutation plan | No |
| Local apply | Mutate current repository only | Yes |
| Publication | Commit and push current repository | Yes |
| Blueprint decision | Record acceptance or return in Blueprint | Yes |
| Reporting view | Render current state | No canonical writes |

## 6. Blueprint operator commands

### 6.1 `prompt-prepare`

Purpose:

```text
Create or update a Blueprint-owned draft prompt and its draft metadata.
```

Behavior:

- mutates Blueprint only;
- MUST NOT publish executable work to a module;
- MUST validate target module identity and prompt lineage;
- SHOULD leave the prompt in a clearly non-executable draft state.

### 6.2 `prompt-release`

Purpose:

```text
Publish an approved prompt for module execution.
```

Behavior:

- mutates Blueprint only;
- requires an already prepared and validated prompt;
- updates Blueprint-owned outgoing prompt and queue metadata;
- MUST NOT modify the target module repository;
- MUST preserve prompt identity and release lineage.

### 6.3 `prompt-status`

Purpose:

```text
Show prompt preparation, release, execution, and review state.
```

Behavior:

- read-only;
- distinguishes draft, released, completed in module, pending review,
  accepted, returned, and superseded states;
- MUST NOT infer success without recorded evidence.

## 7. Module operator commands

### 7.1 `module-start`

Purpose:

```text
Prepare the module worktree for execution of a released prompt.
```

Behavior:

- MAY update module-local awareness or runtime context;
- MUST validate that the prompt is released and targets the current module;
- MUST NOT mutate Blueprint;
- MUST NOT perform completion or publication automatically.

### 7.2 `module-sync`

Purpose:

```text
Refresh module-local awareness of published Blueprint state.
```

Behavior:

- writes only module-local cache or coordination state when explicitly needed;
- SHOULD be safe to repeat;
- MUST NOT modify Blueprint;
- MUST NOT begin implementation automatically.

### 7.3 `module-status`

Purpose:

```text
Show current module prompt, branch, validation, completion, and publication state.
```

Behavior:

- read-only;
- reports evidence rather than assumptions;
- distinguishes local completion from remote publication and Blueprint review.

### 7.4 `module-validate`

Purpose:

```text
Run module-owned validation without changing semantic module state.
```

Behavior:

- read-only;
- executes module-owned validators;
- MUST NOT update completion packets, prompt indexes, roadmap state,
  status records, or tracked reports;
- MUST NOT commit, push, merge, or mutate Blueprint.

### 7.5 `module-finish`

Purpose:

```text
Finalize completed work inside the module repository.
```

Behavior:

- may create or update module-local completion packet, report, status,
  and indexes;
- runs validation before applying completion state;
- MUST NOT commit or push;
- MUST NOT merge;
- MUST NOT record Blueprint acceptance;
- SHOULD be idempotent after successful completion.

### 7.6 `module-publish`

Purpose:

```text
Publish completed module-local work to the configured remote branch.
```

Behavior:

- validates module completion and clean publication boundaries;
- may create the module completion commit;
- may push the current module branch;
- verifies that the configured remote branch contains the published commit;
- emits publication evidence to stdout or an explicitly ignored runtime receipt;
- MUST NOT rewrite tracked completion artifacts after push solely to embed
  the commit hash that was just created;
- MUST NOT merge;
- MUST NOT mutate Blueprint.

## 8. Module completion packet commands

### 8.1 `completion-packet-validate`

Purpose:

```text
Validate packet schema and static field constraints.
```

Behavior:

- read-only;
- no packet mutation;
- no coordination mutation;
- no Git mutation.

### 8.2 `completion-packet-check`

Purpose:

```text
Perform the full read-only completion evidence and lineage check.
```

The check SHOULD include, where applicable:

- module ID;
- prompt ID;
- packet schema;
- completion report path;
- implementation commit;
- completion commit;
- commit ancestry;
- remote containment;
- push status;
- required checks;
- boundary confirmations;
- module-local prompt and roadmap linkage.

Before `module-publish`, publication-only evidence such as remote containment
and push status MUST be reported as `PENDING_PUBLICATION`, not as successful
and not as a validation failure.

After `module-publish`, the same command MUST verify the complete publication
evidence and lineage.

It MUST NOT invoke apply.

### 8.3 `completion-packet-preview`

Purpose:

```text
Render the exact module-local changes that apply would perform.
```

Behavior:

- read-only;
- shows files, fields, status transitions, and index operations;
- MUST NOT write the plan into canonical coordination files;
- SHOULD be deterministic for identical inputs and repository state.

### 8.4 `completion-packet-apply`

Purpose:

```text
Apply the validated completion packet to module-local coordination state.
```

Behavior:

- mutates the module repository only;
- requires successful validation;
- MUST NOT modify Blueprint;
- MUST NOT commit, push, or merge;
- SHOULD produce no semantic changes when repeated after success.

### 8.5 `completion-packet-idempotency-check`

Purpose:

```text
Prove that completion apply is semantically idempotent.
```

Behavior:

- read-only with respect to the live module worktree;
- MUST NOT run live apply twice;
- SHOULD use a temporary sandbox, copied fixture, in-memory model,
  or equivalent isolated state;
- compares first-apply and second-apply semantic results;
- fails on unexpected drift.

## 9. Blueprint completion intake commands

### 9.1 `completion-intake-preview`

Purpose:

```text
Preview Blueprint-owned intake changes for a published module completion.
```

Behavior:

- read-only;
- reads module evidence;
- does not execute module mutation commands;
- shows intended Blueprint queue, roadmap, incoming report, and review updates.

### 9.2 `completion-intake-check`

Purpose:

```text
Independently validate module completion evidence from Blueprint.
```

Behavior:

- read-only;
- implemented and executed by Blueprint;
- MUST NOT rely solely on module-declared success;
- verifies commit identity, lineage, remote containment, packet/report
  consistency, required checks, and repository boundaries;
- MUST NOT modify the module repository or Blueprint state.

### 9.3 `completion-accept`

Purpose:

```text
Record Blueprint acceptance of verified module completion.
```

Behavior:

- mutates Blueprint only;
- requires successful `completion-intake-check`;
- updates Blueprint-owned review, queue, roadmap, and incoming report metadata;
- records acceptance evidence and decision identity;
- MUST NOT modify the module repository;
- MUST NOT merge module code automatically.

### 9.4 `completion-return`

Purpose:

```text
Return module completion for correction with explicit Blueprint review notes.
```

Behavior:

- mutates Blueprint only;
- records actionable return reasons;
- preserves submitted evidence and review history;
- MUST NOT rewrite module completion state;
- MUST NOT modify the module repository.

## 10. Ownership boundary matrix

| Operation | Module repository | Blueprint repository |
| --- | ---: | ---: |
| Read released prompt | Read | Owns source |
| Execute implementation | Owns | No |
| Validate module code | Owns | No |
| Create completion packet | Owns | No |
| Mark `completed_in_module` | Owns | No |
| Commit and push module branch | Owns | No |
| Read completion evidence | Owns source | Read |
| Independently validate intake | No execution required | Owns |
| Mark `accepted_by_blueprint` | No | Owns |
| Return for correction | Receives decision | Owns |
| Merge module branch | Separate governance action | Separate governance action |

No command may silently cross this boundary.

## 11. State model

Recommended prompt lifecycle:

```text
draft
-> prepared
-> released
-> in_progress
-> completed_in_module
-> published_by_module
-> received_pending_blueprint_review
-> accepted_by_blueprint
```

Return path:

```text
received_pending_blueprint_review
-> returned_for_fix
-> in_progress
```

Supersession path:

```text
draft | prepared | released
-> superseded
```

Each transition MUST have a clear repository owner and evidence source.

## 12. Git behavior

Read-only commands MUST NOT invoke:

```text
git add
git commit
git push
git pull
git fetch
git merge
git rebase
git reset
git restore
git clean
git checkout
git switch
git tag
```
Read-only remote-containment checks SHOULD use `git ls-remote` or already
available immutable evidence rather than updating local remote-tracking refs.

`module-publish` is the only standard module workflow command in this version
that may commit and push.

`module-finish` MUST stop before Git publication.

`completion-accept` and `completion-return` MUST NOT commit or push.

Blueprint Git publication is a separate explicit operator step. The semantic
acceptance or return decision MUST exist independently of whether that
Blueprint-owned metadata has already been committed or pushed.

## 13. Generated reports and command purity

Generated runtime views are not canonical authority.

A check command SHOULD:

1. compute results in memory or a temporary location;
2. compare computed results with canonical expectations;
3. return a status;
4. leave tracked files unchanged.

Where persistent report generation is useful, use separate explicit commands:

```text
check
report-generate
report-update
```

Recommended semantics:

- `check`: read-only validation;
- `report-generate`: explicitly create ignored runtime output;
- `report-update`: explicitly update a tracked canonical report, only where
  a tracked report is justified.

Legacy commands such as `check-report` MAY exist during migration, but a
file-writing command containing `check` MUST NOT remain a canonical target
name in the final architecture.

## 14. Transitional compatibility

Current repositories may temporarily use central Blueprint tools or legacy
targets while migration is in progress.

A transitional adapter MUST:

- be documented as transitional;
- preserve repository write boundaries;
- fail clearly if the authoritative validator is unavailable;
- avoid reporting a weak fallback as equivalent to the target validator;
- report weak fallback execution as `DEGRADED` and block target-conformance claims;
- have an identified replacement step.

Known transitional pattern:

- a module `coordination-check` may currently call a Blueprint checker and
  fall back to a weaker module-local YAML check.

Target state:

- each module owns its coordination validator;
- Blueprint owns its independent intake validator;
- neither repository executes the other repository's mutation tools.

## 15. Reference implementation deviations to remove

The currently selected reference-pilot implementation requires migration where:

- `completion-packet-check` invokes validate, apply, and apply again;
- idempotency is tested by mutating the live module state twice;
- `coordination-check` may depend on a Blueprint executable;
- high-level validation may generate or clean reports;
- completion and publication responsibilities are not fully separated.

These are migration findings, not the target standard.

The selected pilot is an evidence source only. Selecting a pilot does not
limit this architecture to that repository or to any fixed set of modules.

No pilot-module mutation is authorized by this document.

## 16. Migration sequence

The controlled migration order is:

1. approve this command architecture;
2. create a machine-readable command adoption matrix;
3. add validators for naming, read/write classification, and ownership;
4. implement Blueprint `completion-intake-check`;
5. issue a reference-pilot-owned prompt to make `completion-packet-check` read-only;
6. add the reference pilot `completion-packet-preview`;
7. add sandboxed `completion-packet-idempotency-check`;
8. replace transitional central coordination validation with a module-owned validator;
9. validate the selected pilot as the reference implementation;
10. update the canonical module Make template;
11. assess all remaining registered or onboarding modules in controlled batches;
12. release module-specific migration prompts only after Blueprint gates permit rollout.

Steps may be split into smaller commits, but their dependency order MUST be
preserved.

## 17. Approval and implementation gates

### 17.1 Document approval criteria

This architecture may be approved when all of the following are true:

- every command has one unambiguous semantic class;
- read-only and mutating commands are clearly separated;
- every mutating command states its repository boundary;
- module completion and Blueprint acceptance are separate;
- module finish, publication, Blueprint review, and Git publication are distinct;
- completion packet pre-publication and post-publication evidence are defined;
- idempotency is tested outside the live worktree;
- the migration dependency order is explicit;
- external rollout remains gated.

### 17.2 Migration completion criteria

Implementation migration is complete only when all of the following are true:

- commands named check, validate, preview, status, show, or list are read-only;
- `module-finish` performs no commit or push;
- `module-publish` performs no merge;
- Blueprint intake uses a Blueprint-owned independent validator;
- modules use module-owned execution and validation scripts;
- tracked reports contain no absolute checkout paths;
- fresh worktrees pass validation without pre-generated ignored reports;
- the canonical module Make template matches the approved architecture;
- the selected reference pilot passes the approved conformance checks;
- every rollout-eligible registered module has a tracked migration assessment;
- Blueprint operational readiness is GREEN before external rollout.

## 18. Non-goals

This version does not:

- implement the Make targets;
- modify module Makefiles;
- modify the canonical module Make template;
- accept or merge module implementation work;
- release migration prompts to unassessed or ineligible modules;
- remove historical compatibility tools;
- authorize cross-repository writes.

## 19. Decision record

The architecture chooses explicit command semantics over compatibility with
ambiguous legacy behavior.

In particular:

```text
completion-packet-check
```

is defined as read-only, even where current implementations mutate state.

Implementations MUST migrate toward the standard. The standard MUST NOT be
weakened to preserve an incorrectly named mutating command.
