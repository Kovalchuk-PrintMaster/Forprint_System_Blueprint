# Blueprint Internal Workflow Foundation Recovery

## Runtime cleanup

Generated runtime paths may be removed without changing canonical workflow
definitions:

```text
reports/modules/forprint_system_blueprint/current/
reports/modules/forprint_system_blueprint/history/
tmp/module_workflows/forprint_system_blueprint/
operator_input/forprint_system_blueprint/bsa.yaml
```

Do not remove the tracked `README.md` or `.gitignore` files.

## Unconsumed input conflict

The prepare command refuses to overwrite an input file whose status is not
`consumed` or `superseded`.

Review the file. Either resume the matching request or explicitly preserve it
outside the live path before starting another audit.

## Invalid response

Correct only:

```text
operator_input/forprint_system_blueprint/bsa.yaml
```

Then rerun:

```bash
make blueprint-self-audit-resume
```

Do not edit runtime state to bypass request or checksum validation.

## Before commit

Review exact changes and never stage runtime input or temporary bundles.

```bash
git diff --check
git status -sb
```

## Foundation rollback

Before commit, restore patched tracked files from the installer backup and
remove only files created by the foundation installer.

After commit, use a normal Git revert of the foundation commit.
