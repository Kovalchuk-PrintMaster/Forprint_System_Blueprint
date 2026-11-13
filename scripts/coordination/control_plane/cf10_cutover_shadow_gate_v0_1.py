"""CF10 r017 — source-bound, always-denying canonical cutover SHADOW gate.

Never an authorization adapter, real supervisor, password checker or claim writer.
The candidate canonical entrypoints call deny_live_launch before reaching legacy
root-inherited subprocess.Popen, sudo PAM, ledger or any real attempt mutation.
All readiness evidence is review-only and cannot switch this gate to allow.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections.abc import Mapping

ATTEMPT = re.compile(r"cf10-[A-Za-z0-9_-]{3,80}-a[0-9]{3,5}\Z")
TASK = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{4,127}\Z")
HEX40 = re.compile(r"[a-f0-9]{40}\Z")
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
WORKER = "worker-01"
VALID_ROUTES = frozenset({"launch_cycle", "launch_authorized_worker_cycle"})
CHECKS = (
    "canonical_operator_authority_replaced",
    "frozen_source_and_handoff_verified",
    "preclaim_workspace_and_runner_verified",
    "ledger_and_root_receipt_crash_protocol_verified",
    "systemd_credential_scope_and_env_verified",
    "systemd_service_and_cgroup_recovery_verified",
    "independent_delta_and_worker_result_verified",
    "independent_release_authority_verified",
)
class CutoverBlocked(RuntimeError):
    pass

def _bad(value, pattern):
    return not isinstance(value, str) or pattern.fullmatch(value) is None

def deny_live_launch(*, route: str, task_prompt_id: str, attempt_id: str,
                     worker_id: str) -> None:
    """Unconditionally block both canonical worker-entry routes before side effects."""
    if route not in VALID_ROUTES or _bad(task_prompt_id, TASK) or _bad(attempt_id, ATTEMPT) or worker_id != WORKER:
        raise CutoverBlocked("CF10_R017_LAUNCH_SCOPE_INVALID_NO_AUTHORITY")
    raise CutoverBlocked("CF10_R017_CANONICAL_CUTOVER_UNWIRED_NO_LIVE_LAUNCH")

def review_only(*, source_head: str, task_prompt_id: str, attempt_id: str,
                handoff_sha256: str, claims: Mapping) -> dict:
    """Hash only allowlisted *boolean* review claims; NEVER accept as evidence.

    Caller-provided values are untrusted, even when every claim is True.
    Reject unknown keys to avoid accidentally serializing secrets.
    """
    if _bad(source_head, HEX40) or _bad(task_prompt_id, TASK) or _bad(attempt_id, ATTEMPT) or _bad(handoff_sha256, HEX64):
        raise CutoverBlocked("CF10_R017_REVIEW_SCOPE_INVALID")
    if not isinstance(claims, Mapping) or set(claims) != set(CHECKS) or any(type(claims[k]) is not bool for k in CHECKS):
        raise CutoverBlocked("CF10_R017_REVIEW_CLAIMS_INVALID_OR_UNEXPECTED")
    observed = {key: claims[key] for key in CHECKS}
    unproven = sorted(key for key in CHECKS if not observed[key])
    binding = dict(source_head=source_head, task_prompt_id=task_prompt_id,
                   attempt_id=attempt_id, handoff_sha256=handoff_sha256)
    digest = hashlib.sha256(json.dumps({"binding":binding,"claims":observed},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {"schema_version":"cf10_r017_shadow_readiness_v0_1",
            "binding":binding,"review_claims_sha256":digest,
            "unproven_or_untrusted_claims":unproven,
            "claims_are_authority":False,"production_quiescence_proven":False,
            "claim_issued":False,"worker_launched":False,
            "automatic_retry":False,"worker_result_accepted":False,
            "operator_authorization_granted":False,"release_allowed":False,
            "status":"BLOCKED_PENDING_INDEPENDENT_PRODUCTION_EVIDENCE"}
