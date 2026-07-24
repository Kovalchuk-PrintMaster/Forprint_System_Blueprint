# Folder Architecture Policy

## Purpose

This standard defines how ForPrint modules should organize folders, scripts, tests, documentation, configuration files, coordination records, fixtures, reports, and other growing file groups.

The goal is to keep every module:

* readable;
* easy to navigate;
* easy to debug;
* easy to audit;
* safe to refactor;
* consistent with the wider ForPrint ecosystem.

ForPrint projects must avoid both extremes:

* overly flat directories with many unrelated files;
* overly deep directory trees that make simple work hard to follow.

The preferred structure is shallow thematic grouping.

## Core Rule

ForPrint projects should prefer one level of thematic nesting when a directory grows or is expected to grow.

Preferred example:

```text
scripts/
  coordination/
  validation/
  reports/
  diagnostics/
```

This is better than a large flat directory:

```text
scripts/
  check_blueprint.py
  sync_blueprint.py
  generate_report.py
  validate_report.py
  update_status.py
  check_status.py
  ...
```

It is also better than unnecessary deep nesting:

```text
scripts/
  coordination/
    blueprint/
      prompts/
        validators/
```

Deep nesting is allowed only when it is clearly justified by responsibility, runtime behavior, data model, versioning, fixtures, or implementation logic.

## Growth Threshold

When a directory contains more than 10 files of the same general type or purpose, the module maintainer must review whether thematic grouping is needed.

This threshold does not require immediate movement of existing files, but it does require a structure decision.

The review should answer:

* Do these files still belong in one directory?
* Are there clear thematic groups?
* Would navigation, debugging, or audit improve if these files were grouped?
* Can new files be placed into a thematic subdirectory from now on?
* Would moving old files require a separate planned refactor checkpoint?

## Preferred Nesting Depth

The default nesting pattern is:

```text
<root_directory>/<theme>/<files>
```

Examples:

```text
scripts/coordination/check_records.py
scripts/reports/generate_status_report.py
scripts/validation/validate_config.py

tests/coordination/test_blueprint_sync.py
tests/database/test_repository_contract.py
tests/content/test_catalog_seed.py

docs/architecture/module_boundaries.md
docs/operations/local_setup.md
docs/contracts/integration_gateway.md
```

The preferred structure normally uses only one thematic level below the main directory.

## Allowed Deep Nesting

Deeper nesting is allowed when there is a strong reason.

Acceptable reasons include:

* generated artifacts must be separated from source files;
* contract fixtures require versioned grouping;
* test data belongs to a specific test family;
* a package has multiple internal subdomains;
* runtime state, snapshots, inbox/outbox, or handoff records need controlled separation;
* import paths or package boundaries require nested structure;
* documentation belongs to a tightly connected policy group.

Example:

```text
tests/fixtures/contracts/gateway/v0_1/
```

This is acceptable if the files are contract fixtures and versioning is part of their responsibility.

Deep nesting should not be used only for visual neatness.

## Naming Rules

Directory names should describe responsibility, not temporary status.

Preferred names:

```text
coordination
validation
reports
diagnostics
database
security
auth
integration
runtime
contracts
fixtures
projections
migrations
maintenance
```

Avoid vague names:

```text
misc
stuff
new
old
temp
helpers
other
```

A directory named `utils` should be used only when the files are truly small shared utilities and cannot be assigned to a clearer responsibility.

## Scripts

When `scripts/` grows, scripts should be grouped by operational purpose.

Recommended examples:

```text
scripts/
  coordination/
  validation/
  reports/
  diagnostics/
  migrations/
  maintenance/
```

Examples:

```text
scripts/coordination/check_blueprint_instructions.py
scripts/coordination/sync_blueprint_directives.py
scripts/reports/generate_status_report.py
scripts/validation/validate_standards_index.py
scripts/diagnostics/check_environment.py
```

A project should avoid placing many unrelated scripts directly in `scripts/`.

## Tests

Tests should be grouped by what they verify.

Recommended examples:

```text
tests/
  unit/
  coordination/
  contracts/
  content/
  database/
  integration/
  reports/
```

Examples:

```text
tests/unit/test_status_model.py
tests/coordination/test_blueprint_records.py
tests/contracts/test_gateway_envelope_contract.py
tests/content/test_catalog_seed.py
tests/database/test_sqlite_repository.py
tests/reports/test_status_report_generation.py
```

A project should avoid placing a large number of unrelated tests directly in `tests/`.

## Documentation

Documentation should be grouped when there are multiple documents for different responsibilities.

Recommended examples:

