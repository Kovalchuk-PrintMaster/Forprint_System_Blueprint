# Anomalies & Open Loops

## Anomalies

### ANOM-TG0710-0001 — new_unique_telegram_source (normal)
No shared message IDs with clean master v3.2 and only trivial thematic overlap with the long-running Telegram source; not a near-duplicate.

### ANOM-TG0710-0002 — filename_date_future_relative_to_export (critical)
Filename `07.10.26` is later than the 15.09.2026 export. No internal timestamp proves the exact historical date.

### ANOM-TG0710-0003 — large_missing_turn_span (critical)
Visible dialogue jumps from turn 4 to 51. The missing middle exchange and attached example CSV bodies are not recoverable.

### ANOM-TG0710-0004 — early_taxonomy_conflicts_with_later_normalized_taxonomy (critical)
Early style/sentiment labels do not match the later owner-defined normalized lookup tables.

### ANOM-TG0710-0005 — synthetic_metadata_presented_as_fixed_values (high)
Response time, feedback and confidence fields are filled by convention rather than observation, risking contamination if treated as measured data.

### ANOM-TG0710-0006 — pii_in_training_ingest (critical)
Historical chat import contract includes client name, phone numbers and real conversation content; privacy/sanitization governance is absent from the source.

### ANOM-TG0710-0007 — telegram_local_master_data_risk (critical)
Generic advice about storing suppliers/products/services in Telegram-side normalized tables predates later domain ownership and could create competing master data.

### ANOM-TG0710-0008 — direct_1c_to_telegram_mirror_risk (critical)
Early 1C→Supabase/Telegram synchronization discussion predates Accounting/Gateway/Operational separation and must not be copied as current architecture.

## Open loops

### LOOP-TG0710-0001
Verify current chat-log schema and migrations against this early 20-field import contract.
**Last known:** Historical CSV contract worked through example files but those bodies are not embedded.
**Verify:** Inspect current Telegram DB migrations and known-good fixtures before reusing any early CSV generator.

### LOOP-TG0710-0002
Reconcile early style/sentiment taxonomy with later normalized Telegram lookup tables.
**Last known:** Early schema uses labels later removed/renamed.
**Verify:** Define migrations/aliases or regenerate training data against the current canonical taxonomy.

### LOOP-TG0710-0003
Audit privacy/sanitization policy for imported real customer chats and synthetic-training derivation.
**Last known:** Historical ingest includes names/phones/conversation text without explicit privacy controls.
**Verify:** Use current privacy/retention policy, de-identify training corpora where required and keep production PII out of portable fixtures.

### LOOP-TG0710-0004
Resolve current owner of supplier/product/service master data.
**Last known:** Historical Telegram discussion considers normalized local tables; later architecture separates canonical definitions and operational/accounting ownership.
**Verify:** Use current Blueprint/Library/Operational/Warehouse manifests and contracts; do not create Telegram-local canon.

### LOOP-TG0710-0005
Resolve current 1C→ForPrint→Telegram information flow.
**Last known:** Only conceptual assistant recommendations exist; no owner-approved implementation.
**Verify:** Start from current Accounting Registry/Operational Registry/Gateway contracts and identify which projections Telegram may read.

### LOOP-TG0710-0006
Recover or supersede missing known-good CSV examples if exact historical compatibility is needed.
**Last known:** Two working sample CSVs are referenced but their bodies are unavailable in MHTML.
**Verify:** Prefer current schema exports/fixtures; recover old samples only for provenance comparison.
