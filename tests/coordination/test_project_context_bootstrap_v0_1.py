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
