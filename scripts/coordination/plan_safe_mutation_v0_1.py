#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "safe_mutation_pipeline_v0_1.yaml"
)


def load_policy() -> dict:
    data = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("safe mutation policy must be a mapping")
    return data


def matches(path: str, pattern: str) -> bool:
    if pattern == "Makefile":
        return path == "Makefile"
    return fnmatch.fnmatch(path, pattern)


def build_plan(paths: list[str]) -> dict:
    policy = load_policy()
    source_classes = policy["source_class_registry"]
    action_registry = policy["action_registry"]

    matched_classes: list[str] = []
    requirements: list[str] = []
    action_ids: set[str] = set()

    normalized_paths = sorted({path.replace("\\", "/").lstrip("./") for path in paths})

    per_path: dict[str, list[str]] = {}
    for path in normalized_paths:
        path_classes: list[str] = []
        for class_id, spec in source_classes.items():
            patterns = spec.get("patterns", [])
            if any(matches(path, pattern) for pattern in patterns):
                path_classes.append(class_id)
                if class_id not in matched_classes:
                    matched_classes.append(class_id)
                for requirement in spec.get("requirements", []):
                    if requirement not in requirements:
                        requirements.append(requirement)
                action_ids.update(spec.get("actions", []))
        per_path[path] = path_classes

    action_ids.update(policy.get("universal_final_actions", []))
    ordered_actions = sorted(
        action_ids,
        key=lambda action_id: (
            int(action_registry[action_id]["order"]),
            action_id,
        ),
    )

    actions = [
        {
            "action_id": action_id,
            "order": int(action_registry[action_id]["order"]),
            "kind": action_registry[action_id]["kind"],
            "automatic_safe": bool(action_registry[action_id]["automatic_safe"]),
            "command": action_registry[action_id]["command"],
        }
        for action_id in ordered_actions
    ]

    return {
        "paths": normalized_paths,
        "per_path_classes": per_path,
        "matched_source_classes": matched_classes,
        "manual_requirements": requirements,
        "actions": actions,
        "assistant_distribution_allowed": False,
        "module_implementation_started": False,
        "commit_performed": False,
        "push_performed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    plan = build_plan(args.paths)

    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    print("SAFE_MUTATION_PLAN=PASS")
    print("PATH_COUNT=" + str(len(plan["paths"])))
    print(
        "SOURCE_CLASSES="
        + ",".join(plan["matched_source_classes"])
    )
    print(
        "MANUAL_REQUIREMENTS="
        + ",".join(plan["manual_requirements"])
    )
    for action in plan["actions"]:
        print(
            "ACTION="
            + action["action_id"]
            + " ORDER="
            + str(action["order"])
            + " COMMAND="
            + " ".join(action["command"])
        )


if __name__ == "__main__":
    main()
