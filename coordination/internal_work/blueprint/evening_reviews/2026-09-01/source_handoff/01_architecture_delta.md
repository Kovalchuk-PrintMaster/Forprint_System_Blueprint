# Consolidated Architecture Delta

## A. Roadmap memory and evening conversations

Evening discussions are exploratory. Afterward Blueprint extracts decisions,
clarifications, Human Intent and roadmap implications, reconciles them with the
repository, and integrates only the missing delta.

Important live human wording must not be lost. Preserve selected exact operator
quotes for important roadmap decisions:

conversation quote -> Human Intent -> roadmap step -> implementation/contract -> evidence

Do not archive every chat sentence. Keep curated quotes that explain why a
roadmap step exists. Expanded human portfolio should show these quotes under the
relevant roadmap step. Narrow/machine portfolio may omit long quote payloads;
balanced portfolio may show concise references.

## B. Full-horizon roadmap rule for every module

Every module must show a visible route from current state to mature target.
Unknown distant areas may be SYNTHETIC/PROPOSED but must still be visible.

Every module ends with `Final Target State` split into:

1. AGREED / HUMAN-CONFIRMED
2. SYNTHETIC / PROPOSED

Then a compact list:
`At mature state this module: 1... 2... 3...`

If Blueprint cannot formulate a useful mature purpose for a module even after
serious synthetic reconstruction, the module becomes a candidate for merge,
absorption, pause or removal.

## C. Module self-inventory / self-indexing

Every module needs concise machine-readable surfaces covering:
- role and ownership;
- capabilities: implemented / partial / planned / deferred;
- current roadmap position and next steps;
- contracts provided/consumed;
- standards used;
- dependencies, blockers and modules blocked;
- known conflicts/gaps;
- last verified commit and evidence;
- semantic review status.

Before meaningful new implementation:
1. search global capability index;
2. check canonical semantic owner;
3. check reusable primitive;
4. check contract/interface;
5. check existing implementation;
6. only then propose new implementation.

Completion reports should state what was implemented, what was reused, newly
proposed reusable capability, dependencies/contracts changed, self-index update,
roadmap evidence, questions, conflicts and tests.

## D. ForPrint Control Center / shared UI

Use Cloud Backup Manager as a reference shell, not automatic authority.

Unified navigation:
- left vertical navigation = modules/assistants;
- inside selected module, top tabs = that module's own functional areas.

Ownership:
- Blueprint: UI governance and adoption boundaries;
- Library: design tokens, themes, reusable components, component catalog,
  versions and exports;
- consumer modules: compose pages;
- Project Inspector: conformance/accessibility/stale-version checks.

Themes/accessibility:
- LIGHT;
- DARK;
- seasonal overlays;
- future high-contrast;
- COMPACT / STANDARD / LARGE;
- per-user preferences;
- larger fonts/touch targets.

New component lifecycle:
check catalog -> prototype/proposal -> Inspector validation -> early operator
approval -> Library publishes versioned component -> index/catalog update ->
controlled adoption.

Each module roadmap classifies Human Control Surface:
USER_FACING / OPERATOR_FACING / ADMIN_FACING / DEVELOPER_AUDIT / HEADLESS.

Important modules should receive early visual surfaces:
UI-0 shell; UI-1 read-only; UI-2 safe controls; UI-3 core workflows;
UI-4 refinement; UI-5 mature interface.

## E. New module candidate: ForPrint Identity & Access Service

Create a dedicated module/capability rather than putting auth inside Website,
Calculator or CRM.

Synthetic mature path includes:
1. account registration;
2. login/logout;
3. sessions;
4. password/passkey support;
5. MFA;
6. recovery;
7. roles;
8. permission sets;
9. per-user permission overrides;
10. admin UI;
11. session/device revocation;
12. security/auth audit;
13. SSO across Website/Calculator/Control Center/Mobile;
14. policy-driven mature access control.

Permission model supports role defaults plus explicit per-user additions or
restrictions.

External provider credentials are not user identity. API keys/passwords for Nova
Poshta, partner sites, Bolt/Uklon, etc. belong to centralized secrets
infrastructure.

## F. Canonical ForPrint data architecture

Use one central PostgreSQL operational platform with logical domain boundaries.

Canonical principle:
ONE physical PostgreSQL platform + stable global IDs + logical domain schemas +
controlled writes + shared reporting projections.

Suggested schemas:
party, orders, catalog, calculator, accounting, warehouse, production, logistics,
identity, audit, reporting.

Physical platform ownership:
System Administration owns cluster, backups, restore/PITR, replication,
monitoring, DB roles/credentials, migration infrastructure, performance/storage.

Logical semantic ownership:
profile/domain modules own semantics and approved write paths for their data.

