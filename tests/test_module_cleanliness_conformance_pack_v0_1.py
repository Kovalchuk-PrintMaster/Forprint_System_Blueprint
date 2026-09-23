import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "module_cleanliness_conformance_pack_v0_1.yaml"
)
PORTFOLIO = (
    ROOT
    / "coordination/internal_work/blueprint/cleanliness/"
    "module_cleanliness_conformance_portfolio_v0_1.yaml"
)
VALIDATOR = (
    "scripts/validation/"
    "validate_module_cleanliness_conformance_pack_v0_1.py"
)
RENDERER = "scripts/coordination/render_module_cleanliness_pack_v0_1.py"


def test_module_cleanliness_pack_validator_passes() -> None:
    process = subprocess.run(
        [sys.executable, VALIDATOR],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert process.returncode == 0, process.stdout
    assert "CANONICAL_MODULE_COUNT=23" in process.stdout
    assert "REQUIRED_COMPONENT_COUNT=13" in process.stdout


def test_pack_requires_retirement_and_safe_mutation() -> None:
    data = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    ids = {
        item["component_id"]
        for item in data["required_components"]
    }
    assert "asset_lifecycle_and_retirement" in ids
    assert "safe_mutation_path" in ids
    assert "skipped_test_inventory_when_applicable" in ids


def test_portfolio_keeps_distribution_closed() -> None:
    data = yaml.safe_load(PORTFOLIO.read_text(encoding="utf-8"))
    assert data["assistant_distribution_allowed"] is False
    assert data["module_implementation_allowed"] is False
    assert len(data["modules"]) == 23


def test_starter_renderer_is_read_only_and_proposed() -> None:
    portfolio = yaml.safe_load(PORTFOLIO.read_text(encoding="utf-8"))
    module_id = next(
        item["module_id"]
        for item in portfolio["modules"]
        if item["module_id"] != "forprint_system_blueprint"
    )
    process = subprocess.run(
        [sys.executable, RENDERER, module_id],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert process.returncode == 0, process.stdout
    starter = yaml.safe_load(process.stdout)
    assert starter["module_id"] == module_id
    assert starter["status"] == "PROPOSED_NOT_IMPLEMENTED"
    assert starter["assistant_distribution_allowed"] is False
    assert len(starter["components"]) == 13
