#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
HI_DIR = ROOT / "coordination/human_intent"
INDEX = HI_DIR / "index.yaml"

CANONICAL_STATUSES = {"AGREED", "RECOVERED", "PROPOSED", "GAP"}
SECTION_HEADING = "## Module intent ledgers"


class IndentDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(data) -> str:
    return yaml.dump(
        data,
        Dumper=IndentDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=110,
    )


def save_yaml(path: Path, data) -> None:
    text = dump_yaml(data)
    if yaml.safe_load(text) != data:
        raise RuntimeError(f"round-trip mismatch: {path}")
    path.write_text(text, encoding="utf-8")


def display_name(entry: dict) -> str:
    value = entry.get("display_name")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return str(entry["module_id"]).replace("_", " ").title()


def sync_index_counts(index: dict) -> None:
    seen = set()
    for entry in index["modules"]:
        module_id = entry["module_id"]
        if module_id in seen:
            raise RuntimeError(f"duplicate module_id in Human Intent index: {module_id}")
        seen.add(module_id)
        path = HI_DIR / entry["file"]
        ledger = load_yaml(path)
        if ledger["module_id"] != module_id:
            raise RuntimeError(f"module_id mismatch: {path}")
        entry["intent_count"] = len(ledger["intents"])


def render_readme_text(index: dict) -> str:
    current = (HI_DIR / "README.md").read_text(encoding="utf-8")
    if SECTION_HEADING not in current:
        raise RuntimeError("Human Intent README module section missing")
    prefix = current.split(SECTION_HEADING, 1)[0].rstrip()
    lines = [
        prefix,
        "",
        SECTION_HEADING,
        "",
        "These links are the canonical navigation surface for the per-module human-intent ledgers.",
        "",
    ]
    for entry in index["modules"]:
        lines.append(
            f"- [{display_name(entry)}]({entry['file']}) — "
            f"{entry['intent_count']} captured human-intent entries."
        )
    return "\n".join(lines).rstrip() + "\n"


def validate(index: dict) -> list[str]:
    issues = []
    seen_ids = set()
    seen_modules = set()
    readme = (HI_DIR / "README.md").read_text(encoding="utf-8")

    if index.get("schema_version") != "forprint_human_intent_index_v0_1":
        issues.append("unexpected Human Intent index schema_version")
    if index.get("append_only") is not True:
        issues.append("Human Intent index append_only must be true")

    for entry in index.get("modules", []):
        module_id = entry.get("module_id")
        if module_id in seen_modules:
            issues.append(f"duplicate module_id: {module_id}")
        seen_modules.add(module_id)

        path = HI_DIR / entry["file"]
        if not path.is_file():
            issues.append(f"ledger file missing: {entry['file']}")
            continue

        ledger = load_yaml(path)
        if ledger.get("module_id") != module_id:
            issues.append(f"ledger module_id mismatch: {entry['file']}")
        if ledger.get("append_only") is not True:
            issues.append(f"ledger append_only not true: {entry['file']}")
        if ledger.get("status") != "active_planning_context":
            issues.append(f"ledger status not standardized: {entry['file']}")

        intents = ledger.get("intents")
        if not isinstance(intents, list):
            issues.append(f"ledger intents is not list: {entry['file']}")
            continue

        if len(intents) != entry.get("intent_count"):
            issues.append(f"intent_count drift: {entry['file']}")

        nav = (
            f"]({entry['file']}) — {entry['intent_count']} "
            "captured human-intent entries."
        )
        if nav not in readme:
            issues.append(f"README navigation/count drift: {entry['file']}")

        for intent in intents:
            iid = intent.get("intent_id")
            status = intent.get("status")
            text = intent.get("text")
            if not isinstance(iid, str) or not iid.strip():
                issues.append(f"missing intent_id: {entry['file']}")
                continue
            if iid in seen_ids:
                issues.append(f"duplicate intent_id: {iid}")
            seen_ids.add(iid)
            if status not in CANONICAL_STATUSES:
                issues.append(f"noncanonical status {status!r}: {iid}")
            if not isinstance(text, str) or not text.strip():
                issues.append(f"empty intent text: {iid}")

    return issues


def load_record(path: Path) -> dict:
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise RuntimeError("intent record file must contain a YAML mapping")
    required = {"intent_id", "status", "text"}
    missing = required - set(data)
    if missing:
        raise RuntimeError("intent record missing required fields: " + ", ".join(sorted(missing)))
    if data["status"] not in CANONICAL_STATUSES:
        raise RuntimeError(
            "intent status must be one of: " + ", ".join(sorted(CANONICAL_STATUSES))
        )
    return data


def append_intent(module_id: str, record_file: Path) -> None:
    index = load_yaml(INDEX)
    matches = [x for x in index["modules"] if x["module_id"] == module_id]
    if len(matches) != 1:
        raise RuntimeError(f"module_id must resolve exactly once: {module_id}")

    entry = matches[0]
    ledger_path = HI_DIR / entry["file"]
    ledger = load_yaml(ledger_path)
    record = load_record(record_file)

    all_ids = {
        intent["intent_id"]
        for item in index["modules"]
        for intent in load_yaml(HI_DIR / item["file"])["intents"]
    }
    if record["intent_id"] in all_ids:
        raise RuntimeError(f"intent_id already exists: {record['intent_id']}")

    ledger["intents"].append(copy.deepcopy(record))
    save_yaml(ledger_path, ledger)
    sync_index_counts(index)
    save_yaml(INDEX, index)
    (HI_DIR / "README.md").write_text(render_readme_text(index), encoding="utf-8")


def cmd_validate() -> int:
    index = load_yaml(INDEX)
    issues = validate(index)
    if issues:
        print("HUMAN_INTENT_SURFACES=FAIL")
        for issue in issues:
            print(" - " + issue)
        return 1
    print("HUMAN_INTENT_SURFACES=PASS")
    print(f"MODULE_COUNT={len(index['modules'])}")
    print("INTENT_COUNT=" + str(sum(int(x["intent_count"]) for x in index["modules"])))
    return 0


def cmd_sync(check: bool) -> int:
    index = load_yaml(INDEX)
    before_index = INDEX.read_text(encoding="utf-8")
    before_readme = (HI_DIR / "README.md").read_text(encoding="utf-8")

    sync_index_counts(index)
    index_text = dump_yaml(index)
    readme_text = render_readme_text(index)

    if check:
        drift = []
        if index_text != before_index:
            drift.append("coordination/human_intent/index.yaml")
        if readme_text != before_readme:
            drift.append("coordination/human_intent/README.md")
        if drift:
            for path in drift:
                print("HUMAN_INTENT_SYNC_DRIFT=" + path)
            return 1
        print("HUMAN_INTENT_SYNC_CHECK=PASS")
        return 0

    INDEX.write_text(index_text, encoding="utf-8")
    (HI_DIR / "README.md").write_text(readme_text, encoding="utf-8")
    print("HUMAN_INTENT_SYNC=PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Canonical Human Intent ledger mutation/synchronization utility."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    sync_p = sub.add_parser("sync")
    sync_p.add_argument("--check", action="store_true")

    append_p = sub.add_parser("append")
    append_p.add_argument("--module-id", required=True)
    append_p.add_argument("--record-yaml", type=Path, required=True)

    args = parser.parse_args()

    if args.command == "validate":
        return cmd_validate()
    if args.command == "sync":
        return cmd_sync(args.check)
    if args.command == "append":
        append_intent(args.module_id, args.record_yaml)
        return cmd_validate()
    raise AssertionError("unreachable")


if __name__ == "__main__":
    sys.exit(main())
