from pathlib import Path

import yaml

ROOT = Path(".")
START = ROOT / "coordination/bootstrap/START_HERE.md"
INDEX = ROOT / "coordination/bootstrap/index_v0_1.yaml"
BUILDER = ROOT / "scripts/coordination/build_project_context_archive.py"


def main() -> int:
    _validate_assistant_bootstrap_living_pack_contract_v0_1()
    for path in (START, INDEX, BUILDER):
        if not path.is_file():
            print(f"PROJECT_CONTEXT_BOOTSTRAP=FAIL missing:{path}")
            return 1

    start = START.read_text(encoding="utf-8")
    data = yaml.safe_load(INDEX.read_text(encoding="utf-8"))

    required_text = [
        "make assistant-context-pack",
        "scripts/coordination/build_context_bundle.py",
        "--task-context",
        "Portfolio Context versus Task Context",
    ]
    if any(value not in start for value in required_text):
        print("PROJECT_CONTEXT_BOOTSTRAP=FAIL start_here_contract")
        return 1

    if data.get("schema_version") != "forprint_project_context_bootstrap_index_v0_1":
        print("PROJECT_CONTEXT_BOOTSTRAP=FAIL schema")
        return 1

    required_topics = {
        "purpose",
        "release",
        "current_workfront",
        "portfolio",
        "lifecycle",
        "self_knowledge",
    }
    topics = data.get("topics")
    if not isinstance(topics, dict) or not required_topics.issubset(topics):
        print("PROJECT_CONTEXT_BOOTSTRAP=FAIL topics")
        return 1

    task = data.get("task_context")
    if not isinstance(task, dict):
        print("PROJECT_CONTEXT_BOOTSTRAP=FAIL task_context")
        return 1
    if task.get("canonical_primitive") != "scripts/coordination/build_context_bundle.py":
        print("PROJECT_CONTEXT_BOOTSTRAP=FAIL task_context_primitive")
        return 1
    if task.get("project_entry_archive_replaces_task_context") is not False:
        print("PROJECT_CONTEXT_BOOTSTRAP=FAIL authority_boundary")
        return 1

    print("PROJECT_CONTEXT_BOOTSTRAP=PASS")
    print("ZERO_CONTEXT_ENTRY=coordination/bootstrap/START_HERE.md")
    print("PROJECT_CONTEXT_COMMAND=make assistant-context-pack")
    print("TASK_CONTEXT_PRIMITIVE_PRESERVED=true")
    print("PROJECT_CONTEXT_GRANTS_EXECUTION_AUTHORITY=false")
    return 0



def _validate_assistant_bootstrap_living_pack_contract_v0_1() -> None:
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[2]

    index_path = root / "coordination/bootstrap/index_v0_1.yaml"

    data = yaml.safe_load(
        index_path.read_text(encoding="utf-8")
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

    defaults = data.get("default_topics")

    if not isinstance(defaults, list):
        raise ValueError("default_topics must be a list")

    if "assistant_bootstrap_living" not in defaults:
        raise ValueError(
            "assistant_bootstrap_living missing from default_topics"
        )

    reading_order = data.get("reading_order")

    if (
        not isinstance(reading_order, list)
        or not reading_order
        or reading_order[0] != "coordination/instruction_intake/assistant_reading_order.md"
    ):
        raise ValueError(
            "assistant_reading_order is not the first project-entry route"
        )

    topics = data.get("topics")

    if not isinstance(topics, dict):
        raise ValueError("topics must be a mapping")

    topic = topics.get("assistant_bootstrap_living")

    if not isinstance(topic, dict):
        raise ValueError(
            "assistant_bootstrap_living topic missing"
        )

    sources = topic.get("sources")

    if not isinstance(sources, list):
        raise ValueError(
            "assistant_bootstrap_living sources missing"
        )

    rows = [
        row
        for row in sources
        if isinstance(row, dict)
    ]

    paths = {
        row.get("path")
        for row in rows
    }

    if paths != required:
        raise ValueError(
            "assistant_bootstrap_living source set mismatch"
        )

    for row in rows:
        if row.get("mode") != "file":
            raise ValueError(
                "assistant bootstrap/living source mode must be file"
            )

        if row.get("required") is not True:
            raise ValueError(
                "assistant bootstrap/living sources must be required"
            )

        rel = row.get("path")

        if not isinstance(rel, str) or not (root / rel).is_file():
            raise ValueError(
                "assistant bootstrap/living source missing: "
                + str(rel)
            )


if __name__ == "__main__":
    raise SystemExit(main())
