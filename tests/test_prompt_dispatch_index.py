from pathlib import Path

import yaml

from scripts.validate_prompt_dispatch_index import validate_prompt_dispatch_index


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_prompt_dispatch_index_is_valid() -> None:
    root = Path(__file__).resolve().parents[1]

    result = validate_prompt_dispatch_index(root=root)

    assert result.ok, result.errors


def test_prompt_dispatch_references_known_modules() -> None:
    root = Path(__file__).resolve().parents[1]

    modules_data = _load_yaml(root / "machine/modules.yaml")
    index_data = _load_yaml(root / "machine/prompt_dispatch_index.yaml")

    known_modules = {item["id"] for item in modules_data["modules"]}

    for item in index_data["prompt_dispatch"]:
        assert item["target_module"] in known_modules


def test_prompt_dispatch_prompt_files_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    index_data = _load_yaml(root / "machine/prompt_dispatch_index.yaml")

    for item in index_data["prompt_dispatch"]:
        assert (root / item["prompt_file"]).exists()