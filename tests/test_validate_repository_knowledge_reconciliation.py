from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "validate_repository_knowledge_reconciliation.py"

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
COORDINATION_DIRECTION = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "direction"
    / "blueprint_coordination"
    / "2026-07-29__forprint_system_blueprint__"
    "state_direction_rationale_snapshot_v0_2.yaml"
)
PORTFOLIO_DIRECTION = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "direction"
    / "system_portfolio"
    / "2026-07-29__forprint_system__"
    "state_direction_rationale_snapshot_v0_2.yaml"
)
AUTHORITY_POLICY = (
    ROOT / "coordination" / "repository_knowledge" / "artifact_authority_policy_v0_1.yaml"
)
MODULE_REGISTRY = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "registries"
    / "module_registry_resolution_v0_1.yaml"
)
CLOSURE = ROOT / "reports" / "semantic_coverage_closure_report.yaml"
RCI_VALIDATION = ROOT / "reports" / "rci_semantic_enrichment_validation_report.yaml"
REDM_VALIDATION = ROOT / "reports" / "redm_dependency_enrichment_validation_report.yaml"

SPEC = importlib.util.spec_from_file_location(
    "validate_repository_knowledge_reconciliation",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load repository knowledge reconciliation validator")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RepositoryKnowledgeReconciliationTests(unittest.TestCase):
    def validate(
        self,
        *,
        rci_path: Path = RCI,
        closure_path: Path = CLOSURE,
    ) -> dict:
        return MODULE.validate_reconciliation(
            rci_path=rci_path,
            redm_path=REDM,
            coordination_direction_path=COORDINATION_DIRECTION,
            portfolio_direction_path=PORTFOLIO_DIRECTION,
            authority_policy_path=AUTHORITY_POLICY,
            module_registry_path=MODULE_REGISTRY,
            closure_report_path=closure_path,
            rci_validation_path=RCI_VALIDATION,
            redm_validation_path=REDM_VALIDATION,
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

    def test_canonical_reconciliation_is_green(self) -> None:
        report = self.validate()

        self.assertEqual(
            report["metadata"]["result"],
            "PASSED",
        )
        self.assertEqual(
            report["summary"]["release_decision"],
            "PROCEED_TO_INVENTORY_ACCEPTANCE_EVIDENCE_INDEX",
        )
        self.assertFalse(report["summary"]["candidate_acceptance_performed"])
        self.assertEqual(
            report["summary"]["candidate_authority_source"],
            "artifact_status",
        )
        self.assertEqual(
            report["summary"]["policy_authority_classes"],
            {
                "accepted": True,
                "generated": True,
            },
        )
        self.assertEqual(
            report["summary"]["unreviewed_files"],
            646,
        )

    def test_authority_policy_semantics_are_detected(
        self,
    ) -> None:
        policy = MODULE.load_yaml(AUTHORITY_POLICY)
        classifications = MODULE.authority_classifications(policy)

        self.assertEqual(
            classifications,
            {
                "accepted": True,
                "generated": True,
            },
        )

    def test_candidate_acceptance_is_red(self) -> None:
        rci = MODULE.load_yaml(RCI)
        mutated = copy.deepcopy(rci)
        mutated[MODULE.RCI_SECTION]["status"] = "ACCEPTED"

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

    def test_hidden_deferrals_is_red(self) -> None:
        closure = MODULE.load_yaml(CLOSURE)
        mutated = copy.deepcopy(closure)
        mutated["explicit_deferrals"] = []

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_yaml(
                Path(temporary),
                "closure.yaml",
                mutated,
            )
            report = self.validate(closure_path=path)

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )


if __name__ == "__main__":
    unittest.main()
