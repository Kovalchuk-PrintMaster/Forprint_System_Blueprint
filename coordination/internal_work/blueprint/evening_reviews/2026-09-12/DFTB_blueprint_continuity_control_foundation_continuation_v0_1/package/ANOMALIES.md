# Anomalies & Open Loops

## Anomalies

### ANOM-BP1209-0001 — continuation_not_duplicate (normal)
No source SHA matches the ten master-memory sources. The dialogue closes the prior 10.09 Handoff Compiler open loop and advances into Lifecycle Enforcement, zero-context closure and Control Foundation work.

### ANOM-BP1209-0002 — partial_conversation_capture (high)
Only 23 retained containers are present although turn numbering reaches 154. Assistant narrative survives in only four messages; much middle execution history is represented only by archive/file labels and pasted outputs.

### ANOM-BP1209-0003 — candidate_vs_durable_state (critical)
An early Step 10 candidate internally marked itself complete but rolled back, so roadmap completion in candidate data disagreed with durable Git/current state.

### ANOM-BP1209-0004 — repeated_bounded_repair_lineage (normal)
Lifecycle Enforcement progresses through multiple u179f* revisions while intermediate assistant explanations are missing. Artifact names prove sequence, not the full rationale for every revision.

### ANOM-BP1209-0005 — step12_acceptance_schema_mismatch (high)
Initial Step 12 acceptance validation expected a different phase/closure evidence schema and failed before later PASS evidence appeared.

### ANOM-BP1209-0006 — temporary_workspace_entropy (normal)
Operator workflow was creating too many per-task temp subdirectories and long filenames whose identifying suffixes were not visible; owner introduces one-horizon folder plus leading numeric indexes.

### ANOM-BP1209-0007 — roadmap_execution_drift (critical)
Roadmap repeatedly lags actual lifecycle execution, creating a systemic double-write/state-reconciliation problem rather than a one-off documentation delay.

### ANOM-BP1209-0008 — partial_mutation_rerun_risk (critical)
Several recovery artifacts explicitly say canonical state may have advanced and prohibit blind reruns; replaying a whole mutator could duplicate or corrupt already-applied state.

### ANOM-BP1209-0009 — checkpoint_cardinality_after_source_apply (high)
CF-01 implementation/checks passed and source transition was already applied, but closure failed only because checkpoint spec had four instead of 5–10 next actions. Recovery therefore had to be evidence-layer-only.

### ANOM-BP1209-0010 — cf02_yaml_safe_fail (high)
First CF-02 candidate fails on malformed YAML insertion before lifecycle activation/canonical mutation; the corrected v0.2 script is prepared but no final PASS is preserved.

### ANOM-BP1209-0011 — multi_day_source (normal)
The Sep 12 export contains Sep 11 handoff artifacts and Sep 12 events. Treat it as a multi-day continuation rather than a single-day execution snapshot.

## Open loops

### LOOP-BP1209-0001
Verify Step 9 Assistant Handoff Compiler remains accepted/current in the live repository.
**Last known:** Historical u179e5 PASS closes the prior 10.09 open loop.
**Verify:** Run current handoff/compiler validators from the live baseline and compare pack determinism/provenance.

### LOOP-BP1209-0002
Verify Lifecycle Enforcement invariants and historical u179f closure.
**Last known:** Later lifecycle status shows u179f CLOSED after multiple bounded repairs.
**Verify:** Inspect current continuity event schema, state transitions, checkpoint binding and closed-state immutability tests.

### LOOP-BP1209-0003
Verify zero-context acceptance and module-transfer Step 12 outcomes.
**Last known:** u179g closure archive exists; Step 12 initial validation failed then later PASS evidence appears and later lifecycle status shows u179h closed-repair.
**Verify:** Re-run/generate a fresh zero-context pack and inspect module-transfer reference assets in current repo.

### LOOP-BP1209-0004
Verify temp-work naming/horizon convention became durable project policy.
**Last known:** Owner requested one bounded folder and leading monotonic indexes.
**Verify:** Inspect current bootstrap/operations policy and representative tmp/assistant_work naming.

### LOOP-BP1209-0005
Verify Control Foundation CF-01 is current and its manual-operator boundary remains intact.
**Last known:** u180a historical recovery PASS: CLOSED, CF-01 COMPLETE, CF-02 NEXT_MANUAL; no worker dispatch/release/foreign writes.
**Verify:** Resolve live control-foundation program state and current authority flags.

### LOOP-BP1209-0006
Complete/verify CF-02 Roadmap Execution State Reconciliation Controller.
**Last known:** 0031 safe-failed before mutation due YAML indentation; corrected 0032 prepared; no PASS result in source. Legacy double-write migration remains pending.
**Verify:** Check whether 0032 or successors passed, then verify event-store execution authority, generated ROADMAP_SYNC, legacy field migration and hard gates.

### LOOP-BP1209-0007
Verify state-aware partial-mutation recovery is a general enforced pattern.
**Last known:** Multiple failures explicitly set `do_not_rerun_blindly=true`; CF-01 recovery repaired evidence/closure only.
**Verify:** Inspect Mutation Compiler/recovery standards and tests for source fingerprint and partial-apply detection.

### LOOP-BP1209-0008
Verify second-level continuity/knowledge hardening backlog.
**Last known:** Explicit source modes, Git provenance records, unresolved-pattern contract, freshness and old context-pack hardening were deferred after foundation.
**Verify:** Map these items to current roadmap/current implementation and classify superseded/completed/pending.
