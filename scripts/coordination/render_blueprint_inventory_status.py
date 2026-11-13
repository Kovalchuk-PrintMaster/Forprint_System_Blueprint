#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BLUE = "\033[34m"
RED = "\033[31m"
DIM = "\033[2m"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
SUPPORTED_MODULE = "forprint_system_blueprint"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def first_int(
    mapping: dict[str, Any],
    keys: tuple[str, ...],
    *,
    default: int = 0,
) -> int:
    for key in keys:
        value = mapping.get(key)

        if isinstance(value, bool):
            continue

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value)

        if isinstance(value, str) and value.isdigit():
            return int(value)

    return default


def find_mapping(node: Any, key: str) -> dict[str, Any]:
    if isinstance(node, dict):
        value = node.get(key)

        if isinstance(value, dict):
            return value

        for child in node.values():
            found = find_mapping(child, key)

            if found:
                return found

    if isinstance(node, list):
        for child in node:
            found = find_mapping(child, key)

            if found:
                return found

    return {}


def find_int(node: Any, keys: tuple[str, ...]) -> int:
    if isinstance(node, dict):
        value = first_int(node, keys, default=-1)

        if value >= 0:
            return value

        for child in node.values():
            found = find_int(child, keys)

            if found >= 0:
                return found

    if isinstance(node, list):
        for child in node:
            found = find_int(child, keys)

            if found >= 0:
                return found

    return -1


def find_text(node: Any, key: str) -> str | None:
    if isinstance(node, dict):
        value = node.get(key)

        if isinstance(value, str):
            return value

        for child in node.values():
            found = find_text(child, key)

            if found is not None:
                return found

    if isinstance(node, list):
        for child in node:
            found = find_text(child, key)

            if found is not None:
                return found

    return None


def visible_length(value: str) -> int:
    return len(ANSI_RE.sub("", value))


def pad(value: str, width: int) -> str:
    return value + (" " * max(0, width - visible_length(value)))


def table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [
        max(
            visible_length(headers[index]),
            *[visible_length(row[index]) for row in rows],
        )
        for index in range(len(headers))
    ]
    top = "┌" + "┬".join("─" * (width + 2) for width in widths) + "┐"
    middle = "├" + "┼".join("─" * (width + 2) for width in widths) + "┤"
    bottom = "└" + "┴".join("─" * (width + 2) for width in widths) + "┘"
    header = (
        "│ "
        + " │ ".join(
            pad(f"{BOLD}{value}{RESET}", widths[index]) for index, value in enumerate(headers)
        )
        + " │"
    )
    body = [
        "│ " + " │ ".join(pad(value, widths[index]) for index, value in enumerate(row)) + " │"
        for row in rows
    ]
    return "\n".join([top, header, middle, *body, bottom])


def percent(done: int, total: int) -> float:
    return done / total if total else 0.0


def percent_text(done: int, total: int) -> str:
    value = percent(done, total)

    if value >= 0.8:
        color = GREEN
    elif value >= 0.5:
        color = CYAN
    else:
        color = YELLOW

    return f"{color}{value * 100:.2f}%{RESET}"


def risk_text(level: str) -> str:
    if level == "BLOCKER":
        return f"{RED}{level}{RESET}"

    if level == "HIGH":
        return f"{YELLOW}{level}{RESET}"

    return f"{CYAN}{level}{RESET}"


