# Blueprint Outgoing Prompt Workflow Architecture v0.1

## Status

Implementation contract for the Blueprint-owned `prompt-prepare` and
`prompt-release` workflow.

## Goal

Provide one unambiguous, recoverable workflow for preparing and releasing work
to modules without writing to module repositories and without extending the
legacy dispatch model.

## Canonical source of truth

For new prompt workflow automation, the source of truth is:

```text
coordination/outgoing_prompts/<module_id>/index.yaml
```

The index must use:

```yaml
schema_version: prompt_queue_v0_2
```

The legacy file below is validation-only compatibility data and is not mutated
by the new workflow:

```text
machine/prompt_dispatch_index.yaml
```

The `sent/` directory is not a release state for Prompt Queue v0.2.

## Artifact states

A managed prompt uses YAML front matter with:

```yaml
schema_version: outgoing_prompt_artifact_v0_1
lifecycle_state: draft | prepared | released
```

The states mean:

| State | Location | Executable by module |
| --- | --- | --- |
| `draft` | operator-provided source | No |
| `prepared` | `drafts/` | No |
| `released` | `approved/` and indexed | Yes, only when queue status is `ready_for_module_pull` |

A file existing in `approved/` without a matching queue record is invalid.
A queue record existing without its approved file is invalid.

## `prompt-prepare`

Input is one managed Markdown source artifact in state `draft`.

The operation:

1. validates duplicate-free YAML front matter;
2. validates `target_module` against `machine/modules.yaml`;
3. validates prompt identity, phase, priority, date, lineage and body;
4. writes one canonical artifact under `drafts/`;
5. changes only artifact lifecycle state to `prepared`;
6. records the source SHA-256 and preparation timestamp;
7. does not touch the queue index;
8. does not make the prompt visible to modules.

Identical repeated preparation is a no-op. Different content for the same
canonical path fails unless replacement is explicitly requested.

## `prompt-release`

Input is an existing prepared artifact identified by explicit module ID and
prompt ID.

The operation:

1. requires Prompt Queue v0.2;
2. requires explicit release authorization policy and evidence;
3. preserves prompt identity and lineage;
4. assigns the next unique module-local sequence;
5. writes the released artifact under `approved/`;
6. appends exactly one queue record;
7. sets `module_execution.status: ready_for_module_pull`;
8. sets `blueprint_review.status: not_started`;
9. removes the prepared draft only after the approved artifact and index are
   durably written;
10. does not write to the module repository;
11. does not commit, push or merge.

Repeated release is a no-op when the existing approved artifact and queue
record agree. Partial or conflicting state fails closed.

## Release authorization

Release is governed by:

```text
coordination/standards/governance/outgoing_prompt_release_policy_v0_1.yaml
```

Authorization requires either:

- global release enabled, or
- the target module listed as an authorized pilot;

and in both cases a Blueprint-owned authorization evidence file must exist.

The repository starts with release disabled and no authorized modules.

## Transaction and recovery model

A release updates two canonical artifacts: the approved Markdown file and the
queue index. Cross-file atomicity is not available, so the implementation uses:

- sibling temporary files;
- file flush and `fsync`;
- `os.replace`;
- directory `fsync`;
- compensating rollback of approved artifact, queue index and prepared draft.

Any incomplete or conflicting state is not repaired silently. Operators must
follow the recovery runbook.

## Boundaries

The workflow must never:

- write outside the Blueprint repository;
- modify a target module repository;
- mutate `machine/prompt_dispatch_index.yaml`;
- use `sent/` as the release mechanism;
- release an unprepared artifact;
- release while governance policy is gated;
- infer module completion or Blueprint acceptance;
- commit, push or merge.
