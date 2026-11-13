# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Audit |
|---|---|---|---|---|---|---|
| `IT-ACC1705-0001` Production operational truth should be separated from 1C accounting truth | architecture_constraint | accepted | critical | EV-ACC1705-0001, EV-ACC1705-0003, EV-ACC1705-0004, EV-ACC1705-0007 | Accounting history | not audited |
| `IT-ACC1705-0002` Material stock should be derived from movement events rather than a manually edited balance | architecture_constraint | discussed | high | EV-ACC1705-0005, EV-ACC1705-0006 | Accounting history | not audited |
| `IT-ACC1705-0003` 1C synchronization should use outbox/queue and an adapter | integration | discussed | critical | EV-ACC1705-0008 | Accounting history | not audited |
| `IT-ACC1705-0004` 1C transfer packages need structured provenance | requirement | discussed | high | EV-ACC1705-0010 | Accounting history | not audited |
| `IT-ACC1705-0005` 1C synchronization supports configurable batch and recovery modes | requirement | discussed | normal | EV-ACC1705-0009 | Accounting history | not audited |
| `IT-ACC1705-0006` Accounting work is reported back to Blueprint before the next prompt | process_rule | accepted | high | EV-ACC1705-0011, EV-ACC1705-0013 | Accounting history | not audited |
| `IT-ACC1705-0007` Accounting Registry tests must contain real assertions rather than empty placeholders | nonfunctional_requirement | agreed | high | EV-ACC1705-0012 | Accounting history | not audited |
| `IT-ACC1705-0008` Historical v0.5 validation reports 117 passing tests | implementation_claim | accepted | normal | EV-ACC1705-0014 | Accounting history | not audited |
| `IT-ACC1705-0009` Local/production 1C artifacts must stay out of Git | process_rule | accepted | high | EV-ACC1705-0015 | Accounting history | not audited |
| `IT-ACC1705-0010` Historical v0.5 implementation commit is 95d4a55 and was pushed cleanly | implementation_claim | accepted | normal | EV-ACC1705-0016 | Accounting history | not audited |
| `IT-ACC1705-0011` Accounting Registry v0.5 handles sanitized/offline 1C intake and parsing | requirement | accepted | critical | EV-ACC1705-0017 | Accounting history | not audited |
| `IT-ACC1705-0012` Unsanitized and production 1C sources are rejected in the sandbox pipeline | architecture_constraint | accepted | critical | EV-ACC1705-0018 | Accounting history | not audited |
| `IT-ACC1705-0013` Sanitized 1C exports support multiple common file formats | requirement | accepted | high | EV-ACC1705-0019 | Accounting history | not audited |
| `IT-ACC1705-0014` 1C discovery/import outputs are staging evidence, not canonical business truth | architecture_constraint | accepted | critical | EV-ACC1705-0020 | Accounting history | not audited |
| `IT-ACC1705-0015` Historical Blueprint status accepts Accounting Registry v0.5 as sandbox_1c_import_export_ready | decision | accepted | high | EV-ACC1705-0021 | Accounting history | not audited |
| `IT-ACC1705-0016` v0.5 acceptance does not authorize live 1C integration | architecture_constraint | accepted | critical | EV-ACC1705-0022 | Accounting history | not audited |
| `IT-ACC1705-0017` v0.5 acceptance forbids production writes | architecture_constraint | accepted | critical | EV-ACC1705-0023 | Accounting history | not audited |
| `IT-ACC1705-0018` v0.5 acceptance forbids automatic posting | architecture_constraint | accepted | critical | EV-ACC1705-0024 | Accounting history | not audited |
| `IT-ACC1705-0019` v0.6 stronger parser profiles are conditional on real sanitized exports | plan | accepted | critical | EV-ACC1705-0025 | Accounting history | not audited |
| `IT-ACC1705-0020` Accounting Registry must not become canonical client order product or material owner | architecture_constraint | accepted | critical | EV-ACC1705-0026 | Accounting history | not audited |
| `IT-ACC1705-0021` Accounting Registry has no live runtime integrations with neighboring modules at v0.5 | architecture_constraint | accepted | critical | EV-ACC1705-0027 | Accounting history | not audited |
| `IT-ACC1705-0022` v0.6 depends on sanitized counterparties nomenclature invoices payments and balances samples | external_dependency | accepted | high | EV-ACC1705-0028 | Accounting history | not audited |
| `IT-ACC1705-0023` Until v0.6 inputs arrive Accounting Registry stays in maintenance mode | process_rule | accepted | critical | EV-ACC1705-0029 | Accounting history | not audited |
| `IT-ACC1705-0024` Sanitized fixtures must exclude real private or banking data | nonfunctional_requirement | accepted | critical | EV-ACC1705-0030 | Accounting history | not audited |
| `IT-ACC1705-0025` Accounting Registry owns accounting/1C boundary, not operational truth | architecture_constraint | accepted | critical | EV-ACC1705-0004, EV-ACC1705-0026, EV-ACC1705-0027 | Accounting history | not audited |
| `IT-ACC1705-0026` This Accounting source is module history, not Blueprint authority | architecture_constraint | accepted | critical | EV-ACC1705-0011, EV-ACC1705-0021 | Accounting history | not audited |
