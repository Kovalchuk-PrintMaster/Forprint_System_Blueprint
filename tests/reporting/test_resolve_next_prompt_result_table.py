from __future__ import annotations

import sys
from pathlib import Path

import scripts.coordination.resolve_next_prompt as resolve_module
from scripts.coordination.resolve_next_prompt import (
    NextPromptSummary,
    render_summary,
)
from scripts.reporting.coordination_result_tables import (
    render_next_prompt_summary,
)


def _summary(tmp_path: Path) -> NextPromptSummary:
    prompt = tmp_path / "prompt.md"
    prompt.write_text("# Prompt body\n\nPreserve this content.\n", encoding="utf-8")
    return NextPromptSummary(
        module="forprint_test",
        sequence=7,
        prompt_id="test_prompt_v0_1",
        title="Test prompt",
        priority="high",
        file="approved/test_prompt.md",
        path=prompt,
    )


def test_shared_next_prompt_renderer_uses_boxed_table() -> None:
    rendered = render_next_prompt_summary(
        module="forprint_test",
        sequence=7,
        prompt_id="test_prompt_v0_1",
        title="Test prompt",
        priority="high",
        file="approved/test_prompt.md",
        path="coordination/outgoing_prompts/forprint_test/approved/test_prompt.md",
        use_color=False,
    )

    assert "ForPrint Next Prompt" in rendered
    assert "┌" in rendered
    assert "│ Module" in rendered
    assert "forprint_test" in rendered
    assert "test_prompt_v0_1" in rendered
    assert "\x1b[" not in rendered


def test_resolve_summary_delegates_to_shared_renderer(
    tmp_path: Path,
) -> None:
    rendered = render_summary(
        _summary(tmp_path),
        tmp_path,
        use_color=False,
    )

    assert "ForPrint Next Prompt" in rendered
    assert "┌" in rendered
    assert "test_prompt_v0_1" in rendered


def test_path_only_contract_remains_plain_path(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    summary = _summary(tmp_path)
    monkeypatch.setattr(
        resolve_module,
        "resolve_next_prompt_summary",
        lambda _root, _module: summary,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "resolve_next_prompt.py",
            "--root",
            str(tmp_path),
            "--module",
            "forprint_test",
            "--path-only",
        ],
    )

    assert resolve_module.main() == 0
    captured = capsys.readouterr()
    assert captured.out == "prompt.md\n"
    assert captured.err == ""


def test_failure_contract_remains_stdout_and_exit_one(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    def fail_resolution(_root: Path, _module: str) -> NextPromptSummary:
        raise LookupError("missing ready prompt")

    monkeypatch.setattr(
        resolve_module,
        "resolve_next_prompt_summary",
        fail_resolution,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "resolve_next_prompt.py",
            "--root",
            str(tmp_path),
            "--module",
            "forprint_test",
        ],
    )

    assert resolve_module.main() == 1
    captured = capsys.readouterr()
    assert captured.out == "FAILED: missing ready prompt\n"
    assert captured.err == ""


def test_read_mode_preserves_prompt_body_after_separator(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    summary = _summary(tmp_path)
    expected_body = summary.path.read_text(encoding="utf-8")

    monkeypatch.setattr(
        resolve_module,
        "resolve_next_prompt_summary",
        lambda _root, _module: summary,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "resolve_next_prompt.py",
            "--root",
            str(tmp_path),
            "--module",
            "forprint_test",
            "--read",
        ],
    )
    monkeypatch.setenv("NO_COLOR", "1")

    assert resolve_module.main() == 0
    captured = capsys.readouterr()
    separator = "=" * 80 + "\n"
    assert separator in captured.out
    assert captured.out.split(separator, 1)[1] == expected_body + "\n"
    assert "\x1b[" not in captured.out
    assert captured.err == ""
