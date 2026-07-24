# Module Workflow Reports

Generated module-scoped workflow reports are written under:

```text
reports/modules/<module_id>/current/
reports/modules/<module_id>/history/
```

`current` is the latest operational view. `history` contains accepted run
artifacts when the workflow records them.

Generated files are ignored by default and are not staged automatically.
