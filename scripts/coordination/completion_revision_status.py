#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


class RevisionRegistryError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RevisionRegistryError(f"missing revision registry: {path}") from error
    except yaml.YAMLError as error:
        raise RevisionRegistryError(f"invalid YAML in {path}: {error}") from error
    if not isinstance(value, dict):
        raise RevisionRegistryError(f"YAML root must be a mapping: {path}")
    return value


def validate_registry(root: Path) -> dict[str, Any]:
    current_path = root / "coordination/revisions/current.yaml"
    history_path = root / "coordination/revisions/history.yaml"
    current = load_yaml(current_path)
    history = load_yaml(history_path)

    if current.get("schema_version") != "completion_exchange_revision_registry_v0_1":
        raise RevisionRegistryError("unexpected current revision registry schema")
    if history.get("schema_version") != "completion_exchange_revision_history_v0_1":
        raise RevisionRegistryError("unexpected revision history schema")

    operational = current.get("operational_current")
    candidate = current.get("candidate_next")
    if not isinstance(operational, dict) or not isinstance(candidate, dict):
        raise RevisionRegistryError("operational_current and candidate_next must be mappings")

    if operational.get("completion_packet") != "module_completion_packet_v0_2":
        raise RevisionRegistryError("v0.2 must remain operational during reference validation")
    if operational.get("completion_intake") != "blueprint_completion_intake_v0_2":
        raise RevisionRegistryError("unexpected operational intake revision")
    if operational.get("normal_acceptance_allowed") is not True:
        raise RevisionRegistryError("operational current must remain explicitly acceptance-capable")

    if candidate.get("prompt_contract") != "module_prompt_contract_v0_3":
        raise RevisionRegistryError("unexpected v0.3 prompt contract")
    if candidate.get("completion_packet") != "module_completion_packet_v0_3":
        raise RevisionRegistryError("unexpected v0.3 completion packet")
    if candidate.get("completion_intake") != "blueprint_completion_intake_v0_3":
        raise RevisionRegistryError("unexpected v0.3 intake protocol")
    if candidate.get("activation_state") != "reference_validation":
        raise RevisionRegistryError("v0.3 candidate must remain in reference validation")
    if candidate.get("normal_acceptance_allowed") is not False:
        raise RevisionRegistryError("candidate revision must not enter normal acceptance")

    revisions = history.get("revisions")
    if not isinstance(revisions, list):
        raise RevisionRegistryError("history revisions must be a list")
    by_revision = {item.get("revision"): item for item in revisions if isinstance(item, dict)}
    for required in ("v0_1", "v0_2", "v0_3"):
        if required not in by_revision:
            raise RevisionRegistryError(f"revision history missing {required}")

    if by_revision["v0_3"].get("status") != "candidate_reference_validation":
        raise RevisionRegistryError("history must classify v0.3 as candidate")

    return {
        "operational_current": operational,
        "candidate_next": candidate,
        "history": by_revision,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and report ForPrint completion exchange revision state."
    )
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--output-format",
        choices=("text", "json", "yaml"),
        default="text",
    )
    args = parser.parse_args()

    try:
        result = validate_registry(Path(args.root).resolve())
    except RevisionRegistryError as error:
        print(f"FAILED: {error}")
        print("RESULT: COMPLETION_REVISION_REGISTRY_INVALID")
        return 1

    payload = {
        "result": "passed",
        "operational_current": result["operational_current"],
        "candidate_next": result["candidate_next"],
    }
    if args.output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif args.output_format == "yaml":
        print(yaml.safe_dump(payload, sort_keys=False), end="")
    else:
        operational = result["operational_current"]
        candidate = result["candidate_next"]
        print("Completion exchange revision status")
        print(f"operational packet: {operational['completion_packet']}")
        print(f"operational intake: {operational['completion_intake']}")
        print(f"candidate prompt contract: {candidate['prompt_contract']}")
        print(f"candidate packet: {candidate['completion_packet']}")
        print(f"candidate intake: {candidate['completion_intake']}")
        print(f"candidate activation: {candidate['activation_state']}")
        print("candidate normal acceptance: False")
        print("RESULT: COMPLETION_REVISION_REGISTRY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
