from pathlib import Path

from scripts.validate_blueprint import validate_project


def test_blueprint_validation_passes() -> None:
    root = Path(__file__).resolve().parents[1]
    result = validate_project(root)
    assert result.ok, result.errors
