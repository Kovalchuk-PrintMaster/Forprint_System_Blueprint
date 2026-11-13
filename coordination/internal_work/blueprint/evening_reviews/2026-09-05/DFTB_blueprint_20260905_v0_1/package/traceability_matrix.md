# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Domain | Audit |
|---|---|---|---|---|---|---|
| `IT-BP0509-0001` Reconcile memory packages semantically, not by blind merge | process_rule | accepted | critical | `EV-BP0509-0001`, `EV-BP0509-0002`, `EV-BP0509-0004` | human_intent, project_memory | not audited |
| `IT-BP0509-0002` Avoid duplicate Human Intent semantics across ID migrations | process_rule | accepted | critical | `EV-BP0509-0003`, `EV-BP0509-0005` | human_intent, governance | not audited |
| `IT-BP0509-0003` Initial v1.1 integration safe-failed on Ruff and rolled back | implementation_claim | accepted | normal | `EV-BP0509-0006` | human_intent, tooling | not audited |
| `IT-BP0509-0004` Normalize module/project descriptive documents to one structure | requirement | agreed | critical | `EV-BP0509-0007`, `EV-BP0509-0008` | documentation, portfolio | not audited |
| `IT-BP0509-0005` Normalize SYNTHETIC and PROPOSED vocabulary | decision | agreed | high | `EV-BP0509-0009` | roadmap, schema | not audited |
| `IT-BP0509-0006` Use bulk semantic normalization for large document sets | process_rule | agreed | high | `EV-BP0509-0010` | documentation, review | not audited |
| `IT-BP0509-0007` Foreign UI task explicitly excluded | rejected_alternative | rejected | high | `EV-BP0509-0011` | scope_control | not audited |
| `IT-BP0509-0008` Project self-cleaning is a formal governance obligation | process_rule | agreed | critical | `EV-BP0509-0012`, `EV-BP0509-0013` | governance, module_assistants | not audited |
| `IT-BP0509-0009` Automated descriptive-document conformance checks | requirement | agreed | high | `EV-BP0509-0014` | documentation, validation | not audited |
| `IT-BP0509-0010` Self-cleaning capability must be indexed/discoverable | process_rule | agreed | high | `EV-BP0509-0015` | indexes, governance | not audited |
| `IT-BP0509-0011` Maintain stale-artifact candidate registry | requirement | agreed | high | `EV-BP0509-0016`, `EV-BP0509-0017` | legacy, repository_maintenance | not audited |
| `IT-BP0509-0012` Retired artifacts leave active validation surface | process_rule | agreed | high | `EV-BP0509-0018` | legacy, validation | not audited |
| `IT-BP0509-0013` Closeout includes documentation propagation | process_rule | agreed | critical | `EV-BP0509-0019`, `EV-BP0509-0020` | governance, closeout | not audited |
| `IT-BP0509-0014` Closeout includes index and health verification | process_rule | agreed | critical | `EV-BP0509-0021` | indexes, health | not audited |
| `IT-BP0509-0015` Logistics inventory reviewed in bounded batches | plan | accepted | high | `EV-BP0509-0022`, `EV-BP0509-0023` | logistics_service, inventory | not audited |
| `IT-BP0509-0016` Blueprint publishes prompts only in Blueprint-owned surfaces | architecture_constraint | agreed | critical | `EV-BP0509-0024`, `EV-BP0509-0026` | forprint_system_blueprint, prompt_lifecycle | not audited |
| `IT-BP0509-0017` Module-side pull/listener consumes released prompts | workflow | agreed | critical | `EV-BP0509-0025`, `EV-BP0509-0026` | module_assistants, listener, prompt_lifecycle | not audited |
| `IT-BP0509-0018` Module listener reads Blueprint but does not write it | architecture_constraint | agreed | critical | `EV-BP0509-0026` | module_assistants, repository_boundary | not audited |
| `IT-BP0509-0019` Fresh AI worker per prompt | process_rule | agreed | critical | `EV-BP0509-0027` | worker_runtime, module_assistants | not audited |
| `IT-BP0509-0020` Fresh-worker context includes prior completion evidence | requirement | agreed | critical | `EV-BP0509-0028` | worker_runtime, context_pack | not audited |
| `IT-BP0509-0021` Fresh-worker context exposes project navigation | requirement | agreed | critical | `EV-BP0509-0029` | context_pack, knowledge | not audited |
| `IT-BP0509-0022` Business acceptance remains separate from prompt execution | process_rule | agreed | critical | `EV-BP0509-0024` | operator_approval, prompt_lifecycle | not audited |
| `IT-BP0509-0023` Generic health release reached ready_for_module_pull | implementation_claim | accepted | high | `EV-BP0509-0030`, `EV-BP0509-0031` | H10, prompt_queue | not audited |
| `IT-BP0509-0024` Release policy returns fail-closed after one-shot release | process_rule | accepted | critical | `EV-BP0509-0032` | release, safety | not audited |
| `IT-BP0509-0025` Acceptance Oracle binding survives prompt release | requirement | accepted | critical | `EV-BP0509-0033` | roadmap, acceptance_oracle, prompt_lifecycle | not audited |
| `IT-BP0509-0026` Prepared prompt set and oracle-bound set are not identical after release | risk | accepted | high | `EV-BP0509-0033` | prompt_lifecycle, tests | not audited |
| `IT-BP0509-0027` Current governance documents require durable inbound references | risk | accepted | high | `EV-BP0509-0034`, `EV-BP0509-0035` | semantic_validation, governance | not audited |
| `IT-BP0509-0028` Repair semantic references, do not weaken validator | process_rule | accepted | critical | `EV-BP0509-0035` | semantic_validation, governance | not audited |
| `IT-BP0509-0029` Maintain self-inventory/system-context snapshot | requirement | accepted | high | `EV-BP0509-0036` | forprint_system_blueprint, knowledge | not audited |
| `IT-BP0509-0030` Maintain portfolio/roadmap current-state snapshot | requirement | accepted | high | `EV-BP0509-0037` | portfolio, roadmap, knowledge | not audited |
