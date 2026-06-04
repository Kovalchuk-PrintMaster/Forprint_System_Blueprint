from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICY_INDEX_PATH = PROJECT_ROOT / "coordination" / "module_policy" / "module_policy_index.yaml"
POLICY_ROOT = PROJECT_ROOT / "coordination" / "module_policy"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def render_list(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- `{item}`" for item in items)


def render_policy(module: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Module Policy — {module['module_name']}",
            "",
            "## Module ID",
            "",
            "```text",
            module["module_id"],
            "```",
            "",
            "## Priority",
            "",
            "```text",
            module["priority"],
            "```",
            "",
            "## Development status",
            "",
            "```text",
            module["development_status"],
            "```",
            "",
            "## Strategic role",
            "",
            module["strategic_role"].strip(),
            "",
            "## Main goals",
            "",
            render_list(module.get("main_goals", [])),
            "",
            "## Owns",
            "",
            render_list(module.get("owns", [])),
            "",
            "## Must not own",
            "",
            render_list(module.get("must_not_own", [])),
            "",
            "## Next focus",
            "",
            render_list(module.get("next_focus", [])),
            "",
            "## Adoption rule",
            "",
            (
                "This module policy is strategic guidance. It does not automatically "
                "authorize large refactors or broad rewrites. The module should compare "
                "this policy with its current implementation and report alignment, "
                "conflicts or questions to Blueprint."
            ),
            "",
        ]
    )


def generate_docs(policy_index_path: Path = POLICY_INDEX_PATH) -> list[Path]:
    data = load_yaml(policy_index_path)
    modules = data["module_policy_index"]["modules"]

    written: list[Path] = []

    for module in modules:
        module_dir = POLICY_ROOT / module["module_id"]
        module_dir.mkdir(parents=True, exist_ok=True)

        target = module_dir / "module_policy.md"
        target.write_text(render_policy(module), encoding="utf-8")
        written.append(target)

    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate human-readable module policy docs from module_policy_index.yaml."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check whether generated files are up to date without writing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.check:
        written = generate_docs()
        print("Generated module policy docs:")
        for path in written:
            print(f"  - {path.relative_to(PROJECT_ROOT)}")
        return 0

    data = load_yaml(POLICY_INDEX_PATH)
    modules = data["module_policy_index"]["modules"]

    outdated: list[Path] = []

    for module in modules:
        target = POLICY_ROOT / module["module_id"] / "module_policy.md"
        expected = render_policy(module)
        if not target.exists() or target.read_text(encoding="utf-8") != expected:
            outdated.append(target)

    if outdated:
        print("Outdated module policy docs:")
        for path in outdated:
            print(f"  - {path.relative_to(PROJECT_ROOT)}")
        return 1

    print("✅ Module policy docs are up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
