# Anomalies & Open Loops

## Anomalies

### ANOM-TG1210-0001 — new_unique_telegram_source (normal)
No shared message IDs, source hash or exact substantive text overlap with sources represented in clean master v2.9.

### ANOM-TG1210-0002 — filename_date_future_relative_to_export (critical)
Filename `12.10.26` is later than the MHTML save date 15.09.2026; it cannot be trusted as project chronology.

### ANOM-TG1210-0003 — schema_v1_to_v2_change (high)
Turn 1 uses textual style/sentiment columns; turn 3 normalizes them to foreign-key IDs. Current schema must not mix both shapes accidentally.

### ANOM-TG1210-0004 — unsupported_generated_style_labels (critical)
Assistant later mentions `friendly/playful` despite the supplied style table allowing only warm/formal/casual/neutral.

### ANOM-TG1210-0005 — unsupported_generated_sentiment_labels (critical)
Assistant later mentions `aggressive/urgent` despite the supplied sentiment table allowing only positive/neutral/negative.

### ANOM-TG1210-0006 — generated_count_inconsistency (high)
Historical claims total 360+500+1000=1860 rows, but assistant later calls the combined master 1800 rows.

### ANOM-TG1210-0007 — dataset_files_not_embedded (critical)
Referenced CSV artifacts are named in the chat but not embedded as recoverable files, so row-level quality/headers/uniqueness cannot be verified.

### ANOM-TG1210-0008 — csv_import_failure_root_cause_unproven (critical)
Owner reports incompatible headers, but the actual failing CSV/selected target table are missing. Assistant lists possible causes without proving one.

### ANOM-TG1210-0009 — missing_turn_span (high)
Turns 5–7 are absent. The exact prompt that produced the extra-500 dataset is not recoverable.

## Open loops

### LOOP-TG1210-0001
Verify current Telegram conversational schema and whether normalized intent/style/sentiment tables still exist.
**Last known:** Historical schema evolves from textual labels to FK-backed taxonomy tables.
**Verify:** Inspect current Telegram DB migrations/schema and enforce one canonical shape.

### LOOP-TG1210-0002
Recover or regenerate training/template datasets under strict schema validation.
**Last known:** Historical CSV bodies are unavailable and assistant descriptions contain taxonomy/count inconsistencies.
**Verify:** Use current taxonomies to regenerate or validate row-level data; reject unknown IDs/labels, duplicates and count drift.

### LOOP-TG1210-0003
Resolve the historical CSV import failure against actual current table headers.
**Last known:** One CSV failed with incompatible headers while an older file imported successfully.
**Verify:** Compare current DB schema and a known-good export; validate header bytes/BOM/delimiter and smoke-test a small import before bulk load.

### LOOP-TG1210-0004
Determine current owner of human-talk taxonomies/templates.
**Last known:** Historical tables are Telegram-local; later architecture treats Telegram as operational interface rather than canonical business truth.
**Verify:** Resolve current Blueprint/module manifests and decide Telegram-local presentation ownership versus shared Library/knowledge ownership.

### LOOP-TG1210-0005
Determine whether Mistral-7B fine-tuning remains part of current Telegram architecture.
**Last known:** Historical dataset was intended for Mistral-7B-Instruct fine-tuning and template DB use.
**Verify:** Inspect current AI runtime/model policy before investing in training data or fine-tuning.

### LOOP-TG1210-0006
Verify multilingual quality and language isolation for uk/ru/en templates.
**Last known:** Historical generation claims balanced language sets but row contents are unavailable.
**Verify:** Run language detection, grammar/style review and per-language duplicate checks on current datasets.

### LOOP-TG1210-0007
Verify current runtime selection logic for intent/style/sentiment/priority.
**Last known:** Historical storage model implies classification-driven template selection but runtime implementation is not visible.
**Verify:** Audit current Telegram response pipeline, fallback behavior, deterministic priority semantics and AI/template interaction.
