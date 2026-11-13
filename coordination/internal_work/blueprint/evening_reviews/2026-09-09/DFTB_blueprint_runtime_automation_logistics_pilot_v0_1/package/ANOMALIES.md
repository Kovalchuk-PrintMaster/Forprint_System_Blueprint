# Anomalies & Open Loops

## Anomalies

### ANOM-BP0909-0001 — assistant_side_capture_gap (high)
102/103 retained turn containers have text, but only three assistant narrative messages survive; many decisions are visible only through owner follow-ups and handoff labels.

### ANOM-BP0909-0002 — historical_phase_drift (high)
Session-start AGENTS says inventory-first/no normal implementation, while the dialogue continues a bounded Logistics pilot; current release revalidation is essential.

### ANOM-BP0909-0003 — runtime_component_ownership_gap (high)
Listener/dispatcher standalone-vs-embedded ownership is not directly resolved in preserved prose.

### ANOM-BP0909-0004 — publication_policy_tension (high)
Owner moves local cleanup/commit/push into worker preflight while AGENTS says no commit/push without explicit authorization.

### ANOM-BP0909-0005 — context_bloat_risk (normal)
Strong fresh-worker snapshots can become polluted by stale history; later startup normalization explicitly separates history from current context.

### ANOM-BP0909-0006 — filename_not_verification (normal)
Many implementation states are visible only through archive filenames; PASS/FAIL labels cannot substitute for repository/test verification.

### ANOM-BP0909-0007 — startup_authority_competition (high)
Old continuity START_HERE and newer startup/context surfaces accumulated overlapping authority semantics.

### ANOM-BP0909-0008 — automation_boundary_risk (critical)
Automatic within-pool progression must remain distinct from manual major-pool/phase approval.

## Open loops

### LOOP-BP0909-0001
Resolve current central listener/dispatcher owner/location.
**Last known:** Owner asks standalone vs embedded; later Blueprint handoffs exist.
**Verify:** Inspect current runtime architecture/code/registry.

### LOOP-BP0909-0002
Resolve worker-local Git publication authority.
**Last known:** Owner wants local baseline preparation; AGENTS gates commit/push.
**Verify:** Check current publication policy and worker runtime profile.

### LOOP-BP0909-0003
Verify Logistics self-knowledge bootstrap prompt.
**Last known:** Owner requires inventory/index automation; versioned bootstrap prompt handoff later exists.
**Verify:** Inspect current Logistics prompt/repository.

### LOOP-BP0909-0004
Verify end-to-end automatic within-pool pilot with manual major-pool approval.
**Last known:** Runtime components/hardening exist; final production-cycle proof not retained.
**Verify:** Audit current pilot evidence/runtime.

### LOOP-BP0909-0005
Verify startup normalization after u175a.
**Last known:** u175 rolled back; u175a handoff exists, no final PASS narrative.
**Verify:** Inspect current startup files/context-pack defaults.

### LOOP-BP0909-0006
Verify Project Inspector provisioning/registry state.
**Last known:** Registry binding followed by provisioning-gap work.
**Verify:** Check current registry and repository existence.
