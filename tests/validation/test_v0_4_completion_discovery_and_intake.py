from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOL = (
    ROOT
    / "scripts/coordination/completion_discovery_and_intake_v0_4.py"
)
REGISTRY = (
    ROOT
    / "coordination/registry/coordination_source_registry_v0_1.yaml"
)
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
QUEUE = ROOT / "coordination/self_coordination/prompt_queue/index.yaml"
HANDOFF = (
    ROOT
    / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
)
BOOTSTRAP = (
    ROOT
    / "coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_1.yaml"
)
LEGACY_INTAKE = ROOT / "scripts/coordination/completion_intake_check.py"

STEP23 = "blueprint_v0_4_completion_outbox_v0_1"
STEP24 = "blueprint_v0_4_completion_discovery_and_intake_v0_1"


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def tool_module():
    spec = importlib.util.spec_from_file_location(
        "completion_discovery_intake_v04",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_registry(repo: Path, *, availability: str = "not_present_yet") -> dict:
    return {
        "schema_version": "coordination_source_registry_v0_1",
        "lookup_policy": {
            "module_repository_access": "read_only_from_blueprint",
            "completion_outbox_authority": "module_owned",
            "completion_outbox_future_path": (
                "coordination/completion_outbox/records"
            ),
            "missing_future_source_behavior": (
                "record_not_present_yet_do_not_fabricate"
            ),
        },
        "modules": [
            {
                "module_id": "demo_module",
                "repository": {
                    "repository_id": "demo_repository",
                    "local_path": str(repo),
                    "remote_name": "origin",
                },
                "sources": {
                    "completion_outbox": {
                        "owner": "demo_module",
                        "repository": "demo_repository",
                        "path": "coordination/completion_outbox/records",
                        "availability": availability,
                        "implementation_step": STEP23,
                    }
                },
                "boundaries": {
                    "blueprint_lookup_mode": "read_only",
                    "module_owns_completion_outbox": True,
                    "blueprint_may_write_repository": False,
                },
            }
        ],
    }


def write_registry(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "registry.yaml"
    path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )
    return path


def passed_outbox(*args, **kwargs) -> dict:
    return {"result": "PASSED", "errors": [], "warnings": []}


def passed_packet(*args, **kwargs) -> dict:
    return {"result": "PASSED", "errors": [], "warnings": []}


def packet_data(completion_id: str, module_id: str, prompt_id: str) -> dict:
    return {
        "schema_version": "module_completion_packet_v0_4",
        "completion_id": completion_id,
        "module_id": module_id,
        "prompt_id": prompt_id,
    }


def event_data(
    event_id: str,
    completion_id: str,
    *,
    supersedes: str | None = None,
) -> dict:
    revision = {}
    if supersedes is not None:
        revision = {
            "supersedes_event_id": supersedes,
            "supersedes_event_path": (
                "coordination/completion_outbox/records/"
                f"{supersedes}.yaml"
            ),
            "revision_reason": "correction",
        }
    return {
        "schema_version": "module_completion_outbox_event_v0_4",
        "event_id": event_id,
        "module_id": "demo_module",
        "repository_id": "demo_repository",
        "prompt_id": "prompt_demo",
        "completion_id": completion_id,
        "emitted_at": "2026-08-16T12:00:00+03:00",
        "completion_packet": {
            "path": (
                "coordination/completion_packets/records/"
                f"{completion_id}.yaml"
            )
        },
        "revision": revision,
    }


def write_event_and_packet(
    repo: Path,
    event: dict,
) -> None:
    outbox = repo / "coordination/completion_outbox/records"
    packets = repo / "coordination/completion_packets/records"
    outbox.mkdir(parents=True, exist_ok=True)
    packets.mkdir(parents=True, exist_ok=True)
    event_id = event["event_id"]
    completion_id = event["completion_id"]
    (outbox / f"{event_id}.yaml").write_text(
        yaml.safe_dump(event, sort_keys=False),
        encoding="utf-8",
    )
    packet = packet_data(
        completion_id,
        event["module_id"],
        event["prompt_id"],
    )
    (packets / f"{completion_id}.yaml").write_text(
        yaml.safe_dump(packet, sort_keys=False),
        encoding="utf-8",
    )


def test_missing_outbox_is_normal_and_not_fabricated(tmp_path: Path) -> None:
    module = tool_module()
    repo = tmp_path / "module"
    repo.mkdir()
    registry = write_registry(tmp_path, fake_registry(repo))

    before = module._tree_fingerprint(repo)
    report = module.discover_completions(
        blueprint_root=ROOT,
        registry_path=registry,
    )
    after = module._tree_fingerprint(repo)

    assert before == after
    assert report["result_state"] == "NO_COMPLETIONS_AVAILABLE"
    assert report["summary"]["registered_sources"] == 1
    assert report["summary"]["events_discovered"] == 0
    assert report["summary"]["review_candidates"] == 0
    assert report["sources"][0]["observed_source_state"] == "not_present_yet"
    assert not (repo / "coordination/completion_outbox/records").exists()
    assert report["governance"]["missing_sources_fabricated"] is False
    assert report["governance"]["module_repository_writes"] is False


def test_discovery_is_idempotent_and_fingerprint_is_stable(
    tmp_path: Path,
) -> None:
    module = tool_module()
    repo = tmp_path / "module"
    repo.mkdir()
    registry = write_registry(tmp_path, fake_registry(repo))

    first = module.discover_completions(
        blueprint_root=ROOT,
        registry_path=registry,
    )
    second = module.discover_completions(
        blueprint_root=ROOT,
        registry_path=registry,
    )

    assert first == second
    assert (
        first["discovery_fingerprint_sha256"]
        == second["discovery_fingerprint_sha256"]
    )


def test_invalid_outbox_event_is_classified_without_module_write(
    tmp_path: Path,
) -> None:
    module = tool_module()
    repo = tmp_path / "module"
    outbox = repo / "coordination/completion_outbox/records"
    outbox.mkdir(parents=True)
    (outbox / "bad.yaml").write_text("{}\n", encoding="utf-8")
    registry = write_registry(
        tmp_path,
        fake_registry(repo, availability="present"),
    )

    before = module._tree_fingerprint(repo)
    report = module.discover_completions(
        blueprint_root=ROOT,
        registry_path=registry,
    )
    after = module._tree_fingerprint(repo)

    assert before == after
    assert report["result_state"] == "ATTENTION_REQUIRED"
    assert report["summary"]["invalid_events"] == 1
    assert report["summary"]["review_candidates"] == 0
    assert (
        report["sources"][0]["events"][0]["classification"]
        == "invalid_outbox_event"
    )


def test_valid_event_and_packet_become_review_candidate(
    tmp_path: Path,
) -> None:
    module = tool_module()
    repo = tmp_path / "module"
    repo.mkdir()
    event = event_data("event_1", "completion_1")
    write_event_and_packet(repo, event)
    registry = write_registry(
        tmp_path,
        fake_registry(repo, availability="present"),
    )

    report = module.discover_completions(
        blueprint_root=ROOT,
        registry_path=registry,
        outbox_validator=passed_outbox,
        packet_validator=passed_packet,
    )

    assert report["result_state"] == "READY_FOR_BLUEPRINT_REVIEW"
    assert report["summary"]["review_candidates"] == 1
    candidate = report["review_candidates"][0]
    assert candidate["event_id"] == "event_1"
    assert candidate["completion_id"] == "completion_1"
    assert candidate["intake_state"] == "READY_FOR_BLUEPRINT_REVIEW"
    assert candidate["operator_decision_created"] is False
    assert report["governance"]["automatic_acceptance"] is False
    assert report["governance"]["automatic_return"] is False


def test_superseding_event_removes_historical_event_from_effective_candidates(
    tmp_path: Path,
) -> None:
    module = tool_module()
    repo = tmp_path / "module"
    repo.mkdir()
    write_event_and_packet(
        repo,
        event_data("event_1", "completion_1"),
    )
    write_event_and_packet(
        repo,
        event_data(
            "event_2",
            "completion_2",
            supersedes="event_1",
        ),
    )
    registry = write_registry(
        tmp_path,
        fake_registry(repo, availability="present"),
    )

    report = module.discover_completions(
        blueprint_root=ROOT,
        registry_path=registry,
        outbox_validator=passed_outbox,
        packet_validator=passed_packet,
    )

    assert report["summary"]["events_discovered"] == 2
    assert report["summary"]["superseded_events"] == 1
    assert report["summary"]["review_candidates"] == 1
    assert report["review_candidates"][0]["event_id"] == "event_2"
    events = {
        item["identity"]["event_id"]: item
        for item in report["sources"][0]["events"]
    }
    assert events["event_1"]["classification"] == "superseded"
    assert events["event_2"]["classification"] == "ready_for_blueprint_review"


def test_ambiguous_supersession_requires_attention(tmp_path: Path) -> None:
    module = tool_module()
    repo = tmp_path / "module"
    repo.mkdir()
    write_event_and_packet(
        repo,
        event_data("event_1", "completion_1"),
    )
    write_event_and_packet(
        repo,
        event_data("event_2", "completion_2", supersedes="event_1"),
    )
    write_event_and_packet(
        repo,
        event_data("event_3", "completion_3", supersedes="event_1"),
    )
    registry = write_registry(
        tmp_path,
        fake_registry(repo, availability="present"),
    )

    report = module.discover_completions(
        blueprint_root=ROOT,
        registry_path=registry,
        outbox_validator=passed_outbox,
        packet_validator=passed_packet,
    )

    assert report["result_state"] == "ATTENTION_REQUIRED"
    assert report["summary"]["invalid_events"] == 3
    assert report["summary"]["review_candidates"] == 0


def test_step24_implementation_does_not_advance_lifecycle_or_decide() -> None:
    roadmap = load(ROADMAP)
    queue = load(QUEUE)
    handoff = load(HANDOFF)

    step24 = next(item for item in roadmap["steps"] if item["step_id"] == STEP24)
    prompt24 = next(item for item in queue["prompts"] if item["prompt_id"] == STEP24)
    state = handoff["completion_discovery_intake_v0_4"]
    step25 = "blueprint_v0_4_review_roadmap_queue_transaction_v0_1"
    step26 = "blueprint_v0_4_next_prompt_selection_and_activation_v0_1"
    step27 = "blueprint_v0_4_tracking_events_reference_v0_1"
    current_id = roadmap["metadata"]["current_step_id"]

    assert current_id in {STEP24, step25, step26, step27}
    assert queue["metadata"]["active_prompt_id"] == current_id

    if current_id == STEP24:
        assert step24["status"] == "active"
        assert prompt24["status"] == "approved"
        assert state["implementation_status"] == "READY_FOR_OPERATOR_REVIEW"
        assert state["operator_decision_created"] is False
    else:
        assert step24["status"] == "completed"
        assert step24["operator_decision"] == "ACCEPT"
        assert prompt24["status"] == "completed"
        assert prompt24["execution_status"] == "accepted"
        assert prompt24["operator_decision"] == "ACCEPT"
        assert state["implementation_status"] == "accepted_v0_4"
        assert state["operator_decision_created"] is True
        assert state["operator_decision"] == "ACCEPT"

        current_prompt = next(
            item for item in queue["prompts"] if item["prompt_id"] == current_id
        )
        assert current_prompt["status"] == "approved"
        assert current_prompt["execution_status"] == "ready_for_module_pull"

    assert state["review_roadmap_queue_transaction_implemented"] is False
    assert state["global_v0_4_promotion_performed"] is False
    assert state["module_repository_writes"] is False
    assert state["automatic_commit"] is False
    assert state["automatic_push"] is False

def test_step23_historical_scope_marker_remains_immutable() -> None:
    handoff = load(HANDOFF)
    outbox = handoff["completion_outbox_v0_4"]
    assert outbox["implementation_status"] == "accepted_v0_4"
    assert outbox["operator_decision"] == "ACCEPT"
    assert outbox["publication_verified"] is True
    assert outbox["promotion_performed"] is False
    assert outbox["completion_discovery_or_intake_implemented"] is False


def test_bootstrap_points_to_v04_discovery_intake_assets() -> None:
    bootstrap = load(BOOTSTRAP)
    source_map = bootstrap["source_of_truth_map"]
    assert (
        source_map["completion_discovery_intake_v0_4_tool"]
        == "scripts/coordination/completion_discovery_and_intake_v0_4.py"
    )
    assert (
        source_map["completion_discovery_intake_v0_4_test"]
        == "tests/validation/test_v0_4_completion_discovery_and_intake.py"
    )


def test_legacy_operational_and_candidate_intake_revisions_are_unchanged() -> None:
    text = LEGACY_INTAKE.read_text(encoding="utf-8")
    assert 'CURRENT_PACKET_SCHEMA = "module_completion_packet_v0_2"' in text
    assert 'CURRENT_INTAKE_PROTOCOL = "blueprint_completion_intake_v0_2"' in text
    assert 'CANDIDATE_PACKET_SCHEMA = "module_completion_packet_v0_3"' in text
    assert 'CANDIDATE_INTAKE_PROTOCOL = "blueprint_completion_intake_v0_3"' in text
