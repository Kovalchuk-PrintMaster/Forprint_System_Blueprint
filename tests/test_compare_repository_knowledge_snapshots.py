from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "compare_repository_knowledge_snapshots.py"

SPEC = importlib.util.spec_from_file_location(
    "compare_repository_knowledge_snapshots",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load snapshot comparison module.")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SnapshotComparisonTests(unittest.TestCase):
    def write_yaml(
        self,
        directory: Path,
        name: str,
        data: object,
    ) -> Path:
        path = directory / name
        path.write_text(
            yaml.safe_dump(
                data,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return path

    def test_keyed_list_and_scalar_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            previous = self.write_yaml(
                directory,
                "previous.yaml",
                {
                    "schema_version": "v1",
                    "steps": [
                        {
                            "step_id": "alpha",
                            "status": "active",
                        }
                    ],
                },
            )
            current = self.write_yaml(
                directory,
                "current.yaml",
                {
                    "schema_version": "v2",
                    "snapshot": {
                        "previous_snapshot": str(previous),
                    },
                    "steps": [
                        {
                            "step_id": "alpha",
                            "status": "completed",
                        },
                        {
                            "step_id": "beta",
                            "status": "active",
                        },
                    ],
                },
            )

            comparison = MODULE.build_comparison(
                previous,
                current,
            )
            paths = {item["path"] for item in comparison["changes"]}

            self.assertTrue(comparison["metadata"]["changed"])
            self.assertTrue(comparison["metadata"]["previous_snapshot_link_matches"])
            self.assertIn("schema_version", paths)
            self.assertIn(
                "steps[step_id=alpha].status",
                paths,
            )
            self.assertIn(
                "steps[step_id=beta]",
                paths,
            )

    def test_identical_documents_have_no_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            data = {
                "schema_version": "v1",
                "value": 3,
            }
            previous = self.write_yaml(
                directory,
                "previous.yaml",
                data,
            )
            current = self.write_yaml(
                directory,
                "current.yaml",
                data,
            )

            comparison = MODULE.build_comparison(
                previous,
                current,
            )

            self.assertFalse(comparison["metadata"]["changed"])
            self.assertEqual(
                comparison["metadata"]["change_count"],
                0,
            )
            self.assertEqual(comparison["changes"], [])

    def test_type_change_is_explicit(self) -> None:
        changes = MODULE.compare_values(
            {"value": 1},
            {"value": "1"},
        )

        self.assertEqual(len(changes), 1)
        self.assertEqual(
            changes[0].change_type,
            "type_changed",
        )
        self.assertEqual(changes[0].path, "value")


if __name__ == "__main__":
    unittest.main()
