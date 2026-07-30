from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "render_blueprint_inventory_status.py"

SPEC = importlib.util.spec_from_file_location(
    "render_blueprint_inventory_status",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load inventory status renderer")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class InventoryStatusRendererTests(unittest.TestCase):
    def test_renderer_shows_lower_bound_and_table(self) -> None:
        rendered = MODULE.render_inventory_status(
            {
                "combined_lower_bounds": {
                    "wave_1_plus_wave_2_reviewed": 80,
                    "purpose_evidenced": 79,
                    "dependencies_mapped": 80,
                    "fully_verified": 79,
                    "tracked_files": 726,
                },
                "summary": {
                    "records_with_unknowns": 25,
                },
            },
            {
                "scope": {
                    "changed_paths_since_rci_commit": 19,
                    "artifact_map_scope_delta": 13,
                }
            },
            {
                "external_rollout": {
                    "state": "gated",
                }
            },
            {
                "metadata": {
                    "current_step_id": "current-step",
                }
            },
            MODULE.SUPPORTED_MODULE,
        )

        self.assertIn("10.88%", rendered)
        self.assertIn("┌", rendered)
        self.assertIn("\033[", rendered)
        self.assertIn("current-step", rendered)

    def test_find_value_is_recursive(self) -> None:
        self.assertEqual(
            MODULE.find_value(
                {"outer": {"inner": {"metric": 7}}},
                "metric",
            ),
            7,
        )

    def test_visible_length_ignores_ansi(self) -> None:
        value = f"{MODULE.GREEN}green{MODULE.RESET}"
        self.assertEqual(MODULE.visible_length(value), 5)


if __name__ == "__main__":
    unittest.main()
