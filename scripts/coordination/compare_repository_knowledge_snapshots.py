#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

IDENTITY_KEYS = (
    "step_id",
    "flow_id",
    "module_id",
    "prompt_id",
    "risk_id",
    "finding_id",
    "class_id",
    "snapshot_id",
    "path",
    "id",
    "name",
)


@dataclass(frozen=True)
class Change:
    path: str
    change_type: str
    previous: Any = None
    current: Any = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "path": self.path,
            "change_type": self.change_type,
        }

        if self.change_type != "added":
            data["previous"] = self.previous

        if self.change_type != "removed":
            data["current"] = self.current

        return data


def load_document(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")

    if path.suffix.lower() == ".json":
        return json.loads(text)

    return yaml.safe_load(text)


def identity_key_for_list(
    previous: list[Any],
    current: list[Any],
) -> str | None:
    combined = previous + current
    dict_items = [item for item in combined if isinstance(item, dict)]

    if not dict_items or len(dict_items) != len(combined):
        return None

    for key in IDENTITY_KEYS:
        valid = True

        for items in (previous, current):
            values: set[str] = set()

            for item in items:
                if not isinstance(item, dict):
                    valid = False
                    break

                value = item.get(key)

                if not isinstance(value, (str, int)):
                    valid = False
                    break

                normalized = str(value)

                if normalized in values:
                    valid = False
                    break

                values.add(normalized)

            if not valid:
                break

        if valid:
            return key

    return None


def child_path(parent: str, child: str) -> str:
    return f"{parent}.{child}" if parent else child


def compare_values(
    previous: Any,
    current: Any,
    *,
    path: str = "",
) -> list[Change]:
    if type(previous) is not type(current):
        return [
            Change(
                path=path or "$",
                change_type="type_changed",
                previous=previous,
                current=current,
            )
        ]

    if isinstance(previous, dict):
        changes: list[Change] = []
        previous_keys = set(previous)
        current_keys = set(current)

        for key in sorted(previous_keys - current_keys):
            changes.append(
                Change(
                    path=child_path(path, str(key)),
                    change_type="removed",
                    previous=previous[key],
                )
            )

        for key in sorted(current_keys - previous_keys):
            changes.append(
                Change(
                    path=child_path(path, str(key)),
                    change_type="added",
                    current=current[key],
                )
            )

        for key in sorted(previous_keys & current_keys):
            changes.extend(
                compare_values(
                    previous[key],
                    current[key],
                    path=child_path(path, str(key)),
                )
            )

        return changes

    if isinstance(previous, list):
        identity_key = identity_key_for_list(previous, current)

        if identity_key:
            previous_index = {
                str(item[identity_key]): item for item in previous if isinstance(item, dict)
            }
            current_index = {
                str(item[identity_key]): item for item in current if isinstance(item, dict)
            }
            changes: list[Change] = []

            for identity in sorted(set(previous_index) - set(current_index)):
                changes.append(
                    Change(
                        path=(
                            f"{path}[{identity_key}={identity}]"
                            if path
                            else f"[{identity_key}={identity}]"
                        ),
                        change_type="removed",
                        previous=previous_index[identity],
                    )
                )

            for identity in sorted(set(current_index) - set(previous_index)):
                changes.append(
                    Change(
                        path=(
                            f"{path}[{identity_key}={identity}]"
                            if path
                            else f"[{identity_key}={identity}]"
                        ),
                        change_type="added",
                        current=current_index[identity],
                    )
                )

            for identity in sorted(set(previous_index) & set(current_index)):
                item_path = (
                    f"{path}[{identity_key}={identity}]" if path else f"[{identity_key}={identity}]"
                )
                changes.extend(
                    compare_values(
                        previous_index[identity],
                        current_index[identity],
                        path=item_path,
                    )
                )

            return changes

        if previous == current:
            return []

        return [
            Change(
                path=path or "$",
                change_type="list_changed",
                previous=previous,
                current=current,
            )
        ]

    if previous != current:
        return [
            Change(
                path=path or "$",
                change_type="changed",
                previous=previous,
                current=current,
            )
        ]

    return []


def extract_previous_snapshot(document: Any) -> str | None:
    if not isinstance(document, dict):
        return None

    snapshot = document.get("snapshot")

    if isinstance(snapshot, dict):
        value = snapshot.get("previous_snapshot")

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def build_comparison(
    previous_path: Path,
    current_path: Path,
) -> dict[str, Any]:
    previous = load_document(previous_path)
    current = load_document(current_path)
    changes = compare_values(previous, current)
    counts: dict[str, int] = {}

    for change in changes:
        counts[change.change_type] = counts.get(change.change_type, 0) + 1

    expected_previous = extract_previous_snapshot(current)
    previous_link_matches = (
        expected_previous is None
        or expected_previous == str(previous_path)
        or expected_previous == previous_path.as_posix()
    )

    return {
        "schema_version": ("repository_snapshot_comparison_v0_1"),
        "metadata": {
            "previous": str(previous_path),
            "current": str(current_path),
            "changed": bool(changes),
            "change_count": len(changes),
            "change_type_counts": dict(sorted(counts.items())),
            "current_previous_snapshot": expected_previous,
            "previous_snapshot_link_matches": (previous_link_matches),
        },
        "changes": [change.as_dict() for change in changes],
    }


def render_markdown(comparison: dict[str, Any]) -> str:
    metadata = comparison["metadata"]
    lines = [
        "# Repository Snapshot Comparison",
        "",
        f"- Previous: `{metadata['previous']}`",
        f"- Current: `{metadata['current']}`",
        f"- Changed: `{metadata['changed']}`",
        f"- Change count: `{metadata['change_count']}`",
        (f"- Previous-snapshot link matches: `{metadata['previous_snapshot_link_matches']}`"),
        "",
        "## Changes",
        "",
    ]

    changes = comparison["changes"]

    if not changes:
        lines.append("No changes.")
    else:
        for item in changes:
            lines.append(f"- `{item['change_type']}` at `{item['path']}`")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Compare two YAML or JSON repository-knowledge snapshots.")
    )
    parser.add_argument("--previous", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument(
        "--format",
        choices=("yaml", "json", "markdown"),
        default="yaml",
    )
    parser.add_argument("--output")
    parser.add_argument(
        "--require-previous-link",
        action="store_true",
        help=(
            "Fail when current.snapshot.previous_snapshot does not "
            "reference the supplied previous path."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    previous_path = Path(args.previous)
    current_path = Path(args.current)

    if not previous_path.is_file():
        raise SystemExit(f"Previous snapshot does not exist: {previous_path}")

    if not current_path.is_file():
        raise SystemExit(f"Current snapshot does not exist: {current_path}")

    comparison = build_comparison(
        previous_path,
        current_path,
    )

    if args.require_previous_link and not comparison["metadata"]["previous_snapshot_link_matches"]:
        raise SystemExit(
            "Current snapshot previous_snapshot link does not match the supplied previous snapshot."
        )

    if args.format == "json":
        rendered = (
            json.dumps(
                comparison,
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
    elif args.format == "markdown":
        rendered = render_markdown(comparison)
    else:
        rendered = yaml.safe_dump(
            comparison,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        )

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
