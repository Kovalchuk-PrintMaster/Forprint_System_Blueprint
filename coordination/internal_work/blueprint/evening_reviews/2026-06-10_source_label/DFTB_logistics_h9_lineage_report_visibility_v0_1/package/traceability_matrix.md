# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Audit |
|---|---|---|---|---|---|---|
| `IT-LOG1006-0001` Logistics module starts as a controlled greenfield bootstrap | requirement | agreed | critical | EV-LOG1006-0001, EV-LOG1006-0002, EV-LOG1006-0005 | Logistics module | not audited |
| `IT-LOG1006-0002` Bootstrap forbids live provider writes and Blueprint mutation | architecture_constraint | accepted | critical | EV-LOG1006-0003, EV-LOG1006-0008 | Logistics module | not audited |
| `IT-LOG1006-0003` Logistics consumes approved upstream contracts | architecture_constraint | accepted | critical | EV-LOG1006-0004 | Logistics module | not audited |
| `IT-LOG1006-0004` Canonical Logistics repository identity is explicit | decision | accepted | high | EV-LOG1006-0006, EV-LOG1006-0007 | Logistics module | not audited |
| `IT-LOG1006-0005` Initial commit waits for working files and green checks | process_rule | accepted | high | EV-LOG1006-0009 | Logistics module | not audited |
| `IT-LOG1006-0006` Logistics reports to Blueprint for review and next prompt | workflow | agreed | critical | EV-LOG1006-0010 | Logistics module | not audited |
| `IT-LOG1006-0007` Module reports should expose a visual pass/warn/fail table | ux_requirement | agreed | normal | EV-LOG1006-0011 | Logistics module | not audited |
| `IT-LOG1006-0008` Owner corrections override accidental pasted tasks | process_rule | accepted | critical | EV-LOG1006-0012, EV-LOG1006-0018 | Logistics module | not audited |
| `IT-LOG1006-0009` Prompt intake is coordination-only before implementation | process_rule | accepted | critical | EV-LOG1006-0014, EV-LOG1006-0015, EV-LOG1006-0016 | Logistics module | not audited |
| `IT-LOG1006-0010` Tracking-events prompt intake historically passed coordination gates | implementation_claim | accepted | normal | EV-LOG1006-0014, EV-LOG1006-0015, EV-LOG1006-0016, EV-LOG1006-0017 | Logistics module | not audited |
| `IT-LOG1006-0011` H9 reference rollout becomes a bounded Logistics workfront | plan | accepted | high | EV-LOG1006-0019, EV-LOG1006-0020 | Logistics module | not audited |
| `IT-LOG1006-0012` H9 pre-seal gates historically pass | implementation_claim | accepted | high | EV-LOG1006-0021 | Logistics module | not audited |
| `IT-LOG1006-0013` External Blueprint freshness can block live start without invalidating module publication | architecture_constraint | accepted | critical | EV-LOG1006-0022, EV-LOG1006-0023 | Logistics module | not audited |
| `IT-LOG1006-0014` Publication metadata sealing must be non-recursive | process_rule | accepted | high | EV-LOG1006-0024 | Logistics module | not audited |
| `IT-LOG1006-0015` H9 module-side is historically reported closed and published | implementation_claim | accepted | high | EV-LOG1006-0025, EV-LOG1006-0026 | Logistics module | not audited |
| `IT-LOG1006-0016` H9 closure preserves WIP and authority boundaries | process_rule | accepted | critical | EV-LOG1006-0027, EV-LOG1006-0028 | Logistics module | not audited |
| `IT-LOG1006-0017` Do not reopen a sealed Logistics candidate because Blueprint HEAD moved | process_rule | accepted | critical | EV-LOG1006-0029, EV-LOG1006-0030 | Logistics module | not audited |
| `IT-LOG1006-0018` After H9 seal control passes to Blueprint context | workflow | accepted | critical | EV-LOG1006-0031, EV-LOG1006-0032 | Logistics module | not audited |
| `IT-LOG1006-0019` Logistics live start requires current Blueprint freshness | process_rule | accepted | critical | EV-LOG1006-0033 | Logistics module | not audited |
| `IT-LOG1006-0020` Source spans a long module history despite 10.06 filename | risk | accepted | high | EV-LOG1006-0005, EV-LOG1006-0019, EV-LOG1006-0025 | Logistics module | not audited |
| `IT-LOG1006-0021` Foreign Cloud Backup output is not Logistics history | rejected_alternative | rejected | high | EV-LOG1006-0034 | Logistics module | not audited |
| `IT-LOG1006-0022` Logistics dialogue is module evidence, not Blueprint authority | architecture_constraint | accepted | critical | EV-LOG1006-0010, EV-LOG1006-0031 | Logistics module | not audited |
