from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

from scripts.run_blueprint_checks import build_checks

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validation/validate_module_workflow_adoption_matrix.py"
MATRIX = Path("coordination/standards/adoption/module_workflow_adoption_matrix_v0_1.yaml")
DECISION = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-01__blueprint__module_workflow_command_architecture_approval_v0_1.yaml"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("matrix_validator", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def fixture(tmp_path: Path) -> Path:
    root = tmp_path / "blueprint"
    for relative in (MATRIX, DECISION):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return root


def replace_once(root: Path, old: str, new: str) -> None:
    path = root / MATRIX
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_current_matrix_passes(tmp_path: Path) -> None:
    assert validator.validate(fixture(tmp_path)) == []


def test_duplicate_yaml_key_fails(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        "  status: draft\n",
        "  status: draft\n  status: draft\n",
    )
    assert any(
        "duplicate key `status`" in item
        for item in validator.validate(root)
    )


def test_duplicate_command_id_fails(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        "  - command_id: prompt-release\n",
        "  - command_id: prompt-prepare\n",
    )
    assert any(
        "duplicate command_id `prompt-prepare`" in item
        for item in validator.validate(root)
    )


def test_read_only_write_scope_fails(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    old = """  - command_id: module-status
    owner_repository_class: module
    command_class: navigation
    mutability: read_only
    repository_write_scope: none
"""
    new = old.replace(
        "repository_write_scope: none",
        "repository_write_scope: module_only",
    )
    replace_once(root, old, new)
    issues = validator.validate(root)
    assert any(
        "`module-status.repository_write_scope` must be 'none'"
        in item
        for item in issues
    )
    assert any(
        "read-only command `module-status` has a repository write scope"
        in item
        for item in issues
    )


def test_completion_check_cannot_apply(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        "    apply_invocation_allowed: false\n",
        "    apply_invocation_allowed: true\n",
    )
    assert any(
        "`completion-packet-check.apply_invocation_allowed` must be False"
        in item
        for item in validator.validate(root)
    )


def test_idempotency_cannot_apply_live_worktree(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        "    live_worktree_apply_allowed: false\n",
        "    live_worktree_apply_allowed: true\n",
    )
    assert any(
        "`completion-packet-idempotency-check."
        "live_worktree_apply_allowed` must be False"
        in item
        for item in validator.validate(root)
    )

def test_new_module_profile_is_fixed(tmp_path: Path) -> None:
    root = fixture(tmp_path)

    old = (
        "  default_for_newly_admitted_module:\n"
        "    repository_class: module\n"
        "    assessment_status: not_assessed\n"
        "    target_conformance: unknown\n"
        "    rollout_authorized: false\n"
        "    command_profile: standard_module_workflow\n"
    )
    new = (
        "  default_for_newly_admitted_module:\n"
        "    repository_class: module\n"
        "    assessment_status: not_assessed\n"
        "    target_conformance: unknown\n"
        "    rollout_authorized: false\n"
        "    command_profile: custom_workflow\n"
    )

    replace_once(root, old, new)

    issues = validator.validate(root)

    assert any(
        "`scope_model.default_for_newly_admitted_module."
        "command_profile` must be 'standard_module_workflow'"
        in item
        for item in issues
    )

def test_rollout_stays_gated(tmp_path: Path) -> None:
    root = fixture(tmp_path)

    old = (
        "  implementation_migration: not_started\n"
        "  external_rollout: gated\n"
    )
    new = (
        "  implementation_migration: not_started\n"
        "  external_rollout: open\n"
    )

    replace_once(root, old, new)

    issues = validator.validate(root)

    assert any(
        "`governance.external_rollout` must be 'gated'"
        in item
        for item in issues
    )

def test_check_catalog_contains_validator() -> None:
    checks = {item.check_id: item for item in build_checks()}
    check = checks["module_workflow_adoption_matrix_validation"]
    assert check.title == "Workflow adoption matrix"
    assert check.group == "documentation"
    assert check.command[-1] == (
        "scripts/validation/"
        "validate_module_workflow_adoption_matrix.py"
    )
