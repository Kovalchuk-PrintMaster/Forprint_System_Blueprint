from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest
import yaml

from scripts.coordination.modules.forprint_system_blueprint.workflows import (
    self_audit,
)

ROOT = Path(__file__).resolve().parents[2]
SELF_AUDIT = (
    ROOT
    / "scripts/coordination/modules/forprint_system_blueprint/"
    "workflows/self_audit.py"
)
STANDARDS_VALIDATOR = (
    ROOT / "scripts/validate_module_standards_template.py"
)
EVIDENCE = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__explicit_write_flow_recovery_"
    "contract_v0_1.yaml"
)
RELEASE_POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)

SELF_AUDIT_HASH = "2a1b565945129a299145943079ef00566f02ddb0011601fdba2e68dbb00b4fda"
STANDARDS_VALIDATOR_HASH = "c8cbbafeb7893ead903dab270e27fc2d65b0741bf09262900e6996751f52700b"


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = [func.attr]
        value = func.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))
    return ""


def test_reviewed_sources_are_exact() -> None:
    assert _sha256(SELF_AUDIT) == SELF_AUDIT_HASH
    assert _sha256(STANDARDS_VALIDATOR) == STANDARDS_VALIDATOR_HASH


def test_resume_uses_only_atomic_copy_publications() -> None:
    tree = ast.parse(
        SELF_AUDIT.read_text(encoding="utf-8"),
        filename=str(SELF_AUDIT),
    )
    resume = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "resume"
    )
    calls = [
        _call_name(node)
        for node in ast.walk(resume)
        if isinstance(node, ast.Call)
    ]

    assert calls.count("_atomic_copy2") == 3
    assert "shutil.copy2" not in calls
    assert "os.replace" not in calls


def test_atomic_copy_successfully_replaces_destination(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.txt"
    destination = tmp_path / "published/result.txt"
    source.write_text("new-content", encoding="utf-8")
    destination.parent.mkdir(parents=True)
    destination.write_text("old-content", encoding="utf-8")

    result = self_audit._atomic_copy2(source, destination)

    assert result == destination
    assert destination.read_text(encoding="utf-8") == "new-content"
    assert source.read_text(encoding="utf-8") == "new-content"
    assert not list(destination.parent.glob(".*.tmp"))


def test_atomic_copy_failure_preserves_previous_destination(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "source.txt"
    destination = tmp_path / "published/result.txt"
    source.write_text("new-content", encoding="utf-8")
    destination.parent.mkdir(parents=True)
    destination.write_text("old-content", encoding="utf-8")

    def fail_replace(source_path, destination_path):
        assert Path(destination_path) == destination
        assert Path(source_path).parent == destination.parent
        raise OSError("injected atomic publish failure")

    monkeypatch.setattr(self_audit.os, "replace", fail_replace)

    with pytest.raises(
        OSError,
        match="injected atomic publish failure",
    ):
        self_audit._atomic_copy2(source, destination)

    assert destination.read_text(encoding="utf-8") == "old-content"
    assert source.read_text(encoding="utf-8") == "new-content"
    assert not list(destination.parent.glob(".*.tmp"))


def test_standards_validator_is_temporary_workspace_only() -> None:
    text = STANDARDS_VALIDATOR.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(STANDARDS_VALIDATOR))

    temporary_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _call_name(node)
        in {
            "TemporaryDirectory",
            "tempfile.TemporaryDirectory",
        }
    ]
    assert temporary_calls

    function_names = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    assert "_write_fake_blueprint" in function_names
    assert "_validate_template_runtime" in function_names

    destructive = {
        "os.remove",
        "os.rename",
        "os.replace",
        "os.unlink",
        "shutil.move",
        "shutil.rmtree",
        "Path.rename",
        "Path.replace",
        "Path.unlink",
    }
    calls = {
        _call_name(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert calls.isdisjoint(destructive)

    string_literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    }
    assert not any(
        value.startswith(("coordination/", "machine/"))
        for value in string_literals
    )


def test_evidence_marks_zero_paths_ready_for_closeout() -> None:
    evidence = _load(EVIDENCE)

    assert evidence["metadata"]["status"] == (
        "implemented_ready_for_closeout"
    )
    assert evidence["per_flow_state"] == {
        "self_audit": "verified_explicit_recovery",
        "validate_module_standards_template": (
            "verified_temporary_isolation"
        ),
        "remaining_manual_blocker_count_after_this_evidence": 0,
    }

    state = evidence["blocker_state"]
    assert state["write_flow_recovery_not_fully_verified"] == (
        "ready_for_closeout"
    )
    assert state["closed_in_this_evidence"] is False
    assert state["closeout_eligible"] is True
    assert state["remaining_write_flow_paths"] == []


def test_operational_and_release_boundaries_remain_gated() -> None:
    evidence = _load(EVIDENCE)
    boundaries = evidence["boundaries"]

    assert boundaries["operational_readiness"] == "blocked"
    assert boundaries["reference_pilot_migration_authorized"] is False
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["external_rollout"] == "gated"
    assert boundaries["cross_repository_writes_by_builder"] is False
    assert boundaries["automatic_commit_push_or_merge"] is False
    assert boundaries["historical_evidence_rewritten"] is False

    policy = _load(RELEASE_POLICY)
    assert policy["release"]["global_enabled"] is False
    assert policy["release"]["authorized_modules"] == []
    assert policy["release"]["authorization_evidence"] is None
    assert policy["result"]["operational_state"] == "gated"
    assert policy["result"]["external_rollout"] == "gated"
