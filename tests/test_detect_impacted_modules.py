from pathlib import Path

from scripts.detect_impacted_modules import detect_impacted


def test_detect_material_catalog_impacts_calculator_and_prepress() -> None:
    root = Path(__file__).resolve().parents[1]
    result = detect_impacted(["material_catalog"], root)
    impacted = {item["module_id"] for item in result["impacted_modules"]}
    assert "calculator_engine" in impacted
    assert "forprint_prepress_hub" in impacted
    assert "warehouse_service" in impacted
