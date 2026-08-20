from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from scripts.coordination import accept_and_advance_v0_1 as h5
from scripts.coordination import review_roadmap_queue_transaction_v0_4 as review_tx


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def fixture_state(
    tmp_path: Path,
    *,
    authorized: bool,
) -> dict[str, Path]:
    root = tmp_path
    roadmap = root / "coordination/roadmaps/demo.yaml"
    queue = root / "coordination/outgoing_prompts/demo/index.yaml"
    approved = (
        root
        / "coordination/outgoing_prompts/demo/approved/demo_prompt.md"
    )
    draft = (
        root
        / "coordination/outgoing_prompts/demo/drafts/"
        "2026-08-20__demo_next__demo_next_prompt_v0_1.md"
    )

    write_yaml(
        roadmap,
        {
            "schema_version": "module_development_roadmap_v0_1",
            "module": "demo",
            "metadata": {
                "current_step_id": "demo_prompt",
                "updated_at": "2026-08-20",
            },
            "roadmap": [
                {
                    "sequence": 1,
                    "step_id": "demo_prompt",
                    "title": "Demo current",
                    "status": "active",
                    "priority": "critical",
                    "owner_module": "demo",
                    "depends_on": [],
                    "expected_outputs": [],
                    "evidence": {
                        "blueprint_review_status": "not_started",
                    },
                },
                {
                    "sequence": 2,
                    "step_id": "demo_next",
                    "title": "Demo next",
                    "status": "planned",
                    "priority": "high",
                    "owner_module": "demo",
                    "depends_on": [
                        {
                            "type": "module_step",
                            "module": "demo",
                            "step_id": "demo_prompt",
                            "status": "pending",
                        }
                    ],
                    "expected_outputs": [],
                    "evidence": {},
                },
            ],
        },
    )

    write_yaml(
        queue,
        {
            "schema_version": "prompt_queue_v0_2",
            "module": "demo",
            "prompt_queue": [
                {
                    "prompt_id": "demo_prompt",
                    "sequence": 1,
                    "title": "Demo current",
                    "file": "approved/demo_prompt.md",
                    "target_module": "demo",
                    "phase": "demo_current",
                    "priority": "critical",
                    "module_execution": {
                        "status": "completed_by_module",
                        "completion_commit": "abc",
                        "completion_report": "report.md",
                        "completed_at": "2026-08-20",
                    },
                    "blueprint_review": {
                        "status": "not_started",
                        "acceptance_commit": None,
                        "accepted_at": None,
                        "review_notes": None,
                    },
                }
            ],
        },
    )

    approved.parent.mkdir(parents=True, exist_ok=True)
    approved.write_text(
        "---\n"
        "prompt_id: demo_prompt\n"
        "status: approved\n"
        "---\n"
        "# Demo current\n",
        encoding="utf-8",
    )

    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(
        "---\n"
        "schema_version: outgoing_prompt_artifact_v0_1\n"
        "prompt_id: demo_next_prompt_v0_1\n"
        "target_module: demo\n"
        "title: Demo next prompt\n"
        "phase: demo_next\n"
        "priority: high\n"
        'created_at: "2026-08-20"\n'
        "source_change: governance/h5-test\n"
        "lifecycle_state: prepared\n"
        "prepared_at: '2026-08-20T14:00:00Z'\n"
        "prepared_from_sha256: "
        + "d" * 64
        + "\n"
        "lineage:\n"
        "  supersedes: null\n"
        "roadmap_step_id: demo_next\n"
        "---\n"
        "# Demo next\n\n"
        "Implements roadmap step demo_next.\n",
        encoding="utf-8",
    )

    write_yaml(
        root / "machine/modules.yaml",
        {
            "modules": [
                {"id": "demo", "title": "Demo"},
            ]
        },
    )

    evidence_rel = (
        "coordination/internal_work/blueprint/governance/"
        "test_prompt_release_authorization.yaml"
    )
    write_yaml(
        root
        / "coordination/standards/governance/"
        "outgoing_prompt_release_policy_v0_1.yaml",
        {
            "schema_version": "outgoing_prompt_release_policy_v0_1",
            "release": {
                "global_enabled": False,
                "authorized_modules": ["demo"] if authorized else [],
                "authorization_evidence": (
                    evidence_rel if authorized else None
                ),
            },
        },
    )
    if authorized:
        write_yaml(root / evidence_rel, {"result": "TEST_AUTHORIZATION"})

    return {
        "root": root,
        "roadmap": roadmap,
        "queue": queue,
        "approved": approved,
        "draft": draft,
    }


