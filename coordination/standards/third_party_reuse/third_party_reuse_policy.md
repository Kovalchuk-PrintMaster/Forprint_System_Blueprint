# Third-Party Reuse Policy

## Purpose

This policy defines how ForPrint should evaluate and use third-party tools, frameworks, services and platforms.

The goal is to keep ForPrint lightweight, controllable, debuggable and local-first while still allowing practical reuse of mature commodity tools.

## Core principle

```text
ForPrint builds its own domain core.
ForPrint may reuse commodity infrastructure.
Third-party tools must not silently become ForPrint architecture owners.
Domain core must remain ForPrint-owned

ForPrint should keep direct ownership over the business and architecture core.

This includes:

system architecture and module boundaries;
module ownership rules;
canonical domain objects;
semantic and catalog meaning;
calculation logic;
operational order and task truth;
accounting ownership boundaries;
1C adapter boundaries;
Gateway handoff semantics;
Make-first workflow;
completion packet and coordination governance;
Blueprint standards and prompts.

Third-party tools may support these areas, but must not replace ForPrint ownership without explicit Blueprint approval.

Reuse modes

Every third-party tool should be classified before adoption.

reference_only

The tool is used only as a source of ideas, terminology, UI patterns or architectural comparison.

It is not integrated into ForPrint runtime.

Examples:

reviewing ERPNext or Odoo workflow concepts;
checking how PIM systems model catalogs;
reviewing BI dashboard patterns;
studying queue or event-streaming terminology.

Rules:

no production dependency;
no data ownership transfer;
no adapter required;
no module boundary changes.
sandbox_adapter

The tool is connected in an isolated experiment.

The goal is to learn whether it is useful.

Examples:

sandbox n8n automation test;
sandbox ERPNext/Odoo integration check;
temporary BI dashboard proof of concept;
experimental PIM import/export adapter.

Rules:

must not own canonical ForPrint data;
must not be required for normal production flow;
must be removable;
must use sample data or explicitly approved test data;
must be documented as sandbox.
supporting_service

The tool is used as commodity infrastructure or operator support.

Examples:

PostgreSQL as database infrastructure;
Keycloak as future identity provider;
Superset or Metabase as BI dashboard layer;
Cloud Backup Manager as backup support;
Mermaid as documentation visualization format;
GitHub as repository hosting;
rclone as backup transport utility.

Rules:

may support production;
must not redefine business ownership;
must have clear backup or recovery story when relevant;
must be replaceable or isolated where practical;
must be documented in module or Blueprint infrastructure notes.
core_dependency

The tool becomes critical for runtime, business flow or data availability.

Examples:

Kafka as required production event backbone;
RabbitMQ as mandatory command delivery layer;
Keycloak as mandatory authentication and authorization authority;
Superset/BI layer used as operational decision source;
external ERP as production accounting or order owner.

Rules:

requires Blueprint approval;
requires ADR or explicit architecture checkpoint;
requires failure and recovery plan;
requires backup or export strategy if it stores important data;
requires ownership boundary review;
requires local degraded-mode strategy where possible.

core_dependency must not be introduced casually inside a module implementation.

Preferred adoption order

ForPrint should prefer the lightest mode that solves the current problem.

Recommended order:

reference_only;
sandbox_adapter;
supporting_service;
core_dependency only when justified.

A module assistant should not jump directly from idea to core dependency.

Examples of current preferred classifications
PostgreSQL

Preferred mode:

supporting_service

Rationale:

PostgreSQL can provide local database infrastructure.
Module ownership still remains separated by schema, role and policy.
PostgreSQL does not own business truth; owner modules do.
Kafka

Preferred early mode:

reference_only

Possible future mode:

supporting_service or core_dependency

Rationale:

Kafka is powerful but operationally heavy.
ForPrint should first use Gateway, outbox/inbox, idempotency, retry and delivery ledger.
Kafka may be evaluated later if event volume, replay or streaming needs justify it.
RabbitMQ or Redis Streams

Preferred early mode:

reference_only or sandbox_adapter

Possible future mode:

supporting_service

Rationale:

They may help with asynchronous delivery later.
They should not replace Gateway ownership of handoff semantics.
n8n

Preferred mode:

sandbox_adapter or supporting_service

Boundary:

n8n may automate peripheral workflows.
n8n must not own core business logic, order truth, accounting truth or module boundaries.
Superset or Metabase

Preferred mode:

supporting_service

Boundary:

BI tools may visualize reporting data.
BI tools must not become canonical writers of business truth.
Keycloak

Preferred future mode:

supporting_service

Potential core dependency only after explicit approval.

Boundary:

Keycloak may own authentication and identity-provider behavior.
ForPrint modules still own business permissions, workflow rules and domain decisions unless explicitly redesigned.
ERPNext or Odoo

Preferred mode:

reference_only or sandbox_adapter

Boundary:

They may be used for comparison, import/export experiments or workflow research.
They must not become the hidden owner of ForPrint orders, clients, pricing or accounting without explicit Blueprint approval.
PIM or admin UI tools

Preferred mode:

reference_only or sandbox_adapter

Examples:

Akeneo;
Pimcore;
Directus;
Appsmith;
Baserow;
Budibase.

Boundary:

They may support catalog/admin interface exploration.
ForPrint Library remains owner of semantic/catalog meaning unless Blueprint explicitly changes ownership.
Debuggability requirement

Third-party adoption must not make debugging significantly worse without clear benefit.

Before adopting a third-party tool, ForPrint should be able to answer:

what problem does it solve;
what module or layer uses it;
what data it stores;
whether it can mutate canonical truth;
how to inspect its state;
how to back it up;
how to restore after failure;
how to run without it in degraded mode;
how to remove it if it fails the experiment.
Local-first requirement

Core ForPrint operations should remain local-first where practical.

Third-party cloud services may be used, but they must not make local business continuity impossible unless explicitly approved.

Examples:

GitHub may be required for repository push/pull.
Telegram API may be required for Telegram channel operation.
Cloud backup providers may be required for offsite backup.
But local operational records and pending handoffs should remain recoverable locally.
Module assistant rule

A module assistant must not introduce a new third-party dependency as a production dependency without explaining:

reuse mode;
reason for adoption;
affected modules;
owned data impact;
failure mode;
rollback or removal path;
Blueprint approval requirement if core_dependency.

If the tool affects ownership, runtime delivery, authentication, accounting, production writes or cross-module communication, the assistant must escalate to Blueprint before implementation.

Approval requirement

The following require Blueprint-level approval:

new production database technology;
new production message broker;
new authentication provider;
new BI tool used for operational decisions;
external ERP/PIM/CRM integration;
third-party tool that stores canonical business data;
third-party tool required for core runtime availability;
third-party tool that changes module ownership boundaries.
Boundary

This policy defines third-party reuse governance.

It does not approve any specific third-party tool by itself.

Specific adoption still requires module prompt, ADR, architecture checkpoint or explicit operator approval depending on risk.
