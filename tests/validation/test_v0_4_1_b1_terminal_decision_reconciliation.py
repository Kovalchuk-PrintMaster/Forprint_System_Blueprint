from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from scripts.coordination import completion_discovery_and_intake_v0_4 as discovery


def _write_fixture(
    root: Path,
    *,
    event_id: str,
    completion_id: str,
) -> tuple[Path, dict, tuple[str, ...]]:
    module_id = "demo_module"
    repository_id = "demo_repository"
    prompt_id = "prompt_demo"

    packet_rel = (
        Path("coordination/completion_packets/records")
        / f"{completion_id}.yaml"
    )
    packet_path = root / packet_rel
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet = {
        "schema_version": "module_completion_packet_v0_4",
        "completion_id": completion_id,
        "module_id": module_id,
        "prompt_id": prompt_id,
    }
    packet_path.write_text(
        yaml.safe_dump(packet, sort_keys=False),
        encoding="utf-8",
    )
    packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()

    event_rel = (
        Path("coordination/completion_outbox/records")
        / f"{event_id}.yaml"
    )
    event_path = root / event_rel
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": "module_completion_outbox_event_v0_4",
        "event_id": event_id,
        "module_id": module_id,
        "repository_id": repository_id,
        "prompt_id": prompt_id,
        "completion_id": completion_id,
        "emitted_at": "2026-08-24T13:00:00+03:00",
        "completion_packet": {
            "path": packet_rel.as_posix(),
            "sha256": packet_sha,
        },
    }
    event_path.write_text(
        yaml.safe_dump(event, sort_keys=False),
        encoding="utf-8",
    )
    event_sha = hashlib.sha256(event_path.read_bytes()).hexdigest()

    module = {
        "module_id": module_id,
        "repository": {
            "repository_id": repository_id,
        },
        "sources": {
            "completion_outbox": {
                "availability": "present",
                "path": "coordination/completion_outbox/records",
            },
        },
    }
    subject_key = (
        module_id,
        prompt_id,
        event_id,
        event_rel.as_posix(),
        event_sha,
        packet_rel.as_posix(),
        packet_sha,
    )
    return root, module, subject_key


def _passed(*_args, **_kwargs) -> dict:
    return {
        "result": "PASSED",
        "errors": [],
        "warnings": [],
    }


def test_exact_terminal_decision_bypasses_current_context_revalidation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo, module, subject_key = _write_fixture(
        tmp_path / "module",
        event_id="event_terminal_exact",
        completion_id="completion_terminal_exact",
    )

    def forbidden_queue_lookup(*_args, **_kwargs):
        raise AssertionError(
            "current queue binding must not be consulted for exact "
            "terminal decision subject"
        )

    monkeypatch.setattr(
        discovery,
        "_queue_prompt_contract_binding",
        forbidden_queue_lookup,
    )

    decision_index = {
        subject_key: {
            "evidence_path": (
                "coordination/review_packets/demo_module/processed/"
                "terminal_exact.yaml"
            ),
            "decision_id": "terminal_exact",
            "operator_decision": "ACCEPT",
            "result": "ACCEPTED",
        }
    }

    result = discovery._discover_module(
        module=module,
        blueprint_root=tmp_path / "blueprint",
        registry_path=tmp_path / "registry.yaml",
        repository_root=repo,
        outbox_validator=_passed,
        packet_validator=_passed,
        decision_index=decision_index,
    )

    assert len(result["events"]) == 1
    event = result["events"][0]
    assert event["classification"] == "ready_for_blueprint_review"
    marker = event["terminal_decision_reconciliation"]
    assert marker["processed_decision_found"] is True
    assert marker["current_context_revalidation_skipped"] is True
    assert marker["reason"] == "exact_terminal_operator_decision_subject"
    assert marker["operator_decision"] == "ACCEPT"


def test_nonexact_terminal_decision_does_not_bypass_queue_validation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo, module, subject_key = _write_fixture(
        tmp_path / "module",
        event_id="event_terminal_nonexact",
        completion_id="completion_terminal_nonexact",
    )

    nonexact_key = tuple(
        "f" * 64 if index == 6 else value
        for index, value in enumerate(subject_key)
    )
    decision_index = {
        nonexact_key: {
            "evidence_path": (
                "coordination/review_packets/demo_module/processed/"
                "terminal_nonexact.yaml"
            ),
            "decision_id": "terminal_nonexact",
            "operator_decision": "ACCEPT",
            "result": "ACCEPTED",
        }
    }

    monkeypatch.setattr(
        discovery,
        "_queue_prompt_contract_binding",
        lambda *_args, **_kwargs: (
            {
                "schema_version": "module_prompt_contract_v0_4",
                "contract_id": "current_contract",
                "path": "current.yaml",
                "file_sha256": "1" * 64,
                "payload_sha256": "2" * 64,
                "source_prompt_sha256": "3" * 64,
            },
            [],
        ),
    )
    monkeypatch.setattr(
        discovery,
        "_packet_queue_contract_errors",
        lambda *_args, **_kwargs: [
            "synthetic current queue binding mismatch"
        ],
    )

    result = discovery._discover_module(
        module=module,
        blueprint_root=tmp_path / "blueprint",
        registry_path=tmp_path / "registry.yaml",
        repository_root=repo,
        outbox_validator=_passed,
        packet_validator=_passed,
        decision_index=decision_index,
    )

    assert len(result["events"]) == 1
    event = result["events"][0]
    assert event["classification"] == "invalid_completion_packet"
    assert "terminal_decision_reconciliation" not in event
    assert event["packet_validation"]["errors"] == [
        "synthetic current queue binding mismatch"
    ]
