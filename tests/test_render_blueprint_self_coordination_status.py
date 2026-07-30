from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "render_blueprint_self_coordination_status.py"

SPEC = importlib.util.spec_from_file_location(
    "render_blueprint_self_coordination_status",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load status renderer")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class StatusRendererTests(unittest.TestCase):
    def test_roadmap_uses_colors_and_table(self) -> None:
        rendered = MODULE.render_roadmap(
            {
                "metadata": {
                    "current_step_id": "active",
                    "actionable_steps_after_current": 8,
                },
                "steps": [
                    {
                        "sequence": 1,
                        "step_id": "active",
                        "title": "Active step",
                        "status": "active",
                    }
                ],
            },
            MODULE.SUPPORTED_MODULE,
        )
        self.assertIn("\033[", rendered)
        self.assertIn("┌", rendered)
        self.assertIn("▶", rendered)

    def test_prompts_show_active_prompt(self) -> None:
        rendered = MODULE.render_prompts(
            {
                "metadata": {
                    "active_prompt_id": "current",
                    "approved_prompt_count": 1,
                    "draft_prompt_count": 2,
                    "completed_prompt_count": 4,
                },
                "prompts": [
                    {
                        "prompt_id": "current",
                        "status": "approved",
                        "roadmap_step_id": "current",
                    }
                ],
            },
            MODULE.SUPPORTED_MODULE,
        )
        self.assertIn("Prompt Queue", rendered)
        self.assertIn("current", rendered)
        self.assertIn("▶", rendered)

    def test_visible_length_ignores_ansi(self) -> None:
        value = f"{MODULE.GREEN}green{MODULE.RESET}"
        self.assertEqual(MODULE.visible_length(value), 5)


if __name__ == "__main__":
    unittest.main()
