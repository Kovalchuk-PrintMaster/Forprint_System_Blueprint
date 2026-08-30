# Repository Structure Minimal Adoption Profile

## Status

Advisory minimal profile / reference only.

## Canonical structure standard

The canonical ForPrint project/repository structure standard is:

`coordination/standards/project_structure_standard.md`

This file is intentionally narrower. It exists only as a compact adoption profile for
young modules and for first-pass repository alignment checks. It must not independently
redefine directory semantics already owned by the canonical standard.

If this profile conflicts with `project_structure_standard.md`, the canonical standard
wins.

## Minimal young-module profile

A young ForPrint module should normally start with:

```text
.
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

The deeper meaning and recommended internal layout of these directories is defined by
`project_structure_standard.md`.

## Minimal coordination profile

An active module should gradually provide a readable coordination surface such as:

```text
coordination/
├── README.md
├── blueprint_source.yaml
├── blueprint_awareness/
├── prompts/
├── reports/
├── roadmaps/
└── status/
```

Exact depth may vary by module maturity. Missing optional structure is alignment work,
not permission for destructive restructuring.

## Adoption rule

For existing modules:

1. inspect the current repository;
2. compare it with the canonical structure standard;
3. preserve working code and valid module-specific structure;
4. make only small, tested, reversible moves;
5. use this profile only as a compact checklist;
6. use `project_structure_standard.md` for semantic decisions.

Large tree moves require an explicit Blueprint-approved migration.
