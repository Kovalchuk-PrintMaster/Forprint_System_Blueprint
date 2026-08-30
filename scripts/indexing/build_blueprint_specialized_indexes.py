from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
INDEX_ROOT = ROOT / "indexes"

IDENTITY = ROOT / "machine/module_identity_registry.yaml"
CURRENT_RELEASE = ROOT / "coordination/releases/current.yaml"
MODULE_SOURCES = ROOT / "coordination/module_sources/module_git_sources.yaml"
COORDINATION_SOURCES = (
    ROOT / "coordination/registry/coordination_source_registry_v0_1.yaml"
)
MODULE_POLICY = ROOT / "coordination/module_policy/module_policy_index.yaml"
STANDARDS_INDEX = ROOT / "coordination/standards/index.yaml"
GOVERNANCE_INDEX = ROOT / "coordination/standards/governance/index.yaml"
MACHINE_CONTRACTS = ROOT / "machine/contracts.yaml"
INCOMING_REQUESTS = ROOT / "coordination/incoming_requests"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _dump(data: dict) -> str:
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )


def _canonical_identity() -> tuple[set[str], dict[str, str]]:
    data = _load(IDENTITY)
    canonical = set(data.get("canonical_module_ids", []))
    aliases = {
        item["alias"]: item["canonical_id"]
        for item in data.get("aliases", [])
        if isinstance(item, dict)
        and isinstance(item.get("alias"), str)
        and isinstance(item.get("canonical_id"), str)
    }
    return canonical, aliases


def _prompt_entries(data: dict) -> list[dict]:
    if isinstance(data.get("prompt_queue"), list):
        return list(data["prompt_queue"])

    result: list[dict] = []
    for key in ("active_prompts", "completed_prompts", "historical_prompts"):
        value = data.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    copied = dict(item)
                    copied["_source_bucket"] = key
                    result.append(copied)
    return result


def _prompt_entry_status(item: dict) -> str:
    module_execution = item.get("module_execution")
    if isinstance(module_execution, dict):
        value = module_execution.get("status")
        if isinstance(value, str):
            return value

    for key in ("status", "original_status"):
        value = item.get(key)
        if isinstance(value, str):
            return value
    return "unknown"


def _prompt_review_status(item: dict) -> str | None:
    review = item.get("blueprint_review")
    if isinstance(review, dict):
        value = review.get("status")
        if isinstance(value, str):
            return value
    return None


def _prompt_path(index_path: Path, item: dict) -> tuple[str | None, bool | None]:
    value = item.get("file")
    if not isinstance(value, str) or not value:
        return None, None

    if value.startswith("coordination/"):
        candidate = ROOT / value
        rel = value
    else:
        candidate = index_path.parent / value
        rel = candidate.relative_to(ROOT).as_posix()

    return rel, candidate.is_file()


def _lifecycle_replacement(path: str | None) -> str | None:
    if not path:
        return None

    candidates = []
    if "/approved/" in path:
        candidates.append(path.replace("/approved/", "/completed/", 1))
    if "/drafts/" in path:
        candidates.append(path.replace("/drafts/", "/approved/", 1))
        candidates.append(path.replace("/drafts/", "/completed/", 1))

    for candidate in candidates:
        if (ROOT / candidate).is_file():
            return candidate
    return None


