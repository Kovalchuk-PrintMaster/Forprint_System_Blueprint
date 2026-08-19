# Coordination Metadata Policy

## Status

Active target standard

## Purpose

ForPrint modules maintain coordination metadata in YAML and Markdown files.

These files are important for ecosystem-level coordination, but manual editing can easily create duplicates, stale values, broken links and inconsistent status reports.

This policy defines the first validation/fix approach.

## Source of truth

Machine-readable coordination metadata lives in:

```text
coordination/status/current_status.yaml
coordination/prompts/index.yaml
coordination/reports/index.yaml
```

Human-readable explanations live in:

```text
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
coordination/reports/completion/*.md
coordination/prompts/received/*.md
```
## Main rule

Coordination YAML files should be checked before commit.

Manual edits are allowed, but they must be validated.

## Required checks

The validator should detect:

missing required coordination files;
invalid YAML;
duplicated prompt_id values;
duplicated report_id values;
broken prompt file references;
broken report file references;
invalid priority values;
pending commit/push placeholders;
missing required current_status.yaml keys;
inconsistent completed reports.
## Fix policy

The fixer may safely:

remove exact duplicate YAML entries;
sort or normalize simple metadata where safe;
normalize priority aliases if explicitly supported;
rewrite YAML in a stable format.

The fixer must not:

invent missing report meaning;
guess business status;
guess check results;
overwrite conflicting duplicate entries with different content;
silently delete non-identical records;
create fake commit hashes;
claim push success without evidence.
## Recommended commands

Each module should eventually support:

make coordination-check
make coordination-fix

In the first stage these commands may call the central Blueprint tool.

## Central tool location

The first implementation lives in ForPrint System Blueprint:

tools/forprint_coordination_tools/
scripts/check_coordination_metadata.py
scripts/fix_coordination_metadata.py

Future extraction to a separate ForPrint Dev Tools repository may be considered after the tool is stable across multiple modules.

## Current adoption mode

This is a guardrail tool.

It does not replace architectural review.

It helps catch simple metadata mistakes early.


---

## Post-commit finalization

The fixer may update commit metadata only when explicitly requested.

Allowed command pattern:

```text
scripts/fix_coordination_metadata.py --module-root <module> --update-git-commit
```

The fixer may mark reports as pushed only when explicitly requested and only when Git confirms that local HEAD is not ahead of upstream.

Allowed command pattern:

```text
scripts/fix_coordination_metadata.py --module-root <module> --update-git-commit --mark-pushed-if-upstream-clean
```

The fixer must not claim that a report is pushed without checking Git upstream state.


---

## Immutable governance metadata correction evidence

Blueprint-owned immutable governance records must not be rewritten merely to
repair ownership metadata discovered after sealing.

A correction may instead use
`schema_version: blueprint_governance_metadata_correction_v0_1`.

It is valid only when `metadata.module_id` and `metadata.owner` both equal
`forprint_system_blueprint`, the correction is immutable, the target stays
inside the Blueprint governance directory, the target is an immutable decision
record, path and SHA256 match exactly, the observed value
matches the sealed bytes, the corrected value is canonical, and at most one
effective correction exists for a target-field pair.

The correction changes only the effective metadata projection used by
validation. It does not rewrite the historical target or alter the underlying
operator decision/authorization semantics. Invalid or stale correction evidence
must not suppress the original validation issue.
