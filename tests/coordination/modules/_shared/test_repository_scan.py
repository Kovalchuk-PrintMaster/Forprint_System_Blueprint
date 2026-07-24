from pathlib import Path

from scripts.coordination.modules._shared.repository_scan import scan_repository


def test_repository_scan_reports_make_and_python_inventory() -> None:
    root = Path(__file__).resolve().parents[4]
    result = scan_repository(
        root,
        workflow_index_path=(
            "coordination/modules/forprint_system_blueprint/workflows/"
            "workflow_index.yaml"
        ),
    )

    assert result["files"]["total"] > 0
    assert result["python"]["files"] > 0
    assert result["python"]["parse_failures"] == 0
    assert "check-report" in result["make"]["targets"]
    assert result["workflows"]["total"] >= 2
