from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOL = (
    ROOT
    / "scripts/coordination/next_prompt_selection_activation_v0_4.py"
)
HANDOFF = (
    ROOT
    / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
)
BOOTSTRAP = (
    ROOT
    / "coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_1.yaml"
)
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
QUEUE = ROOT / "coordination/self_coordination/prompt_queue/index.yaml"

STEP25 = "blueprint_v0_4_review_roadmap_queue_transaction_v0_1"
STEP26 = "blueprint_v0_4_next_prompt_selection_and_activation_v0_1"
STEP27 = "blueprint_v0_4_tracking_events_reference_v0_1"
STEP28 = "blueprint_v0_4_manual_dark_zone_audit_v0_1"


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def tool_module():
    spec = importlib.util.spec_from_file_location(
        "next_prompt_selection_activation_v04",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_state(tmp_path: Path) -> dict[str, Path]:
    root = tmp_path / "blueprint"
    roadmap = root / "coordination/self_coordination/roadmap.yaml"
    queue = (
        root
        / "coordination/self_coordination/prompt_queue/index.yaml"
    )
    handoff = (
        root
        / "coordination/instruction_intake/bootstrap/"
        "current_handoff_v0_1.yaml"
    )
    policy = (
        root
        / "coordination/standards/governance/"
        "coordination_health_policy_v0_1.yaml"
    )
    draft_dir = (
        root
        / "coordination/self_coordination/prompt_queue/draft"
    )
    p2 = draft_dir / "p2.md"
    p3 = draft_dir / "p3.md"

    write_yaml(
        roadmap,
        {
            "schema_version": "demo_roadmap_v0_1",
            "metadata": {"current_step_id": "s1"},
            "steps": [
                {
                    "step_id": "s1",
                    "sequence": 1,
                    "status": "completed",
                    "operator_decision": "ACCEPT",
                    "depends_on": [],
                },
                {
                    "step_id": "s2",
                    "sequence": 2,
                    "status": "planned",
                    "depends_on": ["s1"],
                    "priority": "critical",
                },
                {
                    "step_id": "s3",
                    "sequence": 3,
                    "status": "planned",
                    "depends_on": ["s1"],
                    "priority": "high",
                },
            ],
        },
    )
    write_yaml(
        queue,
        {
            "schema_version": "demo_prompt_queue_v0_1",
            "metadata": {
                "active_prompt_id": None,
                "approved_prompt_count": 0,
                "draft_prompt_count": 2,
                "completed_prompt_count": 0,
                "dispatchable_draft_count": 2,
                "deferred_prompt_count": 0,
            },
            "prompts": [
                {
                    "prompt_id": "p2",
                    "roadmap_step_id": "s2",
                    "status": "draft",
                    "execution_status": "planned",
                    "dispatch_ready": True,
                    "path": (
                        "coordination/self_coordination/"
                        "prompt_queue/draft/p2.md"
                    ),
                    "sequence": 2,
                    "queue_rank": 2,
                    "priority": "critical",
                    "created_at": "2026-08-16",
                },
                {
                    "prompt_id": "p3",
                    "roadmap_step_id": "s3",
                    "status": "draft",
                    "execution_status": "planned",
                    "dispatch_ready": True,
                    "path": (
                        "coordination/self_coordination/"
                        "prompt_queue/draft/p3.md"
                    ),
                    "sequence": 3,
                    "queue_rank": 3,
                    "priority": "high",
                    "created_at": "2026-08-15",
                },
            ],
        },
    )
    write_yaml(
        handoff,
        {
            "metadata": {},
            "current_blueprint_plan": {},
            "self_coordination_health": {},
        },
    )
    write_yaml(
        policy,
        {
            "roadmap": {
                "minimum_future_steps": 1,
                "target_future_steps": 2,
            },
            "prompt_buffer": {
                "minimum_dispatchable_drafts": 1,
                "target_dispatchable_drafts": 2,
            },
        },
    )
    p2.parent.mkdir(parents=True, exist_ok=True)
    p2.write_text(
        "---\n"
        "schema_version: demo_prompt_v0_1\n"
        "prompt_id: p2\n"
        "status: draft\n"
        "roadmap_step_id: s2\n"
        "---\n"
        "# P2\n",
        encoding="utf-8",
    )
    p3.write_text(
        "---\n"
        "schema_version: demo_prompt_v0_1\n"
        "prompt_id: p3\n"
        "status: draft\n"
        "roadmap_step_id: s3\n"
        "---\n"
        "# P3\n",
        encoding="utf-8",
    )
    return {
        "root": root,
        "roadmap": roadmap,
        "queue": queue,
        "handoff": handoff,
        "policy": policy,
        "p2": p2,
        "p3": p3,
    }


def request_for(
    module,
    paths: dict[str, Path],
    *,
    override_prompt_id: str | None = None,
    activation_id: str = "activation_demo_001",
) -> dict:
    root = paths["root"]
    selection = module.select_next_prompt(
        root,
        override_prompt_id=override_prompt_id,
    )
    assert selection["result_state"] == "NEXT_PROMPT_SELECTED"
    selected = selection["selected_prompt"]
    assert selected is not None
    prompt_path = root / selected["path"]

    evidence = (
        root
        / "coordination/internal_work/blueprint/governance/"
        "next_prompt_activation"
        / f"{activation_id}.yaml"
    )
    return {
        "schema_version": module.ACTIVATION_REQUEST_SCHEMA,
        "activation_id": activation_id,
        "activated_at": "2026-08-16T20:00:00+03:00",
        "selection": {
            "prompt_id": selected["prompt_id"],
            "roadmap_step_id": selected["roadmap_step_id"],
            "selection_fingerprint_sha256": selection[
                "selection_fingerprint_sha256"
            ],
            "selection_source": selection["selection_source"],
        },
        "targets": {
            "roadmap_path": str(paths["roadmap"].relative_to(root)),
            "prompt_queue_path": str(paths["queue"].relative_to(root)),
            "handoff_path": str(paths["handoff"].relative_to(root)),
            "prompt_path": str(prompt_path.relative_to(root)),
            "activation_evidence_path": str(
                evidence.relative_to(root)
            ),
        },
        "preconditions": {
            "roadmap_sha256": module.file_sha256(paths["roadmap"]),
            "prompt_queue_sha256": module.file_sha256(paths["queue"]),
            "handoff_sha256": module.file_sha256(paths["handoff"]),
            "prompt_sha256": module.file_sha256(prompt_path),
        },
    }


def test_default_order_prefers_priority_over_queue_sequence_and_date(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)

    queue = load(paths["queue"])
    p2 = next(x for x in queue["prompts"] if x["prompt_id"] == "p2")
    p3 = next(x for x in queue["prompts"] if x["prompt_id"] == "p3")
    p2["priority"] = "high"
    p2["created_at"] = "2020-01-01"
    p3["priority"] = "critical"
    p3["created_at"] = "2099-12-31"
    write_yaml(paths["queue"], queue)

    report = module.select_next_prompt(paths["root"])

    assert report["result_state"] == "NEXT_PROMPT_SELECTED"
    assert report["eligible_prompt_ids"] == ["p3", "p2"]
    assert report["selected_prompt"]["prompt_id"] == "p3"
    assert (
        report["selection_source"]
        == "dependency_eligibility_priority_stable_id"
    )
    assert report["selection_performed"] is True
    assert report["activation_performed"] is False


def test_equal_priority_uses_prompt_id_not_queue_sequence_or_date(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)

    queue = load(paths["queue"])
    p2 = next(x for x in queue["prompts"] if x["prompt_id"] == "p2")
    p3 = next(x for x in queue["prompts"] if x["prompt_id"] == "p3")
    for item in (p2, p3):
        item["priority"] = "high"
    p2["queue_rank"] = 999
    p2["sequence"] = 999
    p2["created_at"] = "2099-12-31"
    p3["queue_rank"] = 1
    p3["sequence"] = 1
    p3["created_at"] = "2020-01-01"
    write_yaml(paths["queue"], queue)

    report = module.select_next_prompt(paths["root"])

    assert report["eligible_prompt_ids"] == ["p2", "p3"]
    assert report["selected_prompt"]["prompt_id"] == "p2"


def test_dependency_ineligible_prompt_is_blocked(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    roadmap = load(paths["roadmap"])
    s2 = next(x for x in roadmap["steps"] if x["step_id"] == "s2")
    s2["depends_on"] = ["s3"]
    write_yaml(paths["roadmap"], roadmap)

    report = module.select_next_prompt(paths["root"])

    assert report["selected_prompt"]["prompt_id"] == "p3"
    assert "p2" in report["blocked_prompts"]
    assert report["blocked_prompts"]["p2"] == [
        "DEPENDENCY_NOT_COMPLETED:s3"
    ]


def test_valid_explicit_override_wins_after_eligibility(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)

    report = module.select_next_prompt(
        paths["root"],
        override_prompt_id="p3",
    )

    assert report["result_state"] == "NEXT_PROMPT_SELECTED"
    assert report["selected_prompt"]["prompt_id"] == "p3"
    assert report["selection_source"] == "explicit_validated_override"


def test_invalid_override_fails_safely(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    roadmap = load(paths["roadmap"])
    s3 = next(x for x in roadmap["steps"] if x["step_id"] == "s3")
    s3["depends_on"] = ["s2"]
    write_yaml(paths["roadmap"], roadmap)

    with pytest.raises(
        module.SelectionActivationError,
        match="explicit override is not dependency-eligible",
    ):
        module.select_next_prompt(
            paths["root"],
            override_prompt_id="p3",
        )


def test_active_prompt_blocks_activation_selection(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    queue = load(paths["queue"])
    p2 = next(x for x in queue["prompts"] if x["prompt_id"] == "p2")
    p2["status"] = "approved"
    p2["execution_status"] = "ready_for_module_pull"
    queue["metadata"]["active_prompt_id"] = "p2"
    write_yaml(paths["queue"], queue)

    report = module.select_next_prompt(paths["root"])

    assert report["result_state"] == "ACTIVE_PROMPT_PRESENT"
    assert report["active_prompt_ids"] == ["p2"]
    assert report["selected_prompt"] is None
    assert report["selection_performed"] is False
    assert report["activation_performed"] is False


def test_multiple_active_prompts_is_attention_required(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    queue = load(paths["queue"])
    for item in queue["prompts"]:
        item["status"] = "approved"
        item["execution_status"] = "ready_for_module_pull"
    queue["metadata"]["active_prompt_id"] = "p2"
    write_yaml(paths["queue"], queue)

    report = module.select_next_prompt(paths["root"])

    assert report["result_state"] == "ATTENTION_REQUIRED"
    assert report["error_code"] == "MULTIPLE_ACTIVE_PROMPTS"
    assert report["active_prompt_count"] == 2


def test_prepare_activation_is_read_only(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths)
    before = {
        key: path.read_bytes()
        for key, path in paths.items()
        if key != "root" and path.is_file()
    }

    plan = module.prepare_activation(paths["root"], request)

    assert plan["result_state"] == "ACTIVATION_READY"
    assert plan["selection_performed"] is True
    assert plan["activation_performed"] is False
    for key, payload in before.items():
        assert paths[key].read_bytes() == payload


def test_activation_mutates_bounded_blueprint_state(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths)

    result = module.apply_activation(
        paths["root"],
        request,
        activation_confirmation="activation_demo_001",
    )

    assert result["result_state"] == "ACTIVATED"
    assert result["prompt_id"] == "p2"
    assert result["roadmap_step_id"] == "s2"
    assert result["automatic_acceptance"] is False
    assert result["automatic_return"] is False
    assert result["automatic_hold"] is False

    roadmap = load(paths["roadmap"])
    queue = load(paths["queue"])
    handoff = load(paths["handoff"])
    s2 = next(x for x in roadmap["steps"] if x["step_id"] == "s2")
    p2 = next(x for x in queue["prompts"] if x["prompt_id"] == "p2")

    assert roadmap["metadata"]["current_step_id"] == "s2"
    assert roadmap["metadata"]["actionable_steps_after_current"] == 1
    assert s2["status"] == "active"
    assert queue["metadata"]["active_prompt_id"] == "p2"
    assert p2["status"] == "approved"
    assert p2["execution_status"] == "ready_for_module_pull"
    assert not paths["p2"].exists()
    approved = paths["p2"].parent.parent / "approved" / "p2.md"
    assert approved.is_file()
    assert "status: approved" in approved.read_text(encoding="utf-8")
    assert (
        handoff["current_blueprint_plan"]["active_blueprint_step"]["id"]
        == "s2"
    )
    evidence = (
        paths["root"]
        / "coordination/internal_work/blueprint/governance/"
        "next_prompt_activation/activation_demo_001.yaml"
    )
    record = load(evidence)
    assert record["result"] == "ACTIVATED"
    assert record["transaction"]["wip_limit"] == 1
    assert record["transaction"]["exact_rollback_on_failure"] is True
    assert record["boundaries"]["module_repository_writes"] is False


def test_explicit_override_can_be_activated(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(
        module,
        paths,
        override_prompt_id="p3",
    )

    result = module.apply_activation(
        paths["root"],
        request,
        activation_confirmation="activation_demo_001",
    )

    assert result["result_state"] == "ACTIVATED"
    assert result["prompt_id"] == "p3"
    assert not paths["p3"].exists()
    approved = paths["p3"].parent.parent / "approved" / "p3.md"
    assert approved.is_file()


def test_activation_confirmation_must_match_identity(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths)

    with pytest.raises(
        module.SelectionActivationError,
        match="activation_confirmation must exactly match activation_id",
    ):
        module.apply_activation(
            paths["root"],
            request,
            activation_confirmation="wrong",
        )


def test_activation_rolls_back_exactly_on_post_write_failure(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths)

    tracked = [
        paths["roadmap"],
        paths["queue"],
        paths["handoff"],
        paths["p2"],
    ]
    before = {
        path: path.read_bytes() if path.exists() else None
        for path in tracked
    }

    def fail() -> None:
        raise RuntimeError("forced post-write failure")

    with pytest.raises(RuntimeError, match="forced post-write failure"):
        module.apply_activation(
            paths["root"],
            request,
            activation_confirmation="activation_demo_001",
            post_write_validator=fail,
        )

    for path, payload in before.items():
        assert path.exists() == (payload is not None)
        if payload is not None:
            assert path.read_bytes() == payload
    approved = paths["p2"].parent.parent / "approved" / "p2.md"
    evidence = (
        paths["root"]
        / "coordination/internal_work/blueprint/governance/"
        "next_prompt_activation/activation_demo_001.yaml"
    )
    assert not approved.exists()
    assert not evidence.exists()


def test_same_activation_identity_is_idempotent(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths)

    first = module.apply_activation(
        paths["root"],
        request,
        activation_confirmation="activation_demo_001",
    )
    roadmap_after = paths["roadmap"].read_bytes()
    queue_after = paths["queue"].read_bytes()

    second = module.apply_activation(
        paths["root"],
        request,
        activation_confirmation="activation_demo_001",
    )

    assert first["result_state"] == "ACTIVATED"
    assert second["result_state"] == "ALREADY_APPLIED"
    assert second["idempotent_noop"] is True
    assert paths["roadmap"].read_bytes() == roadmap_after
    assert paths["queue"].read_bytes() == queue_after


def test_conflicting_activation_identity_fails_safely(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths)
    module.apply_activation(
        paths["root"],
        request,
        activation_confirmation="activation_demo_001",
    )

    conflict = copy.deepcopy(request)
    conflict["activated_at"] = "2026-08-16T20:01:00+03:00"

    with pytest.raises(
        module.SelectionActivationError,
        match="different activation identity",
    ):
        module.apply_activation(
            paths["root"],
            conflict,
            activation_confirmation="activation_demo_001",
        )


def test_activation_evidence_path_is_blueprint_contained(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths)
    request["targets"]["activation_evidence_path"] = (
        "coordination/review_packets/demo.yaml"
    )

    with pytest.raises(
        module.SelectionActivationError,
        match="activation evidence must be under",
    ):
        module.prepare_activation(paths["root"], request)


def test_stale_precondition_hash_fails_before_write(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths)
    request["preconditions"]["roadmap_sha256"] = "0" * 64

    with pytest.raises(
        module.SelectionActivationError,
        match="precondition mismatch: roadmap_sha256",
    ):
        module.prepare_activation(paths["root"], request)


def test_current_step26_implementation_does_not_self_advance() -> None:
    module = tool_module()
    roadmap = load(ROADMAP)
    queue = load(QUEUE)
    handoff = load(HANDOFF)
    bootstrap = load(BOOTSTRAP)

    current_id = roadmap["metadata"]["current_step_id"]
    assert current_id in {STEP26, STEP27}

    step25 = next(
        x for x in roadmap["steps"] if x["step_id"] == STEP25
    )
    step26 = next(
        x for x in roadmap["steps"] if x["step_id"] == STEP26
    )
    prompt26 = next(
        x for x in queue["prompts"] if x["prompt_id"] == STEP26
    )
    state = handoff["next_prompt_selection_activation_v0_4"]

    assert step25["status"] == "completed"
    assert step25["operator_decision"] == "ACCEPT"

    if current_id == STEP26:
        assert step26["status"] == "active"
        assert queue["metadata"]["active_prompt_id"] == STEP26
        assert prompt26["status"] == "approved"
        assert prompt26["execution_status"] == "ready_for_module_pull"
        assert state["implementation_status"] == "READY_FOR_OPERATOR_REVIEW"
        assert state["operator_decision_created"] is False

        live = module.live_status(ROOT)
        assert live["result_state"] == "ACTIVE_PROMPT_PRESENT"
        assert live["active_prompt_ids"] == [STEP26]
        assert live["selection_performed"] is False
        assert live["activation_performed"] is False
    else:
        assert state["implementation_status"] == "accepted_v0_4"
        assert state["operator_decision"] == "ACCEPT"

    assert state["selection_engine_implemented"] is True
    assert state["activation_engine_implemented"] is True
    assert state["selection_activation_separate"] is True
    assert state["activation_wip_limit"] == 1
    assert state["dependency_eligibility_required"] is True
    assert state["explicit_override_must_be_eligible"] is True
    assert state["tracking_events_reference_run"] is False
    assert state["dark_zone_audit_run"] is False
    assert state["global_v0_4_promotion_performed"] is False
    assert state["module_repository_writes"] is False
    assert state["automatic_acceptance"] is False
    assert state["automatic_return"] is False
    assert state["automatic_hold"] is False
    assert state["automatic_commit"] is False
    assert state["automatic_push"] is False

    prior = handoff["review_roadmap_queue_transaction_v0_4"]
    assert prior["step26_selection_activation_implemented"] is False
    assert prior["tracking_events_reference_run"] is False

    source_map = bootstrap["source_of_truth_map"]
    assert (
        source_map["next_prompt_selection_activation_v0_4_tool"]
        == "scripts/coordination/next_prompt_selection_activation_v0_4.py"
    )
    assert (
        source_map["next_prompt_selection_activation_v0_4_test"]
        == "tests/validation/test_v0_4_next_prompt_selection_activation.py"
    )

    prompt27 = next(
        x for x in queue["prompts"] if x["prompt_id"] == STEP27
    )
    prompt28 = next(
        x for x in queue["prompts"] if x["prompt_id"] == STEP28
    )
    if current_id == STEP26:
        assert prompt27["status"] == "draft"
        assert prompt28["status"] == "draft"
