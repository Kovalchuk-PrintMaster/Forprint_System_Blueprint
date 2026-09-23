#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

continuity = importlib.import_module("scripts.coordination.continuity")
lifecycle = importlib.import_module("scripts.coordination.continuity_lifecycle")
projections = importlib.import_module("scripts.coordination.build_continuity_projections")
handoff = importlib.import_module("scripts.coordination.build_assistant_handoff_archive")

CONTRACT = ROOT / "coordination/standards/automation/module_continuity_transfer_contract_v0_1.yaml"

EXPECTED_HISTORICAL_CORE_HASHES = {
    "scripts/coordination/continuity.py": "7971e3e3e8249a9b4cb023ae31ae48bceb7374d82257dbc092ff315231e7f246",
    "scripts/coordination/continuity_lifecycle.py": "54f5bf0b3eb8da8a9e95592e7f479aa31133289c6907a8f9438ef4664077165d",
    "scripts/coordination/build_continuity_projections.py": "f3dae14ffd53a56b5dbe686af1b3ee17a4202fa2c4df8b40c88f993ba88ffdb7",
    "scripts/coordination/build_assistant_handoff_archive.py": "9b61279e1ca6c05fae40f54f7295d5483c5c7fd3843a7a618421b029df6b95e7",
}
REQUIRED_PROFILE_FIELDS = [
    "module_id",
    "module_root",
    "event_root",
    "projection_root",
    "bootstrap_index",
    "mission_source",
    "source_state_mode",
    "authority_scope",
]
REQUIRED_SURFACES = {
    "immutable_event_store",
    "lifecycle_enforcement",
    "generated_projections",
    "deterministic_zero_context_handoff",
}


