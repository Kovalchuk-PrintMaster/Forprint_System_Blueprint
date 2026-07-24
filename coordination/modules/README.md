# ForPrint Module Workflow Control

This directory is the Blueprint-owned control view for repeatable workflows.

It is module-scoped:

```text
coordination/modules/<module_id>/
```

The folder does not contain application implementation from another module.
It contains only Blueprint-side workflow definitions, manifests, external-input
contracts, reporting expectations and synchronization logic.

Shared workflow schemas and templates live under:

```text
coordination/modules/_shared/
```

The first active control profile is:

```text
forprint_system_blueprint
```

Other module folders are created only when a real control workflow exists.

## Boundaries

```text
coordination/modules/<module_id>/
    Blueprint control view

module repository
    actual module implementation
```

Cross-repository writes are forbidden by default.

## Runtime paths

Generated current reports:

```text
reports/modules/<module_id>/current/
```

External operator or assistant input:

```text
operator_input/<module_id>/
```

Temporary analysis workspace:

```text
tmp/module_workflows/<module_id>/<run_id>/
```

Runtime input and temporary work are not canonical repository truth.
