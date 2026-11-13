from __future__ import annotations

import hashlib
import subprocess
import zipfile
from pathlib import Path

import pytest
import yaml

from scripts.coordination.build_context_bundle import (
    build_task_context,
    write_task_context_archive,
)

PROMPT_ID = "logistics_service_authority_lineage_and_module_bootstrap_v0_1"
MODULE = "logistics_service"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_init(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    blueprint = tmp_path / "blueprint"
    module = tmp_path / "module"
    blueprint.mkdir()
    module.mkdir()

    (blueprint / "AGENTS.md").write_text("# Blueprint\n", encoding="utf-8")
    _write_yaml(
        blueprint / "coordination/releases/current.yaml",
        {
            "schema_version": "forprint_current_release_projection_v0_1",
            "metadata": {"status": "authoritative_current"},
            "release": {
                "base_release": "v0.4.0",
                "base_release_state": "CURRENT",
                "hardening_release": "v0.4.1",
                "hardening_state": "ACTIVE_CURRENT",
            },
            "legacy_compatibility": {
                "visibility": "advisory_yellow",
                "default_current_gate_behavior": "nonblocking_excluded_or_skipped",
            },
        },
    )
    _write_yaml(
        blueprint
        / "coordination/standards/governance/outgoing_prompt_release_policy_v0_1.yaml",
        {
            "release": {
                "global_enabled": False,
                "authorized_modules": [],
                "authorization_evidence": None,
            }
        },
    )
    _write_yaml(
        blueprint
        / "coordination/internal_work/blueprint/governance/"
        "2026-09-06__blueprint__control_plane_module_memory_semantic_convergence_program_v0_1.yaml",
        {"schema_version": "fixture"},
    )
    _write_yaml(
        blueprint
        / "coordination/internal_work/blueprint/governance/"
        "2026-09-06__blueprint__operator_clarified_ai_activation_and_portfolio_rollout_architecture_v0_1.yaml",
        {"schema_version": "fixture"},
    )
    _write_yaml(
        blueprint / "coordination/roadmaps/logistics_service.yaml",
        {"module": MODULE, "current": "fixture"},
    )

    approved = (
        blueprint
        / "coordination/outgoing_prompts/logistics_service/approved/"
        "2026-09-05__logistics_service_authority_lineage_and_module_bootstrap_v0_1.md"
    )
    approved.parent.mkdir(parents=True, exist_ok=True)
    approved.write_text(
        """# Prompt

# ForPrint machine prompt

```yaml
prompt_id: logistics_service_authority_lineage_and_module_bootstrap_v0_1
acceptance_handoff:
  acceptance_oracle_path: coordination/acceptance_oracles/logistics_service/oracle.yaml
```
""",
        encoding="utf-8",
    )
    contract = (
        blueprint
        / "coordination/prompt_contracts/logistics_service/"
        "logistics_service_authority_lineage_and_module_bootstrap_v0_1/contract.yaml"
    )
    _write_yaml(contract, {"prompt_id": PROMPT_ID})
    _write_yaml(
        blueprint / "coordination/acceptance_oracles/logistics_service/oracle.yaml",
        {"prompt_id": PROMPT_ID},
    )
    _write_yaml(
        blueprint / "coordination/outgoing_prompts/logistics_service/index.yaml",
        {
            "schema_version": "prompt_queue_v0_2",
            "module": MODULE,
            "prompt_queue": [
                {
                    "prompt_id": "previous",
                    "sequence": 5,
                    "target_module": MODULE,
                    "file": "completed/previous.md",
                    "module_execution": {
                        "status": "completed_by_module",
                        "completion_report": None,
                    },
                },
                {
                    "prompt_id": PROMPT_ID,
                    "sequence": 6,
                    "target_module": MODULE,
                    "file": (
                        "approved/"
                        "2026-09-05__logistics_service_authority_lineage_and_module_bootstrap_v0_1.md"
                    ),
                    "prompt_contract": {
                        "path": (
                            "coordination/prompt_contracts/logistics_service/"
                            "logistics_service_authority_lineage_and_module_bootstrap_v0_1/"
                            "contract.yaml"
                        ),
                        "file_sha256": _sha(contract),
                    },
                    "module_execution": {"status": "ready_for_module_pull"},
                },
            ],
        },
    )

    module_files = {
        "AGENTS.md": "# Logistics\n",
        "coordination/module_memory/module_memory.yaml": "schema_version: fixture\n",
        "coordination/module_memory/inventory_index.yaml": "schema_version: fixture\n",
        "coordination/module_memory/implementation_lineage.yaml": "schema_version: fixture\n",
        "coordination/module_memory/document_authority.yaml": "schema_version: fixture\n",
        "coordination/module_memory/roadmap_state.yaml": "schema_version: fixture\n",
        "coordination/module_memory/current_state.yaml": "schema_version: fixture\n",
    }
    for relative, content in module_files.items():
        path = module / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    # Additional source bound by the fresh-context manifest.
    extra = module / "scripts/validation/validate_fresh_context.py"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("# fixture\n", encoding="utf-8")

    _git_init(module)
    module_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=module,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()

    fresh_sources = []
    for relative in sorted([*module_files, "scripts/validation/validate_fresh_context.py"]):
        path = module / relative
        fresh_sources.append({"path": relative, "sha256": _sha(path)})
    _write_yaml(
        module / "coordination/module_memory/fresh_context_manifest.yaml",
        {
            "schema_version": "logistics_fresh_context_manifest_v0_1",
            "module_id": MODULE,
            "repository": {"head": module_head},
            "prompt": {"prompt_id": PROMPT_ID},
            "worker_dispatch_state": "PAUSED_BY_OPERATOR",
            "unclassified_dirty_paths": [],
            "sources": fresh_sources,
        },
    )

    # Manifest is intentionally generated after fixture commit; HEAD still matches.
    _git_init(blueprint)
    return blueprint, module


def test_task_context_compiles_from_fresh_logistics_reference(tmp_path: Path) -> None:
    blueprint, module = _fixture(tmp_path)

    result = build_task_context(
        root=blueprint,
        module=MODULE,
        prompt_id=PROMPT_ID,
        module_root=module,
    )

    assert result.manifest["schema_version"] == "forprint_task_context_manifest_v0_1"
    assert result.manifest["identity"]["module_id"] == MODULE
    assert result.manifest["identity"]["prompt_id"] == PROMPT_ID
    assert result.manifest["module_self_knowledge"]["fresh_context_state"] == "PASS"
    assert result.manifest["execution_boundaries"]["worker_dispatch_allowed"] is False
    assert result.manifest["execution_boundaries"]["prompt_claim_allowed"] is False
    module_sources = [
        item
        for item in result.manifest["source_manifest"]
        if item["origin"] == "module"
    ]
    assert len(module_sources) == 8


def test_task_context_archive_contains_manifest_bootstrap_and_sources(
    tmp_path: Path,
) -> None:
    blueprint, module = _fixture(tmp_path)
    result = build_task_context(
        root=blueprint,
        module=MODULE,
        prompt_id=PROMPT_ID,
        module_root=module,
    )

    archive = write_task_context_archive(
        result=result,
        output_dir=tmp_path / "out",
    )

    assert archive.is_file()
    with zipfile.ZipFile(archive) as payload:
        names = payload.namelist()
        assert "TASK_CONTEXT_MANIFEST.yaml" in names
        assert "BOOTSTRAP_FOR_TASK.md" in names
        assert "sources/module/AGENTS.md" in names
        assert any(
            name.endswith(
                "2026-09-05__logistics_service_authority_lineage_and_module_bootstrap_v0_1.md"
            )
            for name in names
        )


def test_task_context_fails_closed_on_fresh_source_hash_drift(tmp_path: Path) -> None:
    blueprint, module = _fixture(tmp_path)
    (module / "AGENTS.md").write_text("# drift\n", encoding="utf-8")

    with pytest.raises(ValueError, match="fresh-context source hash drift"):
        build_task_context(
            root=blueprint,
            module=MODULE,
            prompt_id=PROMPT_ID,
            module_root=module,
        )
