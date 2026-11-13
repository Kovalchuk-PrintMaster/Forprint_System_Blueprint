# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Audit |
|---|---|---|---|---|---|---|
| `IT-CRM1605-0001` Prepress automation should use one operator surface for multi-app workflows | requirement | agreed | high | EV-CRM1605-0001, EV-CRM1605-0002 | CRM/cross-module history | not audited |
| `IT-CRM1605-0002` Prepress UI and automation engine should be separated | architecture_constraint | discussed | high | EV-CRM1605-0003, EV-CRM1605-0004, EV-CRM1605-0005 | CRM/cross-module history | not audited |
| `IT-CRM1605-0003` Prepress workflows are declarative presets | requirement | discussed | high | EV-CRM1605-0006 | CRM/cross-module history | not audited |
| `IT-CRM1605-0004` Development governance and production operations are separate control planes | architecture_constraint | accepted | critical | EV-CRM1605-0007, EV-CRM1605-0008 | CRM/cross-module history | not audited |
| `IT-CRM1605-0005` ForPrint Project Inspector replaces the early Project Control naming for conformance verification | decision | accepted | critical | EV-CRM1605-0012, EV-CRM1605-0013 | CRM/cross-module history | not audited |
| `IT-CRM1605-0006` Inspector must not own system architecture design | architecture_constraint | accepted | critical | EV-CRM1605-0013, EV-CRM1605-0014 | CRM/cross-module history | not audited |
| `IT-CRM1605-0007` System architecture needs machine-readable and human-readable representations | requirement | accepted | critical | EV-CRM1605-0015 | CRM/cross-module history | not audited |
| `IT-CRM1605-0008` System architecture must be living and impact-aware | architecture_constraint | accepted | critical | EV-CRM1605-0016, EV-CRM1605-0017 | CRM/cross-module history | not audited |
| `IT-CRM1605-0009` ForPrint System Blueprint is the separate architecture/ideological-control layer | architecture_constraint | accepted | critical | EV-CRM1605-0018, EV-CRM1605-0019 | CRM/cross-module history | not audited |
| `IT-CRM1605-0010` Blueprint and Inspector are distinct: plan vs conformance review | architecture_constraint | accepted | critical | EV-CRM1605-0022 | CRM/cross-module history | not audited |
| `IT-CRM1605-0011` Blueprint can generate module guides/prompts from architecture truth | requirement | discussed | high | EV-CRM1605-0021 | CRM/cross-module history | not audited |
| `IT-CRM1605-0012` Canonical data-object ownership and data flows are explicit architecture surfaces | requirement | accepted | critical | EV-CRM1605-0019, EV-CRM1605-0023 | CRM/cross-module history | not audited |
| `IT-CRM1605-0013` Early Blueprint example temporarily assigns client/order ownership to CRM | risk | superseded | critical | EV-CRM1605-0024, EV-CRM1605-0027 | CRM/cross-module history | not audited |
| `IT-CRM1605-0014` CRM is business orchestration and human-facing management layer | architecture_constraint | accepted | critical | EV-CRM1605-0025 | CRM/cross-module history | not audited |
| `IT-CRM1605-0015` CRM must not become universal canonical/physical data owner | architecture_constraint | accepted | critical | EV-CRM1605-0026, EV-CRM1605-0032 | CRM/cross-module history | not audited |
| `IT-CRM1605-0016` Operational Registry owns canonical clients/orders/tasks/operational statuses | architecture_constraint | accepted | critical | EV-CRM1605-0027 | CRM/cross-module history | not audited |
| `IT-CRM1605-0017` Accounting Registry owns invoices/payments/1C accounting truth | architecture_constraint | accepted | critical | EV-CRM1605-0028 | CRM/cross-module history | not audited |
| `IT-CRM1605-0018` Library owns canonical catalogs/templates/naming references | architecture_constraint | accepted | critical | EV-CRM1605-0029 | CRM/cross-module history | not audited |
| `IT-CRM1605-0019` Project Inspector owns architecture-health checking | architecture_constraint | accepted | critical | EV-CRM1605-0030, EV-CRM1605-0033 | CRM/cross-module history | not audited |
| `IT-CRM1605-0020` Integration Gateway owns command routing/execution delivery | architecture_constraint | accepted | critical | EV-CRM1605-0031, EV-CRM1605-0035 | CRM/cross-module history | not audited |
| `IT-CRM1605-0021` CRM-owned state is limited to human/UI coordination and noncanonical projections | requirement | discussed | high | EV-CRM1605-0034 | CRM/cross-module history | not audited |
| `IT-CRM1605-0022` CRM monolith overreach must be actively prevented | risk | accepted | critical | EV-CRM1605-0032, EV-CRM1605-0033 | CRM/cross-module history | not audited |
| `IT-CRM1605-0023` Initial CRM contracts should separate snapshots commands and results | integration | discussed | high | EV-CRM1605-0035 | CRM/cross-module history | not audited |
| `IT-CRM1605-0024` CRM implementation should start as dashboard/reporting/workflow-command interface | plan | discussed | high | EV-CRM1605-0036 | CRM/cross-module history | not audited |
| `IT-CRM1605-0025` Exact CRM/Operational Registry order-creation boundary remains open | open_question | unclear | critical | EV-CRM1605-0037 | CRM/cross-module history | not audited |
| `IT-CRM1605-0026` CRM is a consumer of architecture-health evidence, not a source of architecture truth | process_rule | accepted | critical | EV-CRM1605-0014, EV-CRM1605-0030, EV-CRM1605-0033 | CRM/cross-module history | not audited |
| `IT-CRM1605-0027` Early Project Control Plane naming should not be conflated with later Strategic Control Plane | risk | accepted | high | EV-CRM1605-0009, EV-CRM1605-0012 | CRM/cross-module history | not audited |
| `IT-CRM1605-0028` This CRM source is cross-module history with embedded Blueprint alignment, not current Blueprint authority | architecture_constraint | accepted | critical | EV-CRM1605-0025, EV-CRM1605-0037 | CRM/cross-module history | not audited |
