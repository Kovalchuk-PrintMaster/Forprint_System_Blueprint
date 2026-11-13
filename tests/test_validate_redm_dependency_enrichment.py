from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "validate_redm_dependency_enrichment.py"
SOURCE = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "flows"
    / "2026-07-29__forprint_system_blueprint__"
    "repository_execution_dependency_map_v0_3.yaml"
)
CANDIDATE = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "flows"
    / "2026-07-30__forprint_system_blueprint__"
    "repository_execution_dependency_map_v0_4.yaml"
)
RCI = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "inventory"
    / "2026-07-30__forprint_system_blueprint__"
    "repository_capability_inventory_v0_4.yaml"
)
RECORD = (
    ROOT
    / "coordination"
    / "internal_work"
    / "blueprint"
    / "inventory_refresh"
    / "2026-07-30__blueprint__"
    "redm_dependency_enrichment_v0_1.yaml"
)

SPEC = importlib.util.spec_from_file_location(
    "validate_redm_dependency_enrichment",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load REDM enrichment validator")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RedmDependencyEnrichmentTests(unittest.TestCase):
    def test_canonical_candidate_passes(self) -> None:
        report = MODULE.validate(
            source_path=SOURCE,
            candidate_path=CANDIDATE,
            capability_context_path=RCI,
            enrichment_record_path=RECORD,
            repo_root=ROOT,
        )

        self.assertEqual(
            report["metadata"]["result"],
            "PASSED",
        )
        self.assertTrue(report["summary"]["additive_only"])
        self.assertGreaterEqual(
            report["summary"]["dependency_index_entry_count"],
            3,
        )

    def test_relative_metadata_paths_match(self) -> None:
        relative = SOURCE.relative_to(ROOT)

        self.assertTrue(
            MODULE.references_path(
                str(relative),
                SOURCE,
                repo_root=ROOT,
            )
        )

    def test_modifying_source_content_is_red(self) -> None:
        candidate = MODULE.load_yaml(CANDIDATE)
        mutated = copy.deepcopy(candidate)
        source_keys = [key for key in mutated if key != MODULE.SECTION]
        mutated[source_keys[0]] = "unauthorized mutation"

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "candidate.yaml"
            path.write_text(
                yaml.safe_dump(
                    mutated,
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            report = MODULE.validate(
                source_path=SOURCE,
                candidate_path=path,
                capability_context_path=RCI,
                enrichment_record_path=RECORD,
                repo_root=ROOT,
            )

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )

    def test_inferred_unknown_edges_is_red(self) -> None:
        candidate = MODULE.load_yaml(CANDIDATE)
        mutated = copy.deepcopy(candidate)
        mutated[MODULE.SECTION]["unresolved_scope"]["dependency_edges_not_inferred"] = False

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "candidate.yaml"
            path.write_text(
                yaml.safe_dump(
                    mutated,
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            report = MODULE.validate(
                source_path=SOURCE,
                candidate_path=path,
                capability_context_path=RCI,
                enrichment_record_path=RECORD,
                repo_root=ROOT,
            )

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )


if __name__ == "__main__":
    unittest.main()
