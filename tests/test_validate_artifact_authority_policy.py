from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "validate_artifact_authority_policy.py"

SPEC = importlib.util.spec_from_file_location(
    "validate_artifact_authority_policy",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load authority validator")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ArtifactAuthorityPolicyTests(unittest.TestCase):
    def test_allowed_classes_are_complete(self) -> None:
        self.assertEqual(
            MODULE.ALLOWED_CLASSES,
            {
                "canonical_control",
                "immutable_snapshot",
                "decision_evidence",
                "generated_rebuildable_view",
                "executable_validation",
            },
        )

    def test_allowed_mutations_are_complete(self) -> None:
        self.assertIn(
            "append_new_version_only",
            MODULE.ALLOWED_MUTATIONS,
        )
        self.assertIn(
            "generator_only",
            MODULE.ALLOWED_MUTATIONS,
        )

    def test_validation_function_exists(self) -> None:
        self.assertTrue(callable(MODULE.validate_policy))


if __name__ == "__main__":
    unittest.main()
