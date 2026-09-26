# ForPrint Portfolio Full-Horizon Target States v0.1

Status: `PROPOSED_PORTFOLIO_BASELINE_REQUIRES_OWNER_REVIEW`

Normal module implementation remains held.

## forprint_system_blueprint

Priority: `P0`
Inventory state: `STRONG_EXISTING_FOUNDATION`
Role: Architecture/governance/portfolio coordination

### AGREED / RECOVERED
- Global architecture, boundaries, standards, Human Intent, dependency/readiness balance.

- Historical Asset Index is accepted as real portfolio work, implemented as a projection over domain-owned asset, technical and operational evidence rather than as a new competing source of truth.
- The retrieval host remains an explicit architecture decision; the existing Semantic Retrieval candidate must not be promoted automatically merely because historical indexing is required.

- The working portfolio host for the first durable Process Manager capability is Operations Control Registry; no standalone Process Manager module is created initially.
- Process Manager is deliberately designed as a hosted-but-extractable capability, so later separation requires evidence rather than an early architectural guess.

### SYNTHETIC / PROPOSED
- Stronger automated portfolio health/decision-support projections.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.
11. Define the cross-module Historical Asset Index contract over Library reference semantics, Prepress technical asset facts and Operations Control Registry order/job/revision state.
12. Define candidate retrieval stages as cheap scoped retrieval followed by deeper comparison of a small candidate set and explicit human/customer selection when ambiguity remains.
13. Resolve the final hosted-capability location only after comparing an existing-host implementation with the noncanonical Semantic Retrieval module candidate.
14. Govern the hosted Process Manager boundary so process truth, domain truth, transport state and human-facing workflow UI remain explicitly separated.
15. Review extraction triggers after real usage evidence, including independent scaling, availability, topology, ownership pressure and cross-domain coupling.

### Dependencies
- none / portfolio owner

Human control surfaces: `DEVELOPER_AUDIT, ADMIN_FACING`
Module value test: `KEEP`

## calculator_engine

Priority: `P0`
Inventory state: `OWNER_DIRECTION_CLEAR_DEEP_INVENTORY_REQUIRED`
Role: Calculation, quote and structured Job Specification engine

### AGREED / RECOVERED
- Calculation/quote/order drafts, price/material/time estimates, early visual configuration, exact reference set recovered.

### SYNTHETIC / PROPOSED
- Reusable constructor family, outsourcing decisions and partner-adapter integration.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `forprint_library`
- `forprint_contract_registry`
- `forprint_prepress_hub`
- `warehouse_service`

Human control surfaces: `USER_FACING, OPERATOR_FACING, ADMIN_FACING`
Module value test: `KEEP`

## forprint_library

Priority: `P0`
Inventory state: `OWNER_DIRECTION_CLEAR`
Role: Canonical semantic/catalog/reference and shared UI publication authority

### AGREED / RECOVERED
- Canonical products/materials/services/operations/aliases/profiles; shared UI package publication.

- Historical/reference asset semantics use stable asset and revision references; Library may own canonical reference-media metadata where applicable, while customer/order/production truth remains with its domain owners.
- Historical Asset Index entries are projections over authoritative sources; an index/search result never becomes canonical asset, order or production truth.

### SYNTHETIC / PROPOSED
- Fast capability/semantic discovery and mature version/adoption lifecycle.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.
11. Define stable historical/reference asset metadata semantics including asset ID, source module, entity links, revision references, media type and provenance.
12. Define the boundary between Library-owned canonical reference media and customer/order/production assets owned by operational domains.

### Dependencies
- `forprint_contract_registry`

Human control surfaces: `DEVELOPER_AUDIT, ADMIN_FACING`
Module value test: `KEEP`

## forprint_contract_registry

Priority: `P0`
Inventory state: `DIRECTION_CLEAR_FOUNDATION_PENDING`
Role: Versioned inter-module contract lifecycle registry

