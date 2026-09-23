from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.coordination.mutation_compiler.engine import MutationCompiler
from scripts.coordination.mutation_compiler.models import CompilerPolicy


def init_git_repo(path: Path) -> None:
    subprocess.run(
        ["git", "init", "-q"],
        cwd=path,
        check=True,
    )


def test_invalid_json_is_rejected_without_apply(tmp_path: Path) -> None:
    target = tmp_path / "repo"
    candidate = tmp_path / "candidate"
    target.mkdir()
    candidate.mkdir()
    init_git_repo(target)

    rel = Path("config/example.json")
    (candidate / rel).parent.mkdir(parents=True)
    (candidate / rel).write_text("{bad json", encoding="utf-8")

    report = MutationCompiler(
        target_root=target,
        candidate_root=candidate,
        paths=[rel.as_posix()],
        mode="check",
        evidence_root=tmp_path / "evidence",
    ).compile()

    assert report.result_state == "FAIL_CANDIDATE"
    assert not (target / rel).exists()


def test_apply_preserves_external_dirty_file(tmp_path: Path) -> None:
    target = tmp_path / "repo"
    candidate = tmp_path / "candidate"
    target.mkdir()
    candidate.mkdir()
    init_git_repo(target)

    external = target / "external.txt"
    external.write_text("keep me", encoding="utf-8")

    rel = Path("config/example.json")
    (candidate / rel).parent.mkdir(parents=True)
    (candidate / rel).write_text('{"ok": true}\n', encoding="utf-8")

    report = MutationCompiler(
        target_root=target,
        candidate_root=candidate,
        paths=[rel.as_posix()],
        mode="apply",
        evidence_root=tmp_path / "evidence",
    ).compile()

    assert report.result_state == "PASS_APPLIED"
    assert json.loads((target / rel).read_text(encoding="utf-8"))["ok"] is True
    assert external.read_text(encoding="utf-8") == "keep me"
    assert report.external_baseline_preserved is True


def test_failed_candidate_gate_blocks_before_durable_apply(tmp_path: Path) -> None:
    target = tmp_path / "repo"
    candidate = tmp_path / "candidate"
    target.mkdir()
    candidate.mkdir()
    init_git_repo(target)

    rel = Path("config/example.json")
    (target / rel).parent.mkdir(parents=True)
    (target / rel).write_text('{"version": 1}\n', encoding="utf-8")
    (candidate / rel).parent.mkdir(parents=True)
    (candidate / rel).write_text('{"version": 2}\n', encoding="utf-8")

    report = MutationCompiler(
        target_root=target,
        candidate_root=candidate,
        paths=[rel.as_posix()],
        mode="apply",
        evidence_root=tmp_path / "evidence",
        post_commands=[
            f'{sys.executable} -c "import sys; sys.exit(7)"',
        ],
    ).compile()

    assert report.result_state == "FAIL_PROJECT_GATE"
    assert report.applied is False
    assert report.rolled_back is False
    assert json.loads((target / rel).read_text(encoding="utf-8"))["version"] == 1


def test_strict_unknown_blocks_unregistered_type(tmp_path: Path) -> None:
    target = tmp_path / "repo"
    candidate = tmp_path / "candidate"
    target.mkdir()
    candidate.mkdir()
    init_git_repo(target)

    rel = Path("assets/example.weird")
    (candidate / rel).parent.mkdir(parents=True)
    (candidate / rel).write_text("data", encoding="utf-8")

    report = MutationCompiler(
        target_root=target,
        candidate_root=candidate,
        paths=[rel.as_posix()],
        mode="check",
        policy=CompilerPolicy(strict_unknown=True),
        evidence_root=tmp_path / "evidence",
    ).compile()

    assert report.result_state == "FAIL_CANDIDATE"


def test_python_syntax_error_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "repo"
    candidate = tmp_path / "candidate"
    target.mkdir()
    candidate.mkdir()
    init_git_repo(target)

    rel = Path("scripts/bad.py")
    (candidate / rel).parent.mkdir(parents=True)
    (candidate / rel).write_text("def broken(:\n", encoding="utf-8")

    report = MutationCompiler(
        target_root=target,
        candidate_root=candidate,
        paths=[rel.as_posix()],
        mode="repair-check",
        evidence_root=tmp_path / "evidence",
    ).compile()

    assert report.result_state == "FAIL_CANDIDATE"


