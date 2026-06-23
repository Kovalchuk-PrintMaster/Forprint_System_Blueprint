ForPrint Project Inspector — Module Policy
Status

Planned / bootstrap pending

Module id

forprint_project_inspector

Working directory

/srv/software_development/forprint-project/forprint_project_inspector

Purpose

ForPrint Project Inspector is the future project-level verification and inspection module for the ForPrint ecosystem.

Its purpose is to inspect whether ForPrint modules follow the agreed architecture, repository structure, Makefile command standard, coordination metadata rules, Blueprint standards, and local readiness requirements.

The module should help the operator and Blueprint understand the current state of all modules without turning Blueprint itself into a permanent cross-module test runner.

Strategic role

Project Inspector is intended to become the dedicated verification layer for the whole ForPrint project.

During early project development, some project-level verification scripts may temporarily live inside forprint_system_blueprint.

As the ecosystem becomes more stable, those scripts should be moved or reimplemented in forprint_project_inspector.

Blueprint remains the source of architectural rules and standards.

Project Inspector verifies adoption of those rules and reports module readiness, gaps, risks, and alignment status.

Owns

Project Inspector may own:

project-level structural verification;
module Makefile standard audits;
module coordination metadata audits;
module status aggregation;
module readiness summaries;
cross-module advisory reports;
standard adoption dashboards or reports;
read-only inspection of module repositories;
project verification scripts migrated from Blueprint;
operator-facing project health summaries.
Does not own

Project Inspector must not own:

ForPrint System Blueprint architecture decisions;
module business logic;
operational order truth;
client truth;
payment truth;
warehouse stock truth;
library catalog truth;
calculator price truth;
prepress lifecycle truth;
production runtime control;
live customer channel handling;
1C accounting sync/write;
automatic posting;
direct fixes inside other modules without explicit operator approval.
Relationship with ForPrint System Blueprint

Blueprint defines:

architecture;
module boundaries;
standards;
coordination protocols;
ownership rules;
cross-module policies;
approved outgoing prompts.

Project Inspector verifies:

which modules follow the standards;
which modules expose required Makefile targets;
which coordination records are missing or stale;
which modules are ready for local work;
which modules need alignment;
which generated reports or verification outputs should be reviewed by Blueprint.

Project Inspector reports findings back to Blueprint through normal coordination channels.

Relationship with modules

Project Inspector may inspect module repositories in read-only mode.

It may check:

Makefile target availability;
Makefile block structure;
module manifest presence;
coordination/status/current_status.yaml;
coordination/reports/index.yaml;
coordination/prompts/index.yaml;
Blueprint instruction and standards snapshots;
completion packet support;
check-report and status-report outputs when explicitly requested.

By default, Project Inspector should not modify module files.

If a repair is needed, it should produce an advisory report or a proposed patch for the module-specific assistant/operator.

Relationship with Production Runtime Inspector

Project Inspector focuses on project structure, standards, coordination, and development readiness.

Production Runtime Inspector focuses on live or runtime service health.

These roles must remain separate.

Project Inspector may report that a module is structurally ready for runtime inspection, but it should not become the runtime monitor itself.

Safety rules

Project Inspector must be read-only by default.

It must not:

commit to other repositories automatically;
push to other repositories automatically;
rewrite module Makefiles automatically;
delete module files;
run destructive commands;
run live integrations;
trigger production writes;
trigger automatic postings;
mutate operational/accounting/warehouse/business data.

Any mutation or repair must require explicit operator approval and should normally happen inside the target module, not from Project Inspector.

Make-first requirement

Project Inspector should follow the ForPrint Make Command Standard.

At minimum, when implemented, it should support:

make install
make lint
make lint-fix
make test
make check
make check-report
make status-report
make blueprint-pull
make blueprint-check
make blueprint-sync
make coordination-check
make module-policy-check
make governance-check
make module-start
make module-validate

Its own Makefile should use the standard thematic block structure from the Blueprint Make Command Standard.

Future expected capabilities

Initial capabilities may include:

module Makefile standard audit;
module policy presence audit;
coordination metadata audit;
module source registry audit;
module status summary aggregation;
Blueprint standards adoption audit;
completion packet readiness audit;
cross-module report generation.

Later capabilities may include:

operator dashboard;
module health scoring;
historical readiness trends;
risk register;
dependency graph inspection;
migration readiness reports;
release readiness reports.
Initial migration path from Blueprint

Blueprint may temporarily host project-level verification scripts under:

scripts/project_verification/
tests/project_verification/

Those scripts should be treated as portable and advisory.

When Project Inspector is ready, they should be moved or reimplemented under:

forprint_project_inspector/

Blueprint should keep only the standards and architectural definitions.

Boundary confirmation

This module is not an orchestrator.

This module is not a business data owner.

This module is not a production runtime controller.

This module is not a replacement for module-local test suites.

This module is an advisory project inspection and verification layer.
