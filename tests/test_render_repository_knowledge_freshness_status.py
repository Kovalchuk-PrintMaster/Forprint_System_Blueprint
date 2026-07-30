from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "render_repository_knowledge_freshness_status.py"

SPEC = importlib.util.spec_from_file_location(
    "render_repository_knowledge_freshness_status",
    MODULE_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load freshness renderer")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RendererTests(unittest.TestCase):
    def test_renderer(self) -> None:
        rendered = MODULE.render(
            {
                "metadata": {"external_rollout_state": "gated"},
                "summary": {
                    "snapshot_count": 1,
                    "fresh_snapshot_count": 0,
                    "bounded_refresh_snapshot_count": 1,
                    "failed_snapshot_count": 0,
                    "changed_path_union_count": 4,
                    "knowledge_relevant_changed_path_union_count": 3,
                    "release_decision": "PROCEED_WITH_BOUNDED_REFRESH",
                },
                "change_class_counts": {"repository_knowledge": 2},
                "snapshots": [
                    {
                        "comparison_id": "rci",
                        "freshness": "BOUNDED_REFRESH_REQUIRED",
                        "baseline_commit": "1234567890abcdef",
                        "changed_path_count": 4,
                        "knowledge_relevant_changed_path_count": 3,
                    }
                ],
            }
        )
        self.assertIn("PROCEED_WITH_BOUNDED_REFRESH", rendered)
        self.assertIn("Snapshot freshness", rendered)
        self.assertIn("12345678", rendered)
        self.assertIn("\033[", rendered)

    def test_visible_length(self) -> None:
        value = f"{MODULE.GREEN}green{MODULE.RESET}"
        self.assertEqual(MODULE.visible_length(value), 5)


if __name__ == "__main__":
    unittest.main()
