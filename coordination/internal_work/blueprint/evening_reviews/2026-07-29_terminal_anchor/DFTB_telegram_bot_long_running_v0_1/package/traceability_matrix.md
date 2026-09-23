# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Current audit |
|---|---|---|---|---|---|---|
| `IT-TG1310-0001` Telegram behavior is modeled explicitly before production execution | architecture_constraint | accepted | critical | EV-TG1310-0001, EV-TG1310-0019 | Telegram history | not audited |
| `IT-TG1310-0002` Low-confidence Telegram decisions escalate to Mentor or AI with context and audit trail | workflow | discussed | high | EV-TG1310-0002, EV-TG1310-0003 | Telegram history | not audited |
| `IT-TG1310-0003` Historical Telegram stack includes Supabase DeBERTa and Mistral | external_dependency | accepted | normal | EV-TG1310-0004 | Telegram history | not audited |
| `IT-TG1310-0004` Historical conversation pipeline is intents→templates→generation→feedback | architecture_constraint | discussed | high | EV-TG1310-0005 | Telegram history | not audited |
| `IT-TG1310-0005` Client qualification conversationally enriches missing profile data | requirement | accepted | critical | EV-TG1310-0006 | Telegram history | not audited |
| `IT-TG1310-0006` Telegram client-card enrichment must not become canonical CRM ownership | risk | accepted | critical | EV-TG1310-0006, EV-TG1310-0007 | Telegram history | not audited |
| `IT-TG1310-0007` Telegram delivery behavior must not absorb Logistics provider execution ownership | risk | superseded | critical | EV-TG1310-0006, EV-TG1310-0007 | Telegram history | not audited |
| `IT-TG1310-0008` Behavior registry is grouped by thematic blocks for operator comprehension | requirement | accepted | normal | EV-TG1310-0008 | Telegram history | not audited |
| `IT-TG1310-0009` Operator behavior artifacts are delivered in Excel and HTML by default | process_rule | accepted | normal | EV-TG1310-0009 | Telegram history | not audited |
| `IT-TG1310-0010` Behavior registry carries integrity/KPI/duplicate metadata | requirement | accepted | normal | EV-TG1310-0010, EV-TG1310-0011 | Telegram history | not audited |
| `IT-TG1310-0011` Path/file sprawl should be corrected before adding more Telegram logic | process_rule | accepted | critical | EV-TG1310-0012, EV-TG1310-0013 | Telegram history | not audited |
| `IT-TG1310-0012` Telegram scripts require durable metadata and explanatory structure | nonfunctional_requirement | accepted | high | EV-TG1310-0014, EV-TG1310-0027 | Telegram history | not audited |
| `IT-TG1310-0013` Telegram code/config must avoid hard-coded paths and constants | nonfunctional_requirement | accepted | critical | EV-TG1310-0028 | Telegram history | not audited |
| `IT-TG1310-0014` Historical classifier/template testing exposed inconsistent behavior | risk | accepted | high | EV-TG1310-0015, EV-TG1310-0017 | Telegram history | not audited |
| `IT-TG1310-0015` A historical classifier checkpoint could route a reengagement sample | implementation_claim | accepted | normal | EV-TG1310-0016 | Telegram history | not audited |
| `IT-TG1310-0016` Owner resets priority from classifier engineering back to behavior-model design | decision | accepted | critical | EV-TG1310-0019 | Telegram history | not audited |
| `IT-TG1310-0017` Synthetic phrases are test fixtures for behavior schemes, not architecture drivers | process_rule | accepted | high | EV-TG1310-0020 | Telegram history | not audited |
| `IT-TG1310-0018` Behavior tooling must detect false-success artifact updates | risk | accepted | high | EV-TG1310-0022 | Telegram history | not audited |
| `IT-TG1310-0019` Wizard simulation should be scenario-modular behind a small dispatcher | architecture_constraint | accepted | critical | EV-TG1310-0023 | Telegram history | not audited |
| `IT-TG1310-0020` Historical ORDER wizard loaded a 113-node Excel flow successfully | implementation_claim | accepted | normal | EV-TG1310-0024 | Telegram history | not audited |
| `IT-TG1310-0021` Historical VENDORS wizard path had syntax/interface defects | risk | accepted | high | EV-TG1310-0025, EV-TG1310-0026 | Telegram history | not audited |
| `IT-TG1310-0022` Production bot logic is separated from XLS/wizard development artifacts | architecture_constraint | accepted | critical | EV-TG1310-0029 | Telegram history | not audited |
| `IT-TG1310-0023` Real Telegram runtime historically targets Supabase-backed project services | architecture_constraint | accepted | high | EV-TG1310-0030 | Telegram history | not audited |
| `IT-TG1310-0024` Runtime model code should be organized by bounded scenarios/domains | architecture_constraint | accepted | high | EV-TG1310-0027 | Telegram history | not audited |
| `IT-TG1310-0025` Telegram source should be Git-backed rather than only locally stored | process_rule | accepted | high | EV-TG1310-0031 | Telegram history | not audited |
| `IT-TG1310-0026` Telegram adopts the canonical ForPrint Make target contract | process_rule | accepted | critical | EV-TG1310-0032 | Telegram history | not audited |
| `IT-TG1310-0027` Module reads Blueprint but writes completion/status only in its own repository | process_rule | accepted | critical | EV-TG1310-0033 | Telegram history | not audited |
| `IT-TG1310-0028` Telegram closure workflow had metadata/formatting gaps | risk | accepted | high | EV-TG1310-0034 | Telegram history | not audited |
| `IT-TG1310-0029` Telegram governance-baseline adoption runs on a dedicated feature branch | plan | accepted | high | EV-TG1310-0035 | Telegram history | not audited |
| `IT-TG1310-0030` Historical `NO_COLOR=1` convention is retired | decision | accepted | normal | EV-TG1310-0036 | Telegram history | not audited |
| `IT-TG1310-0031` Telegram governance remediation must stay inside Telegram repository | architecture_constraint | accepted | critical | EV-TG1310-0037 | Telegram history | not audited |
| `IT-TG1310-0032` Unavailable external Blueprint pull is DEFERRED not false green or Telegram failure | process_rule | accepted | critical | EV-TG1310-0038 | Telegram history | not audited |
| `IT-TG1310-0033` Historical governance closeout commit is dcd2b01 on feature branch | implementation_claim | accepted | high | EV-TG1310-0039 | Telegram history | not audited |
| `IT-TG1310-0034` Historical feature branch was pushed cleanly with zero divergence | implementation_claim | accepted | high | EV-TG1310-0040 | Telegram history | not audited |
| `IT-TG1310-0035` Historical completion-packet apply was idempotent | implementation_claim | accepted | high | EV-TG1310-0041 | Telegram history | not audited |
| `IT-TG1310-0036` READY_FOR_BLUEPRINT_REVIEW is not Blueprint acceptance | architecture_constraint | accepted | critical | EV-TG1310-0042 | Telegram history | not audited |
| `IT-TG1310-0037` Governance closeout intentionally made no dialogue/business/runtime changes | implementation_claim | accepted | high | EV-TG1310-0042 | Telegram history | not audited |
| `IT-TG1310-0038` Filename 13.10.26 is not trustworthy chronology | risk | accepted | critical | EV-TG1310-0035, EV-TG1310-0042 | Telegram history | not audited |
