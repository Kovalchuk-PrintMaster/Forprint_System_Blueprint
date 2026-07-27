from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (
    PROJECT_ROOT
    / "scripts/validation/validate_markdown_fences.py"
)


def write_baseline(
    path: Path,
    *,
    known_issues: list[dict[str, object]],
) -> None:
    payload = {
        "schema_version": "markdown_fence_baseline_v0_1",
        "generated_from_head": "test",
        "known_issues": known_issues,
    }
    path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def run_validator(
    root: Path,
    baseline: Path,
    markdown: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--root",
            str(root),
            "--baseline",
            str(baseline),
            markdown.name,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def issue_entry(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.name,
        "opening_line": 1,
        "fence_char": "`",
        "fence_length": 3,
        "info": "text",
        "content_sha256": hashlib.sha256(data).hexdigest(),
    }


def test_balanced_file_passes_with_empty_baseline(
    tmp_path: Path,
) -> None:
    markdown = tmp_path / "example.md"
    baseline = tmp_path / "baseline.json"

    markdown.write_text(
        "```text\nexample\n```\n",
        encoding="utf-8",
    )
    write_baseline(baseline, known_issues=[])

    result = run_validator(tmp_path, baseline, markdown)

    assert result.returncode == 0
    assert "Current issues: 0" in result.stdout


def test_new_unclosed_fence_fails(
    tmp_path: Path,
) -> None:
    markdown = tmp_path / "example.md"
    baseline = tmp_path / "baseline.json"

    markdown.write_text(
        "```text\nexample\n",
        encoding="utf-8",
    )
    write_baseline(baseline, known_issues=[])

    result = run_validator(tmp_path, baseline, markdown)

    assert result.returncode == 1
    assert "NEW ISSUES" in result.stdout


def test_exact_known_issue_passes(
    tmp_path: Path,
) -> None:
    markdown = tmp_path / "example.md"
    baseline = tmp_path / "baseline.json"

    markdown.write_text(
        "```text\nexample\n",
        encoding="utf-8",
    )
    write_baseline(
        baseline,
        known_issues=[issue_entry(markdown)],
    )

    result = run_validator(tmp_path, baseline, markdown)

    assert result.returncode == 0
    assert "Current issues: 1" in result.stdout


def test_changed_known_issue_file_fails(
    tmp_path: Path,
) -> None:
    markdown = tmp_path / "example.md"
    baseline = tmp_path / "baseline.json"

    markdown.write_text(
        "```text\nexample\n",
        encoding="utf-8",
    )
    entry = issue_entry(markdown)
    write_baseline(baseline, known_issues=[entry])

    markdown.write_text(
        "```text\nchanged example\n",
        encoding="utf-8",
    )

    result = run_validator(tmp_path, baseline, markdown)

    assert result.returncode == 1
    assert "CHANGED BASELINE FILES" in result.stdout


def test_resolved_issue_requires_baseline_reduction(
    tmp_path: Path,
) -> None:
    markdown = tmp_path / "example.md"
    baseline = tmp_path / "baseline.json"

    markdown.write_text(
        "```text\nexample\n",
        encoding="utf-8",
    )
    entry = issue_entry(markdown)
    write_baseline(baseline, known_issues=[entry])

    markdown.write_text(
        "```text\nexample\n```\n",
        encoding="utf-8",
    )

    result = run_validator(tmp_path, baseline, markdown)

    assert result.returncode == 1
    assert "STALE BASELINE ENTRIES" in result.stdout
