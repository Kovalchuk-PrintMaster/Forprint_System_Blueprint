# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Domain | Audit |
|---|---|---|---|---|---|---|
| `IT-BP1406-0001` Blueprint coordinator keeps portfolio and module plans aligned | process_rule | agreed | critical | `EV-BP1406-0002`, `EV-BP1406-0003`, `EV-BP1406-0010`, `EV-BP1406-0015` | forprint_system_blueprint, portfolio | not audited |
| `IT-BP1406-0002` Do not let one module outrun dependencies | process_rule | accepted | critical | `EV-BP1406-0003` | portfolio, dependency_management | not audited |
| `IT-BP1406-0003` Avoid fake dependency truth as normal strategy | architecture_constraint | agreed | high | `EV-BP1406-0005` | data_architecture, module_assistants | not audited |
| `IT-BP1406-0004` Library readiness historically blocks Calculator and Telegram | risk | accepted | high | `EV-BP1406-0006` | forprint_library, calculator_engine, telegram_bot | not audited |
| `IT-BP1406-0005` Telegram + Logistics as parallel self-contained automation line | plan | agreed | high | `EV-BP1406-0007` | telegram_bot, logistics_service | not audited |
| `IT-BP1406-0006` Calculator is a priority business module | plan | agreed | critical | `EV-BP1406-0008` | calculator_engine | not audited |
| `IT-BP1406-0007` Telegram is a priority operational module | plan | agreed | critical | `EV-BP1406-0009` | telegram_bot | not audited |
| `IT-BP1406-0008` Maintain global and per-module roadmaps | process_rule | agreed | critical | `EV-BP1406-0010` | roadmap, portfolio | not audited |
| `IT-BP1406-0009` Roadmaps should carry meaningful forward depth | process_rule | agreed | high | `EV-BP1406-0015` | roadmap, coordination | not audited |
| `IT-BP1406-0010` Do not invent the next front | process_rule | agreed | critical | `EV-BP1406-0012`, `EV-BP1406-0013`, `EV-BP1406-0014` | prompt_lifecycle, roadmap | not audited |
| `IT-BP1406-0011` Complete integrated prompt/report coordination workflow | requirement | agreed | high | `EV-BP1406-0011` | coordination_runtime, tooling | not audited |
| `IT-BP1406-0012` Regular reports are compact and table-first | nonfunctional_requirement | agreed | high | `EV-BP1406-0016`, `EV-BP1406-0026` | reporting, operator_ux | not audited |
| `IT-BP1406-0013` Status reports use consistent visual/color semantics | ux_requirement | agreed | normal | `EV-BP1406-0017` | reporting, operator_ux | not audited |
| `IT-BP1406-0014` Detailed reports end with compact colored summary | requirement | agreed | high | `EV-BP1406-0027` | reporting, operator_ux | not audited |
| `IT-BP1406-0015` Blueprint dogfoods shared standards | process_rule | agreed | high | `EV-BP1406-0018` | forprint_system_blueprint, governance | not audited |
| `IT-BP1406-0016` Document process and rule evolution durably | process_rule | agreed | critical | `EV-BP1406-0019` | project_memory, governance | not audited |
| `IT-BP1406-0017` Propagate shared workflow changes into templates/standards/policy | process_rule | agreed | critical | `EV-BP1406-0020`, `EV-BP1406-0021`, `EV-BP1406-0022` | make, standards, module_policy | not audited |
| `IT-BP1406-0018` Closeout includes documentation and replayability | process_rule | agreed | critical | `EV-BP1406-0023` | closeout, project_memory | not audited |
| `IT-BP1406-0019` Library business-card configurable-product skeleton reported complete | implementation_claim | accepted | high | `EV-BP1406-0024`, `EV-BP1406-0025` | forprint_library | not audited |
| `IT-BP1406-0020` Repository-knowledge input supports Blueprint self-analysis | requirement | accepted | high | `EV-BP1406-0028` | forprint_system_blueprint, knowledge | not audited |
| `IT-BP1406-0021` Reports must be semantically consumed, not merely generated | open_question | agreed | high | `EV-BP1406-0031`, `EV-BP1406-0032` | analytics, governance | not audited |
| `IT-BP1406-0022` Build a reusable Blueprint repository self-analysis capability | plan | discussed | high | `EV-BP1406-0030`, `EV-BP1406-0033`, `EV-BP1406-0034` | forprint_system_blueprint, self_analysis | not audited |
| `IT-BP1406-0023` Self-analysis covers newly added files | requirement | discussed | high | `EV-BP1406-0034` | self_analysis, knowledge | not audited |
| `IT-BP1406-0024` New scripts carry machine-readable responsibility metadata | process_rule | agreed | critical | `EV-BP1406-0035`, `EV-BP1406-0036`, `EV-BP1406-0037` | standards, script_metadata | not audited |
| `IT-BP1406-0025` Audit metadata against actual code behavior | requirement | agreed | critical | `EV-BP1406-0038`, `EV-BP1406-0039` | script_metadata, self_analysis | not audited |
| `IT-BP1406-0026` Flag metadata-update candidates instead of constant manual edits | workflow | agreed | high | `EV-BP1406-0038`, `EV-BP1406-0039` | script_metadata, maintenance | not audited |
| `IT-BP1406-0027` Promote script-metadata/audit model into general policy | process_rule | agreed | critical | `EV-BP1406-0035`, `EV-BP1406-0040` | governance, standards | not audited |
| `IT-BP1406-0028` Coordination information should be quickly visually scannable | nonfunctional_requirement | agreed | high | `EV-BP1406-0016`, `EV-BP1406-0017` | operator_ux, coordination | not audited |
| `IT-BP1406-0029` Shared standards should converge module behavior | architecture_constraint | agreed | critical | `EV-BP1406-0018`, `EV-BP1406-0019` | portfolio, standards | not audited |
| `IT-BP1406-0030` Session replacement must be recoverable from project artifacts | process_rule | agreed | critical | `EV-BP1406-0001`, `EV-BP1406-0019` | continuity, project_memory | not audited |
| `IT-BP1406-0031` Source filename date is not reliable chronology | risk | accepted | normal | `EV-BP1406-0024` | provenance | not audited |
| `IT-BP1406-0032` Module completion evidence should support coordinator acceptance review | acceptance_criterion | accepted | high | `EV-BP1406-0024` | completion_reporting, coordination | not audited |
