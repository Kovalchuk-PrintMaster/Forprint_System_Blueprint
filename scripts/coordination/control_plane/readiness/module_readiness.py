from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import yaml

SCHEMA = "forprint_module_readiness_evaluation_v0_1"

BOOTSTRAP_READY = "BOOTSTRAP_READY"
BOOTSTRAP_BLOCKED = "BOOTSTRAP_BLOCKED"
DEVELOPMENT_READY = "DEVELOPMENT_READY"
DEVELOPMENT_BLOCKED = "DEVELOPMENT_BLOCKED"

PORTFOLIO_BOOTSTRAP_READY = "BOOTSTRAP_READY"
PORTFOLIO_BOOTSTRAPPED = "BOOTSTRAPPED"
PORTFOLIO_VERIFIED_WORK_READY = "VERIFIED_WORK_READY"

BLOCKER_BOOTSTRAP_CONTEXT_NOT_READY = "BOOTSTRAP_CONTEXT_NOT_READY"
BLOCKER_BOOTSTRAP_AUTHORITY_INVALID = "BOOTSTRAP_AUTHORITY_INVALID"
BLOCKER_STAGE_0_NOT_REQUIRED = "STAGE_0_NOT_REQUIRED"
BLOCKER_BOOTSTRAP_ACCEPTANCE_NOT_PROVIDED = "BOOTSTRAP_ACCEPTANCE_NOT_PROVIDED"
BLOCKER_STRICT_TASK_CONTEXT_NOT_READY = "STRICT_TASK_CONTEXT_NOT_READY"
BLOCKER_INSPECTOR_BINDING_NOT_READY = "INSPECTOR_REVIEWER_BINDING_NOT_READY"
BLOCKER_DEPENDENCY_READINESS_NOT_READY = "DEPENDENCY_READINESS_NOT_READY"


class ReadinessError(ValueError):
    pass


@dataclass(frozen=True)
class DevelopmentSignals:
    bootstrap_accepted: bool = False
    strict_task_context_ready: bool = False
    inspector_binding_ready: bool = False
    dependency_readiness_ready: bool = False


def _stable_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _bootstrap_blockers(context: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if context.get("execution_class") != "MODULE_BOOTSTRAP":
        blockers.append(BLOCKER_BOOTSTRAP_CONTEXT_NOT_READY)
    if context.get("state") != BOOTSTRAP_READY:
        blockers.append(BLOCKER_BOOTSTRAP_CONTEXT_NOT_READY)

    authority = context.get("authority")
    if not isinstance(authority, dict) or (
        authority.get("release_authorization_validated") is not True
    ):
        blockers.append(BLOCKER_BOOTSTRAP_AUTHORITY_INVALID)

    stage_0 = context.get("stage_0")
    if not isinstance(stage_0, dict) or stage_0.get("required") is not True:
        blockers.append(BLOCKER_STAGE_0_NOT_REQUIRED)

    debt = context.get("bootstrap_debt", [])
    if not isinstance(debt, list):
        raise ReadinessError("bootstrap_debt must be a list")
    for row in debt:
        if not isinstance(row, dict):
            raise ReadinessError("bootstrap_debt rows must be mappings")
        if row.get("blocking_for_bootstrap") is True:
            code = row.get("code")
            blockers.append(f"BOOTSTRAP_DEBT:{code if isinstance(code, str) else 'UNKNOWN'}")

    return _stable_unique(blockers)


def evaluate_module_readiness(
    *,
    bootstrap_context: dict[str, Any],
    signals: DevelopmentSignals,
) -> dict[str, Any]:
    module_id = bootstrap_context.get("module_id")
    prompt_id = bootstrap_context.get("prompt_id")
    if not isinstance(module_id, str) or not module_id:
        raise ReadinessError("module_id missing")
    if not isinstance(prompt_id, str) or not prompt_id:
        raise ReadinessError("prompt_id missing")

    bootstrap_blockers = _bootstrap_blockers(bootstrap_context)
    bootstrap_state = BOOTSTRAP_READY if not bootstrap_blockers else BOOTSTRAP_BLOCKED

    development_blockers: list[str] = list(bootstrap_blockers)

    if not signals.bootstrap_accepted:
        development_blockers.append(BLOCKER_BOOTSTRAP_ACCEPTANCE_NOT_PROVIDED)
    if not signals.strict_task_context_ready:
        development_blockers.append(BLOCKER_STRICT_TASK_CONTEXT_NOT_READY)
    if not signals.inspector_binding_ready:
        development_blockers.append(BLOCKER_INSPECTOR_BINDING_NOT_READY)
    if not signals.dependency_readiness_ready:
        development_blockers.append(BLOCKER_DEPENDENCY_READINESS_NOT_READY)

    debt = bootstrap_context.get("bootstrap_debt", [])
    unresolved_development_debt: list[dict[str, Any]] = []
    for row in debt:
        if row.get("blocking_for_development") is True:
            code = row.get("code")
            if not isinstance(code, str) or not code:
                code = "UNKNOWN"
            development_blockers.append(f"UNRESOLVED_BOOTSTRAP_DEBT:{code}")
            unresolved_development_debt.append(
                {
                    "code": code,
                    "required_resolution": row.get("required_resolution"),
                }
            )

    development_blockers = _stable_unique(development_blockers)
    development_state = DEVELOPMENT_READY if not development_blockers else DEVELOPMENT_BLOCKED

    if development_state == DEVELOPMENT_READY:
        portfolio_state = PORTFOLIO_VERIFIED_WORK_READY
    elif bootstrap_state == BOOTSTRAP_READY and signals.bootstrap_accepted:
        portfolio_state = PORTFOLIO_BOOTSTRAPPED
    else:
        portfolio_state = PORTFOLIO_BOOTSTRAP_READY

    result = {
        "schema_version": SCHEMA,
        "module_id": module_id,
        "prompt_id": prompt_id,
        "bootstrap_readiness": {
            "state": bootstrap_state,
            "ready": bootstrap_state == BOOTSTRAP_READY,
            "blockers": bootstrap_blockers,
            "bootstrap_debt_count": bootstrap_context.get(
                "bootstrap_debt_count",
                len(debt),
            ),
            "bootstrap_debt_codes": [row.get("code") for row in debt if isinstance(row, dict)],
        },
        "development_readiness": {
            "state": development_state,
            "ready": development_state == DEVELOPMENT_READY,
            "blockers": development_blockers,
            "unresolved_bootstrap_debt": unresolved_development_debt,
            "signals": {
                "bootstrap_accepted": signals.bootstrap_accepted,
                "strict_task_context_ready": (signals.strict_task_context_ready),
                "inspector_binding_ready": signals.inspector_binding_ready,
                "dependency_readiness_ready": (signals.dependency_readiness_ready),
            },
        },
        "portfolio_state": portfolio_state,
        "authority_semantics": {
            "bootstrap_ready_is_execution_authority": False,
            "development_ready_is_operator_approval": False,
            "automatic_accept": False,
            "automatic_next_prompt_release": False,
        },
    }
    fingerprint_source = yaml.safe_dump(
        result,
        sort_keys=True,
        allow_unicode=True,
    ).encode("utf-8")
    result["readiness_fingerprint_sha256"] = hashlib.sha256(fingerprint_source).hexdigest()
    return result
