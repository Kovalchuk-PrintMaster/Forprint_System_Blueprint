from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_calculator_alignment_review_exists_and_is_reviewed() -> None:
    root = Path(__file__).resolve().parents[1]

    review_path = root / "machine/calculator_alignment_review.yaml"
    data = _load_yaml(review_path)

    review = data["calculator_alignment_review"]

    assert review["module_id"] == "calculator_engine"
    assert review["review_status"] == "reviewed"
    assert review["overall_assessment"]["module_direction_is_correct"] is True
    assert review["overall_assessment"]["urgent_architecture_drift"] is False


def test_calculator_alignment_review_tracks_material_consumption_contract_gap() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/calculator_alignment_review.yaml")
    contract_gaps = data["calculator_alignment_review"]["contract_gaps"]

    gap_ids = {item["id"] for item in contract_gaps}

    assert "material_consumption_estimate_contract" in gap_ids


def test_calculator_prompt_dispatch_is_reviewed() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/prompt_dispatch_index.yaml")
    prompts = data["prompt_dispatch"]

    calculator_prompt = next(
        item
        for item in prompts
        if item["id"] == "2026-05-22-align-calculator-engine-with-blueprint"
    )

    assert calculator_prompt["status"] == "reviewed"
    assert calculator_prompt["response_file"].endswith(
        "2026-05-23-calculator-engine-alignment-report.md"
    )
    assert calculator_prompt["review_file"] == "human/calculator_alignment_review.md"