# ForPrint Directive Channels

## Purpose

This directory stores outbound coordination directives from ForPrint System Blueprint to ForPrint modules.

It complements module status reporting.

Direction of information flow:

```text
module repositories
→ coordination/status + reports
→ Blueprint collector

and:

Blueprint directives
→ global/module-specific instructions
→ module assistants apply them in their repositories
```
## Directive types

There are two directive types.

### Global directives

Stored under:

coordination/directives/global/

Global directives apply to all active modules.

Examples:

apply module coordination standard
update common Makefile conventions
follow new naming policy
adopt new status reporting fields
respect new global architecture decision
### Module-specific directives

Stored under:

coordination/directives/modules/<module_id>/

Module-specific directives apply only to one module.

Examples:

calculator_engine should prioritize CalculationOutputPackage
forprint_library should prepare canonical product/service ID governance
forprint_operational_registry should prepare core data model expansion
## Directory structure
```text
coordination/directives/
├── README.md
├── global/
│   ├── index.yaml
│   ├── planned/
│   ├── active/
│   └── archive/
└── modules/
    └── <module_id>/
        ├── index.yaml
        ├── planned/
        ├── active/
        └── archive/
```
## Directive ID format

Recommended directive ID format:

YYYY-MM-DD__scope__directive__short-slug__vN

Examples:

2026-06-02__global__directive__module-coordination-standard-v1
2026-06-02__calculator_engine__directive__coordination-pull-and-calculator-focus-v1
## Directive statuses

Allowed statuses:

active
planned
superseded
archived
cancelled

A planned directive is documented but not released. It must remain under
`planned/`, must not require module acknowledgement and must record that a
separate activation decision is required. Activation moves the file to
`active/` and updates the index in one bounded governance change.
## Module assistant rule

Every module assistant should check:

coordination/directives/global/index.yaml
coordination/directives/modules/<module_id>/index.yaml

before starting a new macro pack or after pulling Blueprint updates.

In the first stage this is manual.

Future automation may pull Blueprint, read directive indexes and notify modules about new directives.

## Safety

Directives must not contain:

secrets
tokens
passwords
private client data
real accounting data
real 1C production data
personal data
large logs
binary files

Only safe strategic, coordination and implementation instructions are allowed.


---

## Module self-check rule

Each module assistant should periodically pull ForPrint System Blueprint and check whether new directives appeared.

The module assistant should check:

```text
coordination/directives/global/index.yaml
coordination/directives/modules/<module_id>/index.yaml
```

If a new active directive applies to the module, the module assistant should read the referenced directive file and decide whether it can be applied immediately or whether it requires a question to Blueprint.

The module must record acknowledgement, progress or questions in its own coordination files.
