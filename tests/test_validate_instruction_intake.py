import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path.cwd()
SCRIPT_PATH = ROOT / "scripts" / "validate_instruction_intake.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_instruction_intake", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_instruction_intake_is_valid() -> None:
    validator = load_validator()
    assert validator.validate_instruction_intake(ROOT) == []


def test_instruction_sources_define_required_priority_order() -> None:
    path = ROOT / "coordination" / "instruction_intake" / "instruction_sources.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    source_ids = [record["source_id"] for record in data["priority_order"]]

    assert source_ids[:5] == [
        "instruction_intake",
        "global_policy",
        "active_directives",
        "module_policy",
        "outgoing_prompt",
    ]
    assert "standards" in source_ids


def test_profile_traits_are_composable_not_rigid_types() -> None:
    path = ROOT / "coordination" / "instruction_intake" / "default_profile_traits.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert data["profiles_are_composable"] is True
    assert data["presets_are_examples_not_rigid_types"] is True
