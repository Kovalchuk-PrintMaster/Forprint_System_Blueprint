import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "module_current_state_evidence_standard_v0_1.yaml"
)
PORTFOLIO = (
    ROOT
    / "coordination/internal_work/blueprint/module_inventory/"
    "module_current_state_evidence_portfolio_v0_1.yaml"
)
VALIDATOR = "scripts/validation/validate_module_current_state_evidence_v0_1.py"
RENDERER = "scripts/coordination/render_module_current_state_profile_v0_1.py"


def test_module_current_state_validator_passes() -> None:
    process = subprocess.run(
        [sys.executable, VALIDATOR],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert process.returncode == 0, process.stdout
    assert "REQUIRED_PROFILE_SECTION_COUNT=14" in process.stdout
    assert "CANONICAL_MODULE_COUNT=23" in process.stdout
    assert "REPO_EVIDENCE_PENDING_COUNT=22" in process.stdout


def test_current_state_standard_separates_current_target_proposed() -> None:
    data = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    labels = set(data["state_labels"])
    assert "CURRENT_CONFIRMED" in labels
    assert "TARGET_AGREED" in labels
    assert "TARGET_PROPOSED" in labels
    assert data["portfolio_rules"]["cross_repo_diagnostics_started_now"] is False


def test_portfolio_does_not_fake_other_repo_verification() -> None:
    data = yaml.safe_load(PORTFOLIO.read_text(encoding="utf-8"))
    non_blueprint = [
        item
        for item in data["modules"]
        if item["module_id"] != "forprint_system_blueprint"
    ]
    assert len(non_blueprint) == 22
    assert all(
        item["repository_evidence_verified"] is False
        for item in non_blueprint
    )
    assert all(
        item["profile_status"]
        == "BLUEPRINT_DOCUMENTED_REPO_EVIDENCE_PENDING"
        for item in non_blueprint
    )


def test_renderer_has_all_required_sections_without_implementation_claims() -> None:
    data = yaml.safe_load(PORTFOLIO.read_text(encoding="utf-8"))
    module_id = next(
        item["module_id"]
        for item in data["modules"]
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
    profile = yaml.safe_load(process.stdout)
    assert len(profile["sections"]) == 14
    assert profile["repository_evidence_verified"] is False
    assert profile["cross_repo_diagnostics_started"] is False
    assert profile["assistant_distribution_allowed"] is False
