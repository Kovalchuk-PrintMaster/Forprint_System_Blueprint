from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "validate_blueprint_self_coordination.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_blueprint_self_coordination",
    MODULE_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load validator")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SelfCoordinationTests(unittest.TestCase):
    def test_validation_function_exists(self) -> None:
        self.assertTrue(callable(MODULE.validate_package))

    def test_frontmatter_rejects_plain_text(self) -> None:
        path = ROOT / "tmp" / "bad_self_prompt.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("plain text\\n", encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                MODULE.parse_frontmatter(path)
        finally:
            path.unlink(missing_ok=True)

    def test_yaml_loader_requires_mapping(self) -> None:
        path = ROOT / "tmp" / "bad_self_yaml.yaml"
        path.write_text("- item\\n", encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                MODULE.load_yaml(path)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
