# Blueprint Repository Knowledge Snapshot Runbook

## Preconditions

- Run at Blueprint root.
- Activate `.venv_blueprint`.
- Record branch, commit and `git status -sb`.
- Do not clean unrelated files.
- Use root `tmp.py` for temporary collector scripts.
- Never use `git add .`.

## Collection

```bash
python -m py_compile tmp.py

rm -rf   /tmp/blueprint_repository_knowledge_input_v0_2   /tmp/blueprint_repository_knowledge_input_v0_2.tar.gz   /tmp/blueprint_repository_knowledge_input_v0_2.tar.gz.sha256

python tmp.py   --repo "$PWD"   --out /tmp/blueprint_repository_knowledge_input_v0_2
```

Verify checksum and `Repository modifications: none`.

## Outputs

Create one dated RCI, one REDM, one Blueprint coordination SDRS and one system
portfolio SDRS.

## Validation

```bash
python - <<'PY'
from pathlib import Path
import yaml

for path in sorted(
    Path("coordination/repository_knowledge").rglob("*.yaml")
):
    yaml.safe_load(path.read_text(encoding="utf-8"))
    print(f"OK: {path}")
PY

make check-report
git diff --check
```

## Historical comparison

From the second snapshot onward, record path changes, flow changes, goal
changes, recurring blockers, repeated rework and unresolved unknowns.

Do not overwrite the previous snapshot.

## Module rollout

Distribute:

```text
coordination/templates/repository_knowledge_template/
```

A module creates RCI, REDM and `module_self_view` SDRS. Module recommendations
remain proposals until Blueprint approves them.
