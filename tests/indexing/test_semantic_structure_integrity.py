import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_semantic_structure_validator_passes() -> None:
    result = subprocess.run(
        [
            str(ROOT / ".venv_blueprint/bin/python"),
            "scripts/indexing/validate_semantic_structure.py",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BLUEPRINT_SEMANTIC_STRUCTURE=PASS" in result.stdout


def test_current_human_docs_are_consolidated() -> None:
    assert not (ROOT / "human").exists()

    documents = _load(ROOT / "indexes/documents.yaml")
    current = {
        item["path"] for item in documents["current_human_architecture"]
    }
    assert current == {
        "docs/architecture/system_architecture.md",
        "docs/architecture/module_boundaries.md",
        "docs/architecture/integration_architecture.md",
    }


def test_legacy_archive_preserves_all_old_human_sources() -> None:
    archive = _load(
        ROOT
        / "coordination/internal_work/blueprint/legacy_alignment/index.yaml"
    )
    human = [
        item
        for item in archive["artifacts"]
        if item["original_path"].startswith("human/")
    ]
    assert len(human) == 25


def test_system_detail_map_uses_canonical_registry_labels() -> None:
    text = (ROOT / "diagrams/system_detail_map.mmd").read_text(encoding="utf-8")

    assert "OperationalRegistry[ForPrint Operations Control Registry<br/>" in text
    assert "Accounting[ForPrint Accounting Registry Service<br/>" in text
    assert "OperationalRegistry[ForPrint Operational Registry<br/>" not in text
    assert "Accounting[Accounting Registry Service<br/>" not in text


def test_repository_knowledge_distribution_is_declared_derived() -> None:
    data = _load(
        ROOT
        / "coordination/templates/repository_knowledge_template/"
        "derivation_manifest.yaml"
    )
    assert data["authority"] == "none"
    assert data["canonical_root"] == "coordination/repository_knowledge/"
    assert len(data["derivations"]) == 6