def test_failed_pre_apply_gate_does_not_mutate_target(tmp_path: Path) -> None:
    target = tmp_path / "repo"
    candidate = tmp_path / "candidate"
    target.mkdir()
    candidate.mkdir()
    init_git_repo(target)

    rel = Path("config/example.json")
    (target / rel).parent.mkdir(parents=True)
    (target / rel).write_text('{"version": 1}\n', encoding="utf-8")
    (candidate / rel).parent.mkdir(parents=True)
    (candidate / rel).write_text('{"version": 2}\n', encoding="utf-8")

    report = MutationCompiler(
        target_root=target,
        candidate_root=candidate,
        paths=[rel.as_posix()],
        mode="apply",
        evidence_root=tmp_path / "evidence",
        pre_commands=[
            f'{sys.executable} -c "import sys; sys.exit(5)"',
        ],
    ).compile()

    assert report.result_state == "FAIL_PROJECT_GATE"
    assert report.applied is False
    assert report.rolled_back is False
    assert json.loads((target / rel).read_text(encoding="utf-8"))["version"] == 1


def test_candidate_project_gate_isolated_and_sees_overlay(tmp_path: Path) -> None:
    target = tmp_path / "repo"
    candidate = tmp_path / "candidate"
    target.mkdir()
    candidate.mkdir()
    init_git_repo(target)

    external = target / "external.txt"
    external.write_text("durable-original", encoding="utf-8")

    rel = Path("config/example.json")
    (target / rel).parent.mkdir(parents=True)
    (target / rel).write_text('{"version": 1}\n', encoding="utf-8")
    (candidate / rel).parent.mkdir(parents=True)
    (candidate / rel).write_text('{"version": 2}\n', encoding="utf-8")

    code = (
        "import json; from pathlib import Path; "
        "assert json.loads(Path('config/example.json').read_text())['version'] == 2; "
        "Path('external.txt').write_text('verification-only')"
    )
    command = f"{sys.executable} -c {json.dumps(code)}"

    report = MutationCompiler(
        target_root=target,
        candidate_root=candidate,
        paths=[rel.as_posix()],
        mode="apply",
        evidence_root=tmp_path / "evidence",
        post_commands=[command],
    ).compile()

    assert report.result_state == "PASS_APPLIED"
    assert json.loads((target / rel).read_text(encoding="utf-8"))["version"] == 2
    assert external.read_text(encoding="utf-8") == "durable-original"
    assert report.external_baseline_preserved is True


