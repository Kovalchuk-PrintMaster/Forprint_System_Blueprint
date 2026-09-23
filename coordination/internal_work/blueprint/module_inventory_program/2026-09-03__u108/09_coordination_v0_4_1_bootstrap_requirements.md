# Coordination / Prompt-Report v0.4.1 Bootstrap Requirements

Before normal autonomous work, every module should support a common Blueprint coordination loop covering:
- prompt/request identity;
- source/target module;
- status;
- correlation/root request identity where applicable;
- intake location;
- working state;
- completion/report location;
- evidence/artifact references;
- blockers/questions;
- validation;
- final disposition;
- durable history.

Prompt receipt never equals execution authority.

A likely first future bounded implementation prompt for many modules:
1. adopt current v0.4.1 prompt-intake/reporting surfaces;
2. add deterministic validation;
3. add module-local inventory/index maintenance tooling;
4. create/update AGENTS.md;
5. demonstrate read-only inventory refresh;
6. return a completion packet through the same reporting loop.

This remains PLANNED until Blueprint opens implementation.
