#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BASELINE = (
    ROOT / "coordination/internal_work/blueprint/normalization/"
    "2026-09-01__document_surface_normalization_baseline_v0_1.yaml"
)
REGISTER = (
    ROOT / "coordination/internal_work/blueprint/normalization/"
    "2026-09-01__remaining_surface_disposition_register_v0_1.yaml"
)
REGISTRY = ROOT / "coordination/standards/governance/document_type_registry_v0_1.yaml"


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def indentless(text: str) -> bool:
    lines = text.splitlines()
    for index, line in enumerate(lines[:-1]):
        stripped = line.lstrip()
        if not stripped.endswith(":") or stripped.startswith("-"):
            continue

        indent = len(line) - len(stripped)
        next_line = lines[index + 1]
        next_stripped = next_line.lstrip()

        if next_stripped.startswith("- ") and len(next_line) - len(next_stripped) <= indent:
            return True

    return False


def h1(text: str) -> int:
    return sum(bool(re.match(r"^#(?!#)\s+", line)) for line in text.splitlines())


def fail(message: str) -> None:
    print("CLEANLINESS_NORMALIZATION_CLOSURE=FAIL")
    print("ERROR=" + message)
    raise SystemExit(1)


def missing_surface_is_allowed(entry: dict) -> bool:
    """Return True for classified generated/historical surfaces allowed absent."""
    return (
        entry.get("disposition") == "PRESERVED_CLASSIFIED"
        and entry.get("preservation_class") == "GENERATED_OR_HISTORICAL_REPORT"
        and entry.get("mutation_policy") == "regenerate_from_source_when_needed"
        and entry.get("immutable_snapshot_hash_enforced") is False
    )


baseline = load(BASELINE)
register = load(REGISTER)
registry = load(REGISTRY)

active = list(baseline.get("yaml_debt", [])) + list(baseline.get("markdown_debt", []))
if active:
    fail("ACTIVE_BASELINE_DEBT_NOT_ZERO")

if baseline.get("active_debt_count") != 0:
    fail("ACTIVE_DEBT_COUNT_FIELD")

entries = register.get("entries", [])
if len(entries) != 235:
    fail("DISPOSITION_COUNT")

paths = [entry.get("path") for entry in entries]
if len(set(paths)) != 235:
    fail("DISPOSITION_PATH_UNIQUENESS")

expected = {
    "NORMALIZED_PACKAGE_A": 70,
    "REGENERATED_PACKAGE_B": 14,
    "NORMALIZED_PACKAGE_C": 1,
    "ALREADY_RESOLVED_PRE_CLOSURE": 1,
    "PRESERVED_CLASSIFIED": 149,
}
counts: dict[str, int] = {}
for entry in entries:
    disposition = entry["disposition"]
    counts[disposition] = counts.get(disposition, 0) + 1

if counts != expected:
    fail("DISPOSITION_COUNTS")

for entry in entries:
    path = ROOT / entry["path"]
    if not path.is_file():
        if missing_surface_is_allowed(entry):
            continue
        fail("MISSING_SURFACE:" + entry["path"])

    disposition = entry["disposition"]
    if disposition in {
        "NORMALIZED_PACKAGE_A",
        "REGENERATED_PACKAGE_B",
        "NORMALIZED_PACKAGE_C",
        "ALREADY_RESOLVED_PRE_CLOSURE",
    }:
        if path.suffix.lower() in {".yaml", ".yml"} and indentless(
            path.read_text(encoding="utf-8")
        ):
            fail("INDENTLESS_NORMALIZED_SURFACE:" + entry["path"])

        if path.suffix.lower() == ".md" and h1(path.read_text(encoding="utf-8")) != 1:
            fail("H1_NORMALIZED_SURFACE:" + entry["path"])

    if entry.get("immutable_snapshot_hash_enforced") is True:
        if sha(path) != entry["u70_sha256"]:
            fail("IMMUTABLE_PRESERVED_HASH_DRIFT:" + entry["path"])

machine = [
    entry
    for entry in entries
    if entry["original_document_type"] == "machine_authority"
    and entry["disposition"] == "NORMALIZED_PACKAGE_A"
]
for entry in machine:
    data = load(ROOT / entry["path"])
    for key in ("schema_version", "status", "authority"):
        if key not in data:
            fail("MACHINE_METADATA:" + entry["path"] + ":" + key)

standards = [
    entry
    for entry in entries
    if entry["original_document_type"] == "standard_or_policy"
    and entry["disposition"] == "NORMALIZED_PACKAGE_A"
    and entry["path"].endswith((".yaml", ".yml"))
]
for entry in standards:
    data = load(ROOT / entry["path"])
    for key in ("schema_version", "status", "authority"):
        if key not in data:
            fail("STANDARD_METADATA:" + entry["path"] + ":" + key)

if registry.get("classified_disposition_register") != str(REGISTER.relative_to(ROOT)):
    fail("REGISTRY_REGISTER_LINK")

print("CLEANLINESS_NORMALIZATION_CLOSURE=PASS")
print("REVIEWED_SURFACE_COUNT=235")
print("ACTIVE_BASELINE_DEBT_PATH_COUNT=0")
print("NORMALIZED_PACKAGE_A_COUNT=70")
print("REGENERATED_PACKAGE_B_COUNT=14")
print("NORMALIZED_PACKAGE_C_COUNT=1")
print("ALREADY_RESOLVED_COUNT=1")
print("CLASSIFIED_PRESERVED_COUNT=149")
