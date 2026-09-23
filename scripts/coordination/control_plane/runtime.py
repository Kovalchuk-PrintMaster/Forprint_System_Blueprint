from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.control_plane.dispatch_intent import build_dispatch_intent
from scripts.coordination.control_plane.events import scan_event_roots
from scripts.coordination.control_plane.monitor import build_monitor_projection


def _load(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{label} missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be mapping")
    return data


def _write_idempotent(path: Path, data: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=112)
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise ValueError(f"idempotency conflict: {path}")
        return "DUPLICATE_EQUIVALENT"
    path.write_text(text, encoding="utf-8")
    return "CREATED"


def run_control_plane_step(
    *,
    launch_request_path: Path,
    worker_invocation_path: Path,
    runtime_dir: Path,
    approval_decision_path: Path | None = None,
    event_roots: list[Path] | None = None,
    active_execution_paths: list[Path] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    launch_request_path = launch_request_path.resolve()
    worker_invocation_path = worker_invocation_path.resolve()
    approval_decision_path = approval_decision_path.resolve() if approval_decision_path else None
    runtime_dir = runtime_dir.resolve()
    launch = _load(launch_request_path, "launch request")
    invocation = _load(worker_invocation_path, "worker invocation")
    approval = (
        _load(approval_decision_path, "approval decision") if approval_decision_path else None
    )
    identity = launch.get("identity") if isinstance(launch.get("identity"), dict) else {}
    module_id = identity.get("module_id")
    prompt_id = identity.get("prompt_id")
    scan = scan_event_roots(
        event_roots=[p.resolve() for p in (event_roots or [])],
        cursor_id=f"{module_id}__{prompt_id}__control_plane_cursor",
    )
    intent = build_dispatch_intent(
        launch_request_path=launch_request_path,
        worker_invocation_path=worker_invocation_path,
        approval_decision_path=approval_decision_path,
        active_execution_paths=[p.resolve() for p in (active_execution_paths or [])],
    )
    projection = build_monitor_projection(
        launch_request=launch,
        worker_invocation=invocation,
        dispatch_intent=intent.document,
        approval_decision=approval,
        observed_event_count=len(scan.observations),
    )
    material = {
        "dispatch_intent_id": intent.document["dispatch_intent_id"],
        "cursor": scan.cursor["cursor_fingerprint_sha256"],
        "monitor_state": projection["state"],
    }
    fp = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    step_id = f"{module_id}__{prompt_id}__step__{fp[:16]}"
    paths = {
        "dispatch_intent": runtime_dir
        / "dispatch_intents"
        / f"{intent.document['dispatch_intent_id']}.yaml",
        "monitor_projection": runtime_dir
        / "monitor"
        / f"{module_id}__{prompt_id}__projection.yaml",
        "event_cursor": runtime_dir
        / "event_cursors"
        / f"{module_id}__{prompt_id}__control_plane_cursor.yaml",
    }
    writes = {}
    if write:
        for key, data in [
            ("dispatch_intent", intent.document),
            ("monitor_projection", projection),
            ("event_cursor", scan.cursor),
        ]:
            writes[key] = _write_idempotent(paths[key], data)
    return {
        "schema_version": "forprint_control_plane_step_result_v0_1",
        "step_id": step_id,
        "performed_at": datetime.now(UTC).isoformat(),
        "mode": "EXPLICIT_ONE_SHOT_CLI_STEP",
        "dispatch_intent_state": intent.state,
        "dispatch_intent_blockers": list(intent.blocker_codes),
        "monitor_state": projection["state"],
        "observed_q5_event_count": len(scan.observations),
        "invalid_q5_event_file_count": len(scan.invalid_files),
        "artifact_paths": {k: str(v) for k, v in paths.items()},
        "write_results": writes,
        "execution_boundaries": {
            "daemon_started": False,
            "worker_process_started": False,
            "prompt_claim_performed": False,
            "module_repository_write_performed": False,
            "blueprint_accept_performed": False,
            "next_prompt_release_performed": False,
        },
    }


def main() -> int:
    p = argparse.ArgumentParser(
        description="One deterministic Blueprint Control Plane step; v0.1 never starts a worker."
    )
    p.add_argument("--launch-request", required=True)
    p.add_argument("--worker-invocation", required=True)
    p.add_argument("--approval-decision")
    p.add_argument("--event-root", action="append", default=[])
    p.add_argument("--active-execution", action="append", default=[])
    p.add_argument("--runtime-dir", default="tmp/control_plane/runtime")
    p.add_argument("--no-write", action="store_true")
    p.add_argument("--print", action="store_true")
    a = p.parse_args()
    result = run_control_plane_step(
        launch_request_path=Path(a.launch_request),
        worker_invocation_path=Path(a.worker_invocation),
        approval_decision_path=Path(a.approval_decision) if a.approval_decision else None,
        event_roots=[Path(x) for x in a.event_root],
        active_execution_paths=[Path(x) for x in a.active_execution],
        runtime_dir=Path(a.runtime_dir),
        write=not a.no_write,
    )
    if a.print:
        print(yaml.safe_dump(result, sort_keys=False, allow_unicode=True, width=112).rstrip())
    else:
        print("CONTROL_PLANE_STEP=PASS")
        print(f"STEP_ID={result['step_id']}")
        print(f"DISPATCH_INTENT_STATE={result['dispatch_intent_state']}")
        print("BLOCKERS=" + ",".join(result["dispatch_intent_blockers"]))
        print(f"MONITOR_STATE={result['monitor_state']}")
        print("WORKER_PROCESS_STARTED=false")
        print("DAEMON_STARTED=false")
        print("PROMPT_CLAIM_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
