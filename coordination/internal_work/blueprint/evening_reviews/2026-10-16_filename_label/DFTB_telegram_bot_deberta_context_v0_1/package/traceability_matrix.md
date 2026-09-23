# Traceability Matrix

| Item | Kind | Status | Evidence strength | Evidence |
|---|---|---|---|---|
| `IT-TG1610-0001` Owner opens the DeBERTa topic without specifying a project decision | open_question | discussed | owner-thin | EV-TG1610-0001 |
| `IT-TG1610-0002` Assistant presents DeBERTa as relevant NLP background | assumption | discussed | assistant-context | EV-TG1610-0002, EV-TG1610-0003 |
| `IT-TG1610-0003` `microsoft/deberta-v3-base` is an illustrative assistant example, not a selected project model | external_dependency | proposed | assistant-context | EV-TG1610-0004 |
| `IT-TG1610-0004` Three-label classifier sample is educational rather than a Telegram schema contract | assumption | discussed | assistant-context | EV-TG1610-0005 |
| `IT-TG1610-0005` Assistant suggests style/sentiment classification as a possible Telegram application | plan | proposed | assistant-context | EV-TG1610-0006 |
| `IT-TG1610-0006` Educational model explanation can be mistaken for implementation evidence | risk | accepted | assistant-context | EV-TG1610-0001, EV-TG1610-0004, EV-TG1610-0007 |
| `IT-TG1610-0007` Current Telegram ML authority must come from live repo/current Blueprint, not this micro-dialogue | architecture_constraint | accepted | assistant-context | EV-TG1610-0001, EV-TG1610-0006 |
