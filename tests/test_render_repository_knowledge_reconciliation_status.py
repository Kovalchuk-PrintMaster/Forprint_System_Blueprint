from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT / "scripts" / "coordination" / "render_repository_knowledge_reconciliation_status.py"
)

SPEC = importlib.util.spec_from_file_location(
    "render_repository_knowledge_reconciliation_status",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load repository reconciliation renderer")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ReconciliationRendererTests(unittest.TestCase):
    def test_renderer_shows_matrix_and_deferrals(self) -> None:
        rendered = MODULE.render(
            {
                "metadata": {
                    "result": "PASSED",
                    "external_rollout_state": "gated",
                },
                "summary": {
                    "release_decision": ("PROCEED_TO_INVENTORY_ACCEPTANCE_EVIDENCE_INDEX"),
                    "matrix_entry_count": 2,
                    "passed_entry_count": 1,
                    "deferred_entry_count": 1,
                    "failed_entry_count": 0,
                    "candidate_acceptance_performed": False,
                },
                "reconciliation_matrix": [
                    {
                        "artifact": "RCI v0.4",
                        "status": "PASSED",
                        "authority": "candidate",
                        "note": "Candidate remains non-accepted.",
                    },
                    {
                        "artifact": "Explicit semantic deferrals",
                        "status": "DEFERRED",
                        "authority": "closure report",
                        "note": "Unknowns stay visible.",
                    },
                ],
                "explicit_deferrals": [
                    {
                        "deferral_id": "unreviewed_repository_scope",
                        "count": 646,
                        "must_remain_visible": True,
                    }
                ],
            }
        )

        self.assertIn(
            "PROCEED_TO_INVENTORY_ACCEPTANCE_EVIDENCE_INDEX",
            rendered,
        )
        self.assertIn("Reconciliation matrix", rendered)
        self.assertIn("646", rendered)
        self.assertIn("\033[", rendered)

    def test_visible_length_ignores_ansi(self) -> None:
        value = f"{MODULE.GREEN}green{MODULE.RESET}"
        self.assertEqual(
            MODULE.visible_length(value),
            5,
        )


if __name__ == "__main__":
    unittest.main()
