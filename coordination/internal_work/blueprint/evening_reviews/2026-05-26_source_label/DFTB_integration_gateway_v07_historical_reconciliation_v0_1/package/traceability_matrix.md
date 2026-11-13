# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Audit |
|---|---|---|---|---|---|---|
| `IT-GW2605-0001` Integration Gateway is a runtime integration boundary, not a business brain | architecture_constraint | accepted | critical | EV-GW2605-0002, EV-GW2605-0003, EV-GW2605-0004 | Gateway history | not audited |
| `IT-GW2605-0002` Gateway must not own domain business truth | architecture_constraint | accepted | critical | EV-GW2605-0005 | Gateway history | not audited |
| `IT-GW2605-0003` Gateway owns transport validation normalization routing correlation idempotency and audit envelopes | requirement | accepted | critical | EV-GW2605-0003, EV-GW2605-0007, EV-GW2605-0008 | Gateway history | not audited |
| `IT-GW2605-0004` Gateway bootstrap starts local and safe | process_rule | accepted | critical | EV-GW2605-0006, EV-GW2605-0009 | Gateway history | not audited |
| `IT-GW2605-0005` Gateway is channel-agnostic | architecture_constraint | accepted | high | EV-GW2605-0010 | Gateway history | not audited |
| `IT-GW2605-0006` Contract-definition authority is external to Gateway | open_question | accepted | critical | EV-GW2605-0011 | Gateway history | not audited |
| `IT-GW2605-0007` Channel semantic vocabulary should come from canonical semantic authority | open_question | accepted | high | EV-GW2605-0012 | Gateway history | not audited |
| `IT-GW2605-0008` Project Inspector integration is planned rather than silently enabled | plan | discussed | normal | EV-GW2605-0013 | Gateway history | not audited |
| `IT-GW2605-0009` Historical Gateway skeleton contains expected bounded services and fixtures | implementation_claim | accepted | normal | EV-GW2605-0014, EV-GW2605-0015, EV-GW2605-0016 | Gateway history | not audited |
| `IT-GW2605-0010` Gateway should consume Blueprint standards as well as prompts | requirement | accepted | critical | EV-GW2605-0017, EV-GW2605-0019 | Gateway history | not audited |
| `IT-GW2605-0011` Historical v0.7 coordination records pass machine checks | implementation_claim | accepted | normal | EV-GW2605-0018 | Gateway history | not audited |
| `IT-GW2605-0012` Gateway standards visibility includes list check and sync surfaces | requirement | accepted | high | EV-GW2605-0019, EV-GW2605-0027 | Gateway history | not audited |
| `IT-GW2605-0013` Gateway readiness stays preview-first across integration capabilities | requirement | accepted | critical | EV-GW2605-0020 | Gateway history | not audited |
| `IT-GW2605-0014` No live delivery 1C posting or final-price authority in v0.7 | architecture_constraint | accepted | critical | EV-GW2605-0021, EV-GW2605-0028 | Gateway history | not audited |
| `IT-GW2605-0015` Historical v0.7 validation reports 59 passing tests | implementation_claim | accepted | normal | EV-GW2605-0022, EV-GW2605-0027 | Gateway history | not audited |
| `IT-GW2605-0016` Coordination regeneration after staging requires final restage | process_rule | accepted | high | EV-GW2605-0023 | Gateway history | not audited |
| `IT-GW2605-0017` Historical v0.7 report commit is pushed to Gateway repository | implementation_claim | accepted | normal | EV-GW2605-0024, EV-GW2605-0025 | Gateway history | not audited |
| `IT-GW2605-0018` Implementation and completion/report commits have separate provenance roles | process_rule | accepted | high | EV-GW2605-0026 | Gateway history | not audited |
| `IT-GW2605-0019` Gateway remains offline contract-only after v0.7 | architecture_constraint | accepted | critical | EV-GW2605-0028 | Gateway history | not audited |
| `IT-GW2605-0020` Gateway completion requires Blueprint acceptance | process_rule | accepted | critical | EV-GW2605-0029 | Gateway history | not audited |
| `IT-GW2605-0021` Next Gateway work is Blueprint-authorized | process_rule | accepted | critical | EV-GW2605-0030 | Gateway history | not audited |
| `IT-GW2605-0022` CRM/business owners retain workflow decisions | architecture_constraint | accepted | critical | EV-GW2605-0004 | Gateway history | not audited |
| `IT-GW2605-0023` Gateway examples bridge CRM Calculator and Accounting through contract-shaped messages | integration | discussed | high | EV-GW2605-0015 | Gateway history | not audited |
| `IT-GW2605-0024` Standards sync may mix visibility with mutation if not carefully bounded | risk | accepted | high | EV-GW2605-0019, EV-GW2605-0023 | Gateway history | not audited |
| `IT-GW2605-0025` Coordination reports appear to require force-add despite reports directory ignore | risk | accepted | normal | EV-GW2605-0024 | Gateway history | not audited |
| `IT-GW2605-0026` This Gateway source is module history not Blueprint authority | architecture_constraint | accepted | critical | EV-GW2605-0001, EV-GW2605-0029 | Gateway history | not audited |
| `IT-GW2605-0027` Filename date does not establish terminal chronology | risk | accepted | high | EV-GW2605-0001, EV-GW2605-0026 | Gateway history | not audited |
| `IT-GW2605-0028` Canonical module-id/no-live guards are first-class governance checks | process_rule | accepted | high | EV-GW2605-0018, EV-GW2605-0021 | Gateway history | not audited |
