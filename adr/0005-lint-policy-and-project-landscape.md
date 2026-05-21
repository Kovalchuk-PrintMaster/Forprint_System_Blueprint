# ADR 0005: Lint policy and current project landscape

## Status

Accepted.

## Context

`make check` initially failed on Ruff `E501 Line too long` in generated/documentation-heavy scripts. These lines were not logic errors. Most of them were long type signatures, long Markdown-generation strings, or Ukrainian architectural guidance embedded in generated module guides.

The current server also already contains several ForPrint project directories, but their real maturity differs: some are active services, some are empty placeholders, and some are external support tools.

## Decision

1. Ignore Ruff `E501` for this repository.
2. Keep `line-length = 100` as a soft formatting target.
3. Add Black as an optional formatter for code that Black can safely format.
4. Track the current filesystem/project landscape in:
   - `machine/project_directories.yaml`
   - `human/project_landscape.md`
   - `diagrams/project_landscape.mmd`

## Consequences

- Long documentation strings no longer block `make check`.
- Real syntax and logic checks still remain active through Ruff, pytest, validation scripts, and generation scripts.
- The Blueprint can now distinguish between:
  - a module that exists architecturally;
  - a directory that exists physically;
  - a module that is actually active in development.
