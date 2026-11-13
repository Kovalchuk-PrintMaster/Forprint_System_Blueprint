from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import yaml

STEP29_SHA = "82308233625a348f8213d3976a60e6aa8a5db83cf3523cf334999e6e5e4727c5"


def load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: YAML root must be mapping")
    return data


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    release_path = root / "coordination/releases/current.yaml"
    if not release_path.is_file():
        return ["current release projection missing"]

    release = load(release_path)
    if release.get("metadata", {}).get("status") != "authoritative_current":
        errors.append("release projection is not authoritative_current")

    state = release.get("release", {})
    if state.get("base_release") != "v0.4":
        errors.append("base release != v0.4")
    if state.get("base_release_state") != "PROMOTED_CLOSED_SEALED":
        errors.append("base release not PROMOTED_CLOSED_SEALED")
    if state.get("hardening_release") != "v0.4.1":
        errors.append("hardening release != v0.4.1")

    decision = state.get("promotion_decision", {})
    decision_path = root / str(decision.get("path", ""))
    if not decision_path.is_file():
        errors.append("promotion decision missing")
    elif sha(decision_path) != STEP29_SHA:
        errors.append("STEP29 SHA mismatch")
    if decision.get("sha256") != STEP29_SHA:
        errors.append("release projection STEP29 SHA mismatch")

    revision = load(root / "coordination/revisions/current.yaml")
    current = revision.get("operational_current", {})
    expected = {
        "prompt_contract": "module_prompt_contract_v0_4",
        "completion_packet": "module_completion_packet_v0_4",
        "completion_outbox": "module_completion_outbox_event_v0_4",
        "discovery_intake": "completion_discovery_and_intake_v0_4",
        "review_transaction": "review_roadmap_queue_transaction_v0_4",
    }
    for key, value in expected.items():
        if current.get(key) != value:
            errors.append(f"current revision {key} != {value}")
    if current.get("normal_acceptance_allowed") is not True:
        errors.append("current v0.4 acceptance path not enabled")

    publication = {
        "coordination/standards/governance/module_prompt_contract_v0_4.yaml": (
            "candidate_reference_only"
        ),
        "coordination/standards/governance/module_completion_packet_v0_4.yaml": (
            "candidate_reference_only"
        ),
        "coordination/standards/governance/module_completion_outbox_v0_4.yaml": (
            "candidate_reference_only"
        ),
        "coordination/standards/governance/coordination_health_policy_v0_1.yaml": (
            "candidate_v0_4"
        ),
    }
    for rel, expected_status in publication.items():
        data = load(root / rel)
        if data.get("metadata", {}).get("status") != expected_status:
            errors.append(f"{rel}: historical publication status drifted")

    legacy = load(root / "coordination/legacy/compatibility_registry_v0_1.yaml")
    if legacy.get("metadata", {}).get("status") != "active_current":
        errors.append("legacy compatibility registry not active_current")
    if legacy.get("default_current_gate_behavior", {}).get("blocking") is not False:
        errors.append("legacy compatibility unexpectedly blocks current gate")

    logistics = load(root / "coordination/roadmaps/logistics_service.yaml")
    horizon = logistics.get("metadata", {}).get("planning_horizon", {})
    if horizon.get("minimum_future_steps") != 5:
        errors.append("Logistics minimum future != 5")
    if horizon.get("target_future_steps") != 8:
        errors.append("Logistics target future != 8")
    if horizon.get("maximum_future_steps") is not None:
        errors.append("Logistics future horizon unexpectedly capped")
    if horizon.get("meaningful_future_steps") != 25:
        errors.append("Logistics meaningful future != 25")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors = validate(root)

    print("ForPrint Current Coordination Release")
    print("base_release: v0.4 PROMOTED/CLOSED/SEALED")
    print("hardening_release: v0.4.1 ACTIVE_CURRENT")
    print("legacy_compatibility: advisory / nonblocking")
    print("roadmap_health: minimum=5 target=8 maximum=none")
    print("prompt_buffer: minimum=2 target=3 maximum=none")
    print("errors:", "-" if not errors else "; ".join(errors))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
