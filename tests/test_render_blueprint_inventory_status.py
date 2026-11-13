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
    def sources(self) -> tuple[dict, dict, dict, dict]:
        wave = {
            "combined_lower_bounds": {
                "tracked_files": 726,
                "wave_1_plus_wave_2_reviewed": 80,
                "purpose_evidenced": 79,
                "dependencies_mapped": 80,
                "fully_verified": 79,
            },
            "summary": {
                "purpose_evidenced": 49,
                "dependencies_mapped": 50,
                "fully_verified": 49,
                "records_with_unknowns": 25,
            },
        }
        dashboard = {
            "scope": {
                "changed_paths_since_rci_commit": 19,
                "artifact_map_scope_delta": 13,
            }
        }
        maintenance = {
            "external_rollout": {
                "state": "gated",
            }
        }
        roadmap = {
            "metadata": {
                "current_step_id": "snapshot-ci",
            }
        }
        return wave, dashboard, maintenance, roadmap

    def test_uses_combined_not_wave_local_metrics(self) -> None:
        wave, dashboard, maintenance, roadmap = self.sources()
        rendered = MODULE.render_inventory_status(
            wave,
            dashboard,
            maintenance,
            roadmap,
            MODULE.SUPPORTED_MODULE,
        )

        self.assertIn("10.88%", rendered)
        self.assertIn("79/726", rendered)
        self.assertNotIn("6.75%", rendered)

    def test_shows_nested_meaning_and_dependencies(self) -> None:
        wave, dashboard, maintenance, roadmap = self.sources()
        rendered = MODULE.render_inventory_status(
            wave,
            dashboard,
            maintenance,
            roadmap,
            MODULE.SUPPORTED_MODULE,
        )

        self.assertIn("Coverage and nested quality", rendered)
        self.assertIn("Metric dependencies", rendered)
        self.assertIn("What it means", rendered)
        self.assertIn("Depends on all above", rendered)
        self.assertIn("Current blockers and drift", rendered)

    def test_build_metrics_preserves_unknowns_and_drift(self) -> None:
        wave, dashboard, _, _ = self.sources()
        metrics = MODULE.build_metrics(wave, dashboard)

        self.assertEqual(metrics["unknown_records"], 25)
        self.assertEqual(metrics["changed_paths"], 19)
        self.assertEqual(metrics["scope_delta"], 13)

    def test_visible_length_ignores_ansi(self) -> None:
        value = f"{MODULE.GREEN}green{MODULE.RESET}"
        self.assertEqual(MODULE.visible_length(value), 5)


if __name__ == "__main__":
    unittest.main()
