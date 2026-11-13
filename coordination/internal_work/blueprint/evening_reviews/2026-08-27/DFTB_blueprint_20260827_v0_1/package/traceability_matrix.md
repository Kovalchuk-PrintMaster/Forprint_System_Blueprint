# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Domain | Audit |
|---|---|---|---|---|---|---|
| `IT-BP2708-0001` Live authority after context loss | process_rule | accepted | critical | `EV-BP2708-0001`, `EV-BP2708-0002` | bootstrap, authority | not audited |
| `IT-BP2708-0002` Governance evolves forward | process_rule | agreed | critical | `EV-BP2708-0006`, `EV-BP2708-0007` | governance, architecture | not audited |
| `IT-BP2708-0003` Significant project memory belongs in repository | process_rule | agreed | critical | `EV-BP2708-0008` | governance, project_memory | not audited |
| `IT-BP2708-0004` Persist decision rationale | requirement | agreed | critical | `EV-BP2708-0009` | project_memory, governance | not audited |
| `IT-BP2708-0005` Avoid documentation/directory proliferation | architecture_constraint | agreed | high | `EV-BP2708-0010`, `EV-BP2708-0011` | repository_structure, documentation | not audited |
| `IT-BP2708-0006` Roadmap and prompts are planning backbone | process_rule | agreed | critical | `EV-BP2708-0012` | roadmap, prompt_lifecycle | not audited |
| `IT-BP2708-0007` Large scripts are files; terminal commands stay short | process_rule | agreed | normal | `EV-BP2708-0013` | tooling, operator_ux | not audited |
| `IT-BP2708-0008` Prevent stale/duplicate artifact identity | risk | agreed | high | `EV-BP2708-0014`, `EV-BP2708-0036` | tooling, artifact_identity | not audited |
| `IT-BP2708-0009` Automatic work cannot require globally clean trees | process_rule | agreed | critical | `EV-BP2708-0015`, `EV-BP2708-0017` | git_workflow, automation | not audited |
| `IT-BP2708-0010` Use bounded execution baselines | requirement | agreed | critical | `EV-BP2708-0016`, `EV-BP2708-0017` | git_workflow, coordination_runtime | not audited |
| `IT-BP2708-0011` Parallel-work semantics must be explicit | process_rule | agreed | critical | `EV-BP2708-0018` | governance, git_workflow | not audited |
| `IT-BP2708-0012` B2 explicitly accepted | decision | accepted | high | `EV-BP2708-0019` | B2, phase_progression | not audited |
| `IT-BP2708-0013` Q2 explicitly activated | decision | accepted | high | `EV-BP2708-0020` | Q2, phase_progression | not audited |
| `IT-BP2708-0014` Manual confirmation only at major phase boundaries | process_rule | agreed | critical | `EV-BP2708-0021` | phase_progression, operator_approval | not audited |
| `IT-BP2708-0015` Same-phase deterministic progression | process_rule | agreed | critical | `EV-BP2708-0022` | phase_progression, automation | not audited |
| `IT-BP2708-0016` Q2 concept-audit safe failure did not advance phase | implementation_claim | accepted | high | `EV-BP2708-0023` | Q2, concept_audit | not audited |
| `IT-BP2708-0017` Module concept audit retained as durable evidence | plan | accepted | normal | `EV-BP2708-0024` | portfolio, module_concepts | not audited |
| `IT-BP2708-0018` Operations Assistant enters portfolio concept space | plan | agreed | high | `EV-BP2708-0025`, `EV-BP2708-0026` | forprint_operations_assistant, portfolio | not audited |
| `IT-BP2708-0019` Filters need top and bottom collapse controls | ux_requirement | agreed | normal | `EV-BP2708-0027` | ui, product_editor | not audited |
| `IT-BP2708-0020` Remove inconsistent filter background | ux_requirement | agreed | low | `EV-BP2708-0028` | ui, product_editor | not audited |
| `IT-BP2708-0021` Normalize related-product button styling | ux_requirement | agreed | low | `EV-BP2708-0029`, `EV-BP2708-0030` | ui, product_editor | not audited |
| `IT-BP2708-0022` Identify owner of product-editor UI branch | open_question | unclear | normal | `EV-BP2708-0027`, `EV-BP2708-0029` | ui, product_editor | not audited |
| `IT-BP2708-0023` Logistics is sole automation-validation pilot | process_rule | agreed | critical | `EV-BP2708-0031`, `EV-BP2708-0038` | logistics_service, portfolio | not audited |
| `IT-BP2708-0024` Minimum two successful real automatic runs | acceptance_criterion | agreed | critical | `EV-BP2708-0032`, `EV-BP2708-0039` | logistics_service, automation_pilot | not audited |
| `IT-BP2708-0025` Expansion requires positive review and separate decision | process_rule | agreed | critical | `EV-BP2708-0033`, `EV-BP2708-0038` | portfolio, operator_approval | not audited |
| `IT-BP2708-0026` Maintain portfolio/module knowledge snapshot | requirement | agreed | high | `EV-BP2708-0034`, `EV-BP2708-0041` | portfolio, knowledge | not audited |
| `IT-BP2708-0027` Maintain Blueprint self-knowledge snapshot | requirement | agreed | high | `EV-BP2708-0034`, `EV-BP2708-0035` | forprint_system_blueprint, knowledge | not audited |
| `IT-BP2708-0028` Logistics-only pilot documentation was published | implementation_claim | accepted | high | `EV-BP2708-0038`, `EV-BP2708-0039` | logistics_service, H10 | not audited |
| `IT-BP2708-0029` H10 current, H11 inactive at checkpoint | implementation_claim | accepted | high | `EV-BP2708-0040` | H10, H11 | not audited |
| `IT-BP2708-0030` Module knowledge snapshot integrity passed | implementation_claim | accepted | normal | `EV-BP2708-0041` | knowledge, portfolio | not audited |
| `IT-BP2708-0031` Portfolio snapshot contained 21 module IDs | implementation_claim | accepted | normal | `EV-BP2708-0042` | portfolio, module_registry | not audited |
| `IT-BP2708-0032` Blueprint self-analysis is an ongoing workstream | process_rule | agreed | high | `EV-BP2708-0035` | forprint_system_blueprint, knowledge | not audited |
| `IT-BP2708-0033` Mutation tooling must fail closed | process_rule | accepted | high | `EV-BP2708-0005`, `EV-BP2708-0037` | tooling, safe_mutation | not audited |
| `IT-BP2708-0034` Artifact identity should be checked before mutation | process_rule | agreed | high | `EV-BP2708-0036`, `EV-BP2708-0037` | tooling, artifact_identity | not audited |
