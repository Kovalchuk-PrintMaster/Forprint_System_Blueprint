# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Audit |
|---|---|---|---|---|---|---|
| `IT-LIB1605-0001` Library foundation must remain extensible | architecture_constraint | agreed | critical | EV-LIB1605-0001, EV-LIB1605-0002 | Library history | not audited |
| `IT-LIB1605-0002` Library is the canonical normative-definition layer | requirement | accepted | critical | EV-LIB1605-0003, EV-LIB1605-0022, EV-LIB1605-0025 | Library history | not audited |
| `IT-LIB1605-0003` Contracts/forms support explicit lifecycle and compatibility | requirement | agreed | critical | EV-LIB1605-0004, EV-LIB1605-0028 | Library history | not audited |
| `IT-LIB1605-0004` Library owns canonical reference catalogs and capability definitions | requirement | accepted | critical | EV-LIB1605-0005, EV-LIB1605-0025 | Library history | not audited |
| `IT-LIB1605-0005` Partner integrations consume approved versioned contracts | integration | agreed | high | EV-LIB1605-0006 | Library history | not audited |
| `IT-LIB1605-0006` Build the versioning/validation foundation before catalog completeness | process_rule | accepted | critical | EV-LIB1605-0007, EV-LIB1605-0016 | Library history | not audited |
| `IT-LIB1605-0007` Cross-module data consistency is strongly tested | nonfunctional_requirement | agreed | critical | EV-LIB1605-0009 | Library history | not audited |
| `IT-LIB1605-0008` Library requires human-friendly governed administration | requirement | agreed | high | EV-LIB1605-0010, EV-LIB1605-0014 | Library history | not audited |
| `IT-LIB1605-0009` Orchestrator Registry and operational modules are separate layers | architecture_constraint | accepted | critical | EV-LIB1605-0011, EV-LIB1605-0012 | Library history | not audited |
| `IT-LIB1605-0010` Initial broad Library vision risks becoming storage for everything | risk | superseded | high | EV-LIB1605-0008, EV-LIB1605-0013, EV-LIB1605-0023 | Library history | not audited |
| `IT-LIB1605-0011` Historical Library bootstrap exposes a healthy service endpoint | implementation_claim | accepted | normal | EV-LIB1605-0015 | Library history | not audited |
| `IT-LIB1605-0012` Historical Stage 2 foundation reports seven passing tests | implementation_claim | accepted | normal | EV-LIB1605-0017, EV-LIB1605-0019 | Library history | not audited |
| `IT-LIB1605-0013` Commit and push each complete working intermediate state | process_rule | agreed | high | EV-LIB1605-0018 | Library history | not audited |
| `IT-LIB1605-0014` Keep generated/cache/local-backup artifacts out of canonical Git history | process_rule | agreed | normal | EV-LIB1605-0020 | Library history | not audited |
| `IT-LIB1605-0015` Blueprint alignment narrows Library to canonical definitions not runtime state | architecture_constraint | accepted | critical | EV-LIB1605-0021, EV-LIB1605-0022, EV-LIB1605-0023, EV-LIB1605-0030 | Library history | not audited |
| `IT-LIB1605-0016` Canonical definitions and runtime instances have different owners | process_rule | accepted | critical | EV-LIB1605-0026 | Library history | not audited |
| `IT-LIB1605-0017` Semantic IDs are stable and never reused for new meanings | architecture_constraint | accepted | critical | EV-LIB1605-0027 | Library history | not audited |
| `IT-LIB1605-0018` Library changes need impact-aware activation lifecycle | requirement | accepted | critical | EV-LIB1605-0028 | Library history | not audited |
| `IT-LIB1605-0019` Change Manifest can feed a separate Sync Manager | plan | discussed | high | EV-LIB1605-0025, EV-LIB1605-0029 | Library history | not audited |
| `IT-LIB1605-0020` Library does not execute Calculator Prepress Warehouse or CRM business logic | architecture_constraint | accepted | critical | EV-LIB1605-0025, EV-LIB1605-0026, EV-LIB1605-0030 | Library history | not audited |
| `IT-LIB1605-0021` Uncontrolled client channels should not directly own or bypass Library contracts | architecture_constraint | discussed | high | EV-LIB1605-0024, EV-LIB1605-0030 | Library history | not audited |
| `IT-LIB1605-0022` Library final historical role is strict deeply-versioned and non-operational | decision | accepted | critical | EV-LIB1605-0030 | Library history | not audited |
| `IT-LIB1605-0023` Canonical contract ownership may overlap later Contract Registry architecture | risk | unclear | critical | EV-LIB1605-0025, EV-LIB1605-0030 | Library history | not audited |
| `IT-LIB1605-0024` Admin UI priority must not expand Library into operational control plane | risk | accepted | high | EV-LIB1605-0010, EV-LIB1605-0023 | Library history | not audited |
| `IT-LIB1605-0025` Project Inspector can validate implementations against Library definitions | integration | discussed | high | EV-LIB1605-0025 | Library history | not audited |
| `IT-LIB1605-0026` Change impact includes contract semantic catalog technical-card and migration changes | requirement | accepted | high | EV-LIB1605-0028 | Library history | not audited |
