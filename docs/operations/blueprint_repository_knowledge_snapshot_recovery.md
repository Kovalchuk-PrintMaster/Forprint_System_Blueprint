# Blueprint Repository Knowledge Snapshot Recovery

## Before commit

Restore the source registry from the installer backup and remove only files
created by the baseline installer.

The installer may remove only this incorrect Blueprint-local marker:

```text
coordination/repository_knowledge/direction/module_self_view/.gitkeep
```

It must not remove the module distribution marker:

```text
coordination/templates/repository_knowledge_template/
direction/module_self_view/.gitkeep
```

Do not touch unrelated Website, risk-register, internal-work or backup paths.

## After commit

```bash
git revert <baseline-commit>
```

Do not rewrite old snapshots.

## Invalid YAML

Do not commit. Restore the affected snapshot from the package, validate with
`yaml.safe_load`, rerun `make check-report`, then inspect exact diff.

## Incorrect historical content

Create a new correction snapshot and link the superseded artifact. Do not
overwrite a committed historical file.

## Accidental staging

```bash
git restore --staged <unrelated-path>
```

Never use a broad clean command in this repository.
