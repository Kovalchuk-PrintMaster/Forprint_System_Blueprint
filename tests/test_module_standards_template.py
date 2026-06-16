from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_module_standards_template.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_module_standards_template", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_module_standards_template_is_valid() -> None:
    validator = load_validator()
    assert validator.validate_template(ROOT) == []


def test_module_standards_template_contains_required_targets() -> None:
    fragment = ROOT / "tools" / "module_standards_template" / "Makefile.fragment"
    text = fragment.read_text(encoding="utf-8")
    assert "blueprint-standards-list:" in text
    assert "blueprint-standards-check:" in text
    assert "blueprint-standards-sync:" in text


def test_module_standards_template_is_advisory_not_prompt() -> None:
    readme = ROOT / "tools" / "module_standards_template" / "README.md"
    text = readme.read_text(encoding="utf-8").lower()
    assert "advisory" in text
    assert "not automatically equivalent to active prompts" in text
    assert "destructive rewrite" in text
