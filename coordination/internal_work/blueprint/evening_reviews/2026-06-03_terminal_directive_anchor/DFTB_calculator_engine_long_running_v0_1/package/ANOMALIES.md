# Anomalies & Open Loops

## Anomalies

### ANOM-CALC0910-0001 — new_unique_calculator_source (normal)
No shared message IDs, source hash or exact substantive message overlap with dialogue sources represented in clean master v2.8.

### ANOM-CALC0910-0002 — filename_date_future_relative_to_export (critical)
Filename says `09.10.26`, but the MHTML was saved on 2026-09-15. Internal evidence also includes 2025 artifacts and a 2026-06-03 Blueprint directive. Filename is not a trustworthy chronology endpoint.

### ANOM-CALC0910-0003 — imported_prior_dialogue_embedded_in_single_user_turn (high)
Turn 3 embeds a large prior ChatGPT conversation. Owner statements inside it are useful secondary historical evidence but have weaker provenance than direct turns in this export.

### ANOM-CALC0910-0004 — sparse_partial_export (high)
206 visible turn sections span turn numbers 1–1151, with many missing turns and attachment-only placeholders. Several Blueprint prompts and implementation steps are not recoverable.

### ANOM-CALC0910-0005 — calculator_admin_scope_overreach (critical)
Historical owner intent briefly treats the Calculator admin as a possible admin framework for the whole project, conflicting with later Blueprint module boundaries.

### ANOM-CALC0910-0006 — local_catalog_vs_library_canonical_authority (critical)
Historical Calculator builds local catalog/reference tables before later Library/Calculator Input Contract authority. Healthy historical implementation must not be mistaken for current canonical ownership.

### ANOM-CALC0910-0007 — direct_channel_coupling_vs_gateway_contract_architecture (critical)
Historical Website/Telegram intake assumptions may bypass later Gateway/Contract Registry/CRM boundaries if copied literally.

### ANOM-CALC0910-0008 — idempotency_test_state_leak_candidate (high)
A visible run reports 1 failed/35 passed because the first idempotent request was already marked reused, suggesting persistent state or test-isolation drift at that point.

### ANOM-CALC0910-0009 — blueprint_directive_sync_silent_schema_mismatch (critical)
Sync command could report OK/no-new-items while parsing the wrong index shape, a dangerous false-success pattern for coordination.

### ANOM-CALC0910-0010 — coordination_tool_cwd_dependency (high)
Historical coordination checks/importers depended on being run from repository root instead of resolving repository identity independently.

### ANOM-CALC0910-0011 — historical_terminal_pause_not_current_state (critical)
Commit `eba5384` and controlled pause are strong historical evidence but cannot be treated as current Calculator state without a live repository audit.

## Open loops

### LOOP-CALC0910-0001
Audit current Calculator repository identity, branch/HEAD and whether historical `eba5384` remains in ancestry.
**Last known:** Historical terminal output shows `eba5384` on local and origin main with controlled pause.
**Verify:** Resolve current repo path, remote, branch, exact HEAD, worktree and current Blueprint release before any execution.

### LOOP-CALC0910-0002
Reconcile Calculator local catalog/admin tables with Library canonical references and Calculator Input Contract.
**Last known:** Historical Calculator had rich local product/material/admin models; later Blueprint explicitly permits only temporary local catalog and Library owns canonical definitions/contracts.
**Verify:** Map current Library contract/catalog authority, Calculator local projections/cache and migration ownership; remove duplicate canon.

### LOOP-CALC0910-0003
Verify current quote/external intake contracts, idempotency, errors and report schemas.
**Last known:** Historical API produced structured quote/error/report responses but had at least one idempotency test-state failure.
**Verify:** Run current contract/focused tests in isolated storage and compare with current Contract Registry/Gateway agreements.

### LOOP-CALC0910-0004
Resolve current Website/Telegram/mobile routing boundary into Calculator.
**Last known:** Historical owner wants reusable multi-channel Calculator; later architecture adds Gateway/CRM/Contract Registry boundaries.
**Verify:** Resolve current end-to-end route and versioned contracts; prevent direct channel-specific coupling inside Calculator.

### LOOP-CALC0910-0005
Verify current centralized path/configuration and cwd-independent command behavior.
**Last known:** Historical repo adopted centralized paths but coordination tooling still exposed cwd-sensitive behavior.
**Verify:** Run current path/config/clean-room checks from multiple working directories and verify project-relative portability.

### LOOP-CALC0910-0006
Verify current DB backup/restore and Alembic/Django schema ownership.
**Last known:** Historical design uses Alembic for schema and unmanaged Django projections; restore tooling reports scope/outcome.
**Verify:** Inspect current migrations/admin models/restore utilities and exercise non-destructive fixtures.

### LOOP-CALC0910-0007
Verify Telegram operational-alert design without coupling Calculator to Telegram as canonical transport.
**Last known:** Owner wants immediate Telegram conflict summaries plus detailed server logs.
**Verify:** Determine current alerting/Operations Assistant/Gateway ownership and emit events/alerts through approved observability path.

### LOOP-CALC0910-0008
Standardize Blueprint module-directive index schema and importer validation across modules.
**Last known:** Calculator parser had to learn `module_directives.active` after false-success/no-import behavior.
**Verify:** Audit current Blueprint schema/validators and all module importers; fail loudly on unsupported shape instead of silently reporting success.

### LOOP-CALC0910-0009
Locate or supersede missing Blueprint prompt bodies in sparse turns 1022–1147.
**Last known:** Owner references clarification/new prompts, but visible attachment bodies are absent.
**Verify:** Use current Blueprint release/history rather than reconstructing missing prompts from guesses.
