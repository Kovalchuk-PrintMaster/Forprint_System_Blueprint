# Anomalies & Open Loops

## Anomalies

### ANOM-BP1407-0001 — source_capture_gap (high)
The MHTML contains 877 turn containers, but text is recoverable in only 133 turns. Most missing turns are assistant placeholders.

### ANOM-BP1407-0002 — acceptance_chain_gap (high)
Many preserved user turns are short acknowledgements whose preceding assistant proposal is absent, so specific accepted requirements cannot be safely reconstructed.

### ANOM-BP1407-0003 — ownership_conflict (high)
The original owner description gives Library a very broad role; the preserved assistant architecture narrows Library to stable canonical references. Explicit owner acceptance is not visible.

### ANOM-BP1407-0004 — ownership_question (high)
Accounting Registry vs Operational Registry separation becomes an explicit later question, but the resolving assistant response is not preserved.

### ANOM-BP1407-0005 — future_authority_overlap (normal)
Strategic Control Plane is planned after Blueprint is already the central architecture/coordination layer; future handoff/coexistence needs an explicit boundary.

### ANOM-BP1407-0006 — security_gap (high)
Telegram+AI assumes powerful operational/file access, but the preserved dialogue does not define permission scopes, audit trails, approval thresholds or rollback.

### ANOM-BP1407-0007 — lifecycle_gap (normal)
The owner notices executed prompts remaining in drafts and asks for cleanup; the final prompt state machine is not preserved.

### ANOM-BP1407-0008 — policy_status_drift_risk (normal)
Historical dialogue treats standards as partly advisory/directional. Current governance may have promoted some standards to mandatory, so effective authority must be audited.

## Open loops

### LOOP-BP1407-0001
Resolve canonical boundary between Accounting Registry and Operational Registry.
**Last known state:** Explicit owner question; answer missing from MHTML.
**Verify:** Check current doctrine, registry, ADRs and live repositories.

### LOOP-BP1407-0002
Verify whether Library's narrowed canonical-reference boundary was formally accepted and remains current.
**Last known state:** Assistant proposed correction; full acceptance chain is missing.
**Verify:** Check current Library policy/ADR/roadmap and implementation.

### LOOP-BP1407-0003
Define Strategic Control Plane vs Blueprint responsibility handoff.
**Last known state:** Strategic component planned; coexistence boundary not preserved.
**Verify:** Check current Strategic Control Plane policy and Blueprint doctrine.

### LOOP-BP1407-0004
Audit Telegram+AI tool safety model.
**Last known state:** Powerful operational concept agreed; detailed permission model absent.
**Verify:** Inspect authorization, audit logs, approval gates and rollback.

### LOOP-BP1407-0005
Verify prompt lifecycle cleanup and archival rules.
**Last known state:** Owner flags stale drafts and asks for lifecycle/roadmap handling.
**Verify:** Inspect current prompt queue/state machine.

### LOOP-BP1407-0006
Determine whether dedicated Blueprint assistant became an accepted operating choice.
**Last known state:** Final preserved user turn asks the question; no answer exists.
**Verify:** Search later dialogues and operating documentation.

### LOOP-BP1407-0007
Verify that a Logistics-derived assistant productivity standard was actually created.
**Last known state:** Policy accepted; later Logistics report is not in this snapshot.
**Verify:** Search current standards/governance and Logistics evidence.
