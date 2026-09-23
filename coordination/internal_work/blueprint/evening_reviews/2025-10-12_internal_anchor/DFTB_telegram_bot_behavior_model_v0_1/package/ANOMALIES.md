# Anomalies & Open Loops

## Anomalies

### ANOM-TG1210B-0001 — new_unique_source_with_embedded_overlap (high)
No shared message IDs with master v3.4. Nineteen exact text fragments overlap the long-running Telegram root because turn 1 embeds prior dialogue/scaffold; sequence similarity is ~0.8%, so this is not a re-export/near-duplicate.

### ANOM-TG1210B-0002 — filename_year_wrong (critical)
Filename says `12.10.26`, but MHTML was exported 15.09.2026 and embedded scaffold is explicitly dated 2025-10-12. Logical chronology uses the internal 2025 anchor.

### ANOM-TG1210B-0003 — voice_transcript_gaps (high)
Several turns are `Transcript Unavailable`, `No transcription available` or corrupted automatic-transcription fragments. Missing voice content is not reconstructed.

### ANOM-TG1210B-0004 — voice_text_sync_failure (high)
The dialogue repeatedly shows failed or over-broad summaries of recent voice instructions, causing the owner to define exact latest-dialogue-only reporting.

### ANOM-TG1210B-0005 — chat_history_memory_overclaim (high)
Assistant repeatedly claims to remember/review prior file structure, then later states it cannot directly retrieve the needed history/file name.

### ANOM-TG1210B-0006 — broad_ai_tool_authority_risk (critical)
Historical personal-assistant vision implies broad email/file/cloud/computer actions. Without explicit permission and audit boundaries this would exceed safe module authority.

### ANOM-TG1210B-0007 — direct_1c_write_scope_drift (critical)
Early owner goal speaks of Telegram directly performing 1C order/material operations, which later architecture routes through Accounting/1C adapters and governance.

### ANOM-TG1210B-0008 — dynamic_test_generation_without_oracle (critical)
Fresh LLM-generated test inputs solve staleness only partially; without independent expected labels and leakage controls the automated score can be misleading.

### ANOM-TG1210B-0009 — time_sensitive_provider_claims (normal)
Assistant statements about external LLM providers/free tiers/costs are historical and time-sensitive, not durable architecture facts.

## Open loops

### LOOP-TG1210B-0001
Verify current behavior-model source of truth and whether embedded YAML/state/feedback scaffolds still exist.
**Last known:** Behavior scaffold is embedded in historical chat with internal 2025-10-12 date; not current repo evidence.
**Verify:** Inventory current Telegram behavior specifications/generators/runtime and classify old YAML scaffolds as active, generated, archival or superseded.

### LOOP-TG1210B-0002
Verify current voice→text reporting/continuity workflow if still needed for operator coordination.
**Last known:** Owner required latest-voice-only compact reports because chat/voice synchronization was unreliable.
**Verify:** Use durable project memory/assistant handoff surfaces rather than relying on implicit voice-chat memory.

### LOOP-TG1210B-0003
Define current Mentor/AI escalation contract, permissions, context scope and fallback.
**Last known:** Owner wants ambiguous cases escalated with sufficient context instead of guessed answers.
**Verify:** Resolve current AI/Operations architecture, least-privilege context contract, logging, timeout/fallback and human approval boundaries.

### LOOP-TG1210B-0004
Resolve current tool-enabled personal-assistant architecture for email/files/cloud/computer actions.
**Last known:** Historical ambition is broad Telegram-mediated routine automation.
**Verify:** Map allowed tools/connectors, credentials, approval levels, audit log and separation between personal-assistant capability and customer-facing Telegram runtime.

### LOOP-TG1210B-0005
Resolve Telegram→Accounting/1C action boundary.
**Last known:** Owner wants routine accounting actions automated; later project architecture separates Accounting/1C authority.
**Verify:** Use current Accounting Registry/Gateway/decision-right contracts and prohibit direct Telegram ownership of accounting truth.

### LOOP-TG1210B-0006
Verify current sales/objection taxonomy and behavior ownership.
**Last known:** Owner wants sales/refusal/objection behavior represented in classifier/routing semantics.
**Verify:** Reconcile with current Telegram/CRM/marketing/customer-journey architecture and current taxonomy tables.

### LOOP-TG1210B-0007
Verify modular multi-dataset training architecture.
**Last known:** Owner prefers specialized domain datasets combined into training rather than one monolithic table.
**Verify:** Inspect current dataset registry, lineage, train/val/test split and domain weighting/merging pipeline.

### LOOP-TG1210B-0008
Design current recurring ML evaluation with fresh cases and an independent oracle.
**Last known:** Owner rejects static/rotation-only testing and wants fresh unseen automated evaluation cases.
**Verify:** Create versioned evaluation pools with provenance, hidden holdouts, expected-label oracle/reviewer path, leakage checks and promotion thresholds before retraining.
