# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Domains | Audit |
|---|---|---|---|---|---|---|
| `IT-BP1407-0001` Blueprint as architecture truth layer | architecture_constraint | agreed | critical | `EV-BP1407-0001`, `EV-BP1407-0010` | forprint_system_blueprint | not audited |
| `IT-BP1407-0002` Maximum practical automation | requirement | agreed | critical | `EV-BP1407-0002` | ecosystem | not audited |
| `IT-BP1407-0003` Project Inspector separated from Blueprint | architecture_constraint | agreed | high | `EV-BP1407-0003`, `EV-BP1407-0011` | forprint_project_inspector, forprint_system_blueprint | not audited |
| `IT-BP1407-0004` CRM as business orchestration layer | architecture_constraint | agreed | high | `EV-BP1407-0001` | forprint_crm | not audited |
| `IT-BP1407-0005` Library scope must remain canonical/reference-oriented | architecture_constraint | discussed | high | `EV-BP1407-0013` | forprint_library | not audited |
| `IT-BP1407-0006` Calculator owns calculation logic | architecture_constraint | agreed | critical | `EV-BP1407-0004` | calculator_engine | not audited |
| `IT-BP1407-0007` Prepress file intake and preparation | requirement | agreed | high | `EV-BP1407-0001` | forprint_prepress_hub | not audited |
| `IT-BP1407-0008` 1C synchronization boundary | integration | agreed | critical | `EV-BP1407-0005` | forprint_accounting_registry_service, 1C | not audited |
| `IT-BP1407-0009` Website should not hard-own customer truth | architecture_constraint | agreed | high | `EV-BP1407-0006` | website, business_data_owner | not audited |
| `IT-BP1407-0010` Telegram AI escalation | workflow | agreed | critical | `EV-BP1407-0008` | telegram_bot, AI | not audited |
| `IT-BP1407-0011` Telegram is an operational interface, not canonical truth | architecture_constraint | discussed | critical | `EV-BP1407-0007`, `EV-BP1407-0012` | telegram_bot | not audited |
| `IT-BP1407-0012` Separate Logistics service | plan | agreed | high | `EV-BP1407-0009` | logistics_service, telegram_bot | not audited |
| `IT-BP1407-0013` Separate Warehouse capability | plan | discussed | high | `EV-BP1407-0001` | warehouse_service | not audited |
| `IT-BP1407-0014` Backup Manager reuse | plan | agreed | normal | `EV-BP1407-0001` | cloud_backup_manager | not audited |
| `IT-BP1407-0015` Production runtime inspection | plan | agreed | normal | `EV-BP1407-0001` | production_runtime_inspector | not audited |
| `IT-BP1407-0016` Per-module manifest | process_rule | discussed | high | `EV-BP1407-0014` | ecosystem, forprint_project_inspector | not audited |
| `IT-BP1407-0017` Blueprint changes trigger affected-module review | process_rule | discussed | high | `EV-BP1407-0010` | forprint_system_blueprint, forprint_project_inspector | not audited |
| `IT-BP1407-0018` Version architecture decisions in Git/ADR | process_rule | discussed | high | `EV-BP1407-0010` | forprint_system_blueprint | not audited |
| `IT-BP1407-0019` Start with text/machine architecture, not visual editor | plan | discussed | normal | `EV-BP1407-0010` | forprint_system_blueprint | not audited |
| `IT-BP1407-0020` Generate module guidance from architecture truth | plan | discussed | high | `EV-BP1407-0010` | forprint_system_blueprint, module_assistants | not audited |
| `IT-BP1407-0021` Bootstrap Gateway if absent | process_rule | agreed | normal | `EV-BP1407-0015` | forprint_integration_gateway | not audited |
| `IT-BP1407-0022` Accounting Registry vs Operational Registry boundary | open_question | unclear | critical | `EV-BP1407-0005` | forprint_accounting_registry_service, forprint_operational_registry | not audited |
| `IT-BP1407-0023` Calculator and Telegram remain priority development fronts | process_rule | agreed | high | `EV-BP1407-0016` | calculator_engine, telegram_bot | not audited |
| `IT-BP1407-0024` Temporary Calculator catalog allowed | plan | agreed | high | `EV-BP1407-0017` | calculator_engine | not audited |
| `IT-BP1407-0025` Use coherent work packages, not excessive micro-prompts | process_rule | agreed | normal | `EV-BP1407-0018` | module_assistants, coordination | not audited |
| `IT-BP1407-0026` Durable execution queue with priority | process_rule | agreed | critical | `EV-BP1407-0019` | forprint_system_blueprint, coordination | not audited |
| `IT-BP1407-0027` Assistants discover directive changes | process_rule | agreed | high | `EV-BP1407-0020` | instruction_intake, module_assistants | not audited |
| `IT-BP1407-0028` Makefile lint autofix pre-step | process_rule | agreed | normal | `EV-BP1407-0021` | forprint_system_blueprint, tooling | not audited |
| `IT-BP1407-0029` Strategic Control Plane planned separately | plan | agreed | high | `EV-BP1407-0022` | forprint_strategic_control_plane | not audited |
| `IT-BP1407-0030` Harvest proven Gateway prompt-reading scripts | plan | agreed | normal | `EV-BP1407-0023`, `EV-BP1407-0024` | forprint_integration_gateway, module_assistants | not audited |
| `IT-BP1407-0031` Continuous standards awareness | process_rule | agreed | critical | `EV-BP1407-0025`, `EV-BP1407-0026` | module_assistants, coordination/standards | not audited |
| `IT-BP1407-0032` Completion packet tooling | requirement | agreed | high | `EV-BP1407-0027` | forprint_system_blueprint, module_assistants | not audited |
| `IT-BP1407-0033` Standardize interfaces, not one universal script | process_rule | agreed | high | `EV-BP1407-0028` | module_assistants, coordination | not audited |
| `IT-BP1407-0034` Prefer project-relative paths | process_rule | agreed | normal | `EV-BP1407-0029` | documentation, module_assistants | not audited |
| `IT-BP1407-0035` Do not duplicate established coordination paths | architecture_constraint | agreed | high | `EV-BP1407-0030` | coordination | not audited |
| `IT-BP1407-0036` Keep colored terminal output | ux_requirement | agreed | low | `EV-BP1407-0031` | tooling, operator_ui | not audited |
| `IT-BP1407-0037` Color entire status rows | ux_requirement | agreed | low | `EV-BP1407-0032` | operator_ui, tooling | not audited |
| `IT-BP1407-0038` Automate reporting updates | requirement | agreed | high | `EV-BP1407-0033` | reporting, module_assistants | not audited |
| `IT-BP1407-0039` Common assistant rules are global, not module-specific | process_rule | agreed | high | `EV-BP1407-0034` | coordination/standards, module_assistants | not audited |
| `IT-BP1407-0040` Close/archive executed prompt drafts | process_rule | agreed | high | `EV-BP1407-0035` | coordination/outgoing_prompts | not audited |
| `IT-BP1407-0041` Roadmap must be explicitly maintained | requirement | agreed | critical | `EV-BP1407-0036` | roadmap, coordination | not audited |
| `IT-BP1407-0042` Logistics as assistant-workflow pilot | plan | accepted | high | `EV-BP1407-0037`, `EV-BP1407-0039` | logistics_service, module_assistants | not audited |
| `IT-BP1407-0043` Living assistant productivity standard | process_rule | accepted | critical | `EV-BP1407-0038`, `EV-BP1407-0040` | module_assistants, forprint_system_blueprint | not audited |
| `IT-BP1407-0044` Reduce coordination overhead | nonfunctional_requirement | accepted | normal | `EV-BP1407-0038` | module_assistants, coordination | not audited |
| `IT-BP1407-0045` Dedicated Blueprint assistant | open_question | proposed | normal | `EV-BP1407-0041` | forprint_system_blueprint, AI_assistant | not audited |
| `IT-BP1407-0046` Gradual assistant rollout | process_rule | agreed | high | `EV-BP1407-0027`, `EV-BP1407-0038` | module_assistants, coordination | not audited |
| `IT-BP1407-0047` Controlled AI tool permissions | requirement | discussed | critical | `EV-BP1407-0008`, `EV-BP1407-0012` | telegram_bot, AI, security | not audited |
