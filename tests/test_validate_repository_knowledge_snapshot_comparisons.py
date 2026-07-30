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
    ROOT / "scripts" / "coordination" / "validate_repository_knowledge_snapshot_comparisons.py"
)
MANIFEST_PATH = (
    ROOT / "coordination" / "repository_knowledge" / "snapshot_comparison_gate_v0_1.yaml"
)

SPEC = importlib.util.spec_from_file_location(
    "validate_repository_knowledge_snapshot_comparisons",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load snapshot gate validator")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SnapshotComparisonGateTests(unittest.TestCase):
    def validate(
        self,
        manifest_path: Path,
    ) -> dict:
        return MODULE.validate_manifest(
            manifest_path,
            repo_root=ROOT,
            execute_cli=False,
            python_executable=sys.executable,
            work_dir=ROOT / "tmp" / "snapshot_gate_test",
        )

    def test_canonical_manifest_passes_static_gate(self) -> None:
        report = self.validate(MANIFEST_PATH)

        self.assertEqual(
            report["metadata"]["result"],
            "PASSED",
        )
        self.assertEqual(
            report["summary"]["comparison_count"],
            4,
        )
        self.assertEqual(
            report["summary"]["failed_comparisons"],
            0,
        )
        self.assertEqual(
            report["summary"]["accepted_change_count_total"],
            319,
        )

    def test_hash_drift_is_red(self) -> None:
        manifest = MODULE.load_yaml(MANIFEST_PATH)
        mutated = copy.deepcopy(manifest)
        mutated["comparisons"][0]["current_sha256"] = "0" * 64

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.yaml"
            path.write_text(
                yaml.safe_dump(
                    mutated,
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            report = self.validate(path)

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )

    def test_external_rollout_must_remain_gated(self) -> None:
        manifest = MODULE.load_yaml(MANIFEST_PATH)
        mutated = copy.deepcopy(manifest)
        mutated["external_rollout"]["state"] = "active"

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.yaml"
            path.write_text(
                yaml.safe_dump(
                    mutated,
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            report = self.validate(path)

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )


if __name__ == "__main__":
    unittest.main()
