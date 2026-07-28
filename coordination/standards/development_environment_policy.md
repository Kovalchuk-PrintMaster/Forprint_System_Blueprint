# ForPrint Development Environment and Tooling Policy

## Status

Target standard.

Adoption mode: gradual alignment.

## Purpose

This document defines the shared development environment and tooling expectations for ForPrint modules.

The goal is to keep module setup, validation, diagnostics and operator workflows predictable across the ForPrint ecosystem while still allowing module-specific implementation details.

This policy covers:

- Python runtime conventions;
- virtual environment naming;
- runtime and development dependency files;
- linting and testing tools;
- environment and secrets handling;
- local service dependencies;
- Makefile operator targets;
- diagnostics and check-report expectations;
- generated/runtime directory conventions.

## Scope

This policy applies to Python-based ForPrint modules and to mixed modules that use Python for tooling, validation or coordination scripts.

For non-Python modules, the same operator concepts should be preserved where possible:

- stable Makefile targets;
- environment check;
- tooling check;
- test/check/check-report;
- secrets separation;
- diagnostics.

## Core principles

### Makefile first

Operators and assistants should prefer documented Make targets over raw tool commands.

Examples:

```text
make install
make env-check
make tooling-check
make lint
make test
make check
make check-report
```

Raw commands may be used during debugging, but stable module workflows should be exposed through Makefile targets.

Local environment must be inspectable

A module should make it easy to answer:

which Python interpreter is used;
which virtual environment is expected;
which dependency files are authoritative;
which local services are required;
which secrets are required but not committed;
which generated files are expected;
which checks prove the module is healthy.
Secrets and configuration are separate

Configuration defaults, examples and schemas may be committed.

Secrets must not be committed.

A real .env file is local/runtime state.

A committed .env.example or template must contain empty or obviously fake placeholder values only.

Development tools must not define business truth

Tools such as PostgreSQL, Redis, Docker, Supabase, Telegram, Sentry, Mermaid, Ruff or pytest support development and operations.

They must not change ForPrint domain ownership rules.

Python runtime
Baseline Python version

ForPrint Python modules should use Python 3.11.2 unless a module-specific reason is documented.

A module may use a newer Python version only if:

the reason is documented;
Blueprint is informed;
dependency compatibility is checked;
deployment/runtime compatibility is considered.
Python executable variable

Module Makefiles should expose a PYTHON variable.

Example:

PYTHON ?= .venv_module/bin/python

Blueprint itself may use:

PYTHON ?= .venv_blueprint/bin/python

The exact module venv name should follow the module naming convention below.

Virtual environments
Naming convention

Python modules should use one local virtual environment per repository.

Recommended pattern:

.venv_<module_short_name>

Examples:

.venv_blueprint
.venv_forprint_library
.venv_gateway
.venv_calculator
.venv_accounting_registry

The venv directory is local runtime state and must not be committed.

Venv expectations

The module should document:

venv name;
Python version;
install command;
dependency source;
how to recreate the environment;
how to verify the environment.

Recommended Make targets:

make install
make env-check
make tooling-check
Dependency files

A module should use one of the following dependency layouts.

Option A: requirements files

Recommended for simple or early modules:

requirements/app.txt
requirements/dev.txt

Expected meaning:

requirements/app.txt = runtime dependencies
requirements/dev.txt = development/test/lint dependencies

requirements/dev.txt may include:

-r app.txt
Option B: pyproject.toml

Recommended for packaged Python modules or modules with stronger tooling needs.

Expected sections may include:

[project]
[project.optional-dependencies]
[tool.ruff]
[tool.pytest.ini_options]
Versioning strategy

Early development may use compatible lower bounds:

ruff>=0.5.0
pytest>=8.0.0

Stabilized modules may move toward pinned or locked dependencies.

If a lock file is introduced, the module should document whether it is source-of-truth.

Standard development tools
Ruff

Ruff is the preferred linting and import-order tool for Python modules.

Recommended target:

make lint
make lint-fix

Recommended underlying command pattern:

$(PYTHON) -m ruff check app scripts tests
$(PYTHON) -m ruff check app scripts tests --fix

The exact paths may differ per module.

Pytest

Pytest is the preferred test runner for Python modules.

Recommended target:

make test

Recommended underlying command pattern:

$(PYTHON) -m pytest -q
YAML validation

Modules with YAML contracts, catalogs, prompt indexes, roadmaps or coordination metadata should validate them through tests or explicit validation scripts.

YAML validation should be included in:

make check
make check-report

where applicable.

Mermaid

Mermaid may be used for generated architecture diagrams and documentation visualizations.

Mermaid diagram generation should be deterministic and validated when diagrams are tracked artifacts.

Raw .mmd files should not be wrapped in Markdown fences unless the module standard explicitly says otherwise.

Runtime and local service dependencies

A module may use local services such as:

