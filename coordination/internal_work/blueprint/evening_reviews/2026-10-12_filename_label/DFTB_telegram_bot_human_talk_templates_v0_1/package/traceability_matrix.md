# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Current audit |
|---|---|---|---|---|---|---|
| `IT-TG1210-0001` Telegram human-talk layer uses classified response templates | requirement | accepted | critical | EV-TG1210-0001, EV-TG1210-0004 | Telegram history | not audited |
| `IT-TG1210-0002` Historical training plan references Mistral-7B-Instruct | external_dependency | accepted | normal | EV-TG1210-0001 | Telegram history | not audited |
| `IT-TG1210-0003` Human-talk schema evolves from textual style/sentiment to normalized foreign keys | data_contract | accepted | critical | EV-TG1210-0002, EV-TG1210-0005 | Telegram history | not audited |
| `IT-TG1210-0004` Telegram intent taxonomy contains ten supplied intents | data_contract | accepted | high | EV-TG1210-0006 | Telegram history | not audited |
| `IT-TG1210-0005` Allowed styles are warm formal casual neutral | data_contract | accepted | critical | EV-TG1210-0007 | Telegram history | not audited |
| `IT-TG1210-0006` Allowed sentiments are positive neutral negative | data_contract | accepted | critical | EV-TG1210-0008 | Telegram history | not audited |
| `IT-TG1210-0007` Templates support uk ru en | requirement | accepted | high | EV-TG1210-0009 | Telegram history | not audited |
| `IT-TG1210-0008` Template priority is bounded 0–10 | requirement | accepted | normal | EV-TG1210-0010 | Telegram history | not audited |
| `IT-TG1210-0009` Template text must be short natural style-consistent and non-repetitive | nonfunctional_requirement | accepted | high | EV-TG1210-0004 | Telegram history | not audited |
| `IT-TG1210-0010` Initial dataset should cover at least 100 balanced examples | requirement | accepted | high | EV-TG1210-0003 | Telegram history | not audited |
| `IT-TG1210-0011` Assistant claims a 360-row full Cartesian baseline dataset | implementation_claim | accepted | normal | EV-TG1210-0012 | Telegram history | not audited |
| `IT-TG1210-0012` Assistant claims an additional 500-row dataset | implementation_claim | accepted | normal | EV-TG1210-0015 | Telegram history | not audited |
| `IT-TG1210-0013` Assistant claims an additional 1000-row dataset | implementation_claim | accepted | normal | EV-TG1210-0019 | Telegram history | not audited |
| `IT-TG1210-0014` Generated-dataset uniqueness and balance are not independently verifiable | risk | accepted | critical | EV-TG1210-0013, EV-TG1210-0014, EV-TG1210-0015, EV-TG1210-0019 | Telegram history | not audited |
| `IT-TG1210-0015` Assistant introduces unsupported style labels friendly/playful | risk | accepted | critical | EV-TG1210-0016 | Telegram history | not audited |
| `IT-TG1210-0016` Assistant introduces unsupported aggressive/urgent labels | risk | accepted | critical | EV-TG1210-0017 | Telegram history | not audited |
| `IT-TG1210-0017` Historical generated-count narrative is inconsistent | risk | accepted | high | EV-TG1210-0012, EV-TG1210-0015, EV-TG1210-0019, EV-TG1210-0020 | Telegram history | not audited |
| `IT-TG1210-0018` CSV is the historical import/delivery format | requirement | accepted | normal | EV-TG1210-0011 | Telegram history | not audited |
| `IT-TG1210-0019` A historical CSV import failed on incompatible headers | implementation_claim | accepted | critical | EV-TG1210-0021 | Telegram history | not audited |
| `IT-TG1210-0020` A prior template CSV was known to import successfully | implementation_claim | accepted | high | EV-TG1210-0022 | Telegram history | not audited |
| `IT-TG1210-0021` Root cause of historical CSV import failure is unresolved | risk | unclear | critical | EV-TG1210-0021, EV-TG1210-0023 | Telegram history | not audited |
| `IT-TG1210-0022` Import payload should use only columns supported by the target schema | process_rule | proposed | high | EV-TG1210-0024, EV-TG1210-0025 | Telegram history | not audited |
| `IT-TG1210-0023` Large template imports should begin with a small smoke test | process_rule | proposed | high | EV-TG1210-0026 | Telegram history | not audited |
| `IT-TG1210-0024` CSV generation should validate encoding quoting and row shape | process_rule | proposed | high | EV-TG1210-0023, EV-TG1210-0027 | Telegram history | not audited |
| `IT-TG1210-0025` Human-talk templates are presentation/conversation data, not canonical customer/order truth | architecture_constraint | accepted | critical | EV-TG1210-0001, EV-TG1210-0005 | Telegram history | not audited |
| `IT-TG1210-0026` Filename 12.10.26 is not trustworthy chronology | risk | accepted | critical | EV-TG1210-0001 | Telegram history | not audited |
| `IT-TG1210-0027` Turns 5–7 are missing from the export | risk | accepted | high | EV-TG1210-0015 | Telegram history | not audited |
| `IT-TG1210-0028` Current owner of conversational taxonomies/templates is unresolved | open_question | unclear | high | EV-TG1210-0005, EV-TG1210-0006 | Telegram history | not audited |
| `IT-TG1210-0029` Current generative-model/fine-tuning strategy is unresolved | open_question | unclear | normal | EV-TG1210-0001 | Telegram history | not audited |
| `IT-TG1210-0030` This Telegram source is module history and cannot supersede current Blueprint/Gateway/CRM authority | architecture_constraint | accepted | critical | EV-TG1210-0001, EV-TG1210-0021 | Telegram history | not audited |
