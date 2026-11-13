# Anomalies & Open Loops

## Anomalies

### ANOM-BP1409-0001 — overlapping_continuation_not_full_duplicate (normal)
14.09 export shares 18 message IDs with the 12.09 source, adds 43 new messages, and omits 5 messages retained in 12.09. Only the 43 new messages are indexed here to avoid duplication.

### ANOM-BP1409-0002 — attachment_only_evidence_gap (high)
Most intermediate turns in the new tail are only visible as `Pasted text.txt` / `Pasted code.yaml`; their contents are not embedded in the MHTML text, so exact CF-03/CF-04 and repair lineage cannot be reconstructed safely.

### ANOM-BP1409-0003 — cf02_partial_advance_failure (critical)
CF-02 closure reports FAIL on roadmap-sync-check while canonical u180b state is already CLOSED; a naïve rerun would risk replaying completed state.

### ANOM-BP1409-0004 — legacy_terminal_state_hints_pending (high)
Active CF double-write is reported removed, but twelve legacy continuity terminal-state fields remain pending retirement at the observed hardening checkpoint.

### ANOM-BP1409-0005 — artifact_delivery_truncation (normal)
Two generated script deliveries are reported truncated; operator requests distinct names and cosmetic changes to improve reliable delivery.

### ANOM-BP1409-0006 — scope_contamination_then_owner_rejection (normal)
Website/UI work appears inside the control-foundation continuation but is explicitly rejected by the owner as not this workfront.

### ANOM-BP1409-0007 — stale_full_check_log (critical)
A full-check report contains an old controlled-failure hash pin even though the current focused rerun passes with the newer pin.

### ANOM-BP1409-0008 — current_tree_vs_isolated_check_ambiguity (critical)
At source end it is unresolved whether the current working tree actually fails full pytest or whether only isolated non-mutating public-check materialization/report freshness is stale.

### ANOM-BP1409-0009 — final_delivery_timeout (high)
The conversation ends with an assistant message-delivery timeout after the 0104-related attachment, so the final diagnostic interpretation is missing.

## Open loops

### LOOP-BP1409-0001
Verify CF-02 final closure and retirement of legacy continuity terminal-state hints.
**Last known:** Active CF double-write removed; legacy hints remained; later closure failure observed u180b CLOSED and required state-aware recovery.
**Verify:** Inspect live lifecycle/event store, roadmap projection and current legacy-field inventory before any rerun.

### LOOP-BP1409-0002
Recover/verify missing CF-03/CF-04 intermediate evidence.
**Last known:** By u180e the roadmap projects CF-04 previous / CF-05 current, but intermediate attachment contents are absent from MHTML.
**Verify:** Use repository history/current artifacts rather than infer from placeholder attachments.

### LOOP-BP1409-0003
Resolve the current-tree vs non-mutating public-check isolation/materialization ambiguity.
**Last known:** Focused rerun passed; full log appeared stale; 0104 was prepared but its result is not visible.
**Verify:** Run current direct full pytest and current non-mutating public check with fresh report provenance; compare source/test hashes and materialized snapshot.

### LOOP-BP1409-0004
Verify controlled-failure source-hash pin maintenance is derived/reconciled correctly.
**Last known:** Historical log expected old 099b pin while current source/test used 7376 pin.
**Verify:** Audit pin derivation/update contract and stale-report invalidation.

### LOOP-BP1409-0005
Verify Website/UI branch remains excluded from Blueprint control-foundation scope.
**Last known:** Owner explicitly says it is not this work and to continue own work.
**Verify:** Keep Website work in its owning module unless later explicit authority reassigns it.

### LOOP-BP1409-0006
Verify generated-script delivery integrity handling.
**Last known:** Two script deliveries arrived truncated and were regenerated under different names.
**Verify:** Use checksums/bytes/line counts or downloadable artifacts to prove complete delivery before execution.
