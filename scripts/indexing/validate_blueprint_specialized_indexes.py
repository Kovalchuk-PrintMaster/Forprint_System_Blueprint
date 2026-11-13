from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate() -> list[str]:
    errors: list[str] = []

    check = subprocess.run(
        [
            str(ROOT / ".venv_blueprint/bin/python"),
            "scripts/indexing/build_blueprint_specialized_indexes.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if check.returncode != 0:
        errors.append("SPECIALIZED_INDEX_DRIFT:" + check.stdout.strip())

    prompts_path = ROOT / "indexes/prompts.yaml"
    roadmaps_path = ROOT / "indexes/roadmaps.yaml"
    governance_path = ROOT / "indexes/governance.yaml"
    contracts_path = ROOT / "indexes/contracts.yaml"
    coverage_path = ROOT / "indexes/source_coverage.yaml"
    incoming_requests_path = ROOT / "indexes/incoming_requests.yaml"

    for path in (
        prompts_path,
        roadmaps_path,
        governance_path,
        contracts_path,
        coverage_path,
        incoming_requests_path,
    ):
        if not path.is_file():
            errors.append(
                "SPECIALIZED_INDEX_MISSING:" + path.relative_to(ROOT).as_posix()
            )

    if prompts_path.is_file():
        prompts = _load(prompts_path)
        for queue in prompts.get("queues", []):
            if (
                queue.get("authority_state") == "current_queue_surface"
                and queue.get("identity_state") != "canonical"
            ):
                errors.append(
                    "CURRENT_PROMPT_QUEUE_NONCANONICAL_ID:"
                    + str(queue.get("module_id"))
                )
            if (
                queue.get("module_id") == "forprint_operational_registry"
                and queue.get("authority_state") != "historical_non_authoritative"
            ):
                errors.append("LEGACY_OPERATIONS_QUEUE_REGAINED_AUTHORITY")

    if governance_path.is_file():
        governance = _load(governance_path)
        effective = governance.get("effective_release", {})
        if effective.get("path") != "coordination/releases/current.yaml":
            errors.append("EFFECTIVE_RELEASE_AUTHORITY_DRIFT")

    if coverage_path.is_file():
        coverage = _load(coverage_path)
        unknown = coverage.get("unknown_specialized_registry_ids", [])
        if unknown:
            errors.append(
                "UNKNOWN_SPECIALIZED_REGISTRY_IDS:" + ",".join(unknown)
            )

        for module in coverage.get("modules", []):
            if not isinstance(module, dict):
                continue
            module_id = str(module.get("module_id"))
            sources = module.get("coordination_sources", {})
            if not isinstance(sources, dict):
                continue
            for source_name, source in sources.items():
                if not isinstance(source, dict):
                    continue
                if source.get("repository") != "forprint_system_blueprint":
                    continue
                if source.get("availability") != "present":
                    continue
                rel = source.get("path")
                if not isinstance(rel, str):
                    errors.append(
                        "PRESENT_BLUEPRINT_SOURCE_WITHOUT_PATH:"
                        + module_id
                        + ":"
                        + str(source_name)
                    )
                    continue
                candidate = ROOT if rel == "." else ROOT / rel
                if not candidate.exists():
                    errors.append(
                        "PRESENT_BLUEPRINT_SOURCE_MISSING:"
                        + module_id
                        + ":"
                        + str(source_name)
                        + ":"
                        + rel
                    )

    if incoming_requests_path.is_file():
        incoming = _load(incoming_requests_path)
        routes = incoming.get("current_routes", [])
        identity = _load(ROOT / "machine/module_identity_registry.yaml")
        canonical_ids = set(identity.get("canonical_module_ids", []))
        route_ids = {
            item.get("module_id")
            for item in routes
            if isinstance(item, dict)
        }
        if route_ids != canonical_ids:
            errors.append(
                "CANONICAL_INCOMING_REQUEST_ROUTE_COVERAGE:"
                + ",".join(
                    sorted(
                        str(item)
                        for item in canonical_ids.symmetric_difference(route_ids)
                    )
                )
            )
        for route in routes:
            if not isinstance(route, dict):
                continue
            module_id = str(route.get("module_id"))
            for key in (
                "present",
                "new_present",
                "reviewed_present",
                "archived_present",
            ):
                if route.get(key) is not True:
                    errors.append(
                        "INCOMING_REQUEST_ROUTE_INCOMPLETE:"
                        + module_id
                        + ":"
                        + key
                    )
            if route.get("authority_state") != "current_canonical_route":
                errors.append(
                    "INCOMING_REQUEST_ROUTE_AUTHORITY_DRIFT:" + module_id
                )

        for alias in incoming.get("historical_alias_routes", []):
            if not isinstance(alias, dict):
                continue
            if alias.get("authority_state") != "historical_alias_route":
                errors.append(
                    "LEGACY_INCOMING_REQUEST_ROUTE_REGAINED_AUTHORITY:"
                    + str(alias.get("alias"))
                )
            if alias.get("current_use_allowed") is not False:
                errors.append(
                    "LEGACY_INCOMING_REQUEST_ROUTE_CURRENT_USE_ALLOWED:"
                    + str(alias.get("alias"))
                )

        unknown_routes = incoming.get("unknown_directory_ids", [])
        if unknown_routes:
            errors.append(
                "UNKNOWN_INCOMING_REQUEST_DIRECTORY_IDS:"
                + ",".join(str(item) for item in unknown_routes)
            )

    reporting_standard = (
        ROOT
        / "coordination/standards/governance/"
        "module_prompt_execution_and_reporting_protocol.md"
    )
    if reporting_standard.is_file():
        text = reporting_standard.read_text(encoding="utf-8")
        stale_incoming_reports = "coordination" + "/incoming_reports/"
        if stale_incoming_reports in text:
            errors.append("STALE_INCOMING_REPORTS_SURFACE_IN_ACTIVE_STANDARD")
        if "coordination/review_packets/<module_id>/processed/" not in text:
            errors.append("CURRENT_REVIEW_PACKET_SURFACE_MISSING_FROM_STANDARD")
        fence_count = sum(
            1
            for line in text.splitlines()
            if line.strip().startswith("```")
        )
        if fence_count % 2 != 0:
            errors.append("PROMPT_REPORTING_STANDARD_MARKDOWN_FENCE_UNBALANCED")

    tracking_snapshot = (
        ROOT
        / "coordination/prompt_contracts/logistics_service/"
        "logistics_service_tracking_events_v0_1/source_prompt_snapshot.md"
    )
    if not tracking_snapshot.is_file():
        errors.append("TRACKING_EVENTS_SOURCE_SNAPSHOT_MISSING")

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    expected_make_ref = (
        "TRACKING_EVENTS_SOURCE_PROMPT ?= "
        "coordination/prompt_contracts/logistics_service/"
        "logistics_service_tracking_events_v0_1/source_prompt_snapshot.md"
    )
    if expected_make_ref not in makefile:
        errors.append("TRACKING_EVENTS_PREFLIGHT_SOURCE_NOT_SNAPSHOT")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR={error}")
        print("BLUEPRINT_SPECIALIZED_INDEX_VALIDATION=FAIL")
        return 1

    print("BLUEPRINT_SPECIALIZED_INDEX_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
