# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Authority | Audit |
|---|---|---|---|---|---|---|
| `IT-PRE2005-0001` ForPrint Prepress Hub starts as a separate module in an existing server directory | plan | accepted | high | EV-PRE2005-0001, EV-PRE2005-0002 | Prepress history | not audited |
| `IT-PRE2005-0002` Prior Prepress prompt/agreements attachment is missing from visible source | risk | accepted | critical | EV-PRE2005-0003 | Prepress history | not audited |
| `IT-PRE2005-0003` Historical Prepress Hub is summarized as a local control center rather than per-app plugin architecture | architecture_constraint | proposed | high | EV-PRE2005-0004 | Prepress history | not audited |
| `IT-PRE2005-0004` Historical scaffold separates web UI backend executors presets and logs | architecture_constraint | proposed | high | EV-PRE2005-0005 | Prepress history | not audited |
| `IT-PRE2005-0005` Zero-platform bootstrap is Python backend plus local web UI preset engine and tests | plan | proposed | high | EV-PRE2005-0006, EV-PRE2005-0007 | Prepress history | not audited |
| `IT-PRE2005-0006` First bootstrap phase excludes direct Photoshop Illustrator and Acrobat automation | process_rule | proposed | high | EV-PRE2005-0007 | Prepress history | not audited |
| `IT-PRE2005-0007` Historical repository scaffold separates API core adapters workers config presets data logs and tests | plan | proposed | normal | EV-PRE2005-0008 | Prepress history | not audited |
| `IT-PRE2005-0008` Bootstrap exposes health and preset-discovery endpoints | plan | proposed | high | EV-PRE2005-0009 | Prepress history | not audited |
| `IT-PRE2005-0009` First preset is structural and non-executing | plan | proposed | high | EV-PRE2005-0010, EV-PRE2005-0015 | Prepress history | not audited |
| `IT-PRE2005-0010` Historical Make `check` is non-mutating lint plus tests | process_rule | proposed | high | EV-PRE2005-0011 | Prepress history | not audited |
| `IT-PRE2005-0011` Proposed local dev server binds to all interfaces | risk | proposed | high | EV-PRE2005-0012 | Prepress history | not audited |
| `IT-PRE2005-0012` Historical settings hard-code an absolute project root | risk | proposed | high | EV-PRE2005-0013 | Prepress history | not audited |
| `IT-PRE2005-0013` Preset loader returns deterministic structured YAML data with source identity | requirement | proposed | normal | EV-PRE2005-0014 | Prepress history | not audited |
| `IT-PRE2005-0014` Preset discovery is separated from execution | architecture_constraint | proposed | high | EV-PRE2005-0015 | Prepress history | not audited |
| `IT-PRE2005-0015` Historical job lifecycle uses incoming processing ready and error directories | workflow | proposed | high | EV-PRE2005-0016 | Prepress history | not audited |
| `IT-PRE2005-0016` Runtime job data and logs are not normal Git content | process_rule | proposed | normal | EV-PRE2005-0017 | Prepress history | not audited |
| `IT-PRE2005-0017` Zero-platform gate is check green plus health OK plus preset discovery | acceptance_criterion | proposed | high | EV-PRE2005-0018 | Prepress history | not audited |
| `IT-PRE2005-0018` Job Runner v1 follows only after bootstrap gate | plan | proposed | normal | EV-PRE2005-0019 | Prepress history | not audited |
| `IT-PRE2005-0019` Prepress processing should preserve the original input | process_rule | proposed | critical | EV-PRE2005-0020, EV-PRE2005-0021 | Prepress history | not audited |
| `IT-PRE2005-0020` Prepress job processing should emit append-style job logs | requirement | proposed | high | EV-PRE2005-0022 | Prepress history | not audited |
| `IT-PRE2005-0021` Historical scaffold is proposal not implementation evidence | risk | accepted | critical | EV-PRE2005-0006, EV-PRE2005-0018 | Prepress history | not audited |
| `IT-PRE2005-0022` This source is early Prepress history and cannot supersede later capability-first/current authority | architecture_constraint | accepted | critical | EV-PRE2005-0004, EV-PRE2005-0019 | Prepress history | not audited |
