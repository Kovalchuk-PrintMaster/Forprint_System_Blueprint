from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.worker_runtime.bootstrap_profile import (
    BootstrapRuntimeError,
    resolve_bootstrap_runtime,
)


def _fixture(tmp_path: Path):
    root = tmp_path / "blueprint"
    module = tmp_path / "module"
    root.mkdir()
    module.mkdir()
    profile = root / (
        "coordination/standards/automation/control_plane/bootstrap_worker_runtime_profile_v0_1.yaml"
    )
    profile.parent.mkdir(parents=True)
    profile.write_text(
        yaml.safe_dump(
            {
                "schema_version": "forprint_bootstrap_worker_runtime_profile_v0_1",
                "status": "active_standard",
                "authority": "forprint_system_blueprint",
                "execution_class": "MODULE_BOOTSTRAP",
                "scope": {
                    "bootstrap_only": True,
                    "roadmap_development_allowed": False,
                },
                "worker_adapter": {
                    "mode": "provider_neutral_console",
                    "canonical_builder": "scripts/coordination/build_worker_invocation.py",
                    "starts_process": False,
                },
                "provider_binding": {
                    "mode": "operator_or_dispatch_time",
                    "provider_in_git": False,
                    "model_in_git": False,
                    "secret_in_git": False,
                },
                "dispatch_requirements": ["operator approval"],
                "limits": {"write_scope": "module_repository_only"},
                "authority_semantics": {
                    "profile_is_execution_authority": False,
                    "profile_is_operator_approval": False,
                    "automatic_accept": False,
                    "automatic_next_prompt_release": False,
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    adapter = root / "scripts/coordination/build_worker_invocation.py"
    adapter.parent.mkdir(parents=True)
    adapter.write_text("# adapter\n", encoding="utf-8")
    return root, module


def test_blueprint_fallback_when_module_profile_missing(tmp_path: Path) -> None:
    root, module = _fixture(tmp_path)
    result = resolve_bootstrap_runtime(
        blueprint_root=root,
        module_root=module,
        execution_class="MODULE_BOOTSTRAP",
    )
    assert result["source"] == "BLUEPRINT_BOOTSTRAP_RUNTIME_PROFILE"
    assert result["blueprint_fallback_used"] is True
    assert result["worker_process_started"] is False


def test_module_profile_wins(tmp_path: Path) -> None:
    root, module = _fixture(tmp_path)
    profile = module / "config/worker_runtime.yaml"
    profile.parent.mkdir()
    profile.write_text("schema_version: module\n", encoding="utf-8")
    result = resolve_bootstrap_runtime(
        blueprint_root=root,
        module_root=module,
        execution_class="MODULE_BOOTSTRAP",
    )
    assert result["source"] == "MODULE_OWNED_RUNTIME_PROFILE"
    assert result["blueprint_fallback_used"] is False


def test_fallback_rejects_roadmap_development(tmp_path: Path) -> None:
    root, module = _fixture(tmp_path)
    with pytest.raises(BootstrapRuntimeError):
        resolve_bootstrap_runtime(
            blueprint_root=root,
            module_root=module,
            execution_class="ROADMAP_DEVELOPMENT",
        )


def test_missing_adapter_fails_closed(tmp_path: Path) -> None:
    root, module = _fixture(tmp_path)
    (root / "scripts/coordination/build_worker_invocation.py").unlink()
    with pytest.raises(BootstrapRuntimeError):
        resolve_bootstrap_runtime(
            blueprint_root=root,
            module_root=module,
            execution_class="MODULE_BOOTSTRAP",
        )
