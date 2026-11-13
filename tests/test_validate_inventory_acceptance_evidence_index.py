from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "validate_inventory_acceptance_evidence_index.py"
INDEX = (
    ROOT
    / "coordination"
    / "internal_work"
    / "blueprint"
    / "inventory_refresh"
    / "2026-07-30__blueprint__"
    "inventory_acceptance_evidence_index_v0_1.yaml"
)

SPEC = importlib.util.spec_from_file_location(
    "validate_inventory_acceptance_evidence_index",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load acceptance evidence validator")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class AcceptanceEvidenceIndexTests(unittest.TestCase):
    def validate(self, index_path: Path = INDEX) -> dict:
        return MODULE.validate_index(
            index_path=index_path,
            repo_root=ROOT,
            module_id="forprint_system_blueprint",
        )

    def write_index(
        self,
        directory: Path,
        data: dict,
    ) -> Path:
        path = directory / "index.yaml"
        path.write_text(
            yaml.safe_dump(
                data,
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        return path

    def test_canonical_index_passes(self) -> None:
        report = self.validate()

        self.assertEqual(
            report["metadata"]["result"],
            "PASSED",
        )
        self.assertEqual(
            report["summary"]["candidate_entry_count"],
            2,
        )
        self.assertFalse(report["summary"]["candidate_acceptance_performed"])
        self.assertEqual(
            report["summary"]["release_decision"],
            "PROCEED_TO_INVENTORY_ACCEPTANCE_DRY_RUN",
        )

    def test_hash_drift_is_red(self) -> None:
        index = MODULE.load_yaml(INDEX)
        mutated = copy.deepcopy(index)
        stable = next(
            item for item in mutated["evidence_entries"] if item["integrity_mode"] == "sha256"
        )
        stable["sha256"] = "0" * 64

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_index(
                Path(temporary),
                mutated,
            )
            report = self.validate(path)

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )

    def test_candidate_relabel_is_red(self) -> None:
        index = MODULE.load_yaml(INDEX)
        mutated = copy.deepcopy(index)
        entry = next(
            item
            for item in mutated["evidence_entries"]
            if item["evidence_id"] == "rci_v0_4_candidate"
        )
        entry["authority"] = "accepted"

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_index(
                Path(temporary),
                mutated,
            )
            report = self.validate(path)

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )

    def test_hidden_deferrals_is_red(self) -> None:
        index = MODULE.load_yaml(INDEX)
        mutated = copy.deepcopy(index)
        mutated["explicit_deferrals"] = []

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_index(
                Path(temporary),
                mutated,
            )
            report = self.validate(path)

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )


if __name__ == "__main__":
    unittest.main()
