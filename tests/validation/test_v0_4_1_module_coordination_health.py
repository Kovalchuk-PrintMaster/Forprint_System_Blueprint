from __future__ import annotations

from pathlib import Path

import yaml

from scripts.coordination import module_coordination_health_v0_1 as health

ROOT = Path(__file__).resolve().parents[2]


def dump(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def prompt(path: Path, *, prompt_id: str, step_id: str | None) -> None:
    binding = f"roadmap_step_id: {step_id}\n" if step_id is not None else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "schema_version: outgoing_prompt_artifact_v0_1\n"
        f"prompt_id: {prompt_id}\n"
        "target_module: logistics_service\n"
        f"{binding}"
        "title: Example\n"
        "phase: example\n"
        "priority: normal\n"
        "created_at: \"2026-08-21\"\n"
        "source_change: test\n"
        "lifecycle_state: prepared\n"
        "lineage:\n"
        "  supersedes: null\n"
        "---\n"
        "Body\n",
        encoding="utf-8",
    )


def test_real_logistics_pilot_supports_deep_prepared_buffer_above_target() -> None:
    report = health.evaluate_module_health(
        root=ROOT,
        module="logistics_service",
    )

    assert report["pilot_enforcement"] is True
    assert report["roadmap"]["future_steps"] >= 8
    assert report["roadmap"]["state"] == "target_met"
    assert report["roadmap"]["dependency_eligible_future_steps"] == 1
    assert report["prompt_buffer"]["valid_prepared_prompts"] == 8
    assert report["prompt_buffer"]["state"] == "target_met"
    assert "PROMPT_BUFFER_BELOW_MINIMUM" not in report["codes"]["warnings"]

    refill = report["operator_refill"]
    assert refill["state"] == "target_met"
    assert refill["operator_action_required"] is False
    assert refill["shortage_to_minimum"] == 0
    assert refill["shortage_to_target"] == 0
    assert refill["recommendations"] == []
    assert refill["execution_selection_performed"] is False


