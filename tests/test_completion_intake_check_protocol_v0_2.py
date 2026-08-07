from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "coordination" / "completion_intake_check.py"


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "completion_intake_check_protocol_v0_2",
        SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def committed_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.email", "tests@example.invalid")
    git(repo, "config", "user.name", "Tests")
    (repo / "file.txt").write_text("evidence\n", encoding="utf-8")
    git(repo, "add", "file.txt")
    git(repo, "commit", "-m", "test evidence")
    return repo, git(repo, "rev-parse", "HEAD")


def base_v0_2_packet(commit: str) -> dict:
    return {
        "schema_version": "module_completion_packet_v0_2",
        "protocol_version": "blueprint_completion_intake_v0_2",
        "implementation_commit": commit,
    }


def test_result_constructor_preserves_legacy_callers() -> None:
    checker = load_checker()

    result = checker.CompletionIntakeCheckResult(
        "example",
        "example_prompt",
        "example_phase",
        "coordination/completion_packets/example.yaml",
        "coordination/reports/completion/example.md",
        "a" * 40,
        "b" * 40,
        "feature/example",
        "origin",
        "b" * 40,
        (),
    )

    assert result.warnings == ()
    assert result.schema_version == "module_completion_packet_v0_1"
    assert result.protocol_version == "blueprint_completion_intake_v0_1"
    assert result.supersedes_completion_id is None
    assert result.historical_legacy is True


def test_short_commit_is_resolved_through_git(tmp_path: Path) -> None:
    checker = load_checker()
    repo, full_commit = committed_repo(tmp_path)

    resolved = checker._verify_commit(
        repo,
        full_commit[:12],
        label="completion_commit",
    )

    assert resolved == full_commit


def test_legacy_packet_metadata_remains_supported() -> None:
    checker = load_checker()

    protocol = checker._packet_protocol({})

    assert protocol.schema_version == "module_completion_packet_v0_1"
    assert protocol.protocol_version == "blueprint_completion_intake_v0_1"
    assert protocol.historical_legacy is True


def test_v0_2_packet_requires_matching_protocol() -> None:
    checker = load_checker()
    packet = {
        "schema_version": "module_completion_packet_v0_2",
        "protocol_version": "wrong",
        "implementation_commit": "a" * 40,
    }

    try:
        checker._packet_protocol(packet)
    except checker.CompletionIntakeCheckError as error:
        issue = checker._classify_intake_error(error)
    else:
        raise AssertionError("protocol mismatch was not rejected")

    assert issue.code == "PACKET_PROTOCOL_MISMATCH"
    assert issue.failure_class == "protocol_compatibility"


def test_superseding_packet_requires_revision_reason() -> None:
    checker = load_checker()
    packet = base_v0_2_packet("a" * 40)
    packet["supersedes_completion_id"] = "old_completion"

    try:
        checker._packet_protocol(packet)
    except checker.CompletionIntakeCheckError as error:
        issue = checker._classify_intake_error(error)
    else:
        raise AssertionError("incomplete superseding packet was not rejected")

    assert issue.code == "SUPERSEDING_PACKET_INCOMPLETE"
    assert issue.remediation_owner == "module"


def test_boundary_failure_is_machine_readable() -> None:
    checker = load_checker()
    error = checker.CompletionIntakeCheckError(
        "unsafe boundary confirmation:\n- no_production_write must be true"
    )

    payload = checker._failure_payload(error)

    assert payload["status"] == "BLOCKED"
    assert payload["decision"] is None
    assert payload["automatic_acceptance"] is False
    assert payload["automatic_return"] is False
    assert payload["issue"]["code"] == "SAFETY_CONFIRMATION_INVALID"
    assert payload["issue"]["implementation_failure_proven"] is False


def test_success_payload_requires_operator_review() -> None:
    checker = load_checker()
    result = checker.CompletionIntakeCheckResult(
        module_id="example",
        prompt_id="example_prompt",
        phase="example_phase",
        packet_path="coordination/completion_packets/example.yaml",
        report_path="coordination/reports/completion/example.md",
        implementation_commit="a" * 40,
        completion_commit="b" * 40,
        branch="feature/example",
        remote="origin",
        remote_commit="b" * 40,
        schema_version="module_completion_packet_v0_2",
        protocol_version="blueprint_completion_intake_v0_2",
        supersedes_completion_id=None,
        historical_legacy=False,
        warnings=(),
    )

    payload = checker._success_payload(result)

    assert payload["status"] == "READY_FOR_OPERATOR_REVIEW"
    assert payload["decision"] is None
    assert payload["automatic_acceptance"] is False
    assert payload["automatic_return"] is False


def test_structured_json_failure_is_valid(capsys) -> None:
    checker = load_checker()
    payload = checker._failure_payload(
        checker.CompletionIntakeCheckError("[UNSUPPORTED_PACKET_SCHEMA] unsupported schema")
    )

    checker._print_structured(payload, output_format="json")

    rendered = json.loads(capsys.readouterr().out)
    assert rendered["issue"]["code"] == "UNSUPPORTED_PACKET_SCHEMA"


def test_structured_yaml_failure_is_valid(capsys) -> None:
    checker = load_checker()
    payload = checker._failure_payload(
        checker.CompletionIntakeCheckError("[COMMIT_IDENTIFIER_INVALID] bad commit")
    )

    checker._print_structured(payload, output_format="yaml")

    rendered = yaml.safe_load(capsys.readouterr().out)
    assert rendered["issue"]["field"] == "commit"
