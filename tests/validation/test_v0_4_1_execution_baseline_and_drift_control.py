from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts/coordination/validate_prompt_contract_v0_4.py"
PREFLIGHT_PATH = ROOT / "scripts/coordination/execution_preflight_v0_1.py"
TEMPLATE = ROOT / "coordination/templates/module_prompt_contract_v0_4.example.yaml"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_policy() -> dict:
    return {
        "schema_version": "module_execution_baseline_policy_v0_1",
        "release_baseline": {
            "blueprint_commit": "a" * 40,
            "module_commit": "b" * 40,
            "module_branch": "main",
            "release_authority": {
                "path": "coordination/releases/current.yaml",
                "sha256": "c" * 64,
                "hardening_release": "v0.4.1",
            },
        },
        "required_inputs": [
            {
                "input_id": "current_release_policy",
                "repository": "blueprint",
                "path": "coordination/releases/current.yaml",
                "sha256": "d" * 64,
                "material": True,
            }
        ],
        "compatibility": {
            "allow_blueprint_forward_descendant": True,
            "allow_module_forward_descendant": True,
            "material_inputs_must_match": True,
            "require_clean_module_worktree": True,
            "require_module_upstream_synced": True,
        },
    }


def test_prompt_contract_template_declares_b1_extension() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    for token in (
        "execution_baseline_policy:",
        "schema_version: module_execution_baseline_policy_v0_1",
        "release_baseline:",
        "required_inputs:",
        "allow_blueprint_forward_descendant: true",
        "allow_module_forward_descendant: true",
        "material_inputs_must_match: true",
        "require_clean_module_worktree: true",
        "require_module_upstream_synced: true",
    ):
        assert token in text


def test_historical_contracts_remain_backward_compatible() -> None:
    validator = load_module(VALIDATOR_PATH, "b1_validator")
    errors: list[str] = []
    validator._validate_b1_execution_baseline_policy({}, errors)
    assert errors == []

    historical_contract = (
        ROOT
        / "coordination/prompt_contracts/forprint_system_blueprint/"
        "blueprint_v0_4_immutable_prompt_contract_v0_1/"
        "blueprint_v0_4_immutable_prompt_contract_v0_1__contract_v0_1.yaml"
    )
    report = validator.validate_contract(ROOT, historical_contract)
    assert report["result"] == "PASSED"
    assert set(report["summary"]) == {
        "source_obligations",
        "implementation_obligations",
        "verification_obligations",
        "completion_evidence_obligations",
        "fidelity_mappings",
    }


def test_b1_policy_accepts_valid_material_manifest() -> None:
    validator = load_module(VALIDATOR_PATH, "b1_validator_valid")
    errors: list[str] = []
    validator._validate_b1_execution_baseline_policy(
        {"execution_baseline_policy": valid_policy()},
        errors,
    )
    assert errors == []


def test_b1_policy_rejects_invalid_manifest() -> None:
    validator = load_module(VALIDATOR_PATH, "b1_validator_bad")
    policy = valid_policy()
    policy["required_inputs"][0]["material"] = False
    policy["required_inputs"].append(
        {
            "input_id": "current_release_policy",
            "repository": "other",
            "path": "../escape",
            "sha256": "bad",
            "material": True,
        }
    )
    errors: list[str] = []
    validator._validate_b1_execution_baseline_policy(
        {"execution_baseline_policy": policy},
        errors,
    )
    joined = "\n".join(errors)
    assert ".material must be true" in joined
    assert ".input_id duplicate" in joined
    assert ".repository must be blueprint or module" in joined
    assert ".path must be a safe repository-relative path" in joined
    assert ".sha256 must be a 64-character lowercase sha256" in joined


