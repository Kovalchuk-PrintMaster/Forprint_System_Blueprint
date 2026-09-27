from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.coordination import continuity
from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
from scripts.coordination.control_plane.context import task_context_adapter as adapter


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "scripts/coordination/assistant_handoff_v2_runtime_v0_1.py"


def load_runtime():
    name = "_cf10_handoff_v2_current_attempt_ledger_freshness"
    spec = importlib.util.spec_from_file_location(name, RUNTIME)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def hash_source(runtime, payload: dict) -> str:
    value = copy.deepcopy(payload)
    value.pop("fingerprint_sha256", None)
    return runtime._sha_bytes(runtime._canonical_json(value))


def source_state(runtime, *, ledger_rel: str | None) -> tuple[dict, dict]:
    frozen = {
        "schema_version": "forprint_continuity_source_state_v0_1",
        "source_mode": "working_tree",
        "git_head": "1" * 40,
        "git_branch": "audit/test",
        "durable_dirty_paths": ["AGENTS.md"],
        "dirty_path_status": {"AGENTS.md": " M"},
        "dirty_path_content_or_symlink_fingerprint": {
            "AGENTS.md": {"kind": "file", "sha256": "a" * 64}
        },
        "rename_or_copy_origins": {},
        "bounded_final_applied_artifact_hashes": {},
        "exclusion_policy": {
            "runtime_top_level": [],
            "runtime_exact": [],
            "runtime_recursive_parts": [],
            "non_source_prefixes": [],
            "reports_implicitly_excluded": False,
        },
    }
    frozen["fingerprint_sha256"] = hash_source(runtime, frozen)

    live = copy.deepcopy(frozen)
    if ledger_rel is not None:
        live["durable_dirty_paths"].append(ledger_rel)
        live["durable_dirty_paths"].sort()
        live["dirty_path_status"][ledger_rel] = "??"
        live["dirty_path_content_or_symlink_fingerprint"][ledger_rel] = {
            "kind": "file",
            "sha256": "b" * 64,
        }
    live["fingerprint_sha256"] = hash_source(runtime, live)
    return frozen, live


def full_context(*, source: dict, task_id: str) -> dict:
    context = {
        "schema_version": "forprint_blueprint_internal_task_context_v0_1",
        "task_id": task_id,
        "module_id": "forprint_system_blueprint",
        "source_type": "MANUAL_INTERNAL",
        "task_artifact": {
            "path": "coordination/internal_work/blueprint/worker_tasks/task.yaml",
            "sha256": "c" * 64,
        },
        "task_envelope": {
            "schema_version": "fixture",
            "work": {"work_front_id": "wf-fixture"},
        },
        "source_state": {
            "provider": "scripts.coordination.continuity.build_source_state",
            "schema_version": source["schema_version"],
            "source_mode": source["source_mode"],
            "git_head": source["git_head"],
            "git_branch": source["git_branch"],
            "fingerprint_sha256": source["fingerprint_sha256"],
            "durable_dirty_path_count": len(source["durable_dirty_paths"]),
        },
        "authority": {
            "context_grants_authority": False,
            "execution_authority_source": "WORK_FRONT",
            "dispatch_authority_conferred": False,
            "release_authority_conferred": False,
            "foreign_write_authority_conferred": False,
        },
    }
    context["task_context_id"] = adapter._sha256_bytes(
        adapter._canonical_json(context)
    )
    return context


