from __future__ import annotations

from pathlib import Path

from scripts.reporting.coordination_result_tables import (
    render_completion_intake_summary,
    render_next_work_summary,
)

ROOT = Path(__file__).resolve().parents[2]


def test_completion_intake_summary_is_compact_and_no_color_safe() -> None:
    rendered = render_completion_intake_summary(
        result="GREEN",
        mode="PREVIEW",
        module="logistics_service",
        prompt_id="provider_adapter_contract_v0_1",
        decision="accepted",
        reviewed_at="2026-07-15",
        changed_files=("coordination/queue.yaml",),
        warnings=(),
        next_actions=("make next-work-suggestion MODULE=logistics_service",),
        use_color=False,
    )

    assert "RESULT:" in rendered
    assert "MODE:" in rendered
    assert "CHANGED_FILES:" in rendered
    assert "NEXT_ACTION:" in rendered
    assert "coordination/queue.yaml" in rendered
    assert "\033[" not in rendered
    assert "┌" in rendered and "┘" in rendered


def test_completion_intake_warning_rows_use_semantic_color() -> None:
    rendered = render_completion_intake_summary(
        result="YELLOW",
        mode="WRITE",
        module="logistics_service",
        prompt_id="x",
        decision="returned_for_fix",
        reviewed_at="2026-07-15",
        changed_files=(),
        warnings=("Evidence needs review",),
        next_actions=(),
        use_color=True,
    )

    assert "Evidence needs review" in rendered
    assert "\033[33m" in rendered


def test_next_work_summary_preserves_contract_labels_and_context() -> None:
    rendered = render_next_work_summary(
        data={
            "result": "ACTIVE_PROMPT",
            "signal": "GREEN",
            "module": "logistics_service",
            "current_step": {
                "sequence": 4,
                "step_id": "provider_adapter_contract",
                "status": "active",
                "title": "Provider adapter contract",
            },
            "next_step": {
                "sequence": 5,
                "step_id": "nova_poshta_read_only",
                "status": "planned",
                "title": "Nova Poshta read-only foundation",
            },
            "active_prompts": [
                {
                    "sequence": 4,
                    "prompt_id": "provider_adapter_contract",
                    "status": "ready_for_module_pull",
                    "file": "approved/prompt.md",
                }
            ],
            "draft_candidates": [],
            "conflicting_drafts": [],
            "decision_required": False,
            "action": "Wait for module completion.",
        },
        use_color=False,
    )

    assert "RESULT:" in rendered
    assert "SIGNAL:" in rendered
    assert "MODULE:" in rendered
    assert "DECISION_REQUIRED:" in rendered
    assert "ACTIVE_PROMPTS: 1" in rendered
    assert "DRAFT_CANDIDATES: 0" in rendered
    assert "CONFLICTING_DRAFTS: 0" in rendered
    assert "provider_adapter_contract" in rendered
    assert "nova_poshta_read_only" in rendered
    assert "\033[" not in rendered


def test_coordination_scripts_delegate_to_shared_result_tables() -> None:
    completion_source = (
        ROOT / "scripts/coordination/module_completion_intake.py"
    ).read_text(encoding="utf-8")
    next_work_source = (
        ROOT / "scripts/coordination/resolve_next_module_work.py"
    ).read_text(encoding="utf-8")

    assert "render_completion_intake_summary" in completion_source
    assert "render_next_work_summary" in next_work_source
    assert 'parser.add_argument("--no-color"' in completion_source
    assert 'parser.add_argument("--no-color"' in next_work_source