def review_request(paths: dict[str, Path]) -> dict:
    root = paths["root"]
    return {
        "schema_version": (
            "blueprint_review_roadmap_queue_transaction_request_v0_4"
        ),
        "review_candidate": {
            "module_id": "demo",
            "prompt_id": "demo_prompt",
            "event_id": "event_demo_h5",
            "event_path": (
                "coordination/completion_outbox/records/"
                "event_demo_h5.yaml"
            ),
            "event_sha256": "a" * 64,
            "packet_path": (
                "coordination/completion_packets/records/"
                "packet_demo_h5.yaml"
            ),
            "packet_sha256": "b" * 64,
            "intake_state": "READY_FOR_BLUEPRINT_REVIEW",
            "operator_decision_created": False,
            "discovery_fingerprint_sha256": "c" * 64,
        },
        "decision": {
            "decision_id": "decision_demo_h5",
            "operator_decision": "ACCEPT",
            "explicit_operator_input": True,
            "decided_at": "2026-08-20T17:00:00+03:00",
            "review_notes": "explicit H5 ACCEPT",
        },
        "targets": {
            "roadmap_path": str(paths["roadmap"].relative_to(root)),
            "prompt_queue_path": str(paths["queue"].relative_to(root)),
            "prompt_path": str(paths["approved"].relative_to(root)),
            "review_evidence_path": (
                "coordination/review_packets/demo/processed/"
                "decision_demo_h5.yaml"
            ),
            "roadmap_step_id": "demo_prompt",
        },
        "preconditions": {
            "roadmap_sha256": review_tx.file_sha256(paths["roadmap"]),
            "prompt_queue_sha256": review_tx.file_sha256(paths["queue"]),
            "prompt_sha256": review_tx.file_sha256(paths["approved"]),
        },
    }


def operation_request(
    paths: dict[str, Path],
    *,
    mode: str,
) -> dict:
    advance: dict = {"mode": mode}
    if mode == "release_explicit_prompt":
        advance.update(
            {
                "explicit_operator_input": True,
                "expected_roadmap_step_id": "demo_next",
                "expected_prompt_id": "demo_next_prompt_v0_1",
            }
        )
    return {
        "schema_version": "blueprint_accept_and_advance_request_v0_1",
        "operation_id": "accept_and_advance_demo_h5",
        "operated_at": "2026-08-20T17:01:00+03:00",
        "explicit_operator_input": True,
        "review_transaction": review_request(paths),
        "advance": advance,
    }


def authorize_release(paths: dict[str, Path]) -> None:
    root = paths["root"]
    evidence_rel = (
        "coordination/internal_work/blueprint/governance/"
        "test_prompt_release_authorization.yaml"
    )
    write_yaml(
        root
        / "coordination/standards/governance/"
        "outgoing_prompt_release_policy_v0_1.yaml",
        {
            "schema_version": "outgoing_prompt_release_policy_v0_1",
            "release": {
                "global_enabled": False,
                "authorized_modules": ["demo"],
                "authorization_evidence": evidence_rel,
            },
        },
    )
    write_yaml(root / evidence_rel, {"result": "TEST_AUTHORIZATION"})


def test_prepare_is_read_only_and_rejects_non_accept(
    tmp_path: Path,
) -> None:
    paths = fixture_state(tmp_path, authorized=True)
    request = operation_request(paths, mode="suggest_only")

    before = {
        key: path.read_bytes()
        for key, path in paths.items()
        if key != "root" and path.is_file()
    }
    plan = h5.prepare_operation(paths["root"], request)

    assert plan["result_state"] == "READY_TO_APPLY"
    assert (
        plan["advance"]["preview_state"]
        == "AFTER_ACCEPT_REEVALUATION_REQUIRED"
    )
    for key, payload in before.items():
        assert paths[key].read_bytes() == payload

    bad = copy.deepcopy(request)
    bad["review_transaction"]["decision"]["operator_decision"] = "HOLD"
    with pytest.raises(
        h5.AcceptAndAdvanceError,
        match="only accepts an explicit ACCEPT",
    ):
        h5.prepare_operation(paths["root"], bad)


