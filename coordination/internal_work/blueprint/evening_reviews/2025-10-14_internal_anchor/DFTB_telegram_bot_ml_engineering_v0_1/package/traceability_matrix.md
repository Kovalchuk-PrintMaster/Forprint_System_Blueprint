# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Current audit |
|---|---|---|---|---|---|---|
| `IT-TG1410-0001` Historical style classifier quality was insufficient at accuracy 0.6394 | risk | accepted | high | EV-TG1410-0001 | Telegram history | not audited |
| `IT-TG1410-0002` ML datasets should be audited balanced and split before retraining | process_rule | discussed | high | EV-TG1410-0002 | Telegram history | not audited |
| `IT-TG1410-0003` Evaluation outputs must be human-readable as well as machine-readable | requirement | accepted | normal | EV-TG1410-0003, EV-TG1410-0004 | Telegram history | not audited |
| `IT-TG1410-0004` Style sentiment and intent training pipelines should share one structural standard | architecture_constraint | accepted | critical | EV-TG1410-0019, EV-TG1410-0021, EV-TG1410-0034 | Telegram history | not audited |
| `IT-TG1410-0005` Every important script should be self-describing and runnable from its header | process_rule | accepted | critical | EV-TG1410-0007, EV-TG1410-0027 | Telegram history | not audited |
| `IT-TG1410-0006` Generated artifact names should be stable and predictable | process_rule | accepted | high | EV-TG1410-0008 | Telegram history | not audited |
| `IT-TG1410-0007` Paths and operational constants belong in centralized configuration | architecture_constraint | accepted | critical | EV-TG1410-0009, EV-TG1410-0016, EV-TG1410-0022 | Telegram history | not audited |
| `IT-TG1410-0008` Derived paths should compose from canonical root/path constants | architecture_constraint | accepted | critical | EV-TG1410-0018 | Telegram history | not audited |
| `IT-TG1410-0009` Config refactoring must preserve existing consumers | process_rule | accepted | critical | EV-TG1410-0017 | Telegram history | not audited |
| `IT-TG1410-0010` Repository structure and filenames require owner approval before changes | process_rule | accepted | high | EV-TG1410-0010, EV-TG1410-0025 | Telegram history | not audited |
| `IT-TG1410-0011` Existing label-map files must not be silently overwritten | data_contract | accepted | critical | EV-TG1410-0011 | Telegram history | not audited |
| `IT-TG1410-0012` Scripts should stay bounded and understandable | nonfunctional_requirement | accepted | normal | EV-TG1410-0012 | Telegram history | not audited |
| `IT-TG1410-0013` Text/CSV encoding is UTF-8 with optional BOM copies for Excel | process_rule | accepted | normal | EV-TG1410-0013 | Telegram history | not audited |
| `IT-TG1410-0014` Scripts must expose important progress and created/changed artifact paths | nonfunctional_requirement | accepted | high | EV-TG1410-0014, EV-TG1410-0027 | Telegram history | not audited |
| `IT-TG1410-0015` Sentiment dataset/label map should be audited against successful style training patterns | requirement | accepted | high | EV-TG1410-0020 | Telegram history | not audited |
| `IT-TG1410-0016` Intent model training must preserve downstream label-decoder compatibility | architecture_constraint | accepted | critical | EV-TG1410-0028, EV-TG1410-0030 | Telegram history | not audited |
| `IT-TG1410-0017` Historical classify_intent path resolution was broken | risk | accepted | high | EV-TG1410-0026 | Telegram history | not audited |
| `IT-TG1410-0018` Historical classify_intent runtime still failed after decoder repair | risk | accepted | high | EV-TG1410-0028, EV-TG1410-0029 | Telegram history | not audited |
| `IT-TG1410-0019` Reuse and audit existing scripts before creating new utilities | process_rule | accepted | critical | EV-TG1410-0023, EV-TG1410-0024 | Telegram history | not audited |
| `IT-TG1410-0020` Prefer extending the owning training pipeline over unnecessary one-off scripts | process_rule | accepted | high | EV-TG1410-0031 | Telegram history | not audited |
| `IT-TG1410-0021` ML ingest settings are configuration-driven | architecture_constraint | accepted | high | EV-TG1410-0022 | Telegram history | not audited |
| `IT-TG1410-0022` Model revision management should be explicit and local-first when remote versioning is unreliable | architecture_constraint | accepted | high | EV-TG1410-0032, EV-TG1410-0033 | Telegram history | not audited |
| `IT-TG1410-0023` ML artifact paths must be entity-specific to avoid constant collisions | architecture_constraint | accepted | critical | EV-TG1410-0034, EV-TG1410-0035 | Telegram history | not audited |
| `IT-TG1410-0024` Windows Zone.Identifier sidecars pollute project working trees | risk | accepted | normal | EV-TG1410-0015, EV-TG1410-0036 | Telegram history | not audited |
| `IT-TG1410-0025` Internal evidence anchors this source to October 2025 engineering work | implementation_claim | accepted | critical | EV-TG1410-0004, EV-TG1410-0037 | Telegram history | not audited |
| `IT-TG1410-0026` Historical WSL user-session issue was resolved to a clean user journal | implementation_claim | accepted | normal | EV-TG1410-0037, EV-TG1410-0038 | Telegram history | not audited |
| `IT-TG1410-0027` Historical ML engineering artifacts do not define Telegram business/runtime authority | architecture_constraint | accepted | critical | EV-TG1410-0007, EV-TG1410-0023 | Telegram history | not audited |
| `IT-TG1410-0028` Historical source is attachment-heavy and implementation bodies are not recoverable | risk | accepted | critical | EV-TG1410-0005, EV-TG1410-0024 | Telegram history | not audited |
| `IT-TG1410-0029` Current ML refactors should preserve semantic compatibility across train/classify/evaluate | process_rule | accepted | critical | EV-TG1410-0021, EV-TG1410-0030, EV-TG1410-0035 | Telegram history | not audited |
| `IT-TG1410-0030` Historic script standard is module-history input, not automatically a current Blueprint standard | risk | accepted | high | EV-TG1410-0007, EV-TG1410-0027 | Telegram history | not audited |
| `IT-TG1410-0031` Evaluation/report pipelines should avoid duplicate overlapping utilities | process_rule | accepted | high | EV-TG1410-0024 | Telegram history | not audited |
| `IT-TG1410-0032` This source precedes later Telegram behavior/governance history | architecture_constraint | accepted | high | EV-TG1410-0004, EV-TG1410-0037 | Telegram history | not audited |
