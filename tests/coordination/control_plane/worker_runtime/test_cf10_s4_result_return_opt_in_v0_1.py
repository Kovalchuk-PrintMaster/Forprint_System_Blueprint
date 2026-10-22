"""Stage 4B: explicit draft transport, frozen-origin materialization boundary.

No Worker invocation or attempt ledger mutation. Legacy full Handoff remains default.
"""
from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.worker_runtime import worker_result_return
from scripts.coordination.control_plane.worker_runtime.s4_result_composer_v0_1 import (
    compose_s4_result_candidate,
)

ROOT = Path(__file__).resolve().parents[4]
ATTEMPT = "cf10-u180j-a999"
HASH = "b" * 64
SOURCE = "2" * 64
DRAFT_MODE = "worker-completion-draft-v0-1"
LEGACY_MODE = "handoff-v2-full"
DRAFT_BEGIN = "FORPRINT_WORKER_COMPLETION_DRAFT_V0_1_BEGIN"
DRAFT_END = "FORPRINT_WORKER_COMPLETION_DRAFT_V0_1_END"
LEGACY_BEGIN = "FORPRINT_HANDOFF_V2_RESULT_BEGIN"
LEGACY_END = "FORPRINT_HANDOFF_V2_RESULT_END"


def _bridge():
    # Tests-first RED: fail before touching any result artifact if opt-in is absent.
    signature = inspect.signature(worker_result_return.materialize_worker_result)
    assert "result_transport" in signature.parameters, (
        "TESTS-FIRST RED: Stage 4B result transport not implemented"
    )
    assert signature.parameters["result_transport"].default == LEGACY_MODE
    return worker_result_return


def _origin():
    context = {
        "schema_version": "forprint_governed_worker_context_projection_v0_1",
        "handoff_manifest_sha256": HASH,
        "handoff_source_state_fingerprint": SOURCE,
        "lifecycle_roadmap_cursor": {
            "roadmap_sync": "IN_SYNC",
            "roadmap_status": "ROADMAP_STATUS=control_foundation_near_horizon:current=CF-10",
            "open_work": {"u180j": {"state": "ACTIVE", "sequence": 67}},
            "lifecycle_status_sha256": "3" * 64,
            "roadmap_status_sha256": "4" * 64,
        },
        "execution_bindings": {"attempt_id": ATTEMPT},
        "authority": {
            "context_grants_authority": False,
            "dispatch_authority_granted": False,
            "release_authority_granted": False,
            "cross_repository_write_authority_granted": False,
        },
    }
    return {"handoff_manifest_sha256": HASH}, context


def _facts(status="PASS"):
    value = {
        "status": status,
        "changed_paths": ["tests/validation/test_validation_suite_runner_v0_1.py"],
        "validation_evidence": [{"name": "blueprint-continuity-planning", "result": "PASS"}],
        "self_repair_attempts": [],
        "unresolved_findings": [],
    }
    if status == "PARTIAL":
        value["partial_resume"] = {
            "latest_completed_node": "post-worker-validation",
            "latest_accepted_ref": "fixture-accepted-ref",
            "replay_forbidden_refs": ["fixture-accepted-ref"],
        }
    return value


def _draft(value):
    return DRAFT_BEGIN + "\n" + json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n" + DRAFT_END + "\n"


def _legacy(value):
    return LEGACY_BEGIN + "\n" + yaml.safe_dump(value, sort_keys=False) + LEGACY_END + "\n"


def _arrange(tmp_path, text):
    attempt = tmp_path / "attempt"
    logs = attempt / "logs"
    logs.mkdir(parents=True)
    stdout = logs / "stdout.log"
    stdout.write_text(text, encoding="utf-8")
    return attempt, stdout


def _invoke(tmp_path, text, *, mode=DRAFT_MODE, manifest=None, context=None, attempt_id=ATTEMPT):
    module = _bridge()
    if manifest is None or context is None:
        manifest0, context0 = _origin()
        manifest = manifest0 if manifest is None else manifest
        context = context0 if context is None else context
    attempt, stdout = _arrange(tmp_path, text)
    kwargs = dict(root=ROOT, attempt_root=attempt, stdout_path=stdout,
                  origin_manifest=manifest, expected_attempt_id=attempt_id,
                  governed_worker_context=context)
    if mode is not None:
        kwargs["result_transport"] = mode
    return module.materialize_worker_result(**kwargs), attempt, stdout


def _deny(tmp_path, text, *, mode=DRAFT_MODE, manifest=None, context=None, attempt_id=ATTEMPT):
    module = _bridge()
    origin0, context0 = _origin()
    manifest = origin0 if manifest is None else manifest
    context = context0 if context is None else context
    attempt, stdout = _arrange(tmp_path, text)
    with pytest.raises(module.WorkerResultReturnError):
        module.materialize_worker_result(
            root=ROOT, attempt_root=attempt, stdout_path=stdout,
            origin_manifest=manifest, expected_attempt_id=attempt_id,
            governed_worker_context=context, result_transport=mode,
        )
    assert not (attempt / "result" / "worker_result.yaml").exists()
    assert not (attempt / "result").exists()


