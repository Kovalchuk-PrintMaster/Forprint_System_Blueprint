from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.coordination.resolve_next_module_work import (
    as_dict,
    resolve_next_work,
)
from scripts.coordination.selection_policy_v0_1 import (
    DEFAULT_SELECTION_SOURCE,
    EXPLICIT_OVERRIDE_SOURCE,
    SelectionPolicyError,
    priority_then_stable_id_key,
)


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def step(
    step_id: str,
    *,
    sequence: int,
    priority: str,
    status: str = "planned",
    depends_on: list | None = None,
) -> dict:
    return {
        "sequence": sequence,
        "step_id": step_id,
        "title": step_id,
        "status": status,
        "priority": priority,
        "owner_module": "demo",
        "depends_on": depends_on or [],
        "expected_outputs": [],
        "evidence": {},
    }


def fixture_state(
    tmp_path: Path,
    candidates: list[dict],
) -> Path:
    root = tmp_path
    roadmap = root / "coordination/roadmaps/demo.yaml"
    queue = root / "coordination/outgoing_prompts/demo/index.yaml"
    drafts = root / "coordination/outgoing_prompts/demo/drafts"

    base = step(
        "base",
        sequence=1,
        priority="critical",
        status="accepted",
    )
    write_yaml(
        roadmap,
        {
            "schema_version": "module_development_roadmap_v0_1",
            "module": "demo",
            "metadata": {
                "current_step_id": "base",
                "updated_at": "2026-08-20",
            },
            "roadmap": [base, *candidates],
        },
    )
    write_yaml(
        queue,
        {
            "schema_version": "prompt_queue_v0_2",
            "module": "demo",
            "prompt_queue": [],
        },
    )
    drafts.mkdir(parents=True, exist_ok=True)
    for candidate in candidates:
        path = drafts / f"{candidate['step_id']}.md"
        path.write_text(
            f"# {candidate['step_id']}\n\n"
            f"roadmap step: {candidate['step_id']}\n",
            encoding="utf-8",
        )
    return root


def test_priority_key_uses_only_priority_then_stable_id() -> None:
    records = [
        {
            "step_id": "zeta",
            "priority": "high",
            "sequence": 1,
            "created_at": "2020-01-01",
        },
        {
            "step_id": "alpha",
            "priority": "high",
            "sequence": 999,
            "created_at": "2099-01-01",
        },
        {
            "step_id": "critical",
            "priority": "critical",
            "sequence": 9999,
            "created_at": "2099-12-31",
        },
    ]
    ordered = sorted(
        records,
        key=lambda item: priority_then_stable_id_key(
            item,
            id_field="step_id",
        ),
    )
    assert [item["step_id"] for item in ordered] == [
        "critical",
        "alpha",
        "zeta",
    ]


def test_noncanonical_priority_fails_closed() -> None:
    with pytest.raises(
        SelectionPolicyError,
        match="unsupported canonical priority",
    ):
        priority_then_stable_id_key(
            {"step_id": "demo", "priority": "medium"},
            id_field="step_id",
        )


def test_module_default_prefers_priority_over_sequence(
    tmp_path: Path,
) -> None:
    root = fixture_state(
        tmp_path,
        [
            step(
                "lower_sequence",
                sequence=2,
                priority="high",
                depends_on=["base"],
            ),
            step(
                "critical_later",
                sequence=99,
                priority="critical",
                depends_on=["base"],
            ),
        ],
    )
    suggestion = resolve_next_work(root=root, module="demo")
    data = as_dict(suggestion, root=root)
    assert data["result"] == "DRAFT_CANDIDATE_FOUND"
    assert data["next_step"]["step_id"] == "critical_later"
    assert data["selection_source"] == DEFAULT_SELECTION_SOURCE


def test_module_dependency_gate_beats_priority(
    tmp_path: Path,
) -> None:
    root = fixture_state(
        tmp_path,
        [
            step(
                "gate",
                sequence=2,
                priority="high",
                depends_on=["base"],
            ),
            step(
                "critical_blocked",
                sequence=3,
                priority="critical",
                depends_on=["gate"],
            ),
        ],
    )
    suggestion = resolve_next_work(root=root, module="demo")
    assert suggestion.next_step is not None
    assert suggestion.next_step["step_id"] == "gate"


