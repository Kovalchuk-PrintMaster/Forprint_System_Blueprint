from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT / "scripts" / "coordination" / "render_repository_knowledge_coverage_dashboard.py"
)

SPEC = importlib.util.spec_from_file_location(
    "render_repository_knowledge_coverage_dashboard",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load coverage dashboard renderer.")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CoverageDashboardTests(unittest.TestCase):
    def test_safe_ratio_handles_zero(self) -> None:
        self.assertEqual(MODULE.safe_ratio(3, 0), 0.0)

    def test_name_status_is_counted(self) -> None:
        result = MODULE.parse_name_status(
            [
                "A\tnew.yaml",
                "M\tchanged.py",
                "D\told.md",
                "R100\tbefore.txt\tafter.txt",
            ]
        )

        self.assertEqual(result["change_count"], 4)
        self.assertEqual(result["counts"]["added"], 1)
        self.assertEqual(result["counts"]["modified"], 1)
        self.assertEqual(result["counts"]["deleted"], 1)
        self.assertEqual(result["counts"]["renamed"], 1)

    def test_drift_creates_critical_priority(self) -> None:
        priorities = MODULE.build_priorities(
            current_tracked=100,
            source_drift_count=4,
            semantic_unknowns=0,
            classification_pending=0,
            registry_findings=0,
            external_rollout_state="gated",
        )

        self.assertEqual(
            priorities[0]["priority"],
            "critical",
        )
        self.assertEqual(
            priorities[0]["evidence_count"],
            4,
        )


if __name__ == "__main__":
    unittest.main()