def render_prompts() -> str:
    canonical, aliases = _canonical_identity()
    queues = []

    root = ROOT / "coordination/outgoing_prompts"
    for index_path in sorted(root.glob("*/index.yaml")):
        data = _load(index_path)
        directory_id = index_path.parent.name
        module_id = data.get("module", directory_id)
        lifecycle = data.get("lifecycle")
        explicit_authority = data.get("authority")

        if lifecycle == "historical_non_authoritative" or explicit_authority == "none":
            authority_state = "historical_non_authoritative"
        elif module_id in canonical:
            authority_state = "current_queue_surface"
        elif module_id in aliases:
            authority_state = "historical_alias_surface"
        else:
            authority_state = "unknown_identity_surface"

        entries = []
        status_counts: Counter[str] = Counter()
        review_counts: Counter[str] = Counter()

        for item in _prompt_entries(data):
            prompt_path, prompt_exists = _prompt_path(index_path, item)
            execution_status = _prompt_entry_status(item)
            review_status = _prompt_review_status(item)
            status_counts[execution_status] += 1
            if review_status:
                review_counts[review_status] += 1

            completion_report = None
            module_execution = item.get("module_execution")
            if isinstance(module_execution, dict):
                value = module_execution.get("completion_report")
                if isinstance(value, str):
                    completion_report = value

            target_module = item.get("target_module")
            if not isinstance(target_module, str):
                target_module = module_id if isinstance(module_id, str) else directory_id

            completion_scope = None
            if completion_report:
                if (ROOT / completion_report).exists():
                    completion_scope = "blueprint_repository"
                elif target_module != "forprint_system_blueprint":
                    completion_scope = "target_module_repository"
                else:
                    completion_scope = "unresolved_blueprint_path"

            entries.append(
                {
                    "prompt_id": item.get("prompt_id"),
                    "sequence": item.get("sequence"),
                    "target_module": target_module,
                    "execution_status": execution_status,
                    "review_status": review_status,
                    "prompt_path": prompt_path,
                    "prompt_path_exists": prompt_exists,
                    "prompt_lifecycle_replacement": (
                        _lifecycle_replacement(prompt_path)
                        if prompt_exists is False
                        else None
                    ),
                    "completion_report": completion_report,
                    "completion_report_scope": completion_scope,
                }
            )

        queues.append(
            {
                "module_id": module_id,
                "directory_id": directory_id,
                "schema_version": data.get("schema_version", "legacy_prompt_index"),
                "index_path": index_path.relative_to(ROOT).as_posix(),
                "identity_state": (
                    "canonical"
                    if module_id in canonical
                    else "historical_alias"
                    if module_id in aliases
                    else "unknown"
                ),
                "canonical_id_if_alias": aliases.get(module_id),
                "authority_state": authority_state,
                "entry_count": len(entries),
                "execution_status_counts": dict(sorted(status_counts.items())),
                "review_status_counts": dict(sorted(review_counts.items())),
                "entries": entries,
            }
        )

    return _dump(
        {
            "schema_version": "forprint_blueprint_prompt_query_index_v0_1",
            "status": "derived_non_authoritative",
            "authority": "none",
            "queues": queues,
        }
    )


def _roadmap_steps(data: dict) -> list[dict]:
    roadmap = data.get("roadmap")
    if isinstance(roadmap, list):
        return [item for item in roadmap if isinstance(item, dict)]
    return []


def _coordination_source_modules() -> list[dict]:
    data = _load(COORDINATION_SOURCES)
    value = data.get("modules", [])
    return [item for item in value if isinstance(item, dict)]


