# U92 Architecture & Governance Canonical Integration — 2026-09-03

Status: **PLANNING ONLY / NOT DISTRIBUTED / NOT IMPLEMENTATION AUTHORITY**

This document is the canonical narrative bridge from the staged u92 evening package into
the Blueprint portfolio. Machine-readable authority remains in the canonical registries,
approval matrix, Human Intent ledgers and standards indexes.

Global gates remain closed:

- assistant distribution: **false**
- module implementation: **false**
- prompt activation: **false**
- H10 widening: **false**
- automatic accept/release: **false**
- cross-repository diagnostics: **false**

The canonical module set is promoted from 22 to 23 by adding `verification_lab`.
`forprint_semantic_retrieval_service` remains **PROPOSED / NONCANONICAL** and is not promoted.

Source planning evidence:
- `coordination/internal_work/blueprint/evening_packages/2026-09-03__u92/`

## website
**Role:** Public web presence, SEO entry point and conversion router; not a business-truth owner.
**AGREED / owner-confirmed direction**
- Website is the public façade and SEO entry point, not authentication, pricing, payment, cart or canonical order truth.
**PROPOSED mature refinement**
- Mature public web should maximize organic discovery and route customers into shared Calculator and Customer Portal/domain workflows.
**10-step horizon**
1. Reconcile Website strictly as public façade, SEO entry point and service discovery surface.
2. Confirm Website owns no authentication, price truth, payment truth, basket truth or canonical order state.
3. Define explicit routing from public service/product pages into Calculator, design tools and Customer Portal workflows.
4. Define crawl/index hygiene, canonical URLs, sitemap, robots and structured-data rules.
5. Define mobile-first performance and Core Web Vitals targets without duplicating native-app functionality.
6. Define service/product landing semantics from Library/Calculator truth with no local shadow catalog.
7. Define Search Console, analytics, conversion and query-to-order measurement with privacy-aware evidence.
8. Plan content freshness, internal linking and authority-building as governed marketing/website collaboration.
9. Plan organic-query → landing → calculation → customer-workflow optimization with measurable funnel evidence.
10. Keep business logic external and implementation deferred until required shared contracts are portfolio-ready.

## mobile_app
**Role:** Deferred native mobile customer/staff channel that reuses shared domain contracts.
**AGREED / owner-confirmed direction**
- Native mobile implementation remains paused until customer scale and native-only value justify it.
**PROPOSED mature refinement**
- Mature native app may provide fast calculation, orders, push, camera/QR and offline non-authoritative cache over shared APIs.
**10-step horizon**
1. Keep Mobile App in PAUSED/PROPOSED planning state and define measurable activation triggers.
2. Use responsive/mobile-first web and shared Customer Portal capabilities as the present customer-mobile baseline.
3. Define future native client as a channel only, with no local domain-truth ownership.
4. Define IAM/session/device security and shared selected business-context behavior before native implementation.
5. Plan fast Calculator and basket/order composition over the same contracts used by web.
6. Define offline cache/estimate behavior as non-authoritative and requiring server revalidation before commitment.
7. Plan push notifications and customer confirmations through audited shared messaging/event contracts.
8. Plan camera, QR and file-upload capabilities without making QR a permission mechanism.
9. Plan unified conversation/history through shared CRM/communication services rather than mobile-only shadow state.
10. Authorize native implementation only after usage, client-base and native-value evidence clears the portfolio gate.

## forprint_system_administration
**Role:** Recovery-first technical operations, device, endpoint, data-platform, secrets and offline-continuity administration.
**AGREED / owner-confirmed direction**
- SysAdmin is the recovery-first technical operations helper and may integrate with voice/mobile/Telegram through bounded interfaces.
**PROPOSED mature refinement**
- Mature SysAdmin should manage known-good endpoint state, software/driver lifecycle, recovery artifacts, diagnostics and bounded technical actions with offline continuity.
**10-step horizon**
1. Reconcile device, endpoint, PostgreSQL, secrets, backup and recovery responsibilities into one technical-operations boundary.
2. Confirm SysAdmin owns technical platform/device administration but not business workflow or domain semantics.
3. Define stable device inventory, discovery and capability evidence distinct from concrete job assignment.
4. Define known-good workstation/device configuration profiles and drift evidence.
5. Define corporate software/workspace/plugin deployment packs while domain owners retain semantic ownership of business resources.
6. Define stable/pinned driver lifecycle, rollback and compatibility evidence rather than uncontrolled latest-driver upgrades.
7. Define recovery images/snapshots, offline artifact bank and restore procedures with measurable evidence.
8. Integrate Operations Assistant/voice/Telegram as human entry surfaces to bounded SysAdmin capabilities.
9. Define diagnostics and approved-manual troubleshooting with no invented repair procedures or arbitrary shell authority.
10. Hold broad autonomous IT actions until IAM, Execution Policy Gate, Verification Lab and operator approval criteria are satisfied.