### AGREED / RECOVERED
- Contract manifests/revisions/compatibility/adoption; first pilot Calculator Job Specification -> OCR.

### SYNTHETIC / PROPOSED
- Generated projections, migration/deprecation automation and compatibility view after proven pilots.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `forprint_system_blueprint`
- `forprint_project_inspector`

Human control surfaces: `DEVELOPER_AUDIT, ADMIN_FACING`
Module value test: `KEEP`

## forprint_project_inspector

Priority: `P0`
Inventory state: `STRONG_DIRECTION`
Role: Read-only structural/semantic/conformance verification

### AGREED / RECOVERED
- Detects drift/contradictions/ownership violations; never invents domain truth.

### SYNTHETIC / PROPOSED
- Self-inventory health, duplicate-capability detection, UI conformance, bounded semantic review.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `forprint_system_blueprint`

Human control surfaces: `DEVELOPER_AUDIT, ADMIN_FACING`
Module value test: `KEEP`

## forprint_identity_access_service

Priority: `P0`
Inventory state: `CONFIRMED_NEW_MODULE_NOT_IMPLEMENTED`
Role: Shared identity/authentication/authorization/access service

### AGREED / RECOVERED
- One shared identity/access capability; roles + user overrides; deny-by-default cross-client access.

### SYNTHETIC / PROPOSED
- Sessions/devices/recovery/MFA/passkeys/SSO/admin access-review.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `forprint_operations_control_registry`
- `forprint_system_administration`

Human control surfaces: `USER_FACING, ADMIN_FACING`
Module value test: `KEEP`

## forprint_operations_control_registry

Priority: `P0`
Inventory state: `FOUNDATION_EXISTS_DEEP_REVIEW_REQUIRED`
Role: Canonical operational party/order/task/control registry and write boundary

### AGREED / RECOVERED
- Operational orders/requests/events/tasks/blockers and stable shared party/order IDs.

- Operations Control Registry remains authoritative for operational order/job identity, Job Ticket revision and production lifecycle state referenced by historical assets.
- Historical asset revision-family projections must derive operational status from explicit order/job/revision evidence rather than filenames or search inference.

- The first durable Process Manager capability is hosted inside Operations Control Registry because this module already owns the canonical operational state and write boundary for orders, tasks, blockers, incidents, deadlines and cross-module execution context.
- Hosted Process Manager state is a distinct capability namespace: it owns durable process instances, current step, waiting conditions, expected events, timers, deadlines, retry state, escalation state and transitions without absorbing foreign domain truth.
- The hosted capability must remain extraction-ready through explicit contracts, its own state model, adapters, tests and minimal imports from the Operations Control Registry host.

- Treat the current Operations Control Registry worktree as present implementation evidence while preserving historical Operational Registry identifiers in immutable provenance; repository/path cleanup remains separately authorized.
- Reconcile the persistent ClientRecord/OrderRecord core with richer ClientAccount/OperationalOrder foundations before promoting either richer generation to canonical runtime truth; make the chosen migration or decomposition boundary explicit.
- Separate business-partner/person/organization/customer/billing/delivery ownership and order/workflow/process/production/payment-fact/dictionary status axes before expanding canonical machine ownership.
- After the project interaction-role taxonomy is settled, reconcile accepted Accounting/Warehouse/Logistics/Prepress inbound facts and references plus Operations command/query boundaries without letting transport or message direction create semantic ownership.

