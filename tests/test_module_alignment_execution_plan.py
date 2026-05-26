from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_alignment_execution_plan_references_known_modules() -> None:
    root = Path(__file__).resolve().parents[1]

    modules_data = _load_yaml(root / "machine/modules.yaml")
    plan_data = _load_yaml(root / "machine/module_alignment_execution_plan.yaml")

    known_modules = {item["id"] for item in modules_data["modules"]}

    for wave in plan_data["alignment_execution_plan"]["waves"]:
        for module in wave["modules"]:
            assert module["module_id"] in known_modules


def test_alignment_execution_plan_prompt_files_exist_when_defined() -> None:
    root = Path(__file__).resolve().parents[1]
    plan_data = _load_yaml(root / "machine/module_alignment_execution_plan.yaml")

    prompt_index_data = _load_yaml(root / "machine/prompt_dispatch_index.yaml")
    known_prompt_ids = {item["id"] for item in prompt_index_data["prompt_dispatch"]}

    for wave in plan_data["alignment_execution_plan"]["waves"]:
        for module in wave["modules"]:
            prompt_id = module.get("prompt_id")
            if prompt_id is not None:
                assert prompt_id in known_prompt_ids

def test_alignment_execution_plan_has_next_manual_action() -> None:
    root = Path(__file__).resolve().parents[1]
    plan_data = _load_yaml(root / "machine/module_alignment_execution_plan.yaml")

    next_action = plan_data["alignment_execution_plan"]["next_manual_action"]

    assert next_action["module_id"] == "forprint_integration_gateway"
    assert next_action["action"] == "send_approved_prompt_to_module_chat"
    assert "/approved/" in next_action["prompt_file"]
    assert next_action["prompt_file"].endswith("align-integration-gateway-with-blueprint.md")