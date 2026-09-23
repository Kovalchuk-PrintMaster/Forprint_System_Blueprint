from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml

ALLOWED_STATES = {
    "DISCOVERED",
    "INVENTORIED",
    "BOOTSTRAP_READY",
    "BOOTSTRAPPED",
    "VERIFIED_WORK_READY",
}


class PreparationRegistryError(ValueError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PreparationRegistryError(f"missing required source: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PreparationRegistryError(f"source is not a YAML mapping: {path}")
    return data


def _source(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha(path),
    }


def _roadmap_path(root: Path, module_id: str) -> Path | None:
    path = root / "coordination/roadmaps" / f"{module_id}.yaml"
    return path if path.is_file() else None


def _seed_path(root: Path, module_id: str) -> Path | None:
    path = (
        root
        / ("coordination/roadmaps/details/forprint_system_blueprint/portfolio_rebuild_seeds")
        / f"{module_id}.yaml"
    )
    return path if path.is_file() else None


def _obligations(
    ledger: dict[str, Any],
    module_id: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    modules = ledger.get("modules")
    if not isinstance(modules, dict):
        return [], []
    block = modules.get(module_id)
    if not isinstance(block, dict):
        return [], []
    obligations = block.get("obligations")
    refs = block.get("source_refs")
    return (
        [row for row in obligations if isinstance(row, dict)]
        if isinstance(obligations, list)
        else [],
        [str(value) for value in refs] if isinstance(refs, list) else [],
    )


def _repository_source_map(module_sources: dict[str, Any]) -> dict[str, dict[str, Any]]:
    root = module_sources.get("module_git_sources")
    if not isinstance(root, dict):
        raise PreparationRegistryError("module_git_sources root missing")
    modules = root.get("modules")
    if not isinstance(modules, list):
        raise PreparationRegistryError("module_git_sources modules list missing")
    rows: dict[str, dict[str, Any]] = {}
    for row in modules:
        if not isinstance(row, dict):
            continue
        module_id = row.get("module_id")
        if isinstance(module_id, str) and module_id:
            rows[module_id] = row
    return rows


def _git_repository_detected(local_path: str | None) -> bool:
    if not local_path:
        return False
    path = Path(local_path)
    if not path.exists():
        return False
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _repository_projection(
    module_id: str,
    source_map: dict[str, dict[str, Any]],
    preparation_required: bool,
) -> dict[str, Any]:
    source = source_map.get(module_id, {})
    local_path = source.get("local_path")
    repo_url = source.get("repo_url")
    repo_status = source.get("repo_status", "UNREGISTERED")
    local_exists = bool(local_path and Path(str(local_path)).exists())
    git_detected = _git_repository_detected(str(local_path) if local_path is not None else None)
    provisioning_required = bool(
        preparation_required
        and not git_detected
        and (
            repo_url is None
            or repo_status
            in {
                "planned_directory_created",
                "planned_not_created",
                "confirm_required",
                "UNREGISTERED",
            }
        )
    )
    return {
        "repository_local_path": local_path,
        "repository_url": repo_url,
        "repository_branch": source.get("branch"),
        "repository_status": repo_status,
        "repository_path_exists": local_exists,
        "repository_git_detected": git_detected,
        "repository_provisioning_required": provisioning_required,
    }


def _preparation_state(
    module_id: str,
    row: dict[str, Any],
    semantic_report_present: bool,
) -> tuple[str, bool, str | None]:
    if module_id == "forprint_system_blueprint":
        return "INVENTORIED", False, "COORDINATOR_CONTROL_PLANE_EXEMPT"

    inventory_state = str(row.get("inventory_state", "NOT_STARTED"))
    consolidation_state = str(row.get("consolidation_state", "NOT_STARTED"))
    readiness = str(row.get("autonomous_readiness_state", "NOT_READY"))

    if readiness in {"VERIFIED_WORK_READY", "READY"}:
        return "VERIFIED_WORK_READY", True, None
    if readiness == "BOOTSTRAPPED":
        return "BOOTSTRAPPED", True, None
    if (
        module_id == "logistics_service"
        and semantic_report_present
        and inventory_state == "COMPLETE_FIRST_PASS"
        and consolidation_state == "COMPLETE"
    ):
        return "BOOTSTRAP_READY", True, None
    if inventory_state != "NOT_STARTED" or consolidation_state != "NOT_STARTED":
        return "INVENTORIED", True, None
    return "DISCOVERED", True, None


def _bootstrap_prompt_state(
    module_id: str,
    control: dict[str, Any],
) -> str:
    if module_id != "logistics_service":
        return "NOT_PREPARED"
    block = control.get("logistics_bootstrap_prompt_replacement")
    if not isinstance(block, dict):
        return "UNKNOWN"
    if block.get("released") is True:
        return "REPLACEMENT_RELEASED"
    if block.get("candidate_state") == "READY_FOR_EXPLICIT_RELEASE_AUTHORIZATION":
        return "REPLACEMENT_CANDIDATE_AWAITING_EXPLICIT_RELEASE_AUTHORIZATION"
    return str(block.get("candidate_state", "UNKNOWN"))


def _blockers(
    module_id: str,
    preparation_state: str,
    prompt_state: str,
    obligation_count: int,
    roadmap_path: Path | None,
) -> list[str]:
    blockers: list[str] = []
    if roadmap_path is None:
        blockers.append("CANONICAL_MODULE_ROADMAP_MISSING")
    if preparation_state == "DISCOVERED":
        blockers.append("FORENSIC_INVENTORY_NOT_STARTED")
    elif preparation_state == "INVENTORIED" and module_id != "forprint_system_blueprint":
        blockers.append("BOOTSTRAP_NOT_READY")
    elif preparation_state == "BOOTSTRAP_READY":
        if prompt_state == "REPLACEMENT_CANDIDATE_AWAITING_EXPLICIT_RELEASE_AUTHORIZATION":
            blockers.append("BOOTSTRAP_REPLACEMENT_PROMPT_RELEASE_AUTHORIZATION_REQUIRED")
    if obligation_count and module_id != "logistics_service":
        blockers.append("BLUEPRINT_OBLIGATIONS_REQUIRE_MODULE_REPOSITORY_EVIDENCE_REVIEW")
    return blockers


def build_registry(
    *,
    root: Path,
    inventory_state_path: Path,
    obligations_path: Path,
    control_path: Path,
    semantic_report_path: Path,
    module_sources_path: Path,
) -> dict[str, Any]:
    root = root.resolve()
    inventory = _load(inventory_state_path)
    ledger = _load(obligations_path)
    control = _load(control_path)
    module_sources = _load(module_sources_path)
    repository_sources = _repository_source_map(module_sources)
    semantic_report_present = semantic_report_path.is_file()

    modules = inventory.get("modules")
    if not isinstance(modules, list):
        raise PreparationRegistryError("inventory state has no modules list")

    legacy_risk = {
        str(value)
        for value in inventory.get("special_legacy_risk_modules", [])
        if isinstance(value, str)
    }

    rows: list[dict[str, Any]] = []
    for source_row in sorted(
        (row for row in modules if isinstance(row, dict)),
        key=lambda row: str(row.get("module_id", "")),
    ):
        module_id = str(source_row.get("module_id", ""))
        if not module_id:
            raise PreparationRegistryError("inventory module row has no module_id")

        roadmap = _roadmap_path(root, module_id)
        seed = _seed_path(root, module_id)
        obligations, obligation_refs = _obligations(ledger, module_id)
        state, required, exemption = _preparation_state(
            module_id,
            source_row,
            semantic_report_present,
        )
        if state not in ALLOWED_STATES:
            raise PreparationRegistryError(f"invalid state for {module_id}: {state}")

        prompt_state = _bootstrap_prompt_state(module_id, control)
        repository = _repository_projection(
            module_id,
            repository_sources,
            required,
        )
        blockers = _blockers(
            module_id,
            state,
            prompt_state,
            len(obligations),
            roadmap,
        )
        if repository["repository_provisioning_required"]:
            blockers.insert(0, "REPOSITORY_PROVISIONING_REQUIRED")
        evidence_refs = [
            value
            for key, value in source_row.items()
            if key.endswith("_ref") and isinstance(value, str)
        ]
        evidence_refs.extend(obligation_refs)
        if module_id == "logistics_service" and semantic_report_present:
            evidence_refs.append(semantic_report_path.relative_to(root).as_posix())

        rows.append(
            {
                "module_id": module_id,
                "preparation_required": required,
                "preparation_exemption_reason": exemption,
                "preparation_state": state,
                "inventory_state": source_row.get("inventory_state"),
                "consolidation_state": source_row.get("consolidation_state"),
                "roadmap_enrichment_state": source_row.get("roadmap_enrichment_state"),
                "autonomous_readiness_state": source_row.get("autonomous_readiness_state"),
                "roadmap_path": (roadmap.relative_to(root).as_posix() if roadmap else None),
                "portfolio_seed_path": (seed.relative_to(root).as_posix() if seed else None),
                "historical_legacy_risk": module_id in legacy_risk,
                "pending_blueprint_obligation_count": len(obligations),
                "pending_blueprint_obligations": obligations,
                "bootstrap_prompt_state": prompt_state,
                **repository,
                "blockers": blockers,
                "evidence_refs": sorted(set(evidence_refs)),
                "next_action_from_inventory_program": source_row.get("next_action"),
            }
        )

    required_rows = [row for row in rows if row["preparation_required"] is True]
    all_verified = bool(required_rows) and all(
        row["preparation_state"] == "VERIFIED_WORK_READY" for row in required_rows
    )
    counts = {
        state: sum(1 for row in rows if row["preparation_state"] == state)
        for state in sorted(ALLOWED_STATES)
    }

    return {
        "schema_version": "forprint_module_preparation_registry_v0_1",
        "status": "ACTIVE_CURRENT",
        "authority": "BLUEPRINT_PORTFOLIO_PREPARATION_PROJECTION",
        "source_precedence_note": (
            "Current Control Plane and reviewed reconciliation evidence override stale "
            "historical pilot-selection hints in older inventory-program projections."
        ),
        "sources": {
            "module_inventory_state": _source(inventory_state_path, root),
            "blueprint_module_obligations": _source(obligations_path, root),
            "control_plane_program": _source(control_path, root),
            "module_git_sources": _source(module_sources_path, root),
            "logistics_semantic_reconciliation": (
                _source(semantic_report_path, root) if semantic_report_present else None
            ),
        },
        "state_machine": [
            "DISCOVERED",
            "INVENTORIED",
            "BOOTSTRAP_READY",
            "BOOTSTRAPPED",
            "VERIFIED_WORK_READY",
        ],
        "module_count": len(rows),
        "preparation_required_module_count": len(required_rows),
        "state_counts": counts,
        "all_required_modules_verified_work_ready": all_verified,
        "development_priority_selection_allowed": all_verified,
        "worker_launch_allowed": False,
        "automatic_prompt_claim_allowed": False,
        "automatic_accept_allowed": False,
        "automatic_release_allowed": False,
        "modules": rows,
    }


def build_queue(registry: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for module in registry["modules"]:
        if module["preparation_required"] is not True:
            continue
        state = module["preparation_state"]
        prompt_state = module["bootstrap_prompt_state"]
        if module.get("repository_provisioning_required") is True:
            action = "AWAIT_EXPLICIT_REPOSITORY_PROVISIONING_AUTHORITY"
        elif state == "DISCOVERED":
            action = "FORENSIC_INVENTORY"
        elif state == "INVENTORIED":
            action = "COMPLETE_BOOTSTRAP_PREPARATION"
        elif state == "BOOTSTRAP_READY":
            if prompt_state == ("REPLACEMENT_CANDIDATE_AWAITING_EXPLICIT_RELEASE_AUTHORIZATION"):
                action = "AWAIT_EXPLICIT_BOOTSTRAP_REPLACEMENT_RELEASE_AUTHORIZATION"
            else:
                action = "OPERATOR_BOOTSTRAP_FLOW"
        elif state == "BOOTSTRAPPED":
            action = "VERIFY_DEVELOPMENT_READINESS"
        else:
            action = "NO_PREPARATION_ACTION"

        rows.append(
            {
                "module_id": module["module_id"],
                "preparation_state": state,
                "action": action,
                "historical_legacy_risk": module["historical_legacy_risk"],
                "pending_blueprint_obligation_count": module["pending_blueprint_obligation_count"],
                "blockers": module["blockers"],
                "development_priority_rank": None,
                "dispatch_allowed": False,
            }
        )

    return {
        "schema_version": "forprint_module_preparation_queue_v0_1",
        "status": "ACTIVE_CURRENT",
        "purpose": "operator-driven module preparation only",
        "ordering": "module_id_lexicographic_not_development_priority",
        "development_priority_selection_performed": False,
        "development_priority_selection_allowed": registry[
            "development_priority_selection_allowed"
        ],
        "worker_launch_allowed": False,
        "operator_selection_required": True,
        "queue_rows": sorted(rows, key=lambda row: row["module_id"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--registry-output", required=True)
    parser.add_argument("--queue-output", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    inventory_state = root / (
        "coordination/internal_work/blueprint/module_inventory/"
        "2026-09-04__module_inventory_program_state_v0_1.yaml"
    )
    obligations = root / (
        "coordination/internal_work/blueprint/module_preparation/"
        "blueprint_module_obligations_v0_1.yaml"
    )
    control = root / (
        "coordination/internal_work/blueprint/governance/"
        "2026-09-06__blueprint__control_plane_module_memory_semantic_convergence_program_v0_1.yaml"
    )
    semantic = root / (
        "coordination/internal_work/blueprint/module_inventory/logistics_service/"
        "2026-09-08__logistics_service__semantic_roadmap_reconciliation_apply_v0_1.yaml"
    )
    module_sources = root / "coordination/module_sources/module_git_sources.yaml"

    registry = build_registry(
        root=root,
        inventory_state_path=inventory_state,
        obligations_path=obligations,
        control_path=control,
        semantic_report_path=semantic,
        module_sources_path=module_sources,
    )
    queue = build_queue(registry)

    registry_output = Path(args.registry_output)
    queue_output = Path(args.queue_output)
    if not registry_output.is_absolute():
        registry_output = root / registry_output
    if not queue_output.is_absolute():
        queue_output = root / queue_output
    registry_output.parent.mkdir(parents=True, exist_ok=True)
    queue_output.parent.mkdir(parents=True, exist_ok=True)

    registry_output.write_text(
        yaml.safe_dump(registry, sort_keys=False, allow_unicode=True, width=112),
        encoding="utf-8",
    )
    queue_output.write_text(
        yaml.safe_dump(queue, sort_keys=False, allow_unicode=True, width=112),
        encoding="utf-8",
    )

    logistics = next(row for row in registry["modules"] if row["module_id"] == "logistics_service")
    inspector = next(
        row for row in registry["modules"] if row["module_id"] == "forprint_project_inspector"
    )
    print("MODULE_PREPARATION_REGISTRY=PASS")
    print(f"MODULE_COUNT={registry['module_count']}")
    print(f"PREPARATION_REQUIRED_MODULE_COUNT={registry['preparation_required_module_count']}")
    print(f"LOGISTICS_PREPARATION_STATE={logistics['preparation_state']}")
    print(f"LOGISTICS_BOOTSTRAP_PROMPT_STATE={logistics['bootstrap_prompt_state']}")
    print(f"INSPECTOR_PREPARATION_STATE={inspector['preparation_state']}")
    print(
        "INSPECTOR_REPOSITORY_PROVISIONING_REQUIRED="
        f"{str(inspector['repository_provisioning_required']).lower()}"
    )
    print(
        "INSPECTOR_PENDING_BLUEPRINT_OBLIGATION_COUNT="
        f"{inspector['pending_blueprint_obligation_count']}"
    )
    print(
        "ALL_REQUIRED_MODULES_VERIFIED_WORK_READY="
        f"{str(registry['all_required_modules_verified_work_ready']).lower()}"
    )
    print(
        "DEVELOPMENT_PRIORITY_SELECTION_ALLOWED="
        f"{str(registry['development_priority_selection_allowed']).lower()}"
    )
    print("WORKER_LAUNCH_ALLOWED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