def test_partial_multifile_apply_failure_rolls_back_all_targets(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "repo"
    candidate = tmp_path / "candidate"
    target.mkdir()
    candidate.mkdir()
    init_git_repo(target)

    rels = [Path("config/a.json"), Path("config/b.json")]
    for index, rel in enumerate(rels, 1):
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        (target / rel).write_text(
            json.dumps({"version": index}) + "\n",
            encoding="utf-8",
        )
        (candidate / rel).parent.mkdir(parents=True, exist_ok=True)
        (candidate / rel).write_text(
            json.dumps({"version": index + 10}) + "\n",
            encoding="utf-8",
        )

    compiler = MutationCompiler(
        target_root=target,
        candidate_root=candidate,
        paths=[rel.as_posix() for rel in rels],
        mode="apply",
        evidence_root=tmp_path / "evidence",
    )
    original_apply = compiler._atomic_apply_file
    calls = {"count": 0}

    def fail_on_second(staged: Path, durable: Path) -> None:
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("simulated second-file apply failure")
        original_apply(staged, durable)

    monkeypatch.setattr(compiler, "_atomic_apply_file", fail_on_second)

    report = compiler.compile()

    assert report.result_state == "SAFE_FAIL_ROLLED_BACK"
    assert report.rolled_back is True
    assert json.loads((target / rels[0]).read_text(encoding="utf-8"))["version"] == 1
    assert json.loads((target / rels[1]).read_text(encoding="utf-8"))["version"] == 2


def test_protected_git_target_is_blocked_before_apply(tmp_path: Path) -> None:
    target = tmp_path / "repo"
    candidate = tmp_path / "candidate"
    target.mkdir()
    candidate.mkdir()
    init_git_repo(target)

    original = (target / ".git/config").read_text(encoding="utf-8")
    rel = Path(".git/config")
    (candidate / rel).parent.mkdir(parents=True)
    (candidate / rel).write_text("[core]\nrepositoryformatversion = 999\n", encoding="utf-8")

    report = MutationCompiler(
        target_root=target,
        candidate_root=candidate,
        paths=[rel.as_posix()],
        mode="apply",
        evidence_root=tmp_path / "evidence",
    ).compile()

    assert report.result_state == "BLOCKED_UNSUPPORTED"
    assert report.applied is False
    assert (target / rel).read_text(encoding="utf-8") == original


def test_partial_apply_rollback_removes_new_parent_directories(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "repo"
    candidate = tmp_path / "candidate"
    target.mkdir()
    candidate.mkdir()
    init_git_repo(target)

    rels = [Path("new/deep/a.json"), Path("config/b.json")]
    (candidate / rels[0]).parent.mkdir(parents=True)
    (candidate / rels[0]).write_text('{"version": 11}\n', encoding="utf-8")

    (target / rels[1]).parent.mkdir(parents=True)
    (target / rels[1]).write_text('{"version": 2}\n', encoding="utf-8")
    (candidate / rels[1]).parent.mkdir(parents=True)
    (candidate / rels[1]).write_text('{"version": 12}\n', encoding="utf-8")

    compiler = MutationCompiler(
        target_root=target,
        candidate_root=candidate,
        paths=[rel.as_posix() for rel in rels],
        mode="apply",
        evidence_root=tmp_path / "evidence",
    )
    original_apply = compiler._atomic_apply_file
    calls = {"count": 0}

    def fail_on_second(staged: Path, durable: Path) -> None:
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("simulated second-file apply failure")
        original_apply(staged, durable)

    monkeypatch.setattr(compiler, "_atomic_apply_file", fail_on_second)

    report = compiler.compile()

    assert report.result_state == "SAFE_FAIL_ROLLED_BACK"
    assert report.rolled_back is True
    assert not (target / "new").exists()
    assert json.loads((target / rels[1]).read_text(encoding="utf-8"))["version"] == 2


def test_python_repair_is_finalized_in_project_relative_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "repo"
    candidate = tmp_path / "candidate"
    evidence = tmp_path / "evidence"
    fake_bin = tmp_path / "bin"
    target.mkdir()
    candidate.mkdir()
    fake_bin.mkdir()
    init_git_repo(target)

    (target / "pyproject.toml").write_text(
        "[tool.ruff]\nline-length = 100\n",
        encoding="utf-8",
    )
    rel = Path("tests/sample.py")
    (target / rel).parent.mkdir(parents=True)
    (target / rel).write_text("VALUE = 'old'\n", encoding="utf-8")
    (candidate / rel).parent.mkdir(parents=True)
    (candidate / rel).write_text("VALUE='candidate'\n", encoding="utf-8")

    fake_ruff = fake_bin / "ruff"
    fake_ruff.write_text(
        """#!/bin/bash
cmd="$1"
shift
fix=0
for arg in "$@"; do
  [ "$arg" = "--fix" ] && fix=1
done
if [ "$cmd" = "check" ] && [ "$fix" = "1" ]; then
  for arg in "$@"; do
    case "$arg" in
      *.py)
        if [[ "$arg" = /* ]]; then
          printf "VALUE = 'staging-context'\\n" > "$arg"
        else
          printf "VALUE = 'project-context'\\n" > "$arg"
        fi
        ;;
    esac
  done
fi
exit 0
""",
        encoding="utf-8",
    )
    fake_ruff.chmod(0o755)
    monkeypatch.setenv(
        "PATH",
        str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
    )

    report = MutationCompiler(
        target_root=target,
        candidate_root=candidate,
        paths=[rel.as_posix()],
        mode="apply",
        evidence_root=evidence,
    ).compile()

    assert report.result_state == "PASS_APPLIED"
    assert (target / rel).read_text(encoding="utf-8") == ("VALUE = 'project-context'\n")
    assert report.metadata["project_context_python_repair"] == "pass"
    phases = {command.phase for command in report.project_commands}
    assert "project_context_safe_repair" in phases
    assert "project_context_static_check" in phases
