from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "forprint_bootstrap_worker_runtime_resolution_v0_1"
EXECUTION_CLASS = "MODULE_BOOTSTRAP"
DEFAULT_PROFILE = (
    "coordination/standards/automation/control_plane/bootstrap_worker_runtime_profile_v0_1.yaml"
)


class BootstrapRuntimeError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise BootstrapRuntimeError(f"runtime profile missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BootstrapRuntimeError("runtime profile must be a YAML mapping")
    return data


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_profile(data: dict[str, Any]) -> None:
    expected = {
        "schema_version": "forprint_bootstrap_worker_runtime_profile_v0_1",
        "status": "active_standard",
        "authority": "forprint_system_blueprint",
        "execution_class": EXECUTION_CLASS,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            raise BootstrapRuntimeError(f"runtime profile {key} mismatch")
    scope = data.get("scope")
    if not isinstance(scope, dict):
        raise BootstrapRuntimeError("runtime scope missing")
    if scope.get("bootstrap_only") is not True:
        raise BootstrapRuntimeError("bootstrap_only must be true")
    if scope.get("roadmap_development_allowed") is not False:
        raise BootstrapRuntimeError("roadmap development must remain forbidden")
    adapter = data.get("worker_adapter")
    if not isinstance(adapter, dict):
        raise BootstrapRuntimeError("worker adapter missing")
    if adapter.get("mode") != "provider_neutral_console":
        raise BootstrapRuntimeError("worker adapter mode mismatch")
    if adapter.get("canonical_builder") != "scripts/coordination/build_worker_invocation.py":
        raise BootstrapRuntimeError("canonical worker adapter mismatch")
    provider = data.get("provider_binding")
    if not isinstance(provider, dict):
        raise BootstrapRuntimeError("provider binding missing")
    if provider.get("mode") != "operator_or_dispatch_time":
        raise BootstrapRuntimeError("provider binding mode mismatch")
    for key in ("provider_in_git", "model_in_git", "secret_in_git"):
        if provider.get(key) is not False:
            raise BootstrapRuntimeError(f"{key} must be false")
    authority = data.get("authority_semantics")
    if not isinstance(authority, dict):
        raise BootstrapRuntimeError("authority semantics missing")
    for key in (
        "profile_is_execution_authority",
        "profile_is_operator_approval",
        "automatic_accept",
        "automatic_next_prompt_release",
    ):
        if authority.get(key) is not False:
            raise BootstrapRuntimeError(f"authority invariant failed: {key}")


def resolve_bootstrap_runtime(
    *,
    blueprint_root: Path,
    module_root: Path,
    execution_class: str,
) -> dict[str, Any]:
    blueprint_root = blueprint_root.resolve()
    module_root = module_root.resolve()
    if execution_class != EXECUTION_CLASS:
        raise BootstrapRuntimeError("Blueprint bootstrap runtime fallback is MODULE_BOOTSTRAP-only")

    module_profile = module_root / Path("config", "worker_runtime.yaml")
    if module_profile.is_file():
        return {
            "schema_version": SCHEMA,
            "execution_class": execution_class,
            "source": "MODULE_OWNED_RUNTIME_PROFILE",
            "module_runtime_profile": {
                "path": str(module_profile),
                "sha256": _sha(module_profile),
            },
            "blueprint_fallback_used": False,
            "worker_process_started": False,
        }

    profile_path = blueprint_root / DEFAULT_PROFILE
    profile = _load(profile_path)
    validate_profile(profile)

    adapter = blueprint_root / profile["worker_adapter"]["canonical_builder"]
    if not adapter.is_file():
        raise BootstrapRuntimeError(f"canonical worker adapter missing: {adapter}")

    return {
        "schema_version": SCHEMA,
        "execution_class": execution_class,
        "source": "BLUEPRINT_BOOTSTRAP_RUNTIME_PROFILE",
        "blueprint_runtime_profile": {
            "path": profile_path.relative_to(blueprint_root).as_posix(),
            "sha256": _sha(profile_path),
        },
        "worker_adapter": profile["worker_adapter"],
        "provider_binding": {
            "mode": profile["provider_binding"]["mode"],
            "provider_selected": False,
            "model_selected": False,
            "secret_material_present": False,
        },
        "dispatch_requirements": profile["dispatch_requirements"],
        "limits": profile["limits"],
        "blueprint_fallback_used": True,
        "worker_process_started": False,
        "operator_approval_created": False,
    }
