from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT / "scripts" / "coordination" / "validate_blueprint_inventory_status_consistency.py"
)
WAVE = (
    ROOT
    / "coordination"
    / "internal_work"
    / "blueprint"
    / "inventory_refresh"
    / "2026-07-29__blueprint__"
    "semantic_inventory_wave_2_v0_1.yaml"
)
DASHBOARD = (
    ROOT
    / "coordination"
    / "internal_work"
    / "blueprint"
    / "inventory_refresh"
    / "2026-07-29__blueprint__"
    "inventory_coverage_drift_dashboard_v0_1.yaml"
)
MAINTENANCE = ROOT / "coordination" / "repository_knowledge" / "inventory_maintenance_v0_1.yaml"
ROADMAP = ROOT / "coordination" / "self_coordination" / "roadmap.yaml"
RENDERER = ROOT / "scripts" / "coordination" / "render_blueprint_inventory_status.py"

SPEC = importlib.util.spec_from_file_location(
    "validate_blueprint_inventory_status_consistency",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load consistency validator")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class InventoryStatusConsistencyTests(unittest.TestCase):
    def validate(
        self,
        *,
        wave_path: Path = WAVE,
        maintenance_path: Path = MAINTENANCE,
    ) -> dict:
        return MODULE.validate_inventory_status(
            wave_path=wave_path,
            dashboard_path=DASHBOARD,
            maintenance_path=maintenance_path,
            roadmap_path=ROADMAP,
            renderer_path=RENDERER,
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

    def test_canonical_inventory_status_is_green(self) -> None:
        report = self.validate()

        self.assertEqual(
            report["metadata"]["result"],
            "PASSED",
        )
        self.assertEqual(
            report["metrics"]["canonical"]["tracked"],
            726,
        )
        self.assertEqual(
            report["metrics"]["canonical"]["purpose"],
            79,
        )
        self.assertAlmostEqual(
            report["summary"]["repository_semantic_lower_bound"],
            79 / 726,
        )

    def test_missing_combined_metrics_is_red(self) -> None:
        wave = MODULE.load_yaml(WAVE)
        mutated = copy.deepcopy(wave)
        mutated.pop("combined_lower_bounds")

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_yaml(
                Path(temporary),
                "wave.yaml",
                mutated,
            )
            report = self.validate(wave_path=path)

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )

    def test_external_rollout_open_is_red(self) -> None:
        maintenance = MODULE.load_yaml(MAINTENANCE)
        mutated = copy.deepcopy(maintenance)
        rollout = mutated.get("external_rollout")

        if isinstance(rollout, dict):
            rollout["state"] = "active"
        else:
            mutated["external_rollout_state"] = "active"

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_yaml(
                Path(temporary),
                "maintenance.yaml",
                mutated,
            )
            report = self.validate(
                maintenance_path=path,
            )

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )


if __name__ == "__main__":
    unittest.main()
