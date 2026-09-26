# ForPrint Portfolio Module Roadmap Approval Matrix v0.1

Status: **ACTIVE INTERNAL PORTFOLIO ANALYSIS**

## Distribution gate

**CLOSED.** No module assistant contact, task distribution, prompt activation or implementation is authorized.

## Module horizons

### `calculator_engine`

Role: Calculation, quote and structured Job Specification engine

1. **AGREED_PLANNING_DIRECTION** — Reconcile implemented calculation, filename parsing, external-reference evidence and stale calculator documentation.
2. **AGREED_PLANNING_DIRECTION** — Confirm Calculator ownership of calculation/quote/Job Spec semantics and its non-ownership of catalog/accounting/order truth.
3. **AGREED_PLANNING_DIRECTION** — Complete capability self-inventory for products, rules, pricing, material/time estimates, filename profiles and warnings.
4. **AGREED_PLANNING_DIRECTION** — Define Contract Registry lifecycle for Calculator Job Specification and mandatory consumer compatibility.
5. **AGREED_OR_RECOVERED_TARGET** — Reconcile Library-owned materials, aliases, production naming profiles and omission/default semantics.
6. **AGREED_OR_RECOVERED_TARGET** — Specify deterministic calculation, rounding, sheet/copy semantics, warnings and evidence fixtures.
7. **AGREED_OR_RECOVERED_TARGET** — Define early visual configuration/workbench UX without duplicating Library catalog or CRM/order truth.
8. **PROPOSED_TARGET_REFINEMENT** — Design outsourcing decision rules and provider adapters, keeping credentials and provider specifics outside Calculator truth.
9. **PROPOSED_TARGET_REFINEMENT** — Define actual-vs-norm feedback intake from Runtime Inspector as proposals that can never silently rewrite approved norms.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold implementation expansion until producer/consumer contracts, self-inventory and portfolio dependency gates are approved.

### `cloud_backup_manager`

Role: Infrastructure backup utility/reference UI shell

1. **AGREED_PLANNING_DIRECTION** — Reconcile implemented backup utility capabilities, UI shell evidence and overlap with SysAdmin.
2. **AGREED_PLANNING_DIRECTION** — Confirm current ownership of backup jobs/sources/targets/health only; no business workflow or domain truth.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for backup scheduling, retention, health, restore evidence and UI capabilities.
4. **AGREED_PLANNING_DIRECTION** — Define encryption, retention, failure reporting and restore-test expectations under SysAdmin security policy.
5. **AGREED_OR_RECOVERED_TARGET** — Define handoff of backup health and recovery evidence to SysAdmin without duplicate platform authority.
6. **AGREED_OR_RECOVERED_TARGET** — Evaluate whether its UI shell remains a reusable reference without making it the shared UI source of truth.
7. **AGREED_OR_RECOVERED_TARGET** — Compare capabilities against SysAdmin backup/PITR roadmap and identify exact duplication.
8. **PROPOSED_TARGET_REFINEMENT** — Choose KEEP, MERGE_INTO_SYSADMIN or RETIRE as a portfolio decision with migration evidence.
9. **PROPOSED_TARGET_REFINEMENT** — If kept, define narrow support-module contracts and operational health SLAs.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Do not expand implementation until the module-value decision is explicitly approved.

### `forprint_accounting_registry_service`

Role: Operational/commercial accounting registry and 1C compatibility boundary

1. **AGREED_PLANNING_DIRECTION** — Reconcile current accounting registry, 1C staging, document and supplier-automation evidence.
2. **AGREED_PLANNING_DIRECTION** — Confirm accounting ownership of accounting references/documents/reconciliation while excluding operational order and catalog truth.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for 1C snapshots, mappings, import/export/reconciliation jobs and accounting documents.
4. **AGREED_PLANNING_DIRECTION** — Define billing/customer/responsibility contexts and prevent proof/sample classifications from implying payment semantics.
5. **AGREED_OR_RECOVERED_TARGET** — Define rounding, totals, taxes/fees and reconciliation boundaries so accounting never silently changes Calculator semantics.
6. **AGREED_OR_RECOVERED_TARGET** — Plan supplier-document parsing into reviewable staging rather than direct authoritative posting.
7. **AGREED_OR_RECOVERED_TARGET** — Define payment/reconciliation views and safe conditional mandates with explicit approval and audit boundaries.
8. **PROPOSED_TARGET_REFINEMENT** — Define management-accounting and settlement projections while preserving operational/accounting truth separation.
9. **PROPOSED_TARGET_REFINEMENT** — Plan mature 1C exchange, failure recovery and evidence without allowing 1C compatibility to dominate internal architecture.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold automation expansion until operational, warehouse, calculator and identity dependencies are contractually ready.

### `forprint_contract_registry`

Role: Versioned inter-module contract lifecycle registry

1. **AGREED_PLANNING_DIRECTION** — Reconcile existing contract concepts, manifests, lifecycle states and governance references.
2. **AGREED_PLANNING_DIRECTION** — Confirm Contract Registry as lifecycle/compatibility authority, not business semantics or runtime routing authority.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for contract IDs, revisions, producer/consumer registration, fixtures and compatibility evidence.
4. **AGREED_PLANNING_DIRECTION** — Finalize lifecycle states and the rule that breaking revisions cannot become ACTIVE before mandatory consumers support them.
5. **AGREED_OR_RECOVERED_TARGET** — Use Calculator Job Specification to OCR/Prepress as the first full contract-lifecycle planning pilot.
6. **AGREED_OR_RECOVERED_TARGET** — Define adoption matrix, compatibility checks, migration metadata and Inspector evidence expectations.
7. **AGREED_OR_RECOVERED_TARGET** — Define deprecation, supported-legacy, revoked and retired handling with explicit operator/governance boundaries.
8. **PROPOSED_TARGET_REFINEMENT** — Plan generated read-only contract catalogs and projections without creating a second semantic source of truth.
9. **PROPOSED_TARGET_REFINEMENT** — Define Integration Gateway consumption of ACTIVE contracts only and prevent unilateral activation by producers or consumers.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold runtime activation until pilot evidence and portfolio dependency gates are explicitly approved.

