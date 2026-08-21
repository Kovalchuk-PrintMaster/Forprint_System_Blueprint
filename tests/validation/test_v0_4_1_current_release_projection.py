from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import yaml

from scripts.coordination.current_release_projection_v0_1 import validate

ROOT = Path(__file__).resolve().parents[2]
STEP29_SHA = "82308233625a348f8213d3976a60e6aa8a5db83cf3523cf334999e6e5e4727c5"


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_current_release_projection_is_green() -> None:
    assert validate(ROOT) == []


def test_v0_4_is_current_without_rewriting_historical_publication_status() -> None:
    release = load(ROOT / "coordination/releases/current.yaml")
    assert release["release"]["base_release_state"] == "PROMOTED_CLOSED_SEALED"
    assert release["release"]["hardening_release"] == "v0.4.1"

    assert load(
        ROOT / "coordination/standards/governance/module_prompt_contract_v0_4.yaml"
    )["metadata"]["status"] == "candidate_reference_only"
    assert load(
        ROOT / "coordination/standards/governance/module_completion_packet_v0_4.yaml"
    )["metadata"]["status"] == "candidate_reference_only"
    assert load(
        ROOT / "coordination/standards/governance/module_completion_outbox_v0_4.yaml"
    )["metadata"]["status"] == "candidate_reference_only"


def test_current_revision_is_v0_4() -> None:
    revision = load(ROOT / "coordination/revisions/current.yaml")
    assert revision["metadata"]["status"] == "current"
    assert revision["operational_current"]["prompt_contract"] == "module_prompt_contract_v0_4"
    assert revision["operational_current"]["completion_packet"] == "module_completion_packet_v0_4"
    assert revision["operational_current"]["completion_outbox"] == "module_completion_outbox_event_v0_4"
    assert revision["candidate_next"]["declared"] is False
    assert revision["superseded_transition"]["status"] == "deprecated_candidate"


def test_step29_remains_immutable() -> None:
    path = (
        ROOT
        / "coordination/internal_work/blueprint/governance/"
        "2026-08-19__blueprint__v0_4_global_promotion_decision_v0_1.yaml"
    )
    assert sha(path) == STEP29_SHA


def test_current_indexes_express_effective_active_adoption() -> None:
    root_index = load(ROOT / "coordination/standards/index.yaml")
    root_entries = {
        item["standard_id"]: item
        for item in root_index["standards"]
        if isinstance(item, dict) and isinstance(item.get("standard_id"), str)
    }
    expected = {
        "module_coordination_sync_protocol_v0_1",
        "accept_and_advance_protocol_v0_1",
        "next_work_selection_policy_v0_1",
        "coordination_health_policy_v0_1",
        "closed_loop_coordination_lifecycle_v0_1",
        "module_prompt_contract_v0_4",
        "module_completion_packet_v0_4",
        "module_completion_outbox_v0_4",
        "legacy_compatibility_retirement_policy_v0_1",
    }
    for standard_id in expected:
        assert root_entries[standard_id]["status"] == "active_standard"

    gov = load(ROOT / "coordination/standards/governance/index.yaml")
    docs = {
        item["file"]: item
        for item in gov["standards_group"]["documents"]
        if isinstance(item, dict) and isinstance(item.get("file"), str)
    }
    for standard_id in expected:
        file_name = root_entries[standard_id]["file"].removeprefix("governance/")
        assert docs[file_name]["status"] == "active_standard"


def test_release_status_cli_is_green() -> None:
    result = subprocess.run(
        ["make", "coordination-release-status"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "legacy_compatibility: advisory / nonblocking" in result.stdout

def test_context_bundle_surfaces_authoritative_current_release() -> None:
    result = subprocess.run(
        [
            ".venv_blueprint/bin/python",
            "scripts/coordination/build_context_bundle.py",
            "--module",
            "forprint_library",
            "--scope",
            "bootstrap",
            "--limit",
            "1",
            "--print",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "## Current Release Authority" in result.stdout
    assert "coordination/releases/current.yaml" in result.stdout
    assert "v0.4 PROMOTED_CLOSED_SEALED" in result.stdout
    assert "v0.4.1 ACTIVE_CURRENT" in result.stdout
    assert "advisory / nonblocking" in result.stdout