def build_metrics(
    wave: dict[str, Any],
    dashboard: dict[str, Any],
) -> dict[str, int]:
    combined = find_mapping(wave, "combined_lower_bounds")

    if not combined:
        raise ValueError("Wave 2 report has no combined_lower_bounds section")

    tracked = first_int(
        combined,
        (
            "tracked_files",
            "tracked_total",
            "repository_tracked_files",
        ),
    )
    reviewed = first_int(
        combined,
        (
            "wave_1_plus_wave_2_reviewed",
            "reviewed_files",
            "reviewed",
        ),
    )
    purpose = first_int(
        combined,
        (
            "purpose_evidenced",
            "purpose_understood",
        ),
    )
    dependencies = first_int(
        combined,
        (
            "dependencies_mapped",
            "dependency_evidenced",
        ),
    )
    verified = first_int(
        combined,
        (
            "fully_verified",
            "verified_files",
        ),
    )

    if not all(
        value > 0
        for value in (
            tracked,
            reviewed,
            purpose,
            dependencies,
            verified,
        )
    ):
        raise ValueError("Combined semantic inventory metrics are incomplete")

    wave_summary = find_mapping(wave, "summary")
    unknown_records = first_int(
        wave_summary,
        ("records_with_unknowns",),
        default=-1,
    )

    if unknown_records < 0:
        unknown_records = find_int(
            wave,
            ("records_with_unknowns",),
        )

    changed_paths = find_int(
        dashboard,
        (
            "changed_paths_since_rci_commit",
            "changed_paths_since_rci",
        ),
    )
    scope_delta = find_int(
        dashboard,
        (
            "artifact_map_scope_delta",
            "scope_delta",
        ),
    )

    return {
        "tracked": tracked,
        "reviewed": reviewed,
        "purpose": purpose,
        "dependencies": dependencies,
        "verified": verified,
        "unknown_records": max(0, unknown_records),
        "changed_paths": max(0, changed_paths),
        "scope_delta": max(0, scope_delta),
    }


