# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Domain | Audit |
|---|---|---|---|---|---|---|
| `IT-BP1209-0001` Assistant Handoff Compiler Step 9 historically accepted | implementation_claim | accepted | high | `EV-BP1209-0001`, `EV-BP1209-0002` | continuity, handoff_compiler | not audited |
| `IT-BP1209-0002` Sterile project-gate tests must not weaken production Git requirement | architecture_constraint | accepted | critical | `EV-BP1209-0003` | mutation_compiler, git_workflow | not audited |
| `IT-BP1209-0003` Execution dependencies reflect actual reads, not convenient persistent artifacts | architecture_constraint | accepted | critical | `EV-BP1209-0004` | dependency_contracts, continuity | not audited |
| `IT-BP1209-0004` Canonical delta probe schema-path fix closes u179e5 | implementation_claim | accepted | normal | `EV-BP1209-0005` | continuity, projection | not audited |
| `IT-BP1209-0005` Continuity work follows enforced lifecycle state machine | process_rule | accepted | critical | `EV-BP1209-0006` | continuity, lifecycle | not audited |
| `IT-BP1209-0006` Direct ACTIVE→CLOSED and reopening a closed work id are forbidden | process_rule | accepted | critical | `EV-BP1209-0007` | continuity, lifecycle | not audited |
| `IT-BP1209-0007` Validation and close bind to the same work checkpoint | process_rule | accepted | critical | `EV-BP1209-0008` | continuity, lifecycle | not audited |
| `IT-BP1209-0008` Legacy lifecycle migration is append-only | process_rule | accepted | high | `EV-BP1209-0009` | continuity, event_store | not audited |
| `IT-BP1209-0009` Durable current state outranks rolled-back candidate/chat state | process_rule | accepted | critical | `EV-BP1209-0010` | authority, continuity | not audited |
| `IT-BP1209-0010` Zero-context acceptance proves continuity foundation | acceptance_criterion | accepted | critical | `EV-BP1209-0011` | continuity, bootstrap | not audited |
| `IT-BP1209-0011` Continuity model transfers to reusable module reference implementation | plan | accepted | high | `EV-BP1209-0012` | continuity, module_templates | not audited |
| `IT-BP1209-0012` Project-entry context and Task Context remain distinct | architecture_constraint | accepted | critical | `EV-BP1209-0013` | continuity, task_context | not audited |
| `IT-BP1209-0013` Second-level continuity hardening remains after foundation | plan | accepted | high | `EV-BP1209-0014` | repository_knowledge, continuity | not audited |
| `IT-BP1209-0014` Lifecycle Enforcement u179f historically progressed through bounded repairs | implementation_claim | accepted | normal | `EV-BP1209-0015` | continuity, lifecycle | not audited |
| `IT-BP1209-0015` Zero-context work u179g historically closed | implementation_claim | accepted | high | `EV-BP1209-0016` | continuity, zero_context | not audited |
| `IT-BP1209-0016` Step 12 acceptance first failed then later passed | implementation_claim | accepted | high | `EV-BP1209-0017`, `EV-BP1209-0018` | continuity, step12 | not audited |
| `IT-BP1209-0017` Successful closure may wait for strategy reconciliation instead of auto-progressing | process_rule | accepted | critical | `EV-BP1209-0019` | continuity, operator_approval | not audited |
| `IT-BP1209-0018` Use one compact temporary work folder per bounded horizon | process_rule | agreed | normal | `EV-BP1209-0020` | operator_workflow, repository_hygiene | not audited |
| `IT-BP1209-0019` Temporary artifact names use leading monotonic indexes | process_rule | agreed | normal | `EV-BP1209-0021` | artifact_identity, operator_ux | not audited |
| `IT-BP1209-0020` Temp-work convention belongs in a machine/bootstrap policy surface | requirement | agreed | normal | `EV-BP1209-0022` | operator_workflow, governance | not audited |
| `IT-BP1209-0021` Roadmap can lag actual execution state | risk | accepted | critical | `EV-BP1209-0023` | roadmap, coordination | not audited |
| `IT-BP1209-0022` Roadmap/execution reconciliation needs deterministic control | requirement | agreed | critical | `EV-BP1209-0024` | roadmap, continuity | not audited |
| `IT-BP1209-0023` Partial failures require state-aware recovery, not blind rerun | process_rule | accepted | critical | `EV-BP1209-0025`, `EV-BP1209-0026` | mutation_compiler, recovery | not audited |
| `IT-BP1209-0024` Continuity checkpoints carry 5–10 next actions | requirement | accepted | high | `EV-BP1209-0027` | continuity, roadmap | not audited |
| `IT-BP1209-0025` Recovery must not repeat already-applied canonical source mutation | process_rule | accepted | critical | `EV-BP1209-0028` | mutation_compiler, recovery | not audited |
| `IT-BP1209-0026` Control Foundation CF-01 historically closed | implementation_claim | accepted | high | `EV-BP1209-0029`, `EV-BP1209-0030` | control_foundation, continuity | not audited |
| `IT-BP1209-0027` Control Foundation closure preserves manual operator boundary | architecture_constraint | accepted | critical | `EV-BP1209-0031` | control_foundation, operator_approval | not audited |
| `IT-BP1209-0028` Roadmap is plan; continuity event store is actual execution authority | architecture_constraint | accepted | critical | `EV-BP1209-0032` | roadmap, continuity, control_foundation | not audited |
| `IT-BP1209-0029` Execution status becomes generated projection | requirement | accepted | critical | `EV-BP1209-0033` | roadmap, generated_projections | not audited |
| `IT-BP1209-0030` CF-02 does not auto-activate the next step | process_rule | accepted | critical | `EV-BP1209-0034` | control_foundation, operator_approval | not audited |
| `IT-BP1209-0031` CF-02 migration is intentionally two-stage | plan | accepted | high | `EV-BP1209-0035` | control_foundation, roadmap | not audited |
| `IT-BP1209-0032` First CF-02 foundation attempt safe-failed before canonical mutation | implementation_claim | accepted | normal | `EV-BP1209-0036`, `EV-BP1209-0037`, `EV-BP1209-0038` | control_foundation, safe_fail | not audited |
| `IT-BP1209-0033` CF-02 contracts require strict document-type registration and sync ordering | requirement | accepted | high | `EV-BP1209-0039` | control_foundation, document_registry | not audited |
| `IT-BP1209-0034` CF-02 legacy double-write migration remains unresolved at source end | open_question | accepted | critical | `EV-BP1209-0040` | control_foundation, roadmap | not audited |
| `IT-BP1209-0035` Current source spans Sep 11→12 execution lineage | implementation_claim | accepted | normal | `EV-BP1209-0001`, `EV-BP1209-0029` | provenance | not audited |
