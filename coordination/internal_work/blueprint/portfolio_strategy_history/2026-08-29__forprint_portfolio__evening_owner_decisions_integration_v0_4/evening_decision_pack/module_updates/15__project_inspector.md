# Project Inspector — evening delta

Deterministic/rule-driven compliance and consistency checker.

Examples:
- module structure;
- required files;
- secret/key exposure;
- standards compliance;
- predictable configuration checks;
- formalized drift checks.

No whole-module "autopause":
specific risky/remediation work can enter `WAITING_FOR_DECISION` / `HOLD` while unrelated checks continue.

Findings escalate to Blueprint / AI review / owner depending severity.

Expanded review should synthesize a top-down checking order from fundamental sources toward dependent modules.
