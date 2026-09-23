from pathlib import Path

import yaml

from scripts.coordination.build_module_roadmap_reconciliation import build_report


def _dump(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    roadmap = tmp_path / "coordination/roadmaps/example.yaml"
    _dump(
        roadmap,
        {
            "metadata": {
                "roadmap_version": "example_v0_1",
                "current_step_id": "example_first_v0_1",
            },
            "roadmap": [
                {
                    "sequence": 1,
                    "step_id": "example_first_v0_1",
                    "title": "First",
                    "status": "accepted",
                },
                {
                    "sequence": 2,
                    "step_id": "example_second_v0_1",
                    "title": "Second",
                    "status": "planned",
                },
            ],
        },
    )
    base = tmp_path / "coordination/internal_work/blueprint/module_inventory/example"
    inv = base / "inventory.yaml"
    lin = base / "lineage.yaml"
    rec = base / "reconciliation.yaml"
    _dump(inv, {"known_step": "example_first_v0_1"})
    _dump(lin, {"history": ["example_first_v0_1"]})
    _dump(rec, {"roadmap_action": "review example_second_v0_1", "candidate": "example_future_v0_1"})

    state = tmp_path / (
        "coordination/internal_work/blueprint/module_inventory/"
        "2026-09-04__module_inventory_program_state_v0_1.yaml"
    )
    _dump(
        state,
        {
            "modules": [
                {
                    "module_id": "example",
                    "inventory_state": "COMPLETE_FIRST_PASS",
                    "consolidation_state": "COMPLETE",
                    "roadmap_enrichment_state": "INPUT_READY",
                    "inventory_evidence_ref": inv.relative_to(tmp_path).as_posix(),
                    "implementation_lineage_ref": lin.relative_to(tmp_path).as_posix(),
                    "first_wave_reconciliation_ref": rec.relative_to(tmp_path).as_posix(),
                }
            ]
        },
    )
    return roadmap, state


def test_read_only_and_alignment(tmp_path: Path) -> None:
    roadmap, state = _fixture(tmp_path)
    before = roadmap.read_bytes()
    report = build_report(
        root=tmp_path,
        module_id="example",
        roadmap_path=roadmap,
        state_path=state,
    )
    assert roadmap.read_bytes() == before
    assert report["auto_apply_performed"] is False
    assert report["roadmap_summary"]["step_count"] == 2
    assert (
        "example_first_v0_1"
        in report["evidence_alignment"][
            "roadmap_step_ids_mentioned_by_inventory_lineage_or_reconciliation"
        ]
    )
    assert (
        "example_future_v0_1"
        in report["evidence_alignment"][
            "step_like_ids_in_evidence_not_present_in_canonical_roadmap"
        ]
    )


def test_semantic_review_gate(tmp_path: Path) -> None:
    roadmap, state = _fixture(tmp_path)
    report = build_report(
        root=tmp_path,
        module_id="example",
        roadmap_path=roadmap,
        state_path=state,
    )
    gate = report["canonical_apply_gate"]
    assert report["state"] == "REVIEW_READY_PENDING_CANONICAL_ROADMAP_APPLY"
    assert gate["required"] is True
    assert gate["automatic"] is False
    assert gate["requires_semantic_review"] is True


def test_blueprint_obligation_invariant(tmp_path: Path) -> None:
    roadmap, state = _fixture(tmp_path)
    report = build_report(
        root=tmp_path,
        module_id="example",
        roadmap_path=roadmap,
        state_path=state,
    )
    assert (
        report["semantic_invariants"][
            "blueprint_assigned_responsibility_must_be_roadmap_visible_or_evidenced"
        ]
        is True
    )
