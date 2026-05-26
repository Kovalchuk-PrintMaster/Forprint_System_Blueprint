from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_library_alignment_review_exists_and_is_reviewed() -> None:
    root = Path(__file__).resolve().parents[1]

    review_path = root / "machine/library_alignment_review.yaml"
    data = _load_yaml(review_path)

    review = data["library_alignment_review"]

    assert review["module_id"] == "forprint_library"
    assert review["review_status"] == "reviewed"
    assert review["overall_assessment"]["module_direction_is_correct"] is True
    assert review["overall_assessment"]["urgent_architecture_drift"] is False


def test_library_alignment_review_tracks_non_operational_boundary() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/library_alignment_review.yaml")
    forbidden = set(data["library_alignment_review"]["must_not_own_runtime_objects"])

    assert "client_order" in forbidden
    assert "payment" in forbidden
    assert "warehouse_stock_balance" in forbidden
    assert "uploaded_client_file_instance" in forbidden


def test_library_alignment_review_tracks_sync_manager_open_question() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/library_alignment_review.yaml")
    questions = data["library_alignment_review"]["open_blueprint_questions"]

    question_ids = {item["id"] for item in questions}

    assert "forprint_sync_manager_first_class_module" in question_ids


def test_library_prompt_dispatch_is_reviewed() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/prompt_dispatch_index.yaml")
    prompts = data["prompt_dispatch"]

    library_prompt = next(
        item
        for item in prompts
        if item["id"] == "2026-05-22-align-library-with-blueprint"
    )

    assert library_prompt["status"] == "reviewed"
    assert library_prompt["response_file"].endswith(
        "2026-05-23-forprint-library-alignment-report.md"
    )
    assert library_prompt["review_file"] == "human/library_alignment_review.md"