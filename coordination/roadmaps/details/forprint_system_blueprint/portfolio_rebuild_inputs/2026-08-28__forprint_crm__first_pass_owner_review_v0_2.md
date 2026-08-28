# ForPrint CRM — evening first-pass owner review

Module: `forprint_crm`

Status: `FIRST_PASS_OWNER_DIRECTION_RECORDED / SYNTHETIC_MICROSTEPS_PENDING_SECOND_PASS`

## AGREED_WITH_OWNER

CRM is the universal human-facing business cockpit. A manager should open one client/supplier/contractor view
and immediately understand relationship value, active work, financial warnings, delivery/production status,
history, recurring behavior, quality problems and useful next actions.

It should make the ecosystem easy to inspect without duplicating each module's source of truth.

## Working boundary

CRM owns relationship/profile/workflow views and manager-facing coordination. It consumes live truth from
Accounting, Logistics, Calculator, production/order systems, Library and Identity rather than replacing them.

## Synthetic roadmap expansion for pass 2

Everything below is `SYNTHETIC_CANDIDATE` unless explicitly described as owner direction.

### CRM-R0 — Inventory CRM evidence and business questions
- reconcile old CRM materials
- map person/counterparty/customer concepts
- list manager questions/actions
- find duplicated domain data
### CRM-R1 — Counterparty/relationship model
- client/supplier/contractor views
- person/contact links and roles
- manager notes/tags/segments
- Identity links without credential ownership
### CRM-R2 — Unified overview
- Accounting debt/balance alerts
- active order/job status
- Logistics live status
- communication history/context
- returns/defects/complaints
### CRM-R3 — Quick analytics
- average order/check
- frequency/seasonality
- product/material preferences
- margin/value indicators from finance truth
- problem/return patterns
### CRM-R4 — Fast actions
- recent orders
- current calculation
- repeat/reconstruct order
- shipment status
- follow-up/reminder/task
### CRM-R5 — Role-specific UX
- manager cockpit
- supplier/contractor views
- lead/admin views
- sensitive-data masking/permissions
### CRM-R6 — Live projections without duplication
- query owning modules
- safe cached read models with freshness markers
- show stale/unavailable truth explicitly
- cross-module drill-down/correlation
### CRM-R7 — Maturity metrics
- time to answer common questions
- share of workflows completed without module hopping
- projection freshness incidents
- user feedback/missing actions

## Dependencies

Identity & Access; Accounting; Logistics; Calculator; Library; Telegram/communication history;
order/production owners.

## Open questions for pass 2

Omnichannel history owner; generic Counterparty vs separate types; precomputed vs on-demand analytics;
privacy/role visibility; CRM vs Operations Assistant boundary.

## Target milestone

Managers answer most normal relationship/order questions and initiate common actions from one interface,
while every critical fact remains traceable to its owning module.

## Steady state

Continue measured improvement after the target milestone; the module is not considered permanently finished.