## cloud_backup_manager
**Role:** Off-site backup, controlled one-way corporate-resource replication and recovery-evidence support service.
**AGREED / owner-confirmed direction**
- Cloud Backup Manager covers off-site backup, controlled one-way corporate-resource replication and retention/integrity/recovery evidence.
**PROPOSED mature refinement**
- Mature backup operation should be provider-neutral, encrypted, checksum-verified, restore-tested and resilient to temporary network loss.
**10-step horizon**
1. Reconcile implemented backup utility capabilities and exact overlap with SysAdmin platform operations.
2. Confirm Cloud Backup Manager owns backup/replication jobs and recovery evidence, not business data semantics.
3. Define domain-owned prepared-artifact backup inputs with explicit source ownership and provenance.
4. Define one canonical publisher → many consumers replication for approved corporate resources without overwriting user areas.
5. Define retention, versioning/immutability options, encryption, checksum and centralized secret requirements.
6. Define RPO/RTO objectives and periodic restore verification as first-class acceptance evidence.
7. Define provider abstraction, quota/health reporting and safe credential rotation boundaries.
8. Define persistent offline queue/retry so temporary internet loss becomes WAITING/RETRY, never silent loss.
9. Define bandwidth scheduling, retry backoff, alerts and degraded-mode behavior.
10. Reassess KEEP versus merge into SysAdmin only after capability overlap and migration evidence are explicit.

## forprint_integration_gateway
**Role:** Narrow-waist transport, schema/version routing, idempotency, correlation and delivery-state boundary.
**AGREED / owner-confirmed direction**
- Gateway owns transport/contract mechanics, not domain truth or business decisions.
**PROPOSED mature refinement**
- Mature Gateway should expose explicit queue/busy/retry/degraded outcomes, backpressure, deadlines, circuit breaking and dead-letter evidence.
**10-step horizon**
1. Reconcile Gateway as narrow-waist transport and contract-validation infrastructure only.
2. Confirm no domain truth, pricing, customer, accounting or workflow-decision ownership.
3. Bind routing to supported Contract Registry revisions and reject unsupported revisions deterministically.
4. Define request envelopes, idempotency keys, correlation/causation and persistent delivery-state ledger semantics.
5. Define shared outcomes OK/QUEUED/BUSY_RETRYABLE/TEMPORARILY_UNAVAILABLE/TIMEOUT/CONFLICT/NOT_FOUND/PERMISSION_DENIED/FAILED_PERMANENT.
6. Define WAITING_RESOURCE/WAITING_EXTERNAL_DEPENDENCY/RETRY_SCHEDULED and distinguish temporary unavailability from not-found.
7. Define bounded retries, exponential backoff, deadlines/TTL, circuit breaker, dead-letter and manual-review escalation.
8. Define backpressure/resource-queue behavior while domain owners retain transactional concurrency decisions.
9. Define observability projections without becoming operational event truth.
10. Remain PAUSED until concrete runtime traffic and portfolio approval demonstrate shared Gateway value.

## production_runtime_inspector
**Role:** Runtime execution evidence, actuals, device-used, queue/retry/health and AI/tool-cost telemetry observer.
**AGREED / owner-confirmed direction**
- Runtime Inspector records facts and actuals but never silently rewrites approved norms.
**PROPOSED mature refinement**
- Mature runtime inspection should trace retries, waiting states, dead letters, AI/tool usage, latency, cost and deployment/canary evidence.
**10-step horizon**
1. Reconcile runtime execution, device-used and actuals evidence scope.
2. Confirm Runtime Inspector observes facts but owns neither approved norms nor architecture policy.
3. Define end-to-end request/job trace identifiers across queue, tool, AI and external dependencies.
4. Define WAITING/RETRY/DEGRADED/dead-letter/stuck-work evidence and detection.
5. Define AI/tool telemetry: calls, repetitions, tokens, latency, cost, retries and escalation counts.
6. Define budget-runway and abnormal-cost signals without autonomously changing business strategy.
7. Define actual-vs-standard variance evidence and proposal-only norm-change feedback.
8. Define deployment/shadow/canary runtime evidence consumed by Verification Lab and release decisions.
9. Define privacy/retention boundaries: execution evidence, not hidden chain-of-thought capture.
10. Hold any active control-loop behavior until bounded autonomy and portfolio gates are explicitly approved.

