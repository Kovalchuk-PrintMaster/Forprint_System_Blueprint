#!/usr/bin/env python3
"""Validate execution dependency registry against the executable Make DAG."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/automation/execution_dependency_contract_v0_1.yaml"
REGISTRY = ROOT / "coordination/registry/execution_dependency_registry_v0_1.yaml"
GRAPH = ROOT / "indexes/execution_dependency_graph.yaml"
MAKEFILE = ROOT / "Makefile"

ALLOWED_CLASSES = {
    "canonical_required",
    "derived_required",
    "derived_persistent",
    "optional",
    "historical_or_runtime_nonrequired",
    "external_tool",
    "runtime_environment",
}
TARGET_REQUIRED_FIELDS = {
    "target",
    "requires",
    "produces",
    "optional_observes",
    "requires_tools",
    "side_effect_scope",
}
ARTIFACT_REQUIRED_FIELDS = {
    "id",
    "path",
    "class",
    "authority",
    "lifecycle",
    "freshness",
    "missing_behavior",
}
TARGET_RE = re.compile(r"^([A-Za-z0-9_.@%/+,\-]+)\s*:(?![=])\s*(.*)$")


def fail(message: str) -> int:
    print("EXECUTION_DEPENDENCY_CONTRACT=FAIL")
    print("ERROR=" + message)
    return 1


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def logical_make_lines(text: str) -> list[str]:
    lines = text.splitlines()
    result: list[str] = []
    buffer = ""

    for raw in lines:
        stripped = raw.rstrip()
        if buffer:
            buffer += stripped.lstrip()
        else:
            buffer = stripped

        if buffer.endswith("\\"):
            buffer = buffer[:-1] + " "
            continue

        result.append(buffer)
        buffer = ""

    if buffer:
        result.append(buffer)
    return result


def make_dependencies(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for line in logical_make_lines(text):
        if not line or line[0].isspace():
            continue
        match = TARGET_RE.match(line)
        if not match:
            continue
        target = match.group(1)
        if target.startswith("."):
            continue
        rhs = match.group(2).split(" #", 1)[0].strip()
        deps = [
            token
            for token in rhs.split()
            if token and token not in {"|", ";"} and not token.startswith("$(") and "=" not in token
        ]
        result[target] = deps
    return result


def main() -> int:
    for path in (CONTRACT, REGISTRY, GRAPH, MAKEFILE):
        if not path.is_file():
            return fail(f"missing={path.relative_to(ROOT)}")

    registry = load_yaml(REGISTRY)
    graph = load_yaml(GRAPH)
    make_deps = make_dependencies(MAKEFILE.read_text(encoding="utf-8"))

    artifacts_list = registry.get("artifacts")
    targets_list = registry.get("targets")
    tools_list = registry.get("tools")

    if not isinstance(artifacts_list, list) or not artifacts_list:
        return fail("artifacts_missing")
    if not isinstance(targets_list, list) or not targets_list:
        return fail("targets_missing")
    if not isinstance(tools_list, list) or not tools_list:
        return fail("tools_missing")

    artifacts: dict[str, dict] = {}
    for row in artifacts_list:
        missing = sorted(ARTIFACT_REQUIRED_FIELDS - set(row))
        if missing:
            return fail(f"artifact_missing_fields={row.get('id')}:{','.join(missing)}")
        artifact_id = row["id"]
        if artifact_id in artifacts:
            return fail(f"duplicate_artifact={artifact_id}")
        if row["class"] not in ALLOWED_CLASSES:
            return fail(f"invalid_artifact_class={artifact_id}:{row['class']}")
        if (
            row["class"]
            in {
                "derived_required",
                "derived_persistent",
                "historical_or_runtime_nonrequired",
            }
            and row["authority"] != "none"
        ):
            return fail(f"non_authoritative_artifact_claims_authority={artifact_id}")
        if row["class"] == "derived_required":
            if not row.get("producer"):
                return fail(f"derived_artifact_without_producer={artifact_id}")
            if row["freshness"] != "same_run":
                return fail(f"runtime_derived_artifact_not_same_run={artifact_id}")
        if row["class"] == "derived_persistent":
            if not row.get("producer"):
                return fail(f"persistent_derived_without_producer={artifact_id}")
            if row["freshness"] != "exact_source_fingerprint":
                return fail(f"persistent_derived_freshness={artifact_id}")
        if row["class"] == "canonical_required":
            if not (ROOT / row["path"]).exists():
                return fail(f"canonical_required_missing={artifact_id}:{row['path']}")
        artifacts[artifact_id] = row

    tools = {row.get("id") for row in tools_list if isinstance(row, dict)}
    if None in tools:
        return fail("tool_without_id")

    targets: dict[str, dict] = {}
    for row in targets_list:
        missing = sorted(TARGET_REQUIRED_FIELDS - set(row))
        if missing:
            return fail(f"target_missing_fields={row.get('target')}:{','.join(missing)}")
        target_name = row["target"]
        if target_name in targets:
            return fail(f"duplicate_target={target_name}")
        if target_name not in make_deps:
            return fail(f"make_target_missing={target_name}")

        for field in ("requires", "produces", "optional_observes"):
            values = row[field]
            if not isinstance(values, list):
                return fail(f"target_field_not_list={target_name}:{field}")
            for artifact_id in values:
                if artifact_id not in artifacts:
                    return fail(f"unknown_artifact={target_name}:{field}:{artifact_id}")

        for tool_id in row["requires_tools"]:
            if tool_id not in tools:
                return fail(f"unknown_tool={target_name}:{tool_id}")

        required_ids = set(row["requires"])
        optional_ids = set(row["optional_observes"])
        if required_ids & optional_ids:
            return fail(f"artifact_required_and_optional={target_name}")

        for artifact_id in row["requires"]:
            artifact = artifacts[artifact_id]
            if artifact["class"] == "historical_or_runtime_nonrequired":
                return fail(
                    f"historical_runtime_artifact_promoted_to_required={target_name}:{artifact_id}"
                )
            if artifact["class"] == "derived_required":
                producer = artifact["producer"]
                if producer not in make_deps[target_name]:
                    return fail(
                        f"producer_not_direct_make_prerequisite="
                        f"{target_name}:{artifact_id}:{producer}"
                    )
            if artifact["class"] == "derived_persistent":
                producer = artifact["producer"]
                if producer in make_deps[target_name]:
                    return fail(
                        f"persistent_derived_check_must_not_auto_refresh="
                        f"{target_name}:{artifact_id}:{producer}"
                    )

        for artifact_id in row["optional_observes"]:
            artifact = artifacts[artifact_id]
            if artifact["class"] not in {
                "optional",
                "historical_or_runtime_nonrequired",
            }:
                return fail(
                    f"invalid_optional_observation_class="
                    f"{target_name}:{artifact_id}:{artifact['class']}"
                )

        for artifact_id in row["produces"]:
            if artifacts[artifact_id].get("producer") != target_name:
                return fail(
                    f"producer_mismatch={target_name}:{artifact_id}:"
                    f"{artifacts[artifact_id].get('producer')}"
                )

        targets[target_name] = row

    for artifact_id, artifact in artifacts.items():
        producer = artifact.get("producer")
        if artifact["class"] in {"derived_required", "derived_persistent"}:
            if producer not in targets:
                return fail(f"derived_producer_not_registered={artifact_id}:{producer}")
            if artifact_id not in targets[producer]["produces"]:
                return fail(f"derived_producer_missing_output={artifact_id}:{producer}")

    for root_surface in registry.get("root_surfaces", []):
        target_name = root_surface.get("target")
        if target_name not in make_deps:
            return fail(f"root_surface_missing={target_name}")
        for required_target in root_surface.get("requires_targets", []):
            if required_target not in make_deps[target_name]:
                return fail(f"root_surface_missing_direct_target={target_name}:{required_target}")

    if graph.get("source_registry") != REGISTRY.relative_to(ROOT).as_posix():
        return fail("graph_registry_binding_mismatch")
    if graph.get("status") != "derived_non_authoritative":
        return fail("graph_status_mismatch")
    if graph.get("authority") != "none":
        return fail("graph_claims_authority")

    print("EXECUTION_DEPENDENCY_CONTRACT=PASS")
    print(f"REGISTERED_ARTIFACTS={len(artifacts)}")
    print(f"REGISTERED_TARGETS={len(targets)}")
    print(
        "DERIVED_REQUIRED_ARTIFACTS="
        + str(sum(1 for row in artifacts.values() if row["class"] == "derived_required"))
    )
    print(
        "DERIVED_PERSISTENT_ARTIFACTS="
        + str(sum(1 for row in artifacts.values() if row["class"] == "derived_persistent"))
    )
    print(
        "HISTORICAL_RUNTIME_NONREQUIRED="
        + str(
            sum(
                1
                for row in artifacts.values()
                if row["class"] == "historical_or_runtime_nonrequired"
            )
        )
    )
    print("DIRECT_PRODUCER_EDGES=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
