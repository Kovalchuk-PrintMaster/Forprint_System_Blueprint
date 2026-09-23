#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "module_current_state_evidence_standard_v0_1.yaml"
)
PORTFOLIO = (
    ROOT
    / "coordination/internal_work/blueprint/module_inventory/"
    "module_current_state_evidence_portfolio_v0_1.yaml"
)

SEARCH_ROOTS = (
    ROOT / "coordination/roadmaps/details/forprint_system_blueprint",
    ROOT / "coordination/human_intent",
    ROOT / "machine",
)
TEXT_SUFFIXES = {".yaml", ".yml", ".md", ".json"}


def exact_blueprint_references(module_id: str, limit: int = 30) -> list[str]:
    references: list[str] = []
    needle = module_id.encode("utf-8")
    for search_root in SEARCH_ROOTS:
        if not search_root.exists():
            continue
        for path in sorted(search_root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                payload = path.read_bytes()
            except OSError:
                continue
            if needle in payload:
                references.append(path.relative_to(ROOT).as_posix())
                if len(references) >= limit:
                    return references
    return references


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("module_id")
    args = parser.parse_args()

    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    portfolio = yaml.safe_load(PORTFOLIO.read_text(encoding="utf-8"))
    modules = {
        item["module_id"]: item
        for item in portfolio["modules"]
    }
    if args.module_id not in modules:
        raise SystemExit("unknown canonical module_id: " + args.module_id)

    portfolio_item = modules[args.module_id]
    is_blueprint = args.module_id == "forprint_system_blueprint"
    default_state = (
        "CURRENT_CONFIRMED"
        if is_blueprint
        else "CURRENT_BLUEPRINT_DOCUMENTED_NOT_REPO_VERIFIED"
    )
    default_level = (
        "VERIFIED_LOCAL_REPOSITORY"
        if is_blueprint
        else "BLUEPRINT_CANONICAL_DOCUMENTATION"
    )

    sections = {}
    for section_id in policy["required_profile_sections"]:
        sections[section_id] = {
            "state": default_state,
            "evidence_level": default_level,
            "value": None,
            "evidence": [],
        }

    sections["last_verified"]["value"] = portfolio_item["last_verified"]
    sections["canonical_paths"]["value"] = exact_blueprint_references(
        args.module_id
    )
    sections["canonical_paths"]["evidence"] = [
        "exact module_id textual reference scan in canonical Blueprint roots"
    ]

    profile = {
        "schema_version": "0.1",
        "module_id": args.module_id,
        "profile_status": portfolio_item["profile_status"],
        "repository_evidence_verified": portfolio_item[
            "repository_evidence_verified"
        ],
        "runtime_evidence_verified": False,
        "standard_reference": (
            "coordination/standards/governance/"
            "module_current_state_evidence_standard_v0_1.yaml"
        ),
        "sections": sections,
        "assistant_distribution_allowed": False,
        "module_implementation_started": False,
        "cross_repo_diagnostics_started": False,
    }

    print(
        yaml.safe_dump(
            profile,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=120,
        ),
        end="",
    )


if __name__ == "__main__":
    main()