## forprint_project_inspector
**Role:** Read-only structural, semantic, cleanliness, architecture and governance conformance verification.
**AGREED / owner-confirmed direction**
- Project Inspector detects drift/conflicts/duplication candidates but never invents or activates domain truth.
**PROPOSED mature refinement**
- Mature Inspector should verify dev/runtime boundary, module maturity, autonomy evidence and intake Verification Lab findings as conformance evidence.
**10-step horizon**
1. Reconcile Project Inspector scope against Blueprint, Runtime Inspector and Verification Lab.
2. Confirm Inspector is read-only conformance authority and not an adversarial test executor or domain owner.
3. Define deterministic checks first: schema, generators, indexes, ownership, cleanliness and contract adoption.
4. Define duplicate/equivalent-capability candidate detection with owner-reviewed dispositions and no auto-delete.
5. Define module current-state, roadmap, maturity M0-M9 and dependency-constrained readiness conformance.
6. Define DEV/VERIFICATION/RELEASE/RUNTIME separation and immutable-runtime conformance checks.
7. Define bounded semantic review after deterministic evidence with stable finding taxonomy.
8. Define periodic/risk-triggered review and checkpoint-to-commit evidence packages.
9. Ingest Verification Lab results as evidence while leaving intentional test generation to Verification Lab.
10. Keep foreign-repo mutation, truth activation and autonomous deletion forbidden.

## forprint_strategic_control_plane
**Role:** Long-horizon business decision intelligence, scenario analysis and strategy-memory plane.
**AGREED / owner-confirmed direction**
- Strategic Control Plane supports long-horizon quantified human decisions rather than acting as an autonomous strategic executor.
**PROPOSED mature refinement**
- Mature capability should maintain strategic objectives/KPIs, economics/capacity/market intelligence, scenarios, investment cases and forecast→decision→actual memory.
**10-step horizon**
1. Reconcile Strategic Control Plane as decision intelligence, not dashboard duplication or operational control.
2. Confirm strategic recommendations remain human decisions and do not directly mutate operational truth.
3. Define strategic objectives registry and structured KPI catalog with provenance.
4. Define product/customer economics, capacity, bottleneck and investment evidence inputs from domain owners.
5. Define external market/search/competitor intelligence as sourced evidence, never invented fact.
6. Define scenario engine with assumptions, uncertainty, risk and sensitivity.
7. Define investment cases and measurable expected return/capacity/quality effects.
8. Define strategy memory linking forecast → recommendation → human decision → actual outcome.
9. Define monthly refresh, quarterly deep review, annual rebaseline and event-triggered recalculation cadence.
10. Keep autonomous execution forbidden; mature output is quantified options and evidence for operator decisions.

## forprint_marketing_orchestrator
**Role:** Brand, campaign and content operations orchestration with human-governed publication.
**AGREED / owner-confirmed direction**
- Marketing Orchestrator is a distinct Brand & Content Operations capability, not merely a post generator and not CRM/customer truth.
**PROPOSED mature refinement**
- Mature capability may orchestrate cross-channel campaigns, AI creative routing, brand-character consistency, reuse, analytics and bounded low-risk auto-publication.
**10-step horizon**
1. Reconcile Marketing Orchestrator as brand/content operations distinct from CRM and Website ownership.
2. Confirm product/customer/accounting truth always comes from domain owners.
3. Define brand system, tone, visual rules and Brand Character Bible for persistent mascot/spokescharacter consistency.
4. Define website visual/content audit and handoff with Website/Prepress/Library.
5. Define multi-channel campaign plan, editorial calendar and reusable content asset lifecycle.
6. Define short-form image/video/content generation with provider abstraction, centralized secrets and cost budgets.
7. Define publication maturity DRAFT_ONLY → HUMAN_APPROVAL_REQUIRED → bounded low-risk auto-publish.
8. Define provenance, rollback and audit for all external publication.
9. Define campaign performance learning as advisory proposals and CRM lead/conversion handoff without duplicate customer history.
10. Remain non-blocking/future until core operations mature and operator explicitly approves activation.

## forprint_operations_assistant
**Role:** Low-friction human entry point for guided operational and bounded technical assistance.
**AGREED / owner-confirmed direction**
- Operations Assistant is a human entry surface and may route technical requests to SysAdmin without becoming technical-system authority.
**PROPOSED mature refinement**
- Mature capability may support voice/mobile/Telegram entry, fuzzy intent resolution, role-aware SOPs and bounded tool invocation.
**10-step horizon**
1. Reconcile shop-floor assistant, SOP, guided form, Job Ticket and technical-help entry responsibilities.
2. Confirm Operations Assistant owns interaction context, not operational/order/accounting/technical platform truth.
3. Define role-aware guided forms, SOP discovery and visual instruction flows.
4. Define voice/mobile/Telegram entry as optional interfaces to the same bounded interaction model.
5. Define fuzzy intent/entity resolution with deterministic confirmation before sensitive action.
6. Define routing of technical requests to SysAdmin capabilities and business requests to domain owners.
7. Define IAM-aware capability checks and Execution Policy Gate before any tool side effect.
8. Define low-friction reprint/exception/observation capture with provenance.
9. Define bounded operational AI with repeat/hop/budget/manual-review limits.
10. Keep autonomous high-impact action disabled until Verification Lab and portfolio gates pass.

