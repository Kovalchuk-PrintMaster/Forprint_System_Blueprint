from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "render_inventory_acceptance_dry_run_status.py"

SPEC = importlib.util.spec_from_file_location(
    "render_inventory_acceptance_dry_run_status",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load inventory dry-run renderer")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class InventoryDryRunRendererTests(unittest.TestCase):
    def test_renderer_shows_non_mutating_simulation(self) -> None:
        rendered = MODULE.render(
            {
                "metadata": {
                    "result": "PASSED",
                    "external_rollout_state": "gated",
                },
                "summary": {
                    "release_decision": ("PROCEED_TO_INVENTORY_ACCEPTANCE_PACKET_INTEGRITY_GATE"),
                    "scenario_count": 1,
                    "passed_scenario_count": 1,
                    "failed_scenario_count": 0,
                    "candidate_acceptance_performed": False,
                    "git_merge_performed": False,
                    "dry_run_effects_applied": False,
                },
                "scenarios": [
                    {
                        "scenario_id": ("candidate_authority_preservation"),
                        "status": "PASSED",
                        "decision": ("Both candidates remain non-accepted."),
                    }
                ],
                "simulated_actions": [
                    {
                        "sequence": 1,
                        "action": "freeze_candidate_hashes",
                        "status": "SIMULATED",
                        "effect_applied": False,
                    }
                ],
            }
        )

        self.assertIn(
            "PROCEED_TO_INVENTORY_ACCEPTANCE_PACKET_INTEGRITY_GATE",
            rendered,
        )
        self.assertIn("SIMULATED", rendered)
        self.assertIn("False", rendered)
        self.assertIn("\033[", rendered)

    def test_visible_length_ignores_ansi(self) -> None:
        value = f"{MODULE.GREEN}green{MODULE.RESET}"
        self.assertEqual(
            MODULE.visible_length(value),
            5,
        )


if __name__ == "__main__":
    unittest.main()
