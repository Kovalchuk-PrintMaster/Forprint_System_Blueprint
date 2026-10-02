from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse

import yaml

from scripts.coordination.control_plane.operator_console.assistant_dev_sandbox import (
    AssistantDevSandboxError,
    create_sandbox,
    sandbox_status,
)
from scripts.coordination.control_plane.operator_console.console_ui import (
    render_console_html,
)
from scripts.coordination.control_plane.operator_console.promotion_surface import (
    PREVIEW_SCHEMA,
    PromotionSurfaceError,
    write_promotion_preview,
)
from scripts.coordination.control_plane.operator_console.protected_terminal import (
    ProtectedTerminalError,
    build_terminal_plan,
    execute_terminal_plan,
    list_capabilities,
)
from scripts.coordination.control_plane.operator_console.sealed_result import (
    SealedResultError,
    sealed_result_status,
    write_checkpoint_projection,
    write_sealed_result_package,
)
from scripts.coordination.control_plane.operator_console.session_projection import (
    SCHEMA_VERSION as SESSION_PROJECTION_SCHEMA,
)

SCHEMA_VERSION = "forprint_oc01_minimum_console_api_v0_1"
SNAPSHOT_SCHEMA = "forprint_oc01_console_snapshot_v0_1"
MAX_BODY_BYTES = 1024 * 1024
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})

ALLOWED_ACTIONS = frozenset(
    {
        "terminal_plan",
        "terminal_run",
        "sandbox_create",
        "sandbox_status",
        "checkpoint",
        "seal",
        "promotion_preview",
    }
)
FORBIDDEN_ACTIONS = frozenset(
    {
        "promotion_apply",
        "commit",
        "push",
        "merge",
        "release",
    }
)


class ConsoleApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConsoleConfig:
    canonical_root: Path
    runtime_root: Path

    @classmethod
    def build(
        cls,
        *,
        canonical_root: Path | str,
        runtime_root: Path | str,
    ) -> "ConsoleConfig":
        canonical = Path(canonical_root).expanduser().resolve()
        runtime = Path(runtime_root).expanduser().resolve()
        if not canonical.is_dir():
            raise ConsoleApiError("canonical_root must be an existing directory")
        if canonical == runtime or canonical in runtime.parents:
            raise ConsoleApiError("runtime_root cannot contain canonical repository")
        runtime.mkdir(parents=True, exist_ok=True)
        return cls(canonical_root=canonical, runtime_root=runtime)


def validate_bind_policy(*, host: str, allow_remote_bind: bool) -> None:
    if host not in LOOPBACK_HOSTS and allow_remote_bind is not True:
        raise ConsoleApiError(
            "non-loopback bind requires --allow-remote-bind; "
            "MINI-6 provides no authentication or TLS"
        )


def _within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _scoped_path(
    config: ConsoleConfig,
    raw: str | Path,
    *,
    label: str,
    canonical_allowed: bool = True,
    runtime_allowed: bool = True,
    must_exist: bool = True,
) -> Path:
    value = Path(raw).expanduser().resolve()
    allowed = (
        (canonical_allowed and _within(value, config.canonical_root))
        or (runtime_allowed and _within(value, config.runtime_root))
    )
    if not allowed:
        raise ConsoleApiError(
            f"{label} is outside configured canonical/runtime scope: {value}"
        )
    if must_exist and not value.exists():
        raise ConsoleApiError(f"{label} does not exist: {value}")
    return value