def test_blueprint_classification() -> None:
    preflight = load_module(PREFLIGHT_PATH, "b1_preflight_blueprint")
    common = {
        "baseline_commit": "a" * 40,
        "forward_allowed": True,
        "ancestor_ok": True,
        "release_compatible": True,
        "missing_required_input": False,
        "material_drift": False,
    }
    assert preflight.classify_blueprint(
        current_head="a" * 40,
        **common,
    ) == "READY_EXACT"
    assert preflight.classify_blueprint(
        current_head="b" * 40,
        **common,
    ) == "READY_FORWARD_COMPATIBLE"
    assert preflight.classify_blueprint(
        current_head="b" * 40,
        **{**common, "missing_required_input": True},
    ) == "BLOCKED_REQUIRED_INPUT_MISSING"
    assert preflight.classify_blueprint(
        current_head="b" * 40,
        **{**common, "release_compatible": False},
    ) == "BLOCKED_BREAKING_RELEASE_CHANGE"
    assert preflight.classify_blueprint(
        current_head="b" * 40,
        **{**common, "material_drift": True},
    ) == "BLOCKED_BLUEPRINT_MATERIAL_DRIFT"
    assert preflight.classify_blueprint(
        current_head="b" * 40,
        **common,
        prompt_superseded=True,
    ) == "BLOCKED_PROMPT_SUPERSEDED"


def test_module_classification() -> None:
    preflight = load_module(PREFLIGHT_PATH, "b1_preflight_module")
    base = {
        "branch": "main",
        "dirty": False,
        "upstream": "c" * 40,
        "divergence": [0, 0],
    }
    kwargs = {
        "baseline_commit": "a" * 40,
        "baseline_branch": "main",
        "forward_allowed": True,
        "clean_required": True,
        "synced_required": True,
        "ancestor_ok": True,
    }
    assert preflight.classify_module(
        current={**base, "head": "a" * 40},
        **kwargs,
    ) == "MODULE_EXACT"
    assert preflight.classify_module(
        current={**base, "head": "b" * 40},
        **kwargs,
    ) == "MODULE_FORWARD_COMPATIBLE"
    assert preflight.classify_module(
        current={**base, "head": "a" * 40, "dirty": True},
        **kwargs,
    ) == "BLOCKED_MODULE_DIRTY"
    assert preflight.classify_module(
        current={**base, "head": "a" * 40, "branch": "other"},
        **kwargs,
    ) == "BLOCKED_MODULE_BRANCH_MISMATCH"
    assert preflight.classify_module(
        current={**base, "head": "a" * 40, "divergence": [1, 0]},
        **kwargs,
    ) == "BLOCKED_MODULE_DIVERGED"


def test_revalidation_and_boundaries() -> None:
    preflight = load_module(PREFLIGHT_PATH, "b1_preflight_revalidation")
    assert preflight.combine_status(
        blueprint_status="READY_FORWARD_COMPATIBLE",
        module_status="MODULE_FORWARD_COMPATIBLE",
        previous_fingerprint="a" * 64,
        current_fingerprint="b" * 64,
    ) == "READY_CURRENT_REVALIDATED"

    source = PREFLIGHT_PATH.read_text(encoding="utf-8")
    for token in (
        '"claim_must_bind_preflight_fingerprint": True',
        '"head_chasing_after_claim_allowed": False',
        '"blueprint_repository_writes": False',
        '"module_repository_writes": False',
        '"operator_decision_created": False',
        '"automatic_acceptance": False',
        '"automatic_commit": False',
        '"automatic_push": False',
    ):
        assert token in source