PostgreSQL;
Redis;
Docker Compose;
Supabase;
Telegram Bot API;
Nova Poshta API;
S3/MinIO;
SMTP;
Sentry or telemetry services.

A service must be classified as one of:

required_for_local_dev
optional_for_local_dev
required_for_tests
optional_future_integration
production_only
deferred

The module should avoid requiring external paid/cloud services for basic local tests unless explicitly approved.

Environment variables
.env

A real .env file is local state and must not be committed.

It may contain:

runtime mode;
local paths;
database connection details;
API keys;
bot tokens;
admin identifiers;
feature flags;
logging settings.
.env.example

A committed .env.example may document expected keys, but must not contain real secrets.

Allowed examples:

BOT_TOKEN=
SUPABASE_URL=
SUPABASE_ANON_KEY=
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=module_dev
POSTGRES_USER=module_user
POSTGRES_PASSWORD=CHANGE_ME_LOCAL_ONLY
LOG_LEVEL=INFO

Disallowed examples:

real bot tokens
real API keys
real database passwords
real personal admin identifiers
real production DSNs
Required variable categories

Common categories:

core mode:
  PROJECT_NAME
  ENV
  DEBUG
  TZ
  LOG_LEVEL

paths:
  PYTHONPATH
  VENV_NAME
  CONFIG_DIR
  DATA_DIR
  LOG_DIR
  STATE_DIR

database:
  POSTGRES_HOST
  POSTGRES_PORT
  POSTGRES_DB
  POSTGRES_USER
  POSTGRES_PASSWORD
  POSTGRES_DSN
  PGSSLMODE

cache:
  REDIS_HOST
  REDIS_PORT
  REDIS_DB
  REDIS_URL

integrations:
  TELEGRAM_BOT_TOKEN
  SUPABASE_URL
  SUPABASE_ANON_KEY
  NOVA_POSHTA_API_KEY
  SENTRY_DSN
  SMTP_HOST

feature flags:
  FEATURE_*

Modules should use module-prefixed variables when a generic name may conflict.

Example:

CALC_LIBRARY_BASE_URL
GATEWAY_ROUTES_CONFIG
LIBRARY_CATALOG_SEED
Environment checks

A module should provide make env-check.

The target should verify:

expected Python executable is available;
venv is present or clearly report how to create it;
required dependency files exist;
required config templates exist;
required local directories exist or can be created;
required environment variables are documented;
missing secrets are reported without printing secret values.

env-check should not print secret values.

Tooling checks

A module may provide make tooling-check.

The target should verify:

Ruff import is available;
pytest import is available;
required YAML library is available;
required module-specific CLI tools are available;
optional tools are reported as optional, not hard failures.

If tooling-check is not separate, its checks may be included in env-check or check-report.

Config and secrets checks

Recommended targets:

make config-check
make secrets-check

config-check should verify that committed config files and templates are structurally valid.

secrets-check should verify that required secret names are documented and local secret files are ignored, but it must not print real values.

A secrets check may fail if obvious real secrets are found in tracked files.

Diagnostics

Recommended target:

make diagnostics

Diagnostics may include:

Python version;
venv path;
project root;
config path;
data/log/state directories;
git branch and status;
dependency import checks;
local service connectivity checks if safe.

Diagnostics must not print real secrets.

Check-report integration

make check-report should be the main confidence command.

Where applicable, it should include:

lint;
tests;
YAML/schema validation;
config check;
env/tooling check;
coordination metadata check;
generated report validation;
module-specific smoke checks.

A check report should be readable by an operator and suitable for completion reports.

Runtime directories

Recommended local/runtime directories:

data/
logs/
tmp/
reports/
state/

Rules:

data/ may contain local runtime data or fixtures depending on the module;
logs/ is runtime output;
tmp/ is scratch space;
reports/ may contain generated reports;
state/ may contain local service state.

Generated or runtime files should not dirty git unless intentionally tracked.

Generated artifacts

Generated files should be classified as:

source_of_truth_generated
operator_report
runtime_output
temporary_output

Only source-of-truth generated files should usually be tracked.

Operator reports may be tracked only when the module explicitly treats them as evidence or coordination records.

Module tooling manifest

Each module may maintain a tooling manifest based on the Blueprint template.

The manifest should summarize:

Python version;
venv name;
dependency files;
Make targets;
required local tools;
optional services;
env files;
diagnostics;
check-report coverage.
Assistant/operator behavior

Before changing a module, assistants should prefer:

make module-start
make prompt-dashboard
make prompt-next
make document-awareness
make status-report

Before commit, assistants should prefer:

make lint
make test
make check-report
git diff --check
git status --short

After a working checkpoint, assistants should help the operator commit and push.

Non-goals

This policy does not require every module to use:

FastAPI;
Django;
PostgreSQL;
Redis;
Docker;
Supabase;
Telegram;
Celery;
Alembic;
Sentry;
any specific dotenv/settings library.

Those tools are module-specific choices.

The shared requirement is that the module documents and validates its environment clearly.
