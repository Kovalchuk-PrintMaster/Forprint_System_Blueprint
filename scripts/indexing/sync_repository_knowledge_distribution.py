from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = (
    ROOT
    / "coordination"
    / "templates"
    / "repository_knowledge_template"
    / "derivation_manifest.yaml"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def run(*, apply: bool) -> int:
    data = _load_manifest()
    drift: list[str] = []

    for item in data["derivations"]:
        source = ROOT / item["source"]
        derived = ROOT / item["derived"]

        if not source.is_file():
            print(f"MISSING_SOURCE={item['source']}")
            return 1

        if apply:
            derived.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, derived)

        if not derived.is_file() or _sha256(source) != _sha256(derived):
            drift.append(item["derived"])

    if drift:
        print("REPOSITORY_KNOWLEDGE_DISTRIBUTION_DRIFT=" + ",".join(drift))
        return 1

    if apply:
        print("REPOSITORY_KNOWLEDGE_DISTRIBUTION_SYNC=PASS")
    else:
        print("REPOSITORY_KNOWLEDGE_DISTRIBUTION_CHECK=PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    return run(apply=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
