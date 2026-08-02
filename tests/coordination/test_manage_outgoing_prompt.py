from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from scripts.coordination import manage_outgoing_prompt as workflow

NOW = datetime(2026, 8, 2, 17, 0, tzinfo=UTC)


def _write_fixture(
    root: Path,
    *,
    authorized: bool = False,
) -> Path:
    (root / "machine").mkdir(parents=True)
    (root / "machine/modules.yaml").write_text(
        "modules:\n"
        "  - id: example_module\n"
        "    title: Example Module\n",
        encoding="utf-8",
    )

    module_dir = (
        root
        / "coordination"
        / "outgoing_prompts"
        / "example_module"
    )
    (module_dir / "drafts").mkdir(parents=True)
    (module_dir / "approved").mkdir(parents=True)
    (module_dir / "index.yaml").write_text(
        "schema_version: prompt_queue_v0_2\n"
        "module: example_module\n"
        "prompt_queue: []\n",
        encoding="utf-8",
    )

    policy_dir = (
        root / "coordination" / "standards" / "governance"
    )
    policy_dir.mkdir(parents=True)
    evidence = (
        "coordination/internal_work/blueprint/governance/"
        "test_prompt_release_authorization.yaml"
    )
    policy = {
        "schema_version": "outgoing_prompt_release_policy_v0_1",
        "release": {
            "global_enabled": False,
            "authorized_modules": (
                ["example_module"] if authorized else []
            ),
            "authorization_evidence": (
                evidence if authorized else None
            ),
        },
    }
    (policy_dir / "outgoing_prompt_release_policy_v0_1.yaml").write_text(
        yaml.safe_dump(policy, sort_keys=False),
        encoding="utf-8",
    )
    if authorized:
        evidence_path = root / evidence
        evidence_path.parent.mkdir(parents=True)
        evidence_path.write_text(
            "result: TEST_AUTHORIZATION\n",
            encoding="utf-8",
        )

    source = root / "operator_input" / "example_prompt.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        "---\n"
        "schema_version: outgoing_prompt_artifact_v0_1\n"
        "prompt_id: example_module_contract_v0_1\n"
        "target_module: example_module\n"
        "title: Example Module Contract v0.1\n"
        "phase: contract_v0_1\n"
        "priority: high\n"
        'created_at: "2026-08-02"\n'
        "source_change: governance/example-change\n"
        "lifecycle_state: draft\n"
        "lineage:\n"
        "  supersedes: null\n"
        "---\n"
        "# Prompt: Example Module Contract v0.1\n\n"
        "## Purpose\n\n"
        "Exercise the managed prompt workflow.\n",
        encoding="utf-8",
    )
    return source


def _prepared_path(root: Path) -> Path:
    return (
        root
        / "coordination"
        / "outgoing_prompts"
        / "example_module"
        / "drafts"
        / "2026-08-02__example_module_contract_v0_1.md"
    )


def _approved_path(root: Path) -> Path:
    return (
        root
        / "coordination"
        / "outgoing_prompts"
        / "example_module"
        / "approved"
        / "2026-08-02__example_module_contract_v0_1.md"
    )


def test_prepare_preview_is_read_only(tmp_path: Path) -> None:
    source = _write_fixture(tmp_path)

    result = workflow.prepare_prompt(
        root=tmp_path,
        source=source,
        apply=False,
        now=NOW,
    )

    assert result.state == "preview"
    assert not _prepared_path(tmp_path).exists()


def test_prepare_writes_non_executable_prepared_draft(
    tmp_path: Path,
) -> None:
    source = _write_fixture(tmp_path)

    result = workflow.prepare_prompt(
        root=tmp_path,
        source=source,
        apply=True,
        now=NOW,
    )

    assert result.state == "prepared"
    prepared = _prepared_path(tmp_path)
    assert prepared.exists()
    text = prepared.read_text(encoding="utf-8")
    assert "lifecycle_state: prepared" in text
    assert "prepared_from_sha256:" in text

    index = yaml.safe_load(
        (
            tmp_path
            / "coordination/outgoing_prompts/example_module/index.yaml"
        ).read_text(encoding="utf-8")
    )
    assert index["prompt_queue"] == []


def test_prepare_is_idempotent_for_identical_source(
    tmp_path: Path,
) -> None:
    source = _write_fixture(tmp_path)
    workflow.prepare_prompt(
        root=tmp_path,
        source=source,
        apply=True,
        now=NOW,
    )

    result = workflow.prepare_prompt(
        root=tmp_path,
        source=source,
        apply=True,
        now=NOW,
    )

    assert result.state == "already_prepared"


def test_prepare_rejects_unknown_module(tmp_path: Path) -> None:
    source = _write_fixture(tmp_path)
    text = source.read_text(encoding="utf-8").replace(
        "target_module: example_module",
        "target_module: unknown_module",
    )
    source.write_text(text, encoding="utf-8")

    with pytest.raises(
        workflow.WorkflowError,
        match="unknown target module",
    ):
        workflow.prepare_prompt(
            root=tmp_path,
            source=source,
            apply=True,
            now=NOW,
        )


