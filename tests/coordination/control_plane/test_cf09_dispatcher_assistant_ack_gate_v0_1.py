from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts/coordination/control_plane/dispatch_intent.py"
CONTROL = (
    ROOT / "coordination/standards/automation/control_plane/"
    "central_listener_dispatcher_monitor_v0_1.yaml"
)
HANDOFF = ROOT / "coordination/standards/automation/assistant_handoff_v2_contract_v0_1.yaml"

spec = importlib.util.spec_from_file_location("_cf09_ack_candidate", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def prepared():
    return {
        "mode": "TASK_EXECUTION",
        "state": "AWAITING_ASSISTANT_ACK",
        "assistant_ack_validated": False,
        "handoff_manifest_sha256": "a" * 64,
        "authority": {
            "execution_authority_granted": False,
            "dispatch_authority_granted": False,
            "worker_dispatch_performed": False,
            "external_dispatch_allowed": False,
            "release_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
        },
        "next_required_human_boundary": "ASSISTANT_ACK_REQUIRED",
    }


def ack():
    return {
        "schema_version": "forprint_assistant_handoff_v2_ack_v0_1",
        "handoff_manifest_sha256": "a" * 64,
        "launch_mode": "TASK_EXECUTION",
        "context_fingerprint": "ctx:test",
        "authority_ack": {"value": "expected-authority"},
        "work_front_ack": {"value": "expected-front"},
        "profile_ack": {"value": "expected-profile"},
        "procedure_ack": {"value": "expected-procedure"},
        "freshness_ack": {"value": "expected-freshness"},
    }


def test_valid_ack_is_only_path_to_ready():
    ready = mod.validate_cf09_assistant_ack(
        root=ROOT,
        prepared_execution=prepared(),
        assistant_ack=ack(),
        expected_ack=ack(),
        expected_ack_source="TRUSTED_HANDOFF_PACK",
    )
    assert ready["state"] == "READY_FOR_EXPLICIT_DISPATCH"
    assert ready["assistant_ack_validated"] is True
    assert ready["next_required_human_boundary"] == "EXPLICIT_DISPATCH_DECISION"
    assert ready["assistant_ack_gate"]["grants_authority"] is False
    assert ready["authority"]["worker_dispatch_performed"] is False


def test_missing_and_additional_fields_fail_closed():
    expected = ack()

    missing = ack()
    missing.pop("freshness_ack")
    try:
        mod.validate_cf09_assistant_ack(
            root=ROOT,
            prepared_execution=prepared(),
            assistant_ack=missing,
            expected_ack=expected,
            expected_ack_source="TRUSTED_HANDOFF_PACK",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("missing ACK field accepted")

    extra = ack()
    extra["manifest_hash"] = "alias"
    try:
        mod.validate_cf09_assistant_ack(
            root=ROOT,
            prepared_execution=prepared(),
            assistant_ack=extra,
            expected_ack=expected,
            expected_ack_source="TRUSTED_HANDOFF_PACK",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("additional ACK field accepted")


def test_manifest_and_launch_mode_bindings_fail_closed():
    for field, value in (
        ("handoff_manifest_sha256", "b" * 64),
        ("launch_mode", "PROJECT_ONBOARD"),
    ):
        expected = ack()
        assistant = ack()
        expected[field] = value
        assistant[field] = value
        try:
            mod.validate_cf09_assistant_ack(
                root=ROOT,
                prepared_execution=prepared(),
                assistant_ack=assistant,
                expected_ack=expected,
                expected_ack_source="DISPATCHER_CANONICAL_BINDING",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(f"{field} mismatch accepted")


def test_any_opaque_ack_binding_mismatch_blocks_ready():
    for field in (
        "context_fingerprint",
        "authority_ack",
        "work_front_ack",
        "profile_ack",
        "procedure_ack",
        "freshness_ack",
    ):
        assistant = ack()
        assistant[field] = {"different": field}
        try:
            mod.validate_cf09_assistant_ack(
                root=ROOT,
                prepared_execution=prepared(),
                assistant_ack=assistant,
                expected_ack=ack(),
                expected_ack_source="TRUSTED_HANDOFF_PACK",
            )
        except ValueError as exc:
            assert field in str(exc)
        else:
            raise AssertionError(f"{field} mismatch accepted")


def test_untrusted_expected_ack_source_is_rejected():
    try:
        mod.validate_cf09_assistant_ack(
            root=ROOT,
            prepared_execution=prepared(),
            assistant_ack=ack(),
            expected_ack=ack(),
            expected_ack_source="ASSISTANT_SUPPLIED_EXPECTATION",
        )
    except ValueError as exc:
        assert "trusted" in str(exc)
    else:
        raise AssertionError("untrusted expected ACK accepted")


def test_contract_reuses_canonical_ack_without_parallel_schema():
    handoff = yaml.safe_load(HANDOFF.read_text(encoding="utf-8"))
    control = yaml.safe_load(CONTROL.read_text(encoding="utf-8"))
    exact = handoff["ack_envelope"]["exact_fields"]
    row = control["cf09_assistant_ack_gate"]

    assert exact == [
        "schema_version",
        "handoff_manifest_sha256",
        "launch_mode",
        "context_fingerprint",
        "authority_ack",
        "work_front_ack",
        "profile_ack",
        "procedure_ack",
        "freshness_ack",
    ]
    assert row["canonical_ack_contract"]["parallel_ack_schema_created"] is False
    assert row["canonical_ack_contract"]["exact_fields_reused"] is True
    assert row["state_transition"]["ready_before_ack"] is False
    assert row["trusted_expectation"]["dispatcher_interprets_ack_field_value_schema"] is False
    assert row["authority"]["worker_launch"] is False
    assert row["authority"]["cf10_started"] is False