def render_roadmaps() -> str:
    current = _load(CURRENT_RELEASE)
    declared_by_module = {
        item.get("module_id"): item
        for item in _coordination_source_modules()
        if isinstance(item.get("module_id"), str)
    }

    discovered = {}
    for path in sorted((ROOT / "coordination/roadmaps").glob("*.yaml")):
        data = _load(path)
        module_id = data.get("module", path.stem)
        steps = _roadmap_steps(data)
        statuses = Counter(
            str(item.get("status", "unknown"))
            for item in steps
        )
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        discovered[module_id] = {
            "module_id": module_id,
            "path": path.relative_to(ROOT).as_posix(),
            "present": True,
            "metadata_status": metadata.get("status"),
            "planning_authority": metadata.get("planning_authority"),
            "current_step_id": metadata.get("current_step_id"),
            "step_count": len(steps),
            "status_counts": dict(sorted(statuses.items())),
        }

    records = []
    module_ids = set(discovered) | set(declared_by_module)
    for module_id in sorted(item for item in module_ids if isinstance(item, str)):
        record = dict(
            discovered.get(
                module_id,
                {
                    "module_id": module_id,
                    "path": None,
                    "present": False,
                    "metadata_status": None,
                    "planning_authority": None,
                    "current_step_id": None,
                    "step_count": 0,
                    "status_counts": {},
                },
            )
        )

        registry = declared_by_module.get(module_id, {})
        sources = registry.get("sources")
        if not isinstance(sources, dict):
            sources = {}
        roadmap_source = sources.get("roadmap")
        if not isinstance(roadmap_source, dict):
            roadmap_source = {}

        record["declared_path"] = roadmap_source.get("path")
        record["declared_availability"] = roadmap_source.get("availability")
        record["declared_repository"] = roadmap_source.get("repository")

        if module_id == "forprint_system_blueprint":
            record["effective_authority_note"] = (
                "coordination/releases/current.yaml is effective release/work "
                "authority; self_coordination roadmap is historical projection"
            )

        records.append(record)

    detail_root = (
        ROOT / "coordination/roadmaps/details/forprint_system_blueprint"
    )
    detail_documents = [
        path.relative_to(ROOT).as_posix()
        for path in sorted(detail_root.rglob("*"))
        if path.is_file()
        and path.suffix.lower() in {".md", ".yaml", ".yml", ".json"}
    ]

    return _dump(
        {
            "schema_version": "forprint_blueprint_roadmap_query_index_v0_2",
            "status": "derived_non_authoritative",
            "authority": "none",
            "effective_release_authority": "coordination/releases/current.yaml",
            "blueprint_effective_roadmap_root": (
                "coordination/roadmaps/details/forprint_system_blueprint/"
            ),
            "historical_non_authoritative_projections": current.get(
                "historical_non_authoritative_projections",
                [],
            ),
            "modules": records,
            "blueprint_detail_document_count": len(detail_documents),
            "blueprint_detail_documents": detail_documents,
        }
    )


def render_governance() -> str:
    current = _load(CURRENT_RELEASE)
    standards = _load(STANDARDS_INDEX)
    governance = _load(GOVERNANCE_INDEX)

    records = []
    for item in standards.get("standards", []):
        if not isinstance(item, dict):
            continue
        rel = item.get("file")
        if isinstance(rel, str):
            full_path = f"coordination/standards/{rel}"
            exists = (ROOT / full_path).is_file()
        else:
            full_path = None
            exists = None
        records.append(
            {
                "standard_id": item.get("standard_id"),
                "title": item.get("title"),
                "path": full_path,
                "exists": exists,
                "status": item.get("status"),
                "adoption_mode": item.get("adoption_mode"),
            }
        )

    group = governance.get("standards_group", {})
    group_docs = group.get("documents", []) if isinstance(group, dict) else []

    template_root = ROOT / "coordination/templates"
    template_documents = [
        path.relative_to(ROOT).as_posix()
        for path in sorted(template_root.rglob("*"))
        if path.is_file()
        and path.suffix.lower() in {".md", ".yaml", ".yml", ".json", ".mk"}
    ]

    return _dump(
        {
            "schema_version": "forprint_blueprint_governance_query_index_v0_2",
            "status": "derived_non_authoritative",
            "authority": "none",
            "effective_release": {
                "path": "coordination/releases/current.yaml",
                "projection_id": current.get("metadata", {}).get("projection_id"),
                "release_status": current.get("metadata", {}).get("status"),
                "base_release": current.get("release", {}).get("base_release"),
                "hardening_release": current.get("release", {}).get(
                    "hardening_release"
                ),
                "hardening_state": current.get("release", {}).get(
                    "hardening_state"
                ),
                "current_slice": current.get("release", {}).get("current_slice"),
            },
            "effective_governance": current.get("effective_governance", {}),
            "progression_gate_policy": current.get("progression_gate_policy", {}),
            "historical_non_authoritative_projections": current.get(
                "historical_non_authoritative_projections",
                [],
            ),
            "standards_count": len(records),
            "standards": records,
            "governance_group_document_count": len(group_docs),
            "coordination_template_document_count": len(template_documents),
            "coordination_template_documents": template_documents,
        }
    )


