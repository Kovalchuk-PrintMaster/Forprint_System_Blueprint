#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "module_cleanliness_conformance_pack_v0_1.yaml"
)
PORTFOLIO = (
    ROOT
    / "coordination/internal_work/blueprint/cleanliness/"
    "module_cleanliness_conformance_portfolio_v0_1.yaml"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("module_id")
    args = parser.parse_args()

    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    portfolio = yaml.safe_load(PORTFOLIO.read_text(encoding="utf-8"))

    known = {
        item["module_id"]
        for item in portfolio.get("modules", [])
    }
    if args.module_id not in known:
        raise SystemExit("unknown canonical module_id: " + args.module_id)

    components = [
        {
            "component_id": item["component_id"],
            "status": "PROPOSED_NOT_IMPLEMENTED",
            "evidence": [],
        }
        for item in policy["required_components"]
    ]

    starter = {
        "schema_version": "0.1",
        "module_id": args.module_id,
        "status": "PROPOSED_NOT_IMPLEMENTED",
        "standard_reference": (
            "coordination/standards/governance/"
            "module_cleanliness_conformance_pack_v0_1.yaml"
        ),
        "owner": args.module_id,
        "normal_check_command": "TO_BE_DEFINED_IN_MODULE",
        "components": components,
        "known_debt": [],
        "retirement_registry": "TO_BE_DEFINED_IN_MODULE",
        "evidence": [],
        "last_verified": None,
        "assistant_distribution_allowed": False,
        "module_implementation_started": False,
    }

    print(
        yaml.safe_dump(
            starter,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=120,
        ),
        end="",
    )


if __name__ == "__main__":
    main()