def test_module_equal_priority_uses_step_id_not_sequence(
    tmp_path: Path,
) -> None:
    root = fixture_state(
        tmp_path,
        [
            step(
                "zeta",
                sequence=2,
                priority="high",
                depends_on=["base"],
            ),
            step(
                "alpha",
                sequence=900,
                priority="high",
                depends_on=["base"],
            ),
        ],
    )
    suggestion = resolve_next_work(root=root, module="demo")
    assert suggestion.next_step is not None
    assert suggestion.next_step["step_id"] == "alpha"


def test_module_explicit_override_wins_after_eligibility(
    tmp_path: Path,
) -> None:
    root = fixture_state(
        tmp_path,
        [
            step(
                "high_default",
                sequence=2,
                priority="critical",
                depends_on=["base"],
            ),
            step(
                "explicit_lower",
                sequence=3,
                priority="normal",
                depends_on=["base"],
            ),
        ],
    )
    suggestion = resolve_next_work(
        root=root,
        module="demo",
        override_step_id="explicit_lower",
    )
    data = as_dict(suggestion, root=root)
    assert data["next_step"]["step_id"] == "explicit_lower"
    assert data["selection_source"] == EXPLICIT_OVERRIDE_SOURCE


def test_module_ineligible_override_fails_closed(
    tmp_path: Path,
) -> None:
    root = fixture_state(
        tmp_path,
        [
            step(
                "gate",
                sequence=2,
                priority="high",
                depends_on=["base"],
            ),
            step(
                "blocked_override",
                sequence=3,
                priority="critical",
                depends_on=["gate"],
            ),
        ],
    )
    with pytest.raises(
        ValueError,
        match="explicit override is not dependency-eligible",
    ):
        resolve_next_work(
            root=root,
            module="demo",
            override_step_id="blocked_override",
        )

def test_local_dependency_canonical_status_beats_stale_snapshot(
    tmp_path: Path,
) -> None:
    root = fixture_state(
        tmp_path,
        [
            step(
                "gate",
                sequence=2,
                priority="high",
                depends_on=["base"],
            ),
            step(
                "must_stay_blocked",
                sequence=3,
                priority="critical",
                depends_on=[
                    {
                        "type": "module_step",
                        "module": "demo",
                        "step_id": "gate",
                        "status": "accepted",
                    }
                ],
            ),
        ],
    )

    suggestion = resolve_next_work(root=root, module="demo")
    assert suggestion.next_step is not None
    assert suggestion.next_step["step_id"] == "gate"


def test_cross_module_dependency_does_not_alias_local_step_id(
    tmp_path: Path,
) -> None:
    root = fixture_state(
        tmp_path,
        [
            step(
                "shared_id",
                sequence=2,
                priority="high",
                status="accepted",
                depends_on=["base"],
            ),
            step(
                "candidate",
                sequence=3,
                priority="critical",
                depends_on=[
                    {
                        "type": "module_step",
                        "module": "other_module",
                        "step_id": "shared_id",
                        "status": "pending",
                    }
                ],
            ),
            step(
                "fallback",
                sequence=4,
                priority="normal",
                depends_on=["base"],
            ),
        ],
    )

    suggestion = resolve_next_work(root=root, module="demo")
    assert suggestion.next_step is not None
    assert suggestion.next_step["step_id"] == "fallback"

    roadmap_path = root / "coordination/roadmaps/demo.yaml"
    roadmap = yaml.safe_load(roadmap_path.read_text(encoding="utf-8"))
    candidate = next(
        item
        for item in roadmap["roadmap"]
        if item["step_id"] == "candidate"
    )
    candidate["depends_on"][0]["status"] = "accepted"
    write_yaml(roadmap_path, roadmap)

    suggestion = resolve_next_work(root=root, module="demo")
    assert suggestion.next_step is not None
    assert suggestion.next_step["step_id"] == "candidate"


def test_acknowledged_document_dependency_is_eligible(
    tmp_path: Path,
) -> None:
    root = fixture_state(
        tmp_path,
        [
            step(
                "document_ready",
                sequence=2,
                priority="critical",
                depends_on=[
                    {
                        "type": "document",
                        "reference": "coordination/standards/example.md",
                        "status": "acknowledged",
                    }
                ],
            ),
        ],
    )

    suggestion = resolve_next_work(root=root, module="demo")
    assert suggestion.next_step is not None
    assert suggestion.next_step["step_id"] == "document_ready"
