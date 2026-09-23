from __future__ import annotations

from scripts.coordination.control_plane.readiness.module_readiness import (
    BOOTSTRAP_BLOCKED,
    BOOTSTRAP_READY,
    DEVELOPMENT_BLOCKED,
    DEVELOPMENT_READY,
    DevelopmentSignals,
    evaluate_module_readiness,
)


def _context(*, debt=None, authority=True, stage_0=True):
    rows = [] if debt is None else debt
    return {
        "schema_version": "forprint_bootstrap_task_context_envelope_v0_1",
        "execution_class": "MODULE_BOOTSTRAP",
        "state": "BOOTSTRAP_READY",
        "module_id": "sample",
        "prompt_id": "sample_bootstrap_v0_1",
        "authority": {
            "release_authorization_validated": authority,
        },
        "stage_0": {"required": stage_0},
        "bootstrap_debt": rows,
        "bootstrap_debt_count": len(rows),
    }


def _green_signals():
    return DevelopmentSignals(
        bootstrap_accepted=True,
        strict_task_context_ready=True,
        inspector_binding_ready=True,
        dependency_readiness_ready=True,
    )


def test_bootstrap_debt_does_not_block_bootstrap_when_nonblocking() -> None:
    result = evaluate_module_readiness(
        bootstrap_context=_context(
            debt=[
                {
                    "code": "FRESH_CONTEXT_STALE",
                    "blocking_for_bootstrap": False,
                    "blocking_for_development": True,
                    "required_resolution": "REFRESH",
                }
            ]
        ),
        signals=DevelopmentSignals(),
    )
    assert result["bootstrap_readiness"]["state"] == BOOTSTRAP_READY
    assert result["development_readiness"]["state"] == DEVELOPMENT_BLOCKED


def test_bootstrap_ready_never_means_development_ready() -> None:
    result = evaluate_module_readiness(
        bootstrap_context=_context(),
        signals=DevelopmentSignals(),
    )
    assert result["bootstrap_readiness"]["ready"] is True
    assert result["development_readiness"]["ready"] is False
    assert "BOOTSTRAP_ACCEPTANCE_NOT_PROVIDED" in result["development_readiness"]["blockers"]


def test_all_development_signals_and_no_debt_yield_development_ready() -> None:
    result = evaluate_module_readiness(
        bootstrap_context=_context(),
        signals=_green_signals(),
    )
    assert result["development_readiness"]["state"] == DEVELOPMENT_READY
    assert result["portfolio_state"] == "VERIFIED_WORK_READY"


def test_unresolved_bootstrap_debt_blocks_development() -> None:
    result = evaluate_module_readiness(
        bootstrap_context=_context(
            debt=[
                {
                    "code": "MODULE_RUNTIME_PROFILE_MISSING",
                    "blocking_for_bootstrap": False,
                    "blocking_for_development": True,
                    "required_resolution": "CREATE_PROFILE",
                }
            ]
        ),
        signals=_green_signals(),
    )
    assert result["bootstrap_readiness"]["state"] == BOOTSTRAP_READY
    assert result["development_readiness"]["state"] == DEVELOPMENT_BLOCKED
    assert (
        "UNRESOLVED_BOOTSTRAP_DEBT:MODULE_RUNTIME_PROFILE_MISSING"
        in result["development_readiness"]["blockers"]
    )


def test_invalid_authority_blocks_both_readiness_levels() -> None:
    result = evaluate_module_readiness(
        bootstrap_context=_context(authority=False),
        signals=_green_signals(),
    )
    assert result["bootstrap_readiness"]["state"] == BOOTSTRAP_BLOCKED
    assert result["development_readiness"]["state"] == DEVELOPMENT_BLOCKED


def test_bootstrap_blocking_debt_is_fail_closed() -> None:
    result = evaluate_module_readiness(
        bootstrap_context=_context(
            debt=[
                {
                    "code": "UNKNOWN_AUTHORITY",
                    "blocking_for_bootstrap": True,
                    "blocking_for_development": True,
                }
            ]
        ),
        signals=_green_signals(),
    )
    assert result["bootstrap_readiness"]["state"] == BOOTSTRAP_BLOCKED
    assert "BOOTSTRAP_DEBT:UNKNOWN_AUTHORITY" in result["bootstrap_readiness"]["blockers"]
