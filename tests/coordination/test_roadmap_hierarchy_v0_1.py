from __future__ import annotations

from pathlib import Path

from scripts.coordination.module_roadmap import (
    render_roadmap_detail,
    validate_roadmap_document,
)
from scripts.coordination.roadmap_hierarchy_v0_1 import substep_progress


def _roadmap(step: dict) -> dict:
    return {
        "schema_version": "module_development_roadmap_v0_1",
        "module": "demo",
        "metadata": {"module": "demo", "current_step_id": "demo_step"},
        "roadmap": [{
            "sequence": 1,
            "step_id": "demo_step",
            "title": "Demo parent task",
            "status": "active",
            "priority": "high",
            "owner_module": "demo",
            "depends_on": [],
            "expected_outputs": [],
            "evidence": {},
            **step,
        }],
    }


def test_legacy_roadmap_without_substeps_remains_valid(tmp_path: Path) -> None:
    result = validate_roadmap_document(
        _roadmap({}),
        path=tmp_path / "roadmap.yaml",
    )
    assert result.ok, result.errors


def test_hierarchical_roadmap_reports_progress(tmp_path: Path) -> None:
    data = _roadmap({"substeps": [
        {"substep_id": "a", "title": "A", "status": "accepted", "blocking": True},
        {"substep_id": "b", "title": "B", "status": "active", "blocking": True},
        {"substep_id": "c", "title": "C", "status": "planned", "blocking": False},
    ]})
    result = validate_roadmap_document(
        data,
        path=tmp_path / "roadmap.yaml",
    )
    assert result.ok, result.errors
    progress = substep_progress(data["roadmap"][0])
    assert (progress.done, progress.total) == (1, 3)
    assert (progress.blocking_done, progress.blocking_total) == (1, 2)


def test_duplicate_substep_id_is_invalid(tmp_path: Path) -> None:
    data = _roadmap({"substeps": [
        {"substep_id": "same", "title": "One", "status": "planned"},
        {"substep_id": "same", "title": "Two", "status": "planned"},
    ]})
    result = validate_roadmap_document(
        data,
        path=tmp_path / "roadmap.yaml",
    )
    assert not result.ok
    assert any("duplicate substep_id" in error for error in result.errors)


def test_completed_or_accepted_parent_requires_blocking_substeps_done(
    tmp_path: Path,
) -> None:
    for status in ("completed", "accepted"):
        data = _roadmap({"status": status, "substeps": [
            {
                "substep_id": f"done_{status}",
                "title": "Done",
                "status": "accepted",
                "blocking": True,
            },
            {
                "substep_id": f"open_{status}",
                "title": "Open",
                "status": "planned",
                "blocking": True,
            },
        ]})
        result = validate_roadmap_document(
            data,
            path=tmp_path / f"{status}.yaml",
        )
        assert not result.ok
        assert any(
            "blocking substeps are only 1/2 done" in error
            for error in result.errors
        )


def test_cancelled_or_superseded_parent_may_leave_blocking_substeps_open(
    tmp_path: Path,
) -> None:
    for status in ("cancelled", "superseded"):
        data = _roadmap({"status": status, "substeps": [
            {
                "substep_id": f"open_{status}",
                "title": "Open",
                "status": "planned",
                "blocking": True,
            },
        ]})
        result = validate_roadmap_document(
            data,
            path=tmp_path / f"{status}.yaml",
        )
        assert result.ok, result.errors


def test_nonblocking_substep_does_not_block_acceptance(
    tmp_path: Path,
) -> None:
    data = _roadmap({"status": "accepted", "substeps": [
        {
            "substep_id": "required",
            "title": "Required",
            "status": "accepted",
            "blocking": True,
        },
        {
            "substep_id": "optional",
            "title": "Optional",
            "status": "planned",
            "blocking": False,
        },
    ]})
    result = validate_roadmap_document(
        data,
        path=tmp_path / "roadmap.yaml",
    )
    assert result.ok, result.errors


def test_detail_renderer_preserves_full_ids_and_uses_canonical_core(
    tmp_path: Path,
) -> None:
    long_id = (
        "demo_step__contract_with_a_deliberately_long_identifier_"
        "that_must_not_be_truncated"
    )
    long_title = (
        "A deliberately long title that detailed history "
        "must preserve completely"
    )
    data = _roadmap({"substeps": [
        {
            "substep_id": long_id,
            "title": long_title,
            "status": "accepted",
            "blocking": True,
            "summary": "Historical implementation detail remains visible.",
        },
        {
            "substep_id": "tests",
            "title": "Tests",
            "status": "active",
            "blocking": True,
        },
    ]})
    rendered = render_roadmap_detail(
        data,
        path=tmp_path / "roadmap.yaml",
        no_color=True,
    )
    assert long_id in rendered
    assert long_title in rendered
    assert "Historical implementation detail remains visible." in rendered
    assert "1/2 (blocking 1/2)" in rendered

    source = (
        Path(__file__).resolve().parents[2]
        / "scripts/coordination/render_module_roadmap_detail.py"
    ).read_text(encoding="utf-8")
    assert "render_roadmap_detail" in source
    assert "def _render_table" not in source
    assert "def _current_step_id" not in source
    assert "def _roadmap_items" not in source


def test_acceptance_oracle_binding_requires_sha_when_enabled(
    tmp_path: Path,
) -> None:
    data = _roadmap(
        {
            "acceptance": {
                "oracle_required": True,
                "oracle_path": (
                    "coordination/acceptance_oracles/demo/oracle.yaml"
                ),
            }
        }
    )
    result = validate_roadmap_document(
        data,
        path=tmp_path / "roadmap.yaml",
    )
    assert not result.ok
    assert any(
        "acceptance.oracle_sha256" in error
        for error in result.errors
    )
