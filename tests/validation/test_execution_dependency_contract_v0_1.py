from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from scripts.validation.validate_cleanliness_normalization_closure_v0_1 import (
    missing_surface_is_allowed,
)

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "coordination/registry/execution_dependency_registry_v0_1.yaml"
GRAPH = ROOT / "indexes/execution_dependency_graph.yaml"


def test_execution_dependency_graph_is_bound_and_non_authoritative() -> None:
    data = yaml.safe_load(GRAPH.read_text(encoding="utf-8"))
    assert data["status"] == "derived_non_authoritative"
    assert data["authority"] == "none"
    assert data["source_registry"].endswith("execution_dependency_registry_v0_1.yaml")
    assert data["summary"]["derived_requirement_edge_count"] >= 10


def test_derived_consumers_have_explicit_make_prerequisites() -> None:
    cp = subprocess.run(
        [
            sys.executable,
            "scripts/validation/validate_execution_dependency_contract.py",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "DIRECT_PRODUCER_EDGES=PASS" in cp.stdout


def test_execution_dependency_graph_check_passes() -> None:
    cp = subprocess.run(
        [
            sys.executable,
            "scripts/indexing/build_execution_dependency_graph.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout


def test_historical_generated_report_is_not_required_for_current_closure() -> None:
    assert missing_surface_is_allowed(
        {
            "disposition": "PRESERVED_CLASSIFIED",
            "preservation_class": "GENERATED_OR_HISTORICAL_REPORT",
            "mutation_policy": "regenerate_from_source_when_needed",
            "immutable_snapshot_hash_enforced": False,
        }
    )
    assert not missing_surface_is_allowed(
        {
            "disposition": "NORMALIZED_PACKAGE_A",
            "preservation_class": "CURRENT_CANONICAL",
            "mutation_policy": "preserve",
            "immutable_snapshot_hash_enforced": True,
        }
    )


def test_artifact_retention_report_is_only_optional_observation() -> None:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    artifacts = {row["id"]: row for row in data["artifacts"]}
    targets = {row["target"]: row for row in data["targets"]}

    artifact = artifacts["artifact_retention_consistency_report"]
    assert artifact["class"] == "historical_or_runtime_nonrequired"
    assert artifact["missing_behavior"] == "allowed_absent"

    target = targets["surface-normalization-check"]
    assert "artifact_retention_consistency_report" in target["optional_observes"]
    assert "artifact_retention_consistency_report" not in target["requires"]


def test_explain_surface_reports_dependency_chain() -> None:
    cp = subprocess.run(
        [
            sys.executable,
            "scripts/coordination/explain_execution_dependency.py",
            "--target",
            "check-inventory-acceptance-dry-run",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "inventory_acceptance_evidence_index_validation_report" in cp.stdout
    assert "check-inventory-acceptance-evidence-index" in cp.stdout
    assert "EXECUTION_DEPENDENCY_EXPLAIN=PASS" in cp.stdout
