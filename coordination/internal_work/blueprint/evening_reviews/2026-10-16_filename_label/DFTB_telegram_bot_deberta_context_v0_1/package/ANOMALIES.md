# Anomalies & Open Loops

## Anomalies

### ANOM-TG1610-0001 — new_unique_micro_dialogue (normal)
No shared message IDs with master v3.3. The generic user text `deberta` appears elsewhere, but the assistant response is distinct and there is no sequence-level duplicate.

### ANOM-TG1610-0002 — filename_date_future_relative_to_export (critical)
Filename `16.10.26` is later than the 15.09.2026 MHTML export date and no internal timestamp resolves the true dialogue date.

### ANOM-TG1610-0003 — extremely_thin_owner_context (high)
The owner contributes only one word. All substantive technical content is assistant-generated educational context, so evidence strength is low for project decisions.

### ANOM-TG1610-0004 — educational_example_not_implementation (high)
The Hugging Face code example and `microsoft/deberta-v3-base` model name are illustrative only and do not prove a project dependency, code path or deployed model.

## Open loops

### LOOP-TG1610-0001
Determine current Telegram classifier/model stack from live implementation, not this educational source.
**Last known:** This source only discusses DeBERTa conceptually; later histories contain actual DeBERTa engineering evidence.
**Verify:** Use existing Telegram ML audit backlog to inspect current repo/config/model artifacts and current Blueprint policy.

### LOOP-TG1610-0002
Do not infer a three-label current schema from the assistant sample.
**Last known:** `num_labels=3` appears only in generic example code.
**Verify:** Bind label counts only to current intent/style/sentiment contracts in live code/data.

### LOOP-TG1610-0003
Keep the micro-dialogue as contextual provenance without creating a parallel ML standard.
**Last known:** Educational explanation overlaps conceptually with later Telegram ML work but adds no accepted project rule.
**Verify:** No standalone action; reference only when reconstructing why DeBERTa appears in later Telegram history.
