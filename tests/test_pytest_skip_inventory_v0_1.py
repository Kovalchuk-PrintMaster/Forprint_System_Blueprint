import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = (
    ROOT
    / "coordination/internal_work/blueprint/testing/"
    "2026-09-02__pytest_skip_inventory_v0_1.yaml"
)


def test_pytest_skip_inventory_validator_passes() -> None:
    process = subprocess.run(
        [
            sys.executable,
            "scripts/validation/validate_pytest_skip_inventory_v0_1.py",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert process.returncode == 0, process.stdout
    assert "REGISTERED_SKIPPED_TEST_COUNT=32" in process.stdout
    assert "UNEXPLAINED_SKIP_COUNT=0" in process.stdout


def test_pytest_skip_inventory_is_explicit() -> None:
    data = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    assert data["expected_total_skipped_tests"] == 32
    assert len(data["groups"]) == 6
    assert sum(
        group["expected_skipped_test_count"]
        for group in data["groups"]
    ) == 32
    assert data["summary"]["unexplained_skip_count"] == 0
    assert data["summary"]["deletion_recommended_now"] is False
