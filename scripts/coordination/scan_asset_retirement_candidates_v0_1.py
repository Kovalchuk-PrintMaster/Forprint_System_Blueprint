#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = (
    ROOT
    / "coordination/internal_work/blueprint/cleanliness/"
    "asset_retirement_registry_v0_1.yaml"
)

EXCLUDED_PREFIXES = (
    ".git/",
    "tmp/",
    "reports/",
    "indexes/",
)


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def tracked_files() -> list[str]:
    process = run_git(["ls-files"])
    if process.returncode != 0:
        raise RuntimeError(process.stdout)
    return [
        line.strip()
        for line in process.stdout.splitlines()
        if line.strip()
        and not line.startswith(EXCLUDED_PREFIXES)
    ]


def last_commit_date(path: str) -> dt.date | None:
    process = run_git(
        ["log", "-1", "--format=%cs", "--", path]
    )
    if process.returncode != 0:
        return None
    value = process.stdout.strip()
    if not value:
        return None
    return dt.date.fromisoformat(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    if args.days < 30:
        raise SystemExit("minimum safe dormancy scan window is 30 days")
    if args.limit < 1:
        raise SystemExit("limit must be positive")

    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    registered = {
        item["path"]: item
        for item in registry.get("assets", [])
    }

    today = dt.date.today()
    candidates: list[tuple[int, str, str]] = []

    for path in tracked_files():
        date = last_commit_date(path)
        if date is None:
            continue
        age_days = (today - date).days
        if age_days < args.days:
            continue

        registered_item = registered.get(path)
        if registered_item is not None:
            # Already governed; report separately instead of duplicating it.
            continue

        candidates.append((age_days, date.isoformat(), path))

    candidates.sort(key=lambda item: (-item[0], item[2]))

    print("ASSET_RETIREMENT_CANDIDATE_SCAN=PASS")
    print("MODE=READ_ONLY")
    print(f"DORMANCY_THRESHOLD_DAYS={args.days}")
    print(f"UNREGISTERED_DORMANT_CANDIDATE_COUNT={len(candidates)}")
    print("AUTOMATIC_DELETION_PERFORMED=false")
    print("AUTOMATIC_ARCHIVE_PERFORMED=false")

    for age_days, date, path in candidates[: args.limit]:
        print(
            "CANDIDATE="
            + path
            + " AGE_DAYS="
            + str(age_days)
            + " LAST_COMMIT_DATE="
            + date
            + " DISPOSITION=NEEDS_OWNER_REVIEW"
        )


if __name__ == "__main__":
    main()
