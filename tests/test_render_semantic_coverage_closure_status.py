from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "render_semantic_coverage_closure_status.py"

SPEC = importlib.util.spec_from_file_location(
    "render_semantic_coverage_closure_status",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load semantic closure renderer")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SemanticCoverageRendererTests(unittest.TestCase):
    def test_renderer_shows_closure_and_deferrals(self) -> None:
        rendered = MODULE.render(
            {
                "metadata": {
                    "external_rollout_state": "gated",
                },
                "summary": {
                    "closure_state": ("GREEN_WITH_EXPLICIT_DEFERRALS"),
                    "release_decision": (
                        "PROCEED_TO_REPOSITORY_KNOWLEDGE_RECONCILIATION_WITH_EXPLICIT_DEFERRALS"
                    ),
                    "tracked_files": 726,
                    "reviewed_files": 80,
                    "purpose_evidenced": 79,
                    "dependencies_mapped": 80,
                    "fully_verified": 79,
                    "repository_semantic_lower_bound": 79 / 726,
                    "reviewed_quality_lower_bound": 79 / 80,
                },
                "candidate_integrity": {
                    "rci_validation": "PASSED",
                    "rci_sha256": "a" * 64,
                    "redm_validation": "PASSED",
                    "redm_sha256": "b" * 64,
                },
                "explicit_deferrals": [
                    {
                        "deferral_id": "unreviewed_repository_scope",
                        "count": 646,
                        "must_remain_visible": True,
                    },
                    {
                        "deferral_id": "wave_2_unknown_records",
                        "count": 25,
                        "must_remain_visible": True,
                    },
                ],
            }
        )

        self.assertIn(
            "GREEN_WITH_EXPLICIT_DEFERRALS",
            rendered,
        )
        self.assertIn("10.88%", rendered)
        self.assertIn("646", rendered)
        self.assertIn("25", rendered)
        self.assertIn("\033[", rendered)

    def test_visible_length_ignores_ansi(self) -> None:
        value = f"{MODULE.GREEN}green{MODULE.RESET}"
        self.assertEqual(
            MODULE.visible_length(value),
            5,
        )


if __name__ == "__main__":
    unittest.main()
