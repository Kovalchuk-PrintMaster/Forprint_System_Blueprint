# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Current audit |
|---|---|---|---|---|---|---|
| `IT-TG1210B-0001` Telegram behavior must be intentionally modeled rather than left to ad hoc responses | architecture_constraint | accepted | critical | EV-TG1210B-0001 | Telegram history | not audited |
| `IT-TG1210B-0002` Embedded behavior scaffold is internally dated 2025-10-12 | implementation_claim | accepted | high | EV-TG1210B-0002 | Telegram history | not audited |
| `IT-TG1210B-0003` Historical behavior scaffold separates policy/config state and feedback handling | architecture_constraint | discussed | normal | EV-TG1210B-0003, EV-TG1210B-0004 | Telegram history | not audited |
| `IT-TG1210B-0004` Telegram conversation should feel human rather than dry or form-like | requirement | accepted | critical | EV-TG1210B-0005 | Telegram history | not audited |
| `IT-TG1210B-0005` During requirements capture the assistant should not over-analyze before the owner finishes a block | process_rule | accepted | normal | EV-TG1210B-0006 | Telegram history | not audited |
| `IT-TG1210B-0006` Phone number is a key client-identity/contact field in Telegram dialogue | requirement | accepted | high | EV-TG1210B-0007 | Telegram history | not audited |
| `IT-TG1210B-0007` Voice-to-text synchronization requires compact visible summaries | process_rule | accepted | high | EV-TG1210B-0008, EV-TG1210B-0010 | Telegram history | not audited |
| `IT-TG1210B-0008` Voice summary should cover only the latest exact voice dialogue | process_rule | accepted | high | EV-TG1210B-0011 | Telegram history | not audited |
| `IT-TG1210B-0009` Order dialogue must disambiguate packaging/quantity semantics | requirement | accepted | high | EV-TG1210B-0009 | Telegram history | not audited |
| `IT-TG1210B-0010` Ambiguous Telegram decisions require escalation rather than confident guessing | architecture_constraint | accepted | critical | EV-TG1210B-0012 | Telegram history | not audited |
| `IT-TG1210B-0011` Historical escalation path is Mentor first or AI assistant when needed | workflow | accepted | critical | EV-TG1210B-0012 | Telegram history | not audited |
| `IT-TG1210B-0012` Escalation should carry sufficient conversation/order/data context | data_contract | accepted | critical | EV-TG1210B-0013 | Telegram history | not audited |
| `IT-TG1210B-0013` AI escalation context must obey current privacy and least-privilege boundaries | risk | accepted | critical | EV-TG1210B-0013 | Telegram history | not audited |
| `IT-TG1210B-0014` Telegram can act as an operator interface for tool-enabled AI workflows | plan | discussed | high | EV-TG1210B-0014 | Telegram history | not audited |
| `IT-TG1210B-0015` One Telegram assistant role should support routine personal-assistant operations | requirement | accepted | high | EV-TG1210B-0015 | Telegram history | not audited |
| `IT-TG1210B-0016` Deterministic bot procedures and AI reasoning are separate layers | architecture_constraint | accepted | critical | EV-TG1210B-0016, EV-TG1210B-0017 | Telegram history | not audited |
| `IT-TG1210B-0017` Tool-enabled Telegram assistant must not become unrestricted computer/cloud authority | risk | accepted | critical | EV-TG1210B-0014, EV-TG1210B-0015 | Telegram history | not audited |
| `IT-TG1210B-0018` Telegram should eventually trigger routine 1C/accounting operations through approved integration | requirement | accepted | high | EV-TG1210B-0018 | Telegram history | not audited |
| `IT-TG1210B-0019` Direct Telegram ownership of 1C writes is superseded by later Accounting/Gateway boundaries | risk | superseded | critical | EV-TG1210B-0018, EV-TG1210B-0019 | Telegram history | not audited |
| `IT-TG1210B-0020` Repository/file-structure claims must be grounded in accessible project artifacts | process_rule | accepted | high | EV-TG1210B-0020, EV-TG1210B-0021 | Telegram history | not audited |
| `IT-TG1210B-0021` Chat/voice continuity is not a reliable substitute for durable project memory | risk | accepted | critical | EV-TG1210B-0008, EV-TG1210B-0021 | Telegram history | not audited |
| `IT-TG1210B-0022` Historical Telegram stack is DeBERTa classification + Mistral generation + AI escalation | architecture_constraint | accepted | critical | EV-TG1210B-0022 | Telegram history | not audited |
| `IT-TG1210B-0023` Telegram bot-manager needs sales and objection-handling capability | requirement | accepted | high | EV-TG1210B-0023 | Telegram history | not audited |
| `IT-TG1210B-0024` Sales/refusal/objection states must be represented in classification/routing semantics | requirement | accepted | high | EV-TG1210B-0024 | Telegram history | not audited |
| `IT-TG1210B-0025` Training data should be modular by domain rather than one giant table | architecture_constraint | accepted | critical | EV-TG1210B-0025 | Telegram history | not audited |
| `IT-TG1210B-0026` Weak behavior domains should be improved with targeted real examples | workflow | accepted | high | EV-TG1210B-0026 | Telegram history | not audited |
| `IT-TG1210B-0027` Classifier quality should be evaluated automatically on a recurring schedule | requirement | accepted | critical | EV-TG1210B-0027 | Telegram history | not audited |
| `IT-TG1210B-0028` A static recurring test set can become invalid evidence through memorization/leakage | risk | accepted | critical | EV-TG1210B-0028 | Telegram history | not audited |
| `IT-TG1210B-0029` Recurring evaluation should include fresh unseen test cases | requirement | accepted | critical | EV-TG1210B-0029 | Telegram history | not audited |
| `IT-TG1210B-0030` Owner rejects simple fixed rotation as the preferred autonomous evaluation strategy | decision | accepted | high | EV-TG1210B-0030 | Telegram history | not audited |
| `IT-TG1210B-0031` External LLM-generated evaluation cases are a historical candidate, not a verified solution | plan | proposed | normal | EV-TG1210B-0031, EV-TG1210B-0032 | Telegram history | not audited |
| `IT-TG1210B-0032` Generated evaluation data needs independent labels/oracles, not only generator output | risk | proposed | critical | EV-TG1210B-0029, EV-TG1210B-0032 | Telegram history | not audited |
| `IT-TG1210B-0033` This source is Telegram history and cannot supersede later Blueprint/CRM/Accounting/Gateway authority | architecture_constraint | accepted | critical | EV-TG1210B-0018, EV-TG1210B-0022 | Telegram history | not audited |
| `IT-TG1210B-0034` Turn 1 embeds prior dialogue/scaffold and must not be double-counted as new direct owner evidence | risk | accepted | critical | EV-TG1210B-0002, EV-TG1210B-0003 | Telegram history | not audited |