def render_contracts() -> str:
    machine = _load(MACHINE_CONTRACTS)
    machine_contracts = []
    for item in machine.get("contracts", []):
        if not isinstance(item, dict):
            continue
        machine_contracts.append(
            {
                "id": item.get("id"),
                "provider": item.get("provider"),
                "consumer": item.get("consumer"),
                "status": item.get("status"),
                "data_objects": item.get("data_objects", []),
            }
        )

    prompt_packages = []
    root = ROOT / "coordination/prompt_contracts"
    if root.is_dir():
        for module_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            for package_dir in sorted(
                path for path in module_dir.iterdir() if path.is_dir()
            ):
                yaml_files = sorted(package_dir.glob("*.yaml"))
                snapshot = package_dir / "source_prompt_snapshot.md"
                prompt_packages.append(
                    {
                        "module_id": module_dir.name,
                        "package_id": package_dir.name,
                        "path": package_dir.relative_to(ROOT).as_posix(),
                        "yaml_artifacts": [
                            path.relative_to(ROOT).as_posix()
                            for path in yaml_files
                        ],
                        "source_prompt_snapshot": (
                            snapshot.relative_to(ROOT).as_posix()
                            if snapshot.is_file()
                            else None
                        ),
                    }
                )

    return _dump(
        {
            "schema_version": "forprint_blueprint_contract_query_index_v0_1",
            "status": "derived_non_authoritative",
            "authority": "none",
            "machine_contract_count": len(machine_contracts),
            "machine_contracts": machine_contracts,
            "prompt_contract_package_count": len(prompt_packages),
            "prompt_contract_packages": prompt_packages,
        }
    )


def render_source_coverage() -> str:
    canonical, aliases = _canonical_identity()
    module_sources_data = _load(MODULE_SOURCES)
    source_modules = module_sources_data.get("module_git_sources", {}).get(
        "modules",
        [],
    )
    source_by_id = {
        item.get("module_id"): item
        for item in source_modules
        if isinstance(item, dict) and isinstance(item.get("module_id"), str)
    }

    coordination_by_id = {
        item.get("module_id"): item
        for item in _coordination_source_modules()
        if isinstance(item.get("module_id"), str)
    }

    policy_data = _load(MODULE_POLICY)
    policy_modules = policy_data.get("module_policy_index", {}).get("modules", [])
    policy_ids = {
        item.get("module_id")
        for item in policy_modules
        if isinstance(item, dict) and isinstance(item.get("module_id"), str)
    }

    records = []
    for module_id in sorted(canonical):
        source = source_by_id.get(module_id)
        coordination = coordination_by_id.get(module_id)
        source_info = {}
        if source:
            source_info = {
                "repo_status": source.get("repo_status"),
                "development_status": source.get("development_status"),
                "local_path": source.get("local_path"),
                "repo_url": source.get("repo_url"),
            }

        coordination_info = {}
        if coordination:
            sources = coordination.get("sources")
            if isinstance(sources, dict):
                coordination_info = {
                    key: {
                        "path": value.get("path"),
                        "availability": value.get("availability"),
                        "repository": value.get("repository"),
                    }
                    for key, value in sources.items()
                    if isinstance(value, dict)
                }

        policy_root = ROOT / "coordination/module_policy" / module_id
        policy_documents = []
        if policy_root.is_dir():
            policy_documents = [
                path.relative_to(ROOT).as_posix()
                for path in sorted(policy_root.rglob("*"))
                if path.is_file()
                and path.suffix.lower() in {".md", ".yaml", ".yml", ".json"}
            ]

        records.append(
            {
                "module_id": module_id,
                "module_source_registered": source is not None,
                "module_source": source_info,
                "coordination_source_registered": coordination is not None,
                "coordination_sources": coordination_info,
                "module_policy_registered": module_id in policy_ids,
                "module_policy_documents": policy_documents,
            }
        )

    current_specialized_ids = (
        set(source_by_id)
        | set(coordination_by_id)
        | policy_ids
    )
    unknown_current_ids = sorted(
        item
        for item in current_specialized_ids
        if item not in canonical and item not in aliases
    )

    return _dump(
        {
            "schema_version": "forprint_blueprint_source_coverage_index_v0_2",
            "status": "derived_non_authoritative",
            "authority": "none",
            "canonical_module_count": len(canonical),
            "modules": records,
            "historical_aliases": [
                {
                    "alias": alias,
                    "canonical_id": canonical_id,
                }
                for alias, canonical_id in sorted(aliases.items())
            ],
            "unknown_specialized_registry_ids": unknown_current_ids,
        }
    )