def test_prepared_buffer_counts_unique_structured_future_bindings(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path
    monkeypatch.setattr(
        health,
        "resolve_roadmap_path",
        lambda *, root, module: root / "coordination/roadmaps/logistics_service.yaml",
    )
    monkeypatch.setattr(
        health,
        "load_yaml_file",
        lambda path: yaml.safe_load(path.read_text(encoding="utf-8")),
    )
    monkeypatch.setattr(
        health,
        "validate_roadmap_document",
        lambda document, path: type("V", (), {"errors": []})(),
    )

    dump(
        root / health.PILOT_DECISION,
        {
            "result": "LOGISTICS_ONLY_PILOT_SCOPE_ACTIVE",
            "pilot_scope": {"pilot_module": "logistics_service"},
        },
    )
    dump(
        root / health.HEALTH_POLICY,
        {
            "roadmap": {
                "minimum_future_steps": 1,
                "target_future_steps": 2,
            },
            "prompt_buffer": {
                "minimum_dispatchable_drafts": 2,
                "target_dispatchable_drafts": 3,
            },
        },
    )
    dump(
        root / "coordination/roadmaps/logistics_service.yaml",
        {
            "module": "logistics_service",
            "roadmap": [
                {
                    "step_id": "done_v0_1",
                    "status": "accepted",
                    "priority": "normal",
                    "depends_on": [],
                },
                {
                    "step_id": "future_a_v0_1",
                    "status": "planned",
                    "priority": "high",
                    "depends_on": [],
                },
                {
                    "step_id": "future_b_v0_1",
                    "status": "planned",
                    "priority": "normal",
                    "depends_on": [
                        {
                            "type": "module_step",
                            "module": "logistics_service",
                            "step_id": "future_a_v0_1",
                            "status": "pending",
                        }
                    ],
                },
            ],
        },
    )

    drafts = root / "coordination/outgoing_prompts/logistics_service/drafts"
    prompt(
        drafts / "a.md",
        prompt_id="prompt_a_v0_1",
        step_id="future_a_v0_1",
    )
    prompt(
        drafts / "b.md",
        prompt_id="prompt_b_v0_1",
        step_id="future_b_v0_1",
    )

    report = health.evaluate_module_health(
        root=root,
        module="logistics_service",
    )

    assert report["roadmap"]["future_steps"] == 2
    assert report["roadmap"]["dependency_eligible_future_steps"] == 1
    assert report["prompt_buffer"]["valid_prepared_prompts"] == 2
    assert report["prompt_buffer"]["state"] == "minimum_met_target_not_met"
    assert "PROMPT_BUFFER_BELOW_TARGET" in report["codes"]["advisories"]


def test_duplicate_binding_does_not_inflate_stock(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path
    monkeypatch.setattr(
        health,
        "resolve_roadmap_path",
        lambda *, root, module: root / "coordination/roadmaps/logistics_service.yaml",
    )
    monkeypatch.setattr(
        health,
        "load_yaml_file",
        lambda path: yaml.safe_load(path.read_text(encoding="utf-8")),
    )
    monkeypatch.setattr(
        health,
        "validate_roadmap_document",
        lambda document, path: type("V", (), {"errors": []})(),
    )

    dump(
        root / health.PILOT_DECISION,
        {
            "result": "LOGISTICS_ONLY_PILOT_SCOPE_ACTIVE",
            "pilot_scope": {"pilot_module": "logistics_service"},
        },
    )
    dump(
        root / health.HEALTH_POLICY,
        {
            "roadmap": {
                "minimum_future_steps": 1,
                "target_future_steps": 1,
            },
            "prompt_buffer": {
                "minimum_dispatchable_drafts": 1,
                "target_dispatchable_drafts": 2,
            },
        },
    )
    dump(
        root / "coordination/roadmaps/logistics_service.yaml",
        {
            "module": "logistics_service",
            "roadmap": [
                {
                    "step_id": "future_a_v0_1",
                    "status": "planned",
                    "priority": "high",
                    "depends_on": [],
                },
            ],
        },
    )

    drafts = root / "coordination/outgoing_prompts/logistics_service/drafts"
    prompt(
        drafts / "a.md",
        prompt_id="prompt_a_v0_1",
        step_id="future_a_v0_1",
    )
    prompt(
        drafts / "b.md",
        prompt_id="prompt_b_v0_1",
        step_id="future_a_v0_1",
    )

    report = health.evaluate_module_health(
        root=root,
        module="logistics_service",
    )

    assert report["prompt_buffer"]["valid_prepared_prompts"] == 0
    assert "PROMPT_BUFFER_DUPLICATE_STEP_BINDING" in report["codes"]["errors"]
    assert "PROMPT_BUFFER_BELOW_MINIMUM" in report["codes"]["warnings"]
    assert report["operator_refill"]["state"] == "blocked_by_buffer_integrity"
    assert report["operator_refill"]["recommendations"] == []
    assert health._exit_code(report) == 2


def test_non_future_binding_is_not_stock(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path
    monkeypatch.setattr(
        health,
        "resolve_roadmap_path",
        lambda *, root, module: root / "coordination/roadmaps/logistics_service.yaml",
    )
    monkeypatch.setattr(
        health,
        "load_yaml_file",
        lambda path: yaml.safe_load(path.read_text(encoding="utf-8")),
    )
    monkeypatch.setattr(
        health,
        "validate_roadmap_document",
        lambda document, path: type("V", (), {"errors": []})(),
    )

    dump(
        root / health.PILOT_DECISION,
        {
            "result": "LOGISTICS_ONLY_PILOT_SCOPE_ACTIVE",
            "pilot_scope": {"pilot_module": "logistics_service"},
        },
    )
    dump(
        root / health.HEALTH_POLICY,
        {
            "roadmap": {
                "minimum_future_steps": 0,
                "target_future_steps": 0,
            },
            "prompt_buffer": {
                "minimum_dispatchable_drafts": 1,
                "target_dispatchable_drafts": 1,
            },
        },
    )
    dump(
        root / "coordination/roadmaps/logistics_service.yaml",
        {
            "module": "logistics_service",
            "roadmap": [
                {
                    "step_id": "accepted_v0_1",
                    "status": "accepted",
                    "priority": "normal",
                    "depends_on": [],
                },
            ],
        },
    )

    drafts = root / "coordination/outgoing_prompts/logistics_service/drafts"
    prompt(
        drafts / "accepted.md",
        prompt_id="prompt_accepted_v0_1",
        step_id="accepted_v0_1",
    )

    report = health.evaluate_module_health(
        root=root,
        module="logistics_service",
    )

    assert report["prompt_buffer"]["valid_prepared_prompts"] == 0
    assert "PROMPT_BUFFER_NON_FUTURE_STEP" in report["codes"]["errors"]



def test_non_pilot_shortage_is_observe_only_advisory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path
    monkeypatch.setattr(
        health,
        "resolve_roadmap_path",
        lambda *, root, module: root / "coordination/roadmaps/other_module.yaml",
    )
    monkeypatch.setattr(
        health,
        "load_yaml_file",
        lambda path: yaml.safe_load(path.read_text(encoding="utf-8")),
    )
    monkeypatch.setattr(
        health,
        "validate_roadmap_document",
        lambda document, path: type("V", (), {"errors": []})(),
    )

    dump(
        root / health.PILOT_DECISION,
        {
            "result": "LOGISTICS_ONLY_PILOT_SCOPE_ACTIVE",
            "pilot_scope": {"pilot_module": "logistics_service"},
        },
    )
    dump(
        root / health.HEALTH_POLICY,
        {
            "roadmap": {
                "minimum_future_steps": 5,
                "target_future_steps": 8,
            },
            "prompt_buffer": {
                "minimum_dispatchable_drafts": 2,
                "target_dispatchable_drafts": 3,
            },
        },
    )
    dump(
        root / "coordination/roadmaps/other_module.yaml",
        {
            "module": "other_module",
            "roadmap": [
                {
                    "step_id": "other_future_v0_1",
                    "status": "planned",
                    "priority": "normal",
                    "depends_on": [],
                },
            ],
        },
    )

    report = health.evaluate_module_health(
        root=root,
        module="other_module",
    )

    assert report["pilot_enforcement"] is False
    assert report["codes"]["warnings"] == []
    assert "ROADMAP_HORIZON_BELOW_MINIMUM" in report["codes"]["advisories"]
    assert "PROMPT_BUFFER_BELOW_MINIMUM" in report["codes"]["advisories"]
    assert report["operator_refill"]["operator_action_required"] is False
    assert health._exit_code(report) == 0
