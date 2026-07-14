from __future__ import annotations

from pathlib import Path

import yaml

from scripts.coordination.module_completion_intake import (
    apply_intake_plan,
    build_intake_plan,
)
from scripts.coordination.resolve_next_module_work import resolve_next_work

MODULE = "logistics_service"
PROMPT_ID = "logistics_service_test_address_book_v0_1"
NEXT_STEP_ID = "logistics_service_provider_adapter_contract_v0_1"


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _blueprint_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "blueprint"
    module_root = tmp_path / MODULE

    queue = {
        "schema_version": "prompt_queue_v0_2",
        "module": MODULE,
        "prompt_queue": [
            {
                "prompt_id": PROMPT_ID,
                "sequence": 3,
                "title": "Test address book",
                "file": "approved/test-address-book.md",
                "target_module": MODULE,
                "phase": "test_address_book_v0_1",
                "priority": "high",
                "module_execution": {
                    "status": "ready_for_module_pull",
                    "completion_commit": None,
                    "completion_report": None,
                    "completed_at": None,
                },
                "blueprint_review": {
                    "status": "not_started",
                    "acceptance_commit": None,
                    "accepted_at": None,
                    "review_notes": None,
                },
            }
        ],
    }
    queue_dir = root / "coordination/outgoing_prompts" / MODULE
    _write_yaml(queue_dir / "index.yaml", queue)
    (queue_dir / "approved").mkdir(parents=True)
    (queue_dir / "approved/test-address-book.md").write_text("# Prompt\n", encoding="utf-8")
    (queue_dir / "drafts").mkdir()

    roadmap = {
        "schema_version": "module_development_roadmap_v0_1",
        "module": MODULE,
        "metadata": {
            "module": MODULE,
            "current_step_id": PROMPT_ID,
            "updated_at": "2026-07-13",
        },
        "status_values": [
            "planned",
            "ready",
            "active",
            "completed",
            "accepted",
            "paused",
            "blocked",
            "deferred",
            "cancelled",
            "superseded",
        ],
        "priority_values": ["critical", "high", "normal", "low", "reference"],
        "roadmap": [
            {
                "sequence": 3,
                "step_id": PROMPT_ID,
                "title": "Test address book",
                "status": "active",
                "priority": "high",
                "owner_module": MODULE,
                "depends_on": [],
                "evidence": {},
                "expected_outputs": ["fixtures"],
            },
            {
                "sequence": 4,
                "step_id": NEXT_STEP_ID,
                "title": "Provider adapter contract",
                "status": "planned",
                "priority": "high",
                "owner_module": MODULE,
                "depends_on": [PROMPT_ID],
                "evidence": {},
                "summary": "Define a provider-neutral adapter contract.",
                "expected_outputs": ["adapter protocol", "dry-run contract"],
            },
        ],
    }
    _write_yaml(root / "coordination/roadmaps/logistics_service.yaml", roadmap)

    report = module_root / "coordination/reports/completion/test_completion.md"
    report.parent.mkdir(parents=True)
    report.write_text("# Completion\n", encoding="utf-8")
    reports_dir = module_root / "reports"
    reports_dir.mkdir()
    (reports_dir / "logistics_service_check_report.md").write_text(
        "# Check report\n",
        encoding="utf-8",
    )

    packet = {
        "completion_id": "test_completed",
        "module_id": MODULE,
        "module_name": "ForPrint Logistics Service",
        "phase": "test_address_book_v0_1",
        "prompt_id": PROMPT_ID,
        "report_id": "test_completion",
        "report_path": "coordination/reports/completion/test_completion.md",
        "created_at": "2026-07-13T23:17:47+03:00",
        "branch": "feature/test",
        "implementation_commit": "1" * 40,
        "push_status": "pushed",
        "summary": "Completed",
        "implemented": ["Done"],
        "checks": {
            "check_report": "ok",
            "tests": "ok",
            "governance_check": "ok",
            "test_count": 77,
            "check_report_passed": 9,
            "check_report_warnings": 0,
            "check_report_failed": 0,
        },
        "boundary_confirmation": {
            "live_provider_writes_added": False,
            "real_provider_credentials_committed": False,
            "blueprint_repository_written_directly": False,
        },
    }
    packet_path = module_root / "coordination/completion_packets/records/test.yaml"
    _write_yaml(packet_path, packet)

    return root, module_root, packet_path