def _write_binding_fixture(
    tmp_path: Path,
    *,
    queue_status: str = "ready_for_module_pull",
) -> tuple[Path, Path, str, str]:
    blueprint_root = tmp_path / "blueprint"
    module_root = tmp_path / "module_repo"
    module_root.mkdir(parents=True)

    registry_path = (
        blueprint_root
        / "coordination/registry/coordination_source_registry_v0_1.yaml"
    )
    queue_path = (
        blueprint_root
        / "coordination/prompt_queues/demo_module.yaml"
    )
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    module_id = "demo_module"
    prompt_id = "demo_prompt_v0_1"

    registry = {
        "modules": [
            {
                "module_id": module_id,
                "boundaries": {
                    "blueprint_lookup_mode": "read_only",
                    "blueprint_may_write_repository": False,
                },
                "repository": {
                    "local_path": str(module_root.resolve()),
                },
                "sources": {
                    "prompt_queue": {
                        "owner": "forprint_system_blueprint",
                        "availability": "present",
                        "path": "coordination/prompt_queues/demo_module.yaml",
                    }
                },
            }
        ]
    }
    queue = {
        "schema_version": "prompt_queue_v0_2",
        "module": module_id,
        "prompt_queue": [
            {
                "prompt_id": prompt_id,
                "target_module": module_id,
                "module_execution": {
                    "status": queue_status,
                },
            }
        ],
    }

    registry_path.write_text(
        yaml.safe_dump(registry, sort_keys=False),
        encoding="utf-8",
    )
    queue_path.write_text(
        yaml.safe_dump(queue, sort_keys=False),
        encoding="utf-8",
    )
    return blueprint_root, module_root, module_id, prompt_id


def test_execution_preflight_binds_module_root_to_registry_identity(
    tmp_path: Path,
) -> None:
    preflight = load_module(PREFLIGHT_PATH, "b1_preflight_binding")
    blueprint_root, module_root, module_id, prompt_id = _write_binding_fixture(
        tmp_path
    )

    binding = preflight.resolve_coordination_binding(
        blueprint_root=blueprint_root,
        module_root=module_root,
        module_id=module_id,
        prompt_id=prompt_id,
    )
    assert binding["registered_module_root"] == module_root.resolve()
    assert binding["queue_status"] == "ready_for_module_pull"

    wrong_root = tmp_path / "wrong_repo"
    wrong_root.mkdir()
    with pytest.raises(
        preflight.PreflightError,
        match="module_root does not match registered repository.local_path",
    ):
        preflight.resolve_coordination_binding(
            blueprint_root=blueprint_root,
            module_root=wrong_root,
            module_id=module_id,
            prompt_id=prompt_id,
        )


def test_prompt_superseded_is_derived_from_queue_status() -> None:
    preflight = load_module(PREFLIGHT_PATH, "b1_preflight_superseded")

    assert preflight.prompt_superseded_from_queue_status(
        "ready_for_module_pull"
    ) is False
    assert preflight.prompt_superseded_from_queue_status("in_progress") is False
    assert preflight.prompt_superseded_from_queue_status("blocked") is False
    assert preflight.prompt_superseded_from_queue_status("superseded") is True

    with pytest.raises(
        preflight.PreflightError,
        match="prompt queue status is not execution-eligible",
    ):
        preflight.prompt_superseded_from_queue_status("completed_by_module")


def test_evaluate_wires_queue_superseded_into_blueprint_classification() -> None:
    source = PREFLIGHT_PATH.read_text(encoding="utf-8")
    assert "binding = resolve_coordination_binding(" in source
    assert "prompt_superseded = prompt_superseded_from_queue_status(" in source
    assert "prompt_superseded=prompt_superseded" in source
    assert '"queue_status": binding["queue_status"]' in source


def test_release_authority_material_drift_helper() -> None:
    preflight = load_module(PREFLIGHT_PATH, "b1_release_authority_drift_helper")

    expected = "a" * 64
    assert (
        preflight.release_authority_material_drift(
            authority_exists=True,
            expected_sha256=expected,
            current_sha256="b" * 64,
        )
        is True
    )
    assert (
        preflight.release_authority_material_drift(
            authority_exists=True,
            expected_sha256=expected,
            current_sha256=expected,
        )
        is False
    )
    assert (
        preflight.release_authority_material_drift(
            authority_exists=False,
            expected_sha256=expected,
            current_sha256=None,
        )
        is False
    )