def test_cf10_stage4b_valid_pass_materialized_as_composed_frozen_origin(tmp_path):
    facts = _facts()
    source = _draft(facts)
    result, attempt, stdout = _invoke(tmp_path, source)
    payload = yaml.safe_load((attempt / "result" / "worker_result.yaml").read_text())
    assert payload == result["result"]
    assert payload["resume_coordinates"]["lifecycle_roadmap_cursor"]["roadmap_status_sha256"] == "4" * 64
    assert payload["handoff_manifest_sha256"] == HASH
    assert payload["status"] == "PASS"
    assert result["result_source"] == "FROZEN_ORIGIN_COMPOSED_WORKER_DRAFT"
    assert result["validation_passed"] is True
    assert result["candidate_promoted"] is False
    assert result["canonical_write_performed"] is False
    assert stdout.read_text() == source


def test_cf10_stage4b_valid_partial_materialized_with_worker_extensions(tmp_path):
    result, attempt, _ = _invoke(tmp_path, _draft(_facts("PARTIAL")))
    resume = result["result"]["resume_coordinates"]
    assert resume["lifecycle_roadmap_cursor"]["roadmap_status_sha256"] == "4" * 64
    assert resume["latest_completed_node"] == "post-worker-validation"
    assert resume["latest_accepted_ref"] == "fixture-accepted-ref"
    assert resume["replay_forbidden_refs"] == ["fixture-accepted-ref"]
    assert (attempt / "result/worker_result.yaml").exists()


def test_cf10_stage4b_input_frozen_origin_and_completion_are_not_modified(tmp_path):
    origin, context = _origin()
    facts = _facts()
    frozen = copy.deepcopy((origin, context, facts))
    _invoke(tmp_path, _draft(facts), manifest=origin, context=context)
    assert (origin, context, facts) == frozen


def test_cf10_stage4b_default_legacy_full_handoff_still_accepted(tmp_path):
    origin, context = _origin()
    payload = compose_s4_result_candidate(
        origin_manifest=origin, governed_worker_context=context,
        expected_attempt_id=ATTEMPT, worker_completion=_facts(),
    )
    result, attempt, _ = _invoke(tmp_path, _legacy(payload), mode=None)
    assert result["result"] == payload
    assert "result_source" not in result
    assert (attempt / "result/worker_result.yaml").is_file()


def test_cf10_stage4b_explicit_legacy_mode_remains_identical(tmp_path):
    origin, context = _origin()
    payload = compose_s4_result_candidate(
        origin_manifest=origin, governed_worker_context=context,
        expected_attempt_id=ATTEMPT, worker_completion=_facts(),
    )
    result, _, _ = _invoke(tmp_path, _legacy(payload), mode=LEGACY_MODE)
    assert result["result"] == payload
    assert "result_source" not in result


def test_cf10_stage4b_legacy_rejects_draft_no_implicit_auto_detect(tmp_path):
    _deny(tmp_path, _draft(_facts()), mode=LEGACY_MODE)


def test_cf10_stage4b_draft_rejects_full_handoff_without_reclassification(tmp_path):
    origin, context = _origin()
    full = compose_s4_result_candidate(origin_manifest=origin, governed_worker_context=context,
        expected_attempt_id=ATTEMPT, worker_completion=_facts())
    _deny(tmp_path, _legacy(full))


def test_cf10_stage4b_legacy_drift_not_silently_fixed(tmp_path):
    origin, context = _origin()
    full = compose_s4_result_candidate(origin_manifest=origin, governed_worker_context=context,
        expected_attempt_id=ATTEMPT, worker_completion=_facts())
    full["resume_coordinates"]["lifecycle_roadmap_cursor"]["roadmap_status_sha256"] = "9" * 64
    _deny(tmp_path, _legacy(full), mode=LEGACY_MODE)


def test_cf10_stage4b_unknown_trusted_transport_value_rejected(tmp_path):
    _deny(tmp_path, _draft(_facts()), mode="use-bash")


@pytest.mark.parametrize("tamper", [
    lambda v: v.update(attempt_id=ATTEMPT),
    lambda v: v.update(handoff_manifest_sha256=HASH),
    lambda v: v.update(source_state_fingerprint=SOURCE),
    lambda v: v.update(lifecycle_roadmap_cursor={}),
    lambda v: v.update(resume_coordinates={}),
    lambda v: v.update(schema_version="forprint_assistant_handoff_v2_result_v0_1"),
    lambda v: v.update(extra_key="surprise"),
])
def test_cf10_stage4b_worker_origin_spoofing_refused(tmp_path, tamper):
    bad = _facts()
    tamper(bad)
    _deny(tmp_path, _draft(bad))


@pytest.mark.parametrize("broken", [
    lambda v: v.update(validation_evidence=[]),
    lambda v: v.update(changed_paths=["../unsafe"]),
    lambda v: v.update(changed_paths=["x.py", "x.py"]),
    lambda v: v.update(status="UNSUPPORTED"),
    lambda v: v.update(unresolved_findings="not a list"),
])
def test_cf10_stage4b_invalid_completion_facts_refused(tmp_path, broken):
    bad = _facts()
    broken(bad)
    _deny(tmp_path, _draft(bad))


