import subprocess
from pathlib import Path

import yaml

from tools.forprint_coordination_tools.metadata import (
    check_module_coordination_metadata,
    fix_module_coordination_metadata,
)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_minimal_module(tmp_path: Path) -> Path:
    root = tmp_path / "module"

    write(
        root / "coordination/status/current_status.yaml",
        """
module_id: "calculator_engine"
module_name: "Calculator Engine"
module_status: "active"
priority: "p0"
current_phase: "test"
last_completed_step: "test"
last_commit: "abc123"
branch: "main"
checks:
  lint: "ok"
  tests: "ok"
  check_report: "ok"
boundary:
  no_foreign_ownership: true
recommended_next_step:
  - "continue"
updated_at: "2026-06-03T00:00:00Z"
""".strip()
        + "\n",
    )
    write(root / "coordination/status/current_status.md", "# Status\n")
    write(root / "coordination/status/next_questions_for_blueprint.md", "# Questions\n")
    write(
        root / "coordination/prompts/received/test-prompt.md",
        "# Prompt\n",
    )
    write(
        root / "coordination/reports/completion/test-report.md",
        "# Report\n",
    )
    write(
        root / "coordination/prompts/index.yaml",
        """
prompts:
  - prompt_id: "prompt-1"
    status: "received"
    file: "coordination/prompts/received/test-prompt.md"
""".strip()
        + "\n",
    )
    write(
        root / "coordination/reports/index.yaml",
        """
reports:
  - report_id: "report-1"
    responds_to_prompt_id: "prompt-1"
    status: "completed"
    report_file: "coordination/reports/completion/test-report.md"
    commit: "abc123"
    pushed: true
""".strip()
        + "\n",
    )

    return root


def test_coordination_metadata_check_passes_for_minimal_valid_module(
    tmp_path: Path,
) -> None:
    module_root = make_minimal_module(tmp_path)

    result = check_module_coordination_metadata(module_root)

    assert result.ok is True
    assert not result.errors


def test_coordination_metadata_check_detects_duplicate_prompt_id(
    tmp_path: Path,
) -> None:
    module_root = make_minimal_module(tmp_path)

    write(
        module_root / "coordination/prompts/index.yaml",
        """
prompts:
  - prompt_id: "prompt-1"
    status: "received"
    file: "coordination/prompts/received/test-prompt.md"
  - prompt_id: "prompt-1"
    status: "received"
    file: "coordination/prompts/received/test-prompt.md"
""".strip()
        + "\n",
    )

    result = check_module_coordination_metadata(module_root)

    assert result.ok is False
    assert any(item.code == "duplicate_prompt_id" for item in result.errors)


def test_coordination_metadata_check_detects_duplicate_report_id(
    tmp_path: Path,
) -> None:
    module_root = make_minimal_module(tmp_path)

    write(
        module_root / "coordination/reports/index.yaml",
        """
reports:
  - report_id: "report-1"
    responds_to_prompt_id: "prompt-1"
    status: "completed"
    report_file: "coordination/reports/completion/test-report.md"
    commit: "abc123"
    pushed: true
  - report_id: "report-1"
    responds_to_prompt_id: "prompt-1"
    status: "completed"
    report_file: "coordination/reports/completion/test-report.md"
    commit: "abc123"
    pushed: true
""".strip()
        + "\n",
    )

    result = check_module_coordination_metadata(module_root)

    assert result.ok is False
    assert any(item.code == "duplicate_report_id" for item in result.errors)


def test_coordination_metadata_check_detects_broken_file_reference(
    tmp_path: Path,
) -> None:
    module_root = make_minimal_module(tmp_path)

    write(
        module_root / "coordination/prompts/index.yaml",
        """
prompts:
  - prompt_id: "prompt-1"
    status: "received"
    file: "coordination/prompts/received/missing.md"
""".strip()
        + "\n",
    )

    result = check_module_coordination_metadata(module_root)

    assert result.ok is False
    assert any(item.code == "broken_reference" for item in result.errors)


def test_coordination_metadata_check_warns_about_priority_alias(
    tmp_path: Path,
) -> None:
    module_root = make_minimal_module(tmp_path)

    status_path = module_root / "coordination/status/current_status.yaml"
    data = yaml.safe_load(status_path.read_text(encoding="utf-8"))
    data["priority"] = "high"
    status_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    result = check_module_coordination_metadata(module_root)

    assert result.ok is True
    assert any(item.code == "priority_alias" for item in result.warnings)


def test_coordination_metadata_fixer_removes_exact_duplicate_entries(
    tmp_path: Path,
) -> None:
    module_root = make_minimal_module(tmp_path)

    write(
        module_root / "coordination/prompts/index.yaml",
        """
prompts:
  - prompt_id: "prompt-1"
    status: "received"
    file: "coordination/prompts/received/test-prompt.md"
  - prompt_id: "prompt-1"
    status: "received"
    file: "coordination/prompts/received/test-prompt.md"
""".strip()
        + "\n",
    )

    fix_result = fix_module_coordination_metadata(module_root)
    check_result = check_module_coordination_metadata(module_root)

    assert "coordination/prompts/index.yaml" in fix_result.changed_files
    assert check_result.ok is True


def test_coordination_metadata_fixer_normalizes_priority_alias(
    tmp_path: Path,
) -> None:
    module_root = make_minimal_module(tmp_path)

    status_path = module_root / "coordination/status/current_status.yaml"
    data = yaml.safe_load(status_path.read_text(encoding="utf-8"))
    data["priority"] = "high"
    status_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    fix_result = fix_module_coordination_metadata(module_root)
    fixed = yaml.safe_load(status_path.read_text(encoding="utf-8"))

    assert "coordination/status/current_status.yaml" in fix_result.changed_files
    assert fixed["priority"] == "p0"

def test_coordination_metadata_fixer_can_update_pending_commit_with_git_head(
    tmp_path: Path,
) -> None:
    module_root = make_minimal_module(tmp_path)

    # create git repository for HEAD lookup

    subprocess.run(["git", "init"], cwd=module_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=module_root,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=module_root,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=module_root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial test commit"],
        cwd=module_root,
        check=True,
        capture_output=True,
    )

    status_path = module_root / "coordination/status/current_status.yaml"
    status = yaml.safe_load(status_path.read_text(encoding="utf-8"))
    status["last_commit"] = "pending"
    status_path.write_text(yaml.safe_dump(status, sort_keys=False), encoding="utf-8")

    report_path = module_root / "coordination/reports/index.yaml"
    reports = yaml.safe_load(report_path.read_text(encoding="utf-8"))
    reports["reports"][0]["commit"] = "pending"
    report_path.write_text(yaml.safe_dump(reports, sort_keys=False), encoding="utf-8")

    fix_result = fix_module_coordination_metadata(
        module_root,
        update_git_commit=True,
    )

    fixed_status = yaml.safe_load(status_path.read_text(encoding="utf-8"))
    fixed_reports = yaml.safe_load(report_path.read_text(encoding="utf-8"))

    assert "coordination/status/current_status.yaml" in fix_result.changed_files
    assert "coordination/reports/index.yaml" in fix_result.changed_files
    assert fixed_status["last_commit"] != "pending"
    assert fixed_reports["reports"][0]["commit"] != "pending"
