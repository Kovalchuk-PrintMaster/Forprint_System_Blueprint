#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import yaml

MODULE_ID = "forprint_system_blueprint"
CURRENT_ID = "blueprint_inventory_acceptance_dry_run_v0_1"
NEXT_ID = "blueprint_inventory_acceptance_packet_integrity_gate_v0_1"
RCI_SECTION = "semantic_enrichment_v0_1"
REDM_SECTION = "dependency_enrichment_v0_1"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapping_by_id(
    values: Any,
    key: str,
) -> dict[str, dict[str, Any]]:
    if not isinstance(values, list):
        return {}

    return {
        str(item.get(key)): item
        for item in values
        if isinstance(item, dict) and isinstance(item.get(key), str)
    }


def coordination_alignment(
    plan: dict[str, Any],
    roadmap: dict[str, Any],
    queue: dict[str, Any],
) -> dict[str, Any]:
    reasons: list[str] = []

    plan_metadata = plan.get("metadata", {})
    roadmap_metadata = roadmap.get("metadata", {})
    queue_metadata = queue.get("metadata", {})

    plan_current = plan_metadata.get("current_step_id") if isinstance(plan_metadata, dict) else None
    roadmap_current = (
        roadmap_metadata.get("current_step_id") if isinstance(roadmap_metadata, dict) else None
    )
    queue_current = (
        queue_metadata.get("active_prompt_id") if isinstance(queue_metadata, dict) else None
    )

    if not (plan_current == roadmap_current == queue_current):
        reasons.append("current step/prompt IDs are not aligned")

    if plan_current == CURRENT_ID:
        phase = "PRE_TRANSITION"
    elif plan_current == NEXT_ID:
        phase = "POST_TRANSITION"
    else:
        phase = "INVALID"
        reasons.append("current coordination ID is outside the dry-run transition")

    plan_steps = mapping_by_id(
        plan.get("steps"),
        "step_id",
    )
    roadmap_steps = mapping_by_id(
        roadmap.get("steps"),
        "step_id",
    )
    queue_prompts = mapping_by_id(
        queue.get("prompts"),
        "prompt_id",
    )

    for label, mapping in (
        ("inventory plan", plan_steps),
        ("self-roadmap", roadmap_steps),
    ):
        if CURRENT_ID not in mapping:
            reasons.append(f"{label} lacks the dry-run step")

        if NEXT_ID not in mapping:
            reasons.append(f"{label} lacks the packet-integrity step")

    if CURRENT_ID not in queue_prompts:
        reasons.append("prompt queue lacks the dry-run prompt")

    if phase == "POST_TRANSITION" and NEXT_ID not in queue_prompts:
        reasons.append("post-transition prompt queue lacks the packet-integrity prompt")

    return {
        "passed": not reasons,
        "phase": phase,
        "reasons": reasons,
        "plan_current": plan_current,
        "roadmap_current": roadmap_current,
        "queue_current": queue_current,
        "next_prompt_required": (phase == "POST_TRANSITION"),
        "next_prompt_present": (NEXT_ID in queue_prompts),
    }


def scenario(
    scenario_id: str,
    passed: bool,
    evidence: str,
    decision: str,
) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "status": "PASSED" if passed else "FAILED",
        "evidence": evidence,
        "decision": decision,
    }


