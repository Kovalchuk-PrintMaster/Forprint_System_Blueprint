# Roadmap Enrichment Living Field Guide v0.1

## 1. Purpose

This file is durable, accumulating process knowledge for Blueprint roadmap
enrichment.

It exists so that a later assistant does not have to rediscover the same
repository navigation, source-role distinctions, fast paths, and failure modes.

This file is **not** a roadmap authority, release authority, work authority,
activation authority, or substitute for canonical project artifacts.

Stable methodology remains in:

`coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md`

Machine-readable navigation is in:

`coordination/repository_knowledge/roadmap_enrichment/source_map.yaml`


## 1.1. Current workstream continuity — temporary parallel-assistant convention

As of 2026-09-21, two independent assistant workstreams may operate in this
repository at the same time:

1. **CF-10 / Internal Worker Engineering**
   - bounded internal Blueprint AI worker implementation;
   - runtime, Dispatcher, Handoff v2, validation, recovery, worker tooling,
     and related Blueprint self-hardening;
   - it does not own global portfolio planning.

2. **Roadmap Enrichment / Portfolio Knowledge Saturation**
   - portfolio-wide knowledge recovery and enrichment;
   - deep module audits and current-state reconstruction;
   - mature target states and capability coverage;
   - Human Intent and conversation evidence;
   - roadmap enrichment and strategic objectives;
   - cross-module dependency discovery;
   - preparation of high-quality knowledge for later automatic planning.

This is a temporary coordination convention, not a new execution-authority,
locking, or multi-worker framework.

Each assistant stays inside its assigned workstream and current task boundary.
Incidental cleanup of another workstream is not permitted.

If a task requires mutation of a shared surface or a surface clearly belonging
to the other active workstream, prepare a short operator-mediated
cross-workstream notice **before mutation** containing:

- affected file or surface;
- reason for the change;
- expected mutation;
- possible collision risk.

The operator may relay that notice to the other assistant. Silence does not
grant write authority. Existing canonical authority, lifecycle, Git
reconciliation, and governance remain unchanged.

### Current enrichment focus

The current enrichment milestone is:

`Portfolio Knowledge Baseline v0.1`

Its purpose is to establish portfolio-wide coverage before global sequencing or
roadmap reformatting.

A source should normally be analyzed once for the **whole portfolio**, not once
per module. During one pass, extract all relevant module implications,
capabilities, target-state evidence, roadmap candidates, dependencies,
strategic implications, provenance, and unresolved questions.

Durable mutation may still be reconciled in bounded owner-specific changes even
when analysis is portfolio-wide.

## 2. Update rule

Update this guide only when a session discovers a **verified, reusable lesson**.

Do not update it merely because a session occurred.

Do not paste raw chat, raw terminal logs, or complete temporary audit reports
into this file.

Every durable lesson should preserve:

- what was learned;
- why it is reusable;
- source or evidence;
- scope;
- authority level;
- caveat or staleness condition;
- recommended sequence or fast path;
- last verified Git commit;
- superseded or conflicting guidance where applicable.

## 3. Starting sequence for roadmap enrichment

Recommended sequence:

1. Verify repository identity, branch, HEAD, upstream, staged state, dirty state,
   and untracked state.
2. Read `coordination/instruction_intake/assistant_reading_order.md`.
3. Read `coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_2.yaml`.
4. Reconcile `coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml` against current Git state.
5. Verify current release / authority before interpreting roadmap state.
6. Read `coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md`.
7. Read this field guide and `coordination/repository_knowledge/roadmap_enrichment/source_map.yaml`.
8. Locate the existing canonical owner before proposing a new artifact.
9. Classify the intended disposition as `REUSE / EXTEND / ADAPT / REPLACE / NEW`.
10. Enrich coverage first; do not force perfect ordering while knowledge is still
    incomplete.
11. Rebuild only derived surfaces that are deterministically stale.
12. Validate source semantics before publication.

## 4. Source-role quick map

Use Git-tracked canonical source artifacts for durable meaning.

Use current handoff and continuity artifacts for navigation and recovery, not
as independent execution authority.

Use generated indexes as rebuildable discovery aids. Do not treat an index as
the original semantic owner.

Use internal-work reports and audit packets as evidence. Promote reusable
conclusions into durable canonical or living-knowledge surfaces only after
validation.

Use `tmp/` only for diagnostics and isolated candidates.

