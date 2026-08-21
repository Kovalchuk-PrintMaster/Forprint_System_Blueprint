from __future__ import annotations

from pathlib import Path

from scripts.coordination import resolve_next_module_work

ROOT = Path(__file__).resolve().parents[2]


def load_resolver():
    return resolve_next_module_work


def test_managed_prompt_uses_exact_structured_roadmap_binding(tmp_path: Path) -> None:
    module = load_resolver()
    prompt = tmp_path / "misleading_step_name.md"
    prompt.write_text(
        "---\n"
        "schema_version: outgoing_prompt_artifact_v0_1\n"
        "prompt_id: example_prompt_v0_1\n"
        "target_module: logistics_service\n"
        "roadmap_step_id: exact_step_v0_1\n"
        "title: Example\n"
        "phase: example\n"
        "priority: normal\n"
        "created_at: 2026-08-21\n"
        "source_change: test\n"
        "lifecycle_state: prepared\n"
        "lineage:\n"
        "  supersedes: null\n"
        "---\n"
        "Body mentions wrong_step_v0_1 and misleading_step_name.\n",
        encoding="utf-8",
    )

    assert module._matches_step(prompt, {"step_id": "exact_step_v0_1"})
    assert not module._matches_step(prompt, {"step_id": "wrong_step_v0_1"})
    assert not module._matches_step(prompt, {"step_id": "misleading_step_name"})


def test_legacy_non_managed_draft_keeps_read_compatibility(tmp_path: Path) -> None:
    module = load_resolver()
    prompt = tmp_path / "legacy_step_v0_1.md"
    prompt.write_text("legacy planning draft\n", encoding="utf-8")
    assert module._matches_step(prompt, {"step_id": "legacy_step_v0_1"})


def test_managed_prompt_without_binding_never_fuzzy_matches(tmp_path: Path) -> None:
    module = load_resolver()
    prompt = tmp_path / "target_step_v0_1.md"
    prompt.write_text(
        "---\n"
        "schema_version: outgoing_prompt_artifact_v0_1\n"
        "prompt_id: example_prompt_v0_1\n"
        "target_module: logistics_service\n"
        "title: Example\n"
        "phase: example\n"
        "priority: normal\n"
        "created_at: 2026-08-21\n"
        "source_change: test\n"
        "lifecycle_state: prepared\n"
        "lineage:\n"
        "  supersedes: null\n"
        "---\n"
        "target_step_v0_1\n",
        encoding="utf-8",
    )
    assert not module._matches_step(prompt, {"step_id": "target_step_v0_1"})
