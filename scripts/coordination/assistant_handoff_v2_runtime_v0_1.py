#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

HANDOFF_V1_PATH = PROJECT_ROOT / "scripts/coordination/build_assistant_handoff_archive.py"
HANDOFF_V1_SPEC = importlib.util.spec_from_file_location(
    "forprint_build_assistant_handoff_archive",
    HANDOFF_V1_PATH,
)
if HANDOFF_V1_SPEC is None or HANDOFF_V1_SPEC.loader is None:
    raise RuntimeError("cannot load build_assistant_handoff_archive.py")
handoff_v1 = importlib.util.module_from_spec(HANDOFF_V1_SPEC)
HANDOFF_V1_SPEC.loader.exec_module(handoff_v1)

S1_CONTRACT = Path("coordination/standards/automation/assistant_handoff_v2_contract_v0_1.yaml")
RUNTIME_CONTRACT = Path(
    "coordination/standards/automation/assistant_handoff_v2_runtime_contract_v0_1.yaml"
)
PROJECT_CONSTITUTION = Path("coordination/standards/governance/project_constitution_v0_1.yaml")
WORK_FRONT_RUNTIME = Path("scripts/coordination/work_front_v0_1.py")
TASK_CONTEXT_RUNTIME = Path("scripts/coordination/control_plane/context/task_context_adapter.py")
EXTERNAL_TASK_CONTEXT_COMPATIBILITY_DELEGATE = (
    "scripts/coordination/build_context_bundle.py --task-context"
)
LIFECYCLE_RUNTIME = Path("scripts/coordination/continuity_lifecycle.py")
ROADMAP_RUNTIME = Path("scripts/coordination/roadmap_execution_reconciliation.py")
EXECUTION_PROFILE_CONTRACT = Path(
    "coordination/standards/automation/execution_profile_registry_contract_v0_1.yaml"
)
PROCEDURE_REGISTRY = Path("coordination/registry/governed_procedure_registry_v0_1.yaml")
LAUNCH_MODES = ("PROJECT_ONBOARD", "TASK_EXECUTION")


