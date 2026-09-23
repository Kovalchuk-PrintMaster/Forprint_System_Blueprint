from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STANDARD = ROOT / "coordination/standards/governance/module_completion_outbox_v0_4.yaml"
TEMPLATE = ROOT / "coordination/templates/module_completion_outbox_v0_4.example.yaml"
VALIDATOR = ROOT / "scripts/coordination/validate_completion_outbox_v0_4.py"
REGISTRY = ROOT / "coordination/registry/coordination_source_registry_v0_1.yaml"
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
QUEUE = ROOT / "coordination/self_coordination/prompt_queue/index.yaml"
HANDOFF = ROOT / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
BOOTSTRAP = ROOT / "coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_1.yaml"

STEP23 = "blueprint_v0_4_completion_outbox_v0_1"


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def validator_module():
    spec = importlib.util.spec_from_file_location("completion_outbox_v0_4", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate(event: dict) -> dict:
    module = validator_module()
    temp = ROOT / "tmp" / "test_completion_outbox_v0_4_event.yaml"
    temp.parent.mkdir(parents=True, exist_ok=True)
    temp.write_text(
        yaml.safe_dump(event, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    try:
        return module.validate_outbox_event(
            temp,
            root=ROOT,
            registry_path=REGISTRY,
            template_mode=True,
        )
    finally:
        if temp.exists():
            temp.unlink()


def test_standard_defines_module_owned_immutable_outbox() -> None:
    standard = load(STANDARD)
    assert standard["schema_version"] == "module_completion_outbox_standard_v0_4"
    assert standard["metadata"]["status"] == "candidate_reference_only"
    assert standard["instance"]["schema_version"] == "module_completion_outbox_event_v0_4"
    assert (
        standard["instance"]["canonical_path"]
        == "coordination/completion_outbox/records/<event_id>.yaml"
    )
    assert standard["instance"]["immutable"] is True
    assert standard["instance"]["historical_event_mutation_allowed"] is False
    assert standard["registry_binding"]["completion_outbox_authority"] == "module_owned"
    assert standard["completion_packet_binding"]["packet_sha256_required"] is True
    assert (
        standard["publication_evidence"]["remote_containment_verified_must_be_true"]
        is True
    )
    assert (
        standard["publication_evidence"]["outbox_event_commit_embedded_in_event"]
        is False
    )
    assert standard["publication_evidence"]["self_reference_avoided"] is True
    assert standard["governance"]["module_event_is_operator_decision"] is False
    assert standard["promotion"]["promotion_performed"] is False


def test_scope_boundaries_do_not_implement_later_steps() -> None:
    standard = load(STANDARD)
    boundaries = standard["scope_boundaries"]
    assert boundaries["module_outbox_directories_created_by_blueprint"] is False
    assert boundaries["registry_availability_mutated"] is False
    assert boundaries["completion_discovery_or_intake_implemented"] is False
    assert boundaries["operator_review_automation_implemented"] is False
    assert boundaries["next_prompt_activation_implemented"] is False
    assert boundaries["tracking_events_reference_run"] is False
    assert boundaries["module_repository_writes"] is False
    assert boundaries["rollout_or_production_write"] is False


def test_registry_locator_and_ownership_are_preserved_for_all_modules() -> None:
    registry = load(REGISTRY)
    assert registry["lookup_policy"]["completion_outbox_authority"] == "module_owned"
    assert (
        registry["lookup_policy"]["completion_outbox_future_path"]
        == "coordination/completion_outbox/records"
    )
    assert (
        registry["lookup_policy"]["module_repository_access"]
        == "read_only_from_blueprint"
    )
    assert len(registry["modules"]) == 8
    for item in registry["modules"]:
        outbox = item["sources"]["completion_outbox"]
        assert outbox["owner"] == item["module_id"]
        assert outbox["repository"] == item["repository"]["repository_id"]
        assert outbox["path"] == "coordination/completion_outbox/records"
        assert outbox["availability"] == "not_present_yet"
        assert outbox["implementation_step"] == STEP23
        assert item["boundaries"]["module_owns_completion_outbox"] is True


def test_template_validates() -> None:
    event = load(TEMPLATE)
    report = validate(event)
    assert report["result"] == "PASSED"
    assert report["errors"] == []


def test_validator_rejects_unregistered_module() -> None:
    event = load(TEMPLATE)
    event["module_id"] = "unknown_module"
    report = validate(event)
    assert "module_id is not uniquely registered" in report["errors"]


def test_validator_rejects_repository_mismatch() -> None:
    event = load(TEMPLATE)
    event["repository_id"] = "wrong_repository"
    report = validate(event)
    assert "repository_id does not match registry" in report["errors"]


def test_validator_rejects_bad_packet_path() -> None:
    event = load(TEMPLATE)
    event["completion_packet"]["path"] = "somewhere/else.yaml"
    report = validate(event)
    assert "completion_packet.path mismatch" in report["errors"]


def test_validator_rejects_bad_packet_hash() -> None:
    event = load(TEMPLATE)
    event["completion_packet"]["sha256"] = "abc"
    report = validate(event)
    assert "completion_packet.sha256 must be 64 lowercase hex" in report["errors"]


def test_validator_requires_remote_containment_proof() -> None:
    event = load(TEMPLATE)
    event["publication"]["remote_containment_verified"] = False
    report = validate(event)
    assert "publication.remote_containment_verified must be true" in report["errors"]


def test_validator_prevents_outbox_commit_self_reference() -> None:
    event = load(TEMPLATE)
    event["publication"]["outbox_event_commit_embedded_in_event"] = True
    report = validate(event)
    assert (
        "publication.outbox_event_commit_embedded_in_event must be false"
        in report["errors"]
    )


def test_superseding_revision_requires_complete_triple() -> None:
    event = load(TEMPLATE)
    event["revision"]["supersedes_event_id"] = "old_event"
    report = validate(event)
    assert "superseding event fields must be provided together" in report["errors"]


def test_superseding_revision_must_use_canonical_path() -> None:
    event = load(TEMPLATE)
    event["revision"] = {
        "supersedes_event_id": "old_event",
        "supersedes_event_path": "wrong/old_event.yaml",
        "revision_reason": "correction",
    }
    report = validate(event)
    assert "revision.supersedes_event_path must be canonical" in report["errors"]


def test_event_cannot_supersede_itself() -> None:
    event = load(TEMPLATE)
    event["revision"] = {
        "supersedes_event_id": event["event_id"],
        "supersedes_event_path": (
            "coordination/completion_outbox/records/"
            f"{event['event_id']}.yaml"
        ),
        "revision_reason": "invalid self revision",
    }
    report = validate(event)
    assert "outbox event cannot supersede itself" in report["errors"]


def test_step23_implementation_does_not_advance_lifecycle() -> None:
    roadmap = load(ROADMAP)
    queue = load(QUEUE)
    handoff = load(HANDOFF)

    step23 = next(x for x in roadmap["steps"] if x["step_id"] == STEP23)
    outbox_state = handoff["completion_outbox_v0_4"]
    step24 = "blueprint_v0_4_completion_discovery_and_intake_v0_1"
    step25 = "blueprint_v0_4_review_roadmap_queue_transaction_v0_1"
    step26 = "blueprint_v0_4_next_prompt_selection_and_activation_v0_1"
    step27 = "blueprint_v0_4_tracking_events_reference_v0_1"
    current_id = roadmap["metadata"]["current_step_id"]

    assert current_id in {STEP23, step24, step25, step26, step27}
    assert queue["metadata"]["active_prompt_id"] == current_id

    prompt23 = next(x for x in queue["prompts"] if x["prompt_id"] == STEP23)
    if current_id == STEP23:
        assert step23["status"] == "active"
        assert prompt23["status"] == "approved"
        assert outbox_state["implementation_status"] == "READY_FOR_OPERATOR_REVIEW"
    else:
        assert step23["status"] == "completed"
        assert step23["operator_decision"] == "ACCEPT"
        assert prompt23["status"] == "completed"
        assert prompt23["execution_status"] == "accepted"
        assert outbox_state["implementation_status"] == "accepted_v0_4"

    if current_id in {step25, step26, step27}:
        step24_record = next(
            x for x in roadmap["steps"] if x["step_id"] == step24
        )
        prompt24 = next(x for x in queue["prompts"] if x["prompt_id"] == step24)
        assert step24_record["status"] == "completed"
        assert step24_record["operator_decision"] == "ACCEPT"
        assert prompt24["status"] == "completed"
        assert prompt24["execution_status"] == "accepted"

    if current_id in {step26, step27}:
        step25_record = next(
            x for x in roadmap["steps"] if x["step_id"] == step25
        )
        prompt25 = next(x for x in queue["prompts"] if x["prompt_id"] == step25)
        assert step25_record["status"] == "completed"
        assert step25_record["operator_decision"] == "ACCEPT"
        assert prompt25["status"] == "completed"
        assert prompt25["execution_status"] == "accepted"

    if current_id == step27:
        step26_record = next(
            x for x in roadmap["steps"] if x["step_id"] == step26
        )
        prompt26 = next(x for x in queue["prompts"] if x["prompt_id"] == step26)
        prompt27 = next(x for x in queue["prompts"] if x["prompt_id"] == step27)
        assert step26_record["status"] == "completed"
        assert step26_record["operator_decision"] == "ACCEPT"
        assert prompt26["status"] == "completed"
        assert prompt26["execution_status"] == "accepted"
        assert prompt27["status"] == "approved"

    assert outbox_state["promotion_performed"] is False
    assert outbox_state["completion_discovery_or_intake_implemented"] is False
    assert outbox_state["module_repository_writes"] is False

def test_completion_packet_step22_state_remains_historical_and_accepted() -> None:
    handoff = load(HANDOFF)
    packet = handoff["completion_packet_v0_4"]
    assert packet["implementation_status"] == "accepted_v0_4"
    assert packet["operator_decision"] == "ACCEPT"
    assert packet["promotion_performed"] is False
    assert packet["completion_outbox_implemented"] is False


def test_bootstrap_points_to_outbox_contract_assets() -> None:
    bootstrap = load(BOOTSTRAP)
    source_map = bootstrap["source_of_truth_map"]
    assert (
        source_map["completion_outbox_v0_4_standard"]
        == "coordination/standards/governance/module_completion_outbox_v0_4.yaml"
    )
    assert (
        source_map["completion_outbox_v0_4_template"]
        == "coordination/templates/module_completion_outbox_v0_4.example.yaml"
    )
    assert (
        source_map["completion_outbox_v0_4_validator"]
        == "scripts/coordination/validate_completion_outbox_v0_4.py"
    )
