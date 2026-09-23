from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "coordination/human_intent/index.yaml"
MUTATOR = ROOT / "scripts/coordination/human_intent_mutation_v0_1.py"


def test_human_intent_mutator_validate_and_sync_check():
    for args in (["validate"], ["sync", "--check"]):
        p = subprocess.run(
            [sys.executable, str(MUTATOR), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert p.returncode == 0, p.stdout


def test_human_intent_ledgers_use_one_machine_status_taxonomy():
    index = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    allowed = {"AGREED", "RECOVERED", "PROPOSED", "GAP"}

    for entry in index["modules"]:
        path = INDEX.parent / entry["file"]
        ledger = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert ledger["status"] == "active_planning_context"
        assert ledger["append_only"] is True
        assert all(intent["status"] in allowed for intent in ledger["intents"])


def test_human_intent_yaml_uses_indented_sequences():
    index = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    paths = [INDEX.parent / entry["file"] for entry in index["modules"]]
    paths += sorted((INDEX.parent / "deltas").glob("*.yaml"))

    for path in paths:
        lines = path.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines[:-1]):
            stripped = line.lstrip()
            if not stripped.endswith(":") or stripped.startswith("-"):
                continue
            key_indent = len(line) - len(line.lstrip())
            next_line = lines[i + 1]
            next_stripped = next_line.lstrip()
            if next_stripped.startswith("- "):
                next_indent = len(next_line) - len(next_stripped)
                assert next_indent > key_indent, (
                    f"indentless sequence remains in {path.relative_to(ROOT)} "
                    f"after key line {i + 1}"
                )
