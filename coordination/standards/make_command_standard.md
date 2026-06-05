# ForPrint Make Command Standard

## Status

Target standard / gradual adoption

## Purpose

This document defines common Makefile command names for ForPrint modules.

The goal is to make module work predictable.

A developer or assistant should be able to run similar commands across modules without learning a completely different command surface every time.

## Core rule

Command names should be standardized.

Implementation may differ per module.

Example:

```text
make test
```

may run Django tests in one module, pytest in another module and shell checks in a utility module.

The external command name should remain consistent.

## Required / preferred targets

Every active module should gradually support:

```text
make install
make lint
make lint-fix
make test
make check
make check-report
make status-report
make blueprint-pull
make blueprint-check
make blueprint-sync-directives
make coordination-check
make coordination-fix
make module-policy-check
```

## install

Purpose:

```text
Install development dependencies.
```

Expected behavior:

```text
create/use venv if project standard defines it;
install package requirements;
prepare project for local checks.
```

## lint

Purpose:

```text
Run configured linter without modifying files.
```

Preferred behavior:

```text
python -m ruff check app scripts tests
```

Module-specific paths are allowed.

## lint-fix

Purpose:

```text
Run configured linter with safe automatic fixes.
```

Preferred behavior:

```text
python -m ruff check app scripts tests --fix
```

## test

Purpose:

```text
Run the module test suite.
```

Expected behavior:

```text
run all current tests required for module confidence;
return non-zero on failure.
```

## check

Purpose:

```text
Run the main local validation flow.
```

Preferred sequence:

```text
lint-fix;
lint;
test;
module-specific validations;
coordination checks if available.
```

`make check` should be the main command before commit.

## check-report

Purpose:

```text
Run module checks and generate human/machine reports.
```

Expected outputs:

```text
reports/<module>_check_report.json
reports/<module>_check_report.md
```

Console output should be easy to read.

## status-report

Purpose:

```text
Generate or show the current module status report without running the full validation suite.

Expected behavior:

read coordination/status/current_status.yaml;
read coordination/status/current_status.md where useful;
print a concise current module status summary;
optionally refresh reports/module_status.json or reports/module_status.md if the module supports it.

Difference from check-report:

check-report = run checks and generate validation report;
status-report = show/export current coordination and development status.

The command should not fake successful checks.

If current status is stale or incomplete, it should report that clearly.


## blueprint-pull

Purpose:

```text
Update the local ForPrint System Blueprint repository.
```

Expected behavior:

```text
git -C /srv/software_development/forprint-project/forprint_system_blueprint pull --ff-only
```

## blueprint-check

Purpose:

```text
Verify that required Blueprint paths exist and are readable.
```

Should check, where applicable:

```text
coordination/global_policy/
coordination/standards/
coordination/module_policy/<module_id>/module_policy.md
coordination/directives/global/index.yaml
coordination/directives/modules/<module_id>/index.yaml
```

Missing module-specific directive index may be a warning during early adoption, not always a hard failure.

## blueprint-sync-directives

Purpose:

```text
Import active Blueprint directives into the local module coordination inbox.
```

Important distinction:

```text
blueprint-pull = update Blueprint repository
blueprint-check = verify Blueprint paths
blueprint-sync-directives = import active directives
```

The canonical directive source is:

```text
module_directives.active
```

from:

```text
coordination/directives/modules/<module_id>/index.yaml
```

Imported directive files should be copied to:

```text
coordination/prompts/received/
```

and registered in:

```text
coordination/prompts/index.yaml
```

The command must avoid duplicate imports.

## coordination-check

Purpose:

```text
Validate module coordination metadata.
```

Preferred behavior:

```bash
/srv/software_development/forprint-project/forprint_system_blueprint/.venv_blueprint/bin/python \
  /srv/software_development/forprint-project/forprint_system_blueprint/scripts/check_coordination_metadata.py \
  --module-root .
```

## coordination-fix

Purpose:

```text
Safely fix simple coordination metadata issues.
```

Preferred behavior:

```bash
/srv/software_development/forprint-project/forprint_system_blueprint/.venv_blueprint/bin/python \
  /srv/software_development/forprint-project/forprint_system_blueprint/scripts/fix_coordination_metadata.py \
  --module-root .
```

When finalizing commit/push metadata, a module may use:

```bash
/srv/software_development/forprint-project/forprint_system_blueprint/.venv_blueprint/bin/python \
  /srv/software_development/forprint-project/forprint_system_blueprint/scripts/fix_coordination_metadata.py \
  --module-root . \
  --update-git-commit \
  --mark-pushed-if-upstream-clean
```

## module-policy-check

Purpose:

```text
Verify that Blueprint module policy for this module is readable.
```

Expected check:

```text
coordination/module_policy/<module_id>/module_policy.md
```

## Help target

Recommended:

```text
make help
```

It should list available targets and short descriptions when practical.

## Deferred targets

If a target cannot be implemented yet, it should not fake success.

Allowed behavior:

```text
print a clear deferred message;
exit 0 only if deferral is expected and documented;
exit non-zero if the missing target blocks the requested action.
```

## Standardization rule

All modules should gradually converge on these command names.

Do not invent module-specific alternatives when a standard command already exists.

Allowed:

```text
make check-report
```

Avoid:

```text
make run-special-super-checks
```

unless it is an additional helper behind the standard command.

## Review rule

During module review, Blueprint may check whether the module exposes standard Makefile targets.

Missing targets should be reported with one of these statuses:

```text
implemented;
deferred;
not_applicable;
missing_needs_fix.
```