### SYNTHETIC / PROPOSED
- Mature operational lifecycle, Job Ticket state, reservations/obligations and resilient commands/events.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.
11. Define the operational historical-asset link contract connecting asset references to order ID, job ID, revision and authoritative operational state.
12. Define explicit current/superseded/production-result and approval-related revision evidence required by historical asset consumers.
13. Expose operational revision/status projections for historical retrieval without transferring operational truth into the search/index layer.
14. Define the hosted Process Manager namespace and durable process-instance identity/state model inside Operations Control Registry.
15. Define current-step, waiting-condition, expected-event, timer, deadline, retry, escalation and transition semantics for long-running processes.
16. Define an append-only process transition/event ledger with correlation, idempotency, restart recovery and deterministic resume semantics.
17. Define operator-attention and authorized human-decision integration without letting unattended workflow state silently authorize foreign-domain actions.
18. Define domain adapters so CRM, Telegram, Logistics and other modules can observe or participate through typed process intents/events without owning the durable process instance.
19. Add explicit extraction-readiness criteria so the capability can later move to a standalone Process Manager service if scale, topology or ownership evidence justifies separation.

### Dependencies
- `calculator_engine`
- `forprint_contract_registry`
- `forprint_library`

Human control surfaces: `OPERATOR_FACING, ADMIN_FACING`
Module value test: `KEEP`

## forprint_accounting_registry_service

Priority: `P0`
Inventory state: `OWNER_DIRECTION_CLEAR_DECOMPOSITION_REQUIRED`
Role: Operational/commercial accounting registry and 1C compatibility boundary

### AGREED / RECOVERED
- Invoices/payments/accounting documents/reconciliation/1C staging; supplier-document automation.

### SYNTHETIC / PROPOSED
- Management accounting, settlements, safe conditional mandates and mature 1C exchange.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `forprint_operations_control_registry`
- `forprint_library`
- `warehouse_service`
- `calculator_engine`

Human control surfaces: `OPERATOR_FACING, ADMIN_FACING`
Module value test: `KEEP`

## warehouse_service

Priority: `P1`
Inventory state: `DEEP_REVIEW_REQUIRED`
Role: Physical inventory/material-location truth and movement service

### AGREED / RECOVERED
- Physical stock fact distinct from accounting valuation and Calculator planned need.

### SYNTHETIC / PROPOSED
- Reservations, receipts/issues/writeoffs, locations, shortages, cycle count, traceable reprint consumption.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `forprint_library`
- `forprint_operations_control_registry`
- `forprint_accounting_registry_service`

Human control surfaces: `OPERATOR_FACING, ADMIN_FACING`
Module value test: `KEEP`

## forprint_prepress_hub

Priority: `P1`
Inventory state: `FIRST_PASS_DIRECTION_RECORDED`
Role: Prepress/file preparation and production-readiness evidence

### AGREED / RECOVERED
- PDF/document probe and readiness evidence consuming Calculator + Library.

- Prepress contributes deterministic technical asset facts and derived preview evidence for historical indexing without owning customer/order history or search-result truth.
- Technical asset evidence may include exact file hash, type, size, page count, dimensions, color/resolution facts, preview references and file revision provenance.

### SYNTHETIC / PROPOSED
- Preflight/normalization/imposition/profile/hot-folder and future metadata projections.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.
11. Define a machine-readable technical Asset Fact Packet containing deterministic file facts, source revision, hashes and safe preview references.
12. Define deterministic fingerprint/probe outputs suitable for downstream candidate retrieval while keeping semantic match decisions outside Prepress.
13. Define historical-file provenance and master-versus-derived relationships without making Prepress the raw archive or historical search owner.

### Dependencies
- `calculator_engine`
- `forprint_library`
- `forprint_contract_registry`

Human control surfaces: `OPERATOR_FACING`
Module value test: `KEEP`

## production_runtime_inspector

Priority: `P1`
Inventory state: `DEEP_REVIEW_REQUIRED`
Role: Runtime production actuals/evidence and exact device-used inspection

### AGREED / RECOVERED
- Records concrete device and actuals without silently rewriting approved norms.

### SYNTHETIC / PROPOSED
- Operation actuals, quality/variance signals, telemetry and norm-change proposals.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `forprint_operations_control_registry`
- `forprint_system_administration`
- `forprint_library`

