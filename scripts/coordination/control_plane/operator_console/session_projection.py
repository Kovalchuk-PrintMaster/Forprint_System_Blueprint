from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import Any
import yaml

SCHEMA_VERSION = "forprint_oc01_session_projection_v0_1"
ALLOWED_ACTOR_TYPES = frozenset({"internal_worker", "operator_assistant", "human_terminal"})
SESSION_PENDING = "DEPENDENCY_PENDING_CF10"
CHECKPOINT_STATE = "PARTIAL_REUSE_DEPENDENCY_PENDING_CF10"


class SessionProjectionError(ValueError):
    pass


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SessionProjectionError(f"{label} must be a mapping")
    return value


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SessionProjectionError(f"{label} must be a non-empty string")
    return value.strip()


def _optional_string(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise SessionProjectionError(f"{label} missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SessionProjectionError(f"{label} must be a mapping")
    return data


def _nested(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    item = value.get(key)
    return item if isinstance(item, Mapping) else {}


def _first_string(*values: Any) -> str | None:
    for value in values:
        result = _optional_string(value)
        if result is not None:
            return result
    return None


def _worker_id(launch: Mapping[str, Any], invocation: Mapping[str, Any]) -> str | None:
    return _first_string(
        invocation.get("worker_id"),
        _nested(invocation, "binding").get("worker_id"),
        _nested(invocation, "identity").get("worker_id"),
        _nested(launch, "identity").get("worker_id"),
    )


def _workspace(invocation: Mapping[str, Any], attempt_id: str, manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    repo = _optional_string(invocation.get("workspace_repo"))
    if repo is None:
        raise SessionProjectionError("worker invocation workspace_repo is required")
    result = {
        "binding_state": "INVOCATION_BOUND_ONLY",
        "workspace_repo": repo,
        "manifest_observed": False,
        "source_head": None,
        "source_state_fingerprint": None,
        "canonical_write_allowed_by_oc01": False,
    }
    if manifest is None:
        return result
    if manifest.get("schema_version") != "forprint_worker_workspace_manifest_v0_1":
        raise SessionProjectionError("workspace manifest schema mismatch")
    if manifest.get("attempt_id") != attempt_id:
        raise SessionProjectionError("workspace manifest attempt_id mismatch")
    if manifest.get("workspace_repo") != repo:
        raise SessionProjectionError("workspace manifest workspace_repo mismatch")
    if manifest.get("canonical_write_allowed") is not False:
        raise SessionProjectionError("workspace manifest canonical_write_allowed must remain false")
    result.update({
        "binding_state": "MANIFEST_BOUND",
        "manifest_observed": True,
        "source_head": _optional_string(manifest.get("source_head")),
        "source_state_fingerprint": _optional_string(manifest.get("source_state_fingerprint")),
        "workspace_state": _optional_string(manifest.get("workspace_state")),
    })
    return result


def build_session_projection(*, launch_request: Mapping[str, Any], worker_invocation: Mapping[str, Any], actor_type: str, actor_id: str, workspace_manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    actor_type = _required_string(actor_type, "actor_type")
    actor_id = _required_string(actor_id, "actor_id")
    if actor_type not in ALLOWED_ACTOR_TYPES:
        raise SessionProjectionError(f"unsupported actor_type={actor_type!r}")
    launch_request = _mapping(launch_request, "launch_request")
    worker_invocation = _mapping(worker_invocation, "worker_invocation")
    if workspace_manifest is not None:
        workspace_manifest = _mapping(workspace_manifest, "workspace_manifest")
    identity = _mapping(launch_request.get("identity"), "launch_request.identity")
    module_id = _required_string(identity.get("module_id"), "identity.module_id")
    prompt_id = _required_string(identity.get("prompt_id"), "identity.prompt_id")
    attempt_id = _required_string(worker_invocation.get("attempt_id"), "worker_invocation.attempt_id")
    worker_id = _worker_id(launch_request, worker_invocation)
    seconds = worker_invocation.get("heartbeat_seconds")
    heartbeat_configured = isinstance(seconds, int) and not isinstance(seconds, bool) and seconds > 0
    return {
        "schema_version": SCHEMA_VERSION,
        "projection_role": "READ_ONLY_DERIVED_CONSUMER_VIEW",
        "authority": {
            "state_authority": False,
            "execution_authority": False,
            "dispatch_authority": False,
            "lease_authority": False,
            "acceptance_authority": False,
            "release_authority": False,
            "canonical_write_authority": False,
        },
        "execution_identity": {
            "module_id": module_id,
            "prompt_id": prompt_id,
            "worker_id": worker_id,
            "worker_id_state": "OBSERVED" if worker_id else "NOT_OBSERVED",
            "attempt_id": attempt_id,
        },
        "actor": {
            "actor_type": actor_type,
            "actor_id": actor_id,
            "binding": "DECLARED_CONSUMER_CONTEXT",
            "authority_conferred": False,
        },
        "session": {
            "canonical_session_state": SESSION_PENDING,
            "canonical_session_id": None,
            "exclusive_module_lease": SESSION_PENDING,
            "lease_id": None,
            "oc01_created_parallel_session_truth": False,
            "oc01_created_parallel_lease_truth": False,
        },
        "workspace": _workspace(worker_invocation, attempt_id, workspace_manifest),
        "heartbeat": {
            "configuration_observed": heartbeat_configured,
            "heartbeat_seconds": seconds if heartbeat_configured else None,
            "observation_state": "CONFIGURED_NOT_OBSERVED_BY_THIS_PROJECTION" if heartbeat_configured else "NOT_OBSERVED",
            "authority": "NON_AUTHORITATIVE_EVIDENCE_ONLY",
            "session_authority": False,
            "lease_authority": False,
        },
        "checkpoint_resume": {"state": CHECKPOINT_STATE, "authority": "CF10_DEPENDENCY"},
        "write_readiness": {
            "canonical_write_ready": False,
            "blockers": ["CANONICAL_SESSION_NOT_PROVEN", "EXCLUSIVE_MODULE_LEASE_NOT_PROVEN"],
        },
        "execution_boundaries": {
            "runtime_state_mutated": False,
            "worker_process_started": False,
            "prompt_claim_performed": False,
            "module_repository_write_performed": False,
            "candidate_promotion_performed": False,
            "commit_performed": False,
            "push_performed": False,
            "release_performed": False,
        },
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Render OC-01 MINI-1 read-only dependency/session projection")
    p.add_argument("--launch-request", required=True)
    p.add_argument("--worker-invocation", required=True)
    p.add_argument("--actor-type", required=True, choices=sorted(ALLOWED_ACTOR_TYPES))
    p.add_argument("--actor-id", required=True)
    p.add_argument("--workspace-manifest")
    p.add_argument("--print", action="store_true")
    a = p.parse_args()
    projection = build_session_projection(
        launch_request=_load_yaml(Path(a.launch_request), "launch request"),
        worker_invocation=_load_yaml(Path(a.worker_invocation), "worker invocation"),
        actor_type=a.actor_type,
        actor_id=a.actor_id,
        workspace_manifest=_load_yaml(Path(a.workspace_manifest), "workspace manifest") if a.workspace_manifest else None,
    )
    if a.print:
        print(yaml.safe_dump(projection, sort_keys=False, allow_unicode=True, width=112).rstrip())
    else:
        print("OC01_SESSION_PROJECTION=PASS")
        print(f"MODULE_ID={projection['execution_identity']['module_id']}")
        print(f"PROMPT_ID={projection['execution_identity']['prompt_id']}")
        print(f"ATTEMPT_ID={projection['execution_identity']['attempt_id']}")
        print(f"ACTOR_TYPE={projection['actor']['actor_type']}")
        print(f"CANONICAL_SESSION_STATE={projection['session']['canonical_session_state']}")
        print(f"EXCLUSIVE_MODULE_LEASE={projection['session']['exclusive_module_lease']}")
        print("CANONICAL_WRITE_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
