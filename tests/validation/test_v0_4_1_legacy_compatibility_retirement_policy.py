from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_legacy_registry_is_nonblocking_and_has_retirement_gate() -> None:
    data = load(ROOT / "coordination/legacy/compatibility_registry_v0_1.yaml")
    assert data["default_current_gate_behavior"]["blocking"] is False
    assert data["default_current_gate_behavior"]["visibility"] == "advisory_yellow"

    component = data["components"][0]
    assert component["status"] == "deprecated_candidate"
    assert component["blocking_current_gates"] is False
    assert component["manual_use_only"] is True
    assert component["retirement"]["planned_slice"] == "H11"
    assert component["retirement"]["requires_h10_complete"] is True
    assert component["retirement"]["requires_explicit_operator_retirement_decision"] is True


def test_current_completion_check_no_longer_targets_old_transition_suite() -> None:
    text = (ROOT / "scripts/run_blueprint_checks.py").read_text(encoding="utf-8")
    start = text.index('check_id="completion_intake_check_tests"')
    window = text[start : start + 3000]
    assert "tests/coordination/test_completion_intake_check.py" not in window
    assert "tests/test_completion_intake_check_protocol_v0_3.py" not in window
    assert "tests/validation/test_completion_revision_registry_v0_1.py" not in window
    assert "tests/validation/test_v0_4_completion_discovery_and_intake.py" in window
    assert "tests/validation/test_v0_4_completion_packet.py" in window
    assert "tests/validation/test_v0_4_completion_outbox.py" in window


def test_legacy_status_is_visible_but_green() -> None:
    result = subprocess.run(
        ["make", "legacy-compat-status"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "current_gate: NONBLOCKING" in result.stdout
    assert "visibility: ADVISORY_YELLOW" in result.stdout
    assert "deprecated_candidate" in result.stdout


def test_deprecated_tests_are_centrally_governed_not_rewritten() -> None:
    data = load(ROOT / "coordination/legacy/compatibility_registry_v0_1.yaml")
    component = data["components"][0]

    assert component["deprecated_test_modules"] == [
        "tests/validation/test_completion_revision_registry_v0_1.py",
        "tests/coordination/test_completion_intake_check.py",
        "tests/test_completion_intake_check_protocol_v0_2.py",
        "tests/test_completion_intake_check_protocol_v0_3.py",
    ]
    assert component["deprecated_test_nodeids"] == [
        (
            "tests/validation/test_v0_4_completion_packet.py::"
            "test_operational_v02_and_candidate_v03_revision_registry_are_unchanged"
        ),
        (
            "tests/validation/test_v0_4_completion_discovery_and_intake.py::"
            "test_legacy_operational_and_candidate_intake_revisions_are_unchanged"
        ),
    ]

    policy = (ROOT / "tests/conftest.py").read_text(encoding="utf-8")
    assert "FORPRINT_LEGACY_COMPATIBILITY_COLLECTION_POLICY_V0_1" in policy
    assert "deprecated_test_modules" in policy
    assert "deprecated_test_nodeids" in policy


def test_full_pytest_reports_legacy_skips_without_failure() -> None:
    result = subprocess.run(
        [
            ".venv_blueprint/bin/python",
            "-m",
            "pytest",
            "-q",
            "tests/validation/test_completion_revision_registry_v0_1.py",
            (
                "tests/validation/test_v0_4_completion_packet.py::"
                "test_operational_v02_and_candidate_v03_revision_registry_are_unchanged"
            ),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "skipped" in result.stdout
