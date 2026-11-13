from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "assess_repository_knowledge_freshness.py"
MANIFEST = ROOT / "coordination" / "repository_knowledge" / "snapshot_comparison_gate_v0_1.yaml"

SPEC = importlib.util.spec_from_file_location(
    "assess_repository_knowledge_freshness",
    MODULE_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load freshness assessor")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FreshnessTests(unittest.TestCase):
    def test_canonical_manifest_is_releasable(self) -> None:
        report = MODULE.assess(MANIFEST, repo=ROOT)

        self.assertEqual(report["metadata"]["result"], "PASSED")
        self.assertEqual(report["summary"]["snapshot_count"], 4)
        self.assertEqual(report["summary"]["failed_snapshot_count"], 0)
        self.assertIn(
            report["summary"]["release_decision"],
            {"PROCEED_AS_FRESH", "PROCEED_WITH_BOUNDED_REFRESH"},
        )

    def test_hash_drift_blocks_rci(self) -> None:
        manifest = MODULE.load_yaml(MANIFEST)
        mutated = copy.deepcopy(manifest)
        mutated["comparisons"][0]["current_sha256"] = "0" * 64

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.yaml"
            path.write_text(
                yaml.safe_dump(mutated, sort_keys=False),
                encoding="utf-8",
            )
            report = MODULE.assess(path, repo=ROOT)

        self.assertEqual(report["metadata"]["result"], "FAILED")
        self.assertEqual(
            report["summary"]["release_decision"],
            "BLOCK_RCI_ENRICHMENT",
        )

    def test_classifier(self) -> None:
        self.assertEqual(
            MODULE.classify("coordination/repository_knowledge/x.yaml"),
            "repository_knowledge",
        )
        self.assertEqual(
            MODULE.classify("tests/test_x.py"),
            "executable_control",
        )
        self.assertEqual(
            MODULE.classify("reports/x.yaml"),
            "generated_view",
        )


if __name__ == "__main__":
    unittest.main()
