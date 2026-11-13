# Traceability Matrix

| Item | Kind | Status | Importance | Evidence |
|---|---|---|---|---|
| `IT-TG0710-0001` Historical Telegram dialogue ingest starts from exported HTML and emits DB-compatible CSV | workflow | accepted | high | EV-TG0710-0001, EV-TG0710-0003, EV-TG0710-0004 |
| `IT-TG0710-0002` Historical manager-chat import contract contains 20 explicit fields | data_contract | accepted | high | EV-TG0710-0005 |
| `IT-TG0710-0003` Client mapping should resolve against an existing clients table | requirement | accepted | critical | EV-TG0710-0002 |
| `IT-TG0710-0004` Non-text media placeholders are excluded from text training rows | process_rule | accepted | normal | EV-TG0710-0003 |
| `IT-TG0710-0005` Chat extraction pairs client inputs with print-shop responses and can merge short context messages | workflow | accepted | high | EV-TG0710-0004 |
| `IT-TG0710-0006` Early Telegram style taxonomy differs from later normalized style lookup | risk | superseded | critical | EV-TG0710-0006 |
| `IT-TG0710-0007` Early Telegram sentiment taxonomy differs from later normalized sentiment lookup | risk | superseded | critical | EV-TG0710-0007 |
| `IT-TG0710-0008` Fixed confidence response-time and feedback values are synthetic labels not observed facts | risk | accepted | high | EV-TG0710-0008, EV-TG0710-0009 |
| `IT-TG0710-0009` Known-good import samples should define compatibility before synthetic expansion | process_rule | accepted | critical | EV-TG0710-0010, EV-TG0710-0013 |
| `IT-TG0710-0010` Historical synthetic intent expansion includes order_modification | requirement | accepted | high | EV-TG0710-0011, EV-TG0710-0012 |
| `IT-TG0710-0011` Synthetic chat rows contain personal-data fields and require privacy/sanitization controls | risk | accepted | critical | EV-TG0710-0002, EV-TG0710-0005 |
| `IT-TG0710-0012` Heterogeneous business entities should not be flattened into one giant sparse table | architecture_constraint | discussed | high | EV-TG0710-0014, EV-TG0710-0015 |
| `IT-TG0710-0013` Telegram-local supplier/product/service tables would conflict with later canonical ownership if treated as master data | risk | superseded | critical | EV-TG0710-0014, EV-TG0710-0015 |
| `IT-TG0710-0014` Owner explores whether Telegram should mirror selected 1C data for broader operation | open_question | discussed | high | EV-TG0710-0016, EV-TG0710-0017 |
| `IT-TG0710-0015` Historical assistant suggests intermediate DB/API periodic/event synchronization from 1C | plan | proposed | normal | EV-TG0710-0018, EV-TG0710-0020 |
| `IT-TG0710-0016` A Telegram-owned synchronized mirror of 1C would create competing truth if copied literally | risk | superseded | critical | EV-TG0710-0016, EV-TG0710-0018 |
| `IT-TG0710-0017` Current 1C integration should be adapter/contract-driven rather than ad hoc file-copy semantics | architecture_constraint | accepted | critical | EV-TG0710-0020 |
| `IT-TG0710-0018` The historical 1C synchronization approach was not owner-approved for implementation | risk | accepted | high | EV-TG0710-0021 |
| `IT-TG0710-0019` Filename 07.10.26 is not trustworthy chronology | risk | accepted | critical | EV-TG0710-0001 |
| `IT-TG0710-0020` This source is Telegram module history and cannot supersede later Blueprint/Accounting/Gateway/CRM authority | architecture_constraint | accepted | critical | EV-TG0710-0016, EV-TG0710-0021 |
