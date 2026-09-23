"""Provider-neutral worker runtime registry for ForPrint Control Plane."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class RuntimeRegistryError(RuntimeError):
    """Raised when a worker runtime registry/config is invalid."""


@dataclass(frozen=True)
class RuntimeProvider:
    provider_id: str
    runtime_id: str
    state: str
    ready: bool
    executable: str | None
    model_selection: dict[str, Any] | None
    auth: dict[str, Any] | None


FORBIDDEN_SECRET_KEYS = {
    "api_key",
    "apikey",
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "credential",
    "credentials",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeRegistryError(f"required runtime YAML missing: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeRegistryError(f"runtime YAML must be a mapping: {path}")
    return value


def _scan_secret_values(value: Any, path: str = "") -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower()
            child = f"{path}.{key}" if path else str(key)
            if normalized in FORBIDDEN_SECRET_KEYS and item not in (
                None,
                False,
                "",
                "outside_git",
            ):
                violations.append(child)
            violations.extend(_scan_secret_values(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            violations.extend(_scan_secret_values(item, f"{path}[{index}]"))
    return violations


def load_runtime_registry(root: Path | str) -> dict[str, Any]:
    root_path = Path(root).resolve()
    data = _load_yaml(
        root_path / "coordination/registry/worker_runtime_adapters_v0_1.yaml"
    )
    providers = data.get("providers")
    if not isinstance(providers, list) or not providers:
        raise RuntimeRegistryError("runtime provider registry is empty")

    ids: list[str] = []
    ready_count = 0
    for row in providers:
        if not isinstance(row, dict):
            raise RuntimeRegistryError("runtime provider row must be a mapping")
        provider_id = row.get("provider_id")
        if not isinstance(provider_id, str) or not provider_id:
            raise RuntimeRegistryError("provider_id missing")
        ids.append(provider_id)

        state = row.get("state")
        ready = row.get("ready")
        if state == "READY":
            ready_count += 1
            if ready is not True:
                raise RuntimeRegistryError(
                    f"READY provider must have ready=true: {provider_id}"
                )
            executable = row.get("executable")
            if not isinstance(executable, str) or not executable:
                raise RuntimeRegistryError(
                    f"READY provider executable missing: {provider_id}"
                )
            if row.get("command_representation") != "ARGV_NO_SHELL":
                raise RuntimeRegistryError(
                    f"READY provider must use ARGV_NO_SHELL: {provider_id}"
                )
        elif state == "NOT_CONFIGURED":
            if ready is not False:
                raise RuntimeRegistryError(
                    f"NOT_CONFIGURED provider must have ready=false: {provider_id}"
                )
            if row.get("executable") is not None:
                raise RuntimeRegistryError(
                    f"NOT_CONFIGURED executable must be null: {provider_id}"
                )
            if row.get("model_selection") is not None:
                raise RuntimeRegistryError(
                    f"NOT_CONFIGURED model_selection must be null: {provider_id}"
                )
            if row.get("auth") is not None:
                raise RuntimeRegistryError(
                    f"NOT_CONFIGURED auth must be null: {provider_id}"
                )
        else:
            raise RuntimeRegistryError(
                f"unsupported provider state {state!r}: {provider_id}"
            )

    if len(ids) != len(set(ids)):
        raise RuntimeRegistryError("duplicate provider_id in runtime registry")
    if ready_count != 1:
        raise RuntimeRegistryError(
            f"Slice 5A requires exactly one READY provider; observed={ready_count}"
        )

    violations = _scan_secret_values(data)
    if violations:
        raise RuntimeRegistryError(
            "runtime registry contains secret-like committed values: "
            + ",".join(violations)
        )
    return data


def resolve_provider(
    root: Path | str,
    provider_id: str,
    *,
    require_ready: bool = True,
) -> RuntimeProvider:
    data = load_runtime_registry(root)
    rows = [
        row
        for row in data["providers"]
        if isinstance(row, dict) and row.get("provider_id") == provider_id
    ]
    if len(rows) != 1:
        raise RuntimeRegistryError(
            f"provider must resolve exactly once: {provider_id}"
        )
    row = rows[0]
    if require_ready and row.get("state") != "READY":
        raise RuntimeRegistryError(f"provider is not READY: {provider_id}")
    return RuntimeProvider(
        provider_id=provider_id,
        runtime_id=str(row.get("runtime_id") or provider_id),
        state=str(row.get("state")),
        ready=bool(row.get("ready")),
        executable=(
            str(row["executable"]) if row.get("executable") is not None else None
        ),
        model_selection=(
            dict(row["model_selection"])
            if isinstance(row.get("model_selection"), dict)
            else None
        ),
        auth=dict(row["auth"]) if isinstance(row.get("auth"), dict) else None,
    )


def load_module_runtime_config(root: Path | str) -> dict[str, Any]:
    root_path = Path(root).resolve()
    data = _load_yaml(root_path / "config/worker_runtime.yaml")
    if data.get("module_id") != "forprint_system_blueprint":
        raise RuntimeRegistryError("module runtime config module_id mismatch")
    if data.get("provider_adapter") != "CONSOLE_COMMAND":
        raise RuntimeRegistryError("module runtime provider_adapter mismatch")
    if data.get("working_directory") != "ATTEMPT_WORKSPACE_REPO":
        raise RuntimeRegistryError("canonical repo cannot be worker cwd")
    command = data.get("command")
    if not isinstance(command, dict):
        raise RuntimeRegistryError("runtime command mapping missing")
    if command.get("representation") != "ARGV_NO_SHELL":
        raise RuntimeRegistryError("runtime command must be ARGV_NO_SHELL")
    if command.get("shell") is not False:
        raise RuntimeRegistryError("shell execution must remain false")
    violations = _scan_secret_values(data)
    if violations:
        raise RuntimeRegistryError(
            "module runtime config contains secret-like committed values: "
            + ",".join(violations)
        )
    return data


def resolve_default_runtime(root: Path | str) -> dict[str, Any]:
    config = load_module_runtime_config(root)
    selection = config.get("provider_selection")
    if not isinstance(selection, dict):
        raise RuntimeRegistryError("provider_selection missing")
    provider_id = selection.get("configured_default_provider")
    if not isinstance(provider_id, str) or not provider_id:
        raise RuntimeRegistryError("configured_default_provider missing")
    provider = resolve_provider(root, provider_id, require_ready=True)

    command = config["command"]
    if command.get("provider_id") != provider.provider_id:
        raise RuntimeRegistryError("runtime config/registry provider mismatch")
    if command.get("executable") != provider.executable:
        raise RuntimeRegistryError("runtime config/registry executable mismatch")

    return {
        "provider_id": provider.provider_id,
        "runtime_id": provider.runtime_id,
        "model_id": selection.get("configured_default_model"),
        "executable": provider.executable,
        "command_representation": command.get("representation"),
        "working_directory": config.get("working_directory"),
        "timeout_seconds": config.get("timeout_seconds"),
        "network_policy": config.get("network_policy"),
        "budget": config.get("budget"),
        "authority_granted": False,
    }
