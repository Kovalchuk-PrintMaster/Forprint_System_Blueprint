# ForPrint Module Standards Visibility Template

This directory contains the canonical module-side template for reading Blueprint standards.

Targets:

```bash
make blueprint-standards-list
make blueprint-standards-check
make blueprint-standards-sync
```

Blueprint standards are continuously readable advisory architecture guidance.

They are not automatically equivalent to active prompts.

A module should not perform a large destructive rewrite only because a standard exists.

Modules should read the standards index, confirm advisory semantics, keep a lightweight snapshot, report reviewed standards in completion reports when relevant, and apply standards gradually through small prompts or explicit directives.

Expected module-side paths:

```text
scripts/read_blueprint_standards.py
scripts/check_blueprint_standards.py
scripts/sync_blueprint_standards_snapshot.py
coordination/standards/blueprint_standards_snapshot.yaml
```

Required variables:

```text
PYTHON
BLUEPRINT_DIR
```
