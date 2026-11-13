from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PULSE = ROOT / "scripts/coordination/coordination_pulse.py"


def pulse_module():
    spec = importlib.util.spec_from_file_location(
        "coordination_pulse_observability_test",
        PULSE,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discovery_report(
    *,
    present: int,
    absent: int,
    review_candidates: int,
    invalid_events: int = 0,
    source_errors: int = 0,
    result_state: str = "READY_FOR_BLUEPRINT_REVIEW",
) -> dict:
    states = {}
    if present:
        states["present"] = present
    if absent:
        states["not_present_yet"] = absent
    return {
        "result_state": result_state,
        "summary": {
            "registered_sources": present + absent,
            "observed_source_states": states,
            "events_discovered": review_candidates,
            "review_candidates": review_candidates,
            "superseded_events": 0,
            "invalid_events": invalid_events,
            "source_errors": source_errors,
        },
        "review_candidates": [],
        "sources": [],
        "governance": {
            "module_repository_writes": False,
            "operator_decision_created": False,
        },
    }


def test_pulse_uses_live_discovery_counts_for_one_present_source(monkeypatch) -> None:
    module = pulse_module()
    report = discovery_report(
        present=1,
        absent=7,
        review_candidates=1,
    )
    monkeypatch.setattr(
        module,
        "_completion_discovery_report",
        lambda root, registry_path: report,
    )

    pulse = module.evaluate(ROOT)
    completions = pulse["completions"]

    assert completions["registered_module_sources"] == 8
    assert completions["outbox_present_sources"] == 1
    assert completions["outbox_not_present_yet_sources"] == 7
    assert completions["outbox_other_sources"] == 0
    assert completions["pending_completions"] == 1
    assert completions["state"] == "review_candidates_available"
    assert completions["review_candidates"] == 1
    assert completions["invalid_events"] == 0
    assert completions["source_errors"] == 0
    assert completions["discovery_result_state"] == "READY_FOR_BLUEPRINT_REVIEW"
    assert completions["observation_source"] == "completion_discovery_and_intake_v0_4"


def test_pulse_preserves_zero_outbox_state(monkeypatch) -> None:
    module = pulse_module()
    report = discovery_report(
        present=0,
        absent=8,
        review_candidates=0,
        result_state="NO_COMPLETIONS_AVAILABLE",
    )
    monkeypatch.setattr(
        module,
        "_completion_discovery_report",
        lambda root, registry_path: report,
    )

    pulse = module.evaluate(ROOT)
    completions = pulse["completions"]

    assert completions["outbox_present_sources"] == 0
    assert completions["outbox_not_present_yet_sources"] == 8
    assert completions["pending_completions"] is None
    assert completions["state"] == "not_available_yet"


def test_pulse_surfaces_discovery_attention_without_inventing_pending_count(
    monkeypatch,
) -> None:
    module = pulse_module()
    report = discovery_report(
        present=1,
        absent=7,
        review_candidates=0,
        invalid_events=1,
        result_state="DISCOVERY_ATTENTION_REQUIRED",
    )
    monkeypatch.setattr(
        module,
        "_completion_discovery_report",
        lambda root, registry_path: report,
    )

    pulse = module.evaluate(ROOT)
    completions = pulse["completions"]

    assert completions["outbox_present_sources"] == 1
    assert completions["outbox_not_present_yet_sources"] == 7
    assert completions["pending_completions"] is None
    assert completions["state"] == "discovery_attention_required"
    assert completions["invalid_events"] == 1
