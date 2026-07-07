# ForPrint Module Outgoing Prompt Pull Protocol

Status: active standard
Created/updated: `2026-06-10T13:52:31.685722+00:00`

## Purpose

This standard defines how a module assistant receives work from ForPrint System Blueprint without manual copy-paste of long prompts.

Blueprint owns the outgoing prompt queue. Modules pull their own active prompts from Blueprint.

This supports the ForPrint push-pull coordination loop:

Blueprint writes outgoing prompt
Module pulls prompt
Module runs governance checks
Module executes work
Module commits and pushes
Blueprint refreshes audit/status
Required module-side script

Every active governance-aligned module that receives Blueprint-driven work should provide:

scripts/read_blueprint_outgoing_prompt.py

The script must:

know its own module id;
read the Blueprint outgoing prompt index;
find prompts with status: ready_for_module_pull;
print the selected prompt file to terminal;
avoid modifying Blueprint files;
fail clearly if the index or prompt file is missing.

Standard Blueprint prompt index path:

/srv/software_development/forprint-project/forprint_system_blueprint/coordination/outgoing_prompts/<module_id>/index.yaml
Required module-side Make targets

Every active module that receives Blueprint-driven work should provide:

make blueprint-prompts-list
make blueprint-prompt

make blueprint-prompts-list must run make blueprint-pull and print the module outgoing prompt index from Blueprint.

make blueprint-prompt must run make blueprint-pull, run scripts/read_blueprint_outgoing_prompt.py, and print the active prompt content.

Required assistant startup for prompt-driven work

Before starting prompt-driven implementation, the module assistant must run:

make governance-check
make blueprint-prompts-list
make blueprint-prompt
git status --short

The assistant must not proceed if:

the working tree is dirty for unrelated reasons;
the prompt belongs to another module;
the prompt requires forbidden live integration;
the prompt conflicts with module boundary policy.
Allowed prompt statuses
draft
ready_for_module_pull
in_progress
completed
cancelled
superseded
blocked

Only prompts with ready_for_module_pull should be pulled as active work.

Rollout policy

Initial rollout targets:

forprint_integration_gateway
forprint_operational_registry
forprint_library
calculator_engine
forprint_accounting_registry_service

Do not add this blindly to unstable modules whose Makefile or test layout is not normalized.

Telegram Bot is deferred until its Makefile and tests are normalized.

Boundary

This protocol does not allow modules to self-assign architecture work.

Blueprint remains the source of module directives and outgoing prompts.

<!-- module_prompt_workflow_automation_v0_1 -->

Workflow Automation v0.1 extension

Every active governance-aligned module should expose:

make blueprint-prompts-list
make blueprint-prompt
make blueprint-prompt-check

The prompt reader must:

- pull the local Blueprint checkout first when requested by Make target;
- read only the module's own outgoing prompt index;
- prefer active prompts with status `ready_for_module_pull`;
- validate referenced prompt files exist;
- tolerate supported index shapes only;
- fail clearly on malformed YAML;
- fail clearly on unknown module id;
- never execute prompt contents;
- print prompt contents for the assistant/operator to read.

Blueprint must validate outgoing prompt indexes before they are consumed by module assistants.

## Cross-repository write boundary

This protocol allows modules to read Blueprint outgoing prompts.

It does not allow modules to write into the Blueprint repository.

After a module completes a prompt, it must write completion reports and coordination status only inside its own repository.

Blueprint-side intake, review and prompt queue acceptance are separate Blueprint-owned actions.

See:

```text
coordination/standards/governance/module_prompt_execution_and_reporting_protocol.md
```
