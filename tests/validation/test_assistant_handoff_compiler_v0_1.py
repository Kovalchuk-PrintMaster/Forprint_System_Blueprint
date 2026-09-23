from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest
import yaml

from scripts.coordination import build_assistant_handoff_archive as handoff

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def handoff_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Use the real Git root normally; synthesize Git only in sterile compiler gates."""
    if (ROOT / ".git").exists():
        return ROOT

    repo = tmp_path_factory.mktemp("assistant_handoff_git_fixture")
    required = (
        Path("AGENTS.md"),
        Path("coordination/bootstrap/START_HERE.md"),
        Path("coordination/bootstrap/index_v0_1.yaml"),
        Path("coordination/global_policy/forprint_project_doctrine.md"),
        Path(
            "coordination/roadmaps/details/forprint_system_blueprint/continuity/"
            "2026-09-10__continuity_assistant_handoff_micro_roadmap_v0_1.yaml"
        ),
        Path("coordination/registry/execution_dependency_registry_v0_1.yaml"),
        Path("coordination/standards/automation/continuity_contract_v0_1.yaml"),
    )
    for rel in required:
        source = ROOT / rel
        assert source.is_file(), rel
        destination = repo / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    event_source = ROOT / "coordination/continuity/events"
    event_destination = repo / "coordination/continuity/events"
    shutil.copytree(event_source, event_destination)

    subprocess.run(
        ["git", "init", "-q"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=ForPrint Test",
            "-c",
            "user.email=forprint-test@example.invalid",
            "commit",
            "-qm",
            "assistant handoff sterile-gate fixture",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return repo


def test_handoff_payload_contains_required_zero_context_surfaces(handoff_root: Path) -> None:
    payload, manifest = handoff.build_payload(handoff_root)
    required = {
        "00_READ_FIRST.md",
        "manifest.json",
        "AGENTS.md",
        "coordination/bootstrap/START_HERE.md",
        "coordination/bootstrap/index_v0_1.yaml",
        "project_mission.md",
        "latest_checkpoint.yaml",
        "CURRENT_WORKFRONT.yaml",
        "NEXT_HORIZON.yaml",
        "RECENT_ACTIVITY.yaml",
        "DECISIONS.yaml",
        "BLOCKERS.yaml",
        "UNKNOWNS.yaml",
        "WORKER_PORTFOLIO.yaml",
        "SOURCE_STATE.yaml",
        "UNRECONCILED_CURRENT_DELTA.yaml",
        "roadmap_slice.yaml",
        "execution_dependency_slice.yaml",
        "knowledge_health.yaml",
    }
    assert required <= set(payload)
    assert manifest["authority"] == "none"
    assert manifest["chat_transcript_included"] is False


def test_handoff_archive_bytes_are_deterministic_for_same_state(handoff_root: Path) -> None:
    payload, _manifest = handoff.build_payload(handoff_root)
    first = handoff.archive_bytes(payload)
    second = handoff.archive_bytes(payload)
    assert first == second


def test_handoff_zip_metadata_is_fixed_and_lexicographic(handoff_root: Path) -> None:
    payload, _manifest = handoff.build_payload(handoff_root)
    blob = handoff.archive_bytes(payload)
    with zipfile.ZipFile(io.BytesIO(blob), "r") as archive:
        names = archive.namelist()
        assert names == sorted(names)
        for info in archive.infolist():
            assert info.date_time == handoff.FIXED_ZIP_DATE
            assert info.compress_type == zipfile.ZIP_STORED
            assert (info.external_attr >> 16) & 0o777 == 0o644


def test_manifest_binds_compiler_state_and_every_non_manifest_entry(handoff_root: Path) -> None:
    payload, manifest = handoff.build_payload(handoff_root)
    assert manifest["compiler_identity"] == handoff.COMPILER_ID
    assert manifest["compiler_version"] == handoff.COMPILER_VERSION
    assert len(manifest["compiler_sha256"]) == 64
    assert len(manifest["source_state_fingerprint"]) == 64
    assert len(manifest["latest_event_sha256"]) == 64
    hashes = manifest["included_path_sha256"]
    assert set(hashes) == set(payload) - {"manifest.json"}
    for name, digest in hashes.items():
        assert digest == hashlib.sha256(payload[name]).hexdigest()


def test_read_first_answers_current_state_and_horizon_without_chat(handoff_root: Path) -> None:
    payload, manifest = handoff.build_payload(handoff_root)
    read_first = payload["00_READ_FIRST.md"].decode("utf-8")
    assert "Chat transcript is not project source of truth." in read_first
    assert "Latest accepted checkpoint" in read_first
    assert "Present state" in read_first
    assert "Next horizon" in read_first
    assert "UNRECONCILED_CURRENT_DELTA.yaml" in read_first
    assert str(manifest["unreconciled_current_delta_material"]).lower() in read_first


def test_handoff_can_represent_unreconciled_current_state(handoff_root: Path) -> None:
    payload, manifest = handoff.build_payload(handoff_root)
    delta = yaml.safe_load(payload["UNRECONCILED_CURRENT_DELTA.yaml"].decode("utf-8"))
    source = yaml.safe_load(payload["SOURCE_STATE.yaml"].decode("utf-8"))
    assert manifest["unreconciled_current_delta_material"] == delta["payload"]["material"]
    assert manifest["source_state_fingerprint"] == source["payload"]["current_fingerprint"]


def test_manifest_has_no_generation_clock_or_chat_payload(handoff_root: Path) -> None:
    payload, manifest = handoff.build_payload(handoff_root)
    manifest_text = json.dumps(manifest, sort_keys=True).lower()
    assert "generated_at" not in manifest_text
    assert "created_at" not in manifest_text
    assert "transcript" not in " ".join(payload).lower()
    assert all(not name.startswith("tmp/") for name in payload)


def test_project_onboard_handoff_contains_exact_bootstrap_living_surfaces():
    import io
    import zipfile
    from pathlib import Path

    from scripts.coordination import (
        blueprint_continuity_adapter_v0_1 as adapter,
    )

    root = Path(__file__).resolve().parents[2]

    required = {
        'coordination/instruction_intake/assistant_reading_order.md', 'coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_2.yaml', 'coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml', 'coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md', 'coordination/repository_knowledge/roadmap_enrichment/README.md', 'coordination/repository_knowledge/roadmap_enrichment/source_map.yaml'
    }

    blob, _manifest, _name = adapter.expected_archive(root)

    with zipfile.ZipFile(io.BytesIO(blob), "r") as archive:
        names = set(archive.namelist())

        assert required <= names

        for rel in sorted(required):
            assert archive.read(rel) == (root / rel).read_bytes()

        read_first = archive.read(
            "00_READ_FIRST.md"
        ).decode("utf-8")

        assert "coordination/instruction_intake/assistant_reading_order.md" in read_first

        reading_order = archive.read(
            "coordination/instruction_intake/assistant_reading_order.md"
        ).decode("utf-8")

        for rel in (
            "coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_2.yaml",
            "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml",
            "coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md",
            "coordination/repository_knowledge/roadmap_enrichment/README.md",
            "coordination/repository_knowledge/roadmap_enrichment/source_map.yaml",
        ):
            assert rel in reading_order
