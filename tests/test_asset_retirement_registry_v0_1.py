import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = (
    ROOT
    / "coordination/internal_work/blueprint/cleanliness/"
    "asset_retirement_registry_v0_1.yaml"
)
VALIDATOR = "scripts/validation/validate_asset_retirement_registry_v0_1.py"
SCANNER = "scripts/coordination/scan_asset_retirement_candidates_v0_1.py"


def test_asset_retirement_registry_validator_passes() -> None:
    process = subprocess.run(
        [sys.executable, VALIDATOR],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert process.returncode == 0, process.stdout
    assert "ASSET_RETIREMENT_REGISTRY_VALIDATION=PASS" in process.stdout
    assert "DEPRECATED_SKIP_COVERAGE=PASS" in process.stdout


def test_asset_retirement_registry_starts_non_destructive() -> None:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    assert data["automatic_deletion_allowed"] is False
    assert data["automatic_archive_allowed"] is False
    assert data["summary"]["remove_approved_count"] == 0
    assert data["summary"]["archive_approved_count"] == 0


def test_deprecated_skip_assets_are_explicitly_governed() -> None:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    assert data["summary"]["registered_asset_count"] == 6
    assert data["summary"]["preserved_deprecated_compatibility_count"] == 6
    assert {
        item["lifecycle_status"]
        for item in data["assets"]
    } == {"DEPRECATED"}
    assert {
        item["disposition"]
        for item in data["assets"]
    } == {"KEEP"}


def test_retirement_scanner_is_read_only() -> None:
    process = subprocess.run(
        [sys.executable, SCANNER, "--days", "365", "--limit", "5"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert process.returncode == 0, process.stdout
    assert "ASSET_RETIREMENT_CANDIDATE_SCAN=PASS" in process.stdout
    assert "AUTOMATIC_DELETION_PERFORMED=false" in process.stdout
    assert "AUTOMATIC_ARCHIVE_PERFORMED=false" in process.stdout
