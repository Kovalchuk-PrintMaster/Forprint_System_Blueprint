# Anomalies & Open Loops

## Anomalies

### ANOM-TG1410-0001 — new_unique_telegram_source (normal)
No shared message IDs, exact substantive blocks or sequence overlap with Telegram 12.10/13.10 sources. Distinct Telegram ML-engineering history root.

### ANOM-TG1410-0002 — filename_date_future_relative_to_export (critical)
Filename `14.10.26` is later than the 15.09.2026 export. Internal artifacts instead show October 2025 timestamps.

### ANOM-TG1410-0003 — attachment_heavy_partial_source (critical)
Most turns name attached scripts/JSON/CSV/tree files but their bodies are not embedded in the visible MHTML; only user descriptions and terminal snippets survive.

### ANOM-TG1410-0004 — classifier_path_failure (high)
Historical intent classification fails because INTENT_KEYWORDS_PATH points to a missing file/path.

### ANOM-TG1410-0005 — classifier_runtime_failure_after_decoder_repair (high)
Canonical label decoder was written successfully, but classify_intent then failed with `_MODEL` undefined; one repaired layer did not imply end-to-end health.

### ANOM-TG1410-0006 — config_constant_collision (high)
Generic DEBERTA_ARCHIVE_BASE_DIR was reused across intent/style/sentiment concerns, motivating entity-specific constant naming.

### ANOM-TG1410-0007 — evaluation_script_sprawl (normal)
Multiple overlapping evaluate/audit scripts accumulated and required role clarification/deduplication.

### ANOM-TG1410-0008 — zone_identifier_worktree_pollution (normal)
Windows/VS file transfers create Zone.Identifier sidecars in the WSL/project filesystem.

### ANOM-TG1410-0009 — module_standard_vs_project_standard_scope (high)
Telegram defines a strong script/documentation standard that resembles later Blueprint doctrine, but it is not automatically project-wide authority.

## Open loops

### LOOP-TG1410-0001
Audit current Telegram ML directory structure and actual train/classify/evaluate ownership.
**Last known:** Historical code was actively being normalized and deduplicated across style/sentiment/intent.
**Verify:** Inventory current scripts and dependency graph before changing or recreating utilities.

### LOOP-TG1410-0002
Verify current label-map/decoder contract across train/classify/evaluate.
**Last known:** Historical canonical decoder repair exposed downstream runtime failure.
**Verify:** Run current end-to-end fixture from training artifact through classifier/evaluator and assert label identity.

### LOOP-TG1410-0003
Verify centralized configuration and entity-specific path constants.
**Last known:** Historical config was repeatedly refactored to remove hard-coded paths and collisions.
**Verify:** Inspect current config/.env, resolve duplicate constants and test from alternate cwd/worktree.

### LOOP-TG1410-0004
Verify current model revision/archive/promotion workflow.
**Last known:** Historical local revision manager was introduced because remote/Hugging Face versioning was problematic.
**Verify:** Determine current model registry/promotion authority and ensure revisions are immutable/reproducible.

### LOOP-TG1410-0005
Verify current datasets and model quality for intent/style/sentiment.
**Last known:** Historical style accuracy 0.6394 was considered insufficient; sentiment data was being reviewed against style results.
**Verify:** Use current labeled datasets, leakage/duplicate audits, stratified splits and current acceptance metrics.

### LOOP-TG1410-0006
Reconcile historical Telegram script standard with current Blueprint engineering standards.
**Last known:** Telegram owner standard requires self-describing scripts, config-first paths, validation, logs and artifact reporting.
**Verify:** Compare against current Blueprint coding/Make/knowledge standards; promote only non-conflicting shared rules.

### LOOP-TG1410-0007
Clean or prevent Zone.Identifier sidecars in current repository workflows.
**Last known:** Historical Windows→WSL copying produced sidecar files.
**Verify:** Check Git ignore/transfer tooling and current working tree; remove only noncanonical sidecars safely.

### LOOP-TG1410-0008
Confirm current workstation/WSL environment is irrelevant to production runtime authority.
**Last known:** Historical user-session systemd issue was resolved locally.
**Verify:** Treat workstation environment fixes as local developer support, not production module requirements unless current deployment depends on them.
