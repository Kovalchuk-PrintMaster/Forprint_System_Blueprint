from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import yaml

from scripts.coordination import completion_intake_check as checker
from scripts.run_blueprint_checks import build_checks

MODULE = "example_module"
PROMPT = "example_module_contract_v0_1"
PHASE = "contract_v0_1"
BRANCH = "feature/completion-check"


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def file_snapshot(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        snapshot[relative] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    return snapshot


def repository_snapshot(root: Path) -> tuple[str, str, str]:
    return (
        git(root, "rev-parse", "HEAD"),
        git(root, "show-ref"),
        git(root, "status", "--porcelain=v1"),
    )


def fixture(
    tmp_path: Path,
) -> tuple[Path, Path, Path, str, Path]:
    blueprint_root = tmp_path / "blueprint"
    module_root = tmp_path / "module"
    remote_root = tmp_path / "remote.git"

    queue = {
        "schema_version": "prompt_queue_v0_2",
        "module": MODULE,
        "prompt_queue": [
            {
                "prompt_id": PROMPT,
                "target_module": MODULE,
                "phase": PHASE,
                "module_execution": {
                    "status": "completed_by_module",
                },
                "blueprint_review": {
                    "status": "not_started",
                },
            }
        ],
    }
    roadmap = {
        "schema_version": "module_development_roadmap_v0_1",
        "module": MODULE,
        "roadmap": [
            {
                "step_id": PROMPT,
                "owner_module": MODULE,
                "status": "active",
            }
        ],
    }
    write_yaml(
        blueprint_root
        / "coordination/outgoing_prompts"
        / MODULE
        / "index.yaml",
        queue,
    )
    write_yaml(
        blueprint_root
        / "coordination/roadmaps"
        / f"{MODULE}.yaml",
        roadmap,
    )

    module_root.mkdir()
    git(module_root, "init", "-b", BRANCH)
    git(module_root, "config", "user.name", "ForPrint Test")
    git(
        module_root,
        "config",
        "user.email",
        "forprint-test@example.invalid",
    )

    (module_root / "implementation.txt").write_text(
        "implementation\n",
        encoding="utf-8",
    )
    git(module_root, "add", "implementation.txt")
    git(module_root, "commit", "-m", "implementation")
    implementation_commit = git(
        module_root,
        "rev-parse",
        "HEAD",
    )

    report_path = (
        module_root
        / "coordination/reports/completion"
        / "completion.md"
    )
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        "# Completion\n",
        encoding="utf-8",
    )

    packet = {
        "completion_id": "example_completed",
        "module_id": MODULE,
        "module_name": "Example Module",
        "phase": PHASE,
        "prompt_id": PROMPT,
        "report_id": "example_completion",
        "report_path": (
            "coordination/reports/completion/completion.md"
        ),
        "created_at": "2026-08-01T16:00:00+00:00",
        "branch": BRANCH,
        "implementation_commit": implementation_commit,
        "push_status": "pushed",
        "summary": "Completed the contract.",
        "implemented": ["Contract"],
        "checks": {
            "check_report": "ok",
            "tests": "ok",
            "governance_check": "ok",
            "check_report_passed": 7,
            "check_report_warnings": 0,
            "check_report_failed": 0,
        },
        "instruction_sources_reviewed": ["Blueprint prompt"],
        "standards_reviewed": ["Workflow architecture"],
        "standards_alignment_notes": ["Read-only intake"],
        "boundary_confirmation": {
            "no_production_api": True,
            "no_live_external_integrations": True,
            "no_real_1c_sync": True,
            "no_production_write": True,
            "no_automatic_posting": True,
            "blueprint_repository_written_directly": False,
        },
        "current_outputs": ["Completion packet"],
        "next_recommended_steps": ["Blueprint review"],
        "next_questions_for_blueprint": [],
    }
    packet_path = (
        module_root
        / "coordination/completion_packets/records"
        / "completion.yaml"
    )
    write_yaml(packet_path, packet)

    git(module_root, "add", ".")
    git(module_root, "commit", "-m", "completion packet")
    completion_commit = git(module_root, "rev-parse", "HEAD")

    subprocess.run(
        ["git", "init", "--bare", str(remote_root)],
        check=True,
        capture_output=True,
        text=True,
    )
    git(module_root, "remote", "add", "origin", str(remote_root))
    git(module_root, "push", "-u", "origin", BRANCH)

    return (
        blueprint_root,
        module_root,
        packet_path,
        completion_commit,
        remote_root,
    )


def run_check(
    blueprint_root: Path,
    module_root: Path,
    packet_path: Path,
    completion_commit: str,
) -> checker.CompletionIntakeCheckResult:
    return checker.check_completion_intake(
        blueprint_root=blueprint_root,
        module_id=MODULE,
        module_root=module_root,
        packet=packet_path,
        completion_commit=completion_commit,
    )


def test_valid_published_completion_passes(
    tmp_path: Path,
) -> None:
    (
        blueprint_root,
        module_root,
        packet_path,
        completion_commit,
        _remote_root,
    ) = fixture(tmp_path)

    result = run_check(
        blueprint_root,
        module_root,
        packet_path,
        completion_commit,
    )

    assert result.module_id == MODULE
    assert result.prompt_id == PROMPT
    assert result.completion_commit == completion_commit
    assert result.remote_commit == completion_commit


