from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PULSE = ROOT / "scripts/coordination/coordination_pulse.py"
POLICY = ROOT / "coordination/standards/governance/coordination_health_policy_v0_1.yaml"
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
QUEUE = ROOT / "coordination/self_coordination/prompt_queue/index.yaml"
HANDOFF = ROOT / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
IMPLEMENTATION = (
    ROOT / "coordination/internal_work/blueprint/governance/"
    "2026-08-14__blueprint__v0_4_coordination_health_and_pulse_"
    "implementation_v0_1.yaml"
)

STEP19 = "blueprint_v0_4_coordination_source_registry_v0_1"
STEP20 = "blueprint_v0_4_coordination_health_and_pulse_v0_1"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def pulse_module():
    spec = importlib.util.spec_from_file_location("coordination_pulse", PULSE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_step20_lifecycle_state_is_coherent() -> None:
    roadmap, queue = load(ROADMAP), load(QUEUE)
    step20 = next(x for x in roadmap["steps"] if x["step_id"] == STEP20)
    prompt20 = next(x for x in queue["prompts"] if x["prompt_id"] == STEP20)

    if step20["status"] == "active":
        assert roadmap["metadata"]["current_step_id"] == STEP20
        assert queue["metadata"]["active_prompt_id"] == STEP20
        assert prompt20["status"] == "approved"
        assert prompt20["execution_status"] == "ready_for_module_pull"
    else:
        assert step20["status"] == "completed"
        assert step20["operator_decision"] == "ACCEPT"
        assert prompt20["status"] == "completed"
        assert prompt20["execution_status"] == "accepted"


def test_current_roadmap_metadata_is_self_consistent() -> None:
    roadmap, queue = load(ROADMAP), load(QUEUE)
    current_id = roadmap["metadata"]["current_step_id"]
    current = next(x for x in roadmap["steps"] if x["step_id"] == current_id)
    future = [
        x
        for x in roadmap["steps"]
        if x["sequence"] > current["sequence"] and x["status"] in {"active", "planned", "ready"}
    ]

    assert roadmap["metadata"]["actionable_steps_after_current"] == len(future)
    assert roadmap["metadata"]["v0_4_workstream"]["current_phase"] == current_id
    assert queue["metadata"]["active_prompt_id"] == current_id

    roadmap_accept = roadmap["metadata"]["last_operator_acceptance"]
    queue_accept = queue["metadata"]["last_operator_acceptance"]
    assert roadmap_accept["decision"] == "ACCEPT"
    assert queue_accept["decision"] == "ACCEPT"
    assert queue_accept["prompt_id"] == roadmap_accept["prompt_id"]
    assert queue_accept["evidence"] == roadmap_accept["evidence"]


def test_current_pulse_is_healthy_and_policy_driven() -> None:
    module = pulse_module()
    data = module.evaluate(ROOT)
    policy = load(POLICY)

    assert data["schema_version"] == "coordination_pulse_v0_1"
    assert data["mode"] == "local_read_only"
    assert data["network_independent"] is True
    assert data["overall_state"] == "healthy"

    roadmap = load(ROADMAP)
    current_id = roadmap["metadata"]["current_step_id"]
    current = next(x for x in roadmap["steps"] if x["step_id"] == current_id)
    expected_future = sum(
        1
        for x in roadmap["steps"]
        if x["sequence"] > current["sequence"] and x["status"] in {"active", "planned", "ready"}
    )

    assert data["roadmap"]["current_step_id"] == current_id
    assert data["roadmap"]["future_steps"] == expected_future
    assert data["roadmap"]["minimum_future_steps"] == policy["roadmap"]["minimum_future_steps"]
    assert data["roadmap"]["target_future_steps"] == policy["roadmap"]["target_future_steps"]

    queue = load(QUEUE)
    prompts = [x for x in queue["prompts"] if isinstance(x, dict)]
    indexed_drafts = [x for x in prompts if x.get("status") == "draft"]
    dispatchable = [
        x
        for x in indexed_drafts
        if x.get("dispatch_ready") is True and x.get("execution_status") != "deferred"
    ]

    assert data["prompt_queue"]["active_prompt_count"] == sum(
        1 for x in prompts if x.get("status") == "approved"
    )
    assert data["prompt_queue"]["physical_draft_files"] == len(
        list((ROOT / "coordination/self_coordination/prompt_queue/draft").glob("*.md"))
    )
    assert data["prompt_queue"]["dispatchable_drafts"] == len(dispatchable)

    assert data["completions"]["pending_completions"] is None
    assert data["completions"]["state"] == "not_available_yet"
    assert data["completions"]["outbox_present_sources"] == 0
    assert data["completions"]["outbox_not_present_yet_sources"] == 8

    assert data["queue_roadmap_drift"]["count"] == 0
    assert data["codes"] == {
        "errors": [],
        "warnings": [],
        "advisories": [],
    }


def test_stable_warning_and_error_codes_are_policy_classified() -> None:
    module = pulse_module()

    assert module.roadmap_health(4, 5, 8) == (
        "below_minimum",
        ["ROADMAP_HORIZON_BELOW_MINIMUM"],
    )
    assert module.roadmap_health(6, 5, 8) == (
        "minimum_met_target_not_met",
        ["ROADMAP_HORIZON_BELOW_TARGET"],
    )
    assert module.prompt_buffer_health(1, 2, 3) == (
        "below_minimum",
        ["PROMPT_BUFFER_BELOW_MINIMUM"],
    )
    assert module.prompt_buffer_health(2, 2, 3) == (
        "minimum_met_target_not_met",
        ["PROMPT_BUFFER_BELOW_TARGET"],
    )
    assert module.active_prompt_health(0, 1) == (
        "missing",
        ["ACTIVE_PROMPT_MISSING"],
    )
    assert module.active_prompt_health(2, 1) == (
        "multiple",
        ["MULTIPLE_ACTIVE_PROMPTS"],
    )


def test_local_pulse_implementation_has_no_network_dependency() -> None:
    text = PULSE.read_text(encoding="utf-8")
    forbidden = ("requests", "urllib", "socket", "http://", "https://")
    assert not any(token in text for token in forbidden)


def test_make_coordination_pulse_renders_read_only_health_view() -> None:
    cp = subprocess.run(
        ["make", "-s", "coordination-pulse"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout + cp.stderr
    assert "ForPrint Coordination Pulse v0.1" in cp.stdout
    assert "overall: healthy" in cp.stdout
    assert "future:" in cp.stdout
    assert "(minimum=5, target=8)" in cp.stdout
    assert "dispatchable_drafts:" in cp.stdout
    assert "pending_completions: unknown" in cp.stdout
    assert "QUEUE<->ROADMAP DRIFT" in cp.stdout
    assert "errors: -" in cp.stdout


def test_handoff_surfaces_dynamic_pulse_without_making_it_source_of_truth() -> None:
    handoff = load(HANDOFF)
    roadmap = load(ROADMAP)
    pulse = handoff["coordination_pulse"]
    step20 = next(x for x in roadmap["steps"] if x["step_id"] == STEP20)

    assert pulse["command"] == "make coordination-pulse"
    assert pulse["script"] == "scripts/coordination/coordination_pulse.py"
    assert pulse["policy"] == (
        "coordination/standards/governance/coordination_health_policy_v0_1.yaml"
    )
    assert pulse["mode"] == "local_read_only"
    assert pulse["network_independent"] is True
    assert pulse["generated_pulse_artifact_is_source_of_truth"] is False

    if step20["status"] == "active":
        assert pulse["operator_decision_created"] is False
    else:
        assert step20["status"] == "completed"
        assert step20["operator_decision"] == "ACCEPT"
        assert pulse["operator_decision_created"] is True
        assert pulse["operator_decision"] == "ACCEPT"
        assert pulse["policy_status"] == "candidate_v0_4"
        assert pulse["policy_promotion_performed"] is False


def test_policy_lifecycle_matches_step20_operator_state() -> None:
    policy = load(POLICY)
    roadmap = load(ROADMAP)
    step20 = next(x for x in roadmap["steps"] if x["step_id"] == STEP20)

    if step20["status"] == "active":
        assert policy["metadata"]["status"] == "candidate_v0_4"
    else:
        assert step20["status"] == "completed"
        assert step20["operator_decision"] == "ACCEPT"
        assert policy["metadata"]["status"] in {
            "candidate_v0_4",
            "accepted_v0_4",
            "active_standard",
        }


def test_implementation_evidence_is_review_ready_without_acceptance() -> None:
    evidence = load(IMPLEMENTATION)
    assert evidence["result"] in {
        "IMPLEMENTATION_IN_PROGRESS",
        "READY_FOR_OPERATOR_REVIEW",
    }
    assert evidence["validation"]["state"] in {"pending", "passed"}
    assert evidence["work"]["roadmap_step_id"] == STEP20
    assert evidence["work"]["operator_decision_created"] is False
    assert evidence["boundaries"]["active_step_advanced"] is False
    assert evidence["boundaries"]["automatic_acceptance"] is False
    assert evidence["boundaries"]["automatic_commit"] is False
    assert evidence["boundaries"]["automatic_push"] is False
