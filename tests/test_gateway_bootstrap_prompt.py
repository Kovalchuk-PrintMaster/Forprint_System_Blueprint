from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_gateway_bootstrap_prompt_is_registered() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/prompt_dispatch_index.yaml")
    prompts = data["prompt_dispatch"]

    prompt = next(
        item
        for item in prompts
        if item["id"] == "2026-05-23-bootstrap-integration-gateway-from-blueprint"
    )

    assert prompt["target_module"] == "forprint_integration_gateway"
    assert prompt["status"] == "approved"
    assert prompt["expected_response_type"] == "module_bootstrap_plan"
    assert prompt["prompt_file"].endswith(
        "2026-05-23-bootstrap-integration-gateway-from-blueprint.md"
    )


def test_gateway_old_alignment_prompt_is_archived() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/prompt_dispatch_index.yaml")
    prompts = data["prompt_dispatch"]

    old_prompt = next(
        item
        for item in prompts
        if item["id"] == "2026-05-22-align-integration-gateway-with-blueprint"
    )

    assert old_prompt["status"] == "archived"


def test_gateway_bootstrap_prompt_file_exists() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/prompt_dispatch_index.yaml")
    prompts = data["prompt_dispatch"]

    prompt = next(
        item
        for item in prompts
        if item["id"] == "2026-05-23-bootstrap-integration-gateway-from-blueprint"
    )

    assert (root / prompt["prompt_file"]).exists()