### `forprint_crm`

Role: Unified human business cockpit, analytics and composite workflow entry point

1. **AGREED_PLANNING_DIRECTION** — Reconcile CRM dashboard, person/organization context, workflow and cross-module read-projection evidence.
2. **AGREED_PLANNING_DIRECTION** — Confirm CRM as human business cockpit/coordinator, not owner of accounting, catalog, calculation or operational registry truth.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for dashboards, operator decisions, analytics, composite workflows and context selection.
4. **AGREED_PLANNING_DIRECTION** — Define person, organization and temporal relationship views while keeping technical auth identity in IAM.
5. **AGREED_OR_RECOVERED_TARGET** — Define Customer/Supplier 360 from domain-owned projections with explicit source and write-routing boundaries.
6. **AGREED_OR_RECOVERED_TARGET** — Plan Task/Case and Exception Center workflows that coordinate domain actions without becoming a shadow operational registry.
7. **AGREED_OR_RECOVERED_TARGET** — Define universal search, saved role workspaces and activity timeline with provenance and permission-aware visibility.
8. **PROPOSED_TARGET_REFINEMENT** — Plan variance/exception analytics and configurable wallboards using reporting projections, not transactional ownership.
9. **PROPOSED_TARGET_REFINEMENT** — Define composite cross-module workflow UI with explicit commands to domain owners and audited confirmations.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold implementation expansion until IAM, operational, accounting, warehouse and logistics contracts are reconciled.
11. **AGREED_PLANNING_DIRECTION** — Define the CRM customer-intelligence model as separate Seed Profile, Observed Customer Model and Effective Policy layers without absorbing canonical client identity or foreign domain truth.
12. **AGREED_PLANNING_DIRECTION** — Define manager-selectable Seed Profiles as bootstrap presets with explicit scope, version and provenance.
13. **AGREED_PLANNING_DIRECTION** — Define the Observed Customer Model with evidence provenance, recency, confidence, domain-specific coverage and safe handling of insufficient evidence.
14. **AGREED_PLANNING_DIRECTION** — Define Effective Policy composition so approved rules may consume customer-model evidence without silently expanding financial, commercial or operational authority.
15. **AGREED_PLANNING_DIRECTION** — Implement baseline-to-shift semantics with exception, possible-shift, probable-shift and new-baseline states plus recency weighting, minimum evidence, hysteresis and contextual segmentation.
16. **AGREED_PLANNING_DIRECTION** — Define multidimensional customer health and trajectory projections using owner-sourced payment, value, growth, margin, service-burden, clarity, dispute, stability and strategic-potential evidence.
17. **AGREED_PLANNING_DIRECTION** — Define event-driven customer-model updates plus periodic reconciliation, freshness checks and explicit conflict/staleness handling.
18. **AGREED_PLANNING_DIRECTION** — Define immutable profile/policy transition history, provenance and auditable human override before customer-specific policy automation is considered mature.
19. **AGREED_PLANNING_DIRECTION** — Define CRM views for active processes, current step, blockers, waiting state, deadlines, escalations and next authorized actions from Process Manager projections.
20. **AGREED_PLANNING_DIRECTION** — Define structured operator commands for clarification, acknowledgement, override request and authorized intervention without creating shadow workflow state.

### `forprint_integration_gateway`

Role: Runtime transport validation/routing/idempotency/correlation boundary

1. **AGREED_PLANNING_DIRECTION** — Reconcile current Gateway concept and verify that no runtime need justifies premature activation.
2. **AGREED_PLANNING_DIRECTION** — Confirm Gateway owns transport validation/routing/idempotency/correlation only, never business decisions or domain truth.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for envelopes, routing rules, validation errors, idempotency and correlation contexts.
4. **AGREED_PLANNING_DIRECTION** — Bind all routing to Contract Registry ACTIVE contracts and reject unsupported revisions deterministically.
5. **AGREED_OR_RECOVERED_TARGET** — Define command/query transport boundaries, retries, deadlines, hop/loop budgets and dead-letter behavior.
6. **AGREED_OR_RECOVERED_TARGET** — Define delivery ledger and observability projections without becoming operational event truth.
7. **AGREED_OR_RECOVERED_TARGET** — Define degraded/manual-review behavior and operator-attention routing for repeated or cyclic failures.
8. **PROPOSED_TARGET_REFINEMENT** — Plan scalable routing/adapters only when concrete channel/domain traffic requires a shared gateway.
9. **PROPOSED_TARGET_REFINEMENT** — Set objective activation criteria so direct module contracts remain preferred until central routing adds value.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Remain PAUSED until runtime need and portfolio approval are explicit.
11. **AGREED_PLANNING_DIRECTION** — Define transport correlation between Gateway delivery attempts and Process Manager process/event identities without merging their state machines.
12. **AGREED_PLANNING_DIRECTION** — Keep Gateway retry/dead-letter decisions transport-scoped while business waiting, deadline and escalation truth remains in the hosted Process Manager capability.

### `forprint_identity_access_service`

Role: Shared identity/authentication/authorization/access service

