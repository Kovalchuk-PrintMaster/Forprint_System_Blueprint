Prompt: Project Inspector Make-First Bootstrap v0.1
Target module

forprint_project_inspector

Working directory

/srv/software_development/forprint-project/forprint_project_inspector

Blueprint directory

/srv/software_development/forprint-project/forprint_system_blueprint

Purpose

Bootstrap the ForPrint Project Inspector module as a minimal make-first project.

The goal is not to implement full project-wide audits yet.

The goal is to create a clean, testable, make-first skeleton that can later own project verification and inspection responsibilities currently described in Blueprint.

Blueprint baseline

Use the current ForPrint System Blueprint.

Project Inspector is registered in Blueprint indexes and has a module policy baseline.

Relevant Blueprint files:

coordination/module_policy/forprint_project_inspector/module_policy.md
coordination/module_policy/module_policy_index.yaml
coordination/module_sources/module_git_sources.yaml
coordination/standards/make_command_standard.md
coordination/templates/module_makefile_standard.template.mk
Core rule

Follow the Blueprint Make Command Standard v0.2 from the beginning.

The module Makefile must use thematic visual blocks and expose standard make-first workflow targets.

Use the Blueprint Makefile scaffold template as the base:

coordination/templates/module_makefile_standard.template.mk
Required bootstrap scope

Create a minimal Python project skeleton.

Required files:

README.md
pyproject.toml
Makefile
forprint_module_manifest.yaml

app/forprint_project_inspector/__init__.py
app/forprint_project_inspector/cli.py

tests/test_bootstrap.py

coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/prompts/index.yaml
coordination/reports/index.yaml
coordination/standards/blueprint_standards_snapshot.yaml
coordination/instruction_intake/blueprint_instruction_packet.yaml

If a file is not meaningful yet, keep it minimal and explicit.

Do not add fake production logic.

Required Makefile targets

At minimum, implement or safely defer the standard targets needed for bootstrap:

install
lint
lint-fix
test
check
check-report
status-report
report-clean

blueprint-pull
blueprint-check
blueprint-sync-directives

blueprint-instruction-list
blueprint-instruction-check
blueprint-instruction-sync
blueprint-instruction

blueprint-standards-list
blueprint-standards-check
blueprint-standards-sync
blueprint-standards

blueprint-prompts-list
blueprint-prompts-check
blueprint-prompts-sync
blueprint-prompts
prompt-read

blueprint-sync

coordination-check
coordination-fix
module-policy-check
governance-check

module-start
module-sync
module-validate

module-finish and completion packet commands may be safely deferred during this bootstrap if completion packet automation is not implemented yet.

Deferral must be explicit and must not fake completed work.

Required behavior

The following commands must work:

make module-start
make module-validate
make check
make check-report
make governance-check

make module-start should:

pull/check Blueprint;
sync or safely defer directives;
list/check/sync instruction intake snapshot;
list/check/sync standards snapshot;
list/check/sync approved Blueprint prompts if available;
check coordination files;
show status report.

make module-validate should:

run check-report;
run check;
run governance-check;
run report-clean;
show status report.
Project Inspector scope boundaries

This bootstrap must not implement real cross-module mutation.

Allowed:

read-only skeleton;
local CLI placeholder;
tests proving package imports and CLI exists;
Makefile standard alignment;
coordination metadata baseline;
Blueprint snapshot baseline.

Forbidden:

editing other module repositories;
running tests inside other modules;
committing or pushing other module repositories;
rewriting other module Makefiles;
production monitoring;
production writes;
live integrations;
automatic remediation.
Initial README direction

README should clearly state:

ForPrint Project Inspector is a future read-only project verification and inspection module.
It will later inspect module structure, Makefile standard adoption, coordination metadata, and readiness.
It does not own Blueprint architecture policy and does not mutate other modules by default.
Required validation before reporting back

Run:

make lint
make test
make check-report
make module-start
make module-validate
git diff --check
git status --short
Final response required

Return:

changed files
created Makefile targets
validation results
whether any targets are deferred
git status
commit recommendation

Do not commit until checks are green and the operator approves.
