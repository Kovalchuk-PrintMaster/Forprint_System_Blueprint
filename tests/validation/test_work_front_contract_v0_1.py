from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/coordination/work_front_v0_1.py"

spec = importlib.util.spec_from_file_location("_work_front_test_runtime", SOURCE)
assert spec is not None and spec.loader is not None
wf = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = wf
spec.loader.exec_module(wf)


def valid_front() -> dict:
    return {
        "work_front_id": "wf-test-001",
        "objective": "Implement one bounded capability.",
        "scope": ["scripts/coordination/example.py"],
        "exclusions": ["release", "foreign writes"],
        "provenance": {
            "source_refs": ["roadmap:CF-04"],
            "chat_is_authority": False,
        },
        "dependencies": ["CF-03"],
        "outputs": ["validated source change"],
        "acceptance": ["focused tests pass"],
        "stop_conditions": ["scope widening required"],
        "authority": {
            "layer": "WORK_FRONT",
            "permissions": ["read", "write_blueprint"],
            "widening_requested": False,
        },
        "capability_reuse": {
            "search_performed": True,
            "searched_surfaces": [
                "coordination/standards",
                "scripts/coordination",
            ],
            "disposition": "EXTEND",
            "target_refs": ["scripts/coordination/existing.py"],
        },
    }


def contract() -> dict:
    return wf.load_contract(ROOT)


def test_contract_loads() -> None:
    value = contract()
    assert value["authority_model"]["precedence_layer"] == "WORK_FRONT"
    assert tuple(value["capability_reuse"]["dispositions"]) == wf.REUSE_DISPOSITIONS


def test_valid_work_front_passes() -> None:
    assert wf.validate_work_front_data(valid_front(), contract()) == []


def test_missing_required_field_fails() -> None:
    value = valid_front()
    del value["acceptance"]
    errors = wf.validate_work_front_data(value, contract())
    assert "missing field: acceptance" in errors


def test_new_requires_rationale() -> None:
    value = valid_front()
    value["capability_reuse"]["disposition"] = "NEW"
    value["capability_reuse"]["target_refs"] = []
    errors = wf.validate_work_front_data(value, contract())
    assert "capability_reuse.rationale required for NEW" in errors


def test_new_with_search_and_rationale_passes() -> None:
    value = valid_front()
    value["capability_reuse"].update(
        {
            "disposition": "NEW",
            "target_refs": [],
            "rationale": "No equivalent capability exists after bounded search.",
        }
    )
    assert wf.validate_work_front_data(value, contract()) == []


def test_existing_disposition_requires_target_ref() -> None:
    value = valid_front()
    value["capability_reuse"]["target_refs"] = []
    errors = wf.validate_work_front_data(value, contract())
    assert "capability_reuse.target_refs required for EXTEND" in errors


def test_capability_search_is_required() -> None:
    value = valid_front()
    value["capability_reuse"]["search_performed"] = False
    errors = wf.validate_work_front_data(value, contract())
    assert "capability_reuse.search_performed must be true" in errors


def test_chat_cannot_be_authority() -> None:
    value = valid_front()
    value["provenance"]["chat_is_authority"] = True
    errors = wf.validate_work_front_data(value, contract())
    assert "provenance.chat_is_authority must be false" in errors


def test_widening_requires_gate_evidence() -> None:
    value = valid_front()
    value["authority"]["widening_requested"] = True
    errors = wf.validate_work_front_data(value, contract())
    assert "authority.widening_gate_evidence required when widening_requested=true" in errors


def test_authority_narrowing_is_allowed() -> None:
    effective = wf.assert_authority_narrowing(
        {"read"},
        {"read", "write_blueprint"},
    )
    assert effective == {"read"}


def test_authority_widening_fails_closed_without_gate() -> None:
    with pytest.raises(wf.WorkFrontError, match="widens higher authority"):
        wf.assert_authority_narrowing(
            {"read", "dispatch"},
            {"read"},
        )