1. **AGREED_PLANNING_DIRECTION** — Reconcile the new IAM concept against current module identity, CRM business-person and SysAdmin security boundaries.
2. **AGREED_PLANNING_DIRECTION** — Confirm ownership of technical accounts/auth/session/authorization while CRM retains business person/customer relationships.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for account IDs, sessions, devices, roles, permissions, overrides, recovery and audit.
4. **AGREED_PLANNING_DIRECTION** — Define account_id to CRM person_id linkage and separate selected business context from authenticated technical identity.
5. **AGREED_OR_RECOVERED_TARGET** — Define deny-by-default authorization, role baselines and per-user overrides with auditable access decisions.
6. **AGREED_OR_RECOVERED_TARGET** — Plan modern password hashing, MFA/passkeys, recovery and device/session controls.
7. **AGREED_OR_RECOVERED_TARGET** — Define SSO/shared-client boundary for web, mobile, Telegram/admin clients without duplicating business context.
8. **PROPOSED_TARGET_REFINEMENT** — Separate external partner credentials into centralized SysAdmin secrets infrastructure with least privilege and rotation.
9. **PROPOSED_TARGET_REFINEMENT** — Define admin access-review UI, security audit evidence and revocation/recovery procedures.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Keep module unimplemented until portfolio roadmap, SysAdmin and operational dependencies are approved.

### `forprint_library`

Role: Canonical semantic/catalog/reference and shared UI publication authority

1. **AGREED_PLANNING_DIRECTION** — Reconcile current Library catalog, alias, template, naming-profile and UI publication evidence.
2. **AGREED_PLANNING_DIRECTION** — Confirm Library ownership of product/material/service/operation semantics and shared UI publication, excluding business workflows.
3. **AGREED_PLANNING_DIRECTION** — Complete capability/self-inventory for canonical IDs, aliases, misspellings, production tokens, templates and technical cards.
4. **AGREED_PLANNING_DIRECTION** — Define versioned naming/profile/default semantics consumed by Calculator, Prepress and operations surfaces.
5. **AGREED_OR_RECOVERED_TARGET** — Define material/product/service canonical identifiers and stable lookup contracts for Warehouse and other consumers.
6. **AGREED_OR_RECOVERED_TARGET** — Define UI design-system package lifecycle: lookup, proposal, prototype, Inspector review, operator approval, publish and adoption.
7. **AGREED_OR_RECOVERED_TARGET** — Add version/adoption metadata and compatibility rules without creating live global CSS or uncontrolled defaults.
8. **PROPOSED_TARGET_REFINEMENT** — Plan fast capability/semantic discovery while keeping retrieval candidate-only and domain-owner truth authoritative.
9. **PROPOSED_TARGET_REFINEMENT** — Define deprecation/migration paths for legacy aliases/profiles and evidence requirements for consumer adoption.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold broader implementation until Contract Registry and consumer readiness are reconciled in the portfolio.
11. **AGREED_PLANNING_DIRECTION** — Define stable historical/reference asset metadata semantics including asset ID, source module, entity links, revision references, media type and provenance.
12. **AGREED_PLANNING_DIRECTION** — Define the boundary between Library-owned canonical reference media and customer/order/production assets owned by operational domains.

### `forprint_marketing_orchestrator`

Role: Marketing campaign/content orchestration

1. **AGREED_PLANNING_DIRECTION** — Reconcile marketing/content orchestration concept and verify separation from CRM/customer truth.
2. **AGREED_PLANNING_DIRECTION** — Confirm ownership of campaign/content planning and creative workflow with mandatory human-reviewed publication.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for briefs, content plans, asset review and campaign-performance views.
4. **AGREED_PLANNING_DIRECTION** — Define Library asset/product semantics and CRM lead/audience handoff boundaries.
5. **AGREED_OR_RECOVERED_TARGET** — Define Accounting budget/cost/performance inputs without creating marketing accounting truth.
6. **AGREED_OR_RECOVERED_TARGET** — Plan multi-channel publication adapters with explicit authorization, scheduling, rollback and audit.
7. **AGREED_OR_RECOVERED_TARGET** — Plan AI image/video/content provider routing with centralized secrets, cost budgets and human review.
8. **PROPOSED_TARGET_REFINEMENT** — Define campaign performance learning as advisory proposals rather than silent strategy mutation.
9. **PROPOSED_TARGET_REFINEMENT** — Define lead/conversion handoff to CRM with provenance and no duplicate customer history.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Remain NON-BLOCKING/FUTURE until core operational portfolio is mature and operator approves activation.

### `forprint_operations_assistant`

Role: Low-friction shop-floor assistant, guided forms and operational knowledge

1. **AGREED_PLANNING_DIRECTION** — Reconcile shop-floor assistant, SOP, guided-form, Job Ticket and observation concepts.
2. **AGREED_PLANNING_DIRECTION** — Confirm assistant as low-friction human surface, not owner of order, accounting, catalog or unbounded decision truth.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for interaction context, guided forms, procedures, operational knowledge and observation capture.
4. **AGREED_PLANNING_DIRECTION** — Define role-aware authentication/authorization through IAM and context through operational registry interfaces.
5. **AGREED_OR_RECOVERED_TARGET** — Define Job Ticket assistance, HOLD/priority/proof/reprint visibility and explicit operator confirmation boundaries.
6. **AGREED_OR_RECOVERED_TARGET** — Plan physical observation capture for equipment/material/quality events with provenance and routing to domain owners.
7. **AGREED_OR_RECOVERED_TARGET** — Define mobile/paper/QR assistance where QR identifies a job/resource but never grants permission.
8. **PROPOSED_TARGET_REFINEMENT** — Plan visual SOP/training and contextual help from Library/knowledge sources without silently inventing procedures.
9. **PROPOSED_TARGET_REFINEMENT** — Define bounded operational AI fallback with budgets, escalation and Assistant Intervention Ledger evidence.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Keep execution disabled until portfolio approval and dependent operational/identity/library contracts are ready.