def handoff(runtime, *, task_context_id: str) -> dict:
    task_evidence = {
        "delegate": (
            "scripts/coordination/control_plane/context/"
            "task_context_adapter.py --task-context"
        ),
        "prompt_id": "task-fixture",
        "module_root": ".",
        "module": "forprint_system_blueprint",
        "task_context_id": task_context_id,
        "validation": "PASS",
    }
    manifest = {
        "schema_version": "forprint_assistant_handoff_v2_runtime_manifest_v0_1",
        "launch_mode": "TASK_EXECUTION",
        "handoff_manifest_sha256": "e" * 64,
        "work_front_or_project_onboard_not_applicable_reason": {
            "front": "coordination/work_fronts/fixture.yaml",
            "work_front_id": "wf-fixture",
            "validation": "PASS",
        },
        "execution_profile_revision_for_task_execution": {
            "profile_id": "light-maintenance",
            "revision": "r1",
        },
        "governed_procedure_revision_or_not_required_reason": {
            "classification": "GRAPH_REQUIRED",
            "procedure_id": "governed_canonical_mutation",
            "revision": "0.1.0",
            "registry_sha256": "f" * 64,
        },
        "lifecycle_roadmap_cursor": {
            "roadmap_sync": "IN_SYNC",
            "event_sequence": 67,
        },
        "resume_coordinates": {
            "launch_mode": "TASK_EXECUTION",
            "git_head": "1" * 40,
            "work_id": "u180j",
            "work_state": {"state": "ACTIVE"},
            "prompt_id": "task-fixture",
            "module_root": ".",
            "front": "coordination/work_fronts/fixture.yaml",
            "profile_id": "light-maintenance",
            "procedure_id": "governed_canonical_mutation",
        },
        "base_context": {
            "project_onboard_handoff_v1": {},
            "task_execution_context": task_evidence,
        },
    }

    composite = {
        "head": manifest["resume_coordinates"]["git_head"],
        "launch_mode": "TASK_EXECUTION",
        "front": manifest[
            "work_front_or_project_onboard_not_applicable_reason"
        ],
        "profile": manifest[
            "execution_profile_revision_for_task_execution"
        ],
        "procedure": manifest[
            "governed_procedure_revision_or_not_required_reason"
        ],
        "task_context": task_evidence,
        "cursor": manifest["lifecycle_roadmap_cursor"],
    }
    manifest["source_state_fingerprint"] = runtime._sha_bytes(
        runtime._canonical_json(composite)
    )
    return manifest


def result(origin: dict, attempt_id: str = "cf10-u180j-a016") -> dict:
    return {
        "schema_version": "forprint_assistant_handoff_v2_result_v0_1",
        "handoff_manifest_sha256": origin["handoff_manifest_sha256"],
        "attempt_id": attempt_id,
        "status": "PASS",
        "changed_paths": ["fixture.py"],
        "validation_evidence": ["pytest:PASS"],
        "self_repair_attempts": [],
        "resume_coordinates": {
            "attempt_id": attempt_id,
            "handoff_manifest_sha256": origin["handoff_manifest_sha256"],
            "source_state_fingerprint": origin["source_state_fingerprint"],
            "lifecycle_roadmap_cursor": origin["lifecycle_roadmap_cursor"],
        },
        "unresolved_findings": [],
    }


def install_exact_started_fixture(monkeypatch, tmp_path: Path):
    runtime = load_runtime()
    attempt_id = "cf10-u180j-a016"
    ledger_rel = (
        "coordination/continuity/execution_attempts/"
        f"{attempt_id}__dddddddddddd.yaml"
    )
    frozen_source, live_source = source_state(runtime, ledger_rel=ledger_rel)
    frozen_context = full_context(
        source=frozen_source,
        task_id="task-fixture",
    )
    live_context = full_context(
        source=live_source,
        task_id="task-fixture",
    )

    origin = handoff(
        runtime,
        task_context_id=frozen_context["task_context_id"],
    )
    live = handoff(
        runtime,
        task_context_id=live_context["task_context_id"],
    )

    started = {
        "attempt_id": attempt_id,
        "work_front_id": "wf-fixture",
        "attempt_stage": "STARTED",
        "result_state": "PENDING",
        "validator_outcome": "NOT_RUN",
        "pack_hash_or_context_hash": origin["handoff_manifest_sha256"],
        "source_fingerprint": frozen_source["fingerprint_sha256"],
    }

    store = tmp_path / "coordination/continuity/execution_attempts"
    store.mkdir(parents=True)
    record_path = store / f"{attempt_id}__dddddddddddd.yaml"
    record_path.write_text("fixture: true\n", encoding="utf-8")

    monkeypatch.setattr(ledger, "load_contract", lambda root: {})
    monkeypatch.setattr(
        ledger,
        "store_root",
        lambda root, contract, override: store,
    )
    monkeypatch.setattr(
        ledger,
        "records_for_attempt",
        lambda store_arg, attempt_arg: (
            [copy.deepcopy(started)]
            if attempt_arg == attempt_id
            else []
        ),
    )
    monkeypatch.setattr(ledger, "record_digest", lambda record: "d" * 64)
    monkeypatch.setattr(
        continuity,
        "build_source_state",
        lambda root: copy.deepcopy(live_source),
    )
    monkeypatch.setattr(
        adapter,
        "build_internal_task_context",
        lambda root, *, task_id, module_root: copy.deepcopy(live_context),
    )

    return (
        runtime,
        origin,
        live,
        frozen_source,
        live_source,
        frozen_context,
        live_context,
        attempt_id,
        record_path,
    )


