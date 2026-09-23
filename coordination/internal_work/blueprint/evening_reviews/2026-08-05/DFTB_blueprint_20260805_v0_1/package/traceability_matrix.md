# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Domain | Audit |
|---|---|---|---|---|---|---|
| `IT-BP0508-0001` Repository-knowledge snapshots require evidence, not templates | process_rule | accepted | critical | `EV-BP0508-0001` | repository_knowledge, forprint_system_blueprint | not audited |
| `IT-BP0508-0002` Repository knowledge uses explicit confidence classes | requirement | accepted | critical | `EV-BP0508-0002` | repository_knowledge, evidence | not audited |
| `IT-BP0508-0003` Repository snapshots bind to exact Git baseline | requirement | accepted | critical | `EV-BP0508-0003` | repository_knowledge, git_workflow | not audited |
| `IT-BP0508-0004` Makefile is the discoverable operational surface | process_rule | agreed | critical | `EV-BP0508-0004` | make, forprint_system_blueprint | not audited |
| `IT-BP0508-0005` Clean Blueprint internal structure before broader assistant work | plan | agreed | high | `EV-BP0508-0005` | forprint_system_blueprint, repository_structure | not audited |
| `IT-BP0508-0006` Lifecycle audit found completion-report and prompt-naming repairs | implementation_claim | accepted | normal | `EV-BP0508-0006` | prompt_lifecycle, reporting | not audited |
| `IT-BP0508-0007` Module roadmaps maintain 8–10 forward steps | process_rule | agreed | critical | `EV-BP0508-0007` | roadmap, portfolio | not audited |
| `IT-BP0508-0008` Index coverage is not semantic understanding | risk | accepted | critical | `EV-BP0508-0008`, `EV-BP0508-0009` | self_knowledge, repository_knowledge | not audited |
| `IT-BP0508-0009` Blueprint self-audit supports bounded external semantic assessment | workflow | accepted | high | `EV-BP0508-0010`, `EV-BP0508-0012` | self_knowledge, external_analysis | not audited |
| `IT-BP0508-0010` External audit roundtrip preserves request identity and checksum | data_contract | accepted | critical | `EV-BP0508-0011` | external_analysis, provenance | not audited |
| `IT-BP0508-0011` Downloadable reports use project-local temporary workspace | process_rule | agreed | normal | `EV-BP0508-0013` | reporting, repository_structure | not audited |
| `IT-BP0508-0012` Module assistants pull current workfront into their own workflow | workflow | agreed | critical | `EV-BP0508-0014` | module_assistants, prompt_lifecycle | not audited |
| `IT-BP0508-0013` Each module operates through module-owned scripts | architecture_constraint | agreed | critical | `EV-BP0508-0015` | module_assistants, ownership | not audited |
| `IT-BP0508-0014` Blueprint inspects modules through Blueprint-owned tooling | architecture_constraint | agreed | critical | `EV-BP0508-0016` | forprint_system_blueprint, ownership | not audited |
| `IT-BP0508-0015` Module workfront completion updates status and produces evidence | workflow | agreed | critical | `EV-BP0508-0017` | module_assistants, completion_reporting | not audited |
| `IT-BP0508-0016` Read-only checks must not be disguised mutations | process_rule | agreed | critical | `EV-BP0508-0018`, `EV-BP0508-0019` | make, command_semantics | not audited |
| `IT-BP0508-0017` Prefer clean target architecture over awkward legacy command behavior | process_rule | agreed | high | `EV-BP0508-0020` | architecture, make | not audited |
| `IT-BP0508-0018` Worktree/copy identity must be unambiguous | risk | agreed | high | `EV-BP0508-0021` | git_workflow, operator_ux | not audited |
| `IT-BP0508-0019` Completion intake and acceptance-gate validators were historically implemented | implementation_claim | accepted | high | `EV-BP0508-0022` | completion_reporting, governance | not audited |
| `IT-BP0508-0020` Pilot migration remains separately authorized | process_rule | accepted | critical | `EV-BP0508-0023`, `EV-BP0508-0038` | pilot, operator_approval | not audited |
| `IT-BP0508-0021` External rollout remains gated until explicit authorization | process_rule | accepted | critical | `EV-BP0508-0024` | rollout, governance | not audited |
| `IT-BP0508-0022` Blueprint needs its own status/prompts/reports indexing surfaces | requirement | discussed | high | `EV-BP0508-0025` | forprint_system_blueprint, indexes | not audited |
| `IT-BP0508-0023` Governance workflow must be stable and unambiguous | nonfunctional_requirement | agreed | critical | `EV-BP0508-0026` | governance, operability | not audited |
| `IT-BP0508-0024` Prompt workflow received governance closeout inventory | implementation_claim | accepted | normal | `EV-BP0508-0027` | prompt_lifecycle, governance | not audited |
| `IT-BP0508-0025` Operational readiness became a formal review workfront | implementation_claim | accepted | high | `EV-BP0508-0028`, `EV-BP0508-0031` | operational_readiness, governance | not audited |
| `IT-BP0508-0026` Write-flow recovery was classified and bounded-reviewed | implementation_claim | accepted | high | `EV-BP0508-0029`, `EV-BP0508-0030` | write_flow, recovery | not audited |
| `IT-BP0508-0027` Validator behavior is formalized as a contract | requirement | accepted | critical | `EV-BP0508-0032` | validation, governance | not audited |
| `IT-BP0508-0028` Write/mutation architecture uses exact contracts | requirement | accepted | critical | `EV-BP0508-0033` | write_flow, governance | not audited |
| `IT-BP0508-0029` Project transparency has a durable machine-readable baseline | requirement | accepted | critical | `EV-BP0508-0034` | transparency, governance | not audited |
| `IT-BP0508-0030` Canonical mutation builder contract | requirement | accepted | critical | `EV-BP0508-0035`, `EV-BP0508-0037` | mutation_builder, governance | not audited |
| `IT-BP0508-0031` Mutation path preserves rollback | process_rule | accepted | critical | `EV-BP0508-0039` | mutation_builder, rollback | not audited |
| `IT-BP0508-0032` Mutation-builder integration historically passed canonical gate | implementation_claim | accepted | high | `EV-BP0508-0036`, `EV-BP0508-0037`, `EV-BP0508-0042` | mutation_builder, validation | not audited |
| `IT-BP0508-0033` Current-state transparency manifest is next control-layer step | plan | accepted | critical | `EV-BP0508-0040` | transparency, governance | not audited |
| `IT-BP0508-0034` Read-only governance status command is next control-layer step | plan | accepted | critical | `EV-BP0508-0043` | transparency, make, command_semantics | not audited |
| `IT-BP0508-0035` Transparency control layer exposes phase blockers boundaries dependencies and next action | requirement | accepted | critical | `EV-BP0508-0045` | transparency, operator_ux | not audited |
| `IT-BP0508-0036` Transparency view includes roughly ten-step forward plan | requirement | accepted | high | `EV-BP0508-0041` | transparency, roadmap | not audited |
| `IT-BP0508-0037` Do not authorize pilot before control layer is explicit | process_rule | accepted | critical | `EV-BP0508-0038`, `EV-BP0508-0046` | pilot, transparency | not audited |
| `IT-BP0508-0038` Session handoff must carry exact current state and reading path | process_rule | agreed | critical | `EV-BP0508-0044`, `EV-BP0508-0045` | continuity, bootstrap | not audited |
| `IT-BP0508-0039` Markdown/document structural cleanup became a prolonged maintenance stream | risk | accepted | normal | `EV-BP0508-0006` | documentation, repository_hygiene | not audited |
| `IT-BP0508-0040` Canonical gates and authorization states remain distinct | process_rule | accepted | critical | `EV-BP0508-0036`, `EV-BP0508-0038`, `EV-BP0508-0024` | governance, validation | not audited |