def test_release_fails_closed_while_gated(
    tmp_path: Path,
) -> None:
    source = _write_fixture(tmp_path, authorized=False)
    workflow.prepare_prompt(
        root=tmp_path,
        source=source,
        apply=True,
        now=NOW,
    )

    with pytest.raises(
        workflow.WorkflowError,
        match="governance-gated",
    ):
        workflow.release_prompt(
            root=tmp_path,
            module="example_module",
            prompt_id="example_module_contract_v0_1",
            apply=True,
            now=NOW,
        )

    assert _prepared_path(tmp_path).exists()
    assert not _approved_path(tmp_path).exists()


def test_release_preview_is_read_only(tmp_path: Path) -> None:
    source = _write_fixture(tmp_path, authorized=True)
    workflow.prepare_prompt(
        root=tmp_path,
        source=source,
        apply=True,
        now=NOW,
    )

    result = workflow.release_prompt(
        root=tmp_path,
        module="example_module",
        prompt_id="example_module_contract_v0_1",
        apply=False,
        now=NOW,
    )

    assert result.state == "preview"
    assert _prepared_path(tmp_path).exists()
    assert not _approved_path(tmp_path).exists()


def test_release_writes_approved_artifact_and_ready_record(
    tmp_path: Path,
) -> None:
    source = _write_fixture(tmp_path, authorized=True)
    workflow.prepare_prompt(
        root=tmp_path,
        source=source,
        apply=True,
        now=NOW,
    )

    result = workflow.release_prompt(
        root=tmp_path,
        module="example_module",
        prompt_id="example_module_contract_v0_1",
        apply=True,
        now=NOW,
    )

    assert result.state == "released"
    assert result.sequence == 1
    assert not _prepared_path(tmp_path).exists()
    assert _approved_path(tmp_path).exists()
    approved = _approved_path(tmp_path).read_text(
        encoding="utf-8"
    )
    assert "lifecycle_state: released" in approved

    index = yaml.safe_load(
        (
            tmp_path
            / "coordination/outgoing_prompts/example_module/index.yaml"
        ).read_text(encoding="utf-8")
    )
    record = index["prompt_queue"][0]
    assert record["prompt_id"] == "example_module_contract_v0_1"
    assert record["sequence"] == 1
    assert (
        record["module_execution"]["status"]
        == "ready_for_module_pull"
    )
    assert record["blueprint_review"]["status"] == "not_started"


def test_release_is_idempotent_and_preserves_execution_state(
    tmp_path: Path,
) -> None:
    source = _write_fixture(tmp_path, authorized=True)
    workflow.prepare_prompt(
        root=tmp_path,
        source=source,
        apply=True,
        now=NOW,
    )
    workflow.release_prompt(
        root=tmp_path,
        module="example_module",
        prompt_id="example_module_contract_v0_1",
        apply=True,
        now=NOW,
    )

    result = workflow.release_prompt(
        root=tmp_path,
        module="example_module",
        prompt_id="example_module_contract_v0_1",
        apply=True,
        now=NOW,
    )

    assert result.state == "already_released"


def test_release_rejects_legacy_index(tmp_path: Path) -> None:
    source = _write_fixture(tmp_path, authorized=True)
    workflow.prepare_prompt(
        root=tmp_path,
        source=source,
        apply=True,
        now=NOW,
    )
    index_path = (
        tmp_path
        / "coordination/outgoing_prompts/example_module/index.yaml"
    )
    index_path.write_text(
        "module: example_module\nactive_prompts: []\n",
        encoding="utf-8",
    )

    with pytest.raises(
        workflow.WorkflowError,
        match="release requires prompt_queue_v0_2",
    ):
        workflow.release_prompt(
            root=tmp_path,
            module="example_module",
            prompt_id="example_module_contract_v0_1",
            apply=True,
            now=NOW,
        )


def test_release_rolls_back_on_index_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_fixture(tmp_path, authorized=True)
    workflow.prepare_prompt(
        root=tmp_path,
        source=source,
        apply=True,
        now=NOW,
    )
    index_path = (
        tmp_path
        / "coordination/outgoing_prompts/example_module/index.yaml"
    )
    original_index = index_path.read_text(encoding="utf-8")
    original_atomic_write = workflow._atomic_write
    failed = False

    def fail_once(path: Path, text: str) -> None:
        nonlocal failed
        if path == index_path and not failed:
            failed = True
            raise OSError("simulated index write failure")
        original_atomic_write(path, text)

    monkeypatch.setattr(workflow, "_atomic_write", fail_once)

    with pytest.raises(
        workflow.WorkflowError,
        match="rollback completed",
    ):
        workflow.release_prompt(
            root=tmp_path,
            module="example_module",
            prompt_id="example_module_contract_v0_1",
            apply=True,
            now=NOW,
        )

    assert _prepared_path(tmp_path).exists()
    assert not _approved_path(tmp_path).exists()
    assert index_path.read_text(encoding="utf-8") == original_index