Cross-domain writes should go through the owning domain/application logic rather
than arbitrary direct SQL. Controlled cross-domain reads can use read-only views
and projections. Integration Gateway is not a generic SQL gatekeeper.

Use stable shared identities:
- one Business Partner master can have CUSTOMER / SUPPLIER / SUBCONTRACTOR /
  CARRIER roles;
- one stable order_id links Calculator, Accounting, Warehouse, Production,
  Logistics and CRM domain records.

Use reporting views/materialized views/read models for cross-domain reporting.

## G. CRM mature direction

CRM is NOT canonical owner of Accounting, Warehouse, Production, Logistics or
other foreign domain truth.

CRM is a unified operational entry point, composition/orchestration UI and
workflow layer.

Two major mature families:

### 1. Aggregated operational intelligence
- configurable dashboards/wallboards;
- Customer/Supplier 360;
- role-aware views;
- production/accounting/logistics projections;
- capacity/risk visibility;
- variance/exception analytics;
- saved role layouts;
- universal search;
- cross-module activity timeline.

Keep dashboard/wallboard capability encapsulated inside CRM for now. Do not
create a separate monitoring module yet, but keep extraction boundaries clean.

### 2. Composite cross-module human workflows
A human should solve a business task in one guided CRM interface instead of
opening Calculator, Warehouse, Accounting, Logistics, etc. manually.

CRM collects input and dispatches structured commands/bundles to real data
owners.

Example: new supplier/material onboarding:
1. create/select Business Partner;
2. enter known contact/legal data;
3. create/select provisional material candidate;
4. choose communication channels;
5. submit one composite workflow;
6. Telegram/email enrichment gathers missing data;
7. Accounting validates legal/payment details;
8. Library resolves material semantics/aliases;
9. Warehouse receives stock/procurement context;
10. Logistics receives delivery context.

Variance dashboards should surface planned vs actual time/material/cost,
reprints, delays, material/equipment/staffing blocks.

## H. Calculator mature direction

Do not manually narrate thousands of mechanical product rules.

Build a full synthetic roadmap. Later the operator will provide 2-3 external
calculator references and identify the primary reference.

Then perform:
- deep analysis of primary reference;
- comparison with secondary references;
- extraction of strongest product/configuration patterns;
- improved UI concept;
- roadmap/configuration/rules/tests update.

Exact reference URLs remain open and must not be invented.

Calculator receives an early visual interface.

For outsourcing:
Calculator produces canonical Job Specification / outsource request.
External partner interaction should be isolated behind provider adapters.
If no API exists, controlled browser automation may be used with validation,
evidence, retries and human escalation.
External credentials belong to secrets infrastructure.

## I. Real-time operational UI

Drag-and-drop is valid, but UI should send domain commands rather than mutate DB
rows directly.

Example:
ReassignJob(job_id, from_device, to_device, actor, reason)

Owner validates, persists, audits and publishes updates. Open workspaces receive
real-time updates through WebSocket/SSE/event stream. Notifications are
role/relevance aware.

## J. Shared capability consistency

Avoid multiple modules implementing the same business rule differently.

Classify reusable logic:
- general technical primitive -> shared Library/package;
- UI primitive -> Library Design System;
- semantic vocabulary/profile -> Library;
- cross-module interface -> Contract Registry;
- domain business rule -> one canonical domain owner;
- financial rounding/accounting rule -> canonical Accounting/Money policy.

Use versioned revisions and controlled adoption.

## K. Cross-module/AI runaway protection

Retain durable outbox/inbox, correlation, idempotency, retries, dead-letter and
manual-review patterns.

Add bounded execution envelope:
root_request_id, correlation_id, origin_module, hop_count, visited_modules,
retry_count, clarification_round, ai_call_count, ai_budget, time_budget, ttl,
escalation_policy.

Repeated unresolved cycles must stop and escalate.

Preferred escalation:
1. deterministic local logic;
2. structured local/domain lookup;
3. structured request to domain owner;
4. bounded AI intervention;
5. human escalation.

## L. Assistant Intervention Ledger

Every deterministic->AI fallback should become a learning signal.

Track trigger, failure reason, capability/roadmap step, context refs, model,
cost/tokens/time, result, resolution class, automation candidate, repeat
signature/count and review status.

Periodic review converts recurring AI interventions into deterministic
capabilities where useful.

## M. Accounting Registry Service / Operations Control Registry / other unclear modules

Do not force full human specification tonight.

For every insufficiently understood module:
- recover all existing live intent;
- reconcile roadmap/policy/evidence;
- synthesize the missing path to mature state;
- clearly separate AGREED from SYNTHETIC target capabilities;
- present the full mature target in the next expanded portfolio for human review.
