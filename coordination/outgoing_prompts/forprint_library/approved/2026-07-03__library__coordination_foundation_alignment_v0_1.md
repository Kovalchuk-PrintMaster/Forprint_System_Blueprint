# Prompt: Library Coordination Foundation Alignment v0.1

## Target module

`forprint_library`

## Purpose

This prompt aligns ForPrint Library with the current ForPrint System Blueprint coordination foundation before the next product-modeling milestone.

The goal is to make Library ready for structuredPrint Library with the current ForPrint System Blueprint coordination foundation before the Blueprint-driven work using the latest standards for:

```text
Makefile operator workflow;
Prompt Queue navigation;
coordination document awareness;
module roadmap visibility;
configuration architecture;
secrets and .env policy;
project directory skeleton;
completion reporting.

This is a structural and coordination-readiness milestone.

It must not implement new product catalog logic yet.

Strategic reason

ForPrint Library is the canonical semantic/catalog authority for product and service meaning.

Before introducing the Configurable Product Workbench, Library should first be structurally aligned with Blueprint so future work can be exchanged, inspected and reported through the newest coordination mechanism.

This prompt is also a controlled pilot for applying the latest Blueprint standards to an existing active module.

Blueprint source standards

Use the current Blueprint standards and templates as references:

coordination/standards/make_command_standard.md
coordination/templates/module_makefile_standard.template.mk

coordination/standards/configuration_policy.md
coordination/templates/config/

coordination/standards/secrets_and_env_policy.md
coordination/templates/secrets/dotenv.example.template

coordination/standards/repository_structure_baseline.md
coordination/standards/project_structure_standard.md
coordination/templates/project_tree.template.md

coordination/standards/governance/prompt_queue_navigation_policy.md
coordination/templates/prompt_queue_v0_2.template.yaml

Do not copy blindly.

Apply only what is safe and useful for the current Library repository.

Scope

This milestone may update Library coordination and operator structure.

Allowed work:

inspect current Library repository structure;
compare it with Blueprint target structure;
update or add safe Makefile targets for Blueprint-first workflow;
ensure prompt intake/status/report directories are understandable;
ensure completion reports and current status are discoverable;
add or update config/ structure only if safe;
add .env.example only if Library needs local environment variables;
add secrets documentation if needed;
add project tree / structure notes if useful;
add lightweight validators or checks for coordination readiness;
add tests for new validators/checks;
add completion report for this milestone.
Makefile alignment

Align the Library Makefile gradually with the Blueprint Makefile standard.

Preferred capabilities, if not already present:

help;
check;
lint;
test;
check-report;

blueprint-pull;
blueprint-check;
blueprint-sync-directives;

coordination-status;
coordination-report;
completion-report-check;

prompt-queue-validate or equivalent;
prompt-next or equivalent;
prompt-read-next or equivalent;

config-check;
env-check;
secrets-check, if applicable.

Do not perform a large destructive Makefile rewrite.

Do not change working commands without tests.

Do not introduce .RECIPEPREFIX changes unless already part of the module's working style and explicitly safe.

Coordination structure alignment

Library should gradually expose or document:

coordination/README.md
coordination/blueprint_source.yaml
coordination/prompts/index.yaml
coordination/prompts/received/
coordination/reports/index.yaml
coordination/reports/completion/
coordination/reports/commits/
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md

If some areas already exist under different names, do not move them destructively.

Document deviations and safe next steps.

Configuration and secrets alignment

Review whether Library has or needs:

config/
.env.example
secrets documentation
env-check
config-check
secrets-check

Rules:

do not commit real secrets;
do not introduce production credentials;
do not invent unnecessary config files;
do not force config/ migration if Library does not need it yet;
prefer small safe placeholders and documentation.

If Library currently does not need secrets, secrets-check may report:

not_applicable

or remain deferred with clear documentation.

Project tree alignment

Compare the current Library tree with the Blueprint project structure standards.

The output should identify:

what already matches;
what was safely aligned now;
what remains deferred;
what should not be changed yet;
what requires Blueprint decision.

This is not a demand to move application code.

Non-goals

Do not implement:

Configurable Product Workbench;
business_card product skeleton;
new product catalog generation;
1C import;
1C database parsing;
Calculator Engine integration;
production write;
price calculation;
material write-off logic;
CRM/client/carrier entities;
large repository refactor.

This prompt prepares the module for that future work but does not start it.

Validation requirements

The module should remain green.

Run or provide equivalent checks:

make lint
make test
make check
make check-report

If exact target names differ in Library, use the current Library equivalents and document them.

Add tests for any new scripts/checks.

Completion report requirements

Prepare a completion report under Library coordination reports.

The report should state:

what structural/coordination files changed;
which Blueprint standards were applied;
which Makefile targets were added or confirmed;
which config/secrets/tree rules were applied;
what checks were run;
what remains deferred;
whether the module is ready for Configurable Product Workbench v0.1.
Acceptance criteria

This prompt is complete when:

Library can be inspected through current Blueprint coordination expectations;
Makefile/operator workflow is safer and clearer;
coordination status and reports are discoverable;
config/secrets/tree alignment is documented or minimally implemented;
checks pass;
no product-modeling work is mixed into this milestone;
completion report is prepared;
next prompt can safely be Configurable Product Workbench v0.1.
Recommended next prompt after acceptance

After this prompt is completed and accepted by Blueprint, the next Library prompt should be:

Library Configurable Product Workbench v0.1 — Business Card Skeleton

---
