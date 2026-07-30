from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "audit_artifact_retention_consistency.py"
POLICY_PATH = ROOT / "coordination" / "repository_knowledge" / "artifact_authority_policy_v0_1.yaml"
SNAPSHOT_GATE_PATH = (
    ROOT / "coordination" / "repository_knowledge" / "snapshot_comparison_gate_v0_1.yaml"
)
SOURCE_MAP_PATH = (
    ROOT
    / "coordination"
    / "internal_work"
    / "blueprint"
    / "inventory_refresh"
    / "2026-07-29__blueprint__"
    "artifact_authority_retention_map_v0_1.yaml"
)

SPEC = importlib.util.spec_from_file_location(
    "audit_artifact_retention_consistency",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load retention audit tool")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ArtifactRetentionAuditTests(unittest.TestCase):
    def audit(
        self,
        policy_path: Path = POLICY_PATH,
        snapshot_gate_path: Path = SNAPSHOT_GATE_PATH,
    ) -> dict:
        return MODULE.audit_retention(
            policy_path,
            snapshot_gate_path,
            SOURCE_MAP_PATH,
            repo_root=ROOT,
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

    def test_canonical_retention_audit_passes(self) -> None:
        report = self.audit()

        self.assertEqual(
            report["metadata"]["result"],
            "PASSED",
        )
        self.assertEqual(
            report["summary"]["artifact_class_count"],
            5,
        )
        self.assertEqual(
            report["summary"]["snapshot_pair_count"],
            4,
        )
        self.assertEqual(
            report["summary"]["protected_snapshot_file_count"],
            8,
        )

    def test_snapshot_hash_drift_is_red(self) -> None:
        gate = MODULE.load_yaml(SNAPSHOT_GATE_PATH)
        mutated = copy.deepcopy(gate)
        mutated["comparisons"][0]["current_sha256"] = "0" * 64

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            gate_path = self.write_yaml(
                directory,
                "gate.yaml",
                mutated,
            )
            report = self.audit(
                snapshot_gate_path=gate_path,
            )

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )

    def test_generated_view_cannot_be_canonical_control(self) -> None:
        policy = MODULE.load_yaml(POLICY_PATH)
        mutated = copy.deepcopy(policy)
        canonical = next(
            item
            for item in mutated["artifact_classes"]
            if item["authority_class"] == "canonical_control"
        )
        canonical["representative_paths"].append("reports/blueprint_check_report.json")

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            policy_path = self.write_yaml(
                directory,
                "policy.yaml",
                mutated,
            )
            report = self.audit(
                policy_path=policy_path,
            )

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )


if __name__ == "__main__":
    unittest.main()