## 5. High-value fast paths

### 5.1 Before reading a dirty canonical target

Classify it first:

- `CLEAN_TRACKED`
- `DIRTY_TRACKED`
- `WORKTREE_ONLY_UNTRACKED`
- `ABSENT`

If the intended canonical target is dirty or worktree-only, do not blindly
edit it in place.

Preferred sequence:

`published baseline -> isolated clean candidate -> validate -> exact delta -> controlled integration`

### 5.2 Separate authored source from derived surfaces

Before rebuilding anything, identify:

- authored source files;
- generated knowledge indexes;
- specialized indexes;
- continuity projections;
- reports / evidence;
- temporary diagnostics.

A generated representation becoming stale does not make it an authority.

### 5.3 Registration

Do not copy historical registration shape blindly.

Use the **current validator and current policy** to determine whether a new
artifact requires registration and which index owns that registration.

Historical Bootstrap v0.1 registration is not a template for new artifacts.

### 5.4 Knowledge-index rebuild

Never publish knowledge-index blobs rebuilt against a broad dirty worktree
unless that dirty state is intentionally part of the publication.

For a bounded publication, rebuild derived indexes from the isolated clean
publication candidate.

### 5.5 Unresolved reference failures

If semantic validation reports unresolved current reference candidates:

1. inspect the exact source artifact;
2. compare against the published baseline;
3. determine whether the reference is real, stale, unpublished, or accidental
   path-like prose;
4. fix the authored source;
5. rebuild derived indexes;
6. never manually edit the derived review-candidate output to hide the issue.

### 5.6 Exact publication from a dirty repository

For a bounded publication where the main worktree contains unrelated changes,
prefer an isolated clean candidate and temporary Git index.

Useful pattern:

`clean candidate -> exact blobs -> temporary index -> write-tree -> commit-tree -> guarded push`

Do not use `git add .`.

### 5.7 Local convergence after isolated publication

Publishing an exact commit remotely does not imply the dirty local worktree
should be overwritten.

Audit the relationship between:

- old HEAD;
- new published HEAD;
- real index;
- current worktree bytes.

A mixed-reset-style baseline move can preserve worktree bytes when explicitly
validated first.

## 6. Known pitfalls

### Pitfall: chat or handoff treated as execution authority

A roadmap item, chat instruction, navigation artifact, or handoff snapshot does
not automatically authorize implementation or activation.

### Pitfall: temporary path becomes canonical by convenience

A temporary candidate that validates is still temporary until a bounded
integration transaction publishes it.

### Pitfall: derived index built from unrelated dirty state

This can accidentally encode unpublished unrelated work into a seemingly clean
publication.

### Pitfall: stale path reference

A document may reference a path visible in a dirty worktree but absent from the
published repository. Always verify references against the publication
baseline.

### Pitfall: accidental path-like prose

Text such as `coordination/...` can be interpreted by semantic tooling as a
repository reference. Use natural prose when no path reference is intended.

### Pitfall: historical process copied as current policy

Old snapshots, historical registration patterns, and previous workstream
procedures are evidence, not automatic current policy.

## 7. Durable lessons seeded from the 2026-09-20 enrichment work

### Lesson FP-RE-001 — coverage before perfect order

During Portfolio Knowledge Saturation, capture useful architectural knowledge
with provenance and approximate placement before attempting perfect sequence.

Evidence:
`coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md`

Last verified commit:
`a4399af4035a6c3fcb29d4001d4445e63a6b1dc9`

### Lesson FP-RE-002 — roadmap presence is not execution authority

Keep planning, implementation readiness, binding, and activation as separate
states.

Evidence:
`coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md`

Last verified commit:
`a4399af4035a6c3fcb29d4001d4445e63a6b1dc9`

### Lesson FP-RE-003 — reuse-first canonicalization

Before creating a new framework, inspect existing owners and assign:

`REUSE / EXTEND / ADAPT / REPLACE / NEW`

`NEW` requires rationale.

Evidence:
`coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md`

Last verified commit:
`a4399af4035a6c3fcb29d4001d4445e63a6b1dc9`

### Lesson FP-RE-004 — clean-candidate workflow protects dirty work

When canonical targets or derived indexes are already dirty, isolate the
publication candidate from the dirty worktree before validation and publication.

Evidence:
2026-09-20 Blueprint roadmap-enrichment publication sequence.

