# Current ForPrint Execution Focus

## Status

Active global policy

## Current priority model

## P0

### 1. System Blueprint coordination foundation

Keep System Blueprint as the current governance and coordination center.

Control Plane is planned but deferred.

### 2. Calculator Engine

Calculator Engine is the first module used to validate the full coordination loop.

Calculator remains a P0 module.

Current direction:

```text
CalculationOutputPackage;
Quote / CommercialOffer;
OrderDraft / OrderCreationDraft;
price_breakdown;
material_consumption_estimate;
production_method_plan;
accounting line drafts;
prepress requirements;
manual/custom operation drafts.
```
3. Module coordination loop

Each active module must eventually maintain:

coordination/status/current_status.yaml;
coordination/prompts/index.yaml;
coordination/reports/index.yaml;
completion reports;
questions for Blueprint.
P1
Operational Registry

Next planned direction:

Core ForPrint Data Model Expansion

Expected future focus:

ClientAccount;
ClientGroup;
ContactPerson;
ContactMethod;
ChannelIdentity;
Relationship;
CustomerRequest lifecycle;
Order lifecycle;
1C-aware references;
logistics addresses;
manual decision records.
Library

Next planned direction:

Canonical Product/Service ID and Alias Governance

Expected future focus:

canonical IDs;
aliases;
semantic definition requests;
draft/review/approved lifecycle;
module ambiguity routing.
Telegram Bot

Next planned direction:

Channel-agnostic customer request and Calculator handoff

Telegram must remain a channel adapter.

Selective / waiting
Accounting Registry

Current status:

sandbox_1c_import_export_ready

Next deeper v0.6 requires real sanitized 1C export samples.

Do not proceed to live 1C write or production sync.

Hold / planned
Integration Gateway

Hold until real runtime handoff is needed.

Control Plane

Planned high priority, deferred until core modules are alive.

Legacy file parser

Low-priority fallback.

Future core workflow should come from Calculator-generated packages.


---

<!-- forprint-execution-workspace-compatibility-v0-1 -->
## v0.4.1 execution-workspace interpretation

Current B1 work uses the following interpretation:

- Blueprint global cleanliness is not a readiness condition by itself.
- Readiness is determined from release authority, prompt/contract binding, declared required inputs, compatibility classification, and preflight evidence.
- Unrelated Blueprint development may coexist with queued or active module work.
- The current shared module execution lane remains clean/attributable before CLAIM; a busy lane keeps later work queued.
- Stable execution identity after CLAIM prevents `HEAD` chasing.
- Future same-module parallel execution requires isolated execution workspaces; it is not authorized by simply relaxing the module dirty-worktree blocker.
- Tool-specific clean-worktree requirements may remain temporarily where a mutation tool has not yet implemented exact dirty-scope preservation; such a tooling constraint is not an ecosystem compatibility rule.

This clarification changes no B1 acceptance state and authorizes no autonomous execution by itself.

<!-- b1-logistics-reference-validation-current-focus-v0-1 -->
## v0.4.1 current B1 checkpoint — 2026-08-24

B1 implementation and Logistics reference validation are complete.

Current durable exit marker:

`B1_LOGISTICS_REFERENCE_VALIDATION_PASS`

The next legally eligible transition is explicit `B1-ACCEPT` review / seal /
publication.

This checkpoint does not ACCEPT or close B1, does not activate B2, does not
release a business prompt, and does not authorize autonomous execution.

<!-- b1-explicit-acceptance-current-focus-v0-1 -->
## v0.4.1 B1 acceptance checkpoint — 2026-08-24

Operator decision: `ACCEPT B1`.

B1 has passed implementation, Logistics reference validation and final
acceptance-readiness review.

This transaction creates the local B1 acceptance/seal. It does not activate B2.
After separate publication of the exact seal commit, the next transition is
`B2-ACTIVATE`.
