# Secrets and Environment Policy

## Status

Target standard / gradual adoption

## Purpose

This document defines the ForPrint policy for secrets, `.env` files, environment variables and secret-related diagnostics.

The goal is to keep real credentials out of Git while giving every module a predictable way to declare, load and verify required local secrets.

## Core rule

Secrets must not be committed to Git.

A ForPrint module may document required secret names, but it must not commit real secret values.

Commit examples and placeholders only.

## What counts as a secret

Treat these values as secrets:

```text
passwords;
API tokens;
bot tokens;
OAuth client secrets;
private keys;
database passwords;
full database URLs containing credentials;
production 1C credentials;
cloud provider access keys;
SMTP passwords;
webhook signing secrets;
client-private credentials;
service account private material.
```

When unsure, treat the value as a secret.

## Config vs secrets

`config/` contains non-secret configuration.

`.env` and external secret stores contain secrets.

Allowed in committed config:

```text
DATABASE_URL environment variable name;
adapter mode;
timeout values;
retry values;
sandbox enabled flag;
non-secret endpoint label;
non-secret route name;
path to required local secret variable name.
```

Not allowed in committed config:

```text
real DATABASE_URL with password;
real bot token;
real API key;
real private key;
real production credential;
client-private data.
```

Preferred pattern:

```text
config says which environment variable to read;
.env provides the local value;
code reads secrets through a settings layer.
```

Example:

```yaml
database:
  enabled: true
  url_env: DATABASE_URL
```

The real `DATABASE_URL` value belongs in an ignored `.env` file or external secret store.

## Module-level .env policy

Each module should have its own local `.env` file.

Do not use one shared global `.env` file for all ForPrint modules as the default pattern.

Reason:

```text
least privilege;
clear module ownership;
easier local debugging;
safer sandbox/staging split;
lower risk of leaking unrelated module credentials.
```

A shared infrastructure secret store may exist later, but module-local secret declaration should remain explicit.

## Recommended files

Committed:

```text
.env.example
```

Ignored:

```text
.env
.env.local
.env.sandbox
.env.staging
.env.production
```

Optional ignored local files:

```text
secrets/local.env
secrets/*.local
secrets/*.secret
```

The exact ignored patterns must be present in `.gitignore` before using local secret files.

## .env.example rule

Every module that needs secrets should provide `.env.example`.

`.env.example` is committed and must contain only safe placeholders.

Allowed:

```text
DATABASE_URL=
TELEGRAM_BOT_TOKEN=
VIBER_AUTH_TOKEN=
ONE_C_USERNAME=
ONE_C_PASSWORD=
```

Also allowed:

```text
DATABASE_URL=postgresql://user:password@localhost:5432/db_name
```

only if the value is clearly fake and not usable.

Preferred for sensitive values:

```text
DATABASE_URL=
API_TOKEN=
BOT_TOKEN=
```

Do not put real tokens into `.env.example`.

## Environment-specific env files

Environment-specific `.env` files may be used locally:

```text
.env.local
.env.sandbox
.env.staging
.env.production
```

These files must be ignored by Git.

A production `.env.production` file must never be committed.

If production secrets are needed, prefer a deployment secret store or server-local secure configuration.

## Loading order

Recommended local loading order:

```text
1. config/defaults.yaml
2. config/module.yaml
3. config/environments/<environment>.yaml
4. .env or .env.<environment> ignored by Git
5. real environment variables already present in the shell/systemd/container
6. Makefile variables for one-off operator overrides
```

Environment variables already present in the runtime may override `.env` values when the module explicitly supports this.

The selected environment should be explicit:

```text
FORPRINT_ENV=local
```

or:

```text
ENV=local
```

## Secret naming convention

Use clear uppercase names.

Recommended format:

```text
FORPRINT_<MODULE>_<PURPOSE>
```

or common integration names:

```text
DATABASE_URL
INTEGRATION_GATEWAY_BASE_URL
TELEGRAM_BOT_TOKEN
VIBER_AUTH_TOKEN
SMTP_PASSWORD
ONE_C_USERNAME
ONE_C_PASSWORD
```

Avoid vague names:

```text
TOKEN
PASSWORD
KEY
SECRET
```

unless the module is very small and the context is unambiguous.

## Runtime access rule

Application code should not read secrets randomly throughout the codebase.

Preferred pattern:

```text
.env / environment -> settings loader -> typed settings object -> services/adapters
```

Avoid:

```text
os.getenv(...) scattered across business logic;
adapter files loading unrelated secrets;
printing secret values during startup;
committed config containing private values.
```

## Makefile integration

Modules should expose:

```text
make secrets-check
```

Purpose:

```text
Verify that required secrets are configured without printing secret values.
```

Allowed output:

```text
DATABASE_URL: present
TELEGRAM_BOT_TOKEN: missing
VIBER_AUTH_TOKEN: present
```

Forbidden output:

```text
DATABASE_URL=postgresql://user:real_password@host/db
TELEGRAM_BOT_TOKEN=real_token
```

`secrets-check` should return non-zero when a required secret is missing for the selected environment.

Optional or deferred secrets may be reported as:

```text
deferred;
not_applicable;
optional_missing.
```

## Diagnostics redaction rule

Diagnostics may print:

```text
secret variable name;
presence/absence;
selected environment;
secret source type;
safe placeholder examples.
```

Diagnostics must not print:

```text
secret values;
partial tokens;
password fragments;
private key contents;
full URLs containing credentials.
```

If a URL may contain credentials, print only a redacted version:

```text
postgresql://<redacted>@host:5432/db
```

or print only:

```text
DATABASE_URL: present
```

## Git policy

`.gitignore` should ignore:

```text
.env
.env.*
*.pem
*.key
*.crt
*.p12
*.pfx
*.sqlite
*.sqlite3
*.db
```

`.env.example` should be explicitly allowed:

```text
!.env.example
```

Before committing, run:

```text
git status --short
git diff --cached --check
```

If secret-like files are staged, stop and inspect.

## Secret rotation rule

If a real secret is accidentally committed:

```text
1. stop using the secret immediately;
2. rotate/revoke it in the external service;
3. remove it from the repository;
4. document the incident in the module coordination report if relevant;
5. do not rely only on deleting the line from the latest commit.
```

Git history may still contain the leaked value.

## Sandbox and production separation

Sandbox credentials and production credentials must be separate.

A module must not use production credentials in sandbox tests unless explicitly approved.

Production write access must be guarded by configuration and secrets policy.

Recommended production safety flag:

```text
PRODUCTION_WRITE_ENABLED=false
```

The flag itself is not a secret, but production credentials are secrets.

## 1C and accounting credentials

1C credentials are sensitive.

Do not commit:

```text
production 1C username;
production 1C password;
production 1C connection string with credentials;
production exchange keys.
```

For sandbox import/export work, use fake or local-only credentials and keep real values ignored.

## Bot and channel tokens

Telegram, Viber, website webhook, email and future mobile channel credentials are secrets.

Do not commit:

```text
bot tokens;
webhook signing secrets;
channel auth tokens;
SMTP passwords;
OAuth client secrets.
```

Committed adapter config may reference environment variable names only.

## Local secret directories

If a module needs a `secrets/` directory, it should contain only documentation or ignored local files.

Allowed committed file:

```text
secrets/README.md
```

Ignored local examples:

```text
secrets/local.env
secrets/service_account.local.json
secrets/private.key
```

Do not commit real secret material from `secrets/`.

## CI and automation

CI should receive secrets from the CI secret store, not from committed files.

CI logs must not print secret values.

If a CI job runs `secrets-check`, it should verify presence only.

## Review rule

During module review, Blueprint may check:

```text
whether .env.example exists when secrets are required;
whether .gitignore protects .env files;
whether committed config avoids real credentials;
whether secrets-check exists or is documented as deferred;
whether diagnostics redact secret values;
whether production credentials are separated from sandbox credentials.
```

Review should produce a safe alignment plan, not uncontrolled restructuring.

## Non-goals

This policy does not require:

```text
a specific Python dotenv library;
immediate migration of all existing modules;
one global secret manager from day one;
committing real secret values;
printing secrets for debugging;
large destructive refactors.
```
