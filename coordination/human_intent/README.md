# ForPrint Human Intent Ledger

This directory preserves the human meaning behind roadmap and architecture decisions.

## Core rule

Human-intent entries are append-only planning/governance context.

- New intent is appended.
- Changed intent supersedes an older intent; it does not silently erase it.
- Roadmap steps should carry `human_intent_refs` whenever a human discussion materially defines design intent.
- Expanded human portfolio documents are projections of this ledger, not release authority.
- Missing exact details are recorded as `GAP`; assistants must not invent them.

## Mandatory output after a substantial architecture / evening review

1. technical integration package;
2. Human Intent Delta by module;
3. updated append-only module ledgers;
4. regenerated expanded human portfolio;
5. explicit GAP list.

## Status semantics

- `AGREED`: explicitly agreed or reconfirmed.
- `RECOVERED`: recovered from existing project / portfolio evidence.
- `PROPOSED`: synthesis for review; not yet agreed.
- `GAP`: known missing exact detail that must be recovered instead of guessed.

## Source of truth boundary

This ledger preserves design intent. It does not replace:
- release authority;
- module contracts;
- canonical business data;
- implementation source code;
- completion evidence.

Current initial ledger snapshot: `index.yaml`.

## Module intent ledgers

These links are the canonical navigation surface for the per-module human-intent ledgers.

- [ForPrint System Blueprint](modules/forprint_system_blueprint.yaml) — 13 captured human-intent entries.
- [Calculator Engine](modules/calculator_engine.yaml) — 13 captured human-intent entries.
- [ForPrint Operations Assistant](modules/forprint_operations_assistant.yaml) — 11 captured human-intent entries.
- [ForPrint Operations Control Registry](modules/forprint_operations_control_registry.yaml) — 10 captured human-intent entries.
- [ForPrint CRM](modules/forprint_crm.yaml) — 8 captured human-intent entries.
- [ForPrint Accounting Registry Service](modules/forprint_accounting_registry_service.yaml) — 8 captured human-intent entries.
- [ForPrint Semantic Retrieval Service (PROPOSED)](modules/forprint_semantic_retrieval_service.yaml) — 9 captured human-intent entries.
- [Telegram Bot](modules/telegram_bot.yaml) — 7 captured human-intent entries.
- [Website](modules/website.yaml) — 7 captured human-intent entries.
- [Mobile App](modules/mobile_app.yaml) — 5 captured human-intent entries.
- [ForPrint Library](modules/forprint_library.yaml) — 8 captured human-intent entries.
- [ForPrint Prepress Hub](modules/forprint_prepress_hub.yaml) — 6 captured human-intent entries.
- [Warehouse Service](modules/warehouse_service.yaml) — 6 captured human-intent entries.
- [Production Runtime Inspector](modules/production_runtime_inspector.yaml) — 5 captured human-intent entries.
- [ForPrint Project Inspector](modules/forprint_project_inspector.yaml) — 6 captured human-intent entries.
- [ForPrint Strategic Control Plane](modules/forprint_strategic_control_plane.yaml) — 5 captured human-intent entries.
- [ForPrint Integration Gateway](modules/forprint_integration_gateway.yaml) — 5 captured human-intent entries.
- [Logistics Service](modules/logistics_service.yaml) — 5 captured human-intent entries.
- [ForPrint System Administration](modules/forprint_system_administration.yaml) — 5 captured human-intent entries.
- [ForPrint Contract Registry](modules/forprint_contract_registry.yaml) — 5 captured human-intent entries.
- [ForPrint Marketing Orchestrator](modules/forprint_marketing_orchestrator.yaml) — 5 captured human-intent entries.
- [Cloud Backup Manager](modules/cloud_backup_manager.yaml) — 5 captured human-intent entries.