def test_check_is_read_only_for_both_repositories(
    tmp_path: Path,
) -> None:
    (
        blueprint_root,
        module_root,
        packet_path,
        completion_commit,
        _remote_root,
    ) = fixture(tmp_path)

    blueprint_files = file_snapshot(blueprint_root)
    module_files = file_snapshot(module_root)
    module_git = repository_snapshot(module_root)

    run_check(
        blueprint_root,
        module_root,
        packet_path,
        completion_commit,
    )

    assert file_snapshot(blueprint_root) == blueprint_files
    assert file_snapshot(module_root) == module_files
    assert repository_snapshot(module_root) == module_git


def test_only_git_subprocesses_are_invoked(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (
        blueprint_root,
        module_root,
        packet_path,
        completion_commit,
        _remote_root,
    ) = fixture(tmp_path)

    real_run = subprocess.run
    commands: list[list[str]] = []

    def traced_run(command, *args, **kwargs):
        commands.append(list(command))
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(checker.subprocess, "run", traced_run)

    run_check(
        blueprint_root,
        module_root,
        packet_path,
        completion_commit,
    )

    assert commands
    assert all(command[0] == "git" for command in commands)


def test_unpublished_completion_commit_fails(
    tmp_path: Path,
) -> None:
    (
        blueprint_root,
        module_root,
        packet_path,
        _completion_commit,
        _remote_root,
    ) = fixture(tmp_path)

    (module_root / "after-publication.txt").write_text(
        "local only\n",
        encoding="utf-8",
    )
    git(module_root, "add", "after-publication.txt")
    git(module_root, "commit", "-m", "local completion")
    unpublished_commit = git(module_root, "rev-parse", "HEAD")

    try:
        run_check(
            blueprint_root,
            module_root,
            packet_path,
            unpublished_commit,
        )
    except checker.CompletionIntakeCheckError as error:
        assert "not contained" in str(error)
    else:
        raise AssertionError("unpublished completion commit passed")


def test_modified_report_after_commit_fails(
    tmp_path: Path,
) -> None:
    (
        blueprint_root,
        module_root,
        packet_path,
        completion_commit,
        _remote_root,
    ) = fixture(tmp_path)

    report = (
        module_root
        / "coordination/reports/completion/completion.md"
    )
    report.write_text(
        "# Completion\n\nUncommitted change\n",
        encoding="utf-8",
    )

    try:
        run_check(
            blueprint_root,
            module_root,
            packet_path,
            completion_commit,
        )
    except checker.CompletionIntakeCheckError as error:
        assert "completion report content differs" in str(error)
    else:
        raise AssertionError("modified completion report passed")


def test_duplicate_packet_key_fails(
    tmp_path: Path,
) -> None:
    (
        blueprint_root,
        module_root,
        packet_path,
        completion_commit,
        _remote_root,
    ) = fixture(tmp_path)

    packet_path.write_text(
        packet_path.read_text(encoding="utf-8")
        + f"\nmodule_id: {MODULE}\n",
        encoding="utf-8",
    )

    try:
        run_check(
            blueprint_root,
            module_root,
            packet_path,
            completion_commit,
        )
    except checker.CompletionIntakeCheckError as error:
        assert "duplicate key `module_id`" in str(error)
    else:
        raise AssertionError("duplicate YAML key passed")


def test_non_ancestor_implementation_commit_fails(
    tmp_path: Path,
) -> None:
    (
        blueprint_root,
        module_root,
        packet_path,
        _completion_commit,
        _remote_root,
    ) = fixture(tmp_path)

    git(module_root, "switch", "--orphan", "unrelated")
    for child in module_root.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    (module_root / "unrelated.txt").write_text(
        "unrelated\n",
        encoding="utf-8",
    )
    git(module_root, "add", "unrelated.txt")
    git(module_root, "commit", "-m", "unrelated")
    unrelated_commit = git(module_root, "rev-parse", "HEAD")
    git(module_root, "switch", BRANCH)

    data = yaml.safe_load(packet_path.read_text(encoding="utf-8"))
    data["implementation_commit"] = unrelated_commit
    write_yaml(packet_path, data)
    git(
        module_root,
        "add",
        packet_path.relative_to(module_root).as_posix(),
    )
    git(module_root, "commit", "-m", "invalid lineage")
    invalid_completion = git(module_root, "rev-parse", "HEAD")
    git(module_root, "push", "origin", BRANCH)

    try:
        run_check(
            blueprint_root,
            module_root,
            packet_path,
            invalid_completion,
        )
    except checker.CompletionIntakeCheckError as error:
        assert "is not an ancestor" in str(error)
    else:
        raise AssertionError("invalid commit lineage passed")


def test_make_target_and_check_catalog_are_registered() -> None:
    root = Path(__file__).resolve().parents[2]
    makefile = (root / "Makefile").read_text(encoding="utf-8")

    assert ".PHONY: completion-intake-check" in makefile
    assert "completion_intake_check.py" in makefile

    checks = {
        item.check_id: item
        for item in build_checks()
    }
    check = checks["completion_intake_check_tests"]

    assert check.title == "Completion intake check"
    assert check.group == "coordination"
    assert (
        "tests/coordination/test_completion_intake_check.py"
        in check.command
    )
