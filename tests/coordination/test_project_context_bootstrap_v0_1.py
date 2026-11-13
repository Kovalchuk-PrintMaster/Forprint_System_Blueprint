from pathlib import Path

from scripts.coordination.build_project_context_archive import (
    select_sources,
    source_fingerprint,
)


def _index() -> dict:
    return {
        "topics": {
            "purpose": {
                "sources": [
                    {
                        "path": "AGENTS.md",
                        "mode": "file",
                        "required": True,
                    }
                ]
            },
            "portfolio": {
                "sources": [
                    {
                        "path": "coordination/roadmaps",
                        "mode": "directory_files",
                        "recursive": False,
                        "extensions": [".yaml"],
                        "required": True,
                    }
                ]
            },
        },
        "module_detail": {
            "directory_root": "coordination/roadmaps/details",
            "extensions": [".md", ".yaml"],
            "recursive": True,
        },
        "safety": {
            "forbidden_name_fragments": [
                ".env",
                "credential",
                "secret",
            ]
        },
    }


def test_select_sources_is_bounded_and_sorted(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# agent\n", encoding="utf-8")
    roadmaps = tmp_path / "coordination/roadmaps"
    roadmaps.mkdir(parents=True)
    (roadmaps / "z.yaml").write_text("z: 1\n", encoding="utf-8")
    (roadmaps / "a.yaml").write_text("a: 1\n", encoding="utf-8")
    (roadmaps / "ignore.md").write_text("# no\n", encoding="utf-8")

    selected, missing = select_sources(
        root=tmp_path,
        index=_index(),
        topics=["purpose", "portfolio"],
        module=None,
    )

    assert missing == []
    assert [path.relative_to(tmp_path).as_posix() for path in selected] == [
        "AGENTS.md",
        "coordination/roadmaps/a.yaml",
        "coordination/roadmaps/z.yaml",
    ]


def test_missing_required_source_is_reported(tmp_path: Path) -> None:
    selected, missing = select_sources(
        root=tmp_path,
        index=_index(),
        topics=["purpose"],
        module=None,
    )
    assert selected == []
    assert missing == [{"topic": "purpose", "path": "AGENTS.md", "required": True}]


def test_module_detail_adds_existing_deep_roadmap(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# agent\n", encoding="utf-8")
    detail = tmp_path / "coordination/roadmaps/details/example"
    detail.mkdir(parents=True)
    (detail / "plan.md").write_text("# plan\n", encoding="utf-8")

    selected, missing = select_sources(
        root=tmp_path,
        index=_index(),
        topics=["purpose"],
        module="example",
    )
    assert missing == []
    assert {path.relative_to(tmp_path).as_posix() for path in selected} == {
        "AGENTS.md",
        "coordination/roadmaps/details/example/plan.md",
    }


def test_source_fingerprint_changes_when_source_hash_changes() -> None:
    first = source_fingerprint(
        head="abc",
        branch="main",
        topics=["purpose"],
        module=None,
        rows=[{"path": "AGENTS.md", "sha256": "111"}],
    )
    second = source_fingerprint(
        head="abc",
        branch="main",
        topics=["purpose"],
        module=None,
        rows=[{"path": "AGENTS.md", "sha256": "222"}],
    )
    assert first != second



def test_module_analysis_resume_is_default_project_context_contract():
    import yaml

    root = Path(__file__).resolve().parents[2]
    data = yaml.safe_load(
        (root / "coordination/bootstrap/index_v0_1.yaml").read_text(encoding="utf-8")
    )

    assert "module_analysis_resume" in data["default_topics"]
    topic = data["topics"]["module_analysis_resume"]

    required_paths = {
        "coordination/bootstrap/module_analysis_methodology_current.yaml",
        "coordination/bootstrap/module_analysis_lifecycle_methodology_v0_2.md",
        "coordination/bootstrap/module_analysis_lifecycle_methodology_v0_2.yaml",
        "coordination/repository_knowledge/module_knowledge_stabilization/priority_module_sequence_v0_1.yaml",
        "coordination/repository_knowledge/module_knowledge_stabilization/snapshots/index_v0_1.yaml",
        "coordination/repository_knowledge/module_knowledge_stabilization/stage_2_module_knowledge_stabilization_charter_v0_1.md",
        "coordination/repository_knowledge/module_knowledge_stabilization/module_analysis_playbook_v0_1.md",
    }

    assert {row["path"] for row in topic["sources"]} == required_paths
    assert all(row["required"] is True for row in topic["sources"])
    assert all((root / path).is_file() for path in required_paths)


def test_module_analysis_resume_semantics_are_evidence_first():
    import yaml

    root = Path(__file__).resolve().parents[2]

    specs = yaml.safe_load(
        (
            root
            / "coordination/bootstrap/assistant_context_system_specs_v0_1.yaml"
        ).read_text(encoding="utf-8")
    )

    resume = specs["module_analysis_resume"]

    assert resume["required_before_target_selection"] is True
    assert resume["hardcoded_current_module_forbidden"] is True
    assert "COMPLETE_REGISTERED" in resume["status_vocabulary"]
    assert (
        "COMPLETE_MODULE_ONLY_NEEDS_BLUEPRINT_REGISTRATION"
        in resume["status_vocabulary"]
    )
    assert resume["analysis_entry_shape"]["coarse_inventory_first"] is True
    assert resume["analysis_entry_shape"]["large_thematic_packets_first"] is True
    assert (
        resume["analysis_entry_shape"][
            "micro_file_by_file_chat_analysis_forbidden_as_default"
        ]
        is True
    )


def test_accounting_snapshot_is_registered_before_advancing_normal_wave():
    import yaml

    root = Path(__file__).resolve().parents[2]

    index = yaml.safe_load(
        (
            root
            / "coordination/repository_knowledge/module_knowledge_stabilization/"
              "snapshots/index_v0_1.yaml"
        ).read_text(encoding="utf-8")
    )

    row = index["latest_by_module"]["forprint_accounting_registry_service"]

    assert row["snapshot_date"] == "2026-09-26"
    assert row["status"] == "complete"

    registration = root / row["record"]

    assert registration.is_file()

    data = yaml.safe_load(registration.read_text(encoding="utf-8"))

    assert data["module_id"] == "forprint_accounting_registry_service"
    assert data["repository_snapshot"]["remote_contains_snapshot_commit"] is True
    assert data["classification"]["implementation_authority_created"] is False


def test_current_methodology_requires_status_reconstruction_before_next_target():
    import yaml

    root = Path(__file__).resolve().parents[2]

    data = yaml.safe_load(
        (
            root
            / "coordination/bootstrap/module_analysis_lifecycle_methodology_v0_2.yaml"
        ).read_text(encoding="utf-8")
    )

    resume = data["portfolio_resume"]

    assert resume["required_before_target_selection"] is True
    assert resume["hardcoded_current_module_forbidden"] is True
    assert resume["priority_sequence_is_ordering_not_current_state_truth"] is True
    assert resume["micro_file_by_file_analysis_default"] is False
    assert (
        resume["operator_packet_exchange"][
            "one_large_thematic_packet_at_a_time_supported"
        ]
        is True
    )


def test_assistant_bootstrap_living_is_default_project_context_contract():
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[2]

    data = yaml.safe_load(
        (root / "coordination/bootstrap/index_v0_1.yaml").read_text(encoding="utf-8")
    )

    required = {
        'coordination/bootstrap/index_v0_1.yaml',
        'coordination/instruction_intake/assistant_reading_order.md',
        'coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_2.yaml',
        'coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml',
        'coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md',
        'coordination/repository_knowledge/roadmap_enrichment/README.md',
        'coordination/repository_knowledge/roadmap_enrichment/source_map.yaml',
    }

    assert "assistant_bootstrap_living" in data["default_topics"]

    assert data["reading_order"][0] == "coordination/instruction_intake/assistant_reading_order.md"

    topic = data["topics"]["assistant_bootstrap_living"]

    rows = topic["sources"]

    assert {
        row["path"]
        for row in rows
    } == required

    assert all(
        row["mode"] == "file"
        for row in rows
    )

    assert all(
        row["required"] is True
        for row in rows
    )

    assert all(
        (root / row["path"]).is_file()
        for row in rows
    )


def test_project_wide_closed_loop_direction_is_default_assistant_context_contract():
    import yaml

    root = Path(__file__).resolve().parents[2]

    transition_yaml = yaml.safe_load(
        (
            root
            / "coordination/global_policy/strategic_transition_vector_v0_1.yaml"
        ).read_text(encoding="utf-8")
    )

    policy_yaml = yaml.safe_load(
        (
            root
            / "coordination/global_policy/"
              "governed_change_and_acceptance_policy_direction_v0_1.yaml"
        ).read_text(encoding="utf-8")
    )

    specs = yaml.safe_load(
        (
            root
            / "coordination/bootstrap/assistant_context_system_specs_v0_1.yaml"
        ).read_text(encoding="utf-8")
    )

    index = yaml.safe_load(
        (
            root
            / "coordination/bootstrap/index_v0_1.yaml"
        ).read_text(encoding="utf-8")
    )

    direction = transition_yaml["project_wide_closed_loop_direction"]

    assert (
        direction["normative_scope"]
        == "all_current_and_future_forprint_modules"
    )

    assert direction["cf10"]["role"] == "current_proving_ground"
    assert direction["cf10"]["exclusive_policy_scope"] is False
    assert direction["permanent_chat_execution_orchestrator"] is False

    assert direction["engineering_entry_rule"] == [
        "resolve_live_roadmap_and_current_state",
        "inventory_nearest_existing_capability",
        "REUSE",
        "EXTEND",
        "ADAPT",
        "REPLACE",
        "NEW_only_when_required",
    ]

    closed_loop = policy_yaml["project_wide_closed_loop_execution"]

    assert (
        closed_loop["normative_scope"]
        == "all_current_and_future_forprint_modules"
    )

    assert (
        closed_loop["lifecycle_closure"]["test_pass_alone_is_sufficient"]
        is False
    )

    assert (
        closed_loop["automation"]["silently_expands_authority"]
        is False
    )

    assert closed_loop["cf10"]["exclusive_scope"] is False

    assert (
        closed_loop["future_dispatcher"]["current_authority"]
        == "none"
    )

    context = specs["project_wide_closed_loop_context"]

    assert (
        context["normative_scope"]
        == "all_current_and_future_forprint_modules"
    )

    assert (
        context["rules"]["live_sources_win_for_current_position"]
        is True
    )

    assert (
        context["rules"]["static_current_truth_snapshot_required"]
        is False
    )

    assert (
        context["rules"]["cf10_is_current_proving_ground_not_policy_scope"]
        is True
    )

    assert context["rules"]["reuse_order"] == [
        "REUSE",
        "EXTEND",
        "ADAPT",
        "REPLACE",
        "NEW",
    ]

    assert "assistant_operating_context" in index["default_topics"]
    assert "release" in index["default_topics"]

    assistant_sources = {
        row["path"]: row
        for row in index["topics"]["assistant_operating_context"]["sources"]
    }

    required_direct = {
        "coordination/global_policy/strategic_transition_vector_v0_1.md",
        "coordination/global_policy/strategic_transition_vector_v0_1.yaml",
        "coordination/global_policy/governed_change_and_acceptance_policy_direction_v0_1.md",
        "coordination/global_policy/governed_change_and_acceptance_policy_direction_v0_1.yaml",
        "coordination/roadmap_execution/projections/ROADMAP_EXECUTION_STATUS.yaml",
        "coordination/roadmap_execution/projections/ROADMAP_RECONCILIATION_STATUS.yaml",
    }

    assert required_direct.issubset(assistant_sources)

    assert all(
        assistant_sources[path]["required"] is True
        for path in required_direct
    )

    assert (
        "coordination/bootstrap/"
        "parallel_workstream_current_snapshot_v0_1.yaml"
        not in assistant_sources
    )

    release_sources = {
        row["path"]: row
        for row in index["topics"]["release"]["sources"]
    }

    focus = "coordination/global_policy/current_execution_focus.md"

    assert focus in release_sources
    assert release_sources[focus]["required"] is True

    transition_md = (
        root
        / "coordination/global_policy/strategic_transition_vector_v0_1.md"
    ).read_text(encoding="utf-8")

    governed_md = (
        root
        / "coordination/global_policy/"
          "governed_change_and_acceptance_policy_direction_v0_1.md"
    ).read_text(encoding="utf-8")

    assert "ForPrint-project-wide" in transition_md
    assert "REUSE → EXTEND → ADAPT → REPLACE → NEW" in transition_md

    assert (
        "Project-wide closed-loop execution policy direction"
        in governed_md
    )

    assert (
        "test suite is evidence, not lifecycle closure"
        in governed_md
    )
