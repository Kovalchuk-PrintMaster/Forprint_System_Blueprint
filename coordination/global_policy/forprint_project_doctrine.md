# ForPrint Project Doctrine

## Status

Active global policy

## Core idea

ForPrint is an operational platform for advertising and informational products.

The system must support:

```text
customer intake;
calculation;
structured order formalization;
internal operational registry;
accounting and 1C synchronization;
prepress preparation;
production support;
reporting and analytics;
multi-channel customer communication.
```

ForPrint is not only a print shop tool.

It should be built as an extensible operational platform for advertising/informational products and related services.

Main strategic goal

The goal is to build a coordinated ecosystem where modules work through clear boundaries and shared contracts.

The system must reduce manual duplicate work, especially:

manual order re-entry;
manual 1C data entry;
manual customer history search;
manual repeated report building;
manual cross-module status tracking.
Current governance

Current governance is:

owner / mentor
+
architectural assistant
+
ForPrint System Blueprint

ForPrint Control Plane is planned but deferred.

Control Plane must not be actively implemented until core modules are alive and interconnected.

Core module roles
ForPrint System Blueprint

Owns architecture, module boundaries, execution queue, coordination standards and global project alignment.

Operational Registry

Main physical/internal data custodian of ForPrint.

It owns the internal ForPrint DB foundation and structured data access, but must not become the logical owner of every domain rule.

Library

Canonical semantic/catalog authority.

It owns canonical product/service/material/operation IDs, names, aliases, catalog definitions and semantic registry.

Calculator Engine

Primary formalization point for new order/calculation requests.

It produces structured machine-readable calculation and order draft packages.

Accounting Registry

Accounting and 1C synchronization boundary.

It owns 1C import/export, mapping, staging, reconciliation and accounting workflow adapters.

Telegram Bot / Website / Mobile App

Customer channel adapters.

They must not become business truth owners.

Integration Gateway

Future runtime validation, routing, idempotency and correlation layer.

Gateway remains limited until real runtime handoff is needed.

CRM

Future human dashboard, reporting and workflow coordination layer.

CRM must not become the physical database owner.

Core development principles
1. One ecosystem, many modules

Modules must move in one coordinated direction.

A module should not optimize itself in a way that breaks the overall ecosystem.

2. Stable IDs over names

Names can change.

Stable IDs must be used for canonical references:

ClientAccount ID;
product_id;
service_id;
material_id;
operation_id;
order_id;
request_id;
quote_id.
3. Phone is lookup, not truth

Phone number is a strong lookup/contact key.

Canonical customer identity is ClientAccount ID.

4. Calculator-first order formalization

New orders should primarily pass through Calculator Engine.

Manual and legacy paths are fallback only.

5. Operational Registry keeps internal data

ForPrint DB is the internal data foundation.

Operational Registry is the physical/internal data custodian.

6. Library controls semantics

Modules must not invent permanent product/service/material names independently.

Ambiguity must go to Library.

7. 1C-aware, not 1C-dependent

ForPrint DB must be 1C-aware and sync-friendly.

1C remains important, but it is not the global ForPrint source of truth.

8. Configuration over hardcoding

No important paths, thresholds, repository locations or timing rules should be hardcoded in business logic.

Use config files.

9. Reports and checkups are part of development

Each module must publish coordination status, reports and open questions.

10. Manual override must be visible

Manager/manual adjustments are allowed where needed, but they must be logged and later analyzed.

11. Development-first governance

ForPrint is a young, actively evolving system. Existing policy, protocol,
document or workflow is not authoritative merely because it is older.

When an existing rule blocks a materially better current design, first decide
whether that rule still has an active consumer, migration value or explicit
governance reason. If it does not, evolve the authority deliberately: update
the current document when the concern is continuous, or create the next clear
revision and mark the previous authority deprecated/superseded when semantics
materially change.

Backward compatibility is not a project goal by itself. Architecture must not
be distorted solely to preserve obsolete assumptions.

12. Durable project memory and forward control

Significant completed implementation, architecture and governance decisions
must be recoverable from repository evidence. Chat history is not canonical
project memory.

Roadmaps define intended project movement. Prompt sequencing defines executable
coordination steps. Current work must stay reconciled with both so modules move
at a balanced pace and dependent work is not advanced prematurely.

Current strategic direction

Near-term project direction:

1. Stabilize Blueprint coordination.
2. Apply module coordination standard.
3. Use Calculator as first active module in the full coordination loop.
4. Move Calculator toward CalculationOutputPackage / Quote / OrderDraft.
5. Expand Operational Registry data model later.
6. Strengthen Library canonical catalog/semantic authority.
7. Keep Accounting Registry ready, but wait for sanitized 1C samples before deeper v0.6.

---

<!-- forprint-execution-workspace-compatibility-v0-1 -->
## Execution compatibility over global cleanliness

ForPrint development is expected to remain active while coordination work is queued and executed. Global repository cleanliness is therefore not a project goal by itself.

Execution must be judged from explicit authority, immutable contracts, required-input compatibility, and execution ownership. Unrelated Blueprint worktree changes do not invalidate a prompt. Material changes to required inputs do.

Shared module execution lanes remain attributable before CLAIM. Future parallelism in one module must use isolated execution workspaces rather than multiple agents writing into one dirty checkout.

No workflow may destroy, auto-stash, absorb, or silently reinterpret unrelated operator work merely to satisfy a historical "clean tree" assumption.

<!-- portfolio-operated-development-doctrine-v0-1:start -->
## Portfolio-operated development and roadmap continuity

ForPrint module development is governed as a portfolio, not as isolated repositories.

Blueprint must continuously maintain enough durable knowledge to recover:

- why a module exists;
- what it can/should do;
- what the current target finish is;
- what roadmap outcomes remain;
- what dependencies exist and when they become blocking;
- what evidence justifies progress.

Roadmaps remain living control artifacts until final project delivery.
A roadmap item whose design intent cannot be reconstructed is a governance defect.

Module executors consume Blueprint standards as read-only authority. They may request clarification or propose a
change, but they do not silently fork project-wide governance inside their own repositories.

Portfolio optimization balances time, budget, dependency criticality, business/project value, risk and executor
quality rather than maximizing one module's local velocity.
<!-- portfolio-operated-development-doctrine-v0-1:end -->
