# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Domain | Audit |
|---|---|---|---|---|---|---|
| `IT-BP1009-0001` Canonical startup chain | process_rule | accepted | critical | `EV-BP1009-0002` | bootstrap, authority | not audited |
| `IT-BP1009-0002` Historical continuity retired from current authority | decision | accepted | critical | `EV-BP1009-0003` | continuity, bootstrap | not audited |
| `IT-BP1009-0003` Generated indexes are derived artifacts | process_rule | accepted | critical | `EV-BP1009-0004` | knowledge, indexes | not audited |
| `IT-BP1009-0004` Broad default context, explicit focused context | requirement | accepted | high | `EV-BP1009-0005` | context_pack, bootstrap | not audited |
| `IT-BP1009-0005` Deep independent audit of autogeneration | requirement | agreed | critical | `EV-BP1009-0006`, `EV-BP1009-0007`, `EV-BP1009-0008`, `EV-BP1009-0023` | autogeneration, knowledge | not audited |
| `IT-BP1009-0006` Generator derivation registry | requirement | accepted | critical | `EV-BP1009-0024` | autogeneration, knowledge | not audited |
| `IT-BP1009-0007` Ruff/syntax failures are a recurring mutation bottleneck | risk | agreed | high | `EV-BP1009-0009`, `EV-BP1009-0011` | tooling, mutation | not audited |
| `IT-BP1009-0008` Project-aware Mutation Compiler | requirement | agreed | critical | `EV-BP1009-0010`, `EV-BP1009-0025` | mutation_compiler, tooling | not audited |
| `IT-BP1009-0009` Mutation Compiler remains transactional and fail-closed | process_rule | accepted | critical | `EV-BP1009-0018`, `EV-BP1009-0019` | mutation_compiler, safety | not audited |
| `IT-BP1009-0010` Non-mutating Make checks | requirement | accepted | high | `EV-BP1009-0026` | make, tooling | not audited |
| `IT-BP1009-0011` No hidden or implicit execution dependencies | process_rule | agreed | critical | `EV-BP1009-0012`, `EV-BP1009-0014` | dependencies, maintainability | not audited |
| `IT-BP1009-0012` Dependencies must be explicit or deliberately generated | requirement | agreed | critical | `EV-BP1009-0013` | dependencies, execution_contract | not audited |
| `IT-BP1009-0013` Clean-room dependency audit | requirement | accepted | critical | `EV-BP1009-0027` | dependencies, clean_room | not audited |
| `IT-BP1009-0014` Execution dependency contract and Make DAG | requirement | accepted | critical | `EV-BP1009-0028` | dependencies, make | not audited |
| `IT-BP1009-0015` Project execution architecture must remain readable | nonfunctional_requirement | agreed | high | `EV-BP1009-0014` | maintainability, architecture | not audited |
| `IT-BP1009-0016` Continue agreed infrastructure plan stepwise | process_rule | accepted | high | `EV-BP1009-0015` | coordination, roadmap | not audited |
| `IT-BP1009-0017` Long-running scripts must expose progress | nonfunctional_requirement | agreed | high | `EV-BP1009-0016` | tooling, operator_ux | not audited |
| `IT-BP1009-0018` Progress visibility is a durable assistant/script policy | process_rule | agreed | high | `EV-BP1009-0017`, `EV-BP1009-0029` | governance, tooling | not audited |
| `IT-BP1009-0019` Faithful knowledge mirror / drift detection | requirement | accepted | critical | `EV-BP1009-0030` | knowledge, indexes | not audited |
| `IT-BP1009-0020` Deterministic knowledge/runtime caches | requirement | accepted | high | `EV-BP1009-0031` | knowledge, cache | not audited |
| `IT-BP1009-0021` Persist assistant-handoff micro-roadmap | requirement | accepted | critical | `EV-BP1009-0032` | continuity, roadmap | not audited |
| `IT-BP1009-0022` Continuity contract | requirement | accepted | critical | `EV-BP1009-0033` | continuity, governance | not audited |
| `IT-BP1009-0023` Immutable checkpoint store | requirement | accepted | critical | `EV-BP1009-0034` | continuity, checkpoint | not audited |
| `IT-BP1009-0024` Generated operational continuity projections | requirement | accepted | critical | `EV-BP1009-0035` | continuity, projections | not audited |
| `IT-BP1009-0025` Assistant Handoff Compiler | requirement | accepted | critical | `EV-BP1009-0036`, `EV-BP1009-0037` | continuity, handoff_compiler | not audited |
| `IT-BP1009-0026` Assistant Handoff Compiler failures stay fail-closed | process_rule | accepted | critical | `EV-BP1009-0018`, `EV-BP1009-0019` | handoff_compiler, safety | not audited |
| `IT-BP1009-0027` Canonical current-delta projection uses `payload.material` | data_contract | accepted | high | `EV-BP1009-0020` | continuity_projection, schema | not audited |
| `IT-BP1009-0028` Lifecycle Enforcement follows Assistant Handoff Compiler | plan | accepted | high | `EV-BP1009-0021`, `EV-BP1009-0022` | continuity, lifecycle | not audited |
| `IT-BP1009-0029` Startup-authority retirement was actively hardened | implementation_claim | accepted | normal | `EV-BP1009-0002`, `EV-BP1009-0003` | bootstrap, continuity | not audited |
| `IT-BP1009-0030` Dependency/continuity infrastructure progressed through multiple bounded hardening stages | implementation_claim | accepted | high | `EV-BP1009-0024`, `EV-BP1009-0025`, `EV-BP1009-0028`, `EV-BP1009-0033`, `EV-BP1009-0036` | forprint_system_blueprint, infrastructure | not audited |
| `IT-BP1009-0031` Historical immutable records are not mass-rewritten during startup cleanup | process_rule | accepted | high | `EV-BP1009-0003`, `EV-BP1009-0004` | governance, history | not audited |
| `IT-BP1009-0032` Onboarding generation must distinguish current authority from optional history | requirement | accepted | critical | `EV-BP1009-0003`, `EV-BP1009-0005` | onboarding, context_pack | not audited |
