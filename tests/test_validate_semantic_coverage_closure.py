from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "validate_semantic_coverage_closure.py"
RCI = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "inventory"
    / "2026-07-30__forprint_system_blueprint__"
    "repository_capability_inventory_v0_4.yaml"
)
REDM = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "flows"
    / "2026-07-30__forprint_system_blueprint__"
    "repository_execution_dependency_map_v0_4.yaml"
)
RCI_VALIDATION = ROOT / "reports" / "rci_semantic_enrichment_validation_report.yaml"
REDM_VALIDATION = ROOT / "reports" / "redm_dependency_enrichment_validation_report.yaml"
FRESHNESS = ROOT / "reports" / "repository_knowledge_freshness_report.yaml"
UNKNOWNS = (
    ROOT
    / "coordination"
    / "internal_work"
    / "blueprint"
    / "inventory_refresh"
    / "2026-07-30__blueprint__"
    "semantic_inventory_unknowns_triage_v0_1.yaml"
)

SPEC = importlib.util.spec_from_file_location(
    "validate_semantic_coverage_closure",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load semantic closure validator")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SemanticCoverageClosureTests(unittest.TestCase):
    def validate(
        self,
        *,
        rci_path: Path = RCI,
        redm_path: Path = REDM,
    ) -> dict:
        return MODULE.validate_closure(
            rci_path=rci_path,
            redm_path=redm_path,
            rci_validation_path=RCI_VALIDATION,
            redm_validation_path=REDM_VALIDATION,
            freshness_path=FRESHNESS,
            unknowns_path=UNKNOWNS,
            module_id="forprint_system_blueprint",
        )

    def write_yaml(
        self,
        directory: Path,
        name: str,
        data: dict,
    ) -> Path:
        path = directory / name
        path.write_text(
            yaml.safe_dump(
                data,
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        return path

    def test_canonical_closure_is_green(self) -> None:
        report = self.validate()

        self.assertEqual(
            report["metadata"]["result"],
            "PASSED",
        )
        self.assertEqual(
            report["summary"]["closure_state"],
            "GREEN_WITH_EXPLICIT_DEFERRALS",
        )
        self.assertEqual(
            report["summary"]["unreviewed_files"],
            646,
        )
        self.assertFalse(report["summary"]["full_semantic_coverage_claim_allowed"])

    def test_rci_metric_drift_is_red(self) -> None:
        rci = MODULE.load_yaml(RCI)
        mutated = copy.deepcopy(rci)
        mutated[MODULE.RCI_SECTION]["coverage_lower_bounds"]["purpose_evidenced"] = 80

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_yaml(
                Path(temporary),
                "rci.yaml",
                mutated,
            )
            report = self.validate(rci_path=path)

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )

    def test_inferred_dependency_edges_is_red(self) -> None:
        redm = MODULE.load_yaml(REDM)
        mutated = copy.deepcopy(redm)
        mutated[MODULE.REDM_SECTION]["unresolved_scope"]["dependency_edges_not_inferred"] = False

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_yaml(
                Path(temporary),
                "redm.yaml",
                mutated,
            )
            report = self.validate(redm_path=path)

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )


if __name__ == "__main__":
    unittest.main()
