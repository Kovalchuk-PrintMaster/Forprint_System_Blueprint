from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from scripts.coordination.control_plane.completion.human_gate import (
    project_human_acceptance_gate,
)
from scripts.coordination.control_plane.completion.inspector import (
    RESULT_SCHEMA,
    build_inspector_request,
    validate_inspector_result,
    write_inspector_request,
)
from scripts.coordination.control_plane.completion.intake import (
    normalize_completion_intake,
    write_normalized_completion,
)
from scripts.coordination.control_plane.completion.q5_completion import (
    validate_completion_publication_event,
)
from scripts.coordination.control_plane.events import Q5_REQUIRED_FIELDS


def _write(path: Path, data: dict) -> Path:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _chain(tmp_path: Path):
    capture = _write(
        tmp_path / "capture.yaml",
        {
            "schema_version": "forprint_worker_completion_capture_v0_1",
            "state": "COMPLETED",
            "identity": {
                "module_id": "logistics_service",
                "prompt_id": "prompt-1",
                "worker_invocation_id": "inv-1",
                "dispatch_intent_id": "dispatch-1",
                "launch_request_id": "launch-1",
                "task_context_fingerprint_sha256": "a" * 64,
            },
            "module_head_before": "head-before",
            "module_head_after": "head-after",
        },
    )
    invocation = _write(
        tmp_path / "invocation.yaml",
        {
            "schema_version": "forprint_worker_invocation_v0_1",
            "invocation_id": "inv-1",
            "identity": {
                "module_id": "logistics_service",
                "prompt_id": "prompt-1",
            },
            "authority_binding": {"module_head": "head-before"},
        },
    )
    dispatch = _write(
        tmp_path / "dispatch.yaml",
        {
            "schema_version": "forprint_dispatch_intent_v0_1",
            "dispatch_intent_id": "dispatch-1",
            "identity": {
                "module_id": "logistics_service",
                "prompt_id": "prompt-1",
            },
        },
    )
    report = _write(
        tmp_path / "report.yaml",
        {
            "schema_version": "forprint_worker_completion_report_v0_1",
            "identity": {
                "module_id": "logistics_service",
                "prompt_id": "prompt-1",
            },
            "completion_capture_sha256": hashlib.sha256(capture.read_bytes()).hexdigest(),
            "changed_files": ["src/example.py"],
            "validation_evidence": [{"name": "pytest", "result": "PASS"}],
            "inventory_lineage_impact": {
                "inventory_update_required": True,
                "lineage_update_required": False,
            },
            "resource_observability": {"runtime_duration": 3.0},
            "evidence_manifest": [{"path": "evidence.txt", "sha256": "b" * 64}],
        },
    )
    return capture, report, dispatch, invocation


def _request_chain(tmp_path: Path):
    capture, report, dispatch, invocation = _chain(tmp_path)
    normalized = normalize_completion_intake(
        completion_capture_path=capture,
        completion_report_path=report,
        dispatch_intent_path=dispatch,
        worker_invocation_path=invocation,
    )
    normalized_path = write_normalized_completion(
        result=normalized, output_dir=tmp_path / "normalized"
    )
    oracle = _write(tmp_path / "oracle.yaml", {"schema_version": "oracle"})
    contract = _write(tmp_path / "contract.yaml", {"schema_version": "contract"})
    request = build_inspector_request(
        normalized_completion_path=normalized_path,
        acceptance_oracle_path=oracle,
        prompt_contract_path=contract,
    )
    request_path = write_inspector_request(result=request, output_dir=tmp_path / "requests")
    return normalized, request, request_path


def test_normalized_completion_is_not_acceptance(tmp_path: Path) -> None:
    capture, report, dispatch, invocation = _chain(tmp_path)
    result = normalize_completion_intake(
        completion_capture_path=capture,
        completion_report_path=report,
        dispatch_intent_path=dispatch,
        worker_invocation_path=invocation,
    )
    assert result.document["identity"]["module_head_before"] == "head-before"
    assert result.document["identity"]["module_head_after"] == "head-after"
    assert (
        result.document["completion"]["resource_observability"]["input_tokens"] == "not_observable"
    )
    assert result.document["semantic_boundaries"]["automatic_accept"] is False


def test_inspector_request_is_read_only_and_unbound(tmp_path: Path) -> None:
    _, request, _ = _request_chain(tmp_path)
    boundary = request.document["inspector_boundary"]
    assert boundary["read_only"] is True
    assert boundary["repository_binding"] == "UNBOUND_EXTERNAL_REVIEWER"
    assert boundary["inspector_may_blueprint_accept"] is False


def test_conformant_result_only_reaches_human_gate(tmp_path: Path) -> None:
    _, request, request_path = _request_chain(tmp_path)
    result_path = _write(
        tmp_path / "result.yaml",
        {
            "schema_version": RESULT_SCHEMA,
            "request_id": request.request_id,
            "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
            "state": "CONFORMANT",
            "identity": {
                "module_id": "logistics_service",
                "prompt_id": "prompt-1",
            },
            "findings": [],
            "authority": {
                "read_only": True,
                "module_write_performed": False,
                "worker_dispatch_performed": False,
                "blueprint_accept_performed": False,
                "next_prompt_release_performed": False,
            },
        },
    )
    assert validate_inspector_result(request_path=request_path, result_path=result_path).valid
    projection = project_human_acceptance_gate(
        inspector_request_path=request_path, inspector_result_path=result_path
    )
    assert projection["state"] == "AWAITING_HUMAN_ACCEPTANCE"
    assert projection["human_decision"]["decision"] == "NOT_DECIDED"
    assert projection["semantic_boundaries"]["inspector_conformant_is_blueprint_accept"] is False


def test_nonconformant_is_return_recommendation_only(tmp_path: Path) -> None:
    _, request, request_path = _request_chain(tmp_path)
    result_path = _write(
        tmp_path / "result.yaml",
        {
            "schema_version": RESULT_SCHEMA,
            "request_id": request.request_id,
            "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
            "state": "NON_CONFORMANT",
            "identity": {
                "module_id": "logistics_service",
                "prompt_id": "prompt-1",
            },
            "findings": [{"code": "FIX_REQUIRED"}],
            "authority": {
                "read_only": True,
                "module_write_performed": False,
                "worker_dispatch_performed": False,
                "blueprint_accept_performed": False,
                "next_prompt_release_performed": False,
            },
        },
    )
    projection = project_human_acceptance_gate(
        inspector_request_path=request_path, inspector_result_path=result_path
    )
    assert projection["state"] == "RETURN_RECOMMENDED"
    assert projection["human_decision"]["decision"] == "NOT_DECIDED"
    assert projection["semantic_boundaries"]["automatic_return"] is False


def test_q5_completion_publication_family_is_reused() -> None:
    event = {field: None for field in Q5_REQUIRED_FIELDS}
    event.update(
        {
            "event_id": "event-1",
            "event_type": "completion_publication.normalized",
            "occurred_at": "2026-09-06T00:00:00+00:00",
            "producer": "blueprint",
            "target": "blueprint",
            "correlation_id": "corr-1",
            "severity": "notice",
            "blocking": False,
            "schema_version": "completion_publication_payload_v0_1",
            "payload": {
                "normalized_completion_id": "completion-1",
                "normalized_completion_sha256": "c" * 64,
            },
            "evidence_refs": [],
            "idempotency_key": "completion-1",
        }
    )
    valid, errors = validate_completion_publication_event(event)
    assert valid is True
    assert errors == ()
