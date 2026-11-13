from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
GENERATOR_REGISTRY = ROOT / "coordination/registry/generator_derivation_registry_v0_1.yaml"
DEPENDENCY_REGISTRY = ROOT / "coordination/registry/execution_dependency_registry_v0_1.yaml"
DEPENDENCY_GRAPH = ROOT / "indexes/execution_dependency_graph.yaml"
MAKEFILE = ROOT / "Makefile"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_projection_builder_is_semantically_registered_generator() -> None:
    registry = load(GENERATOR_REGISTRY)
    row = next(
        item for item in registry["generators"] if item["id"] == "continuity_projection_builder"
    )
    assert row["script"] == ("scripts/coordination/build_continuity_projections.py")
    assert row["authority"] == "none"
    assert row["check_mode"] == "native_exact_check"
    assert row["apply_mode"] == "explicit_apply"


def test_persistent_projection_dependency_does_not_hide_mutating_prerequisite() -> None:
    registry = load(DEPENDENCY_REGISTRY)
    artifacts = {row["id"]: row for row in registry["artifacts"]}
    targets = {row["target"]: row for row in registry["targets"]}

    projection = artifacts["continuity_projection_set"]
    assert projection["class"] == "derived_persistent"
    assert projection["producer"] == "continuity-projections-refresh"
    assert projection["freshness"] == "exact_source_fingerprint"

    check_target = targets["continuity-projections-check"]
    assert "continuity_projection_set" in check_target["requires"]

    makefile = MAKEFILE.read_text(encoding="utf-8")
    line = next(
        raw for raw in makefile.splitlines() if raw.startswith("continuity-projections-check:")
    )
    assert "continuity-projections-refresh" not in line.split()[1:]


def test_execution_graph_exposes_persistent_projection_edge() -> None:
    graph = load(DEPENDENCY_GRAPH)
    matches = [
        edge
        for edge in graph["edges"]
        if edge["artifact"] == "continuity_projection_set"
        and edge["consumer"] == "continuity-projections-check"
    ]
    assert len(matches) == 1
    edge = matches[0]
    assert edge["kind"] == "persistent_derived_requirement"
    assert edge["producer"] == "continuity-projections-refresh"


def test_check_core_directly_includes_non_mutating_projection_check() -> None:
    registry = load(DEPENDENCY_REGISTRY)
    root = next(row for row in registry["root_surfaces"] if row["target"] == "check-core")
    assert "continuity-projections-check" in root["requires_targets"]

    makefile = MAKEFILE.read_text(encoding="utf-8")
    check_core = next(raw for raw in makefile.splitlines() if raw.startswith("check-core:"))
    assert "continuity-projections-check" in check_core.split()
