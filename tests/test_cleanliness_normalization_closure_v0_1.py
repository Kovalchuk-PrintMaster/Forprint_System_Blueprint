import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_closure_validator_passes() -> None:
    process = subprocess.run(
        [
            sys.executable,
            "scripts/validation/validate_cleanliness_normalization_closure_v0_1.py",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert process.returncode == 0, process.stdout
    assert "ACTIVE_BASELINE_DEBT_PATH_COUNT=0" in process.stdout


def test_baseline_active_debt_is_zero() -> None:
    path = (
        ROOT
        / "coordination/internal_work/blueprint/normalization/"
        "2026-09-01__document_surface_normalization_baseline_v0_1.yaml"
    )
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["yaml_debt"] == []
    assert data["markdown_debt"] == []
    assert data["active_debt_count"] == 0