def test_exact_current_attempt_started_ledger_is_normalized(
    monkeypatch,
    tmp_path: Path,
) -> None:
    (
        runtime,
        origin,
        live,
        frozen_source,
        live_source,
        frozen_context,
        _live_context,
        attempt_id,
        record_path,
    ) = install_exact_started_fixture(monkeypatch, tmp_path)

    normalized, proof = (
        runtime._normalize_task_execution_live_manifest_for_started_attempt(
            tmp_path,
            origin,
            live,
            result(origin, attempt_id),
        )
    )

    assert proof["applied"] is True
    assert proof["reason"] == "CURRENT_ATTEMPT_STARTED_LEDGER_ONLY"
    assert proof["authority_widened"] is False
    assert proof["source_drift_ignored"] is False
    assert proof["unrelated_source_drift_allowed"] is False
    assert proof["ledger_record"] == record_path.relative_to(tmp_path).as_posix()
    assert proof["frozen_source_fingerprint"] == frozen_source["fingerprint_sha256"]
    assert proof["live_source_fingerprint"] == live_source["fingerprint_sha256"]
    assert proof["reconstructed_task_context_id"] == (
        frozen_context["task_context_id"]
    )
    assert normalized["source_state_fingerprint"] == (
        origin["source_state_fingerprint"]
    )


def test_unrelated_source_drift_is_not_normalized(
    monkeypatch,
    tmp_path: Path,
) -> None:
    (
        runtime,
        origin,
        _live,
        _frozen_source,
        live_source,
        _frozen_context,
        _live_context,
        attempt_id,
        _record_path,
    ) = install_exact_started_fixture(monkeypatch, tmp_path)

    drifted = copy.deepcopy(live_source)
    drifted["durable_dirty_paths"].append("UNRELATED.txt")
    drifted["durable_dirty_paths"].sort()
    drifted["dirty_path_status"]["UNRELATED.txt"] = "??"
    drifted["dirty_path_content_or_symlink_fingerprint"]["UNRELATED.txt"] = {
        "kind": "file",
        "sha256": "9" * 64,
    }
    drifted["fingerprint_sha256"] = hash_source(runtime, drifted)

    drifted_context = full_context(
        source=drifted,
        task_id="task-fixture",
    )
    monkeypatch.setattr(
        continuity,
        "build_source_state",
        lambda root: copy.deepcopy(drifted),
    )
    monkeypatch.setattr(
        adapter,
        "build_internal_task_context",
        lambda root, *, task_id, module_root: copy.deepcopy(drifted_context),
    )

    drifted_live = handoff(
        runtime,
        task_context_id=drifted_context["task_context_id"],
    )

    normalized, proof = (
        runtime._normalize_task_execution_live_manifest_for_started_attempt(
            tmp_path,
            origin,
            drifted_live,
            result(origin, attempt_id),
        )
    )

    assert proof["applied"] is False
    assert proof["reason"] == "NON_LEDGER_CANONICAL_SOURCE_DRIFT_PRESENT"
    assert normalized["source_state_fingerprint"] == (
        drifted_live["source_state_fingerprint"]
    )


