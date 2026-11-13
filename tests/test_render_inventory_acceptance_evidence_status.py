from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "render_inventory_acceptance_evidence_status.py"

SPEC = importlib.util.spec_from_file_location(
    "render_inventory_acceptance_evidence_status",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load acceptance evidence renderer")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class AcceptanceEvidenceRendererTests(unittest.TestCase):
    def test_renderer_shows_modes_and_deferrals(self) -> None:
        rendered = MODULE.render(
            {
                "evidence_entries": [
                    {
                        "evidence_id": "rci_v0_4_candidate",
                        "integrity_mode": "sha256",
                        "authority": "candidate",
                        "artifact_type": ("repository_capability_inventory"),
                    },
                    {
                        "evidence_id": "rci_validation_report",
                        "integrity_mode": "runtime_result",
                        "authority": "generated_validation",
                        "artifact_type": "runtime_report",
                    },
                ],
                "explicit_deferrals": [
                    {
                        "deferral_id": ("unreviewed_repository_scope"),
                        "count": 646,
                        "must_remain_visible": True,
                    },
                    {
                        "deferral_id": "wave_2_unknown_records",
                        "count": 25,
                        "must_remain_visible": True,
                    },
                ],
            },
            {
                "metadata": {
                    "result": "PASSED",
                    "external_rollout_state": "gated",
                },
                "summary": {
                    "release_decision": ("PROCEED_TO_INVENTORY_ACCEPTANCE_DRY_RUN"),
                    "evidence_entry_count": 2,
                    "passed_entry_count": 2,
                    "stable_hash_entry_count": 1,
                    "runtime_result_entry_count": 1,
                    "candidate_acceptance_performed": False,
                },
            },
        )

        self.assertIn(
            "PROCEED_TO_INVENTORY_ACCEPTANCE_DRY_RUN",
            rendered,
        )
        self.assertIn("sha256", rendered)
        self.assertIn("runtime_result", rendered)
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
