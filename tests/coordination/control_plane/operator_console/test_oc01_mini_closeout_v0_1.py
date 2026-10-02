from __future__ import annotations

from pathlib import Path

from scripts.coordination.control_plane.operator_console.mini_closeout import (
    MILESTONES,
    validate_closeout,
)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_oc01_mini_closeout_validates_published_chain() -> None:
    result = validate_closeout(repository_root())
    assert result["result"] == "PASS"
    assert result["milestone_count"] == 9
    assert result["mini_slice_count"] == 8
    assert result["mini_sequence_complete"] is True
    assert result["completion_state"] == "USEFUL_MINIMUM_PROVEN_PARTIAL_OC01"
    assert result["oc01_full_complete"] is False
    assert result["oc01_full_activated"] is False
    assert result["cf10_canonical_write_reentry_allowed"] is True


def test_mini8_publication_is_terminal_mini_milestone() -> None:
    assert (
        MILESTONES["OC01-MINI-8"]
        == "89afbb3b4f3f06c664979de788bfd9bb117c789a"
    )
