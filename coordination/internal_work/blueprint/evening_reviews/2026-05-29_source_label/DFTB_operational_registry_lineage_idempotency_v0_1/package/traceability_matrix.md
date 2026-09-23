# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Audit |
|---|---|---|---|---|---|---|
| `IT-OPREG2905-0001` Operational Registry owns operational truth | architecture_constraint | accepted | critical | EV-OPREG2905-0001 | Operational Registry history | not audited |
| `IT-OPREG2905-0002` Operational Registry must not absorb neighboring domain ownership | architecture_constraint | accepted | critical | EV-OPREG2905-0002, EV-OPREG2905-0006 | Operational Registry history | not audited |
| `IT-OPREG2905-0003` Bootstrap validates model/lifecycle/boundaries before production storage | plan | accepted | high | EV-OPREG2905-0003, EV-OPREG2905-0008 | Operational Registry history | not audited |
| `IT-OPREG2905-0004` Initial storage is abstracted behind a simple repository interface | architecture_constraint | accepted | high | EV-OPREG2905-0004 | Operational Registry history | not audited |
| `IT-OPREG2905-0005` Order lifecycle uses explicit allowed transitions | workflow | agreed | high | EV-OPREG2905-0005 | Operational Registry history | not audited |
| `IT-OPREG2905-0006` Accounting/1C truth is distinct from operational truth | architecture_constraint | accepted | critical | EV-OPREG2905-0006, EV-OPREG2905-0009, EV-OPREG2905-0012 | Operational Registry history | not audited |
| `IT-OPREG2905-0007` Boundary tests must fail on domain ownership creep | process_rule | accepted | critical | EV-OPREG2905-0007 | Operational Registry history | not audited |
| `IT-OPREG2905-0008` Operational data foundation distinguishes master data facts events projections and external references | architecture_constraint | accepted | high | EV-OPREG2905-0010, EV-OPREG2905-0011, EV-OPREG2905-0012 | Operational Registry history | not audited |
| `IT-OPREG2905-0009` Operational Registry consumes Blueprint governance/module policy | workflow | accepted | high | EV-OPREG2905-0013, EV-OPREG2905-0014 | Operational Registry history | not audited |
| `IT-OPREG2905-0010` Snapshot and completion automation must be idempotent | process_rule | accepted | critical | EV-OPREG2905-0015 | Operational Registry history | not audited |
| `IT-OPREG2905-0011` Approved prompts come from Blueprint module-specific outgoing_prompts directory | process_rule | accepted | critical | EV-OPREG2905-0016, EV-OPREG2905-0017 | Operational Registry history | not audited |
| `IT-OPREG2905-0012` Make `check` is read-only while lint-fix is separate | process_rule | accepted | critical | EV-OPREG2905-0018 | Operational Registry history | not audited |
| `IT-OPREG2905-0013` Module-start historically performs a Blueprint pull | risk | accepted | high | EV-OPREG2905-0019 | Operational Registry history | not audited |
| `IT-OPREG2905-0014` Generated report cleanup is non-failing and bounded | process_rule | accepted | normal | EV-OPREG2905-0020, EV-OPREG2905-0027 | Operational Registry history | not audited |
| `IT-OPREG2905-0015` Historical make-first alignment gate reports 232 passing tests | implementation_claim | accepted | normal | EV-OPREG2905-0021 | Operational Registry history | not audited |
| `IT-OPREG2905-0016` Alignment checkpoint is separate from main business prompt implementation | process_rule | accepted | high | EV-OPREG2905-0028, EV-OPREG2905-0030, EV-OPREG2905-0032 | Operational Registry history | not audited |
| `IT-OPREG2905-0017` Prompt discovery is narrow and approved-only | process_rule | accepted | critical | EV-OPREG2905-0025 | Operational Registry history | not audited |
| `IT-OPREG2905-0018` Prompt sync validates source before replacing local state | process_rule | accepted | critical | EV-OPREG2905-0026 | Operational Registry history | not audited |
| `IT-OPREG2905-0019` Historical alignment commit `a6ca69f` is pushed to Operational Registry origin/main | implementation_claim | accepted | normal | EV-OPREG2905-0023, EV-OPREG2905-0032 | Operational Registry history | not audited |
| `IT-OPREG2905-0020` Blueprint snapshots and prompts are provenance-bound to an observed Blueprint commit | process_rule | accepted | high | EV-OPREG2905-0029 | Operational Registry history | not audited |
| `IT-OPREG2905-0021` Completion finalization requires explicit packet identity | process_rule | accepted | critical | EV-OPREG2905-0022, EV-OPREG2905-0031 | Operational Registry history | not audited |
| `IT-OPREG2905-0022` Filename 29.05 is only a source/start label | risk | accepted | high | EV-OPREG2905-0010, EV-OPREG2905-0016, EV-OPREG2905-0029 | Operational Registry history | not audited |
| `IT-OPREG2905-0023` Operational Registry source is module history not Blueprint authority | architecture_constraint | accepted | critical | EV-OPREG2905-0014, EV-OPREG2905-0029 | Operational Registry history | not audited |
| `IT-OPREG2905-0024` Operational payment state naming must avoid accounting-authority ambiguity | open_question | discussed | high | EV-OPREG2905-0009 | Operational Registry history | not audited |
| `IT-OPREG2905-0025` CRM coordinates/displays but Operational Registry owns operational records | architecture_constraint | accepted | critical | EV-OPREG2905-0006 | Operational Registry history | not audited |
| `IT-OPREG2905-0026` Library catalogs/contracts remain outside Operational Registry | architecture_constraint | accepted | critical | EV-OPREG2905-0006, EV-OPREG2905-0007 | Operational Registry history | not audited |
| `IT-OPREG2905-0027` Gateway routes runtime commands rather than owning operational truth | architecture_constraint | accepted | high | EV-OPREG2905-0006 | Operational Registry history | not audited |
| `IT-OPREG2905-0028` Make-first startup must succeed before main task execution | process_rule | accepted | critical | EV-OPREG2905-0028 | Operational Registry history | not audited |
| `IT-OPREG2905-0029` Current Blueprint prompt-directory topology may differ from this historical checkpoint | risk | accepted | normal | EV-OPREG2905-0016, EV-OPREG2905-0024 | Operational Registry history | not audited |
| `IT-OPREG2905-0030` Alignment findings are reported back to Blueprint as a separate checkpoint | workflow | accepted | high | EV-OPREG2905-0032 | Operational Registry history | not audited |