Human control surfaces: `OPERATOR_FACING, DEVELOPER_AUDIT`
Module value test: `KEEP`

## forprint_crm

Priority: `P1`
Inventory state: `FIRST_PASS_PLUS_NEW_OWNER_DIRECTION`
Role: Unified human business cockpit, analytics and composite workflow entry point

### AGREED / RECOVERED
- Owner-data aggregation without foreign-data ownership; dashboards/wallboards; composite workflows.

- Customer intelligence is a layered CRM capability with separate Seed Profile, Observed Customer Model and Effective Policy layers; this does not make CRM the canonical client registry or owner of foreign domain truth.
- Seed Profile is a simple manager-selected starting preset for relationship and communication handling and is not inferred authority.
- Observed Customer Model is derived from evidence with provenance, recency, confidence and domain-specific coverage rather than from opaque permanent labels.
- Effective Policy combines approved policy rules with permitted customer-model evidence but must never silently expand commercial, financial or operational authority.
- Customer-specific semantics distinguish baseline, exception, possible shift, probable shift and new baseline using recency weighting, minimum evidence, hysteresis and contextual segmentation.
- Customer relationship health and trajectory are multidimensional projections covering payment health, commercial value, growth momentum, margin quality, service burden, order clarity, dispute risk, relationship stability and strategic potential, with underlying facts retained by their owner modules.
- Customer-model updates combine event-driven evidence with periodic reconciliation; stale, conflicting and insufficient evidence must remain explicit.
- Profile and policy transitions require durable provenance, transition history and auditable human override rather than destructive replacement of prior state.

- CRM is the primary human-facing Process Manager control surface but does not own durable process instances, timers, retries, deadlines or transition truth.

### SYNTHETIC / PROPOSED
- Customer/Supplier 360, universal search, saved role views, activity timeline, exception center.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.
11. Define the CRM customer-intelligence model as separate Seed Profile, Observed Customer Model and Effective Policy layers without absorbing canonical client identity or foreign domain truth.
12. Define manager-selectable Seed Profiles as bootstrap presets with explicit scope, version and provenance.
13. Define the Observed Customer Model with evidence provenance, recency, confidence, domain-specific coverage and safe handling of insufficient evidence.
14. Define Effective Policy composition so approved rules may consume customer-model evidence without silently expanding financial, commercial or operational authority.
15. Implement baseline-to-shift semantics with exception, possible-shift, probable-shift and new-baseline states plus recency weighting, minimum evidence, hysteresis and contextual segmentation.
16. Define multidimensional customer health and trajectory projections using owner-sourced payment, value, growth, margin, service-burden, clarity, dispute, stability and strategic-potential evidence.
17. Define event-driven customer-model updates plus periodic reconciliation, freshness checks and explicit conflict/staleness handling.
18. Define immutable profile/policy transition history, provenance and auditable human override before customer-specific policy automation is considered mature.
19. Define CRM views for active processes, current step, blockers, waiting state, deadlines, escalations and next authorized actions from Process Manager projections.
20. Define structured operator commands for clarification, acknowledgement, override request and authorized intervention without creating shadow workflow state.

### Dependencies
- `forprint_operations_control_registry`
- `calculator_engine`
- `forprint_accounting_registry_service`
- `warehouse_service`
- `logistics_service`
- `forprint_identity_access_service`

Human control surfaces: `OPERATOR_FACING, ADMIN_FACING`
Module value test: `KEEP`

## logistics_service

Priority: `P1`
Inventory state: `IMPLEMENTATION_EXISTS_RUNTIME_SCOPE_GATED`
Role: Provider-neutral shipment/pickup/delivery/tracking truth

### AGREED / RECOVERED
- Provider adapters, shipment drafts/tracking/events; current H10 sole automation pilot.

- Logistics retains authoritative shipment-specific workflow state machines, retries and reconciliation, while broader cross-domain Process Manager state is hosted by Operations Control Registry.

