# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Current audit |
|---|---|---|---|---|---|---|
| `IT-CALC0910-0001` Calculator is a data-driven pricing/calculation engine, not a hard-coded price list | architecture_constraint | accepted | critical | EV-CALC0910-0002, EV-CALC0910-0004 | Calculator history | not audited |
| `IT-CALC0910-0002` Pricing supports audience-specific B2B/B2C presentation and modifiers | requirement | accepted | high | EV-CALC0910-0003 | Calculator history | not audited |
| `IT-CALC0910-0003` Bulk pricing policies must support filtered group changes | requirement | accepted | critical | EV-CALC0910-0004 | Calculator history | not audited |
| `IT-CALC0910-0004` Calculator pricing capability must be reusable by Telegram and future Website/mobile clients | integration | accepted | critical | EV-CALC0910-0002, EV-CALC0910-0005, EV-CALC0910-0034 | Calculator history | not audited |
| `IT-CALC0910-0005` Calculator implementation should move in bounded incremental steps | process_rule | accepted | high | EV-CALC0910-0006 | Calculator history | not audited |
| `IT-CALC0910-0006` Calculator code must remain understandable years later | nonfunctional_requirement | accepted | high | EV-CALC0910-0008 | Calculator history | not audited |
| `IT-CALC0910-0007` Initial domain rollout uses a few representative products before scaling | architecture_constraint | accepted | critical | EV-CALC0910-0012 | Calculator history | not audited |
| `IT-CALC0910-0008` Product/catalog relationships must scale without manual per-product enumeration | data_contract | accepted | critical | EV-CALC0910-0015, EV-CALC0910-0019, EV-CALC0910-0020 | Calculator history | not audited |
| `IT-CALC0910-0009` Material/product labels must be user-friendly | requirement | accepted | high | EV-CALC0910-0014 | Calculator history | not audited |
| `IT-CALC0910-0010` Material eligibility supports class plus grammage/range constraints | data_contract | accepted | high | EV-CALC0910-0019, EV-CALC0910-0020 | Calculator history | not audited |
| `IT-CALC0910-0011` Calculator needs a serious scalable admin/data-management surface | requirement | accepted | critical | EV-CALC0910-0016, EV-CALC0910-0017 | Calculator history | not audited |
| `IT-CALC0910-0012` Historical idea of one admin controlling the whole project conflicts with later module boundaries | risk | superseded | critical | EV-CALC0910-0016 | Calculator history | not audited |
| `IT-CALC0910-0013` Database schema evolution is migration-controlled | architecture_constraint | accepted | high | EV-CALC0910-0011 | Calculator history | not audited |
| `IT-CALC0910-0014` Historical Calculator had request-id logging and Alembic infrastructure | implementation_claim | accepted | normal | EV-CALC0910-0010 | Calculator history | not audited |
| `IT-CALC0910-0015` Django admin models historically project existing tables while Alembic owns schema | architecture_constraint | accepted | high | EV-CALC0910-0018 | Calculator history | not audited |
| `IT-CALC0910-0016` Backup/restore tooling must be explicit about scope and outcomes | requirement | accepted | high | EV-CALC0910-0021 | Calculator history | not audited |
| `IT-CALC0910-0017` Repository structure should be modular with informative boundaries | architecture_constraint | accepted | high | EV-CALC0910-0022 | Calculator history | not audited |
| `IT-CALC0910-0018` All filesystem paths must be centralized and composable | architecture_constraint | accepted | critical | EV-CALC0910-0023, EV-CALC0910-0024 | Calculator history | not audited |
| `IT-CALC0910-0019` Calculator path/storage configuration must remain portable | nonfunctional_requirement | accepted | high | EV-CALC0910-0025 | Calculator history | not audited |
| `IT-CALC0910-0020` Legacy repository state may be quarantined during structural cleanup | process_rule | accepted | normal | EV-CALC0910-0026 | Calculator history | not audited |
| `IT-CALC0910-0021` A historical refactor checkpoint had clean Django check and 12 passing support tests | implementation_claim | accepted | normal | EV-CALC0910-0028 | Calculator history | not audited |
| `IT-CALC0910-0022` External quote intake must fail safely on malformed channel data | architecture_constraint | accepted | critical | EV-CALC0910-0029, EV-CALC0910-0035 | Calculator history | not audited |
| `IT-CALC0910-0023` Operational intake conflicts require visible alerting plus detailed logs | nonfunctional_requirement | accepted | high | EV-CALC0910-0030 | Calculator history | not audited |
| `IT-CALC0910-0024` Quote intake uses explicit idempotency semantics | architecture_constraint | accepted | critical | EV-CALC0910-0032 | Calculator history | not audited |
| `IT-CALC0910-0025` Historical quote API returned structured human/external reports and line-item calculation output | implementation_claim | accepted | high | EV-CALC0910-0033 | Calculator history | not audited |
| `IT-CALC0910-0026` API errors carry stable code and request correlation | architecture_constraint | accepted | high | EV-CALC0910-0035 | Calculator history | not audited |
| `IT-CALC0910-0027` Calculator backend contracts must remain usable by mobile clients | requirement | accepted | high | EV-CALC0910-0034 | Calculator history | not audited |
| `IT-CALC0910-0028` Historical idempotency tests exposed state-isolation risk | risk | accepted | high | EV-CALC0910-0031 | Calculator history | not audited |
| `IT-CALC0910-0029` Calculator work packages should reconcile with Blueprint before the next large front | process_rule | accepted | critical | EV-CALC0910-0036, EV-CALC0910-0037 | Calculator history | not audited |
| `IT-CALC0910-0030` Calculator↔Blueprint coordination should be Git-visible and can be intentionally paused | process_rule | accepted | high | EV-CALC0910-0038, EV-CALC0910-0039 | Calculator history | not audited |
| `IT-CALC0910-0031` Historical terminal Calculator checkpoint is commit eba5384 with local and origin main aligned | implementation_claim | accepted | high | EV-CALC0910-0040 | Calculator history | not audited |
| `IT-CALC0910-0032` Historical terminal state is a controlled pause after Blueprint directive intake | implementation_claim | accepted | high | EV-CALC0910-0041 | Calculator history | not audited |
| `IT-CALC0910-0033` Blueprint directive sync originally failed silently on schema mismatch | risk | accepted | critical | EV-CALC0910-0042 | Calculator history | not audited |
| `IT-CALC0910-0034` Directive sync tooling must parse canonical module_directives.active and preserve compatibility deliberately | architecture_constraint | accepted | critical | EV-CALC0910-0042, EV-CALC0910-0044 | Calculator history | not audited |
| `IT-CALC0910-0035` Coordination/check tooling should be independent of current working directory | nonfunctional_requirement | accepted | high | EV-CALC0910-0043 | Calculator history | not audited |
| `IT-CALC0910-0036` Blueprint should centrally validate directive-index schema | process_rule | proposed | high | EV-CALC0910-0045 | Calculator history | not audited |
| `IT-CALC0910-0037` Early local Calculator catalog/admin is not current canonical reference authority | risk | superseded | critical | EV-CALC0910-0013, EV-CALC0910-0016 | Calculator history | not audited |
| `IT-CALC0910-0038` Direct Website/Telegram integration assumptions must be reconciled with later Gateway/Contract Registry architecture | risk | unclear | critical | EV-CALC0910-0005, EV-CALC0910-0029 | Calculator history | not audited |
| `IT-CALC0910-0039` Filename date is inconsistent with export and embedded chronology | risk | accepted | critical | EV-CALC0910-0040, EV-CALC0910-0042 | Calculator history | not audited |
| `IT-CALC0910-0040` This Calculator source is module history and cannot supersede current Blueprint/Library/Gateway authority | architecture_constraint | accepted | critical | EV-CALC0910-0037, EV-CALC0910-0041 | Calculator history | not audited |