def render_inventory_status(
    wave: dict[str, Any],
    dashboard: dict[str, Any],
    maintenance: dict[str, Any],
    roadmap: dict[str, Any],
    module: str,
) -> str:
    metrics = build_metrics(wave, dashboard)
    tracked = metrics["tracked"]
    reviewed = metrics["reviewed"]
    purpose = metrics["purpose"]
    dependencies = metrics["dependencies"]
    verified = metrics["verified"]

    repository_lower_bound = min(
        percent(reviewed, tracked),
        percent(purpose, tracked),
        percent(dependencies, tracked),
        percent(verified, tracked),
    )
    reviewed_quality_lower_bound = min(
        percent(purpose, reviewed),
        percent(dependencies, reviewed),
        percent(verified, reviewed),
    )

    if repository_lower_bound >= 0.8:
        readiness = f"{GREEN}READY FOR ACCEPTANCE REVIEW{RESET}"
    elif repository_lower_bound >= 0.5:
        readiness = f"{CYAN}PARTIAL — ENRICHMENT REQUIRED{RESET}"
    else:
        readiness = f"{RED}EARLY — NOT READY FOR ACCEPTANCE{RESET}"

    roadmap_metadata = roadmap.get("metadata")

    if not isinstance(roadmap_metadata, dict):
        raise ValueError("Roadmap metadata is missing")

    current_step = str(roadmap_metadata.get("current_step_id", "unknown"))
    rollout_state = (
        find_text(maintenance, "state")
        or find_text(maintenance, "external_rollout_state")
        or "unknown"
    )

    metric_rows = [
        [
            "Repository scope",
            "Reviewed",
            f"{reviewed}/{tracked}",
            percent_text(reviewed, tracked),
            "Files with direct semantic review evidence.",
        ],
        [
            "├─ Reviewed quality",
            "Purpose evidenced",
            f"{purpose}/{reviewed}",
            percent_text(purpose, reviewed),
            "Reviewed files whose role/purpose is explicitly supported.",
        ],
        [
            "├─ Reviewed quality",
            "Dependencies mapped",
            f"{dependencies}/{reviewed}",
            percent_text(dependencies, reviewed),
            "Reviewed files with execution/dependency relationships mapped.",
        ],
        [
            "└─ Reviewed quality",
            "Fully verified",
            f"{verified}/{reviewed}",
            percent_text(verified, reviewed),
            "Reviewed files with purpose, dependency and verification evidence.",
        ],
        [
            "Repository total",
            "Purpose evidenced",
            f"{purpose}/{tracked}",
            percent_text(purpose, tracked),
            "Repository-wide lower-bound purpose coverage.",
        ],
        [
            "Repository total",
            "Dependencies mapped",
            f"{dependencies}/{tracked}",
            percent_text(dependencies, tracked),
            "Repository-wide lower-bound dependency coverage.",
        ],
        [
            "Repository total",
            "Fully verified",
            f"{verified}/{tracked}",
            percent_text(verified, tracked),
            "Repository-wide minimum accepted semantic coverage.",
        ],
    ]

    blocker_rows = [
        [
            risk_text("BLOCKER"),
            "Unreviewed repository scope",
            str(tracked - reviewed),
            "Review or explicitly defer before full-coverage claims.",
        ],
        [
            risk_text("HIGH"),
            "Wave 2 records with unknowns",
            str(metrics["unknown_records"]),
            "Resolve, defer with rationale, or accept as known unknown.",
        ],
        [
            risk_text("HIGH"),
            "Paths changed since current RCI",
            str(metrics["changed_paths"]),
            "Reconcile before repository-knowledge acceptance.",
        ],
        [
            risk_text("HIGH"),
            "Artifact authority-map scope delta",
            str(metrics["scope_delta"]),
            "Explain tracked scope versus authority-map scope.",
        ],
    ]

    dependency_rows = [
        [
            "Reviewed",
            "Foundation",
            "Direct file review evidence.",
        ],
        [
            "Purpose evidenced",
            "Depends on Reviewed",
            "A purpose claim is valid only for reviewed files.",
        ],
        [
            "Dependencies mapped",
            "Depends on Reviewed",
            "Dependency claims require reviewed execution context.",
        ],
        [
            "Fully verified",
            "Depends on all above",
            "The strictest metric; controls the semantic lower bound.",
        ],
    ]

    lower_color = RED if repository_lower_bound < 0.5 else CYAN

    return "\n\n".join(
        [
            "\n".join(
                [
                    (f"{BOLD}{BLUE}Blueprint Inventory Status{RESET} {DIM}module={module}{RESET}"),
                    f"readiness={readiness}",
                    (
                        "repository semantic lower bound="
                        f"{lower_color}{repository_lower_bound * 100:.2f}%{RESET}"
                    ),
                    (
                        "quality inside reviewed scope="
                        f"{CYAN}{reviewed_quality_lower_bound * 100:.2f}%{RESET}"
                    ),
                    (
                        f"current={CYAN}{current_step}{RESET}  "
                        f"external rollout={YELLOW}{rollout_state}{RESET}"
                    ),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}1. Coverage and nested quality{RESET}",
                    table(
                        [
                            "Layer",
                            "Metric",
                            "Value",
                            "Coverage",
                            "What it means",
                        ],
                        metric_rows,
                    ),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}2. Metric dependencies{RESET}",
                    table(
                        ["Metric", "Depends on", "Interpretation"],
                        dependency_rows,
                    ),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}3. Current blockers and drift{RESET}",
                    table(
                        ["Risk", "Blocker", "Count", "Required action"],
                        blocker_rows,
                    ),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}4. How to read this status{RESET}",
                    (
                        f"{DIM}• Repository lower bound uses the strictest "
                        "repository-wide semantic metric."
                        f"{RESET}"
                    ),
                    (
                        f"{DIM}• Reviewed quality shows whether already-reviewed "
                        "files are documented consistently."
                        f"{RESET}"
                    ),
                    (
                        f"{DIM}• High reviewed quality does not compensate for "
                        "a large unreviewed repository scope."
                        f"{RESET}"
                    ),
                    (
                        f"{DIM}• Acceptance and external rollout remain blocked "
                        "until reconciliation gates are GREEN."
                        f"{RESET}"
                    ),
                ]
            ),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True)
    args = parser.parse_args()

    if args.module != SUPPORTED_MODULE:
        print(f"{RED}Unsupported module: {args.module}{RESET}")
        return 2

    print(
        render_inventory_status(
            load_yaml(
                Path(
                    "coordination/internal_work/blueprint/"
                    "inventory_refresh/"
                    "2026-07-29__blueprint__"
                    "semantic_inventory_wave_2_v0_1.yaml"
                )
            ),
            load_yaml(
                Path(
                    "coordination/internal_work/blueprint/"
                    "inventory_refresh/"
                    "2026-07-29__blueprint__"
                    "inventory_coverage_drift_dashboard_v0_1.yaml"
                )
            ),
            load_yaml(Path("coordination/repository_knowledge/inventory_maintenance_v0_1.yaml")),
            load_yaml(Path("coordination/self_coordination/roadmap.yaml")),
            args.module,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