def test_completion_acceptance_updates_queue_roadmap_and_review(tmp_path: Path) -> None:
    root, module_root, packet_path = _blueprint_fixture(tmp_path)

    plan = build_intake_plan(
        root=root,
        module_id=MODULE,
        module_root=module_root,
        packet=packet_path,
        decision="accepted",
        review_notes="Accepted by test.",
        completion_commit="2" * 40,
        reviewed_at="2026-07-14",
        verify_git=False,
    )

    prompt = plan.queue_data["prompt_queue"][0]
    assert prompt["module_execution"]["status"] == "completed_by_module"
    assert prompt["module_execution"]["completion_commit"] == "2" * 40
    assert prompt["blueprint_review"]["status"] == "accepted_by_blueprint"

    step = plan.roadmap_data["roadmap"][0]
    assert step["status"] == "accepted"
    assert step["evidence"]["implementation_commit"] == "1" * 40
    assert step["evidence"]["completion_commit"] == "2" * 40
    assert step["evidence"]["check_report"] == "reports/logistics_service_check_report.md"

    assert plan.review_data["decision"] == "accepted"
    assert len(plan.changed_paths) == 3


def test_completion_acceptance_is_idempotent(tmp_path: Path) -> None:
    root, module_root, packet_path = _blueprint_fixture(tmp_path)

    first = build_intake_plan(
        root=root,
        module_id=MODULE,
        module_root=module_root,
        packet=packet_path,
        decision="accepted",
        review_notes="Accepted by test.",
        completion_commit="2" * 40,
        reviewed_at="2026-07-14",
        verify_git=False,
    )
    apply_intake_plan(first)

    second = build_intake_plan(
        root=root,
        module_id=MODULE,
        module_root=module_root,
        packet=packet_path,
        decision="accepted",
        review_notes="Accepted by test.",
        completion_commit="2" * 40,
        reviewed_at="2026-07-14",
        verify_git=False,
    )
    assert second.changed_paths == ()


def test_return_for_fix_keeps_roadmap_step_active(tmp_path: Path) -> None:
    root, module_root, packet_path = _blueprint_fixture(tmp_path)

    plan = build_intake_plan(
        root=root,
        module_id=MODULE,
        module_root=module_root,
        packet=packet_path,
        decision="returned_for_fix",
        review_notes="Correct one boundary.",
        completion_commit="2" * 40,
        reviewed_at="2026-07-14",
        verify_git=False,
    )

    prompt = plan.queue_data["prompt_queue"][0]
    assert prompt["module_execution"]["status"] == "returned_for_fix"
    assert prompt["blueprint_review"]["status"] == "returned_for_fix"
    assert plan.roadmap_data["roadmap"][0]["status"] == "active"


def test_next_work_uses_roadmap_when_no_draft_exists(tmp_path: Path) -> None:
    root, module_root, packet_path = _blueprint_fixture(tmp_path)
    del module_root, packet_path

    queue_path = root / "coordination/outgoing_prompts/logistics_service/index.yaml"
    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    queue["prompt_queue"][0]["module_execution"]["status"] = "completed_by_module"
    queue["prompt_queue"][0]["blueprint_review"]["status"] = "accepted_by_blueprint"
    _write_yaml(queue_path, queue)

    roadmap_path = root / "coordination/roadmaps/logistics_service.yaml"
    roadmap = yaml.safe_load(roadmap_path.read_text(encoding="utf-8"))
    roadmap["roadmap"][0]["status"] = "accepted"
    _write_yaml(roadmap_path, roadmap)

    suggestion = resolve_next_work(root=root, module=MODULE)
    assert suggestion.result == "ROADMAP_PROMPT_NEEDED"
    assert suggestion.next_step is not None
    assert suggestion.next_step["step_id"] == NEXT_STEP_ID


def test_next_work_finds_matching_draft(tmp_path: Path) -> None:
    root, module_root, packet_path = _blueprint_fixture(tmp_path)
    del module_root, packet_path

    queue_path = root / "coordination/outgoing_prompts/logistics_service/index.yaml"
    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    queue["prompt_queue"][0]["module_execution"]["status"] = "completed_by_module"
    _write_yaml(queue_path, queue)

    roadmap_path = root / "coordination/roadmaps/logistics_service.yaml"
    roadmap = yaml.safe_load(roadmap_path.read_text(encoding="utf-8"))
    roadmap["roadmap"][0]["status"] = "accepted"
    _write_yaml(roadmap_path, roadmap)

    draft = (
        root
        / "coordination/outgoing_prompts/logistics_service/drafts"
        / "2026-07-14__logistics_service__provider_adapter_contract_v0_1.md"
    )
    draft.write_text(f"# Draft\n\nPrompt ID: `{NEXT_STEP_ID}`\n", encoding="utf-8")

    suggestion = resolve_next_work(root=root, module=MODULE)
    assert suggestion.result == "DRAFT_CANDIDATE_FOUND"
    assert suggestion.draft_candidates == (draft,)


def test_active_prompt_has_priority_over_drafts_and_roadmap(tmp_path: Path) -> None:
    root, module_root, packet_path = _blueprint_fixture(tmp_path)
    del module_root, packet_path

    suggestion = resolve_next_work(root=root, module=MODULE)
    assert suggestion.result == "ACTIVE_PROMPT_EXISTS"
    assert len(suggestion.active_prompts) == 1
    assert suggestion.decision_required is False