### SYNTHETIC / PROPOSED
- Mature carrier/taxi/courier adapters, evidence handoff, delivery exceptions and bounded automation.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.
11. Define the boundary between Logistics shipment lifecycle state and a parent or linked cross-domain Process Manager instance.
12. Expose typed shipment events, waiting conditions and outcomes to Process Manager without transferring carrier/provider truth out of Logistics.

### Dependencies
- `forprint_operations_control_registry`
- `forprint_accounting_registry_service`
- `forprint_identity_access_service`

Human control surfaces: `OPERATOR_FACING, ADMIN_FACING`
Module value test: `KEEP`

## telegram_bot

Priority: `P1`
Inventory state: `ACTIVE_HISTORY_NEW_EXECUTION_HELD`
Role: Conversational customer/staff channel adapter

### AGREED / RECOVERED
- Structured request/response channel without owning CRM/order/accounting truth.
- Personalized communication orchestration: Telegram preserves dialogue continuity and renders canonical domain facts according to approved customer communication context without changing those facts.
- Structured inbound requests and outbound communication intents are the preferred cross-module communication contract.
- Customer-specific communication context may be consumed by Telegram, while canonical customer profile, commercial policy and customer economics remain outside Telegram ownership.
- Clarification converges toward structured Order Drafts using canonical Library, Calculator and other domain constraints.
- AI remains a replaceable helper after deterministic rules, history, classifiers, customer context and clarification, with human escalation for unresolved ambiguity.
- Historical asset retrieval is consumed through a machine-readable index; Telegram does not own archives, fingerprints or historical asset truth.
- Long-running business processes are external durable process truth; Telegram participates only through communication intents, acknowledgements and clarification.

### SYNTHETIC / PROPOSED
- Voice transcription, supplier enrichment, richer self-service, future TTS/voice.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.
11. Define personalized communication orchestration with conversation continuity, approved communication preferences and strict presentation-versus-facts separation.
12. Define channel-neutral inbound structured domain requests/events and outbound structured communication intents with correlation and provenance.
13. Define consumption of customer-specific communication context without moving canonical customer profile, commercial policy or analytics into Telegram.
14. Define bounded clarification and structured Order Draft interaction using canonical Library/Calculator/domain constraints.
15. Define deterministic-to-context-to-AI-to-human escalation with replaceable model/provider slots and progress/contradiction based escalation.
16. Define Telegram consumption of historical customer asset retrieval results without live archive scanning or asset-index ownership.
17. Define Telegram as a communication participant for durable long-running business processes while process state/timers/deadlines/transitions remain with the eventual canonical Process Manager owner.

### Dependencies
- `calculator_engine`
- `forprint_crm`
- `forprint_identity_access_service`
- `forprint_integration_gateway`

Human control surfaces: `USER_FACING, ADMIN_FACING`
Module value test: `KEEP`

## forprint_operations_assistant

Priority: `P1`
Inventory state: `FIRST_PASS_DIRECTION_RECORDED`
Role: Low-friction shop-floor assistant, guided forms and operational knowledge

### AGREED / RECOVERED
- Procedures/guided forms/Job Ticket assistance/physical observations.

### SYNTHETIC / PROPOSED
- Role-aware training, visual SOPs, reprint/exception capture, bounded operational AI.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `forprint_library`
- `forprint_operations_control_registry`
- `forprint_identity_access_service`

Human control surfaces: `OPERATOR_FACING`
Module value test: `KEEP`

## forprint_system_administration

Priority: `P1`
Inventory state: `FIRST_PASS_DIRECTION_RECORDED`
Role: IT/workplace/device/data-platform/secrets administration

### AGREED / RECOVERED
- Workstation/admin surface plus physical PostgreSQL and secrets-platform operations.

### SYNTHETIC / PROPOSED
- Fleet onboarding, device capability inventory, backup/PITR, health and operational-readiness gates.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `cloud_backup_manager`
- `forprint_project_inspector`

