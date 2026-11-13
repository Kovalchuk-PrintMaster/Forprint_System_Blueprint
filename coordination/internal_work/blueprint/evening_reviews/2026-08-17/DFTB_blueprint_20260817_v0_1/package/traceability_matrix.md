# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Domain | Audit |
|---|---|---|---|---|---|---|
| `IT-BP1708-0001` Live state outranks stale handoff archives | process_rule | accepted | critical | `EV-BP1708-0001`, `EV-BP1708-0002` | continuity, authority | not audited |
| `IT-BP1708-0002` Makefile is the primary operational surface | process_rule | agreed | critical | `EV-BP1708-0007` | tooling, forprint_system_blueprint | not audited |
| `IT-BP1708-0003` Blueprint coordinates; module assistants implement | architecture_constraint | agreed | critical | `EV-BP1708-0008`, `EV-BP1708-0009` | forprint_system_blueprint, module_assistants | not audited |
| `IT-BP1708-0004` Normal inter-module coordination uses internal Make mechanisms | process_rule | agreed | high | `EV-BP1708-0010` | coordination_runtime, tooling | not audited |
| `IT-BP1708-0005` STEP27 is reference-chain validation, not feature rewrite | architecture_constraint | accepted | high | `EV-BP1708-0003`, `EV-BP1708-0004` | logistics_service, v0_4 | not audited |
| `IT-BP1708-0006` Blueprint must respect module-owned artifacts | architecture_constraint | accepted | critical | `EV-BP1708-0005` | forprint_system_blueprint, module_repositories | not audited |
| `IT-BP1708-0007` No automatic acceptance or promotion from review readiness | process_rule | accepted | critical | `EV-BP1708-0006`, `EV-BP1708-0012`, `EV-BP1708-0013` | review, release | not audited |
| `IT-BP1708-0008` Explicit operator confirmation for review mutations | process_rule | accepted | critical | `EV-BP1708-0014` | operator_approval, review_transaction | not audited |
| `IT-BP1708-0009` Separate module completion from Blueprint acceptance | architecture_constraint | accepted | critical | `EV-BP1708-0015` | roadmap, prompt_lifecycle | not audited |
| `IT-BP1708-0010` Acceptance requires an explicit transaction and seal | process_rule | accepted | critical | `EV-BP1708-0016`, `EV-BP1708-0017`, `EV-BP1708-0018` | review, publication | not audited |
| `IT-BP1708-0011` Use tmp as ephemeral report workspace | process_rule | agreed | normal | `EV-BP1708-0011` | reporting, repository_structure | not audited |
| `IT-BP1708-0012` Finish bounded task before roadmap re-planning | process_rule | agreed | high | `EV-BP1708-0019`, `EV-BP1708-0036` | roadmap, coordination | not audited |
| `IT-BP1708-0013` Hierarchical roadmap tasks and subtasks | requirement | agreed | high | `EV-BP1708-0020` | roadmap, reporting | not audited |
| `IT-BP1708-0014` Roadmap compact and detailed views | ux_requirement | agreed | normal | `EV-BP1708-0021` | roadmap_ui | not audited |
| `IT-BP1708-0015` Current architecture may supersede legacy workflow | process_rule | agreed | critical | `EV-BP1708-0022`, `EV-BP1708-0023` | governance, tooling | not audited |
| `IT-BP1708-0016` Optimize for predictability, stability and transparency | nonfunctional_requirement | agreed | critical | `EV-BP1708-0023` | ecosystem, coordination | not audited |
| `IT-BP1708-0017` Website remains paused | deferred_item | agreed | high | `EV-BP1708-0024` | website | not audited |
| `IT-BP1708-0018` Logistics is the sole pilot for the new model | process_rule | agreed | critical | `EV-BP1708-0025` | logistics_service, portfolio | not audited |
| `IT-BP1708-0019` Propagate stable Logistics model to other modules | plan | agreed | critical | `EV-BP1708-0026` | portfolio, module_assistants | not audited |
| `IT-BP1708-0020` Owner business intent is translated into technical machine prompts | process_rule | agreed | high | `EV-BP1708-0027`, `EV-BP1708-0028` | prompt_design, module_assistants | not audited |
| `IT-BP1708-0021` Prefer reusable machine-like specifications | process_rule | agreed | high | `EV-BP1708-0028` | prompt_design, architecture | not audited |
| `IT-BP1708-0022` Legacy tests/tools should not block current platform | process_rule | agreed | high | `EV-BP1708-0029` | legacy, testing | not audited |
| `IT-BP1708-0023` Archive legacy tooling for optional access | plan | agreed | normal | `EV-BP1708-0030` | legacy, repository_structure | not audited |
| `IT-BP1708-0024` STEP27 acceptance was sealed and published | implementation_claim | accepted | high | `EV-BP1708-0017`, `EV-BP1708-0018` | step27, logistics_service | not audited |
| `IT-BP1708-0025` B1 became active after H9 closure | implementation_claim | accepted | high | `EV-BP1708-0031` | v0_4_1, B1 | not audited |
| `IT-BP1708-0026` B1 exact integration review reached bounded-mutation-ready | implementation_claim | accepted | normal | `EV-BP1708-0032` | v0_4_1, B1 | not audited |
| `IT-BP1708-0027` Shared filter/browser styling should be centrally reusable | ux_requirement | agreed | normal | `EV-BP1708-0033` | ui, design_system | not audited |
| `IT-BP1708-0028` Tree hierarchy needs visible indentation | ux_requirement | agreed | normal | `EV-BP1708-0034` | ui, browser | not audited |
| `IT-BP1708-0029` Breadcrumbs align to main-content origin | ux_requirement | agreed | low | `EV-BP1708-0035` | ui, browser | not audited |
| `IT-BP1708-0030` Zero-context bootstrap must survive session loss | process_rule | agreed | critical | `EV-BP1708-0037`, `EV-BP1708-0038` | bootstrap, continuity | not audited |
| `IT-BP1708-0031` Bootstrap carries the full remaining release path | requirement | agreed | critical | `EV-BP1708-0038` | bootstrap, roadmap | not audited |
| `IT-BP1708-0032` End-to-end Logistics/Codex automatic chain is a release objective | requirement | agreed | critical | `EV-BP1708-0039` | logistics_service, codex, coordination_runtime | not audited |
| `IT-BP1708-0033` Zero-context continuity package was published current | implementation_claim | accepted | high | `EV-BP1708-0040`, `EV-BP1708-0041`, `EV-BP1708-0042` | bootstrap, continuity, B1 | not audited |
| `IT-BP1708-0034` Resume bounded B1-P2 F01–F04 after continuity publication | plan | accepted | high | `EV-BP1708-0043` | B1, v0_4_1 | not audited |
| `IT-BP1708-0035` Global promotion remains a separate decision | process_rule | accepted | critical | `EV-BP1708-0006` | release, governance | not audited |
| `IT-BP1708-0036` Read-only diagnostics before mutation | process_rule | accepted | high | `EV-BP1708-0002`, `EV-BP1708-0043` | diagnostics, governance | not audited |