### `forprint_operations_control_registry`

Role: Canonical operational party/order/task/control registry and write boundary

1. **AGREED_PLANNING_DIRECTION** — Reconcile operational order/request/task/event/party concepts, historical aliases, and the historical Operational Registry → canonical Operations Control Registry repository/layout mapping while preserving immutable historical provenance.
2. **AGREED_PLANNING_DIRECTION** — Confirm stable operational identities and the authorized operational-truth/write boundary for clients/orders/jobs/tasks/status/events, with explicit Accounting/CRM/Library/Warehouse/Logistics/Prepress exclusions and no foreign-domain semantic absorption.
3. **AGREED_PLANNING_DIRECTION** — Complete current-worktree self-inventory for business-partner references, order IDs, requests, tasks, blockers, incidents, deadlines and current documentation/status; classify the persistent core separately from next-generation foundations.
4. **AGREED_PLANNING_DIRECTION** — Define the canonical operational order/Job Ticket lifecycle, including explicit HOLD, priority, proof, reprint and exception states; reconcile OrderRecord versus OperationalOrder generation while separating order, workflow/process, production, payment-fact/projection and dictionary/reference status axes.
5. **AGREED_OR_RECOVERED_TARGET** — Define obligations, requirements, reservations, shortages and execution-context contracts with Warehouse, Accounting, Logistics and Prepress, preserving each domain's truth and making inbound fact/reference directions explicit.
6. **AGREED_OR_RECOVERED_TARGET** — Define command/query and event-contract boundaries plus outbox/inbox/idempotency/correlation rules for resilient cross-module interactions; once the project interaction-role taxonomy is canonical, distinguish semantic/domain ownership from message direction and transport/runtime state.
7. **AGREED_OR_RECOVERED_TARGET** — Define stable business-partner/person/organization/customer/billing/delivery identity and reference boundaries across Operations, CRM, IAM, Accounting and Logistics while preserving historical relationships, before promoting the rich ClientAccount foundation to canonical truth.
8. **PROPOSED_TARGET_REFINEMENT** — Define read/write interfaces used by CRM and channels without transferring ownership of operational truth.
9. **PROPOSED_TARGET_REFINEMENT** — Plan reporting projections and exception/event evidence for dashboards without making read models authoritative.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold expanded execution until Calculator/Library/Contract Registry producer dependencies and portfolio gates are ready.
11. **AGREED_PLANNING_DIRECTION** — Define the operational historical-asset link contract connecting asset references to order ID, job ID, revision and authoritative operational state.
12. **AGREED_PLANNING_DIRECTION** — Define explicit current/superseded/production-result and approval-related revision evidence required by historical asset consumers.
13. **AGREED_PLANNING_DIRECTION** — Expose operational revision/status projections for historical retrieval without transferring operational truth into the search/index layer.
14. **AGREED_PLANNING_DIRECTION** — Define the hosted Process Manager namespace and durable process-instance identity/state model inside Operations Control Registry.
15. **AGREED_PLANNING_DIRECTION** — Define current-step, waiting-condition, expected-event, timer, deadline, retry, escalation and transition semantics for long-running processes.
16. **AGREED_PLANNING_DIRECTION** — Define an append-only process transition/event ledger with correlation, idempotency, restart recovery and deterministic resume semantics.
17. **AGREED_PLANNING_DIRECTION** — Define operator-attention and authorized human-decision integration without letting unattended workflow state silently authorize foreign-domain actions.
18. **AGREED_PLANNING_DIRECTION** — Define domain adapters so CRM, Telegram, Logistics and other modules can observe or participate through typed process intents/events without owning the durable process instance.
19. **AGREED_PLANNING_DIRECTION** — Add explicit extraction-readiness criteria so the capability can later move to a standalone Process Manager service if scale, topology or ownership evidence justifies separation.

### `forprint_prepress_hub`

Role: Prepress/file preparation and production-readiness evidence

1. **AGREED_PLANNING_DIRECTION** — Reconcile current PDF/document probe, readiness and prepress planning evidence.
2. **AGREED_PLANNING_DIRECTION** — Confirm Prepress ownership of file preparation/readiness evidence, not Calculator logic, catalog truth or device identity.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for probes, requirements, blockers, corrections, profiles, imposition and production-package outputs.
4. **AGREED_PLANNING_DIRECTION** — Define consumption of accepted Calculator Job Spec and Library naming/material/profile contracts.
5. **AGREED_OR_RECOVERED_TARGET** — Specify deterministic PDF validation/correction boundaries; ambiguous semantic repair must escalate rather than guess.
6. **AGREED_OR_RECOVERED_TARGET** — Plan imposition, normalization and production profile selection with explicit evidence and reproducible fixtures.
7. **AGREED_OR_RECOVERED_TARGET** — Define hot-folder/station preset policy while concrete device identity/capability remains SysAdmin-owned.
8. **PROPOSED_TARGET_REFINEMENT** — Define HOLD/reject/readiness evidence and handoff to operational Job Ticket/QC flows.
9. **PROPOSED_TARGET_REFINEMENT** — Plan production-file provenance and future metadata projections without making filenames the source of truth.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold implementation expansion until Calculator, Library and Contract Registry dependencies are accepted.
11. **AGREED_PLANNING_DIRECTION** — Define a machine-readable technical Asset Fact Packet containing deterministic file facts, source revision, hashes and safe preview references.
12. **AGREED_PLANNING_DIRECTION** — Define deterministic fingerprint/probe outputs suitable for downstream candidate retrieval while keeping semantic match decisions outside Prepress.
13. **AGREED_PLANNING_DIRECTION** — Define historical-file provenance and master-versus-derived relationships without making Prepress the raw archive or historical search owner.

