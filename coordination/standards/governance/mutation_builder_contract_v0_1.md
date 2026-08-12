# ForPrint Mutation Builder Contract

## Status

Active standard. Adoption requires an explicit Blueprint prompt or directive.

The machine-readable authority is:

```text
coordination/standards/governance/mutation_builder_contract_v0_1.yaml
```

## Purpose

Mutation builders must behave predictably. They must discover the exact current
repository structure, construct the complete change in memory, validate it
before the first tracked write, modify only declared paths, validate the final
reviewable commit surface including newly created files, and restore the
original clean worktree after any failure.

This contract applies to scripts that modify tracked repository files, create
governance or standards artifacts, or evolve canonical validation contracts.
Read-only inspections and ignored rebuildable runtime reports are outside this
contract.

## Mandatory ten-stage flow

1. `inspect_exact_structure`
2. `render_all_changes_in_memory`
3. `validate_typed_exact_path_set`
4. `reject_no_op_mutations`
5. `parse_and_compile_generated_artifacts`
6. `preserve_existing_file_modes`
7. `perform_bounded_atomic_writes`
8. `run_focused_tests`
9. `run_canonical_gate`
10. `verify_complete_rollback_on_failure`

No tracked write is allowed during stages 1–6.

## Source and path contracts

A mutation builder must require a clean working tree and verify the expected
branch, HEAD, and SHA-256 values of every source contract it patches.

In-memory rendered paths use `pathlib.Path`. Git status paths use normalized
repository-relative strings. The builder must compare typed sets deliberately,
report missing and unexpected paths, and reject existing paths whose rendered
content is unchanged.

## Preflight validation

Before the first tracked write, the builder must:

- render every future file completely in memory;
- parse and compile generated Python;
- reject duplicate YAML keys and validate YAML structure;
- validate Markdown fence balance;
- normalize generated Python with the repository Ruff configuration in an
  ignored `tmp/` preflight tree;
- rerun Ruff in check-only mode before the first tracked write;
- verify the exact rendered path set and immutable boundaries.

## Atomic write contract

Writes are bounded to declared paths and use atomic replacement. Existing file
modes are preserved. New files use mode `0644`. Automatic formatter fixes after
tracked writes are not allowed; formatting must already pass preflight.

## Verification order

Focused tests run before the canonical gate. After verification and after any
generated tracked reports are restored, the builder must confirm the exact
dirty path set and re-check immutable boundary hashes.

The final reviewable mutation surface must then pass the canonical precommit
surface validator:

```text
scripts/validation/validate_mutation_precommit_surface.py
```

The validator must use a temporary `GIT_INDEX_FILE`, seed that temporary index
from `HEAD`, stage only the declared expected mutation paths into the temporary
index, verify that the temporary staged path set exactly matches the declared
dirty path set, and run `git diff --cached --check` against that temporary
index. This requirement exists because plain `git diff --check` does not inspect
new untracked files.

The real Git index must be clean before this validation and must remain
byte-for-byte unchanged afterward. The validator must also prove that it did
not change the working-tree status. A new file with trailing whitespace must
therefore fail the builder before the builder reports success.

A successful builder leaves the declared reviewable changes uncommitted and
unstaged in the real Git index. Commit, push, merge, pilot authorization, and
rollout authorization remain explicit operator or governance decisions.

## Failure and rollback behavior

Any exception or failed command triggers rollback. Rollback restores original
bytes and modes for existing files and removes only the declared new files.

If the internal restore is insufficient, the builder may use a bounded
`git restore --source=HEAD --worktree -- <declared-existing-paths>` fallback
because the clean-worktree precondition proves that those paths had no
pre-existing user changes. Broad reset and broad clean commands are forbidden.

After rollback, the builder must verify a clean working tree. It must report the
failure stage, failed command, and any remaining dirty paths. It must not
automatically retry a partially failed mutation.

## Review checklist

A mutation builder is ready only when all answers are yes:

```text
Was the exact structure inspected?
Were all outputs rendered before the first tracked write?
Were Path and Git-string contracts kept separate?
Were no-op mutations rejected?
Were Python, YAML, Markdown, and lint preflight checks run?
Were existing file modes preserved?
Were writes atomic and bounded?
Did focused tests pass before the canonical gate?
Were generated tracked reports restored before final surface validation?
Did the temporary-index precommit validator cover every declared dirty path?
Did `git diff --cached --check` pass against the temporary Git index?
Did the real Git index remain unchanged and unstaged?
Were immutable boundaries rechecked?
Can every failure restore the original clean worktree?
```

## Safety boundaries

This standard does not authorize a reference pilot, release external prompts,
change the release policy, perform cross-repository writes, or open external
rollout. External rollout remains gated.

## Defect closed by this rule

On `2026-08-12`, the Completion Exchange v0.3 candidate builder passed its
builder-level `git diff --check` while a newly created Markdown standard still
contained trailing whitespace. The later operator-side
`git diff --cached --check` caught the defect after staging. The root cause was
that untracked files are outside the surface inspected by plain
`git diff --check`.

The temporary-index precommit validator is the canonical regression control for
that failure mode. Builders must not replace it with a weaker worktree-only
check.