def _runtime_path(
    config: ConsoleConfig,
    raw: str | Path,
    *,
    label: str,
    must_exist: bool,
) -> Path:
    return _scoped_path(
        config,
        raw,
        label=label,
        canonical_allowed=False,
        runtime_allowed=True,
        must_exist=must_exist,
    )


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise ConsoleApiError(f"{label} cannot be a symlink")
    if not path.is_file():
        raise ConsoleApiError(f"{label} must be a file: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ConsoleApiError(f"{label} must be a YAML mapping")
    return value


def _required(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConsoleApiError(f"{key} is required")
    return value.strip()


def _optional(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _bool(payload: Mapping[str, Any], key: str) -> bool:
    return payload.get(key) is True


def _int(payload: Mapping[str, Any], key: str, default: int) -> int:
    value = payload.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConsoleApiError(f"{key} must be an integer")
    return value


def _session(
    config: ConsoleConfig,
    raw: str,
) -> dict[str, Any]:
    path = _scoped_path(config, raw, label="session_projection")
    value = _load_yaml(path, "session projection")
    if value.get("schema_version") != SESSION_PROJECTION_SCHEMA:
        raise ConsoleApiError("session projection schema mismatch")
    authority = value.get("authority")
    if not isinstance(authority, dict) or any(
        item is not False for item in authority.values()
    ):
        raise ConsoleApiError("session projection unexpectedly grants authority")
    return value


def _promotion_preview_status(
    config: ConsoleConfig,
    raw: str,
) -> dict[str, Any]:
    path = _runtime_path(
        config,
        raw,
        label="promotion_preview",
        must_exist=True,
    )
    value = _load_yaml(path, "promotion preview")
    if value.get("schema_version") != PREVIEW_SCHEMA:
        raise ConsoleApiError("promotion preview schema mismatch")
    return {
        "state": value.get("state"),
        "attempt_id": value.get("attempt_id"),
        "source_head": value.get("source_head"),
        "changed_paths": value.get("changed_paths"),
        "preview_sha256": value.get("preview_sha256"),
        "promotion_authority": (
            value.get("authority", {}).get("promotion_authority")
            if isinstance(value.get("authority"), dict)
            else None
        ),
        "apply_control_exposed_by_mini6": False,
    }


def build_snapshot(
    *,
    config: ConsoleConfig,
    inputs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    inputs = inputs or {}
    result: dict[str, Any] = {
        "schema_version": SNAPSHOT_SCHEMA,
        "projection_role": "NON_AUTHORITATIVE_OPERATOR_VIEW",
        "authority": {
            "state_authority": False,
            "execution_authority": False,
            "dispatch_authority": False,
            "lease_authority": False,
            "canonical_write_authority": False,
            "promotion_authority": False,
            "release_authority": False,
        },
        "transport": {
            "default_bind": "127.0.0.1",
            "authentication_provided": False,
            "tls_provided": False,
            "remote_access_requires_external_trusted_transport": True,
        },
        "roots": {
            "canonical_root": str(config.canonical_root),
            "runtime_root": str(config.runtime_root),
        },
        "terminal": list_capabilities(),
        "session": None,
        "sandbox": None,
        "result": None,
        "promotion_preview": None,
        "actions": {
            "allowed": sorted(ALLOWED_ACTIONS),
            "forbidden": sorted(FORBIDDEN_ACTIONS),
        },
    }

    session_raw = _optional(inputs, "session_projection")
    session = _session(config, session_raw) if session_raw else None
    if session is not None:
        result["session"] = session

    sandbox_raw = _optional(inputs, "sandbox_manifest")
    if sandbox_raw:
        if session is None:
            raise ConsoleApiError(
                "session_projection is required with sandbox_manifest"
            )
        manifest = _runtime_path(
            config,
            sandbox_raw,
            label="sandbox_manifest",
            must_exist=True,
        )
        result["sandbox"] = sandbox_status(
            manifest_path=manifest,
            session_projection=session,
        )

    result_raw = _optional(inputs, "result_manifest")
    if result_raw:
        manifest = _runtime_path(
            config,
            result_raw,
            label="result_manifest",
            must_exist=True,
        )
        result["result"] = sealed_result_status(manifest_path=manifest)

    preview_raw = _optional(inputs, "promotion_preview")
    if preview_raw:
        result["promotion_preview"] = _promotion_preview_status(
            config,
            preview_raw,
        )

    return result


def _action_terminal(
    *,
    config: ConsoleConfig,
    payload: Mapping[str, Any],
    execute: bool,
) -> dict[str, Any]:
    if _bool(payload, "enabled") is not True:
        raise ConsoleApiError("Protected Terminal explicit enabled=true is required")
    if execute and _bool(payload, "confirm") is not True:
        raise ConsoleApiError("terminal_run explicit confirm=true is required")

    session = _session(
        config,
        _required(payload, "session_projection"),
    )
    evidence_dir_raw = _optional(payload, "evidence_dir")
    evidence_dir = (
        _runtime_path(
            config,
            evidence_dir_raw,
            label="evidence_dir",
            must_exist=False,
        )
        if evidence_dir_raw
        else config.runtime_root / "terminal_evidence"
    )
    try:
        plan = build_terminal_plan(
            capability_id=_required(payload, "capability_id"),
            cwd=config.canonical_root,
            session_projection=session,
            enabled=True,
            capability_class="READ_ONLY",
            timeout_seconds=_int(payload, "timeout_seconds", 30),
            evidence_dir=evidence_dir,
        )
        if execute:
            return execute_terminal_plan(plan)
        return plan
    except ProtectedTerminalError as exc:
        raise ConsoleApiError(str(exc)) from exc


def _action_sandbox_create(
    config: ConsoleConfig,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    session = _session(
        config,
        _required(payload, "session_projection"),
    )
    try:
        return create_sandbox(
            canonical_repo=config.canonical_root,
            runtime_root=config.runtime_root,
            module_id=_required(payload, "module_id"),
            worker_id=_required(payload, "worker_id"),
            attempt_id=_required(payload, "attempt_id"),
            expected_base_head=_required(payload, "expected_base_head"),
            session_projection=session,
        )
    except AssistantDevSandboxError as exc:
        raise ConsoleApiError(str(exc)) from exc


def _action_sandbox_status(
    config: ConsoleConfig,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    session = _session(
        config,
        _required(payload, "session_projection"),
    )
    manifest = _runtime_path(
        config,
        _required(payload, "manifest"),
        label="manifest",
        must_exist=True,
    )
    try:
        return sandbox_status(
            manifest_path=manifest,
            session_projection=session,
        )
    except AssistantDevSandboxError as exc:
        raise ConsoleApiError(str(exc)) from exc


def _action_checkpoint(
    config: ConsoleConfig,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    session = _session(
        config,
        _required(payload, "session_projection"),
    )
    manifest = _runtime_path(
        config,
        _required(payload, "manifest"),
        label="manifest",
        must_exist=True,
    )
    resume_raw = _optional(payload, "resume_evidence")
    resume = (
        _runtime_path(
            config,
            resume_raw,
            label="resume_evidence",
            must_exist=True,
        )
        if resume_raw
        else None
    )
    try:
        return write_checkpoint_projection(
            manifest_path=manifest,
            session_projection=session,
            resume_evidence_path=resume,
        )
    except SealedResultError as exc:
        raise ConsoleApiError(str(exc)) from exc


def _action_seal(
    config: ConsoleConfig,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    session = _session(
        config,
        _required(payload, "session_projection"),
    )
    manifest = _runtime_path(
        config,
        _required(payload, "manifest"),
        label="manifest",
        must_exist=True,
    )
    validation = payload.get("validation_evidence")
    if not isinstance(validation, list) or not all(
        isinstance(item, str) and item.strip() for item in validation
    ):
        raise ConsoleApiError(
            "validation_evidence must be a non-empty list of strings"
        )
    artifacts = payload.get("artifacts")
    issues = payload.get("open_issues")
    try:
        return write_sealed_result_package(
            manifest_path=manifest,
            session_projection=session,
            validation_evidence=validation,
            artifacts=artifacts if isinstance(artifacts, list) else None,
            open_issues=issues if isinstance(issues, list) else None,
        )
    except SealedResultError as exc:
        raise ConsoleApiError(str(exc)) from exc


def _action_promotion_preview(
    config: ConsoleConfig,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    candidate = _runtime_path(
        config,
        _required(payload, "candidate_root"),
        label="candidate_root",
        must_exist=True,
    )
    sealed = _runtime_path(
        config,
        _required(payload, "sealed_result"),
        label="sealed_result",
        must_exist=True,
    )
    work_front = _scoped_path(
        config,
        _required(payload, "work_front"),
        label="work_front",
    )
    origin = _scoped_path(
        config,
        _required(payload, "origin_handoff_manifest"),
        label="origin_handoff_manifest",
    )
    handoff = _scoped_path(
        config,
        _required(payload, "handoff_result"),
        label="handoff_result",
    )
    output = _runtime_path(
        config,
        _required(payload, "output"),
        label="promotion_preview_output",
        must_exist=False,
    )
    try:
        return write_promotion_preview(
            output_path=output,
            root=config.canonical_root,
            candidate_root=candidate,
            sealed_result_path=sealed,
            work_front_path=work_front,
            origin_handoff_manifest_path=origin,
            handoff_result_path=handoff,
            expected_profile_ref=_required(payload, "expected_profile_ref"),
            expected_procedure_id=_required(payload, "expected_procedure_id"),
            operator_review=_bool(payload, "operator_review"),
        )
    except PromotionSurfaceError as exc:
        raise ConsoleApiError(str(exc)) from exc


def dispatch_action(
    *,
    config: ConsoleConfig,
    action: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if action in FORBIDDEN_ACTIONS:
        raise ConsoleApiError(f"action forbidden by MINI-6 boundary: {action}")
    if action not in ALLOWED_ACTIONS:
        raise ConsoleApiError(f"unknown console action: {action}")

    if action == "terminal_plan":
        result = _action_terminal(
            config=config,
            payload=payload,
            execute=False,
        )
    elif action == "terminal_run":
        result = _action_terminal(
            config=config,
            payload=payload,
            execute=True,
        )
    elif action == "sandbox_create":
        result = _action_sandbox_create(config, payload)
    elif action == "sandbox_status":
        result = _action_sandbox_status(config, payload)
    elif action == "checkpoint":
        result = _action_checkpoint(config, payload)
    elif action == "seal":
        result = _action_seal(config, payload)
    else:
        result = _action_promotion_preview(config, payload)

    return {
        "schema_version": "forprint_oc01_console_action_response_v0_1",
        "ok": True,
        "action": action,
        "result": result,
        "authority": {
            "console_is_state_authority": False,
            "promotion_apply_exposed": False,
            "commit_exposed": False,
            "push_exposed": False,
            "merge_exposed": False,
            "release_exposed": False,
        },
    }


def _query_value(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if not values:
        return None
    value = values[-1].strip()
    return value or None


def make_handler(config: ConsoleConfig) -> type[BaseHTTPRequestHandler]:
    class ConsoleHandler(BaseHTTPRequestHandler):
        server_version = "ForPrintOC01Mini6/0.1"

        def _json(self, status: int, payload: Mapping[str, Any]) -> None:
            raw = json.dumps(
                dict(payload),
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def _html(self, html: str) -> None:
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def _error(self, exc: Exception) -> None:
            self._json(
                400,
                {
                    "schema_version": SCHEMA_VERSION,
                    "ok": False,
                    "error": str(exc),
                    "authority": {
                        "console_is_state_authority": False,
                    },
                },
            )

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/":
                    self._html(render_console_html())
                    return
                if parsed.path == "/api/health":
                    self._json(
                        200,
                        {
                            "schema_version": SCHEMA_VERSION,
                            "ok": True,
                            "state": "READY",
                            "console_is_state_authority": False,
                            "promotion_apply_exposed": False,
                            "commit_push_merge_release_exposed": False,
                        },
                    )
                    return
                if parsed.path == "/api/snapshot":
                    query = parse_qs(parsed.query, keep_blank_values=False)
                    inputs = {
                        key: value
                        for key in (
                            "session_projection",
                            "sandbox_manifest",
                            "result_manifest",
                            "promotion_preview",
                        )
                        if (
                            value := _query_value(query, key)
                        ) is not None
                    }
                    self._json(
                        200,
                        build_snapshot(config=config, inputs=inputs),
                    )
                    return
                self._json(404, {"ok": False, "error": "not found"})
            except Exception as exc:
                self._error(exc)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            prefix = "/api/action/"
            if not parsed.path.startswith(prefix):
                self._json(404, {"ok": False, "error": "not found"})
                return
            action = parsed.path[len(prefix):].strip("/")
            try:
                raw_length = self.headers.get("Content-Length", "0")
                length = int(raw_length)
                if length <= 0 or length > MAX_BODY_BYTES:
                    raise ConsoleApiError(
                        "request body must be between 1 byte and 1 MiB"
                    )
                raw = self.rfile.read(length)
                payload = json.loads(raw.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ConsoleApiError("JSON request body must be an object")
                self._json(
                    200,
                    dispatch_action(
                        config=config,
                        action=action,
                        payload=payload,
                    ),
                )
            except Exception as exc:
                self._error(exc)

        def log_message(self, fmt: str, *args: Any) -> None:
            return

    return ConsoleHandler


def serve(
    *,
    config: ConsoleConfig,
    host: str,
    port: int,
    allow_remote_bind: bool,
) -> None:
    validate_bind_policy(
        host=host,
        allow_remote_bind=allow_remote_bind,
    )
    if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
        raise ConsoleApiError("port must be an integer between 1 and 65535")

    server = ThreadingHTTPServer(
        (host, port),
        make_handler(config),
    )
    print("OC01_CONSOLE_SERVER=READY", flush=True)
    print(f"HOST={host}", flush=True)
    print(f"PORT={server.server_address[1]}", flush=True)
    print("STATE_AUTHORITY=false", flush=True)
    print("AUTHENTICATION_PROVIDED=false", flush=True)
    print("TLS_PROVIDED=false", flush=True)
    print(
        "REMOTE_ACCESS_REQUIRES_EXTERNAL_TRUSTED_TRANSPORT=true",
        flush=True,
    )
    server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OC-01 MINI-6 minimum Operator Console HTTP/JSON surface"
    )
    parser.add_argument("--canonical-root", default=".")
    parser.add_argument(
        "--runtime-root",
        default="/tmp/forprint-oc01/operator_console",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("--session-projection")
    snapshot.add_argument("--sandbox-manifest")
    snapshot.add_argument("--result-manifest")
    snapshot.add_argument("--promotion-preview")

    server = sub.add_parser("serve")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8099)
    server.add_argument("--allow-remote-bind", action="store_true")

    args = parser.parse_args()
    config = ConsoleConfig.build(
        canonical_root=args.canonical_root,
        runtime_root=args.runtime_root,
    )

    if args.command == "snapshot":
        inputs = {
            key: value
            for key, value in {
                "session_projection": args.session_projection,
                "sandbox_manifest": args.sandbox_manifest,
                "result_manifest": args.result_manifest,
                "promotion_preview": args.promotion_preview,
            }.items()
            if value
        }
        print(
            json.dumps(
                build_snapshot(config=config, inputs=inputs),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    serve(
        config=config,
        host=args.host,
        port=args.port,
        allow_remote_bind=args.allow_remote_bind,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
