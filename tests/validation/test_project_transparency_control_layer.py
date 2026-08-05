from __future__ import annotations

import copy
import importlib.util
import shutil
import sys
from pathlib import Path

import yaml

from scripts.run_blueprint_checks import build_checks

ROOT = Path(__file__).resolve().parents[2]
RENDERER_PATH = (
    ROOT
    / "scripts"
    / "coordination"
    / "render_blueprint_governance_status.py"
)
VALIDATOR_PATH = (
    ROOT
    / "scripts"
    / "validation"
    / "validate_project_transparency_control_layer.py"
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


renderer = load_module(
    RENDERER_PATH,
    "render_blueprint_governance_status_for_tests",
)
validator = load_module(
    VALIDATOR_PATH,
    "validate_project_transparency_control_layer_for_tests",
)


def repository_state() -> dict:
    return {
        "branch": (
            "governance/module-workflow-command-architecture-v01"
        ),
        "head": "9caf51155b98fb515c6aa663e2991a61a7dea4cd",
        "tracked_worktree_clean": True,
        "tracked_changes": [],
    }


def fixture(tmp_path: Path) -> Path:
    root = tmp_path / "blueprint"
    for relative in renderer.SOURCE_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return root


def write_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def test_current_manifest_is_agreed_and_fail_closed_boundaries_hold() -> None:
    manifest = renderer.build_manifest(ROOT)

    assert manifest["source_consistency"]["state"] == "agreed"
    assert manifest["authorization_evidence"] == {
        "reference_pilot_authorized": False,
        "external_prompts_released": False,
        "external_rollout": "gated",
        "release_policy_global_enabled": False,
        "authorized_modules": [],
        "release_authorization_evidence": None,
    }
    assert len(
        manifest["coordination_control_state"][
            "ten_step_forward_plan"
        ]
    ) == 10
    assert manifest["projection"]["independent_authority"] is False


def test_blocker_disagreement_fails_closed(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    path = root / renderer.READINESS_CLOSEOUT
    data = renderer.load_yaml(path)
    mutated = copy.deepcopy(data)
    mutated["remaining_readiness_blockers"] = []
    write_yaml(path, mutated)

    manifest = renderer.build_manifest(
        root,
        repository_state=repository_state(),
    )

    assert manifest["source_consistency"]["state"] == "failed"
    assert manifest["result"] == (
        "PROJECT_TRANSPARENCY_CURRENT_STATE_FAILED_CLOSED"
    )
    assert any(
        row["check_id"] == "active_blocker_agreement"
        for row in manifest["source_consistency"]["disagreements"]
    )


def test_release_enablement_fails_closed(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    path = root / renderer.RELEASE_POLICY
    data = renderer.load_yaml(path)
    mutated = copy.deepcopy(data)
    mutated["release"]["global_enabled"] = True
    write_yaml(path, mutated)

    manifest = renderer.build_manifest(
        root,
        repository_state=repository_state(),
    )

    assert manifest["source_consistency"]["state"] == "failed"
    assert any(
        row["check_id"] == "external_prompt_release_boundary"
        for row in manifest["source_consistency"]["disagreements"]
    )


def test_status_renderer_separates_governance_and_coordination() -> None:
    rendered = renderer.render_status(
        renderer.build_manifest(ROOT)
    )

    assert "Observed governance decision state" in rendered
    assert "Coordination control state" in rendered
    assert (
        "reference_pilot_migration_authorization_decision"
        in rendered
    )
    assert (
        "define_reference_pilot_authorization_criteria"
        in rendered
    )
    assert "reference pilot authorized: false" in rendered


def test_validator_accepts_current_control_layer() -> None:
    assert validator.validate(ROOT, RENDERER_PATH) == []


def test_canonical_catalog_contains_transparency_validator() -> None:
    checks = build_checks()
    check_ids = [item.check_id for item in checks]

    assert len(check_ids) == len(set(check_ids))

    check = {
        item.check_id: item
        for item in checks
    }["project_transparency_control_layer_validation"]

    assert check.title == "Project transparency control layer"
    assert check.group == "documentation"
    assert check.command[-1] == (
        "scripts/validation/"
        "validate_project_transparency_control_layer.py"
    )
    assert check_ids.index(
        "blueprint_command_applicability_validation"
    ) < check_ids.index(
        "project_transparency_control_layer_validation"
    ) < check_ids.index(
        "module_standards_template_validation"
    )
