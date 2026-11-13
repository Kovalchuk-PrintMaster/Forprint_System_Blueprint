from pathlib import Path

import pytest

from scripts.coordination.control_plane.worker_runtime.registry import (
    RuntimeRegistryError,
    load_module_runtime_config,
    load_runtime_registry,
    resolve_default_runtime,
    resolve_provider,
)

ROOT = Path(__file__).resolve().parents[4]


def test_registry_has_one_ready_provider_and_three_reserved() -> None:
    data = load_runtime_registry(ROOT)
    rows = {row["provider_id"]: row for row in data["providers"]}

    assert rows["github_copilot_cli"]["state"] == "READY"
    assert rows["github_copilot_cli"]["ready"] is True
    assert rows["github_copilot_cli"]["executable"] == "/usr/local/bin/copilot"

    for provider_id in (
        "openai_codex_cli",
        "anthropic_claude_code",
        "xai_grok_cli",
    ):
        row = rows[provider_id]
        assert row["state"] == "NOT_CONFIGURED"
        assert row["ready"] is False
        assert row["executable"] is None
        assert row["model_selection"] is None
        assert row["auth"] is None


def test_worker_identity_is_provider_neutral() -> None:
    data = load_runtime_registry(ROOT)
    assert data["worker_identity"]["provider_neutral"] is True
    assert data["worker_identity"]["provider_selected_per_attempt"] is True


def test_default_runtime_resolves_copilot_without_authority() -> None:
    runtime = resolve_default_runtime(ROOT)
    assert runtime["provider_id"] == "github_copilot_cli"
    assert runtime["model_id"] == "auto"
    assert runtime["executable"] == "/usr/local/bin/copilot"
    assert runtime["command_representation"] == "ARGV_NO_SHELL"
    assert runtime["working_directory"] == "ATTEMPT_WORKSPACE_REPO"
    assert runtime["authority_granted"] is False


def test_not_configured_provider_fails_ready_resolution() -> None:
    with pytest.raises(RuntimeRegistryError, match="not READY"):
        resolve_provider(ROOT, "openai_codex_cli", require_ready=True)


def test_runtime_config_has_no_execution_authority() -> None:
    config = load_module_runtime_config(ROOT)
    authority = config["authority"]
    assert all(value is False for value in authority.values())
    tool_policy = config["tool_policy"]
    assert tool_policy["canonical_repository_write_allowed"] is False
    assert tool_policy["foreign_repository_write_allowed"] is False
    assert tool_policy["git_commit_allowed"] is False
    assert tool_policy["git_push_allowed"] is False
    assert tool_policy["merge_allowed"] is False
    assert tool_policy["release_allowed"] is False
    assert tool_policy["automatic_accept_allowed"] is False