def test_suggest_only_applies_accept_without_release(
    tmp_path: Path,
) -> None:
    paths = fixture_state(tmp_path, authorized=False)
    request = operation_request(paths, mode="suggest_only")

    result = h5.apply_operation(
        paths["root"],
        request,
        operator_confirmation="accept_and_advance_demo_h5",
    )

    assert result["result_state"] == "ACCEPT_AND_SUGGEST_APPLIED"
    assert result["review_result"]["result_state"] == "ACCEPT_APPLIED"
    assert result["advance"]["result"] == "SUGGESTED"
    assert result["advance"]["next_work"]["result"] == "DRAFT_CANDIDATE_FOUND"

    roadmap = load(paths["roadmap"])
    queue = load(paths["queue"])
    assert roadmap["roadmap"][0]["status"] == "accepted"
    assert roadmap["roadmap"][1]["status"] == "planned"
    assert (
        queue["prompt_queue"][0]["blueprint_review"]["status"]
        == "accepted_by_blueprint"
    )
    assert paths["draft"].is_file()

    evidence = paths["root"] / result["evidence_path"]
    assert evidence.is_file()


def test_release_mode_accepts_and_activates_explicit_candidate(
    tmp_path: Path,
) -> None:
    paths = fixture_state(tmp_path, authorized=True)
    request = operation_request(
        paths,
        mode="release_explicit_prompt",
    )

    result = h5.apply_operation(
        paths["root"],
        request,
        operator_confirmation="accept_and_advance_demo_h5",
    )

    assert result["result_state"] == "ACCEPT_AND_ADVANCE_APPLIED"
    assert result["advance"]["result"] == "ACTIVATED"
    assert result["advance"]["next_prompt_selection_performed"] is True
    assert result["advance"]["next_prompt_activation_performed"] is True

    roadmap = load(paths["roadmap"])
    next_step = roadmap["roadmap"][1]
    assert roadmap["metadata"]["current_step_id"] == "demo_next"
    assert next_step["status"] == "active"
    assert next_step["prompt_id"] == "demo_next_prompt_v0_1"

    unresolved = h5._unresolved_queue_records(paths["root"], "demo")
    assert unresolved == [
        {
            "prompt_id": "demo_next_prompt_v0_1",
            "module_execution_status": "ready_for_module_pull",
            "blueprint_review_status": "not_started",
        }
    ]
    assert not paths["draft"].exists()


def test_gated_release_preserves_accept_and_retry_can_advance(
    tmp_path: Path,
) -> None:
    paths = fixture_state(tmp_path, authorized=False)
    request = operation_request(
        paths,
        mode="release_explicit_prompt",
    )

    blocked = h5.apply_operation(
        paths["root"],
        request,
        operator_confirmation="accept_and_advance_demo_h5",
    )

    assert (
        blocked["result_state"]
        == "ACCEPT_APPLIED_ADVANCE_BLOCKED"
    )
    assert (
        blocked["advance"]["code"]
        == "RELEASE_POLICY_OR_WORKFLOW_BLOCKED"
    )
    assert load(paths["roadmap"])["roadmap"][0]["status"] == "accepted"
    assert paths["draft"].is_file()
    evidence = (
        paths["root"]
        / "coordination/internal_work/blueprint/governance/"
        "accept_and_advance/accept_and_advance_demo_h5.yaml"
    )
    assert not evidence.exists()

    authorize_release(paths)

    retried = h5.apply_operation(
        paths["root"],
        request,
        operator_confirmation="accept_and_advance_demo_h5",
    )
    assert retried["result_state"] == "ACCEPT_AND_ADVANCE_APPLIED"
    assert retried["review_result"]["result_state"] == "ALREADY_APPLIED"
    assert evidence.is_file()


