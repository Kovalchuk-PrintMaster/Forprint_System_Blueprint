# Global Directive: Module Coordination Standard v1

## Directive ID

```text
2026-06-02__global__directive__module-coordination-standard-v1
Scope
all_active_modules
Status
active
```
Purpose

All active ForPrint modules must maintain a structured coordination directory.

This is required so ForPrint System Blueprint / future Control Plane can collect the real ecosystem state through Git instead of manually copying reports from module chats.

Required coordination structure

Each active module repository must contain:

coordination/
├── status/
│   ├── current_status.yaml
│   ├── current_status.md
│   └── next_questions_for_blueprint.md
│
├── prompts/
│   ├── received/
│   └── index.yaml
│
├── reports/
│   ├── completion/
│   ├── commits/
│   └── index.yaml
│
└── README.md
Required source prompt

Use the standard prompt from Blueprint:

coordination/templates/module_coordination_prompt.md
Required module behavior

After each meaningful milestone, macro pack, checkpoint, commit or push, each module should update:

coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
coordination/prompts/index.yaml
coordination/reports/index.yaml

If work was triggered by a Blueprint prompt/directive, the completion report must reference the prompt/directive ID.

Safety rule

Coordination files must not contain secrets, private client data, real 1C production data, tokens, passwords or sensitive logs.

Expected acknowledgement

Each module should return:

Module Coordination Standard Applied

with:

files added/changed
current_status summary
prompts/index summary
reports/index summary
check results
commit hash
push status
open questions
Future direction

This global directive is the first step toward ecosystem-wide status aggregation.

Future automation may:

pull all module repositories
read current_status.yaml
read prompts/index.yaml
read reports/index.yaml
generate ecosystem status
detect blocked modules
detect outdated modules
recommend next priority

---
