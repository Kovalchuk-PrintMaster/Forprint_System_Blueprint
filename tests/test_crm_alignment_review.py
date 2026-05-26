from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_crm_alignment_review_exists_and_is_reviewed() -> None:
    root = Path(__file__).resolve().parents[1]

    review_path = root / "machine/crm_alignment_review.yaml"
    data = _load_yaml(review_path)

    review = data["crm_alignment_review"]

    assert review["module_id"] == "forprint_crm"
    assert review["review_status"] == "reviewed"
    assert review["overall_assessment"]["module_direction_is_correct"] is True
    assert review["overall_assessment"]["urgent_architecture_drift"] is False


def test_crm_alignment_review_tracks_core_contracts() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/crm_alignment_review.yaml")
    contracts = data["crm_alignment_review"]["required_contracts"]

    contract_ids = {item["id"] for item in contracts}

    assert "operational_registry_to_crm_dashboard_snapshot.v1" in contract_ids
    assert "crm_to_integration_gateway_command.v1" in contract_ids
    assert "integration_gateway_to_crm_command_result.v1" in contract_ids


def test_crm_prompt_dispatch_is_reviewed() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/prompt_dispatch_index.yaml")
    prompts = data["prompt_dispatch"]

    crm_prompt = next(
        item
        for item in prompts
        if item["id"] == "2026-05-22-align-crm-with-blueprint"
    )

    assert crm_prompt["status"] == "reviewed"
    assert crm_prompt["response_file"].endswith(
        "2026-05-23-forprint-crm-alignment-report.md"
    )
    assert crm_prompt["review_file"] == "human/crm_alignment_review.md"