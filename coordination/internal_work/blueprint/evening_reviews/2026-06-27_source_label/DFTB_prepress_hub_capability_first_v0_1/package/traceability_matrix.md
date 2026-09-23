# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Audit |
|---|---|---|---|---|---|---|
| `IT-PRE2706-0001` Prepress discovery is capability-first before architecture integration | process_rule | accepted | critical | EV-PRE2706-0001, EV-PRE2706-0003, EV-PRE2706-0031 | Prepress history | not audited |
| `IT-PRE2706-0002` Prepress assistants are product-specific rather than one abstract Raster Assistant | architecture_constraint | accepted | critical | EV-PRE2706-0002, EV-PRE2706-0004 | Prepress history | not audited |
| `IT-PRE2706-0003` Shared Prepress Tools provide reusable technical facts, not domain decisions | architecture_constraint | accepted | critical | EV-PRE2706-0005, EV-PRE2706-0006 | Prepress history | not audited |
| `IT-PRE2706-0004` Shared tools return a stable inspection report schema | data_contract | accepted | high | EV-PRE2706-0007, EV-PRE2706-0010 | Prepress history | not audited |
| `IT-PRE2706-0005` Specialized assistants initially depend on shared tools, not each other | architecture_constraint | accepted | critical | EV-PRE2706-0008 | Prepress history | not audited |
| `IT-PRE2706-0006` Build a capability map before broad implementation | plan | accepted | high | EV-PRE2706-0009 | Prepress history | not audited |
| `IT-PRE2706-0007` One input may have multiple controlled processing candidates | architecture_constraint | accepted | critical | EV-PRE2706-0011, EV-PRE2706-0016 | Prepress history | not audited |
| `IT-PRE2706-0008` Production-normalized outputs trend toward PDF | process_rule | agreed | high | EV-PRE2706-0012 | Prepress history | not audited |
| `IT-PRE2706-0009` Candidate results are previewable and selectable | requirement | accepted | high | EV-PRE2706-0013, EV-PRE2706-0024 | Prepress history | not audited |
| `IT-PRE2706-0010` Tool choice is policy-driven by file type task and risk | architecture_constraint | accepted | critical | EV-PRE2706-0014, EV-PRE2706-0023 | Prepress history | not audited |
| `IT-PRE2706-0011` Unix-first processing is the default practical policy | architecture_constraint | accepted | critical | EV-PRE2706-0015, EV-PRE2706-0027, EV-PRE2706-0032 | Prepress history | not audited |
| `IT-PRE2706-0012` Raster preflight detects problematic edge strips before bleed | requirement | accepted | high | EV-PRE2706-0017 | Prepress history | not audited |
| `IT-PRE2706-0013` Bleed generation supports multiple explicit strategies | workflow | accepted | high | EV-PRE2706-0018, EV-PRE2706-0019, EV-PRE2706-0020 | Prepress history | not audited |
| `IT-PRE2706-0014` Crop-before-bleed can lose important edge content | risk | accepted | critical | EV-PRE2706-0018 | Prepress history | not audited |
| `IT-PRE2706-0015` Windows Photoshop Station is a bounded executor | architecture_constraint | accepted | critical | EV-PRE2706-0022, EV-PRE2706-0036 | Prepress history | not audited |
| `IT-PRE2706-0016` Unix quick-check layer handles technical inspection and candidate preparation | architecture_constraint | accepted | critical | EV-PRE2706-0021 | Prepress history | not audited |
| `IT-PRE2706-0017` Processing candidates include explicit risk/confidence metadata | requirement | accepted | high | EV-PRE2706-0025 | Prepress history | not audited |
| `IT-PRE2706-0018` Photoshop Assistant v0.1 focuses on raster-to-print-PDF candidates | plan | accepted | high | EV-PRE2706-0026, EV-PRE2706-0037 | Prepress history | not audited |
| `IT-PRE2706-0019` Minimum effective DPI is configurable and can trigger client approval | requirement | agreed | critical | EV-PRE2706-0028 | Prepress history | not audited |
| `IT-PRE2706-0020` Automatic aspect-ratio distortion is bounded by a configurable tolerance | requirement | agreed | critical | EV-PRE2706-0029 | Prepress history | not audited |
| `IT-PRE2706-0021` Effective-DPI quality and aspect-ratio suitability are separate checks | architecture_constraint | accepted | critical | EV-PRE2706-0034 | Prepress history | not audited |
| `IT-PRE2706-0022` Raster preflight returns structured status and client questions | requirement | accepted | critical | EV-PRE2706-0033 | Prepress history | not audited |
| `IT-PRE2706-0023` K-only enhancement on raster text must be heuristic and safety-gated | risk | accepted | critical | EV-PRE2706-0030, EV-PRE2706-0035 | Prepress history | not audited |
| `IT-PRE2706-0024` Every processing action emits preview and report | process_rule | accepted | high | EV-PRE2706-0038 | Prepress history | not audited |
| `IT-PRE2706-0025` Prepress module solves practical file-processing functions while global coordination remains external | architecture_constraint | accepted | critical | EV-PRE2706-0031 | Prepress history | not audited |
| `IT-PRE2706-0026` Initial practical Unix toolchain is raster inspection/fit/bleed/black-text-candidate/PDF/report | plan | discussed | high | EV-PRE2706-0033, EV-PRE2706-0037 | Prepress history | not audited |
| `IT-PRE2706-0027` Tool-result superiority cannot be assumed globally | risk | accepted | high | EV-PRE2706-0011, EV-PRE2706-0014 | Prepress history | not audited |
| `IT-PRE2706-0028` Windows station job exchange should be file/contract based | integration | discussed | high | EV-PRE2706-0022 | Prepress history | not audited |
| `IT-PRE2706-0029` Historical 80–90% Unix estimate is heuristic, not acceptance criterion | risk | unclear | normal | EV-PRE2706-0032 | Prepress history | not audited |
| `IT-PRE2706-0030` This Prepress source is module history, not current Blueprint authority | architecture_constraint | accepted | critical | EV-PRE2706-0001, EV-PRE2706-0031 | Prepress history | not audited |
