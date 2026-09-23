# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Audit |
|---|---|---|---|---|---|
| `IT-BP1409-0001` CF-02 active double-write gate hardening historically passes | implementation_claim | accepted | high | EV-BP1409-0001 | not audited |
| `IT-BP1409-0002` Active Control Foundation double-write is removed | implementation_claim | accepted | high | EV-BP1409-0002, EV-BP1409-0003 | not audited |
| `IT-BP1409-0003` Retire legacy continuity terminal-state hints before CF-02 closure | plan | accepted | critical | EV-BP1409-0003, EV-BP1409-0006 | not audited |
| `IT-BP1409-0004` Roadmap/lifecycle reconciliation gate is fail-closed | process_rule | accepted | critical | EV-BP1409-0004 | not audited |
| `IT-BP1409-0005` CF-02 does not gain dispatch/release/auto-next authority | process_rule | accepted | critical | EV-BP1409-0005 | not audited |
| `IT-BP1409-0006` CF-02 closure can fail after canonical lifecycle advanced | implementation_claim | accepted | high | EV-BP1409-0007, EV-BP1409-0008 | not audited |
| `IT-BP1409-0007` State-aware recovery forbids blind rerun after partial advancement | process_rule | accepted | critical | EV-BP1409-0009, EV-BP1409-0010 | not audited |
| `IT-BP1409-0008` Artifact delivery truncation requires identity-safe regeneration | process_rule | agreed | normal | EV-BP1409-0011, EV-BP1409-0012 | not audited |
| `IT-BP1409-0009` Website/UI branch is explicitly out of Blueprint work scope here | rejected_alternative | rejected | high | EV-BP1409-0013, EV-BP1409-0014 | not audited |
| `IT-BP1409-0010` u180e reaches CF-05 with roadmap sync and broad focused checks green | implementation_claim | accepted | high | EV-BP1409-0015, EV-BP1409-0019, EV-BP1409-0020 | not audited |
| `IT-BP1409-0011` One aggregate full-pytest blocker remains despite green focused checks | risk | accepted | high | EV-BP1409-0016, EV-BP1409-0023 | not audited |
| `IT-BP1409-0012` Diagnose exact failing node before rerunning expensive aggregate checks | process_rule | accepted | high | EV-BP1409-0017, EV-BP1409-0018 | not audited |
| `IT-BP1409-0013` Controlled-failure source-hash contract is the reported failing node | implementation_claim | accepted | normal | EV-BP1409-0021, EV-BP1409-0022 | not audited |
| `IT-BP1409-0014` Diagnostic logs can be stale relative to current source/test pins | risk | accepted | critical | EV-BP1409-0027, EV-BP1409-0028 | not audited |
| `IT-BP1409-0015` Separate current-tree truth from isolated public-check materialization | process_rule | accepted | critical | EV-BP1409-0029, EV-BP1409-0030 | not audited |
| `IT-BP1409-0016` If current tree is green and public log stale repair isolation/report freshness, not source | process_rule | accepted | critical | EV-BP1409-0030, EV-BP1409-0031, EV-BP1409-0032 | not audited |
| `IT-BP1409-0017` Historical release projection remains v0.4 sealed / v0.4.1 active | implementation_claim | accepted | normal | EV-BP1409-0024 | not audited |
| `IT-BP1409-0018` Historical planning health shows roadmap 5/8 and prompt buffer 2/3 | implementation_claim | accepted | normal | EV-BP1409-0025 | not audited |
| `IT-BP1409-0019` Semantic structure is green at the u180e diagnostic checkpoint | implementation_claim | accepted | normal | EV-BP1409-0026 | not audited |
| `IT-BP1409-0020` Final 0104 diagnosis result is not preserved | open_question | unclear | critical | EV-BP1409-0030, EV-BP1409-0033 | not audited |
