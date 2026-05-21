from pathlib import Path

from scripts.blueprint_utils import load_yaml

ALLOWED_DIRECTORY_STATUSES = {
    "active_development",
    "active_development_legacy_rich",
    "directory_created_empty",
    "external_active_development",
    "planned",
    "future",
}


def test_project_directories_reference_known_modules() -> None:
    modules = load_yaml(Path("machine/modules.yaml"))["modules"]
    known_module_ids = {module["id"] for module in modules}

    project_directories = load_yaml(Path("machine/project_directories.yaml"))["directories"]

    for item in project_directories:
        assert item["module_id"] in known_module_ids
        assert item["status"] in ALLOWED_DIRECTORY_STATUSES
        assert item["path"].startswith("/")
        assert item["recommended_next_action"]
