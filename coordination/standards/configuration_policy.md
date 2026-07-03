# Configuration Policy

## Status

Target standard / gradual adoption

## Purpose

This document defines the ForPrint policy for module configuration, paths, thresholds, runtime options and non-secret constants.

The goal is to keep module behavior configurable without scattering local paths, server names, timeouts, thresholds, URLs and environment-specific values across business logic.

## Core rule

Avoid hardcoded paths, thresholds, repository locations, timeout values and environment-specific constants in business logic.

Prefer configuration files.

Business logic should not contain hardcoded environment-specific values.

Avoid hardcoding:

```text
absolute paths;
repository locations;
database hosts;
adapter URLs;
timeout values;
retry limits;
feature flags;
runtime thresholds;
report output paths;
external service endpoints;
operator-specific local paths.
```

Prefer:

```text
config files;
environment variables for secrets;
Makefile variables for operator overrides;
documented local overrides;
external secret storage when needed.
```

## Config vs secrets

`config/` is for non-secret configuration that can usually be committed to Git.

Secrets must not be committed to Git.

Do not store these values in repository config files:

```text
tokens;
passwords;
private keys;
real credentials;
production 1C access;
private client data;
OAuth client secrets;
API keys that grant real access;
database passwords.
```

Secrets should be loaded from:

```text
.env files ignored by Git;
environment variables;
local secret files ignored by Git;
external secret storage where available.
```

A separate secrets and `.env` policy may define the exact secret loading convention.

## Preferred config directory

Every active ForPrint module should gradually converge on:

```text
config/
```

Small modules may start with:

```text
config/
├── defaults.yaml
└── module.yaml
```

Larger modules may split configuration by domain:

```text
config/
├── README.md
├── defaults.yaml
├── module.yaml
├── environments/
│   ├── local.yaml
│   ├── sandbox.yaml
│   ├── staging.yaml
│   └── production.yaml
├── adapters/
│   ├── database.yaml
│   ├── integration_gateway.yaml
│   └── external_services.yaml
├── paths/
│   ├── local_paths.yaml
│   └── storage_paths.yaml
└── schemas/
    └── config_schema.yaml
```

Not every module needs every file from the beginning.

Young modules may keep deferred or missing sections until the relevant functionality exists.

## Recommended file roles

### defaults.yaml

Purpose:

```text
Safe non-secret defaults used by the module.
```

May contain:

```text
default timeouts;
retry counts;
pagination limits;
feature defaults;
safe local development values;
non-secret report limits;
default operator display settings.
```

Must not contain secrets.

### module.yaml

Purpose:

```text
Module identity and module-level non-secret behavior.
```

May contain:

```text
module id;
module display name;
owned capabilities;
default mode;
local report names;
coordination file paths;
roadmap or status config references.
```

Must not redefine global Blueprint ownership rules.

### environments/*.yaml

Purpose:

```text
Environment-specific non-secret settings.
```

Common environments:

```text
local;
sandbox;
staging;
production.
```

May contain:

```text
non-secret endpoint names;
runtime mode;
debug flags;
safe local paths;
feature toggles;
non-secret adapter mode selection.
```

Must not contain passwords, tokens or private keys.

### adapters/*.yaml

Purpose:

```text
Non-secret integration and adapter settings.
```

May contain:

```text
adapter enabled/disabled flags;
base route names;
sandbox mode flags;
timeout and retry settings;
contract version references;
non-secret endpoint labels.
```

Must not contain real credentials.

### paths/*.yaml

Purpose:

```text
Local and runtime paths used by the module.
```

May contain:

```text
input directories;
output directories;
report directories;
staging directories;
cache directories;
temporary directories;
operator export paths.
```

Absolute paths may be used for local developer environments when needed, but they must be isolated in config files and not scattered through business logic.

### schemas/*.yaml

Purpose:

```text
Document the expected config shape.
```

May contain:

```text
required sections;
optional sections;
allowed values;
type hints;
migration notes.
```

## Configuration hierarchy

When a module supports layered configuration, the recommended merge order is:

```text
1. config/defaults.yaml
2. config/module.yaml
3. config/environments/<environment>.yaml
4. local ignored overrides when explicitly supported
5. environment variables for secrets and operator overrides
6. Makefile variables for one-off command execution
```

Later layers may override earlier layers.