### `forprint_project_inspector`

Role: Read-only structural/semantic/conformance verification

1. **AGREED_PLANNING_DIRECTION** — Reconcile Inspector structural, semantic, cleanliness, UI and contract-conformance scope.
2. **AGREED_PLANNING_DIRECTION** — Confirm Inspector detects/report conflicts but never invents domain truth, owns architecture or mutates foreign semantics.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for repository checks, module readiness, duplicate capability, UI and document-surface conformance.
4. **AGREED_PLANNING_DIRECTION** — Define deterministic checks first: schema, generators, indexes, ownership, duplicate capabilities and contract adoption.
5. **AGREED_OR_RECOVERED_TARGET** — Define bounded semantic review only after deterministic evidence, with context limits and stable finding taxonomy.
6. **AGREED_OR_RECOVERED_TARGET** — Define checkpoint-to-commit evidence and read-only audit packages with reproducible references.
7. **AGREED_OR_RECOVERED_TARGET** — Define cleanliness pack against Document Type/Generator/Validator registries and canonical source maps.
8. **PROPOSED_TARGET_REFINEMENT** — Define periodic/risk-triggered semantic audits, including UI conformance and legal issue spotting only.
9. **PROPOSED_TARGET_REFINEMENT** — Define advisory escalation and manual resolution without automatic truth activation or foreign-repo rewrite.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold runtime-like automation until portfolio and governance acceptance criteria are satisfied.

### `forprint_strategic_control_plane`

Role: Strategic priority/status/decision-support layer

1. **AGREED_PLANNING_DIRECTION** — Reconcile whether a separate strategic control plane still adds value beyond Blueprint and CRM analytics.
2. **AGREED_PLANNING_DIRECTION** — Confirm any future role as advisory priority/status layer, not current runtime orchestration or operator override.
3. **AGREED_PLANNING_DIRECTION** — Complete a minimal self-inventory/value hypothesis before creating implementation scope.
4. **AGREED_PLANNING_DIRECTION** — Define strategic goals/priority/status inputs and provenance from Blueprint/domain reporting projections.
5. **AGREED_OR_RECOVERED_TARGET** — Define scenario analysis and KPI aggregation as advisory outputs with explicit uncertainty.
6. **AGREED_OR_RECOVERED_TARGET** — Define stale-direction challenge mechanism that proposes review without changing priorities automatically.
7. **AGREED_OR_RECOVERED_TARGET** — Define boundaries against Blueprint architecture authority, CRM operational dashboards and Accounting metrics.
8. **PROPOSED_TARGET_REFINEMENT** — Plan decision-support loops and operator review surfaces only if duplication remains acceptably low.
9. **PROPOSED_TARGET_REFINEMENT** — Run module-value test: KEEP, MERGE or RETIRE based on demonstrated unique capability.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Remain NON-BLOCKING/FUTURE until explicit portfolio decision.

### `forprint_system_administration`

Role: IT/workplace/device/data-platform/secrets administration

1. **AGREED_PLANNING_DIRECTION** — Reconcile workstation, endpoint, device, PostgreSQL, backup and secrets administration evidence.
2. **AGREED_PLANNING_DIRECTION** — Confirm SysAdmin ownership of physical IT/platform operations without owning business data semantics or workflow.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for endpoints, approved software, device identity/capabilities, DB platform, secrets and backups.
4. **AGREED_PLANNING_DIRECTION** — Define canonical device identity/model/serial/capability inventory distinct from eligible queues/groups.
5. **AGREED_OR_RECOVERED_TARGET** — Define central PostgreSQL platform operations, roles, credentials, backups/PITR and health while domain schemas retain semantic ownership.
6. **AGREED_OR_RECOVERED_TARGET** — Define centralized secrets storage, least privilege, rotation, audit and provider credential boundaries.
7. **AGREED_OR_RECOVERED_TARGET** — Reconcile Cloud Backup Manager responsibilities and decide keep/merge/retire based on capability overlap and evidence.
8. **PROPOSED_TARGET_REFINEMENT** — Plan fleet onboarding, software consistency, disk/health monitoring and administrative readiness gates.
9. **PROPOSED_TARGET_REFINEMENT** — Define admin Control Center surfaces and audited privileged actions without arbitrary remote-shell authority.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold expanded automation until Inspector/backup/platform contracts and operator security policy are approved.

### `forprint_system_blueprint`

Role: Architecture/governance/portfolio coordination

1. **AGREED_PLANNING_DIRECTION** — Reconcile all evening/morning Human Intent, handoff evidence and current canonical planning surfaces.
2. **AGREED_PLANNING_DIRECTION** — Close canonical module identity questions, including the review-only semantic retrieval candidate.
3. **AGREED_PLANNING_DIRECTION** — Lock module charters, data ownership and must-not-own boundaries across the portfolio.
4. **AGREED_PLANNING_DIRECTION** — Complete module self-inventory/self-index baselines and reusable-capability visibility.
5. **AGREED_OR_RECOVERED_TARGET** — Replace generic mature targets with module-specific current-to-target roadmaps and explicit gaps.
6. **AGREED_OR_RECOVERED_TARGET** — Reconcile producer/consumer dependencies, Contract Registry timing and dependency-constrained readiness.
7. **AGREED_OR_RECOVERED_TARGET** — Bind shared UI, IAM, PostgreSQL, anti-loop, cleanliness and Human Control Surface standards to module plans.
8. **PROPOSED_TARGET_REFINEMENT** — Run portfolio balancing/critical-path review so no assistant outruns blocked producers.
9. **PROPOSED_TARGET_REFINEMENT** — Resolve semantic conflicts and mark each roadmap step AGREED, PROPOSED, BLOCKED or REVIEW-ONLY.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Obtain explicit operator approval of the portfolio and only then prepare future assistant distribution/execution packages.
11. **AGREED_PLANNING_DIRECTION** — Define the cross-module Historical Asset Index contract over Library reference semantics, Prepress technical asset facts and Operations Control Registry order/job/revision state.
12. **AGREED_PLANNING_DIRECTION** — Define candidate retrieval stages as cheap scoped retrieval followed by deeper comparison of a small candidate set and explicit human/customer selection when ambiguity remains.
13. **AGREED_PLANNING_DIRECTION** — Resolve the final hosted-capability location only after comparing an existing-host implementation with the noncanonical Semantic Retrieval module candidate.
14. **AGREED_PLANNING_DIRECTION** — Govern the hosted Process Manager boundary so process truth, domain truth, transport state and human-facing workflow UI remain explicitly separated.
15. **AGREED_PLANNING_DIRECTION** — Review extraction triggers after real usage evidence, including independent scaling, availability, topology, ownership pressure and cross-domain coupling.

