from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_directive_index_schema_standard_exists() -> None:
    assert (
        ROOT
        / "coordination"
        / "standards"
        / "directive_index_schema.md"
    ).exists()


def test_calculator_directive_index_uses_canonical_module_directives_key() -> None:
    path = (
        ROOT
        / "coordination"
        / "directives"
        / "modules"
        / "calculator_engine"
        / "index.yaml"
    )

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert "module_directives" in data
    assert "active" in data["module_directives"]
    assert "archived" in data["module_directives"]
    assert isinstance(data["module_directives"]["active"], list)
    assert isinstance(data["module_directives"]["archived"], list)


def test_calculator_final_pause_directive_is_registered_as_active() -> None:
    path = (
        ROOT
        / "coordination"
        / "directives"
        / "modules"
        / "calculator_engine"
        / "index.yaml"
    )

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    active = {
        item["directive_id"]: item
        for item in data["module_directives"]["active"]
    }

    directive_id = (
        "2026-06-03__calculator_engine__directive__"
        "final-coordination-checkpoint-and-pause-v1"
    )

    assert directive_id in active
    assert active[directive_id]["status"] == "active"
    assert active[directive_id]["file"].endswith(f"{directive_id}.md")


def test_directive_index_schema_standard_mentions_module_directives_active() -> None:
    content = (
        ROOT
        / "coordination"
        / "standards"
        / "directive_index_schema.md"
    ).read_text(encoding="utf-8")

    assert "module_directives.active" in content
    assert "blueprint-sync-directives" in content
    assert "coordination-sync-check" in content
    assert (
        "Blueprint freshness, local readability, and directive import "
        "are separate actions."
        in content
    )