@pytest.mark.parametrize("broken", [
    lambda v: v.pop("partial_resume"),
    lambda v: v["partial_resume"].update(latest_accepted_ref=""),
    lambda v: v["partial_resume"].update(replay_forbidden_refs=[]),
])
def test_cf10_stage4b_incomplete_partial_resume_refused(tmp_path, broken):
    bad = _facts("PARTIAL")
    broken(bad)
    _deny(tmp_path, _draft(bad))


@pytest.mark.parametrize("broken", [
    lambda origin, context: origin.update(handoff_manifest_sha256="a" * 64),
    lambda origin, context: context["execution_bindings"].update(attempt_id="cf10-u180j-a998"),
    lambda origin, context: context["authority"].update(release_authority_granted=True),
    lambda origin, context: context["lifecycle_roadmap_cursor"].update(roadmap_status_sha256="!"),
])
def test_cf10_stage4b_invalid_frozen_origin_refused(tmp_path, broken):
    origin, context = _origin()
    broken(origin, context)
    _deny(tmp_path, _draft(_facts()), manifest=origin, context=context)


@pytest.mark.parametrize("malformed", [
    "{broken json",
    "[]",
    "null",
    "true",
    '{"status":"PASS","status":"FAIL"}',
    '{"validation_evidence":[{"name":"A","name":"B"}]}',
    '{"status":NaN}',
    '{"status":Infinity}',
])
def test_cf10_stage4b_malformed_or_duplicate_json_refused(tmp_path, malformed):
    _deny(tmp_path, DRAFT_BEGIN + "\n" + malformed + "\n" + DRAFT_END + "\n")


@pytest.mark.parametrize("malformed", [
    DRAFT_BEGIN + "\n{}\n",
    "{}\n" + DRAFT_END,
    DRAFT_END + "\n{}\n" + DRAFT_BEGIN,
    "before\n" + DRAFT_BEGIN + "\n{}\n" + DRAFT_END,
    DRAFT_BEGIN + "\n{}\n" + DRAFT_END + "\nafter",
    DRAFT_BEGIN + "\n{}\n" + DRAFT_END + DRAFT_BEGIN + "\n{}\n" + DRAFT_END,
    LEGACY_BEGIN + "\n{}\n" + LEGACY_END + "\n" + DRAFT_BEGIN + "\n{}\n" + DRAFT_END,
])
def test_cf10_stage4b_missing_duplicate_mixed_or_extra_frames_refused(tmp_path, malformed):
    _deny(tmp_path, malformed)


def test_cf10_stage4b_oversized_json_refused(tmp_path):
    long_draft = DRAFT_BEGIN + "\n" + " " * 66000 + json.dumps(_facts()) + "\n" + DRAFT_END + "\n"
    _deny(tmp_path, long_draft)


def test_cf10_stage4b_refuses_preexisting_result(tmp_path):
    _bridge()
    origin, context = _origin()
    attempt, stdout = _arrange(tmp_path, _draft(_facts()))
    result_dir = attempt / "result"
    result_dir.mkdir()
    sentinel = result_dir / "worker_result.yaml"
    sentinel.write_bytes(b"DO_NOT_OVERWRITE")
    with pytest.raises(worker_result_return.WorkerResultReturnError):
        worker_result_return.materialize_worker_result(
            root=ROOT, attempt_root=attempt, stdout_path=stdout,
            origin_manifest=origin, expected_attempt_id=ATTEMPT,
            governed_worker_context=context, result_transport=DRAFT_MODE,
        )
    assert sentinel.read_bytes() == b"DO_NOT_OVERWRITE"


def test_cf10_stage4b_refuses_symlink_result_directory(tmp_path):
    _bridge()
    origin, context = _origin()
    attempt, stdout = _arrange(tmp_path, _draft(_facts()))
    outside = tmp_path / "outside"
    outside.mkdir()
    (attempt / "result").symlink_to(outside, target_is_directory=True)
    with pytest.raises(worker_result_return.WorkerResultReturnError):
        worker_result_return.materialize_worker_result(
            root=ROOT, attempt_root=attempt, stdout_path=stdout,
            origin_manifest=origin, expected_attempt_id=ATTEMPT,
            governed_worker_context=context, result_transport=DRAFT_MODE,
        )
    assert list(outside.iterdir()) == []


def test_cf10_stage4b_rejects_stdout_outside_attempt(tmp_path):
    _bridge()
    origin, context = _origin()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    outside = tmp_path / "outside.log"
    outside.write_text(_draft(_facts()))
    with pytest.raises(worker_result_return.WorkerResultReturnError):
        worker_result_return.materialize_worker_result(
            root=ROOT, attempt_root=attempt, stdout_path=outside,
            origin_manifest=origin, expected_attempt_id=ATTEMPT,
            governed_worker_context=context, result_transport=DRAFT_MODE,
        )
    assert not (attempt / "result").exists()
