# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Current audit |
|---|---|---|---|---|---|
| `IT-BP1709-0001` Source opens with u180e / CF-05 already ACTIVE | implementation_claim | accepted | critical | EV-BP1709-0001, EV-BP1709-0002 | not audited |
| `IT-BP1709-0002` Do not re-activate an already ACTIVE lifecycle step | risk | accepted | critical | EV-BP1709-0005, EV-BP1709-0009 | not audited |
| `IT-BP1709-0003` Morning reconciliation defect is a missing standard governance metadata mapping | task | accepted | high | EV-BP1709-0003 | not audited |
| `IT-BP1709-0004` Governance metadata mapping uses the standard five-field vocabulary | data_contract | accepted | high | EV-BP1709-0006 | not audited |
| `IT-BP1709-0005` Generated indexes/projections are refreshed by canonical producers, not hand-edited | process_rule | accepted | critical | EV-BP1709-0007 | not audited |
| `IT-BP1709-0006` Final make check is validation-only and every new failure remains an acceptance blocker | process_rule | accepted | critical | EV-BP1709-0008 | not audited |
| `IT-BP1709-0007` Historical execution advances from CF-05 to CF-06 before the later morning intake | implementation_claim | accepted | high | EV-BP1709-0010 | not audited |
| `IT-BP1709-0008` Context/intake packages are not automatically executable authority | process_rule | accepted | critical | EV-BP1709-0011 | not audited |
| `IT-BP1709-0009` Finish CF-06 before starting the Blueprint internal AI worker stream | plan | accepted | high | EV-BP1709-0012 | not audited |
| `IT-BP1709-0010` CF-07 second-slice runtime conformance safe-fails before canonical mutation | implementation_claim | accepted | high | EV-BP1709-0013, EV-BP1709-0014, EV-BP1709-0015 | not audited |
| `IT-BP1709-0011` Candidate/test construction failures fail closed before lifecycle advancement | process_rule | accepted | critical | EV-BP1709-0015 | not audited |
| `IT-BP1709-0012` Transition-strategy apply can fail after canonical planning mutation | risk | accepted | critical | EV-BP1709-0016, EV-BP1709-0017 | not audited |
| `IT-BP1709-0013` Partial planning applies require state-aware recovery rather than blind rerun | process_rule | accepted | critical | EV-BP1709-0016, EV-BP1709-0017 | not audited |
| `IT-BP1709-0014` Frequently required developer utilities should be provisioned explicitly | process_rule | proposed | normal | EV-BP1709-0018 | not audited |
| `IT-BP1709-0015` Large evening/handoff packages are applied stepwise with identity confirmation | process_rule | accepted | high | EV-BP1709-0019 | not audited |
| `IT-BP1709-0016` Makefile must be an operator-readable command map | ux_requirement | accepted | critical | EV-BP1709-0020, EV-BP1709-0021 | not audited |
| `IT-BP1709-0017` Legacy or alternate-purpose Make targets must be explicitly classified | process_rule | accepted | high | EV-BP1709-0022 | not audited |
| `IT-BP1709-0018` CF-09 ACK gate repair historically reaches 24/24 control-plane tests passing | implementation_claim | accepted | high | EV-BP1709-0023, EV-BP1709-0024 | not audited |
| `IT-BP1709-0019` Dispatcher closure requires a read-only requirement audit before the project boundary gate | process_rule | accepted | high | EV-BP1709-0025 | not audited |
| `IT-BP1709-0020` CF-09 local closure-readiness is historically 9/9 with zero gaps | implementation_claim | accepted | high | EV-BP1709-0026 | not audited |
| `IT-BP1709-0021` CF-09 remains ACTIVE at sequence 62 before project closure gate | implementation_claim | accepted | critical | EV-BP1709-0027, EV-BP1709-0028 | not audited |
| `IT-BP1709-0022` Local Dispatcher readiness does not imply full-project closure acceptance | risk | accepted | critical | EV-BP1709-0026, EV-BP1709-0029 | not audited |
| `IT-BP1709-0023` CF-09 full project gate is blocked by stale generator inventory | implementation_claim | accepted | critical | EV-BP1709-0029, EV-BP1709-0030 | not audited |
| `IT-BP1709-0024` Cross-module validation can expose Blueprint generated-state drift | risk | accepted | high | EV-BP1709-0030 | not audited |
| `IT-BP1709-0025` Failed CF-09 project closure must not start worker/CF-10 or mutate lifecycle | process_rule | accepted | critical | EV-BP1709-0031 | not audited |
| `IT-BP1709-0026` CF-09 failure returns to state-aware closure-gate recovery | plan | accepted | critical | EV-BP1709-0032 | not audited |
| `IT-BP1709-0027` Source ends before CF-09 recovery/closure result | risk | accepted | critical | EV-BP1709-0033 | not audited |
| `IT-BP1709-0028` Human boundary acceptance remains between Dispatcher closure and first internal worker pilot | architecture_constraint | accepted | critical | EV-BP1709-0025 | not audited |
