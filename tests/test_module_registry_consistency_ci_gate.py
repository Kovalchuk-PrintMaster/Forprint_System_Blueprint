from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "coordination" / "validate_module_registry_resolution.py"
MANIFEST_PATH = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "registries"
    / "module_registry_resolution_v0_1.yaml"
)

SPEC = importlib.util.spec_from_file_location(
    "validate_module_registry_resolution_gate",
    VALIDATOR_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load module registry validator")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ModuleRegistryConsistencyGateTests(unittest.TestCase):
    def load_manifest(self) -> dict[str, object]:
        data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))

        if not isinstance(data, dict):
            raise AssertionError("Canonical manifest must be a mapping")

        return data

    def write_manifest(
        self,
        directory: Path,
        data: dict[str, object],
    ) -> Path:
        path = directory / "manifest.yaml"
        path.write_text(
            yaml.safe_dump(
                data,
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        return path

    def test_canonical_manifest_is_green(self) -> None:
        report = MODULE.validate_manifest(
            MANIFEST_PATH,
            repo_root=ROOT,
        )

        self.assertEqual(
            report["metadata"]["result"],
            "PASSED",
        )
        self.assertEqual(
            report["summary"]["module_count"],
            3,
        )
        self.assertEqual(
            report["summary"]["failed_modules"],
            0,
        )

    def test_duplicate_module_identity_is_red(self) -> None:
        manifest = copy.deepcopy(self.load_manifest())
        modules = manifest["modules"]
        self.assertIsInstance(modules, list)
        modules[1]["module_id"] = modules[0]["module_id"]

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_manifest(
                Path(temporary),
                manifest,
            )
            report = MODULE.validate_manifest(
                path,
                repo_root=ROOT,
            )

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )
        self.assertGreater(
            report["summary"]["policy_error_count"],
            0,
        )

    def test_external_rollout_drift_is_red(self) -> None:
        manifest = copy.deepcopy(self.load_manifest())
        manifest["external_rollout"]["state"] = "active"

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_manifest(
                Path(temporary),
                manifest,
            )
            report = MODULE.validate_manifest(
                path,
                repo_root=ROOT,
            )

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )


if __name__ == "__main__":
    unittest.main()