Secrets should not be placed in layers 1–3.

## Environment selection

A module may use a variable such as:

```text
FORPRINT_ENV=local
```

or a Makefile variable such as:

```text
ENV=local
```

The selected environment should map to:

```text
config/environments/local.yaml
```

The environment name should be explicit in logs and diagnostics.

If no environment is selected, `local` is the preferred safe default for development.

## Configuration loading rule

A module should load configuration through a small dedicated config loader or settings layer.

Business logic should receive already-resolved settings instead of reading YAML files directly in many places.

Preferred pattern:

```text
config files -> config loader -> typed settings object -> business/service code
```

Avoid:

```text
business function opens config YAML directly;
business logic reads random environment variables;
constants are duplicated across scripts;
adapter credentials are mixed with adapter behavior settings.
```

## Coordination configuration

Coordination-related paths and thresholds should be config-driven where practical.

Examples:

```text
Blueprint repository path;
module repository path;
coordination status file path;
prompt queue path;
document awareness ledger path;
roadmap file path;
report output path;
activity warning threshold;
activity critical threshold.
```

The Blueprint path may also be provided by Makefile variable:

```text
BLUEPRINT_ROOT=/path/to/forprint_system_blueprint
```

## Thresholds and limits

Timing, priority and display thresholds should not be hardcoded.

Examples:

```yaml
activity_thresholds:
  p0:
    warning_after_days_without_report: 3
    critical_after_days_without_report: 7
  p1:
    warning_after_days_without_report: 7
    critical_after_days_without_report: 14

dashboard:
  default_limit: 40
  default_before_current: 5
  default_after_current: 10
```

Thresholds should be documented because they affect operator decisions.

## Feature flags

Feature flags may live in config when they are non-secret.

Examples:

```yaml
features:
  prompt_queue_enabled: true
  document_awareness_enabled: true
  roadmap_dashboard_enabled: true
  sandbox_adapters_enabled: false
```

Feature flags must not be used to hide unfinished production behavior without documentation.

## Local overrides

Local overrides are allowed only when documented.

Recommended ignored local files may include:

```text
config/local.override.yaml
config/environments/local.override.yaml
```

Local override files must be listed in `.gitignore` if they can contain machine-specific or private values.

Local overrides should not become the only place where required config structure exists.

## Git policy

Commit:

```text
safe defaults;
module identity config;
environment templates without secrets;
adapter config without credentials;
path templates;
schema files;
README files;
example config files.
```

Do not commit:

```text
real secrets;
private credentials;
operator-only local overrides;
production passwords;
client-private data;
machine-specific temporary paths unless explicitly intended.
```

## Makefile integration

Modules should expose standard Make targets where practical:

```text
make env-check
make config-check
make secrets-check
```

`config-check` should verify that required non-secret config files are readable and structurally valid.

`env-check` should verify that required local runtime variables and executables are present.

`secrets-check` should verify the presence of required secrets without printing secret values.

A missing optional config section may be reported as deferred or not applicable.

A missing required config section should fail clearly.

## Diagnostics rule

Diagnostics may print:

```text
config file paths;
selected environment name;
enabled adapter names;
non-secret timeout values;
non-secret feature flags;
presence/absence of required secrets.
```

Diagnostics must not print:

```text
secret values;
tokens;
passwords;
private keys;
full database URLs containing credentials.
```

## Migration rule

Existing modules may keep their current config layout until a planned migration checkpoint.

Do not perform large config refactors without tests.

For existing modules, prefer this sequence:

```text
1. inventory current config/constants;
2. identify secrets and move them out of committed files;
3. introduce config loader;
4. move paths and thresholds into config;
5. split large config files by domain only when useful;
6. add config-check diagnostics;
7. update docs and completion report.
```

## Non-goals

This policy does not require:

```text
identical config internals in every module;
a specific Python settings library;
immediate refactoring of working modules;
moving all constants into YAML;
committing environment-specific secrets;
large destructive rewrites.
```

## Review rule

During module review, Blueprint may check:

```text
whether config/ exists when needed;
whether secrets are absent from committed config;
whether key paths and thresholds are configurable;
whether config-check exists or is documented as deferred;
whether business logic avoids scattered hardcoded environment values.
```

Review should produce a safe alignment plan, not uncontrolled restructuring.
