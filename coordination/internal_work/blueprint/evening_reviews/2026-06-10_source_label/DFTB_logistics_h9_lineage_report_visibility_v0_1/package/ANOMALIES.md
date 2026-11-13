# Anomalies & Open Loops

## Anomalies

### ANOM-LOG1006-0001 — new_unique_cross_module_source (normal)
No SHA/message-ID/meaningful text-sequence match exists against the currently loaded master/Blueprint sources. This is a distinct Logistics module dialogue.

### ANOM-LOG1006-0002 — partial_conversation_capture (high)
122 visible message blocks survive but only four assistant messages are present; most intermediate work is represented by attachment/report placeholders.

### ANOM-LOG1006-0003 — long_span_filename_mismatch (high)
Filename label 10.06 is not an end date: the same conversation carries dated report artifacts through 2026-08-22.

### ANOM-LOG1006-0004 — foreign_module_tail_contamination (normal)
Final visible turn contains Cloud Backup Manager output under `/opt/forprint-utils/cloud_backup_manager`; it is excluded from Logistics semantics.

### ANOM-LOG1006-0005 — external_freshness_blocker_not_module_failure (critical)
H9 module publication is reported complete while Blueprint local/remote freshness remains STALE; status layers must not collapse external dependency freshness into module implementation failure.

### ANOM-LOG1006-0006 — seal_recursion_risk (high)
Recording a seal commit's own SHA by creating another seal commit would cause recursive metadata sealing; historical guidance explicitly forbids it.

### ANOM-LOG1006-0007 — sealed_candidate_reopen_risk (critical)
Blueprint HEAD moved after Logistics H9 sealing; rewriting sealed Logistics metadata to chase the new external HEAD would reopen a completed candidate.

## Open loops

### LOOP-LOG1006-0001
Verify current Logistics repository identity/bootstrap contracts against live repo.
**Last known:** Historical source begins from greenfield bootstrap and later evolves substantially.
**Verify:** Audit current Logistics manifest/tree/provider boundaries/contracts; do not assume bootstrap-era structure remains current.

### LOOP-LOG1006-0002
Verify prompt intake remains coordination-only and Blueprint-driven.
**Last known:** Historical tracking-events intake passed coordination-only checks.
**Verify:** Run current prompt-intake/check-only gates and compare changed-path policy.

### LOOP-LOG1006-0003
Verify H9 reference rollout closure and publication evidence in current Git history.
**Last known:** Historical assistant reports subject+seal pushed, clean tree and full gates green.
**Verify:** Resolve actual commits/branch ancestry/current module history before relying on H9 claims.

### LOOP-LOG1006-0004
Verify external Blueprint freshness is modeled separately from Logistics implementation/publication state.
**Last known:** Historical H9 is published while coordination freshness is STALE and live start blocked.
**Verify:** Inspect current coordination-sync-check/status schema and runtime start gate.

### LOOP-LOG1006-0005
Verify sealed-candidate immutability and non-recursive publication metadata.
**Last known:** Historical guidance says no recursive seal commit and no reopening H9 merely because Blueprint HEAD moved.
**Verify:** Inspect current seal/report identity rules and regression tests.

### LOOP-LOG1006-0006
Reconcile H9 module-side history with Blueprint H10/reference-pilot lineage.
**Last known:** H9 closes module-side and hands control to Blueprint; later Blueprint history promotes Logistics as H10 sole pilot.
**Verify:** Trace Blueprint acceptance/promotion from H9 handoff into H10 authority without treating Logistics source as Blueprint authority.
