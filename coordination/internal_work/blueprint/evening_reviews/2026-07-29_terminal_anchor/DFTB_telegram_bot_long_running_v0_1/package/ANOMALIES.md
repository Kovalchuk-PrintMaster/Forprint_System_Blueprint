# Anomalies & Open Loops

## Anomalies

### ANOM-TG1310-0001 — new_unique_telegram_source (normal)
No shared message IDs or exact role+normalized-text overlap with the prior Telegram 12.10 source; distinct long-running Telegram root.

### ANOM-TG1310-0002 — filename_date_future_relative_to_export (critical)
Filename `13.10.26` is later than the MHTML export date 15.09.2026. Terminal governance packet is dated 2026-07-29; filename is not chronology authority.

### ANOM-TG1310-0003 — sparse_long_running_export (high)
144 retained turn sections span 1–920 with many missing turns and attachment-only messages. Missing file/prompt bodies are not reconstructed.

### ANOM-TG1310-0004 — behavior_phase_drift (high)
Development drifted into classifier/runtime tuning before owner reset stage one to behavior-model design. Current roadmap should preserve the phase boundary rather than repeat the detour.

### ANOM-TG1310-0005 — path_and_nonexistent_file_drift (high)
Historical testing work created references to nonexistent directories/scripts before owner correction to actual package structure/config paths.

### ANOM-TG1310-0006 — tool_false_success_candidate (high)
Seed patcher claimed success although owner observed no workbook changes, showing need for artifact-level postcondition checks.

### ANOM-TG1310-0007 — telegram_logistics_scope_overreach (critical)
Early behavior registry includes delivery/provider execution concepts that later belong to Logistics service. Telegram may collect preference and communicate status but should not own provider execution.

### ANOM-TG1310-0008 — telegram_client_card_canonical_ownership_risk (critical)
Client qualification/card enrichment in Telegram can be mistaken for CRM/Operational Registry canonical ownership.

### ANOM-TG1310-0009 — blueprint_pull_external_blocker (high)
Blueprint branch lacked upstream during Telegram governance closeout. Correct handling was DEFERRED in Telegram, not cross-repo repair or false failure.

### ANOM-TG1310-0010 — governance_ready_not_accepted (critical)
Historical closeout is `READY_FOR_BLUEPRINT_REVIEW`, explicitly not accepted/merged. Current authority must determine later acceptance/merge fate.

## Open loops

### LOOP-TG1310-0001
Verify current Telegram repository identity and historical governance branch lineage.
**Last known:** Historical feature branch ended at pushed `dcd2b01`, clean and ready for Blueprint review, not merged/accepted.
**Verify:** Resolve current repo/remote/branch/HEAD/worktree and whether dcd2b01 was merged/superseded before doing new work.

### LOOP-TG1310-0002
Reconcile Telegram behavior/client qualification with CRM/Operational Registry ownership.
**Last known:** Historical bot conversationally gathers/updates client profile fields.
**Verify:** Define current read/write contracts and ensure Telegram does not maintain competing canonical client records.

### LOOP-TG1310-0003
Reconcile Telegram delivery behavior with Logistics service.
**Last known:** Early registry includes delivery preference/provider-action ideas; later Logistics is separate service.
**Verify:** Telegram should collect intent/preference and surface status via contracts; verify no provider booking/routing logic remains embedded.

### LOOP-TG1310-0004
Verify current behavior-spec/runtime boundary.
**Last known:** Owner ultimately separates behavior-table/wizard development artifacts from production app/Supabase runtime.
**Verify:** Inventory current Excel/registry/wizard artifacts and runtime code; mark each as spec, test fixture, generator or production dependency.

### LOOP-TG1310-0005
Verify current configuration/path/documentation standards across Telegram scripts.
**Last known:** Owner corrected nonexistent paths and requires config-driven paths plus detailed script metadata/logging.
**Verify:** Run repository-relative/cwd-independent checks and semantic script-header audit.

### LOOP-TG1310-0006
Verify current classifier/template/generative runtime and historical model dependencies.
**Last known:** Historical stack uses DeBERTa/Mistral/Supabase with Mentor/AI escalation; testing was unstable during development.
**Verify:** Inspect current model/runtime policy, privacy rules, confidence thresholds, fallback authority and observability.

### LOOP-TG1310-0007
Verify current governance closeout automation and DEFERRED external-dependency semantics.
**Last known:** Historical closeout adds idempotent packet apply and truthful DEFERRED blueprint_pull handling.
**Verify:** Run current canonical Make/coordination gates and confirm external Blueprint unavailability is represented without false green or cross-repo write.

### LOOP-TG1310-0008
Determine whether historical behavior registry/dashboard artifacts remain authoritative, archival or generated projections.
**Last known:** Historical Excel/HTML artifacts were operator-facing design/control surfaces with integrity/KPI sheets.
**Verify:** Classify current owner/source-of-truth and avoid manual double-write against machine-readable runtime/roadmap state.