class TransferValidationError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(root: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if cp.returncode:
        raise TransferValidationError("git command failed: " + " ".join(args) + "\n" + cp.stdout)
    return cp.stdout.strip()


def validate_contract() -> dict[str, Any]:
    if not CONTRACT.is_file():
        raise TransferValidationError("transfer contract missing")
    raw = CONTRACT.read_text(encoding="utf-8")
    value = yaml.safe_load(raw)
    if not isinstance(value, dict):
        raise TransferValidationError("transfer contract must be a mapping")
    if value.get("schema_version") != "forprint_module_continuity_transfer_contract_v0_1":
        raise TransferValidationError("transfer contract schema mismatch")
    if value.get("authority") != "none":
        raise TransferValidationError("transfer contract authority must be none")
    for key in (
        "mutation_authority_conferred",
        "release_authority_conferred",
        "worker_dispatch_authority_conferred",
        "foreign_repository_write_authority_conferred",
    ):
        if value.get(key) is not False:
            raise TransferValidationError(f"{key} must be false")
    if value.get("required_profile_fields") != REQUIRED_PROFILE_FIELDS:
        raise TransferValidationError("required profile fields mismatch")
    modes = value.get("source_state_modes")
    if modes != ["working_tree", "git_tracked"]:
        raise TransferValidationError("source state modes mismatch")
    surfaces = value.get("portable_surfaces")
    if not isinstance(surfaces, list):
        raise TransferValidationError("portable_surfaces must be a list")
    ids = {row.get("id") for row in surfaces if isinstance(row, dict)}
    if ids != REQUIRED_SURFACES:
        raise TransferValidationError("portable surface set mismatch")
    forbidden_count = raw.lower().count("forprint_system_blueprint")
    if forbidden_count:
        raise TransferValidationError("portable contract contains module-specific Blueprint path")
    return value


def validate_core_hashes() -> dict[str, Any]:
    """Preserve historical u179h evidence while pinning the current validated core."""

    contract = validate_contract()
    evolution = contract.get("post_reference_acceptance_evolution")
    if not isinstance(evolution, dict):
        raise TransferValidationError("post-reference core evolution policy missing")

    historical = evolution.get("historical_accepted_core_sha256")
    if historical != EXPECTED_HISTORICAL_CORE_HASHES:
        raise TransferValidationError("historical accepted core hash evidence changed")

    current = evolution.get("current_validated_core_sha256")
    if not isinstance(current, dict) or set(current) != set(EXPECTED_HISTORICAL_CORE_HASHES):
        raise TransferValidationError("current validated core hash set is incomplete")

    if evolution.get("current_core_byte_identity_to_reference_required") is not False:
        raise TransferValidationError(
            "post-reference evolution must not rewrite historical acceptance as a live byte lock"
        )
    if evolution.get("historical_reference_acceptance_rewritten") is not False:
        raise TransferValidationError(
            "historical reference acceptance must remain immutable evidence"
        )
    current_work_id = evolution.get("current_validated_under_work_id")
    if not isinstance(current_work_id, str) or not current_work_id.strip():
        raise TransferValidationError("current core evolution owning work item missing")

    current_change_scope = evolution.get("current_change_scope")
    if not isinstance(current_change_scope, str) or not current_change_scope.strip():
        raise TransferValidationError("current core evolution change scope missing")

    current_change_paths = evolution.get("current_change_paths")
    if (
        not isinstance(current_change_paths, list)
        or not current_change_paths
        or not all(isinstance(value, str) and value in current for value in current_change_paths)
    ):
        raise TransferValidationError("current core evolution change paths invalid")

    actual: dict[str, str] = {}
    for rel, expected_current in current.items():
        path = ROOT / rel
        if not path.is_file():
            raise TransferValidationError("current core missing: " + rel)
        digest = _sha256(path)
        actual[rel] = digest
        if digest != expected_current:
            raise TransferValidationError(
                f"current validated core drift: {rel} expected={expected_current} actual={digest}"
            )

    return {
        "historical_accepted_core_sha256": dict(historical),
        "current_validated_core_sha256": dict(current),
        "actual_current_core_sha256": actual,
        "current_validated_under_work_id": evolution["current_validated_under_work_id"],
        "historical_reference_acceptance_rewritten": False,
        "current_core_byte_identity_to_reference_required": False,
    }


def _write_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _fixture_roadmap() -> dict[str, Any]:
    return {
        "schema_version": "fixture_roadmap_v0_1",
        "status": "test_fixture",
        "authority": "none",
        "accepted_foundations": [],
        "steps": [
            {"order": 1, "id": "fixture_continuity", "state": "complete", "work": "fixture-work"}
        ],
        "next_action": {"step": 2, "id": "fixture_next"},
        "deferred_after_continuity_foundation": [],
    }


def _prepare_fixture(root: Path, *, module_id: str, nested: bool) -> dict[str, Any]:
    root.mkdir(parents=True)
    _git(root, "init")
    _git(root, "config", "user.email", "forprint@example.invalid")
    _git(root, "config", "user.name", "ForPrint Test")

    if nested:
        domain = root / "src" / "warehouse" / "inventory" / "domain.txt"
    else:
        domain = root / "catalog.txt"
    domain.parent.mkdir(parents=True, exist_ok=True)
    domain.write_text(f"{module_id} baseline\n", encoding="utf-8")

    (root / "AGENTS.md").write_text("# Fixture assistant policy\n", encoding="utf-8")
    (root / "coordination/bootstrap").mkdir(parents=True, exist_ok=True)
    (root / "coordination/bootstrap/START_HERE.md").write_text(
        "# Fixture bootstrap\n", encoding="utf-8"
    )
    _write_yaml(
        root / "coordination/bootstrap/index_v0_1.yaml",
        {"schema_version": "fixture_bootstrap_v0_1", "status": "active", "authority": "none"},
    )
    (root / "coordination/global_policy").mkdir(parents=True, exist_ok=True)
    (root / "coordination/global_policy/forprint_project_doctrine.md").write_text(
        "# Fixture mission\n", encoding="utf-8"
    )
    # The accepted event-store contract requires a checkpoint genesis. Create one
    # before lifecycle enforcement is enabled, matching the production migration model.
    _git(root, "add", ".")
    _git(root, "commit", "-m", "sterile fixture baseline")
    event_root = root / "coordination/continuity/events"
    baseline_hashes = {str(domain.relative_to(root)): _sha256(domain)}
    baseline_state = continuity.build_source_state(
        root, bounded_final_applied_artifact_hashes=baseline_hashes
    )
    historical_spec = {
        "schema_version": continuity.SPEC_SCHEMA,
        "event_id": f"evt-{module_id}-genesis",
        "work_id": "fixture-bootstrap-history",
        "occurred_at": "2026-09-12T11:59:00Z",
        "actor": "transfer-validator",
        "summary": "fixture historical genesis checkpoint",
        "bootstrap_historical_import": True,
        "historical_import_scope": ["sterile fixture baseline"],
        "what_changed": ["established sterile fixture baseline"],
        "why": "satisfy append-only event-store genesis semantics",
        "evidence": [{"kind": "sterile_fixture_genesis", "result": "PASS"}],
        "decision_rationale": "historical bootstrap checkpoint precedes lifecycle enforcement",
        "rejected_alternative_when_material": "fabricating lifecycle transitions before enforcement",
        "blockers": [],
        "unknowns": [],
        "next_actions": [{"order": i, "id": f"bootstrap-next-{i}"} for i in range(1, 6)],
        "source_state_before": baseline_state,
        "source_state_after": baseline_state,
        "final_applied_artifact_hashes": baseline_hashes,
        "external_baseline_preserved": True,
    }
    historical_spec_path = root / "tmp" / "fixture-genesis.yaml"
    _write_yaml(historical_spec_path, historical_spec)
    continuity.append_checkpoint(root=root, spec_path=historical_spec_path, event_root=event_root)

    _write_yaml(
        root / "coordination/standards/automation/continuity_contract_v0_1.yaml",
        {
            "schema_version": "fixture_continuity_contract_v0_1",
            "status": "active",
            "authority": "none",
            "lifecycle": {"enforcement": {"enabled": True}},
        },
    )
    _write_yaml(
        root / "coordination/registry/execution_dependency_registry_v0_1.yaml",
        {
            "schema_version": "fixture_dependency_registry_v0_1",
            "status": "active",
            "authority": "none",
            "artifacts": [],
            "targets": [],
            "root_surfaces": [],
        },
    )
    # Compatibility layout consumed by the accepted handoff v1 core.
    _write_yaml(
        root
        / "coordination/roadmaps/details/forprint_system_blueprint/continuity"
        / "2026-09-10__continuity_assistant_handoff_micro_roadmap_v0_1.yaml",
        _fixture_roadmap(),
    )

    lifecycle.plan(
        root=root,
        event_root=event_root,
        event_id=f"evt-{module_id}-planned",
        work_id="fixture-work",
        actor="transfer-validator",
        summary="fixture work planned",
        reason="sterile transfer validation",
    )
    lifecycle.activate(
        root=root,
        event_root=event_root,
        event_id=f"evt-{module_id}-active",
        work_id="fixture-work",
        actor="transfer-validator",
        summary="fixture work active",
        reason="sterile transfer validation",
    )

    hashes = {str(domain.relative_to(root)): _sha256(domain)}
    state = continuity.build_source_state(root, bounded_final_applied_artifact_hashes=hashes)
    spec = {
        "schema_version": continuity.SPEC_SCHEMA,
        "event_id": f"evt-{module_id}-checkpoint",
        "work_id": "fixture-work",
        "occurred_at": "2026-09-12T12:00:00Z",
        "actor": "transfer-validator",
        "summary": "fixture checkpoint",
        "what_changed": ["established sterile fixture continuity state"],
        "why": "prove accepted core works against a non-Blueprint repository root",
        "evidence": [{"kind": "sterile_fixture", "result": "PASS"}],
        "decision_rationale": "root-configured accepted core is reused unchanged",
        "rejected_alternative_when_material": "copying or editing accepted core",
        "blockers": [],
        "unknowns": [],
        "next_actions": [{"order": i, "id": f"fixture-next-{i}"} for i in range(1, 6)],
        "source_state_before": state,
        "source_state_after": state,
        "final_applied_artifact_hashes": hashes,
        "external_baseline_preserved": True,
    }
    spec_path = root / "tmp" / "fixture-checkpoint.yaml"
    _write_yaml(spec_path, spec)
    continuity.append_checkpoint(root=root, spec_path=spec_path, event_root=event_root)
    lifecycle.validation_passed(
        root=root,
        event_root=event_root,
        event_id=f"evt-{module_id}-validated",
        work_id="fixture-work",
        actor="transfer-validator",
        summary="fixture validated",
        evidence=["sterile fixture acceptance"],
    )
    lifecycle.close(
        root=root,
        event_root=event_root,
        event_id=f"evt-{module_id}-closed",
        work_id="fixture-work",
        actor="transfer-validator",
        summary="fixture closed",
        evidence=["sterile fixture acceptance"],
    )

    docs = projections.build_projection_documents(root)
    if tuple(docs) != projections.PROJECTION_IDS:
        raise TransferValidationError("projection set mismatch")
    blob1, manifest1, _name1 = handoff.expected_archive(root)
    blob2, manifest2, _name2 = handoff.expected_archive(root)
    if blob1 != blob2 or manifest1 != manifest2:
        raise TransferValidationError("handoff archive is not byte deterministic")

    profile = {
        "module_id": module_id,
        "module_root": str(root),
        "event_root": str(event_root),
        "projection_root": str(root / "coordination/continuity/projections"),
        "bootstrap_index": str(root / "coordination/bootstrap/index_v0_1.yaml"),
        "mission_source": str(root / "coordination/global_policy/forprint_project_doctrine.md"),
        "source_state_mode": "working_tree",
        "authority_scope": "read_and_local_bounded_continuity_only",
    }
    if list(profile) != REQUIRED_PROFILE_FIELDS:
        raise TransferValidationError("fixture profile field order/set mismatch")
    return profile


def _invalid_transition_probe(root: Path) -> tuple[bool, bool]:
    probe = root / "invalid_probe"
    probe.mkdir()
    _git(probe, "init")
    _git(probe, "config", "user.email", "forprint@example.invalid")
    _git(probe, "config", "user.name", "ForPrint Test")
    tracked = probe / "tracked.txt"
    tracked.write_text("baseline\n", encoding="utf-8")
    _git(probe, "add", "tracked.txt")
    _git(probe, "commit", "-m", "baseline")

    event_root = probe / "coordination/continuity/events"
    lifecycle.plan(
        root=probe,
        event_root=event_root,
        event_id="evt-invalid-planned",
        work_id="invalid-work",
        actor="transfer-validator",
        summary="invalid probe planned",
        reason="verify fail closed",
    )
    lifecycle.activate(
        root=probe,
        event_root=event_root,
        event_id="evt-invalid-active",
        work_id="invalid-work",
        actor="transfer-validator",
        summary="invalid probe active",
        reason="verify fail closed",
    )

    before_files = sorted(p.name for p in event_root.glob("*.yaml"))
    before_state = continuity.build_source_state(probe)["fingerprint_sha256"]
    try:
        lifecycle.close(
            root=probe,
            event_root=event_root,
            event_id="evt-invalid-illegal-close",
            work_id="invalid-work",
            actor="transfer-validator",
            summary="forbidden direct close",
            evidence=["must fail"],
        )
    except lifecycle.LifecycleError:
        pass
    else:
        raise TransferValidationError("invalid ACTIVE->CLOSED transition was accepted")

    after_files = sorted(p.name for p in event_root.glob("*.yaml"))
    after_state = continuity.build_source_state(probe)["fingerprint_sha256"]
    return before_files != after_files, before_state != after_state


def run_validation() -> dict[str, Any]:
    validate_contract()
    validate_core_hashes()

    temp = Path(tempfile.mkdtemp(prefix="forprint_continuity_transfer_"))
    try:
        catalog = _prepare_fixture(
            temp / "catalog_module", module_id="catalog-module", nested=False
        )
        warehouse = _prepare_fixture(
            temp / "warehouse_module", module_id="warehouse-module", nested=True
        )
        appended, mutated = _invalid_transition_probe(temp)
    finally:
        shutil.rmtree(temp, ignore_errors=True)

    return {
        "portable_event_store": True,
        "portable_lifecycle": True,
        "portable_projections": True,
        "portable_handoff": True,
        "sterile_catalog_fixture": "PASS",
        "sterile_warehouse_fixture": "PASS",
        "invalid_transition_event_appended": appended,
        "invalid_transition_mutation_performed": mutated,
        "blueprint_specific_paths_in_portable_contract": (
            CONTRACT.read_text(encoding="utf-8").lower().count("forprint_system_blueprint")
        ),
        "core_modification_performed": False,
        "foreign_module_write_performed": False,
        "worker_dispatch_performed": False,
        "profiles": [catalog, warehouse],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = run_validation()
        if result["invalid_transition_event_appended"]:
            raise TransferValidationError("invalid transition appended an event")
        if result["invalid_transition_mutation_performed"]:
            raise TransferValidationError("invalid transition mutated source")
        if result["blueprint_specific_paths_in_portable_contract"] != 0:
            raise TransferValidationError("portable contract contains Blueprint path")
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        print("MODULE_CONTINUITY_TRANSFER_VALIDATION=PASS")
        print("PORTABLE_EVENT_STORE=true")
        print("PORTABLE_LIFECYCLE=true")
        print("PORTABLE_PROJECTIONS=true")
        print("PORTABLE_HANDOFF=true")
        print("STERILE_CATALOG_FIXTURE=PASS")
        print("STERILE_WAREHOUSE_FIXTURE=PASS")
        print("INVALID_TRANSITION_EVENT_APPENDED=false")
        print("INVALID_TRANSITION_MUTATION_PERFORMED=false")
        print("BLUEPRINT_SPECIFIC_PATHS_IN_PORTABLE_CONTRACT=0")
        print("CORE_MODIFICATION_PERFORMED=false")
        print("HISTORICAL_CORE_BASELINE_PRESERVED=true")
        print("CURRENT_CORE_BYTE_IDENTITY_TO_REFERENCE_REQUIRED=false")
        print("CURRENT_CORE_INTEGRITY_PINNED=true")
        print("FOREIGN_MODULE_WRITE_PERFORMED=false")
        print("WORKER_DISPATCH_PERFORMED=false")
        return 0
    except Exception as exc:
        print("MODULE_CONTINUITY_TRANSFER_VALIDATION=FAIL")
        print(f"ERROR={type(exc).__name__}:{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