Last verified commit:
`a4399af4035a6c3fcb29d4001d4445e63a6b1dc9`

### Lesson FP-RE-005 — fix unresolved references at the source

Semantic unresolved-reference output is a diagnostic projection. Repair the
authored source and regenerate the projection.

Evidence:
2026-09-20 roadmap-enrichment operating-guide publication validation.

Last verified commit:
`a4399af4035a6c3fcb29d4001d4445e63a6b1dc9`

### Lesson FP-RE-006 — publication and local convergence are separate

A commit can be created and published from an isolated exact tree while the
main dirty worktree remains byte-preserved. Local branch/index convergence can
then be performed as a separately audited transaction.

Evidence:
2026-09-20 Blueprint publication boundary closure.

Last verified commit:
`a4399af4035a6c3fcb29d4001d4445e63a6b1dc9`

### Lesson FP-RE-007 — inspect command side effects before audit execution

A command, Make target, or validator can have a read-oriented name such as
`check` or `status` while still writing reports or temporary output.

Before using an unfamiliar command inside a preservation-sensitive audit:

1. inspect the Make recipe or command implementation;
2. identify explicit output paths;
3. identify inherited environment or Make variables;
4. decide whether those writes are allowed;
5. prefer a disposable isolated sandbox when output generation is intentional.

A concrete failure mode is an inherited module variable changing the semantic
target of a reconciliation report while the command also overwrites that
report.

Evidence:
2026-09-20 Bootstrap v0.2 candidate impact audit.

Known caveat:
Output-producing checks are not prohibited. Their mutation must simply be
declared, scoped, and contained instead of being assumed read-only.

Last verified baseline commit:
`a4399af4035a6c3fcb29d4001d4445e63a6b1dc9`

### Lesson FP-RE-008 — isolated validation may require a temporary toolchain bridge

A clean isolated Git clone intentionally does not contain the local
`.venv_blueprint` environment, but repository tests may resolve the Python
interpreter relative to their own repository root.

When a validator or test requires `repo/.venv_blueprint/bin/python`:

1. keep the canonical environment outside the publication candidate;
2. create a temporary sandbox-local symlink to the canonical environment;
3. keep the bridge alive for the complete validator or pytest subprocess;
4. remove it in `finally`;
5. verify that the symlink was removed;
6. never include the bridge in Git or publication content.

This is runtime validation plumbing only, not repository content.

Evidence:
2026-09-20 Bootstrap v0.2 publication-candidate validation.

Last verified baseline commit:
`a4399af4035a6c3fcb29d4001d4445e63a6b1dc9`

## 8. When to enrich this guide

Add or correct an entry when at least one of these is true:

- a faster repeatable discovery sequence was proven;
- a misleading or stale surface caused avoidable work;
- an authority/source-role distinction was clarified;
- a recurring validation failure received a reusable diagnosis;
- a cross-module ownership shortcut was verified;
- an existing lesson became stale or was superseded.

Do not add speculative advice.

## 9. Relationship to current handoff

`coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml` answers:

**What was the latest observed coordination state?**

This field guide answers:

**What reusable knowledge makes roadmap enrichment faster and safer?**

They must not be merged into one artifact.

## 10. Relationship to repository knowledge

This living pack is part of repository knowledge because it stores reusable
project self-knowledge.

It remains subject to:

- `coordination/repository_knowledge/repository_knowledge_and_direction_snapshot_protocol_v0_3.md`
- `coordination/repository_knowledge/artifact_authority_policy_v0_1.yaml`
- `coordination/repository_knowledge/inventory_maintenance_v0_1.yaml`

It does not create a second authority layer.


### Lesson FP-RE-009 — reconcile implementation reality and roadmap before novelty

Dirty repository state is context, not an automatic stop condition. Before a
significant new implementation is created, inspect both repository reality and
planning reality: current implementation/inventory, the owning module roadmap,
Human Intent, target/capability surfaces, dependencies and relevant portfolio
plans. Assign `REUSE / EXTEND / ADAPT / REPLACE / NEW` before code creation.

If the capability is already represented, enrich or reconcile the existing
owner/roadmap item instead of creating duplicate functionality. `NEW` requires
search evidence; `REPLACE` requires migration/supersession semantics.

The search scope is proportional to significance: module-local for local work,
relevant portfolio-wide for shared/cross-module architecture.

Evidence:
`coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md`

