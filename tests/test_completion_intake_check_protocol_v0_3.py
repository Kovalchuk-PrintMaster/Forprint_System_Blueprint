from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.coordination import completion_intake_check as checker

MODULE = "example_module"
PROMPT = "example_prompt_v0_3"
PHASE = "example_phase_v0_3"
BRANCH = "feature/example-v03"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
    )


def build_fixture(tmp_path: Path):
    blueprint = tmp_path / "blueprint"
    module = tmp_path / "module"
    remote = tmp_path / "remote.git"
    blueprint.mkdir()
    module.mkdir()

    prompt_rel = f"coordination/outgoing_prompts/{MODULE}/approved/prompt.md"
    prompt_path = blueprint / prompt_rel
    prompt_path.parent.mkdir(parents=True)
    prompt_path.write_text("# Prompt\n\nDo the thing.\n", encoding="utf-8")
    prompt_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()

    write_yaml(
        blueprint / "coordination/outgoing_prompts" / MODULE / "index.yaml",
        {
            "module": MODULE,
            "prompt_queue": [
                {
                    "prompt_id": PROMPT,
                    "target_module": MODULE,
                    "phase": PHASE,
                    "module_execution": {
                        "status": "completed_by_module",
                    },
                    "blueprint_review": {"status": "not_started"},
                }
            ],
        },
    )
    write_yaml(
        blueprint / "coordination/roadmaps" / f"{MODULE}.yaml",
        {
            "module": MODULE,
            "roadmap": [
                {
                    "step_id": PROMPT,
                    "owner_module": MODULE,
                    "status": "active",
                }
            ],
        },
    )

    git(module, "init", "-b", BRANCH)
    git(module, "config", "user.name", "Test")
    git(module, "config", "user.email", "test@example.invalid")

    (module / "foundation.txt").write_text("foundation\n", encoding="utf-8")
    git(module, "add", ".")
    git(module, "commit", "-m", "foundation")
    base = git(module, "rev-parse", "HEAD")

    contract = {
        "schema_version": "module_prompt_contract_v0_3",
        "contract_id": "example_prompt_contract_v0_3",
        "module_id": MODULE,
        "prompt_id": PROMPT,
        "phase": PHASE,
        "source_prompt": {
            "path": prompt_rel,
            "sha256": prompt_hash,
        },
        "implementation_base_commit": base,
        "requirements": [
            {
                "id": "REQ-001",
                "required": True,
                "statement": "Implement and test feature",
                "evidence_policy": "paths_and_tests",
                "changed_path_required": True,
            },
            {
                "id": "REQ-002",
                "required": True,
                "statement": "Document feature",
                "evidence_policy": "artifacts",
            },
            {
                "id": "REQ-003",
                "required": True,
                "statement": "Preserve safety",
                "evidence_policy": "boundary",
                "boundary_flags": [
                    "no_production_api",
                    "no_production_write",
                ],
            },
        ],
        "required_checks": [
            {"id": "CHECK-001", "command": "make check"},
            {"id": "CHECK-002", "command": "git diff --check"},
        ],
    }
    write_yaml(
        blueprint / "coordination/prompt_contracts" / MODULE / f"{PROMPT}.yaml",
        contract,
    )

    (module / "src").mkdir()
    (module / "tests").mkdir()
    (module / "docs").mkdir()
    (module / "src/feature.py").write_text("VALUE = 1\n", encoding="utf-8")
    (module / "tests/test_feature.py").write_text(
        "def test_feature():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    (module / "docs/feature.md").write_text("# Feature\n", encoding="utf-8")
    git(module, "add", ".")
    git(module, "commit", "-m", "implementation")
    tip = git(module, "rev-parse", "HEAD")

    report_rel = "coordination/reports/completion/completion.md"
    report = module / report_rel
    report.parent.mkdir(parents=True)
    report.write_text(
        "---\n"
        + yaml.safe_dump(
            {
                "schema_version": "module_completion_packet_v0_3",
                "protocol_version": "blueprint_completion_intake_v0_3",
                "prompt_contract_id": "example_prompt_contract_v0_3",
                "prompt_id": PROMPT,
                "target_module": MODULE,
                "phase": PHASE,
                "implementation_base_commit": base,
                "implementation_tip_commit": tip,
            },
            sort_keys=False,
        )
        + "---\n\n# Completion\n",
        encoding="utf-8",
    )

    packet = {
        "schema_version": "module_completion_packet_v0_3",
        "protocol_version": "blueprint_completion_intake_v0_3",
        "completion_id": "example_complete_v03",
        "module_id": MODULE,
        "module_name": "Example",
        "phase": PHASE,
        "prompt_id": PROMPT,
        "report_id": "example_report_v03",
        "report_path": report_rel,
        "created_at": "2026-08-12T12:00:00+03:00",
        "summary": "Complete",
        "implemented": ["Feature", "docs", "safety"],
        "checks": {
            "check_report": "ok",
            "tests": "ok",
            "governance_check": "ok",
            "check_report_failed": 0,
            "check_report_warnings": 0,
        },
        "instruction_sources_reviewed": ["prompt"],
        "standards_reviewed": ["v0.3"],
        "standards_alignment_notes": ["aligned"],
        "boundary_confirmation": {
            "no_production_api": True,
            "no_live_external_integrations": True,
            "no_real_1c_sync": True,
            "no_production_write": True,
            "no_automatic_posting": True,
        },
        "current_outputs": [
            "src/feature.py",
            "tests/test_feature.py",
            "docs/feature.md",
            report_rel,
        ],
        "next_recommended_steps": ["Blueprint reference review"],
        "next_questions_for_blueprint": [],
        "branch": BRANCH,
        "push_status": "pushed",
        "prompt_contract": {
            "contract_id": "example_prompt_contract_v0_3",
            "revision": "module_prompt_contract_v0_3",
            "source_prompt_sha256": prompt_hash,
        },
        "implementation_range": {
            "base_commit": base,
            "tip_commit": tip,
        },
        "requirement_results": [
            {
                "requirement_id": "REQ-001",
                "status": "completed",
                "implementation_paths": ["src/feature.py"],
                "test_paths": ["tests/test_feature.py"],
            },
            {
                "requirement_id": "REQ-002",
                "status": "completed",
                "artifact_paths": ["docs/feature.md"],
            },
            {
                "requirement_id": "REQ-003",
                "status": "completed",
            },
        ],
        "check_results": [
            {
                "check_id": "CHECK-001",
                "command": "make check",
                "status": "passed",
            },
            {
                "check_id": "CHECK-002",
                "command": "git diff --check",
                "status": "passed",
            },
        ],
    }
    packet_rel = "coordination/completion_packets/records/completion.yaml"
    packet_path = module / packet_rel
    write_yaml(packet_path, packet)

    git(module, "add", ".")
    git(module, "commit", "-m", "completion")
    completion = git(module, "rev-parse", "HEAD")

    subprocess.run(["git", "init", "--bare", str(remote)], check=True)
    git(module, "remote", "add", "origin", str(remote))
    git(module, "push", "-u", "origin", BRANCH)

    return blueprint, module, packet_path, completion, base, tip


def test_candidate_v03_reference_validation_is_green(tmp_path: Path) -> None:
    blueprint, module, packet, completion, base, tip = build_fixture(tmp_path)

    result = checker.check_completion_intake(
        blueprint_root=blueprint,
        module_id=MODULE,
        module_root=module,
        packet=packet,
        completion_commit=completion,
        allow_candidate_reference=True,
    )

    assert result.candidate_reference is True
    assert result.implementation_base_commit == base
    assert result.implementation_commit == tip
    assert result.requirement_coverage == ("REQ-001", "REQ-002", "REQ-003")
    assert result.check_coverage == ("CHECK-001", "CHECK-002")
    payload = checker._success_payload(result)
    assert payload["status"] == "REFERENCE_VALIDATION_READY"
    assert payload["decision"] is None


def test_candidate_v03_cannot_enter_normal_acceptance_path(tmp_path: Path) -> None:
    blueprint, module, packet, completion, _base, _tip = build_fixture(tmp_path)

    with pytest.raises(checker.CompletionIntakeCheckError) as caught:
        checker.check_completion_intake(
            blueprint_root=blueprint,
            module_id=MODULE,
            module_root=module,
            packet=packet,
            completion_commit=completion,
        )

    issue = checker._classify_intake_error(caught.value)
    assert issue.code == "PROTOCOL_NOT_ACTIVATED"
    assert issue.remediation_owner == "blueprint"


def test_v03_missing_requirement_is_blocked(tmp_path: Path) -> None:
    blueprint, module, packet, _completion, _base, _tip = build_fixture(tmp_path)
    data = yaml.safe_load(packet.read_text(encoding="utf-8"))
    data["requirement_results"] = data["requirement_results"][:-1]
    write_yaml(packet, data)
    git(module, "add", ".")
    git(module, "commit", "-m", "bad requirement coverage")
    completion = git(module, "rev-parse", "HEAD")
    git(module, "push", "origin", BRANCH)

    with pytest.raises(checker.CompletionIntakeCheckError) as caught:
        checker.check_completion_intake(
            blueprint_root=blueprint,
            module_id=MODULE,
            module_root=module,
            packet=packet,
            completion_commit=completion,
            allow_candidate_reference=True,
        )

    assert checker._classify_intake_error(caught.value).code == (
        "PROMPT_REQUIREMENT_COVERAGE_INCOMPLETE"
    )


def test_v03_missing_required_check_is_blocked(tmp_path: Path) -> None:
    blueprint, module, packet, _completion, _base, _tip = build_fixture(tmp_path)
    data = yaml.safe_load(packet.read_text(encoding="utf-8"))
    data["check_results"] = data["check_results"][:-1]
    write_yaml(packet, data)
    git(module, "add", ".")
    git(module, "commit", "-m", "bad check coverage")
    completion = git(module, "rev-parse", "HEAD")
    git(module, "push", "origin", BRANCH)

    with pytest.raises(checker.CompletionIntakeCheckError) as caught:
        checker.check_completion_intake(
            blueprint_root=blueprint,
            module_id=MODULE,
            module_root=module,
            packet=packet,
            completion_commit=completion,
            allow_candidate_reference=True,
        )

    assert checker._classify_intake_error(caught.value).code == ("REQUIRED_CHECK_EVIDENCE_MISSING")
