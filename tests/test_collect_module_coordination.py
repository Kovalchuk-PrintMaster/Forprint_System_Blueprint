from pathlib import Path

from scripts.collect_module_coordination import (
    GitPullResult,
    build_snapshot,
    find_module,
    render_markdown,
)


def test_find_module_returns_requested_module() -> None:
    modules = [
        {"module_id": "alpha", "module_name": "Alpha"},
        {"module_id": "beta", "module_name": "Beta"},
    ]

    module = find_module("beta", modules)

    assert module["module_id"] == "beta"


def test_build_snapshot_reports_missing_local_path() -> None:
    module = {
        "module_id": "calculator_engine",
        "module_name": "Calculator Engine",
        "local_path": "/path/that/does/not/exist/forprint-test",
        "repo_url": "git@example.com:test.git",
        "branch": "main",
        "repo_status": "confirmed",
        "status_file": "coordination/status/current_status.yaml",
        "prompt_index": "coordination/prompts/index.yaml",
        "report_index": "coordination/reports/index.yaml",
        "notes": "test module",
    }

    snapshot = build_snapshot(module=module, pull=False)

    assert snapshot.module_id == "calculator_engine"
    assert snapshot.coordination_ready is False
    assert snapshot.pull.ok is False
    assert "coordination/status/current_status.yaml" in snapshot.missing_files


def test_build_snapshot_loads_existing_coordination_files(tmp_path: Path) -> None:
    (tmp_path / "coordination" / "status").mkdir(parents=True)
    (tmp_path / "coordination" / "prompts").mkdir(parents=True)
    (tmp_path / "coordination" / "reports").mkdir(parents=True)

    (tmp_path / "coordination" / "status" / "current_status.yaml").write_text(
        "\n".join(
            [
                "module_id: calculator_engine",
                "module_status: active_development",
                "priority: p0",
                "current_phase: test_phase",
                "last_completed_step: test_step",
                "recommended_next_step:",
                "  - continue",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "coordination" / "prompts" / "index.yaml").write_text(
        "prompts: []\n",
        encoding="utf-8",
    )
    (tmp_path / "coordination" / "reports" / "index.yaml").write_text(
        "reports: []\n",
        encoding="utf-8",
    )

    module = {
        "module_id": "calculator_engine",
        "module_name": "Calculator Engine",
        "local_path": str(tmp_path),
        "repo_url": "git@example.com:test.git",
        "branch": "main",
        "repo_status": "confirmed",
        "status_file": "coordination/status/current_status.yaml",
        "prompt_index": "coordination/prompts/index.yaml",
        "report_index": "coordination/reports/index.yaml",
        "notes": "test module",
    }

    snapshot = build_snapshot(module=module, pull=False)

    assert snapshot.coordination_ready is True
    assert snapshot.current_status is not None
    assert snapshot.current_status["module_status"] == "active_development"
    assert not snapshot.missing_files


def test_render_markdown_contains_module_and_readiness() -> None:
    snapshot = GitPullResult(
        attempted=False,
        ok=True,
        returncode=None,
        stdout="",
        stderr="",
    )

    module_snapshot = type(
        "Snapshot",
        (),
        {
            "module_id": "calculator_engine",
            "module_name": "Calculator Engine",
            "generated_at": "2026-06-02T00:00:00+00:00",
            "local_path": "/tmp/calculator_engine",
            "repo_url": "git@example.com:test.git",
            "branch": "main",
            "repo_status": "confirmed",
            "pull": snapshot,
            "coordination_ready": True,
            "missing_files": [],
            "loaded_files": ["coordination/status/current_status.yaml"],
            "current_status": {
                "module_status": "active_development",
                "priority": "p0",
                "current_phase": "test_phase",
                "last_completed_step": "test_step",
                "recommended_next_step": ["continue"],
            },
            "notes": "test notes",
        },
    )()

    markdown = render_markdown(module_snapshot)

    assert "calculator_engine" in markdown
    assert "READY" in markdown
