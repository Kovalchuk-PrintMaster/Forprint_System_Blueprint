from __future__ import annotations

import copy
import importlib
from pathlib import Path

import pytest

from scripts.coordination.assistant_handoff_v2_freshness_resume_v0_1 import (
    validate_resume,
)
from scripts.coordination.assistant_handoff_v2_result_v0_1 import (
    validate_result_envelope,
)

ROOT = Path(__file__).resolve().parents[4]
EXPECTED_MODULE = (
    ROOT / "scripts/coordination/control_plane/worker_runtime/"
    "s4_result_composer_v0_1.py"
)
ATTEMPT = "cf10-u180j-a999"
HASH = "b" * 64
SOURCE_FINGERPRINT = "2" * 64


def _composer():
    assert EXPECTED_MODULE.is_file(), (
        "TESTS-FIRST RED: isolated Stage 4A composer is not yet implemented"
    )
    return importlib.import_module(
        "scripts.coordination.control_plane.worker_runtime.s4_result_composer_v0_1"
    )


def _origin():
    cursor = {
        "roadmap_sync": "IN_SYNC",
        "roadmap_status": (
            "ROADMAP_STATUS=control_foundation_near_horizon:"
            "previous=CF-09:current=CF-10:next=CF-11:ready=CF-11"
        ),
        "open_work": {"u180j": {"state": "ACTIVE", "sequence": 67}},
        "lifecycle_status_sha256": "3" * 64,
        "roadmap_status_sha256": "4" * 64,
    }
    context = {
        "schema_version": "forprint_governed_worker_context_projection_v0_1",
        "handoff_manifest_sha256": HASH,
        "handoff_source_state_fingerprint": SOURCE_FINGERPRINT,
        "lifecycle_roadmap_cursor": cursor,
        "execution_bindings": {"attempt_id": ATTEMPT},
        "authority": {
            "context_grants_authority": False,
            "dispatch_authority_granted": False,
            "release_authority_granted": False,
            "cross_repository_write_authority_granted": False,
        },
    }
    origin_manifest = {"handoff_manifest_sha256": HASH}
    return origin_manifest, context


def _completion(status="PASS"):
    completion = {
        "status": status,
        "changed_paths": ["tests/validation/test_validation_suite_runner_v0_1.py"],
        "validation_evidence": [
            {"name": "blueprint-continuity-planning", "result": "PASS"}
        ],
        "self_repair_attempts": [],
        "unresolved_findings": [],
    }
    if status == "PARTIAL":
        completion["partial_resume"] = {
            "latest_completed_node": "post-worker-validation",
            "latest_accepted_ref": "fixture-verified-work",
            "replay_forbidden_refs": ["fixture-verified-work"],
        }
    return completion


def _compose(origin, context, completion, attempt=ATTEMPT):
    return _composer().compose_s4_result_candidate(
        origin_manifest=origin,
        governed_worker_context=context,
        expected_attempt_id=attempt,
        worker_completion=completion,
    )


def _must_reject(origin, context, completion, attempt=ATTEMPT):
    composer = _composer()
    with pytest.raises(composer.S4ResultComposerError):
        composer.compose_s4_result_candidate(
            origin_manifest=origin,
            governed_worker_context=context,
            expected_attempt_id=attempt,
            worker_completion=completion,
        )


def test_cf10_stage4a_pass_composes_frozen_origin_and_validates() -> None:
    origin, context = _origin()
    facts = _completion()
    result = _compose(origin, context, facts)
    assert set(result) == {
        "schema_version", "handoff_manifest_sha256", "attempt_id",
        "status", "changed_paths", "validation_evidence",
        "self_repair_attempts", "resume_coordinates", "unresolved_findings",
    }
    assert result["schema_version"] == "forprint_assistant_handoff_v2_result_v0_1"
    assert result["attempt_id"] == ATTEMPT
    assert result["handoff_manifest_sha256"] == HASH
    assert result["resume_coordinates"] == {
        "attempt_id": ATTEMPT,
        "handoff_manifest_sha256": HASH,
        "source_state_fingerprint": SOURCE_FINGERPRINT,
        "lifecycle_roadmap_cursor": context["lifecycle_roadmap_cursor"],
    }
    for field in facts:
        assert result[field] == facts[field]
    assert validate_result_envelope(result, origin, root=ROOT) == []
    assert validate_resume(result, {
        "source_state_fingerprint": SOURCE_FINGERPRINT,
        "lifecycle_roadmap_cursor": context["lifecycle_roadmap_cursor"],
    }) == []