def test_unresolved_other_prompt_blocks_wip_advance(
    tmp_path: Path,
) -> None:
    paths = fixture_state(tmp_path, authorized=True)
    queue = load(paths["queue"])
    queue["prompt_queue"].append(
        {
            "prompt_id": "other_blocked_prompt",
            "sequence": 2,
            "title": "Other blocked",
            "file": "approved/other_blocked.md",
            "target_module": "demo",
            "phase": "other_blocked",
            "priority": "high",
            "module_execution": {
                "status": "blocked",
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
    )
    write_yaml(paths["queue"], queue)

    request = operation_request(
        paths,
        mode="release_explicit_prompt",
    )
    request["review_transaction"]["preconditions"][
        "prompt_queue_sha256"
    ] = review_tx.file_sha256(paths["queue"])

    result = h5.apply_operation(
        paths["root"],
        request,
        operator_confirmation="accept_and_advance_demo_h5",
    )

    assert result["result_state"] == "ACCEPT_APPLIED_ADVANCE_BLOCKED"
    assert result["advance"]["code"] == "UNRESOLVED_PROMPT_EXISTS"
    assert paths["draft"].is_file()


def test_confirmation_and_operation_identity_are_fail_closed(
    tmp_path: Path,
) -> None:
    paths = fixture_state(tmp_path, authorized=False)
    request = operation_request(paths, mode="suggest_only")

    with pytest.raises(
        h5.AcceptAndAdvanceError,
        match="must exactly match operation_id",
    ):
        h5.apply_operation(
            paths["root"],
            request,
            operator_confirmation="wrong",
        )

    first = h5.apply_operation(
        paths["root"],
        request,
        operator_confirmation="accept_and_advance_demo_h5",
    )
    assert first["result_state"] == "ACCEPT_AND_SUGGEST_APPLIED"

    changed = copy.deepcopy(request)
    changed["operated_at"] = "2026-08-20T17:02:00+03:00"
    with pytest.raises(
        h5.AcceptAndAdvanceError,
        match="different request identity",
    ):
        h5.apply_operation(
            paths["root"],
            changed,
            operator_confirmation="accept_and_advance_demo_h5",
        )


def test_h5_does_not_implement_h6_default_ranking() -> None:
    source = (
        Path(__file__).resolve().parents[2]
        / "scripts/coordination/accept_and_advance_v0_1.py"
    ).read_text(encoding="utf-8")

    assert "release_explicit_prompt" in source
    assert "expected_roadmap_step_id" in source
    assert "expected_prompt_id" in source
    assert "PRIORITY_ORDER" not in source
    assert "_sort_key" not in source
    assert "next_prompt_selection_activation_v0_4" not in source

def test_compound_evidence_write_failure_rolls_back_to_post_accept(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = fixture_state(tmp_path, authorized=True)
    request = operation_request(
        paths,
        mode="release_explicit_prompt",
    )

    original_writer = h5._atomic_write_yaml

    def fail_compound_evidence(path: Path, data: dict) -> None:
        if "accept_and_advance" in path.parts:
            raise OSError("simulated compound evidence write failure")
        original_writer(path, data)

    monkeypatch.setattr(
        h5,
        "_atomic_write_yaml",
        fail_compound_evidence,
    )

    blocked = h5.apply_operation(
        paths["root"],
        request,
        operator_confirmation="accept_and_advance_demo_h5",
    )

    assert (
        blocked["result_state"]
        == "ACCEPT_APPLIED_ADVANCE_BLOCKED"
    )
    assert (
        blocked["advance"]["code"]
        == "COMPOUND_EVIDENCE_WRITE_FAILED"
    )

    roadmap = load(paths["roadmap"])
    queue = load(paths["queue"])

    assert roadmap["roadmap"][0]["status"] == "accepted"
    assert roadmap["roadmap"][1]["status"] == "planned"
    assert roadmap["metadata"]["current_step_id"] == "demo_prompt"
    assert paths["draft"].is_file()
    assert not any(
        row.get("prompt_id") == "demo_next_prompt_v0_1"
        for row in queue["prompt_queue"]
    )

    compound_evidence = (
        paths["root"]
        / "coordination/internal_work/blueprint/governance/"
        "accept_and_advance/accept_and_advance_demo_h5.yaml"
    )
    assert not compound_evidence.exists()

    monkeypatch.setattr(
        h5,
        "_atomic_write_yaml",
        original_writer,
    )

    retried = h5.apply_operation(
        paths["root"],
        request,
        operator_confirmation="accept_and_advance_demo_h5",
    )
    assert retried["result_state"] == "ACCEPT_AND_ADVANCE_APPLIED"
    assert retried["review_result"]["result_state"] == "ALREADY_APPLIED"
    assert compound_evidence.is_file()

