# ForPrint Module Project Tree Template

## Purpose

This template shows the preferred starting tree for a ForPrint module.

It is a starting point, not a destructive migration command.

## Minimal young-module tree

```text
<module_root>/
├── app/
├── config/
├── coordination/
├── docs/
├── examples/
├── reports/
├── scripts/
├── tests/
├── Makefile
├── README.md
├── pyproject.toml
└── forprint_module_manifest.yaml
```

## Recommended coordination tree

```text
coordination/
├── README.md
├── blueprint_source.yaml
├── blueprint_awareness/
│   └── document_review_ledger.yaml
├── prompts/
│   ├── index.yaml
│   └── received/
├── reports/
│   ├── index.yaml
│   ├── completion/
│   └── commits/
├── roadmaps/
└── status/
    ├── current_status.yaml
    ├── current_status.md
    └── next_questions_for_blueprint.md
```

## Recommended growing-module tree

```text
<module_root>/
├── app/
│   └── <python_package>/
│       ├── __init__.py
│       ├── domain/
│       ├── services/
│       ├── repositories/
│       ├── schemas/
│       └── adapters/
├── config/
│   ├── README.md
│   ├── defaults.yaml
│   ├── module.yaml
│   ├── environments/
│   ├── adapters/
│   ├── paths/
│   └── schemas/
├── coordination/
├── contracts/
├── docs/
│   ├── architecture/
│   └── development/
├── examples/
├── reports/
├── scripts/
│   ├── coordination/
│   ├── diagnostics/
│   ├── previews/
│   ├── migrations/
│   └── validation/
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   ├── coordination/
│   └── config/
├── Makefile
├── README.md
├── pyproject.toml
└── forprint_module_manifest.yaml
```

## Runtime/local directories

These directories may exist locally and are usually ignored by Git:

```text
data/
logs/
tmp/
```

Do not commit private runtime data, local logs or temporary files.

---
