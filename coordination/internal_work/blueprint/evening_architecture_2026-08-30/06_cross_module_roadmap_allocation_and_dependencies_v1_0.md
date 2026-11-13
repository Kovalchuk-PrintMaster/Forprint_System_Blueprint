# 06. Cross-Module Roadmap Allocation & Dependencies v1.0

## forprint_system_blueprint

Add roadmap work for:
- universal assistant front door;
- bootstrap/task context bundles;
- operator profile contract;
- versioned process contract registry;
- Governance Snapshot;
- roadmap-step start/finalize evidence;
- deterministic index freshness gate;
- Inspector audit contract;
- formal proposal/adoption path for Semantic Retrieval Service.

## forprint_project_inspector

Add:
- governance snapshot verification;
- process revision status check;
- stale standard detection;
- index drift;
- completion evidence validation;
- roadmap-step conformance;
- independent reproducibility of PASS/FAIL.

## forprint_crm

Add:
- immutable person/organization IDs;
- multi-channel identifiers;
- adoption of existing phone normalization logic into canonical standard;
- identity resolution;
- dedup/merge/split;
- historical representation graph;
- order-context confirmation;
- anonymous/one-off flow.

## calculator_engine

Add:
- canonical calculation request;
- canonical order/job specification;
- manual/alternative intake normalization;
- versioned filename grammar/parser;
- ambiguity/clarification workflow;
- operation-standard consumption;
- quantity bands;
- setup/waste/time rules.

## forprint_operations_control_registry

Add:
- operational order creation;
- material reservation orchestration;
- execution gates;
- production queues;
- Job Ticket revision;
- planned vs actual operation state;
- critical event channel;
- stop-work;
- hard execution lock;
- WIP location/disposition;
- operational impact of overdue/payment state.

## forprint_operations_assistant

Add:
- queue UI;
- Job Ticket scan;
- contextual instructions;
- lightweight variance reporting;
- voice input/note;
- critical audio/visual alert;
- acknowledgement/escalation;
- product photo capture;
- Semantic Retrieval consumer UI.

## forprint_accounting_registry_service

Add:
- invoice/order linkage;
- payment policy;
- receivable lifecycle;
- due date;
- payment reconciliation;
- promise-to-pay;
- collection state machine;
- adaptive reminder policy;
- actual-cost impact from variance.

## telegram_bot

Add:
- CRM identity-resolution handoff;
- organization confirmation in order dialogue;
- collection dialogue transport;
- structured promise/dispute handoff;
- client photo → Semantic Retrieval;
- critical cancellation → OCR high-priority event;
- dialogue persistence references.

## warehouse_service

Add:
- reservation integration;
- actual consumption;
- scrap/write-off;
- product identification confirmation;
- WIP/material location where relevant;
- incoming product photo requirement support.

## forprint_library

Add:
- canonical operation/material/machine reference IDs;
- SOP text/photo/animation/video metadata;
- product aliases/reference media metadata;
- retrieval-friendly descriptors;
- explicit separation from physical inventory truth.

## forprint_system_administration

Add:
- printer/device registry;
- print routing priority;
- fallback;
- device health;
- critical local alert transport.

## Identity & Access cross-cutting capability

Add:
- printer selection permissions;
- group/user allow/deny and overrides;
- critical alert recipient role permissions;
- retrieval visibility inputs.

## forprint_integration_gateway

Add:
- bank/payment connectors;
- future email/Viber/channel adapters;
- normalized safe integration events.

## production_runtime_inspector

Add:
- machine start/stop telemetry;
- downtime;
- machine anomaly facts;
- comparison with human-reported variance.

## New candidate: forprint_semantic_retrieval_service

After formal acceptance:
- hybrid retrieval;
- text/image embeddings;
- ACL-aware search;
- candidates/confidence;
- reindex lifecycle;
- evaluation corpus;
- integrations with Assistant/Telegram/CRM/Warehouse/Library/OCR.

## Recommended dependency sequence

### Wave 1 — Governance
1. assistant bootstrap/front door;
2. context bundle contract;
3. process revision status;
4. Governance Snapshot;
5. completion attestation;
6. Inspector adoption.

### Wave 2 — Canonical customer/order foundations
7. CRM identity/representation;
8. Calculator canonical request;
9. canonical order/job specification;
10. OCR execution gates + Job Ticket revision;
11. payment-policy integration.

### Wave 3 — Production
12. queue UI;
13. print routing;
14. contextual instruction delivery;
15. stop-work/hard execution lock;
16. normative/actual production model.

### Wave 4 — Business automation
17. AR collection;
18. Telegram org confirmation/payment dialogue;
19. bank reconciliation;
20. Semantic Retrieval foundation.

### Wave 5 — Multimodal
21. product/client/order semantic retrieval;
22. image retrieval;
23. Telegram photo workflow;
24. inventory visual identification;
25. retrieval quality metrics.

## Dependency blockers

- Do not build filename parser before canonical Calculator request.
- Do not build product semantic search before canonical product/material IDs.
- Do not enable automatic production action without OCR execution permission.
- Do not enable AR AI-dialogue before structured receivable state.
- Do not treat QR as permission token.
- Do not auto-learn standards from raw variance.
