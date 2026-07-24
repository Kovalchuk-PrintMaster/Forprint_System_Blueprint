# ForPrint System Blueprint Workflow Control

This folder documents and controls Blueprint's own repeatable operating
workflows.

The initial workflow is:

```text
blueprint_self_audit
```

It scans current repository evidence, calculates self-knowledge coverage,
writes compact and detailed reports, builds one analysis bundle and pauses for
the exact external-input file:

```text
operator_input/forprint_system_blueprint/bsa.yaml
```

`bsa` means `Blueprint Self Audit`.

The short filename is intentional. The terminal output always prints the full
workflow name, current stage, required content and resume command.
