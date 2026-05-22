from pathlib import Path

import yaml

from scripts.validate_module_manifest import validate_manifest


def test_calculator_manifest_example_is_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "module_manifests/examples/calculator_engine.forprint_module_manifest.example.yaml"

    result = validate_manifest(manifest_path, root=root)

    assert result.ok, result.errors


def test_manifest_rejects_forbidden_ownership(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = {
        "module_id": "calculator_engine",
        "title": "Bad Calculator Manifest",
        "status": "test",
        "implementation_root": "/tmp/calculator_engine",
        "responsibilities": {
            "owns": ["client"],
            "consumes": [],
            "provides": [],
            "must_not_own": [],
        },
        "contracts": {"consumes": [], "provides": []},
        "reports": {"status_report": "reports/forprint_module_status.json"},
    }
    manifest_path = tmp_path / "forprint_module_manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, allow_unicode=True), encoding="utf-8")

    result = validate_manifest(manifest_path, root=root)

    assert not result.ok
    assert any("claims forbidden ownership" in error for error in result.errors)