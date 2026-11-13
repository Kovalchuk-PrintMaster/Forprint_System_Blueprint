from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.context.bootstrap_task_context import (
    BootstrapContextError,
    build_bootstrap_task_context,
)

PROMPT_ID = "bootstrap_prompt_v0_1"


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _repo(path: Path) -> Path:
    path.mkdir()
    _git(path, "init")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    (path / "README.md").write_text("baseline\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-m", "baseline")
    return path


def _write_yaml(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _fixture(tmp_path: Path):
    root = _repo(tmp_path / "blueprint")
    module = _repo(tmp_path / "module")
    module_id = "sample_module"

    prompt = root / "prompt.md"
    prompt.write_text("# bootstrap\n", encoding="utf-8")
    oracle = _write_yaml(root / "oracle.yaml", {"schema_version": "oracle"})
    contract = _write_yaml(
        root / "contract.yaml",
        {"schema_version": "contract"},
    )
    policy = _write_yaml(
        root / "policy.yaml",
        {
            "execution_classes": {"MODULE_BOOTSTRAP": {"requires_stage_0_local_hygiene": True}},
            "stage_0_module_local_hygiene": {
                "owner": "MODULE_ASSISTANT",
                "steps": ["inspect repository", "commit and push own module"],
                "module_local_commit_allowed": True,
                "module_local_push_allowed": True,
                "forbidden": ["force push"],
            },
        },
    )
    release = _write_yaml(
        root / "release.yaml",
        {
            "authorization": {
                "module": module_id,
                "prompt_id": PROMPT_ID,
                "explicit_user_execution_required": True,
            },
            "authority_basis": {
                "prompt_contract": "contract.yaml",
                "prompt_contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
                "acceptance_oracle": "oracle.yaml",
                "acceptance_oracle_sha256": hashlib.sha256(oracle.read_bytes()).hexdigest(),
            },
        },
    )
    return root, module, module_id, prompt, contract, release, oracle, policy


def _build(fixture):
    root, module, module_id, prompt, contract, release, oracle, policy = fixture
    return build_bootstrap_task_context(
        blueprint_root=root,
        module_root=module,
        module_id=module_id,
        prompt_id=PROMPT_ID,
        prompt_path=prompt,
        prompt_contract_path=contract,
        release_authorization_path=release,
        acceptance_oracle_path=oracle,
        stage_0_policy_path=policy,
    )


def test_missing_self_knowledge_and_runtime_are_bootstrap_debt(tmp_path: Path) -> None:
    envelope = _build(_fixture(tmp_path))
    codes = {row["code"] for row in envelope["bootstrap_debt"]}
    assert "FRESH_CONTEXT_MISSING" in codes
    assert "MODULE_MEMORY_INCOMPLETE" in codes
    assert "MODULE_RUNTIME_PROFILE_MISSING" in codes
    assert envelope["state"] == "BOOTSTRAP_READY"
    assert envelope["strict_development_context_ready"] is False
    assert envelope["execution_boundaries"]["roadmap_development_allowed_before_stage_0"] is False


def test_dirty_worktree_is_reported_but_does_not_block_bootstrap(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    module = fixture[1]
    (module / "local.txt").write_text("intentional local prep\n", encoding="utf-8")
    envelope = _build(fixture)
    codes = {row["code"] for row in envelope["bootstrap_debt"]}
    assert "LOCAL_WORKTREE_DIRTY" in codes
    assert envelope["state"] == "BOOTSTRAP_READY"
    assert envelope["stage_0"]["required"] is True


def test_stale_fresh_context_is_bootstrap_debt(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    module = fixture[1]
    for rel in (
        "coordination/module_memory/module_memory.yaml",
        "coordination/module_memory/inventory_index.yaml",
        "coordination/module_memory/implementation_lineage.yaml",
        "coordination/module_memory/document_authority.yaml",
        "coordination/module_memory/roadmap_state.yaml",
    ):
        _write_yaml(module / rel, {"schema_version": "x"})
    _write_yaml(
        module / "coordination/module_memory/fresh_context_manifest.yaml",
        {"repository": {"head": "0" * 40}},
    )
    envelope = _build(fixture)
    codes = {row["code"] for row in envelope["bootstrap_debt"]}
    assert "FRESH_CONTEXT_STALE" in codes
    assert envelope["state"] == "BOOTSTRAP_READY"


def test_release_authorization_mismatch_fails_closed(tmp_path: Path) -> None:
    fixture = list(_fixture(tmp_path))
    release = fixture[5]
    data = yaml.safe_load(release.read_text(encoding="utf-8"))
    data["authorization"]["prompt_id"] = "wrong"
    _write_yaml(release, data)
    fixture[5] = release
    with pytest.raises(BootstrapContextError):
        _build(tuple(fixture))


def test_bootstrap_mode_never_grants_roadmap_development(tmp_path: Path) -> None:
    envelope = _build(_fixture(tmp_path))
    assert envelope["execution_class"] == "MODULE_BOOTSTRAP"
    assert envelope["execution_boundaries"]["roadmap_development_allowed_before_stage_0"] is False
    assert envelope["canonical_task_context_compiler"]["strict_mode_preserved"] is True
    assert (
        envelope["canonical_task_context_compiler"]["strict_task_context_required_after_stage_0"]
        is True
    )