def test_cf10_stage4a_partial_composes_only_worker_owned_extensions() -> None:
    origin, context = _origin()
    completion = _completion("PARTIAL")
    result = _compose(origin, context, completion)
    assert result["status"] == "PARTIAL"
    assert result["resume_coordinates"]["latest_completed_node"] == "post-worker-validation"
    assert result["resume_coordinates"]["latest_accepted_ref"] == "fixture-verified-work"
    assert result["resume_coordinates"]["replay_forbidden_refs"] == ["fixture-verified-work"]
    assert "partial_resume" not in result
    assert validate_result_envelope(result, origin, root=ROOT) == []
    assert validate_resume(result, {
        "source_state_fingerprint": SOURCE_FINGERPRINT,
        "lifecycle_roadmap_cursor": context["lifecycle_roadmap_cursor"],
    }) == []


def test_cf10_stage4a_pure_composition_does_not_alias_origin_or_worker_facts() -> None:
    origin, context = _origin()
    completion = _completion()
    frozen_inputs = copy.deepcopy((origin, context, completion))
    result = _compose(origin, context, completion)
    assert (origin, context, completion) == frozen_inputs
    result["resume_coordinates"]["lifecycle_roadmap_cursor"]["roadmap_status_sha256"] = "9" * 64
    result["changed_paths"].append("scripts/other.py")
    assert context["lifecycle_roadmap_cursor"]["roadmap_status_sha256"] == "4" * 64
    assert completion["changed_paths"] == ["tests/validation/test_validation_suite_runner_v0_1.py"]


def test_cf10_stage4a_rejects_mismatched_attempt_binding() -> None:
    origin, context = _origin()
    _must_reject(origin, context, _completion(), attempt="cf10-u180j-a998")


@pytest.mark.parametrize("injected", [
    "attempt_id", "handoff_manifest_sha256", "source_state_fingerprint",
    "lifecycle_roadmap_cursor", "resume_coordinates", "schema_version", "origin_manifest",
])
def test_cf10_stage4a_rejects_worker_owned_origin_spoofing(injected: str) -> None:
    origin, context = _origin()
    completion = _completion()
    completion[injected] = "a" * 64
    _must_reject(origin, context, completion)


@pytest.mark.parametrize("mutator", [
    lambda v: v.update(validation_evidence=[]),
    lambda v: v.update(changed_paths=["src/x.py", "src/x.py"]),
    lambda v: v.update(changed_paths=["../escape.py"]),
    lambda v: v.update(unexpected_parameter="worker-invented"),
])
def test_cf10_stage4a_rejects_invalid_worker_completion(mutator) -> None:
    origin, context = _origin()
    completion = _completion()
    mutator(completion)
    _must_reject(origin, context, completion)


@pytest.mark.parametrize("mutator", [
    lambda origin, context: context.update(schema_version="not-governed"),
    lambda origin, context: origin.update(handoff_manifest_sha256="f" * 64),
    lambda origin, context: context.pop("lifecycle_roadmap_cursor"),
    lambda origin, context: context["execution_bindings"].update(attempt_id="cf10-u180j-a998"),
])
def test_cf10_stage4a_rejects_invalid_or_unbound_origin(mutator) -> None:
    origin, context = _origin()
    mutator(origin, context)
    _must_reject(origin, context, _completion())


@pytest.mark.parametrize("mutator", [
    lambda v: v.pop("partial_resume"),
    lambda v: v["partial_resume"].update(latest_accepted_ref=""),
    lambda v: v["partial_resume"].update(replay_forbidden_refs=[]),
])
def test_cf10_stage4a_rejects_incomplete_partial_resume(mutator) -> None:
    origin, context = _origin()
    completion = _completion("PARTIAL")
    mutator(completion)
    _must_reject(origin, context, completion)
