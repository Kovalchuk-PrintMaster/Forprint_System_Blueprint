#!/usr/bin/env python3
"""Build deterministic non-authoritative execution dependency graph."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "coordination/registry/execution_dependency_registry_v0_1.yaml"
OUTPUT = ROOT / "indexes/execution_dependency_graph.yaml"


class Dumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_registry() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


def build_graph() -> dict:
    registry = load_registry()
    artifacts = {row["id"]: row for row in registry.get("artifacts", [])}
    targets = {row["target"]: row for row in registry.get("targets", [])}

    edges: list[dict] = []
    for target_name, target in sorted(targets.items()):
        for artifact_id in target.get("requires", []):
            artifact = artifacts[artifact_id]
            kind = {
                "derived_required": "derived_requirement",
                "derived_persistent": "persistent_derived_requirement",
                "canonical_required": "canonical_requirement",
            }.get(artifact["class"], "requirement")
            edges.append(
                {
                    "kind": kind,
                    "producer": artifact.get("producer"),
                    "artifact": artifact_id,
                    "path": artifact["path"],
                    "consumer": target_name,
                    "freshness": artifact["freshness"],
                }
            )
        for artifact_id in target.get("optional_observes", []):
            artifact = artifacts[artifact_id]
            edges.append(
                {
                    "kind": "optional_observation",
                    "producer": artifact.get("producer"),
                    "artifact": artifact_id,
                    "path": artifact["path"],
                    "consumer": target_name,
                    "freshness": artifact["freshness"],
                }
            )

    consumers_by_artifact: dict[str, list[str]] = {artifact_id: [] for artifact_id in artifacts}
    for edge in edges:
        consumers_by_artifact[edge["artifact"]].append(edge["consumer"])

    artifact_rows = []
    for artifact_id, artifact in sorted(artifacts.items()):
        artifact_rows.append(
            {
                **artifact,
                "consumers": sorted(consumers_by_artifact[artifact_id]),
            }
        )

    target_rows = []
    for _target_name, target in sorted(targets.items()):
        target_rows.append(
            {
                **target,
                "derived_predecessors": sorted(
                    {
                        artifacts[artifact_id].get("producer")
                        for artifact_id in target.get("requires", [])
                        if artifacts[artifact_id].get("producer")
                    }
                ),
            }
        )

    return {
        "schema_version": "forprint_execution_dependency_graph_v0_1",
        "status": "derived_non_authoritative",
        "authority": "none",
        "source_registry": REGISTRY.relative_to(ROOT).as_posix(),
        "source_registry_sha256": sha256(REGISTRY),
        "summary": {
            "artifact_count": len(artifact_rows),
            "target_count": len(target_rows),
            "derived_requirement_edge_count": sum(
                1 for edge in edges if edge["kind"] == "derived_requirement"
            ),
            "persistent_derived_requirement_edge_count": sum(
                1 for edge in edges if edge["kind"] == "persistent_derived_requirement"
            ),
            "canonical_requirement_edge_count": sum(
                1 for edge in edges if edge["kind"] == "canonical_requirement"
            ),
            "optional_observation_edge_count": sum(
                1 for edge in edges if edge["kind"] == "optional_observation"
            ),
            "same_run_artifact_count": sum(
                1 for row in artifact_rows if row["freshness"] == "same_run"
            ),
        },
        "artifacts": artifact_rows,
        "targets": target_rows,
        "edges": sorted(
            edges,
            key=lambda row: (
                row["kind"],
                str(row["producer"]),
                row["consumer"],
                row["artifact"],
            ),
        ),
    }


def render() -> str:
    return yaml.dump(
        build_graph(),
        Dumper=Dumper,
        allow_unicode=True,
        sort_keys=False,
        width=112,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render()

    if args.check:
        if not OUTPUT.is_file():
            print(f"EXECUTION_DEPENDENCY_GRAPH=DRIFT missing={OUTPUT.relative_to(ROOT)}")
            return 1
        if OUTPUT.read_text(encoding="utf-8") != rendered:
            print(f"EXECUTION_DEPENDENCY_GRAPH=DRIFT stale={OUTPUT.relative_to(ROOT)}")
            return 1
        print("EXECUTION_DEPENDENCY_GRAPH_CHECK=PASS")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"EXECUTION_DEPENDENCY_GRAPH={OUTPUT.relative_to(ROOT)}")
    print("EXECUTION_DEPENDENCY_GRAPH_APPLY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