## calculator_engine
**Role:** Canonical production calculation, quote-item semantics and production-filename interpretation engine.
**AGREED / owner-confirmed direction**
- Calculator owns calculated quote/item semantics and production filename interpretation, not the whole customer basket or order.
**PROPOSED mature refinement**
- Mature Calculator should expose deterministic contracts, offline estimate rules with revalidation and Verification Lab regression surfaces.
**10-step horizon**
1. Preserve Calculator ownership of calculation, quote-item and production-filename semantics.
2. Keep Library as vocabulary/profile source and avoid local shadow aliases/defaults.
3. Separate calculated item/quote from CRM basket/checkout and OCR canonical operational order state.
4. Define stable request/result contracts with provenance, assumptions and deterministic rounding rules.
5. Define offline estimate behavior where allowed and mandatory server/current-norm revalidation before commitment.
6. Define deterministic filename correction only for unambiguous cases and retain source/provenance.
7. Define Prepress capability/probe handoff without Calculator owning file-repair execution.
8. Provide deterministic fixtures and boundary cases to Verification Lab for regression.
9. Use Runtime Inspector actuals only as proposal evidence for norm changes, never silent rewrite.
10. Hold broader automation until Library/Contract Registry/consumer adoption evidence is portfolio-ready.

## forprint_crm
**Role:** Business workflow coordinator, Customer Portal composition layer and cross-domain human workspace.
**AGREED / owner-confirmed direction**
- CRM may compose Customer Portal and basket/checkout workflow while domain-owned semantics remain with their actual owners.
**PROPOSED mature refinement**
- Mature CRM should provide customer/supplier 360, exception/task workspaces, universal search, timeline and cross-domain projections without absorbing foreign truth.
**10-step horizon**
1. Reconcile CRM as business coordinator and human workspace rather than physical owner of all ForPrint data.
2. Preserve person/organization/context semantics and phone as strong identifier/search aid, not immutable identity.
3. Define Customer Portal composition with shared IAM and selected business context.
4. Define basket/checkout orchestration around Calculator quote items without creating calculator or accounting truth.
5. Define request/order handoff through Operations Control Registry with stable operational identifiers.
6. Define payment/accounting/logistics/warehouse views through owner-provided projections and explicit provenance.
7. Define Task/Case/Exception Center and role-specific workspaces as CRM-owned workflow composition.
8. Define universal search/timeline/customer-supplier 360 over read models without cross-domain write ownership.
9. Define analytics/variance views while strategic recommendation ownership remains with Strategic Control Plane.
10. Keep cross-domain writes contract-bound and dependency-gated before assistant distribution.

## forprint_system_blueprint
**Role:** Portfolio architecture, ownership, governance, roadmap/dependency balancing and release/distribution gate authority.
**AGREED / owner-confirmed direction**
- Blueprint must formalize managed autonomy, Verification Lab, development/runtime separation and a common module maturity path before future distribution.
**PROPOSED mature refinement**
- Mature Blueprint should reduce human control to a small number of portfolio/exception/approval surfaces while preserving explicit high-impact authority.
**10-step horizon**
1. Integrate u92 architecture decisions into Human Intent, canonical portfolio roadmaps and governance without opening implementation.
2. Promote Verification Lab to canonical module identity while Semantic Retrieval remains proposed/noncanonical.
3. Formalize DEV → VERIFICATION → RELEASE → RUNTIME separation and immutable-runtime/self-evolution rules.
4. Formalize M0-M9 module maturity and production-entry sequence for all future modules.
5. Formalize shared resource concurrency/availability states, retry/backpressure/dead-letter semantics.
6. Formalize Execution Policy Gate, capability-shaped tools and risk-class authorization.
7. Formalize managed-autonomy levels, context checkpoint/handoff and AI budget-runway evidence.
8. Strengthen dependency-constrained readiness and assistant-distribution prerequisites using the 23-module canonical set.
9. Require Verification Lab and Project Inspector evidence before production promotion while keeping their roles separate.
10. Keep assistant distribution, module implementation, H10 widening and automatic acceptance closed until explicit operator approval.

## verification_lab
**Role:** Independent verification, adversarial testing, fault-injection and deterministic regression evidence module.
**AGREED / owner-confirmed direction**
- Verification Lab is a distinct canonical module that intentionally tries to prove the system wrong before customers or incidents do.
**PROPOSED mature refinement**
- Mature Verification Lab should support black/gray/white-box Test Plane campaigns, adversarial/fault/concurrency testing, deterministic regression and release-gate evidence with synthetic side effects only.
**10-step horizon**
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
