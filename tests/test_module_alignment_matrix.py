from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_alignment_matrix_references_known_modules() -> None:
    root = Path(__file__).resolve().parents[1]

    modules_data = _load_yaml(root / "machine/modules.yaml")
    matrix_data = _load_yaml(root / "machine/module_alignment_matrix.yaml")

    known_modules = {item["id"] for item in modules_data["modules"]}
    alignment_items = matrix_data["module_alignment"]

    assert alignment_items, "module_alignment_matrix.yaml must not be empty"

    for item in alignment_items:
        assert item["module_id"] in known_modules


def test_alignment_matrix_has_required_fields() -> None:
    root = Path(__file__).resolve().parents[1]
    matrix_data = _load_yaml(root / "machine/module_alignment_matrix.yaml")

    required_fields = {
        "module_id",
        "correct_role",
        "priority",
        "current_status",
        "drift_risk",
        "required_next_action",
        "notes",
    }

    for item in matrix_data["module_alignment"]:
        missing = required_fields - set(item)
        assert not missing, f"{item.get('module_id')} missing fields: {sorted(missing)}"
        assert isinstance(item["notes"], list)
        assert item["notes"], f"{item['module_id']} must have at least one note"