def test_b1_completion_correction_release_authority_and_previous_report_binding() -> None:
    preflight = load_module(PREFLIGHT_PATH, "b1_preflight_completion_correction")

    assert preflight._valid_sha256("a" * 64)
    assert not preflight._valid_sha256("A" * 64)
    assert not preflight._valid_sha256("a" * 63)

    release_baseline = {
        "blueprint_commit": "1" * 40,
        "module_commit": "2" * 40,
        "module_branch": "feature/demo",
        "release_authority": {
            "path": "coordination/releases/current.yaml",
            "sha256": "3" * 64,
            "hardening_release": "v0.4.1",
        },
        "required_inputs": [],
    }
    contract_path = Path("/tmp/demo_contract.yaml")
    fingerprint = "4" * 64

    previous = {
        "schema_version": preflight.REPORT_SCHEMA,
        "contract": {
            "contract_id": "demo_contract",
            "module_id": "demo_module",
            "prompt_id": "demo_prompt_v0_1",
            "path": str(contract_path),
        },
        "release_baseline": release_baseline,
        "preflight_fingerprint_sha256": fingerprint,
        "execution_identity": {
            "execution_epoch_id": fingerprint,
        },
        "revalidation": {
            "current_preflight_fingerprint_sha256": fingerprint,
        },
    }

    assert (
        preflight.validate_previous_preflight_report(
            previous,
            contract_id="demo_contract",
            module_id="demo_module",
            prompt_id="demo_prompt_v0_1",
            contract_path=contract_path,
            release_baseline=release_baseline,
        )
        == fingerprint
    )

    wrong_schema = dict(previous)
    wrong_schema["schema_version"] = "unrelated_report_v0_1"
    with pytest.raises(preflight.PreflightError, match="schema mismatch"):
        preflight.validate_previous_preflight_report(
            wrong_schema,
            contract_id="demo_contract",
            module_id="demo_module",
            prompt_id="demo_prompt_v0_1",
            contract_path=contract_path,
            release_baseline=release_baseline,
        )

    wrong_contract = {
        **previous,
        "contract": {
            **previous["contract"],
            "prompt_id": "other_prompt_v0_1",
        },
    }
    with pytest.raises(preflight.PreflightError, match="prompt_id mismatch"):
        preflight.validate_previous_preflight_report(
            wrong_contract,
            contract_id="demo_contract",
            module_id="demo_module",
            prompt_id="demo_prompt_v0_1",
            contract_path=contract_path,
            release_baseline=release_baseline,
        )

    wrong_release = {
        **previous,
        "release_baseline": {
            **release_baseline,
            "blueprint_commit": "9" * 40,
        },
    }
    with pytest.raises(preflight.PreflightError, match="release_baseline mismatch"):
        preflight.validate_previous_preflight_report(
            wrong_release,
            contract_id="demo_contract",
            module_id="demo_module",
            prompt_id="demo_prompt_v0_1",
            contract_path=contract_path,
            release_baseline=release_baseline,
        )

    wrong_epoch = {
        **previous,
        "execution_identity": {
            "execution_epoch_id": "5" * 64,
        },
    }
    with pytest.raises(
        preflight.PreflightError,
        match="execution_epoch_id/fingerprint mismatch",
    ):
        preflight.validate_previous_preflight_report(
            wrong_epoch,
            contract_id="demo_contract",
            module_id="demo_module",
            prompt_id="demo_prompt_v0_1",
            contract_path=contract_path,
            release_baseline=release_baseline,
        )

    wrong_revalidation = {
        **previous,
        "revalidation": {
            "current_preflight_fingerprint_sha256": "6" * 64,
        },
    }
    with pytest.raises(
        preflight.PreflightError,
        match="revalidation fingerprint mismatch",
    ):
        preflight.validate_previous_preflight_report(
            wrong_revalidation,
            contract_id="demo_contract",
            module_id="demo_module",
            prompt_id="demo_prompt_v0_1",
            contract_path=contract_path,
            release_baseline=release_baseline,
        )

    source = PREFLIGHT_PATH.read_text(encoding="utf-8")
    assert "release_authority_material_drift(" in source
    assert (
        "material_drift=material_drift or authority_material_drift"
        in source
    )
    assert '"matches_release_baseline": authority_matches_release_baseline' in source
    assert "validate_previous_preflight_report(" in source
