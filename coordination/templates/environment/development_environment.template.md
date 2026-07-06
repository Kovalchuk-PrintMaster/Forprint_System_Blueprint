# Development Environment

## Module

`forprint_module`

## Purpose

This document describes the local development environment, tooling and diagnostics for this module.

## Python

Expected Python version:

```text
3.11.2

Expected virtual environment:

.venv_module

Expected Python executable:

.venv_module/bin/python
Setup
python3.11 -m venv .venv_module
.venv_module/bin/python -m pip install --upgrade pip
.venv_module/bin/pip install -r requirements/dev.txt

Adapt the commands if the module uses pyproject.toml instead of requirements/dev.txt.

Dependency files

Runtime dependencies:

requirements/app.txt

Development dependencies:

requirements/dev.txt

Alternative dependency source:

pyproject.toml
Standard tools

Expected development tools:

ruff
pytest
PyYAML

Optional tools:

black
mypy
alembic
docker
docker compose
Environment files

Local file:

.env

Committed example:

.env.example

Rules:

.env is local runtime state and must not be committed.
.env.example may be committed.
.env.example must not contain real secrets.
Diagnostics must not print secret values.
Common environment variables

Core:

PROJECT_NAME=
ENV=dev
DEBUG=true
TZ=Europe/Kyiv
LOG_LEVEL=INFO

Paths:

PYTHONPATH=.
VENV_NAME=.venv_module
CONFIG_DIR=config
DATA_DIR=data
LOG_DIR=logs
STATE_DIR=state

Database:

POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=module_dev
POSTGRES_USER=module_user
POSTGRES_PASSWORD=CHANGE_ME_LOCAL_ONLY
POSTGRES_DSN=
PGSSLMODE=prefer

Cache:

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=

Integrations:

TELEGRAM_BOT_TOKEN=
SUPABASE_URL=
SUPABASE_ANON_KEY=
NOVA_POSHTA_API_KEY=
SENTRY_DSN=
SMTP_HOST=

Feature flags:

FEATURE_EXAMPLE=false
Make targets

Install:

make install

Environment check:

make env-check

Tooling check:

make tooling-check

Config check:

make config-check

Secrets check:

make secrets-check

Lint:

make lint

Tests:

make test

Full check:

make check

Visual check report:

make check-report

Diagnostics:

make diagnostics
Local services

PostgreSQL:

status: optional_for_local_dev

Redis:

status: optional_for_local_dev

Docker Compose:

status: optional_for_local_dev

Update this section if the module requires any service for normal local development or tests.

Diagnostics must show

Recommended diagnostics output:

python version
python executable
venv name
project root
dependency files
required directories
git status
available tools
optional service status

Diagnostics must not show:

real tokens
real passwords
real API keys
full production DSNs with passwords
Check-report expectations

make check-report should include, where applicable:

lint
tests
config check
environment check
tooling check
coordination check
module-specific validation
Notes

Document module-specific deviations here.