```text
docs/
  architecture/
  operations/
  contracts/
  decisions/
  examples/
```

Small modules may keep a flat `docs/` directory until the number or variety of documents makes grouping useful.

## Coordination Records

Coordination records should remain easy to audit.

Recommended examples:

```text
coordination/
  status/
  reports/
  prompts/
  standards/
  instruction_intake/
```

When a coordination area grows, it may introduce one thematic level below it.

Example:

```text
coordination/standards/governance/
coordination/standards/modular_topology_and_resilience/
```

Existing flat coordination directories should not be reorganized automatically. Such moves require a separate planned refactor checkpoint.

## Large Single-File Rule

Folder architecture problems can also appear as oversized single files.

A file should be reviewed for splitting when it:

* grows beyond approximately 300 to 500 lines;
* contains more than 5 to 7 independent thematic sections;
* mixes unrelated responsibilities;
* becomes difficult to audit or debug;
* becomes a central dumping ground for new constants, paths, settings, helpers, or runtime logic.

Typical examples include large `config.py`, `settings.py`, `utils.py`, `helpers.py`, or `constants.py` files.

A large file does not have to be split immediately, but new unrelated sections should not continue to be added without review.

Possible refactor directions:

```text
config/
  __init__.py
  env.py
  secrets.py
  paths.py
  telegram.py
  database.py
  ml_models.py
  logging.py
```

or:

```text
config/
  __init__.py
  runtime.py
  paths.py
  integrations.py
  bot.py
  labs.py
```

The project should preserve backward compatibility where practical.

Example:

```python
# config/__init__.py
from .telegram import BOT_TOKEN, ADMIN_CHAT_ID
from .database import SUPABASE_URL, SUPABASE_KEY, SUPABASE_READY
```

This allows older imports such as `from config import BOT_TOKEN` to keep working while the internal structure becomes cleaner.

## Central Config Files

Central configuration files are allowed, but they should not become owners of unrelated module logic.

A central config file may contain:

* simple constants;
* non-secret default paths;
* environment variable loading;
* small runtime flags.

A central config file should not accumulate:

* independent submodule settings without grouping;
* database client initialization mixed with bot settings;
* ML model paths mixed with Telegram settings;
* testing lab constants mixed with production runtime settings;
* large comments describing many unrelated subsystems.

When this happens, the file should be treated as a legacy central config and split gradually.

The preferred refactor approach is:

1. Do not break existing imports.
2. Describe the target structure first.
3. Move one thematic block at a time.
4. Add compatibility exports in `__init__.py` or the old module if needed.
5. Run tests after every move.
6. Commit each safe step separately.

## Existing Files

This policy applies primarily to new files and new growth.

Existing flat directories or oversized files should not be reorganized automatically.

Old files should be moved only when:

* the move is part of an explicit refactor checkpoint;
* tests are updated;
* imports and references are checked;
* generated reports are cleaned or regenerated as expected;
* the change is committed as a clear structural cleanup.

## Assistant Behavior

When an assistant creates or modifies files in any ForPrint module, it should:

1. Check whether the target directory is already large.
2. Avoid adding new files into an overcrowded flat directory.
3. Prefer a clear thematic subdirectory.
4. Keep nesting shallow unless deeper structure is justified.
5. Avoid vague directory names.
6. Mention structural concerns before adding many files.
7. Keep generated, temporary, source, test, fixture, report, and runtime files separated.
8. Review large single files before adding unrelated new sections.
9. Preserve backward compatibility during structural refactors.
10. Respect existing module conventions unless a planned refactor is approved.

## Summary

ForPrint folder architecture should be:

```text
readable
shallow by default
thematically grouped
easy to audit
easy to debug
safe to refactor
consistent across modules
```

The default rule is:

```text
Flat while small.
Grouped when growing.
One thematic nesting level by default.
Deeper nesting only when clearly justified.
Large single files are reviewed like overcrowded directories.
```

<!-- module-workflow-control-v0-1:start -->

## Module-scoped workflow control

Blueprint-owned workflow control must use one module grouping level before the
final workflow folder:

```text
coordination/modules/<module_id>/
scripts/coordination/modules/<module_id>/
tests/coordination/modules/<module_id>/
reports/modules/<module_id>/
operator_input/<module_id>/
tmp/module_workflows/<module_id>/
```

Shared engines, schemas and templates use `_shared`.

A Blueprint control folder for another module is not that module's
implementation repository. Cross-repository implementation files must not be
copied into this structure.

Empty module trees should not be created in advance. Add a module folder only
when a real control workflow, synchronization rule or report exists.

<!-- module-workflow-control-v0-1:end -->
