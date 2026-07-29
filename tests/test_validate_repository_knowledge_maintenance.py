from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "validate_repository_knowledge_maintenance.py"

SPEC = importlib.util.spec_from_file_location(
    "validate_repository_knowledge_maintenance",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load inventory maintenance validator.")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class InventoryMaintenanceValidatorTests(unittest.TestCase):
    def write_yaml(
        self,
        path: Path,
        data: object,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(
                data,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    def build_fixture(
        self,
        directory: Path,
        *,
        previous_link: str,
    ) -> Path:
        previous_relative = "snapshots/2026-07-20__previous.yaml"
        current_relative = "snapshots/2026-07-29__current.yaml"

        self.write_yaml(
            directory / previous_relative,
            {
                "snapshot": {
                    "id": "previous",
                }
            },
        )
        self.write_yaml(
            directory / current_relative,
            {
                "snapshot": {
                    "id": "current",
                    "previous_snapshot": previous_link,
                }
            },
        )

        config = directory / "maintenance.yaml"
        self.write_yaml(
            config,
            {
                "schema_version": ("repository_knowledge_inventory_maintenance_v0_1"),
                "policy": {
                    "require_git_tracked_snapshots": False,
                },
                "external_rollout": {
                    "state": "gated",
                    "release_conditions": [
                        "acceptance gate passed",
                    ],
                },
                "artifact_families": [
                    {
                        "family_id": "test",
                        "artifact_type": "test",
                        "owner": "test",
                        "previous": previous_relative,
                        "current": current_relative,
                        "maximum_age_days": 30,
                        "maximum_interval_days": 30,
                    }
                ],
            },
        )
        return config

    def test_valid_lineage_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            previous = "snapshots/2026-07-20__previous.yaml"
            config = self.build_fixture(
                directory,
                previous_link=previous,
            )
            report = MODULE.validate_config(
                config,
                repo_root=directory,
                as_of=date(2026, 7, 29),
            )

            self.assertEqual(
                report["metadata"]["result"],
                "PASSED",
            )
            self.assertEqual(
                report["summary"]["passed_families"],
                1,
            )

    def test_previous_link_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            config = self.build_fixture(
                directory,
                previous_link="wrong.yaml",
            )
            report = MODULE.validate_config(
                config,
                repo_root=directory,
                as_of=date(2026, 7, 29),
            )

            self.assertEqual(
                report["metadata"]["result"],
                "FAILED",
            )
            self.assertEqual(
                report["summary"]["failed_families"],
                1,
            )

    def test_external_rollout_must_remain_gated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            previous = "snapshots/2026-07-20__previous.yaml"
            config = self.build_fixture(
                directory,
                previous_link=previous,
            )
            data = yaml.safe_load(config.read_text(encoding="utf-8"))
            data["external_rollout"]["state"] = "active"
            self.write_yaml(config, data)

            report = MODULE.validate_config(
                config,
                repo_root=directory,
                as_of=date(2026, 7, 29),
            )

            self.assertEqual(
                report["metadata"]["result"],
                "FAILED",
            )
            self.assertGreater(
                report["summary"]["policy_errors"],
                0,
            )


if __name__ == "__main__":
    unittest.main()