### `logistics_service`

Role: Provider-neutral shipment/pickup/delivery/tracking truth

1. **AGREED_PLANNING_DIRECTION** — Reconcile Logistics provider-neutral shipment/pickup/delivery/tracking model and existing H10 pilot evidence.
2. **AGREED_PLANNING_DIRECTION** — Confirm Logistics truth boundaries against OCR operational identities, Accounting costs and IAM access.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for shipment drafts, provider adapters, tracking events, delivery evidence and exceptions.
4. **AGREED_PLANNING_DIRECTION** — Define stable shipment/order/address references and provider-neutral command/response contracts.
5. **AGREED_OR_RECOVERED_TARGET** — Define carrier/taxi/courier adapter boundary, secrets usage, retries, idempotency and correlation.
6. **AGREED_OR_RECOVERED_TARGET** — Define pickup/delivery/tracking event lifecycle plus evidence for failures, cancellation and manual takeover.
7. **AGREED_OR_RECOVERED_TARGET** — Define cost/charge handoff to Accounting without making Logistics accounting authority.
8. **PROPOSED_TARGET_REFINEMENT** — Define delivery exception and escalation workflows with Telegram/operator attention but no hidden auto-decisions.
9. **PROPOSED_TARGET_REFINEMENT** — Evaluate the existing Logistics-only H10 automation pilot against cost, quality, retry and operator-intervention evidence.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Do not widen H10 or authorize other modules until the pilot and full portfolio are explicitly approved.
11. **AGREED_PLANNING_DIRECTION** — Define the boundary between Logistics shipment lifecycle state and a parent or linked cross-domain Process Manager instance.
12. **AGREED_PLANNING_DIRECTION** — Expose typed shipment events, waiting conditions and outcomes to Process Manager without transferring carrier/provider truth out of Logistics.

### `mobile_app`

Role: Future mobile customer/staff channel

1. **AGREED_PLANNING_DIRECTION** — Reconcile mobile-app concept against Website, Telegram and shared-domain channel architecture.
2. **AGREED_PLANNING_DIRECTION** — Confirm Mobile App as deferred client/channel with no domain truth ownership.
3. **AGREED_PLANNING_DIRECTION** — Complete a future self-inventory skeleton for auth, account, calculation, order, file, payment and delivery surfaces.
4. **AGREED_PLANNING_DIRECTION** — Define IAM/session/device security and selected business-context behavior before any client implementation.
5. **AGREED_OR_RECOVERED_TARGET** — Reuse the same Calculator, Library, OCR and delivery contracts as web instead of creating mobile-specific semantics.
6. **AGREED_OR_RECOVERED_TARGET** — Define offline/cache behavior as non-authoritative with explicit freshness/conflict handling.
7. **AGREED_OR_RECOVERED_TARGET** — Plan notifications, uploads and customer confirmations through bounded APIs and audit evidence.
8. **PROPOSED_TARGET_REFINEMENT** — Define accessibility, device compatibility, telemetry and release/security requirements.
9. **PROPOSED_TARGET_REFINEMENT** — Reassess value/timing after Website and shared API contracts mature to avoid parallel duplication.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Remain DEFERRED until explicit portfolio approval releases the channel.

### `production_runtime_inspector`

Role: Runtime production actuals/evidence and exact device-used inspection

1. **AGREED_PLANNING_DIRECTION** — Reconcile current production-inspection, device-used and actuals concepts.
2. **AGREED_PLANNING_DIRECTION** — Confirm Runtime Inspector records actual execution evidence and never owns approved norms or general project conformance.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for concrete device, operation actuals, time/material actuals, quality and telemetry evidence.
4. **AGREED_PLANNING_DIRECTION** — Bind concrete device identity/model/serial/capability to SysAdmin sources and operational jobs to OCR identities.
5. **AGREED_OR_RECOVERED_TARGET** — Define actual material/time/operation capture and provenance without inferring missing production truth.
6. **AGREED_OR_RECOVERED_TARGET** — Define quality, defect and reprint signals with routing to Warehouse/OCR and traceable cause evidence.
7. **AGREED_OR_RECOVERED_TARGET** — Define variance calculation against approved norms without modifying Calculator/Library norms.
8. **PROPOSED_TARGET_REFINEMENT** — Plan norm-change proposal generation as reviewable suggestions routed to the correct domain owner.
9. **PROPOSED_TARGET_REFINEMENT** — Plan telemetry/health integration and runtime exception evidence without becoming equipment administration authority.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold broader runtime automation until contracts, identifiers and portfolio approval are complete.

### `telegram_bot`

