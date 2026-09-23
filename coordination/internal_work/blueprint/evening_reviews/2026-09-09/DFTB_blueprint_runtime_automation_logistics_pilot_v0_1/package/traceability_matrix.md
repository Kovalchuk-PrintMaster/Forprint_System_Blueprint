# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Domain | Audit |
|---|---|---|---|---|---|---|
| `IT-BP0909-0001` Release authority first | process_rule | accepted | critical | `EV-BP0909-0001` | bootstrap, governance | not audited |
| `IT-BP0909-0002` Generated task context preferred | process_rule | accepted | high | `EV-BP0909-0002` | bootstrap, context_compiler | not audited |
| `IT-BP0909-0003` Fail closed on missing evidence | process_rule | accepted | critical | `EV-BP0909-0006` | release, coordination | not audited |
| `IT-BP0909-0004` Unique archive names | process_rule | agreed | high | `EV-BP0909-0009` | handoff, tooling | not audited |
| `IT-BP0909-0005` Durable module self-knowledge | requirement | agreed | critical | `EV-BP0909-0010` | logistics_service, module_self_knowledge | not audited |
| `IT-BP0909-0006` Fresh worker per substantial prompt | process_rule | agreed | critical | `EV-BP0909-0011` | worker_runtime | not audited |
| `IT-BP0909-0007` Generated strong worker snapshot | requirement | agreed | critical | `EV-BP0909-0012`, `EV-BP0909-0007` | context_compiler, worker_runtime | not audited |
| `IT-BP0909-0008` Manual pilot before widening | process_rule | agreed | critical | `EV-BP0909-0013` | logistics_service, automation_pilot | not audited |
| `IT-BP0909-0009` Automatic within-pool loop | workflow | agreed | critical | `EV-BP0909-0014` | coordination_runtime | not audited |
| `IT-BP0909-0010` Manual major-pool acceptance | process_rule | agreed | critical | `EV-BP0909-0015`, `EV-BP0909-0008` | operator_approval | not audited |
| `IT-BP0909-0011` Listener/dispatcher ownership | open_question | discussed | high | `EV-BP0909-0016` | listener_dispatcher | not audited |
| `IT-BP0909-0012` Durable documentation of agreements | process_rule | agreed | critical | `EV-BP0909-0017` | documentation, governance | not audited |
| `IT-BP0909-0013` Clean nested repository structure | architecture_constraint | agreed | high | `EV-BP0909-0018`, `EV-BP0909-0019` | repository_structure | not audited |
| `IT-BP0909-0014` Blueprint avoids foreign-repo Git repair | architecture_constraint | agreed | high | `EV-BP0909-0020` | forprint_system_blueprint, module_repositories | not audited |
| `IT-BP0909-0015` Module-local baseline preflight | process_rule | agreed | high | `EV-BP0909-0021` | module_assistants, git_workflow | not audited |
| `IT-BP0909-0016` Automated inventory/index maintenance first | requirement | agreed | critical | `EV-BP0909-0022` | logistics_service, module_self_knowledge | not audited |
| `IT-BP0909-0017` Single canonical startup entry | requirement | agreed | critical | `EV-BP0909-0023`, `EV-BP0909-0027` | bootstrap, continuity | not audited |
| `IT-BP0909-0018` Old continuity START_HERE becomes history | decision | discussed | critical | `EV-BP0909-0024`, `EV-BP0909-0025` | continuity, history | not audited |
| `IT-BP0909-0019` Stable mission separated from history | decision | discussed | high | `EV-BP0909-0026` | global_policy | not audited |
| `IT-BP0909-0020` Broad default context | requirement | discussed | high | `EV-BP0909-0028` | context_compiler, bootstrap | not audited |
| `IT-BP0909-0021` History excluded from default context | process_rule | discussed | high | `EV-BP0909-0029` | context_compiler, knowledge | not audited |
| `IT-BP0909-0022` Task Context Compiler | plan | accepted | critical | `EV-BP0909-0037`, `EV-BP0909-0038` | task_context_compiler | not audited |
| `IT-BP0909-0023` Operator Approval Gateway | plan | accepted | critical | `EV-BP0909-0039`, `EV-BP0909-0040` | operator_approval | not audited |
| `IT-BP0909-0024` Console Worker Adapter | plan | accepted | high | `EV-BP0909-0041`, `EV-BP0909-0042` | worker_runtime, console_adapter | not audited |
| `IT-BP0909-0025` Central Listener / Dispatcher / Monitor | plan | accepted | critical | `EV-BP0909-0043`, `EV-BP0909-0044` | listener_dispatcher | not audited |
| `IT-BP0909-0026` Completion Intake + Inspector Conformance | plan | accepted | critical | `EV-BP0909-0045`, `EV-BP0909-0046` | completion_intake, forprint_project_inspector | not audited |
| `IT-BP0909-0027` Approval-gated Logistics pilot preflight | process_rule | accepted | critical | `EV-BP0909-0047` | logistics_service, operator_approval | not audited |
| `IT-BP0909-0028` Prompt-scoped dependency readiness | requirement | accepted | critical | `EV-BP0909-0048` | dependency_readiness | not audited |
| `IT-BP0909-0029` Module bootstrap execution policy | process_rule | accepted | high | `EV-BP0909-0049` | bootstrap, portfolio | not audited |
| `IT-BP0909-0030` Bootstrap task-context mode | requirement | accepted | high | `EV-BP0909-0050` | bootstrap, task_context_compiler | not audited |
| `IT-BP0909-0031` Worker runtime profile | requirement | accepted | high | `EV-BP0909-0051` | worker_runtime, governance | not audited |
| `IT-BP0909-0032` Project Inspector registry binding | requirement | accepted | high | `EV-BP0909-0052` | forprint_project_inspector, module_registry | not audited |
| `IT-BP0909-0033` Versioned Logistics bootstrap prompt | requirement | accepted | high | `EV-BP0909-0053` | logistics_service, prompt_lifecycle | not audited |
| `IT-BP0909-0034` Self-knowledge / roadmap reconciliation | requirement | accepted | critical | `EV-BP0909-0054`, `EV-BP0909-0055` | module_self_knowledge, roadmap | not audited |
| `IT-BP0909-0035` Module preparation registry / queue | requirement | accepted | high | `EV-BP0909-0056` | portfolio, module_registry, queue | not audited |
| `IT-BP0909-0036` Inspector provisioning gap resolution | open_question | accepted | high | `EV-BP0909-0057` | forprint_project_inspector | not audited |
| `IT-BP0909-0037` Zero-context startup authority audit | process_rule | accepted | high | `EV-BP0909-0058`, `EV-BP0909-0059` | bootstrap, continuity | not audited |
| `IT-BP0909-0038` u175 safe failure and rollback | implementation_claim | accepted | high | `EV-BP0909-0030`, `EV-BP0909-0031` | bootstrap, tooling | not audited |
| `IT-BP0909-0039` u175a rerun prepared | implementation_claim | accepted | high | `EV-BP0909-0032`, `EV-BP0909-0060` | bootstrap, tooling | not audited |
