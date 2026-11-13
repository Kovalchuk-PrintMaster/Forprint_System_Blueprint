# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Domain | Audit |
|---|---|---|---|---|---|---|
| `IT-BP0508C-0001` Continuation must re-verify observed repository state | process_rule | accepted | critical | `EV-BP0508C-0001`, `EV-BP0508C-0002` | continuity, git_workflow | not audited |
| `IT-BP0508C-0002` Transparency control layer continues after mutation-builder checkpoint | plan | accepted | high | `EV-BP0508C-0003` | transparency, governance | not audited |
| `IT-BP0508C-0003` Makefile remains a primary architecture/operations map | process_rule | agreed | critical | `EV-BP0508C-0004` | make, forprint_system_blueprint | not audited |
| `IT-BP0508C-0004` Avoid temporary cloned repositories as routine parallel-work mechanism | process_rule | agreed | high | `EV-BP0508C-0005`, `EV-BP0508C-0006` | git_workflow, repository_structure | not audited |
| `IT-BP0508C-0005` Completion-intake blocker review classified managed modules | implementation_claim | accepted | normal | `EV-BP0508C-0007`, `EV-BP0508C-0008` | completion_intake, portfolio | not audited |
| `IT-BP0508C-0006` Completion-intake semantics must be durably documented | process_rule | agreed | critical | `EV-BP0508C-0009`, `EV-BP0508C-0011` | completion_intake, project_memory | not audited |
| `IT-BP0508C-0007` Finish automatic completion-report intake before next automation step | plan | agreed | critical | `EV-BP0508C-0010`, `EV-BP0508C-0011` | completion_intake, automation | not audited |
| `IT-BP0508C-0008` Prompt issuance and completion reporting use a standardized exchange contract | requirement | agreed | critical | `EV-BP0508C-0012` | prompt_lifecycle, completion_reporting | not audited |
| `IT-BP0508C-0009` Completion evidence includes task-level and final test evidence | acceptance_criterion | agreed | high | `EV-BP0508C-0013` | completion_reporting, tests | not audited |
| `IT-BP0508C-0010` v0.3 completion/publication chain was not yet working end to end | risk | accepted | high | `EV-BP0508C-0014` | v0_3, completion_intake | not audited |
| `IT-BP0508C-0011` Roadmaps maintain a 5–8-step minimum forward horizon | process_rule | agreed | critical | `EV-BP0508C-0015` | roadmap, portfolio | not audited |
| `IT-BP0508C-0012` Maintain at least two draft prompts beyond active work | process_rule | agreed | critical | `EV-BP0508C-0016` | prompt_lifecycle, portfolio | not audited |
| `IT-BP0508C-0013` Low roadmap/prompt buffer is warning-level health, not automatic stop | process_rule | agreed | high | `EV-BP0508C-0017` | health, roadmap, prompt_lifecycle | not audited |
| `IT-BP0508C-0014` Module completion availability is machine-discoverable | requirement | agreed | critical | `EV-BP0508C-0018` | completion_intake, module_assistants | not audited |
| `IT-BP0508C-0015` Completion intake is part of the normal coordination command chain | requirement | agreed | critical | `EV-BP0508C-0018`, `EV-BP0508C-0019` | completion_intake, coordination_runtime | not audited |
| `IT-BP0508C-0016` Prompt queue has deterministic default order plus operator override | process_rule | agreed | high | `EV-BP0508C-0020` | prompt_queue, operator_approval | not audited |
| `IT-BP0508C-0017` Prompts and reports bind to roadmap items | requirement | agreed | critical | `EV-BP0508C-0021` | roadmap, prompt_lifecycle, completion_reporting | not audited |
| `IT-BP0508C-0018` Accepted completion can activate the next prompt under explicit algorithm | workflow | agreed | critical | `EV-BP0508C-0022` | automation, prompt_lifecycle | not audited |
| `IT-BP0508C-0019` v0.4 targets a closed-loop coordination cycle | plan | agreed | critical | `EV-BP0508C-0023` | v0_4, coordination_runtime | not audited |
| `IT-BP0508C-0020` v0.4 master prompt doubles as continuity package | requirement | agreed | critical | `EV-BP0508C-0024`, `EV-BP0508C-0025` | v0_4, continuity | not audited |
| `IT-BP0508C-0021` Accepted/completed prompts leave approved/current surfaces | process_rule | agreed | high | `EV-BP0508C-0026`, `EV-BP0508C-0027` | prompt_lifecycle, repository_hygiene | not audited |
| `IT-BP0508C-0022` STEP20 publication verification historically passed | implementation_claim | accepted | normal | `EV-BP0508C-0028`, `EV-BP0508C-0029` | v0_4, STEP20 | not audited |
| `IT-BP0508C-0023` Website/UI side branch is not promoted into Blueprint governance requirements | rejected_alternative | unclear | normal | `EV-BP0508C-0030`, `EV-BP0508C-0031` | website, scope_control | not audited |
| `IT-BP0508C-0024` Latest current documentation outranks stale contradictory docs during active work | process_rule | agreed | high | `EV-BP0508C-0032` | governance, documentation | not audited |
| `IT-BP0508C-0025` STEP26 acceptance subject was historically published | implementation_claim | accepted | high | `EV-BP0508C-0033` | v0_4, STEP26 | not audited |
| `IT-BP0508C-0026` STEP26 seal verification must not execute STEP27 work or global promotion | process_rule | accepted | critical | `EV-BP0508C-0034`, `EV-BP0508C-0035` | v0_4, STEP26, STEP27 | not audited |
| `IT-BP0508C-0027` First STEP26 seal attempt safe-failed on expected dirty seal paths | implementation_claim | accepted | normal | `EV-BP0508C-0036` | STEP26, safe_mutation | not audited |
| `IT-BP0508C-0028` End state has STEP27 approved and ready for module pull | implementation_claim | accepted | high | `EV-BP0508C-0037` | STEP27, prompt_lifecycle | not audited |
| `IT-BP0508C-0029` STEP26 manual seal commit remained pending at source end | implementation_claim | accepted | high | `EV-BP0508C-0038`, `EV-BP0508C-0039` | STEP26, publication | not audited |
| `IT-BP0508C-0030` Global v0.4 promotion remains a separate decision | process_rule | accepted | critical | `EV-BP0508C-0040` | v0_4, promotion | not audited |
| `IT-BP0508C-0031` Automatic acceptance is not assumed from completion evidence | process_rule | discussed | critical | `EV-BP0508C-0019` | completion_intake, operator_approval | not audited |
| `IT-BP0508C-0032` Roadmap, prompt queue and real implementation state can drift apart | risk | accepted | critical | `EV-BP0508C-0021`, `EV-BP0508C-0023` | roadmap, prompt_lifecycle, coordination_runtime | not audited |
| `IT-BP0508C-0033` Completion discovery should not depend on chat notifications | process_rule | agreed | critical | `EV-BP0508C-0018` | completion_intake, continuity | not audited |
| `IT-BP0508C-0034` Current work should favor canonical Git state over temporary synchronized copies | process_rule | agreed | high | `EV-BP0508C-0005`, `EV-BP0508C-0006` | git_workflow, continuity | not audited |