Role: Conversational customer/staff channel adapter

1. **AGREED_PLANNING_DIRECTION** — Reconcile current Telegram channel flows, identity/context handling and historical execution evidence.
2. **AGREED_PLANNING_DIRECTION** — Confirm Telegram as channel adapter only, never canonical CRM/order/calculation/accounting/catalog truth.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for dialog flow, message UI, uploads, confirmations and channel context.
4. **AGREED_PLANNING_DIRECTION** — Define authentication/linkage through IAM and visible customer/billing/business context selection.
5. **AGREED_OR_RECOVERED_TARGET** — Define structured calculation/order request handoff to Calculator/OCR with audited confirmations.
6. **AGREED_OR_RECOVERED_TARGET** — Define file/status/payment/delivery views as domain-owned read projections with clear freshness/provenance.
7. **AGREED_OR_RECOVERED_TARGET** — Define context switching without duplicate CRM persons/orders and without phone becoming immutable identity.
8. **PROPOSED_TARGET_REFINEMENT** — Plan voice transcription and richer interaction as bounded channel capabilities with fallback and operator visibility.
9. **PROPOSED_TARGET_REFINEMENT** — Define retry/idempotency/correlation and anti-loop budgets for channel-to-domain interactions.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold new execution until IAM, Gateway/contract and portfolio readiness gates are approved.

11. **AGREED_PLANNING_DIRECTION** — Define personalized communication orchestration with conversation continuity, approved communication preferences and strict presentation-versus-facts separation.
12. **AGREED_PLANNING_DIRECTION** — Define channel-neutral inbound structured domain requests/events and outbound structured communication intents with correlation and provenance.
13. **AGREED_PLANNING_DIRECTION** — Define consumption of customer-specific communication context without moving canonical customer profile, commercial policy or analytics into Telegram.
14. **AGREED_PLANNING_DIRECTION** — Define bounded clarification and structured Order Draft interaction using canonical Library/Calculator/domain constraints.
15. **AGREED_PLANNING_DIRECTION** — Define deterministic-to-context-to-AI-to-human escalation with replaceable model/provider slots and progress/contradiction based escalation.
16. **AGREED_PLANNING_DIRECTION** — Define Telegram consumption of historical customer asset retrieval results without live archive scanning or asset-index ownership.
17. **AGREED_PLANNING_DIRECTION** — Define Telegram as a communication participant for durable long-running business processes while process state/timers/deadlines/transitions remain with the eventual canonical Process Manager owner.

### `warehouse_service`

Role: Physical inventory/material-location truth and movement service

1. **AGREED_PLANNING_DIRECTION** — Reconcile warehouse stock, location, movement, material and defect/reprint evidence.
2. **AGREED_PLANNING_DIRECTION** — Confirm Warehouse ownership of physical inventory truth distinct from accounting valuation and Calculator planned consumption.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for stock facts, locations, lots, movements, reservations, shortages and counts.
4. **AGREED_PLANNING_DIRECTION** — Bind all stock/material records to Library canonical material IDs and controlled alias resolution.
5. **AGREED_OR_RECOVERED_TARGET** — Define receipts, issues, transfers, writeoffs and reservations against stable operational order/job references.
6. **AGREED_OR_RECOVERED_TARGET** — Define shortage and availability contracts for Calculator/OCR without letting Warehouse decide pricing or production rules.
7. **AGREED_OR_RECOVERED_TARGET** — Define internal-defect/reprint material consumption as traceable physical movements with reason/evidence.
8. **PROPOSED_TARGET_REFINEMENT** — Plan cycle counts, discrepancy workflows and audit trails with explicit human resolution.
9. **PROPOSED_TARGET_REFINEMENT** — Define Accounting handoff for valuation/documents while retaining physical quantity/location truth.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Hold automation until Library, operational registry and accounting contracts are accepted.

### `website`

Role: Customer web channel using shared Calculator/Identity/domain contracts

1. **AGREED_PLANNING_DIRECTION** — Reconcile legacy website capabilities, duplicated semantics and current channel evidence.
2. **AGREED_PLANNING_DIRECTION** — Confirm Website as customer channel using shared domain contracts, not owner of Calculator/catalog/order/accounting truth.
3. **AGREED_PLANNING_DIRECTION** — Complete self-inventory for account, calculation, order, file, payment and delivery customer surfaces.
4. **AGREED_PLANNING_DIRECTION** — Define authentication/session integration through IAM and shared business-context selection.
5. **AGREED_OR_RECOVERED_TARGET** — Replace duplicated calculation/configuration logic with Calculator contracts and Library canonical semantics.
6. **AGREED_OR_RECOVERED_TARGET** — Define order/request/status interactions through OCR rather than local shadow order truth.
7. **AGREED_OR_RECOVERED_TARGET** — Define file/prepress/payment/delivery views through accepted domain projections and explicit provenance.
8. **PROPOSED_TARGET_REFINEMENT** — Adopt Library shared UI design-system packages with versioned controlled adoption.
9. **PROPOSED_TARGET_REFINEMENT** — Plan modern self-service UX, observability, accessibility and exception handling without bypassing domain owners.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Keep implementation deferred until Calculator, IAM, Library and operational contracts are portfolio-ready.

## Proposed noncanonical review

### `forprint_semantic_retrieval_service`

Review-only. This is not a module promotion or execution plan.

