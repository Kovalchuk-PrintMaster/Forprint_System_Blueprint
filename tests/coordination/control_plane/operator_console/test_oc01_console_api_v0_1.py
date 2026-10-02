from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.operator_console.console_api import (
    ALLOWED_ACTIONS,
    FORBIDDEN_ACTIONS,
    ConsoleApiError,
    ConsoleConfig,
    build_snapshot,
    dispatch_action,
    validate_bind_policy,
)
from scripts.coordination.control_plane.operator_console.session_projection import (
    SCHEMA_VERSION as SESSION_SCHEMA,
)


def git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    return cp.stdout.strip()


def fixture(tmp_path: Path) -> tuple[ConsoleConfig, Path]:
    canonical = tmp_path / "canonical"
    runtime = tmp_path / "runtime"
    canonical.mkdir()
    git(canonical, "init", "-q")
    git(canonical, "config", "user.email", "oc01@example.invalid")
    git(canonical, "config", "user.name", "OC01 Test")
    (canonical / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(canonical, "add", "tracked.txt")
    git(canonical, "commit", "-q", "-m", "baseline")
    return (
        ConsoleConfig.build(
            canonical_root=canonical,
            runtime_root=runtime,
        ),
        canonical.resolve(),
    )


def session_file(config: ConsoleConfig) -> Path:
    value = {
        "schema_version": SESSION_SCHEMA,
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
        "actor": {
            "actor_type": "human_terminal",
            "actor_id": "human-test",
            "authority_conferred": False,
        },
    }
    path = config.runtime_root / "session.yaml"
    path.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_snapshot_is_non_authoritative_and_lists_only_bounded_actions(
    tmp_path: Path,
) -> None:
    config, _ = fixture(tmp_path)
    snapshot = build_snapshot(config=config)

    assert snapshot["projection_role"] == "NON_AUTHORITATIVE_OPERATOR_VIEW"
    assert all(value is False for value in snapshot["authority"].values())
    assert set(snapshot["actions"]["allowed"]) == ALLOWED_ACTIONS
    assert set(snapshot["actions"]["forbidden"]) == FORBIDDEN_ACTIONS
    assert "promotion_apply" not in snapshot["actions"]["allowed"]
    assert snapshot["transport"]["authentication_provided"] is False


def test_terminal_plan_delegates_to_existing_gateway(tmp_path: Path) -> None:
    config, canonical = fixture(tmp_path)
    session = session_file(config)

    response = dispatch_action(
        config=config,
        action="terminal_plan",
        payload={
            "session_projection": str(session),
            "capability_id": "repo_head",
            "enabled": True,
        },
    )

    plan = response["result"]
    assert plan["capability"]["capability_id"] == "repo_head"
    assert plan["capability"]["exact_scope"] == str(canonical)
    assert plan["execution"]["shell"] is False
    assert plan["authority"]["commit_allowed"] is False
    assert response["authority"]["promotion_apply_exposed"] is False


def test_terminal_run_requires_explicit_confirm(tmp_path: Path) -> None:
    config, _ = fixture(tmp_path)
    session = session_file(config)

    with pytest.raises(ConsoleApiError, match="confirm=true"):
        dispatch_action(
            config=config,
            action="terminal_run",
            payload={
                "session_projection": str(session),
                "capability_id": "repo_status",
                "enabled": True,
            },
        )


def test_forbidden_promotion_apply_and_git_actions_fail_closed(
    tmp_path: Path,
) -> None:
    config, _ = fixture(tmp_path)
    for action in ("promotion_apply", "commit", "push", "merge", "release"):
        with pytest.raises(ConsoleApiError, match="forbidden"):
            dispatch_action(
                config=config,
                action=action,
                payload={},
            )


def test_file_scope_rejects_arbitrary_host_path(tmp_path: Path) -> None:
    config, _ = fixture(tmp_path)
    outside = tmp_path / "outside.yaml"
    outside.write_text(
        yaml.safe_dump(
            {
                "schema_version": SESSION_SCHEMA,
                "authority": {"state_authority": False},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConsoleApiError, match="outside configured"):
        build_snapshot(
            config=config,
            inputs={"session_projection": str(outside)},
        )


def test_bind_policy_is_loopback_by_default() -> None:
    validate_bind_policy(host="127.0.0.1", allow_remote_bind=False)
    validate_bind_policy(host="::1", allow_remote_bind=False)
    with pytest.raises(ConsoleApiError, match="allow-remote-bind"):
        validate_bind_policy(host="0.0.0.0", allow_remote_bind=False)
    validate_bind_policy(host="0.0.0.0", allow_remote_bind=True)
