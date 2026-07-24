# Blueprint Internal Workflow Foundation Architecture

## Purpose

The foundation turns repeatable Blueprint operations into module-scoped,
discoverable workflows while keeping Blueprint available as one profile among
future controlled modules.

## Layers

```text
coordination/modules/
    workflow definitions, manifests and control contracts

scripts/coordination/modules/
    reusable engine and module-specific workflow code

tests/coordination/modules/
    shared and module-specific tests

reports/modules/
    generated compact and detailed reports

operator_input/
    exact live external-input files

tmp/module_workflows/
    temporary analysis bundles and run state
```

## Initial workflow

```text
Blueprint Self Audit
```

The local phase scans repository evidence and builds reports. It then pauses for
one exact YAML file:

```text
operator_input/forprint_system_blueprint/bsa.yaml
```

The terminal prints the full workflow name, completed stage, bundle path,
expected response and resume command.

## Reporting

Compact output reuses the shared Blueprint boxed-table renderer.

Detailed evidence is written to files. Routine terminal output does not dump
the complete scan.

## Boundaries

- no network calls;
- no cross-repository writes;
- no automatic Git staging;
- no automatic commit or push;
- no silent external-input substitution;
- no automatic dead-code claims.

## Growth path

Future module profiles reuse `_shared` collection and reporting infrastructure.
They add only module-specific source adapters, control workflows and manifests.
