# Module Workflow Automation and External Input Policy

Status: active standard v0.1
Adoption mode: gradual alignment
Owner: ForPrint System Blueprint

## Purpose

Repeatable Blueprint and module-control work must progressively become
discoverable, reusable and executable through canonical scripts and Make
targets.

The standard also defines a minimal safe handshake when a workflow needs
structured analysis or information that cannot be produced locally.

## Module-scoped structure

Workflow control is grouped by module id:

```text
coordination/modules/<module_id>/
scripts/coordination/modules/<module_id>/
tests/coordination/modules/<module_id>/
reports/modules/<module_id>/
operator_input/<module_id>/
tmp/module_workflows/<module_id>/
```

Reusable implementation belongs under `_shared`.

Blueprint control folders for another module must not contain that module's
application implementation.

## Automation rule

A repeatable workflow should have:

1. a stable workflow id;
2. a manifest or registry entry;
3. a canonical script entrypoint;
4. a canonical Make target;
5. declared inputs and outputs;
6. declared side effects;
7. compact terminal reporting;
8. a detailed file-first report;
9. tests;
10. recovery documentation.

A new raw shell sequence should not become the normal operating procedure when
the same operation can be safely represented by a reusable script and Make
target.

## Reuse-first rule

Before creating a script, inspect existing:

```text
scripts/coordination/
scripts/reporting/
tools/
Makefile
coordination/templates/
```

Shared parsing, rendering, artifact writing and validation must be reused where
practical.

Module-specific scripts should contain only module-specific collection,
translation or orchestration logic.

## Make synchronization rule

When a standard workflow target is introduced or changed:

```text
repository Makefile
module Makefile template
workflow documentation
tests
runbook
recovery guide
```

must be reviewed in the same change.

A repository may expose a convenient module-specific alias, but the generic
module target remains canonical.

## External-input handshake

A workflow may pause for external analysis or operator-provided information.

The live input file must use one exact documented path:

```text
operator_input/<module_id>/<short_name>.yaml
```

The filename should be short and memorable. The terminal instruction must be
meaningful and must state:

- current module;
- workflow;
- completed stage;
- exact expected file;
- exact source bundle;
- required response content;
- resume command;
- validation expectations.

The script must generate the expected YAML structure. The operator should not
have to invent keys or layout.

Initial validation may remain intentionally small:

```text
file exists;
YAML parses;
schema version matches;
module id matches;
workflow id matches;
request id matches;
status is provided;
required analysis fields are populated.
```

The script must not silently accept a different file or guess missing keys.

## Reporting contract

Every workflow exposes two report modes.

Compact terminal report:

- one boxed table;
- normally no more than 15 metrics;
- explicit state and note;
- semantic colors only;
- no full raw diagnostics.

Detailed report:

- file-first;
- unrestricted practical size;
- machine-readable data plus human-readable analysis;
- evidence, unknowns, conflicts and recovery paths;
- stable artifact paths printed in the terminal.

## Knowledge-depth model

Self-knowledge coverage uses these levels:

```text
0 unknown
1 indexed
2 purpose understood
3 dependencies and side effects mapped
4 tests, consumers and recovery verified
5 included in a documented automated workflow
```

A low coverage percentage is not a failure by itself. It is a visible planning
signal.

## Safety

External analysis is advisory until a workflow applies it through explicit
validated logic.

No workflow may:

- write to another module repository by default;
- commit or push automatically;
- stage broad unrelated paths;
- overwrite unconsumed operator input;
- treat an expected waiting state as successful completion;
- hide an unknown by converting it to a guessed value.