def _route_file_count(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(
        1
        for item in path.rglob("*")
        if item.is_file() and item.name != ".gitkeep"
    )


def render_incoming_requests() -> str:
    canonical, aliases = _canonical_identity()
    physical_ids = {
        path.name
        for path in INCOMING_REQUESTS.iterdir()
        if path.is_dir()
    }

    current_routes = []
    for module_id in sorted(canonical):
        root = INCOMING_REQUESTS / module_id
        new_dir = root / "new"
        reviewed_dir = root / "reviewed"
        archived_dir = root / "archived"
        current_routes.append(
            {
                "module_id": module_id,
                "path": root.relative_to(ROOT).as_posix(),
                "present": root.is_dir(),
                "new_path": new_dir.relative_to(ROOT).as_posix(),
                "new_present": new_dir.is_dir(),
                "reviewed_path": reviewed_dir.relative_to(ROOT).as_posix(),
                "reviewed_present": reviewed_dir.is_dir(),
                "archived_path": archived_dir.relative_to(ROOT).as_posix(),
                "archived_present": archived_dir.is_dir(),
                "new_request_count": _route_file_count(new_dir),
                "reviewed_request_count": _route_file_count(reviewed_dir),
                "archived_request_count": _route_file_count(archived_dir),
                "authority_state": "current_canonical_route",
            }
        )

    historical_alias_routes = []
    for alias, canonical_id in sorted(aliases.items()):
        root = INCOMING_REQUESTS / alias
        if not root.exists():
            continue
        historical_alias_routes.append(
            {
                "alias": alias,
                "canonical_id": canonical_id,
                "path": root.relative_to(ROOT).as_posix(),
                "present": root.is_dir(),
                "authority_state": "historical_alias_route",
                "current_use_allowed": False,
            }
        )

    unknown_ids = sorted(
        item
        for item in physical_ids
        if item not in canonical and item not in aliases
    )

    return _dump(
        {
            "schema_version": "forprint_blueprint_incoming_request_query_index_v0_1",
            "status": "derived_non_authoritative",
            "authority": "none",
            "routing_rule": (
                "Current incoming-request routes use canonical module IDs. "
                "Historical alias directories are evidence-only."
            ),
            "canonical_route_count": len(current_routes),
            "current_routes": current_routes,
            "historical_alias_routes": historical_alias_routes,
            "unknown_directory_ids": unknown_ids,
        }
    )


def expected_files() -> dict[Path, str]:
    return {
        INDEX_ROOT / "prompts.yaml": render_prompts(),
        INDEX_ROOT / "roadmaps.yaml": render_roadmaps(),
        INDEX_ROOT / "governance.yaml": render_governance(),
        INDEX_ROOT / "contracts.yaml": render_contracts(),
        INDEX_ROOT / "source_coverage.yaml": render_source_coverage(),
        INDEX_ROOT / "incoming_requests.yaml": render_incoming_requests(),
    }


def build(check: bool) -> int:
    drift = []
    for path, content in expected_files().items():
        if check:
            actual = path.read_text(encoding="utf-8") if path.is_file() else ""
            if actual != content:
                drift.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if drift:
        print("BLUEPRINT_SPECIALIZED_INDEX_DRIFT=" + ",".join(drift))
        return 1

    if check:
        print("BLUEPRINT_SPECIALIZED_INDEX_CHECK=PASS")
    else:
        print("BLUEPRINT_SPECIALIZED_INDEX_BUILD=PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return build(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
