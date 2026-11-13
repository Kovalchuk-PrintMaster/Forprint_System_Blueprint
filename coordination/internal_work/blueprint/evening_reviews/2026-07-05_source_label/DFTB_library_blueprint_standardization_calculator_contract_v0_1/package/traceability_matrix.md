# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Audit |
|---|---|---|---|---|---|---|
| `IT-LIB0507-0001` Library remains canonical catalog/semantic authority without runtime business logic | architecture_constraint | accepted | critical | EV-LIB0507-0001, EV-LIB0507-0004 | Library history | not audited |
| `IT-LIB0507-0002` Library modernization proceeds through bounded checkpoints | workflow | accepted | high | EV-LIB0507-0002, EV-LIB0507-0003, EV-LIB0507-0005 | Library history | not audited |
| `IT-LIB0507-0003` Early noncritical skeleton may be cleaned aggressively to meet Blueprint standard | process_rule | agreed | high | EV-LIB0507-0006 | Library history | not audited |
| `IT-LIB0507-0004` Large changes should use reliable file-based editing rather than huge terminal paste blocks | process_rule | agreed | normal | EV-LIB0507-0007 | Library history | not audited |
| `IT-LIB0507-0005` Intermediate Library `make check` is mutating | risk | accepted | critical | EV-LIB0507-0008 | Library history | not audited |
| `IT-LIB0507-0006` Library adopts Blueprint make-first command surface | process_rule | accepted | high | EV-LIB0507-0009 | Library history | not audited |
| `IT-LIB0507-0007` Blueprint pull inside Library governance workflow can mutate a foreign checkout | risk | accepted | high | EV-LIB0507-0010, EV-LIB0507-0026, EV-LIB0507-0027 | Library history | not audited |
| `IT-LIB0507-0008` Repository scanners/loggers must exclude .git and virtual environments | risk | accepted | high | EV-LIB0507-0011 | Library history | not audited |
| `IT-LIB0507-0009` Architecture/reference docs belong under structured docs directories | process_rule | agreed | normal | EV-LIB0507-0012 | Library history | not audited |
| `IT-LIB0507-0010` New high-volume directories use thematic one-level subdirectories | process_rule | accepted | high | EV-LIB0507-0013, EV-LIB0507-0015 | Library history | not audited |
| `IT-LIB0507-0011` Do not mass-migrate legacy layout merely for cosmetic structure | process_rule | accepted | normal | EV-LIB0507-0014 | Library history | not audited |
| `IT-LIB0507-0012` Unknown reference gaps are escalated instead of invented | process_rule | accepted | critical | EV-LIB0507-0017 | Library history | not audited |
| `IT-LIB0507-0013` Reports should not repeat semantically identical checks | process_rule | agreed | normal | EV-LIB0507-0018 | Library history | not audited |
| `IT-LIB0507-0014` Library work can proceed from local validation to Blueprint verification | workflow | accepted | high | EV-LIB0507-0019 | Library history | not audited |
| `IT-LIB0507-0015` Calculator Input Contract is consumed as a bounded Library work package | integration | accepted | critical | EV-LIB0507-0020, EV-LIB0507-0032 | Library history | not audited |
| `IT-LIB0507-0016` Commit is delayed until the module gate is green | process_rule | accepted | high | EV-LIB0507-0021, EV-LIB0507-0022, EV-LIB0507-0023 | Library history | not audited |
| `IT-LIB0507-0017` Library commits only Library-owned files | process_rule | accepted | critical | EV-LIB0507-0024, EV-LIB0507-0027 | Library history | not audited |
| `IT-LIB0507-0018` Blueprint is governance/reference input, not Library's write target | architecture_constraint | accepted | critical | EV-LIB0507-0025, EV-LIB0507-0026, EV-LIB0507-0027 | Library history | not audited |
| `IT-LIB0507-0019` Canonical Library Git remote is its own repository | decision | accepted | high | EV-LIB0507-0028, EV-LIB0507-0029 | Library history | not audited |
| `IT-LIB0507-0020` Historical governance-fix commit was pushed cleanly | implementation_claim | accepted | normal | EV-LIB0507-0029, EV-LIB0507-0030 | Library history | not audited |
| `IT-LIB0507-0021` Completion packet separates implementation completion and governance-fix identities | workflow | accepted | critical | EV-LIB0507-0032 | Library history | not audited |
| `IT-LIB0507-0022` Completion packet validation/apply uses explicit packet identity | requirement | accepted | critical | EV-LIB0507-0033 | Library history | not audited |
| `IT-LIB0507-0023` Historical final Library validation is fully green | implementation_claim | accepted | normal | EV-LIB0507-0022, EV-LIB0507-0023, EV-LIB0507-0034 | Library history | not audited |
| `IT-LIB0507-0024` Completion packet apply must be idempotent | process_rule | accepted | critical | EV-LIB0507-0035 | Library history | not audited |
| `IT-LIB0507-0025` Governance fixes must not silently change domain implementation scope | process_rule | accepted | critical | EV-LIB0507-0036 | Library history | not audited |
| `IT-LIB0507-0026` READY_FOR_BLUEPRINT_REVIEW is not acceptance or merge | process_rule | accepted | critical | EV-LIB0507-0031, EV-LIB0507-0037 | Library history | not audited |
| `IT-LIB0507-0027` Do not overclaim focused test evidence not present in the log | process_rule | accepted | high | EV-LIB0507-0038 | Library history | not audited |
| `IT-LIB0507-0028` Blueprint working rules attachment is not recoverable from this export | risk | accepted | high | EV-LIB0507-0016 | Library history | not audited |
| `IT-LIB0507-0029` Most mid-dialogue implementation history is attachment-only | risk | accepted | high | EV-LIB0507-0019, EV-LIB0507-0020 | Library history | not audited |
| `IT-LIB0507-0030` This Library dialogue is module evidence and cannot supersede Blueprint authority | architecture_constraint | accepted | critical | EV-LIB0507-0019, EV-LIB0507-0031 | Library history | not audited |
