from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/validation/validate_assistant_handoff_v2_contract_v0_1.py"

spec = importlib.util.spec_from_file_location("handoff_v2_validator", VALIDATOR)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def canonical():
    return validator.load_contract(ROOT)


def test_canonical_contract_is_valid():
    assert validator.validate_contract(canonical(), ROOT) == []


def test_ack_alias_or_extra_field_is_rejected():
    data = deepcopy(canonical())
    data["ack_envelope"]["exact_fields"].append("manifest_hash")
    errors = validator.validate_contract(data, ROOT)
    assert any("ACK exact fields mismatch" in error for error in errors)


def test_task_execution_requires_work_front():
    data = deepcopy(canonical())
    data["launch_modes"]["TASK_EXECUTION"]["front_required"] = False
    errors = validator.validate_contract(data, ROOT)
    assert any("TASK_EXECUTION.front_required must be true" in error for error in errors)


def test_contract_never_grants_dispatch_authority():
    data = deepcopy(canonical())
    data["authority"]["grants_dispatch_authority"] = True
    errors = validator.validate_contract(data, ROOT)
    assert any("grants_dispatch_authority must be false" in error for error in errors)


def test_runtime_integration_remains_outside_s1():
    data = canonical()
    assert data["cf08_s1_boundary"]["runtime_compiler_integration_implemented"] is False
    assert data["cf08_s1_boundary"]["dispatcher_implemented"] is False
    assert data["cf08_s1_boundary"]["worker_dispatch_performed"] is False
