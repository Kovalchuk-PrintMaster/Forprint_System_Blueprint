# Anomalies & Open Loops

## Anomalies

### ANOM-BP1009-0001 — assistant_side_capture_gap (high)
54/56 retained turn containers have text, but only two assistant narrative messages survive. Most intermediate implementation reasoning is represented only by handoff archive names.

### ANOM-BP1009-0002 — startup_authority_stale_reference_drift (high)
Current bootstrap/context generators still carried references to retired continuity authority, demonstrating that source authority and derived indexes/onboarding could drift apart.

### ANOM-BP1009-0003 — mutation_lint_failure_loop (high)
Repeated mutation attempts were failing on Ruff/syntax defects often enough that the owner requested a dedicated project-aware Mutation Compiler rather than endless one-off reruns.

### ANOM-BP1009-0004 — hidden_dependency_risk (critical)
Clean-room execution exposed dependencies that could be accidentally present in one environment but absent elsewhere, making failures hard to understand and maintain.

### ANOM-BP1009-0005 — silent_execution_operability_gap (normal)
Long-running scripts could appear frozen because they did not expose progress; owner explicitly requires visible progress/status and durable policy.

### ANOM-BP1009-0006 — knowledge_derivation_drift (high)
The dialogue initiates faithful-mirror/index-drift and cache-determinism hardening, implying generated knowledge/index outputs could diverge or rebuild non-deterministically without stronger derivation rules.

### ANOM-BP1009-0007 — continuity_stack_complexity (high)
Continuity evolved into a multi-layer stack (micro-roadmap, contract, checkpoint store, generated projections, handoff compiler). Without explicit dependency/lifecycle enforcement, the stack itself can become a new source of hidden ordering and stale-state risk.

### ANOM-BP1009-0008 — handoff_projection_schema_mismatch (high)
At the end of the source, Assistant Handoff Compiler hardening safe-fails because the validation probe reads `material` at the wrong YAML level instead of `payload.material`. The rerun archive exists, but final PASS is not preserved.

### ANOM-BP1009-0009 — historical_handoff_not_current_proof (normal)
The source contains 51 unique handoff ZIP names covering many infrastructure steps. They establish chronology, not today's implementation or PASS state.

## Open loops

### LOOP-BP1009-0001
Verify final startup-authority normalization / continuity retirement.
**Last known:** u175c–u175e hardening completed historically enough to move into autogeneration audit, but current bootstrap/index/context behavior is not audited here.
**Verify:** Inspect current bootstrap index, START_HERE, README, context generator and generated indexes.

### LOOP-BP1009-0002
Verify independent autogeneration/knowledge/onboarding audit findings and closure.
**Last known:** u176 audit led into generator-derivation and knowledge-drift hardening.
**Verify:** Inspect current derivation registry, generator tests, knowledge mirror and onboarding outputs.

### LOOP-BP1009-0003
Verify Mutation Compiler became canonical for project mutations.
**Last known:** Mutation Compiler foundation and dogfood handoffs exist; dialogue continues using it in later hardening.
**Verify:** Inspect current mutation entrypoint, autofix boundaries, rollback/checkpoint integration and policy.

### LOOP-BP1009-0004
Verify explicit execution dependency contract / Make DAG and absence of hidden dependencies.
**Last known:** Clean-room audits and Make-DAG foundation were executed through several reruns.
**Verify:** Run current sterile/clean-room checks and inspect declared prerequisites/generated dependencies.

### LOOP-BP1009-0005
Verify progress visibility is enforced by current policy/tooling.
**Last known:** Owner made progress visibility a permanent assistant/script policy and a validator/fix handoff followed.
**Verify:** Inspect current standards and representative long-running scripts/Make targets.

### LOOP-BP1009-0006
Verify knowledge mirror/index drift and cache determinism hardening.
**Last known:** Dedicated drift-probe and cache-determinism handoffs exist.
**Verify:** Rebuild in clean order twice and compare generated knowledge/index/cache outputs.

### LOOP-BP1009-0007
Verify continuity stack end to end.
**Last known:** Micro-roadmap → continuity contract → immutable checkpoint store → generated projections → Assistant Handoff Compiler were implemented/hardened in sequence.
**Verify:** Generate a fresh assistant handoff from current state and validate dependencies, checkpoint provenance, projections and rollback behavior.

### LOOP-BP1009-0008
Determine whether u179e5 passed and whether Step 10 Lifecycle Enforcement began/completed.
**Last known:** u179e4 safe-failed on wrong canonical delta schema path; u179e5 rerun archive is the final visible artifact. No final PASS narrative is preserved.
**Verify:** Check current handoff compiler tests/roadmap and lifecycle-enforcement artifacts.