class RuntimeErrorV2(RuntimeError):
    pass


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_path(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _require(root: Path, rel: Path) -> Path:
    path = root / rel
    if not path.is_file():
        raise RuntimeErrorV2(f"required file missing: {rel}")
    return path


def _run(root: Path, argv: list[str], timeout: int = 1200) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def _git_head(root: Path) -> str:
    cp = _run(root, ["git", "rev-parse", "HEAD"], timeout=120)
    if cp.returncode:
        raise RuntimeErrorV2("cannot resolve git HEAD")
    return cp.stdout.strip()


def _find_maps(node: Any, key: str, value: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if node.get(key) == value:
            hits.append(node)
        for child in node.values():
            hits.extend(_find_maps(child, key, value))
    elif isinstance(node, list):
        for child in node:
            hits.extend(_find_maps(child, key, value))
    return hits


def _find_string(node: Any, suffix: str) -> list[str]:
    hits: list[str] = []
    if isinstance(node, str) and node.replace("\\", "/").endswith(suffix):
        hits.append(node)
    elif isinstance(node, dict):
        for child in node.values():
            hits.extend(_find_string(child, suffix))
    elif isinstance(node, list):
        for child in node:
            hits.extend(_find_string(child, suffix))
    return hits


def _profile_binding(root: Path, profile_id: str) -> dict[str, Any]:
    contract = _load_yaml(_require(root, EXECUTION_PROFILE_CONTRACT))
    refs = sorted(set(_find_string(contract, "execution_profiles_v0_1.yaml")))
    if len(refs) != 1:
        raise RuntimeErrorV2(f"execution profile registry path must resolve once: {refs}")
    registry_path = _require(root, Path(refs[0]))
    data = _load_yaml(registry_path)
    hits = _find_maps(data, "profile_id", profile_id)
    if len(hits) != 1:
        raise RuntimeErrorV2(f"execution profile must resolve exactly once: {profile_id}")
    row = hits[0]
    revision = row.get("revision") or row.get("profile_revision")
    if revision is None:
        raise RuntimeErrorV2(f"execution profile revision missing: {profile_id}")
    return {
        "profile_id": profile_id,
        "revision": str(revision),
        "registry_path": refs[0],
        "registry_sha256": _sha_path(registry_path),
    }


def _procedure_binding(
    root: Path, procedure_id: str | None, not_required_reason: str | None
) -> dict[str, Any]:
    if procedure_id:
        path = _require(root, PROCEDURE_REGISTRY)
        data = _load_yaml(path)
        hits = _find_maps(data, "procedure_id", procedure_id)
        if len(hits) != 1:
            raise RuntimeErrorV2(f"procedure must resolve exactly once: {procedure_id}")
        row = hits[0]
        revision = row.get("revision") or row.get("procedure_revision")
        if revision is None:
            raise RuntimeErrorV2(f"procedure revision missing: {procedure_id}")
        return {
            "classification": "GRAPH_REQUIRED",
            "procedure_id": procedure_id,
            "revision": str(revision),
            "registry_sha256": _sha_path(path),
        }
    if not_required_reason and not_required_reason.strip():
        return {"classification": "NOT_REQUIRED", "reason": not_required_reason.strip()}
    raise RuntimeErrorV2(
        "TASK_EXECUTION requires --procedure-id or --procedure-not-required-reason"
    )


def _work_front_binding(root: Path, front: str) -> dict[str, Any]:
    py = root / ".venv_blueprint/bin/python"
    cp = _run(
        root,
        [
            str(py),
            str(_require(root, WORK_FRONT_RUNTIME)),
            "--root",
            ".",
            "--front",
            front,
            "--action",
            "validate",
        ],
    )
    if cp.returncode or "WORK_FRONT_VALIDATION=PASS" not in cp.stdout:
        raise RuntimeErrorV2("work front validation failed:\n" + cp.stdout)
    values = {}
    for line in cp.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    return {
        "front": front,
        "work_front_id": values.get("WORK_FRONT_ID"),
        "front_path": values.get("WORK_FRONT_PATH"),
        "validation": "PASS",
    }


def _task_context_evidence(
    root: Path, prompt_id: str, module_root: str, module: str | None
) -> dict[str, Any]:
    py = root / ".venv_blueprint/bin/python"
    argv = [
        str(py),
        str(_require(root, TASK_CONTEXT_RUNTIME)),
        "--task-context",
        "--prompt-id",
        prompt_id,
        "--module-root",
        module_root,
        "--no-write",
    ]
    if module:
        argv.extend(["--module", module])
    cp = _run(root, argv, timeout=1800)
    if cp.returncode or "TASK_CONTEXT_COMPILER=PASS" not in cp.stdout:
        raise RuntimeErrorV2("task context compiler failed:\n" + cp.stdout)
    values = {}
    for line in cp.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    return {
        "delegate": "scripts/coordination/control_plane/context/task_context_adapter.py --task-context",
        "prompt_id": prompt_id,
        "module_root": module_root,
        "module": module,
        "task_context_id": values.get("TASK_CONTEXT_ID"),
        "task_context_mode": values.get("TASK_CONTEXT_MODE"),
        "work_id": values.get("WORK_ID"),
        "validation": "PASS",
    }


def _v1_summary(root: Path) -> dict[str, Any]:
    result = handoff_v1.build_payload(root)
    if not isinstance(result, tuple) or len(result) != 2:
        raise RuntimeErrorV2("Handoff v1 build_payload must return (payload, manifest)")

    payload, manifest = result
    if not isinstance(payload, dict):
        raise RuntimeErrorV2("Handoff v1 payload must be a mapping")
    if not isinstance(manifest, dict):
        raise RuntimeErrorV2("Handoff v1 manifest must be a mapping")

    if not all(
        isinstance(name, str) and isinstance(value, bytes) for name, value in payload.items()
    ):
        raise RuntimeErrorV2("Handoff v1 payload must be dict[str, bytes]")

    handoff_v1.validate_payload(payload, manifest)

    selected = {}
    for key, value in payload.items():
        if any(
            token in key.lower()
            for token in (
                "dependency",
                "health",
                "roadmap",
                "checkpoint",
                "workfront",
                "work_front",
            )
        ):
            selected[key] = {
                "sha256": _sha_bytes(value),
                "bytes": len(value),
            }

    return {
        "delegate": "scripts/coordination/build_assistant_handoff_archive.py",
        "payload_member_count": len(payload),
        "manifest_schema_version": manifest.get("schema_version"),
        "source_state_fingerprint": manifest.get("source_state_fingerprint"),
        "selected_dependency_health_members": selected,
    }


def _cursor(root: Path) -> dict[str, Any]:
    py = root / ".venv_blueprint/bin/python"
    life = _run(
        root,
        [str(py), str(_require(root, LIFECYCLE_RUNTIME)), "--root", ".", "status"],
        timeout=300,
    )
    if life.returncode:
        raise RuntimeErrorV2("lifecycle status failed")
    life_data = yaml.safe_load(life.stdout)
    states = life_data.get("work_states") if isinstance(life_data, dict) else None
    if not isinstance(states, dict):
        raise RuntimeErrorV2("work_states missing")
    road = _run(
        root, [str(py), str(_require(root, ROADMAP_RUNTIME)), "--root", ".", "status"], timeout=600
    )
    if road.returncode or "ROADMAP_SYNC=IN_SYNC" not in road.stdout:
        raise RuntimeErrorV2("roadmap status is not IN_SYNC")
    status = next(
        (
            line
            for line in road.stdout.splitlines()
            if line.startswith("ROADMAP_STATUS=control_foundation_near_horizon:")
        ),
        None,
    )
    if not status:
        raise RuntimeErrorV2("roadmap cursor missing")
    open_work = {
        k: v
        for k, v in states.items()
        if isinstance(v, dict)
        and v.get("state") in {"PLANNED", "ACTIVE", "CHECKPOINTED", "VALIDATED"}
    }
    return {
        "roadmap_sync": "IN_SYNC",
        "roadmap_status": status,
        "open_work": open_work,
        "lifecycle_status_sha256": _sha_bytes(life.stdout.encode()),
        "roadmap_status_sha256": _sha_bytes(road.stdout.encode()),
    }


def _manifest_hash(manifest: dict[str, Any]) -> str:
    value = dict(manifest)
    value.pop("handoff_manifest_sha256", None)
    return _sha_bytes(_canonical_json(value))


def compile_runtime_manifest(
    root: Path,
    *,
    launch_mode: str,
    front: str | None = None,
    profile_id: str | None = None,
    procedure_id: str | None = None,
    procedure_not_required_reason: str | None = None,
    prompt_id: str | None = None,
    module_root: str | None = None,
    module: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    if launch_mode not in LAUNCH_MODES:
        raise RuntimeErrorV2(f"unsupported launch_mode: {launch_mode}")
    s1_path = _require(root, S1_CONTRACT)
    _require(root, RUNTIME_CONTRACT)
    constitution = _require(root, PROJECT_CONSTITUTION)
    s1 = _load_yaml(s1_path)
    revision = s1.get("revision") if isinstance(s1, dict) else None
    if not isinstance(revision, str):
        raise RuntimeErrorV2("S1 revision missing")

    base = _v1_summary(root)
    cursor = _cursor(root)
    head = _git_head(root)

    if launch_mode == "PROJECT_ONBOARD":
        if any(
            v is not None
            for v in (
                profile_id,
                procedure_id,
                procedure_not_required_reason,
                prompt_id,
                module_root,
            )
        ):
            raise RuntimeErrorV2("PROJECT_ONBOARD does not accept task-execution bindings")
        front_binding = {
            "classification": "NOT_APPLICABLE",
            "reason": "PROJECT_ONBOARD_COMPAT_NO_WORK_FRONT",
            "front": front,
        }
        profile_binding = None
        procedure_binding = {"classification": "NOT_APPLICABLE", "reason": "PROJECT_ONBOARD_COMPAT"}
        task_context = None
    else:
        if not front:
            raise RuntimeErrorV2("TASK_EXECUTION requires --front")
        if not profile_id:
            raise RuntimeErrorV2("TASK_EXECUTION requires --profile-id")
        if not prompt_id:
            raise RuntimeErrorV2("TASK_EXECUTION requires --prompt-id")
        if not module_root:
            raise RuntimeErrorV2("TASK_EXECUTION requires --module-root")
        front_binding = _work_front_binding(root, front)
        profile_binding = _profile_binding(root, profile_id)
        procedure_binding = _procedure_binding(root, procedure_id, procedure_not_required_reason)
        task_context = _task_context_evidence(root, prompt_id, module_root, module)

    resume_work_id = "u180h"
    resume_work_state = cursor["open_work"].get(resume_work_id)
    if (
        launch_mode == "TASK_EXECUTION"
        and isinstance(task_context, dict)
        and task_context.get("task_context_mode") == "MANUAL_INTERNAL"
    ):
        internal_work_id = task_context.get("work_id")
        if not isinstance(internal_work_id, str) or not internal_work_id.strip():
            raise RuntimeErrorV2(
                "MANUAL_INTERNAL TASK_EXECUTION requires Task Context WORK_ID"
            )
        resume_work_id = internal_work_id.strip()
        resume_work_state = cursor["open_work"].get(resume_work_id)

    fingerprint = {
        "head": head,
        "launch_mode": launch_mode,
        "front": front_binding,
        "profile": profile_binding,
        "procedure": procedure_binding,
        "task_context": task_context,
        "cursor": cursor,
    }
    manifest: dict[str, Any] = {
        "schema_version": "forprint_assistant_handoff_v2_runtime_manifest_v0_1",
        "runtime_revision": "0.1.0",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "launch_mode": launch_mode,
        "authority": {
            "execution_authority_granted": False,
            "dispatch_authority_granted": False,
            "release_authority_granted": False,
            "cross_repository_write_authority_granted": False,
        },
        "project_laws_or_constitution_revision": {
            "path": PROJECT_CONSTITUTION.as_posix(),
            "sha256": _sha_path(constitution),
        },
        "work_front_or_project_onboard_not_applicable_reason": front_binding,
        "execution_profile_revision_for_task_execution": profile_binding,
        "governed_procedure_revision_or_not_required_reason": procedure_binding,
        "dependency_health_slice": base["selected_dependency_health_members"],
        "source_state_fingerprint": _sha_bytes(_canonical_json(fingerprint)),
        "lifecycle_roadmap_cursor": cursor,
        "resume_coordinates": {
            "launch_mode": launch_mode,
            "git_head": head,
            "work_id": resume_work_id,
            "work_state": resume_work_state,
            "prompt_id": prompt_id,
            "module_root": module_root,
            "front": front,
            "profile_id": profile_id,
            "procedure_id": procedure_id,
        },
        "expected_result_schema_revision": revision,
        "base_context": {
            "project_onboard_handoff_v1": base,
            "task_execution_context": task_context,
        },
        "s2_scope": {
            "exact_result_validation_deferred_to_s3": False,
            "exact_result_validation_implemented_s3": True,
            "bounded_self_repair_execution_deferred_to_s3": False,
            "bounded_self_repair_execution_implemented_s3": True,
            "freshness_fail_closed_hardening_deferred_to_s4": False,
            "freshness_fail_closed_hardening_implemented_s4": True,
            "durable_resume_hardening_deferred_to_s4": False,
            "durable_resume_hardening_implemented_s4": True,
            "dispatcher_integration_deferred_to_cf09": True,
            "worker_dispatch_performed": False,
        },
    }
    manifest["handoff_manifest_sha256"] = _manifest_hash(manifest)
    return manifest


def _load_result_runtime(root: Path) -> Any:
    path = root / "scripts/coordination/assistant_handoff_v2_result_v0_1.py"
    if not path.is_file():
        raise RuntimeErrorV2("Handoff v2 S3 result runtime is missing")
    spec = importlib.util.spec_from_file_location(
        "forprint_assistant_handoff_v2_result_v0_1",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeErrorV2("cannot load Handoff v2 S3 result runtime")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_freshness_resume_runtime(root: Path) -> Any:
    path = root / "scripts/coordination/assistant_handoff_v2_freshness_resume_v0_1.py"
    if not path.is_file():
        raise RuntimeErrorV2("Handoff v2 S4 freshness/resume runtime is missing")
    spec = importlib.util.spec_from_file_location(
        "forprint_assistant_handoff_v2_freshness_resume_v0_1",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeErrorV2("cannot load Handoff v2 S4 freshness/resume runtime")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _task_execution_recompile_bindings(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    if manifest.get("launch_mode") != "TASK_EXECUTION":
        return {}

    resume = manifest.get("resume_coordinates")
    if not isinstance(resume, dict):
        raise RuntimeErrorV2(
            "TASK_EXECUTION origin manifest resume_coordinates missing"
        )

    front_binding = manifest.get(
        "work_front_or_project_onboard_not_applicable_reason"
    )
    profile_binding = manifest.get(
        "execution_profile_revision_for_task_execution"
    )
    procedure_binding = manifest.get(
        "governed_procedure_revision_or_not_required_reason"
    )
    base_context = manifest.get("base_context")
    task_context = (
        base_context.get("task_execution_context")
        if isinstance(base_context, dict)
        else None
    )

    if not isinstance(front_binding, dict):
        raise RuntimeErrorV2("TASK_EXECUTION origin Work Front binding missing")
    if not isinstance(profile_binding, dict):
        raise RuntimeErrorV2("TASK_EXECUTION origin Execution Profile binding missing")
    if not isinstance(procedure_binding, dict):
        raise RuntimeErrorV2("TASK_EXECUTION origin procedure binding missing")
    if not isinstance(task_context, dict):
        raise RuntimeErrorV2("TASK_EXECUTION origin task-context binding missing")

    front = resume.get("front") or front_binding.get("front")
    profile_id = resume.get("profile_id") or profile_binding.get("profile_id")
    prompt_id = resume.get("prompt_id") or task_context.get("prompt_id")
    module_root = resume.get("module_root") or task_context.get("module_root")
    module = task_context.get("module")

    required = {
        "front": front,
        "profile_id": profile_id,
        "prompt_id": prompt_id,
        "module_root": module_root,
    }
    for name, value in required.items():
        if not isinstance(value, str) or not value.strip():
            raise RuntimeErrorV2(
                f"TASK_EXECUTION origin binding missing: {name}"
            )

    kwargs: dict[str, Any] = {
        "front": front,
        "profile_id": profile_id,
        "prompt_id": prompt_id,
        "module_root": module_root,
        "module": module if isinstance(module, str) and module.strip() else None,
        "procedure_id": None,
        "procedure_not_required_reason": None,
    }

    classification = procedure_binding.get("classification")
    if classification == "GRAPH_REQUIRED":
        procedure_id = (
            resume.get("procedure_id")
            or procedure_binding.get("procedure_id")
        )
        if not isinstance(procedure_id, str) or not procedure_id.strip():
            raise RuntimeErrorV2(
                "TASK_EXECUTION GRAPH_REQUIRED procedure_id missing"
            )
        kwargs["procedure_id"] = procedure_id
    elif classification == "NOT_REQUIRED":
        reason = procedure_binding.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise RuntimeErrorV2(
                "TASK_EXECUTION NOT_REQUIRED procedure reason missing"
            )
        kwargs["procedure_not_required_reason"] = reason
    else:
        raise RuntimeErrorV2(
            "TASK_EXECUTION origin procedure classification unsupported"
        )

    return kwargs

def _normalize_task_execution_live_manifest_for_started_attempt(
    root: Path,
    origin_manifest: dict[str, Any],
    live_manifest: dict[str, Any],
    result: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    # Normalize only a mathematically proven current-attempt STARTED/PENDING
    # ledger side effect. Every mismatch returns the original live manifest,
    # so ordinary S4 freshness remains fail-closed.
    import copy as _copy

    from scripts.coordination import execution_attempt_ledger_v0_1 as _ledger
    from scripts.coordination import continuity as _continuity
    from scripts.coordination.control_plane.context import (
        task_context_adapter as _task_adapter,
    )

    def rejected(reason: str) -> tuple[dict[str, Any], dict[str, Any]]:
        return live_manifest, {
            "applied": False,
            "reason": reason,
            "authority_widened": False,
            "source_drift_ignored": False,
        }

    if origin_manifest.get("launch_mode") != "TASK_EXECUTION":
        return rejected("NOT_TASK_EXECUTION")

    origin_fp = origin_manifest.get("source_state_fingerprint")
    live_fp = live_manifest.get("source_state_fingerprint")
    if origin_fp == live_fp:
        return rejected("ALREADY_FRESH")
    if not (
        isinstance(origin_fp, str)
        and len(origin_fp) == 64
        and isinstance(live_fp, str)
        and len(live_fp) == 64
    ):
        return rejected("HANDOFF_FINGERPRINT_INVALID")

    attempt_id = result.get("attempt_id")
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        return rejected("RESULT_ATTEMPT_ID_MISSING")

    origin_hash = origin_manifest.get("handoff_manifest_sha256")
    if not isinstance(origin_hash, str) or len(origin_hash) != 64:
        return rejected("ORIGIN_HANDOFF_HASH_INVALID")

    contract = _ledger.load_contract(root)
    store = _ledger.store_root(root, contract, None)
    records = _ledger.records_for_attempt(store, attempt_id)
    if len(records) != 1:
        return rejected("ATTEMPT_LEDGER_RECORD_COUNT_NOT_ONE")

    started = records[0]
    if (
        started.get("attempt_id") != attempt_id
        or started.get("attempt_stage") != "STARTED"
        or started.get("result_state") != "PENDING"
        or started.get("validator_outcome") != "NOT_RUN"
    ):
        return rejected("ATTEMPT_LEDGER_NOT_STARTED_PENDING")

    if started.get("pack_hash_or_context_hash") != origin_hash:
        return rejected("ATTEMPT_LEDGER_ORIGIN_HASH_MISMATCH")

    front_binding = origin_manifest.get(
        "work_front_or_project_onboard_not_applicable_reason"
    )
    if not isinstance(front_binding, dict):
        return rejected("ORIGIN_WORK_FRONT_BINDING_MISSING")
    if started.get("work_front_id") != front_binding.get("work_front_id"):
        return rejected("ATTEMPT_LEDGER_WORK_FRONT_MISMATCH")

    frozen_source_fp = started.get("source_fingerprint")
    if not isinstance(frozen_source_fp, str) or len(frozen_source_fp) != 64:
        return rejected("ATTEMPT_LEDGER_SOURCE_FINGERPRINT_INVALID")

    record_digest = _ledger.record_digest(started)
    expected_record = store / f"{attempt_id}__{record_digest[:12]}.yaml"
    if not expected_record.is_file():
        return rejected("STARTED_LEDGER_RECORD_FILE_MISSING")
    try:
        record_rel = expected_record.resolve().relative_to(root).as_posix()
    except ValueError:
        return rejected("STARTED_LEDGER_RECORD_OUTSIDE_ROOT")

    live_source = _continuity.build_source_state(root)
    live_source_fp = live_source.get("fingerprint_sha256")
    if not isinstance(live_source_fp, str) or len(live_source_fp) != 64:
        return rejected("LIVE_CANONICAL_SOURCE_FINGERPRINT_INVALID")

    origin_resume = origin_manifest.get("resume_coordinates")
    if not isinstance(origin_resume, dict):
        return rejected("ORIGIN_RESUME_COORDINATES_MISSING")
    if live_source.get("git_head") != origin_resume.get("git_head"):
        return rejected("CANONICAL_HEAD_DRIFT")

    dirty_paths = live_source.get("durable_dirty_paths")
    dirty_status = live_source.get("dirty_path_status")
    dirty_content = live_source.get(
        "dirty_path_content_or_symlink_fingerprint"
    )
    rename_origins = live_source.get("rename_or_copy_origins")
    if not (
        isinstance(dirty_paths, list)
        and isinstance(dirty_status, dict)
        and isinstance(dirty_content, dict)
        and isinstance(rename_origins, dict)
    ):
        return rejected("LIVE_CANONICAL_SOURCE_STATE_MALFORMED")

    if dirty_paths.count(record_rel) != 1:
        return rejected("STARTED_LEDGER_NOT_EXACTLY_ONE_DIRTY_PATH")
    if record_rel not in dirty_status or record_rel not in dirty_content:
        return rejected("STARTED_LEDGER_SOURCE_STATE_EVIDENCE_MISSING")

    normalized_source = _copy.deepcopy(live_source)
    normalized_source["durable_dirty_paths"] = [
        path for path in dirty_paths if path != record_rel
    ]
    normalized_source["dirty_path_status"].pop(record_rel, None)
    normalized_source[
        "dirty_path_content_or_symlink_fingerprint"
    ].pop(record_rel, None)
    normalized_source["rename_or_copy_origins"].pop(record_rel, None)
    normalized_source.pop("fingerprint_sha256", None)

    # This payload is a continuity source-state payload, so its
    # fingerprint MUST use continuity's canonical serializer/hash rather than
    # Handoff's generic manifest serializer. The two serializers are not byte-
    # identical; a018 proved that using the Handoff serializer creates a false
    # NON_LEDGER_CANONICAL_SOURCE_DRIFT_PRESENT result.
    normalized_source_fp = _continuity.sha256_bytes(
        _continuity._canonical_json_bytes(normalized_source)
    )
    normalized_source["fingerprint_sha256"] = normalized_source_fp

    if normalized_source_fp != frozen_source_fp:
        return rejected("NON_LEDGER_CANONICAL_SOURCE_DRIFT_PRESENT")

    origin_base = origin_manifest.get("base_context")
    live_base = live_manifest.get("base_context")
    if not isinstance(origin_base, dict) or not isinstance(live_base, dict):
        return rejected("HANDOFF_BASE_CONTEXT_MISSING")

    origin_task = origin_base.get("task_execution_context")
    live_task = live_base.get("task_execution_context")
    if not isinstance(origin_task, dict) or not isinstance(live_task, dict):
        return rejected("HANDOFF_TASK_CONTEXT_EVIDENCE_MISSING")

    origin_task_id = origin_task.get("task_context_id")
    live_task_id = live_task.get("task_context_id")
    if not (
        isinstance(origin_task_id, str)
        and len(origin_task_id) == 64
        and isinstance(live_task_id, str)
        and len(live_task_id) == 64
    ):
        return rejected("TASK_CONTEXT_ID_INVALID")

    origin_task_without_id = dict(origin_task)
    live_task_without_id = dict(live_task)
    origin_task_without_id.pop("task_context_id", None)
    live_task_without_id.pop("task_context_id", None)
    if (
        _canonical_json(origin_task_without_id)
        != _canonical_json(live_task_without_id)
    ):
        return rejected("TASK_CONTEXT_EVIDENCE_DRIFT_BEYOND_ID")

    bindings = _task_execution_recompile_bindings(origin_manifest)
    prompt_id = bindings.get("prompt_id")
    module_root = bindings.get("module_root")
    if not (
        isinstance(prompt_id, str)
        and prompt_id.strip()
        and isinstance(module_root, str)
        and module_root.strip()
    ):
        return rejected("TASK_CONTEXT_RECOMPILE_BINDINGS_INVALID")

    live_full_context = _task_adapter.build_internal_task_context(
        root,
        task_id=prompt_id,
        module_root=module_root,
    )
    if live_full_context.get("task_context_id") != live_task_id:
        return rejected("LIVE_TASK_CONTEXT_ID_EVIDENCE_MISMATCH")

    full_source = live_full_context.get("source_state")
    if not isinstance(full_source, dict):
        return rejected("LIVE_TASK_CONTEXT_SOURCE_STATE_MISSING")
    if full_source.get("fingerprint_sha256") != live_source_fp:
        return rejected("LIVE_TASK_CONTEXT_SOURCE_STATE_MISMATCH")

    reconstructed_context = _copy.deepcopy(live_full_context)
    reconstructed_context.pop("task_context_id", None)
    reconstructed_source = reconstructed_context.get("source_state")
    if not isinstance(reconstructed_source, dict):
        return rejected("RECONSTRUCTED_TASK_CONTEXT_SOURCE_STATE_MISSING")

    reconstructed_source["fingerprint_sha256"] = normalized_source_fp
    reconstructed_source["durable_dirty_path_count"] = len(
        normalized_source["durable_dirty_paths"]
    )

    reconstructed_task_id = _task_adapter._sha256_bytes(
        _task_adapter._canonical_json(reconstructed_context)
    )
    if reconstructed_task_id != origin_task_id:
        return rejected("ORIGIN_TASK_CONTEXT_ID_NOT_REPRODUCED")

    normalized_live = _copy.deepcopy(live_manifest)
    normalized_base = normalized_live.get("base_context")
    if not isinstance(normalized_base, dict):
        return rejected("NORMALIZED_BASE_CONTEXT_MISSING")
    normalized_task = normalized_base.get("task_execution_context")
    if not isinstance(normalized_task, dict):
        return rejected("NORMALIZED_TASK_CONTEXT_MISSING")
    normalized_task["task_context_id"] = reconstructed_task_id

    normalized_resume = normalized_live.get("resume_coordinates")
    if not isinstance(normalized_resume, dict):
        return rejected("NORMALIZED_RESUME_COORDINATES_MISSING")

    composite_input = {
        "head": normalized_resume.get("git_head"),
        "launch_mode": normalized_live.get("launch_mode"),
        "front": normalized_live.get(
            "work_front_or_project_onboard_not_applicable_reason"
        ),
        "profile": normalized_live.get(
            "execution_profile_revision_for_task_execution"
        ),
        "procedure": normalized_live.get(
            "governed_procedure_revision_or_not_required_reason"
        ),
        "task_context": normalized_task,
        "cursor": normalized_live.get("lifecycle_roadmap_cursor"),
    }
    reconstructed_handoff_fp = _sha_bytes(
        _canonical_json(composite_input)
    )
    if reconstructed_handoff_fp != origin_fp:
        return rejected("ORIGIN_HANDOFF_COMPOSITE_NOT_REPRODUCED")

    normalized_live["source_state_fingerprint"] = (
        reconstructed_handoff_fp
    )

    return normalized_live, {
        "applied": True,
        "reason": "CURRENT_ATTEMPT_STARTED_LEDGER_ONLY",
        "attempt_id": attempt_id,
        "ledger_record": record_rel,
        "frozen_source_fingerprint": frozen_source_fp,
        "live_source_fingerprint": live_source_fp,
        "reconstructed_task_context_id": reconstructed_task_id,
        "reconstructed_handoff_source_fingerprint": (
            reconstructed_handoff_fp
        ),
        "authority_widened": False,
        "source_drift_ignored": False,
        "unrelated_source_drift_allowed": False,
    }

def validate_result_for_return(
    root: Path,
    manifest: dict[str, Any],
    result: dict[str, Any],
    *,
    max_self_repair_attempts: int = 2,
) -> dict[str, Any]:
    root = root.resolve()
    result_runtime = _load_result_runtime(root)
    report = result_runtime.validate_with_bounded_self_repair(
        result,
        manifest,
        root=root,
        max_self_repair_attempts=max_self_repair_attempts,
    )
    if not report.get("valid"):
        return report

    freshness_runtime = _load_freshness_resume_runtime(root)
    launch_mode = manifest.get("launch_mode")
    if launch_mode not in LAUNCH_MODES:
        report["valid"] = False
        report["errors"] = [
            {
                "code": "STALE_GENERATED_CONTEXT",
                "field": "launch_mode",
                "message": "origin manifest launch_mode is invalid",
            }
        ]
        return report

    recompile_bindings = (
        _task_execution_recompile_bindings(manifest)
        if launch_mode == "TASK_EXECUTION"
        else {}
    )
    live_manifest = compile_runtime_manifest(
        root,
        launch_mode=launch_mode,
        **recompile_bindings,
    )

    normalization = {
        "applied": False,
        "reason": "NOT_REQUIRED",
        "authority_widened": False,
        "source_drift_ignored": False,
    }
    if (
        launch_mode == "TASK_EXECUTION"
        and manifest.get("source_state_fingerprint")
        != live_manifest.get("source_state_fingerprint")
    ):
        live_manifest, normalization = (
            _normalize_task_execution_live_manifest_for_started_attempt(
                root,
                manifest,
                live_manifest,
                report["result"],
            )
        )

    report["freshness_normalization"] = normalization

    freshness = freshness_runtime.validate_freshness_and_resume(
        manifest,
        live_manifest,
        report["result"],
        root=root,
    )
    report["freshness_resume"] = freshness
    if not freshness["valid"]:
        report["valid"] = False
        report["errors"] = [
            *report.get("errors", []),
            *freshness["errors"],
        ]
    return report




def write_manifest(root: Path, manifest: dict[str, Any], output_dir: Path | None) -> Path:
    out = output_dir if output_dir is not None else Path("tmp/assistant_handoff_v2_runtime")
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)
    path = (
        out
        / f"assistant_handoff_v2_runtime__{str(manifest['launch_mode']).lower()}__{manifest['handoff_manifest_sha256'][:12]}.yaml"
    )
    if path.exists():
        raise RuntimeErrorV2(f"runtime manifest already exists: {path}")
    path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=140), encoding="utf-8"
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(PROJECT_ROOT))
    parser.add_argument("--launch-mode", required=True, choices=LAUNCH_MODES)
    parser.add_argument("--front")
    parser.add_argument("--profile-id")
    parser.add_argument("--procedure-id")
    parser.add_argument("--procedure-not-required-reason")
    parser.add_argument("--prompt-id")
    parser.add_argument("--module-root")
    parser.add_argument("--module")
    parser.add_argument("--output-dir")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--print", dest="print_manifest", action="store_true")
    args = parser.parse_args()
    try:
        manifest = compile_runtime_manifest(
            Path(args.root),
            launch_mode=args.launch_mode,
            front=args.front,
            profile_id=args.profile_id,
            procedure_id=args.procedure_id,
            procedure_not_required_reason=args.procedure_not_required_reason,
            prompt_id=args.prompt_id,
            module_root=args.module_root,
            module=args.module,
        )
        output = (
            None
            if args.no_write
            else write_manifest(
                Path(args.root).resolve(),
                manifest,
                Path(args.output_dir) if args.output_dir else None,
            )
        )
        print("ASSISTANT_HANDOFF_V2_RUNTIME=PASS")
        print(f"LAUNCH_MODE={manifest['launch_mode']}")
        print("HANDOFF_MANIFEST_SHA256=" + manifest["handoff_manifest_sha256"])
        print("EXECUTION_AUTHORITY_GRANTED=false")
        print("DISPATCH_AUTHORITY_GRANTED=false")
        print("WORKER_DISPATCH_PERFORMED=false")
        if output is not None:
            print("RUNTIME_MANIFEST=" + output.relative_to(Path(args.root).resolve()).as_posix())
        if args.print_manifest:
            print(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=140))
        return 0
    except Exception as exc:
        print("ASSISTANT_HANDOFF_V2_RUNTIME=FAIL")
        print(f"ERROR={type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
