# ForPrint System Blueprint

<!-- FORPRINT_AI_ASSISTANT_ENTRY_START -->
## AI assistant entry

A new AI assistant with no repository context should start with
[`AGENTS.md`](AGENTS.md), which is the canonical onboarding/navigation front door.
<!-- FORPRINT_AI_ASSISTANT_ENTRY_END -->


**ForPrint System Blueprint** is the architecture and coordination control repository for
the ForPrint ecosystem.

It does not execute customer orders, calculate prices or run production workflows. It
defines and validates how modules fit together, which module owns which data, which
contracts/flows exist, and which coordination/release state is effective.

## Authority map

```text
coordination/releases/current.yaml
    effective Blueprint release/work authority

machine/module_identity_registry.yaml
    stable module identifiers

machine/modules.yaml
machine/data_objects.yaml
machine/ownership.yaml
machine/contracts.yaml
machine/data_flows.yaml
machine/system_layers.yaml
    current machine-readable architecture

coordination/standards/
    normative governance and engineering rules

docs/
    stable human explanation

indexes/
    derived non-authoritative navigation
```

## Human architecture entry points

- `docs/architecture/system_architecture.md`
- `docs/architecture/module_boundaries.md`
- `docs/architecture/integration_architecture.md`

Historical early alignment material is preserved under
`coordination/internal_work/blueprint/legacy_alignment/` and is not current authority.

## Quick start

```bash
cd /srv/software_development/forprint-project/forprint_system_blueprint
source .venv_blueprint/bin/activate
make check
```

## Main commands

```bash
make validate
make diagrams
make guides
make test
make check
make check-report
make prompt-queue-validate
make coordination-check
```

## Repository structure

```text
forprint_system_blueprint/
├── machine/        # current machine-readable architecture/control truth
├── docs/           # stable authored human documentation
├── coordination/   # releases, roadmaps, prompts, standards, evidence and workflows
├── indexes/        # derived non-authoritative navigation
├── diagrams/       # generated/manual explanatory Mermaid views
├── module_guides/  # generated module-facing guides
├── adr/            # architecture decision history
├── scripts/        # generators, validators and workflow tooling
├── tests/          # deterministic repository validation
├── reports/        # generated reports/evidence
└── tools/          # reusable support tooling/templates
```

## Module boundary rule

CRM coordinates business workflow and operator views; it is not the physical owner of
all business data.

Current canonical identities include:

- `forprint_operations_control_registry` — operational client/order/task/status truth;
- `forprint_accounting_registry_service` — accounting/invoice/payment/1C contour;
- `forprint_library` — semantic/catalog/reference truth;
- `calculator_engine` — calculation and quote logic.

Exact role/status/ownership remains defined by current `machine/*.yaml`.

## Working with modules

Current prompt release/pull is governed by Prompt Queue v0.2:

`coordination/outgoing_prompts/<module_id>/index.yaml`

Released prompts are execution contracts and are not rewritten by generic structural
cleanup.

Module completion/review progression must follow current coordination standards and the
effective release authority.

## Git safety

Repository tooling may provide explicit mutation commands, but structural or governance
work must not imply commit/push/merge automatically.

Before publication, review:

```bash
make check
git status --short
git diff --check
```

Commit/push remains an explicit operator decision.
