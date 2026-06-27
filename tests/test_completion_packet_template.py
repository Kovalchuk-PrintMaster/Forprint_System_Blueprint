from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_completion_packet_template.py"
TEMPLATE_ROOT = ROOT / "tools" / "completion_packet_template"


def _load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_completion_packet_template",
        VALIDATOR_PATH,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_completion_packet_template_validation_passes() -> None:
    module = _load_validator_module()

    assert module.validate_template(ROOT) == []


def test_completion_packet_example_has_required_metadata() -> None:
    packet_path = TEMPLATE_ROOT / "completion_packet.example.yaml"
    packet = yaml.safe_load(packet_path.read_text(encoding="utf-8"))

    assert packet["instruction_sources_reviewed"]
    assert packet["standards_reviewed"]
    assert packet["standards_alignment_notes"]
    assert packet["boundary_confirmation"]["no_production_api"] is True
    assert (
        "forprint_system_blueprint/coordination/standards/modular_topology_and_resilience/"
        in packet["standards_reviewed"]
    )
    assert (
        "forprint_system_blueprint/coordination/standards/third_party_reuse/"
        in packet["standards_reviewed"]
    )


def test_completion_packet_reference_scripts_exist() -> None:
    assert (TEMPLATE_ROOT / "validate_completion_packet.py").exists()
    assert (TEMPLATE_ROOT / "apply_completion_packet.py").exists()
    assert (TEMPLATE_ROOT / "Makefile.fragment").exists()


def test_completion_packet_readme_defines_idempotency() -> None:
    readme = (TEMPLATE_ROOT / "README.md").read_text(encoding="utf-8")

    assert "idempotent" in readme
    assert "duplicate" in readme
    assert "timestamp-only churn" in readme

def test_blueprint_check_report_includes_completion_packet_template() -> None:
    checks = (ROOT / "scripts" / "run_blueprint_checks.py").read_text(encoding="utf-8")

    assert "completion_packet_template_validation" in checks
    assert "Completion packet template validation" in checks
    assert "scripts/validate_completion_packet_template.py" in checks
