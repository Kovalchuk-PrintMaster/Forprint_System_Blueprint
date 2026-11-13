from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT
    / "scripts"
    / "coordination"
    / "validate_module_registry_resolution.py"
)
MANIFEST = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "registries"
    / "module_registry_resolution_v0_1.yaml"
)


def test_module_registry_report_is_checkout_path_independent(
    tmp_path: Path,
) -> None:
    output = tmp_path / "module_registry_report.yaml"
    completed = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--manifest",
            str(MANIFEST),
            "--repo-root",
            str(ROOT),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, (
        completed.stdout + completed.stderr
    )

    report_text = output.read_text(encoding="utf-8")
    report = yaml.safe_load(report_text)

    assert report["metadata"]["manifest"] == (
        "coordination/repository_knowledge/registries/"
        "module_registry_resolution_v0_1.yaml"
    )
    assert report["metadata"]["repo_root"] == "."
    assert str(ROOT) not in report_text