@pytest.mark.parametrize(
    ("stage", "state", "validator"),
    [
        ("BLOCKED", "BLOCKED", "NOT_RUN"),
        ("STARTED", "PENDING", "PASS"),
    ],
)
def test_non_started_pending_attempt_state_is_not_normalized(
    monkeypatch,
    tmp_path: Path,
    stage: str,
    state: str,
    validator: str,
) -> None:
    (
        runtime,
        origin,
        live,
        _frozen_source,
        _live_source,
        _frozen_context,
        _live_context,
        attempt_id,
        _record_path,
    ) = install_exact_started_fixture(monkeypatch, tmp_path)

    bad = {
        "attempt_id": attempt_id,
        "work_front_id": "wf-fixture",
        "attempt_stage": stage,
        "result_state": state,
        "validator_outcome": validator,
        "pack_hash_or_context_hash": origin["handoff_manifest_sha256"],
        "source_fingerprint": "a" * 64,
    }
    monkeypatch.setattr(
        ledger,
        "records_for_attempt",
        lambda store_arg, attempt_arg: [bad],
    )

    normalized, proof = (
        runtime._normalize_task_execution_live_manifest_for_started_attempt(
            tmp_path,
            origin,
            live,
            result(origin, attempt_id),
        )
    )
    assert proof["applied"] is False
    assert proof["reason"] == "ATTEMPT_LEDGER_NOT_STARTED_PENDING"
    assert normalized["source_state_fingerprint"] == (
        live["source_state_fingerprint"]
    )


def test_validate_result_for_return_uses_only_proven_normalization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    (
        runtime,
        origin,
        live,
        _frozen_source,
        _live_source,
        _frozen_context,
        _live_context,
        attempt_id,
        _record_path,
    ) = install_exact_started_fixture(monkeypatch, tmp_path)

    returned = result(origin, attempt_id)

    monkeypatch.setattr(
        runtime,
        "_load_result_runtime",
        lambda root: SimpleNamespace(
            validate_with_bounded_self_repair=lambda *args, **kwargs: {
                "valid": True,
                "result": returned,
                "errors": [],
                "repair_attempt_count": 0,
            }
        ),
    )

    def validate_freshness(origin_arg, live_arg, result_arg, *, root):
        valid = (
            origin_arg["source_state_fingerprint"]
            == live_arg["source_state_fingerprint"]
            and origin_arg["lifecycle_roadmap_cursor"]
            == live_arg["lifecycle_roadmap_cursor"]
        )
        return {
            "valid": valid,
            "errors": (
                []
                if valid
                else [{"code": "STALE_SOURCE_STATE_FINGERPRINT"}]
            ),
        }

    monkeypatch.setattr(
        runtime,
        "_load_freshness_resume_runtime",
        lambda root: SimpleNamespace(
            validate_freshness_and_resume=validate_freshness
        ),
    )
    monkeypatch.setattr(
        runtime,
        "compile_runtime_manifest",
        lambda root, *, launch_mode, **kwargs: copy.deepcopy(live),
    )
    monkeypatch.setattr(
        runtime,
        "_task_execution_recompile_bindings",
        lambda manifest: {
            "front": "coordination/work_fronts/fixture.yaml",
            "profile_id": "light-maintenance",
            "prompt_id": "task-fixture",
            "module_root": ".",
            "module": "forprint_system_blueprint",
            "procedure_id": "governed_canonical_mutation",
            "procedure_not_required_reason": None,
        },
    )

    report = runtime.validate_result_for_return(
        tmp_path,
        origin,
        returned,
    )

    assert report["valid"] is True
    assert report["freshness_normalization"]["applied"] is True
    assert report["freshness_normalization"]["authority_widened"] is False
    assert report["freshness_resume"]["valid"] is True