1. **REVIEW_ONLY_PROPOSED_NONCANONICAL** — Reconcile the proposed semantic retrieval concept against Library, Inspector, CRM search and Blueprint capability boundaries.
2. **REVIEW_ONLY_PROPOSED_NONCANONICAL** — Run module-necessity/value test before any canonical promotion.
3. **REVIEW_ONLY_PROPOSED_NONCANONICAL** — Define candidate-only retrieval semantics: retrieval finds candidates; domain owner decides truth.
4. **REVIEW_ONLY_PROPOSED_NONCANONICAL** — Define source/index provenance, freshness and access-control requirements.
5. **REVIEW_ONLY_PROPOSED_NONCANONICAL** — Define bounded indexing/query interfaces without creating a second semantic authority.
6. **REVIEW_ONLY_PROPOSED_NONCANONICAL** — Define evaluation datasets and precision/recall acceptance evidence for realistic project queries.
7. **REVIEW_ONLY_PROPOSED_NONCANONICAL** — Define permission-aware retrieval and prevention of cross-domain data leakage.
8. **REVIEW_ONLY_PROPOSED_NONCANONICAL** — Compare implementation cost/complexity against simpler indexed lookup/search capabilities.
9. **REVIEW_ONLY_PROPOSED_NONCANONICAL** — Choose PROMOTE, MERGE or RETIRE as an explicit portfolio decision.
10. **REVIEW_ONLY_PROPOSED_NONCANONICAL** — If promoted, only then create canonical identity, ownership policy, dependencies and implementation roadmap.

<!-- project-cleanliness-conformance-2026-09-01:start -->
## Project cleanliness conformance

Project cleanliness is now a portfolio requirement for all canonical module repositories.

- Blueprint owns the single canonical cleanliness policy and current conformance projection.
- Each module owns cleanliness inside its own repository.
- Project Inspector is the future cross-repository conformance auditor, not a semantic owner.
- Blueprint local automated cleanliness checks are already implemented.
- Other module-local cleanliness packs are required/planned but are not started by this planning update.
- Inspector cross-repository automation is planned but not yet implemented.
- No module may create a competing project-wide cleanliness standard.
- Future assistant distribution requires a recorded cleanliness-conformance roadmap/state for the module.
- This planning requirement does not open implementation or assistant-distribution gates.
<!-- project-cleanliness-conformance-2026-09-01:end -->

<!-- ai-execution-safety-gate-2026-09-01 -->
## AI Execution Safety & Runtime Governance gate

Before future assistant distribution can reopen, the portfolio must review the planning gate at
`coordination/roadmaps/details/forprint_system_blueprint/ai_execution_safety_runtime_governance_gate_v0_1.md`.

Current state: `PLANNING_REQUIRED_NOT_IMPLEMENTED`.

This requirement does not authorize implementation, assistant contact, prompt activation or H10 widening.

### `verification_lab`

- Identity state: `CANONICAL`
- Strategic priority: `P0`
- Role: Independent verification, adversarial testing, fault-injection and deterministic regression evidence module.
- Module value test: `KEEP`
- Inventory state: `CONFIRMED_NEW_MODULE_NOT_IMPLEMENTED`
- Roadmap status: `PLANNING_ONLY_NOT_DISTRIBUTED`

**Dependencies / inputs**

- `forprint_system_blueprint`
- `forprint_contract_registry`
- `forprint_project_inspector`
- `forprint_system_administration`

**Owns**

- `verification_campaign_definition`
- `synthetic_test_case_corpus`
- `test_plane_scenario`
- `adversarial_test_execution`
- `deterministic_regression_corpus`
- `verification_finding_evidence`
- `release_candidate_verification_result`
- `fault_injection_profile`

**Must not own**

- `architecture_policy`
- `business_domain_truth`
- `production_runtime_control`
- `deployment_approval`
- `live_external_side_effects`
- `unrestricted_shell_authority`
- `secrets`
- `foreign_module_semantic_rewrite`

**Target state — agreed / recovered**

- Verification Lab is a distinct canonical module that intentionally tries to prove the system wrong before customers or incidents do.

**Target state — synthetic / proposed**

- Mature Verification Lab should support black/gray/white-box Test Plane campaigns, adversarial/fault/concurrency testing, deterministic regression and release-gate evidence with synthetic side effects only.

**Roadmap approval steps**

1. **AGREED_PLANNING_DIRECTION** — Establish Verification Lab canonical identity, charter and strict separation from Project Inspector and Runtime Inspector.
2. **AGREED_PLANNING_DIRECTION** — Define BLACK_BOX, GRAY_BOX and WHITE_BOX read-only diagnostic modes and their evidence boundaries.
3. **AGREED_PLANNING_DIRECTION** — Define Test Plane isolation with fake/synthetic payment, courier, printer, email, cloud, Telegram and database side effects.
4. **PROPOSED_TARGET_REFINEMENT** — Define normal/invalid/boundary/malformed/combinatorial/multilingual/out-of-domain/auth/data-isolation test taxonomy.
5. **PROPOSED_TARGET_REFINEMENT** — Define prompt-adversarial, tool-misuse, state-machine, concurrency, idempotency, stale-cache and schema-fuzz campaigns.
6. **PROPOSED_TARGET_REFINEMENT** — Define fault/recovery, timeout, unavailable-resource, retry/dead-letter, load/performance and cost-regression campaigns.
7. **PROPOSED_TARGET_REFINEMENT** — Convert useful AI-discovered failures into owner-confirmed deterministic regression corpus rather than permanent stochastic-only tests.
8. **PROPOSED_TARGET_REFINEMENT** — Define change-triggered, nightly, weekly, manual, pre-release and post-release verification campaign policy.
9. **PROPOSED_TARGET_REFINEMENT** — Define trace-aware evaluation of intermediate contract/tool/state behavior, not only final user-visible answer.
10. **HOLD_FOR_FINAL_PORTFOLIO_APPROVAL** — Remain planning-only until Test Plane, Execution Policy Gate, IAM and explicit operator distribution/implementation approval are ready.

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
