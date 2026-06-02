# Repository Structure Baseline

## Status

Target standard

## Purpose

This document defines the preferred baseline structure for ForPrint module repositories.

It is a target direction, not a command to immediately rewrite every existing project.

## Preferred baseline

```text
.
├── app/
├── config/
├── coordination/
├── docs/
├── reports/
├── scripts/
├── tests/
├── Makefile
├── README.md
├── pyproject.toml
└── forprint_module_manifest.yaml
Required coordination structure
coordination/
├── status/
│   ├── current_status.yaml
│   ├── current_status.md
│   └── next_questions_for_blueprint.md
│
├── prompts/
│   ├── received/
│   └── index.yaml
│
├── reports/
│   ├── completion/
│   ├── commits/
│   └── index.yaml
│
└── README.md
Common directory roles
app/

Main source code.

config/

Configuration files.

Important rule:

paths, thresholds, repo URLs, timing rules and runtime options should live in config where practical.
coordination/

Live coordination status, prompts, reports and questions.

docs/

Stable architecture and development documentation.

reports/

Generated check reports and module status exports.

scripts/

Developer/admin/check/report scripts.

tests/

Automated tests.

Gradual alignment

Existing modules may differ.

Alignment should happen in small tested steps.

Do not break working modules only to match structure.


---
