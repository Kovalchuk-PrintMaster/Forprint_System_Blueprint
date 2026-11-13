from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.coordination.modules.forprint_system_blueprint.workflows import (
    self_audit,
)

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (
    ROOT
    / "scripts/validation/"
    "validate_blueprint_command_applicability.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "blueprint_command_applicability_validator",
        VALIDATOR,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def run_script(*parts: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *parts],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def test_current_applicability_registry_passes() -> None:
    assert validator.validate(ROOT) == []


def test_self_audit_evidence_cannot_claim_green(
    tmp_path: Path,
) -> None:
    target = tmp_path / "self_audit_evidence.yaml"
    shutil.copy2(
        ROOT / validator.SELF_AUDIT_EVIDENCE,
        target,
    )
    content = target.read_text(encoding="utf-8")
    old = "  operational_readiness: blocked\n"
    new = "  operational_readiness: green\n"
    assert content.count(old) == 1
    target.write_text(
        content.replace(old, new, 1),
        encoding="utf-8",
    )
    assert any(
        "subject.operational_readiness must be 'blocked'"
        in issue
        for issue in validator.validate_self_audit_evidence(
            target
        )
    )


def test_blueprint_coordination_check_is_not_applicable() -> None:
    result = run_script(
        "scripts/check_coordination_metadata.py",
        "--module-root",
        ".",
    )
    assert result.returncode == 0
    assert "Repository class: blueprint" in result.stdout
    assert "Applicability: NOT_APPLICABLE" in result.stdout
    assert "RESULT: N/A" in result.stdout
    assert "current_status.yaml" not in result.stdout


def test_blueprint_prompt_dashboard_uses_self_queue() -> None:
    result = run_script(
        "scripts/coordination/render_prompt_dashboard.py",
        "--module",
        "forprint_system_blueprint",
        "--no-color",
    )
    assert result.returncode == 0
    assert "forprint_system_blueprint" in result.stdout
    assert "prompt index does not exist" not in result.stdout
    assert (
        "coordination/outgoing_prompts/"
        "forprint_system_blueprint/index.yaml"
        not in result.stdout
    )


def test_blueprint_self_status_is_ready_to_initialize(
    tmp_path: Path,
    capsys,
) -> None:
    result = self_audit.status(tmp_path, use_color=False)
    captured = capsys.readouterr()
    assert result == 0
    assert "configured and ready to initialize" in captured.out
    assert "RESULT: READY_TO_INITIALIZE" in captured.out
    assert "RESULT: NOT_INITIALIZED" not in captured.out