def run_dry_run(
    *,
    index_path: Path,
    index_validation_path: Path,
    rci_path: Path,
    redm_path: Path,
    closure_path: Path,
    reconciliation_path: Path,
    authority_policy_path: Path,
    plan_path: Path,
    roadmap_path: Path,
    queue_path: Path,
    module_id: str,
) -> dict[str, Any]:
    errors: list[str] = []
    scenarios: list[dict[str, Any]] = []

    if module_id != MODULE_ID:
        errors.append(f"module mismatch: expected {MODULE_ID}, found {module_id}")

    index = load_yaml(index_path)
    index_validation = load_yaml(index_validation_path)
    rci = load_yaml(rci_path)
    redm = load_yaml(redm_path)
    closure = load_yaml(closure_path)
    reconciliation = load_yaml(reconciliation_path)
    authority_policy = load_yaml(authority_policy_path)
    plan = load_yaml(plan_path)
    roadmap = load_yaml(roadmap_path)
    queue = load_yaml(queue_path)

    index_metadata = index.get("metadata", {})
    index_summary = index.get("summary", {})
    index_deferrals = index.get("explicit_deferrals", [])

    index_green = (
        isinstance(index_metadata, dict)
        and isinstance(index_summary, dict)
        and index_validation.get("metadata", {}).get("result") == "PASSED"
        and index_validation.get("summary", {}).get("release_decision")
        == "PROCEED_TO_INVENTORY_ACCEPTANCE_DRY_RUN"
        and index_metadata.get("state") == "READY_FOR_DRY_RUN"
    )

    if not index_green:
        errors.append("acceptance evidence index is not dry-run ready")

    scenarios.append(
        scenario(
            "evidence_index_integrity",
            index_green,
            str(index_validation_path),
            (
                "Evidence index is complete and released."
                if index_green
                else "Evidence index blocks the dry run."
            ),
        )
    )

    rci_section = rci.get(RCI_SECTION)
    redm_section = redm.get(REDM_SECTION)
    candidates_green = (
        isinstance(rci_section, dict)
        and rci_section.get("status") == "CANDIDATE"
        and isinstance(redm_section, dict)
        and redm_section.get("status") == "CANDIDATE"
    )

    if not candidates_green:
        errors.append("RCI/REDM candidate authority is invalid")

    scenarios.append(
        scenario(
            "candidate_authority_preservation",
            candidates_green,
            f"{rci_path}; {redm_path}",
            (
                "Both candidates remain non-accepted."
                if candidates_green
                else "Candidate authority blocks simulation."
            ),
        )
    )

    closure_green = (
        closure.get("metadata", {}).get("result") == "PASSED"
        and closure.get("summary", {}).get("closure_state") == "GREEN_WITH_EXPLICIT_DEFERRALS"
    )
    reconciliation_green = (
        reconciliation.get("metadata", {}).get("result") == "PASSED"
        and reconciliation.get("summary", {}).get("candidate_acceptance_performed") is False
    )

    if not closure_green:
        errors.append("semantic closure is not releasable")

    if not reconciliation_green:
        errors.append("repository reconciliation is not releasable")

    scenarios.append(
        scenario(
            "closure_and_reconciliation",
            closure_green and reconciliation_green,
            f"{closure_path}; {reconciliation_path}",
            (
                "Closure and reconciliation release simulation."
                if closure_green and reconciliation_green
                else "Closure or reconciliation blocks simulation."
            ),
        )
    )

    visible_deferrals = {
        str(item.get("deferral_id")): item
        for item in index_deferrals
        if isinstance(item, dict) and item.get("must_remain_visible") is True
    }
    deferrals_green = (
        visible_deferrals.get(
            "unreviewed_repository_scope",
            {},
        ).get("count")
        == 646
        and visible_deferrals.get(
            "wave_2_unknown_records",
            {},
        ).get("count")
        == 25
    )

    if not deferrals_green:
        errors.append("explicit semantic deferrals are not preserved")

    scenarios.append(
        scenario(
            "explicit_deferral_preservation",
            deferrals_green,
            str(index_path),
            (
                "646 unreviewed files and 25 unknown records stay visible."
                if deferrals_green
                else "Hidden deferrals block acceptance simulation."
            ),
        )
    )

    coordination = coordination_alignment(
        plan,
        roadmap,
        queue,
    )
    coordination_green = bool(coordination.get("passed"))

    if not coordination_green:
        errors.append(
            "coordination transition is not aligned: "
            + "; ".join(
                str(reason)
                for reason in coordination.get(
                    "reasons",
                    [],
                )
            )
        )

    scenarios.append(
        scenario(
            "coordination_transition_alignment",
            coordination_green,
            f"{plan_path}; {roadmap_path}; {queue_path}",
            (
                f"Coordination state is aligned for {coordination.get('phase')}."
                if coordination_green
                else "Coordination state blocks the dry run."
            ),
        )
    )

    integrity_policy = index.get("integrity_policy", {})
    authority_green = (
        bool(authority_policy)
        and isinstance(integrity_policy, dict)
        and integrity_policy.get("candidate_acceptance_allowed") is False
        and isinstance(index_summary, dict)
        and index_summary.get("candidate_acceptance_performed") is False
    )

    if not authority_green:
        errors.append("authority or non-acceptance policy blocks simulation")

    scenarios.append(
        scenario(
            "authority_and_non_mutation_policy",
            authority_green,
            f"{authority_policy_path}; {index_path}",
            (
                "Authority permits simulation only."
                if authority_green
                else "Authority policy blocks simulation."
            ),
        )
    )

    action_names = [
        "freeze_candidate_hashes",
        "validate_acceptance_evidence_packet",
        "prepare_candidate_to_accepted_lineage",
        "prepare_authority_transition",
        "prepare_snapshot_gate_update",
        "prepare_post_acceptance_check",
        "prepare_merge_commit",
    ]
    simulated_actions = [
        {
            "sequence": position,
            "action": action,
            "status": "SIMULATED",
            "effect_applied": False,
        }
        for position, action in enumerate(
            action_names,
            start=1,
        )
    ]
    non_mutating = all(item["effect_applied"] is False for item in simulated_actions)

    if not non_mutating:
        errors.append("dry-run effects were applied")

    scenarios.append(
        scenario(
            "non_mutating_acceptance_simulation",
            non_mutating,
            "simulated_actions",
            (
                "All acceptance operations remain simulated."
                if non_mutating
                else "Dry run mutated repository state."
            ),
        )
    )

    passed = not errors

    return {
        "schema_version": ("inventory_acceptance_dry_run_report_v0_1"),
        "metadata": {
            "result": "PASSED" if passed else "FAILED",
            "module_id": module_id,
            "external_rollout_state": "gated",
        },
        "summary": {
            "error_count": len(errors),
            "scenario_count": len(scenarios),
            "passed_scenario_count": sum(item["status"] == "PASSED" for item in scenarios),
            "failed_scenario_count": sum(item["status"] == "FAILED" for item in scenarios),
            "simulated_action_count": len(simulated_actions),
            "coordination_phase": coordination.get("phase"),
            "next_prompt_required": coordination.get("next_prompt_required"),
            "next_prompt_present": coordination.get("next_prompt_present"),
            "candidate_acceptance_performed": False,
            "candidate_files_modified": False,
            "git_merge_performed": False,
            "dry_run_effects_applied": False,
            "unreviewed_files": 646,
            "wave_2_records_with_unknowns": 25,
            "release_decision": (
                "PROCEED_TO_INVENTORY_ACCEPTANCE_PACKET_INTEGRITY_GATE"
                if passed
                else ("BLOCK_INVENTORY_ACCEPTANCE_PACKET_INTEGRITY_GATE")
            ),
        },
        "candidate_hashes": {
            "rci_v0_4": sha256(rci_path),
            "redm_v0_4": sha256(redm_path),
        },
        "scenarios": scenarios,
        "simulated_actions": simulated_actions,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True)
    parser.add_argument("--index-validation", required=True)
    parser.add_argument("--rci", required=True)
    parser.add_argument("--redm", required=True)
    parser.add_argument("--closure", required=True)
    parser.add_argument("--reconciliation", required=True)
    parser.add_argument("--authority-policy", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--roadmap", required=True)
    parser.add_argument("--queue", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_dry_run(
        index_path=Path(args.index),
        index_validation_path=Path(args.index_validation),
        rci_path=Path(args.rci),
        redm_path=Path(args.redm),
        closure_path=Path(args.closure),
        reconciliation_path=Path(args.reconciliation),
        authority_policy_path=Path(args.authority_policy),
        plan_path=Path(args.plan),
        roadmap_path=Path(args.roadmap),
        queue_path=Path(args.queue),
        module_id=args.module,
    )
    Path(args.output).write_text(
        yaml.safe_dump(
            report,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )
    return 0 if report["metadata"]["result"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
