from __future__ import annotations

import subprocess
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "coordination/global_policy/project_native_execution_policy_v0_1.yaml"
SPECS = ROOT / "coordination/bootstrap/assistant_context_system_specs_v0_1.yaml"

def test_project_native_execution_policy_is_active_and_complete() -> None:
    data = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    assert data["status"] == "ACTIVE_CANONICAL_POLICY"
    assert data["human_owner_intent"]["chat_is_not_primary_runtime"] is True
    assert data["human_owner_intent"]["project_is_primary_home_for_logic"] is True
    assert [row["id"] for row in data["core_rules"]] == [
        "PNX-01", "PNX-02", "PNX-03", "PNX-04",
        "PNX-05", "PNX-06", "PNX-07", "PNX-08",
    ]

def test_assistant_context_specs_carry_mandatory_policy_digest() -> None:
    specs = yaml.safe_load(SPECS.read_text(encoding="utf-8"))
    section = specs["project_native_execution_policy"]
    assert section["canonical_source"] == "coordination/global_policy/project_native_execution_policy_v0_1.yaml"
    assert section["required_for_zero_context_assistant"] is True
    assert section["required_for_module_context_work"] is True
    assert section["grants_execution_authority"] is False

def test_validator_passes() -> None:
    cp = subprocess.run([str(ROOT / ".venv_blueprint/bin/python"), "scripts/validation/validate_project_native_execution_policy_v0_1.py"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    assert cp.returncode == 0, cp.stdout
    assert "PROJECT_NATIVE_EXECUTION_POLICY=PASS" in cp.stdout
