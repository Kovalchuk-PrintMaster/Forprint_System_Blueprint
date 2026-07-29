from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "validate_module_registry_resolution.py"

SPEC = importlib.util.spec_from_file_location(
    "validate_module_registry_resolution",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load module registry validator.")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ModuleRegistryResolutionTests(unittest.TestCase):
    def write_yaml(
        self,
        path: Path,
        data: object,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(data, sort_keys=False),
            encoding="utf-8",
        )

    def build_manifest(
        self,
        directory: Path,
        *,
        duplicate: bool = False,
        rollout_state: str = "gated",
    ) -> Path:
        modules = []

        for module_id in ("alpha", "beta"):
            roadmap = f"coordination/roadmaps/{module_id}.yaml"
            prompt_index = f"coordination/outgoing_prompts/{module_id}/index.yaml"
            self.write_yaml(
                directory / roadmap,
                {"module_id": module_id},
            )
            self.write_yaml(
                directory / prompt_index,
                {"module_id": module_id},
            )
            modules.append(
                {
                    "module_id": ("alpha" if duplicate else module_id),
                    "canonical_sources": [
                        {
                            "kind": "module_roadmap",
                            "path": roadmap,
                        },
                        {
                            "kind": "prompt_queue_index",
                            "path": prompt_index,
                        },
                    ],
                }
            )

        manifest = directory / "manifest.yaml"
        self.write_yaml(
            manifest,
            {
                "schema_version": ("module_registry_resolution_v0_1"),
                "policy": {
                    "canonical_id_unique": True,
                    "require_git_tracked_sources": False,
                    "cross_repository_writes_forbidden": True,
                },
                "external_rollout": {
                    "state": rollout_state,
                },
                "expected_active_module_ids": [
                    "alpha",
                    "beta",
                ],
                "modules": modules,
            },
        )
        return manifest

    def test_valid_manifest_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = self.build_manifest(directory)
            report = MODULE.validate_manifest(
                manifest,
                repo_root=directory,
            )

            self.assertEqual(
                report["metadata"]["result"],
                "PASSED",
            )
            self.assertEqual(
                report["summary"]["passed_modules"],
                2,
            )

    def test_duplicate_module_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = self.build_manifest(
                directory,
                duplicate=True,
            )
            report = MODULE.validate_manifest(
                manifest,
                repo_root=directory,
            )

            self.assertEqual(
                report["metadata"]["result"],
                "FAILED",
            )
            self.assertGreater(
                report["summary"]["policy_error_count"],
                0,
            )

    def test_external_rollout_must_be_gated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = self.build_manifest(
                directory,
                rollout_state="active",
            )
            report = MODULE.validate_manifest(
                manifest,
                repo_root=directory,
            )

            self.assertEqual(
                report["metadata"]["result"],
                "FAILED",
            )


if __name__ == "__main__":
    unittest.main()