Human control surfaces: `ADMIN_FACING, DEVELOPER_AUDIT`
Module value test: `KEEP`

## forprint_integration_gateway

Priority: `P2`
Inventory state: `PAUSED_UNTIL_RUNTIME_NEED`
Role: Runtime transport validation/routing/idempotency/correlation boundary

### AGREED / RECOVERED
- Routes/validates ACTIVE contracts without business ownership.

- Gateway delivery state, retry, queue and dead-letter handling remain transport mechanics and must not become durable business Process Manager state.

### SYNTHETIC / PROPOSED
- Delivery ledger, observability and scalable routing when runtime need justifies activation.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.
11. Define transport correlation between Gateway delivery attempts and Process Manager process/event identities without merging their state machines.
12. Keep Gateway retry/dead-letter decisions transport-scoped while business waiting, deadline and escalation truth remains in the hosted Process Manager capability.

### Dependencies
- `forprint_contract_registry`
- `forprint_operations_control_registry`

Human control surfaces: `DEVELOPER_AUDIT, ADMIN_FACING`
Module value test: `KEEP`

## website

Priority: `P2`
Inventory state: `FIRST_PASS_DIRECTION_RECORDED`
Role: Customer web channel using shared Calculator/Identity/domain contracts

### AGREED / RECOVERED
- Must not duplicate Calculator/catalog/order truth; legacy surface needs controlled reconciliation.

### SYNTHETIC / PROPOSED
- Modern self-service, account/order/calculation/files/payment/delivery views.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `calculator_engine`
- `forprint_identity_access_service`
- `forprint_library`
- `forprint_operations_control_registry`

Human control surfaces: `USER_FACING`
Module value test: `KEEP`

## mobile_app

Priority: `P2`
Inventory state: `DEFERRED`
Role: Future mobile customer/staff channel

### AGREED / RECOVERED
- Deferred until Calculator/Identity/API contracts mature.

### SYNTHETIC / PROPOSED
- Secure mobile self-service over the same domain contracts as web.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `calculator_engine`
- `forprint_identity_access_service`
- `forprint_integration_gateway`

Human control surfaces: `USER_FACING`
Module value test: `KEEP`

## forprint_marketing_orchestrator

Priority: `P3`
Inventory state: `NON_BLOCKING_FUTURE`
Role: Marketing campaign/content orchestration

### AGREED / RECOVERED
- Campaign/content planning and human-reviewed publication without becoming CRM.

### SYNTHETIC / PROPOSED
- Multi-channel automation, AI creative routing, cost/performance learning and lead handoff.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `forprint_crm`
- `website`
- `forprint_library`
- `forprint_accounting_registry_service`

Human control surfaces: `OPERATOR_FACING, ADMIN_FACING`
Module value test: `KEEP`

## forprint_strategic_control_plane

Priority: `P3`
Inventory state: `NON_BLOCKING_FUTURE`
Role: Strategic priority/status/decision-support layer

### AGREED / RECOVERED
- Tracks goals/priorities and challenges stale direction without overriding Blueprint/operator.

### SYNTHETIC / PROPOSED
- Scenario analysis, strategic KPI aggregation and advisory loops.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `forprint_system_blueprint`

Human control surfaces: `ADMIN_FACING, DEVELOPER_AUDIT`
Module value test: `KEEP`

## cloud_backup_manager

Priority: `SUPPORT`
Inventory state: `IMPLEMENTED_SUPPORT_MODULE`
Role: Infrastructure backup utility/reference UI shell

### AGREED / RECOVERED
- Backup/health support; UI reference shell candidate.

### SYNTHETIC / PROPOSED
- Possible absorption into System Administration if lifecycle evidence justifies it.

### Full horizon
1. Reconcile current implementation/evidence and stale documentation.
2. Close charter, ownership boundaries and mature target state.
3. Build/repair capability catalog and module self-inventory surfaces.
4. Define canonical data/contracts/dependency timing.
5. Harden deterministic core with fixtures/tests.
6. Add early role-appropriate Human Control Surface where useful.
7. Integrate only through accepted producer/consumer contracts.
8. Add observability, exception handling, recovery and audit evidence.
9. Pilot bounded automation only under explicit authority and measure variance/cost/quality.
10. Reach mature target, document migration/retirement paths and continue measured optimization.

### Dependencies
- `forprint_system_administration`

Human control surfaces: `ADMIN_FACING`
Module value test: `REVIEW_MERGE_LATER`

## Proposed/noncanonical

- `forprint_semantic_retrieval_service`: preserve proposal/Human Intent, but require explicit value review before canonical promotion.

## verification_lab

- Strategic priority: `P0`
- Role: Independent verification, adversarial testing, fault-injection and deterministic regression evidence module.
- Inventory state: `CONFIRMED_NEW_MODULE_NOT_IMPLEMENTED`
- Implementation eligible now: `false`
- Portfolio gate: `HOLD_UNTIL_PORTFOLIO_READINESS_BASELINE_COMPLETE`
- Module value test: `KEEP`

### AGREED / RECOVERED

- Detects drift/contradictions/ownership violations; never invents domain truth.
- Verification Lab is a distinct canonical module that intentionally tries to prove the system wrong before customers or incidents do.

### SYNTHETIC / PROPOSED

- Self-inventory health, duplicate-capability detection, UI conformance, bounded semantic review.
- Mature Verification Lab should support black/gray/white-box Test Plane campaigns, adversarial/fault/concurrency testing, deterministic regression and release-gate evidence with synthetic side effects only.

### Full horizon

1. Establish Verification Lab canonical identity, charter and strict separation from Project Inspector and Runtime Inspector.
2. Define BLACK_BOX, GRAY_BOX and WHITE_BOX read-only diagnostic modes and their evidence boundaries.
3. Define Test Plane isolation with fake/synthetic payment, courier, printer, email, cloud, Telegram and database side effects.
4. Define normal/invalid/boundary/malformed/combinatorial/multilingual/out-of-domain/auth/data-isolation test taxonomy.
5. Define prompt-adversarial, tool-misuse, state-machine, concurrency, idempotency, stale-cache and schema-fuzz campaigns.
6. Define fault/recovery, timeout, unavailable-resource, retry/dead-letter, load/performance and cost-regression campaigns.
7. Convert useful AI-discovered failures into owner-confirmed deterministic regression corpus rather than permanent stochastic-only tests.
8. Define change-triggered, nightly, weekly, manual, pre-release and post-release verification campaign policy.
9. Define trace-aware evaluation of intermediate contract/tool/state behavior, not only final user-visible answer.
10. Remain planning-only until Test Plane, Execution Policy Gate, IAM and explicit operator distribution/implementation approval are ready.

### Dependencies

- `forprint_system_blueprint`
- `forprint_contract_registry`
- `forprint_project_inspector`
- `forprint_system_administration`

### Human control surfaces

- `DEVELOPER_AUDIT`
- `ADMIN_FACING`

<!-- FORPRINT_U92_U107_CANONICAL_INTEGRATION_20260903:START -->
## 2026-09-03 u92/u107 architecture integration

Canonical module count after approved planning promotion: **23**.

New canonical module: `verification_lab`.

`forprint_semantic_retrieval_service` remains proposed/noncanonical.

Roadmap/governance narrative:
`coordination/internal_work/blueprint/evening_reviews/2026-09-03/2026-09-03__u92_architecture_governance_integration_v0_1.md`

This planning integration does **not** authorize module implementation, assistant distribution,
prompt activation, H10 widening, automatic acceptance/release, or cross-repository diagnostics.
<!-- FORPRINT_U92_U107_CANONICAL_INTEGRATION_20260903:END -->
