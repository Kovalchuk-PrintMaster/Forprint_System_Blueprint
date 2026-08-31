import hashlib
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

STANDARD = ROOT / "coordination/standards/governance/portfolio_rendering_and_content_specification_v0_1.md"
GAPS = ROOT / "coordination/internal_work/blueprint/evening_reviews/2026-08-31/open_gaps_and_deferred_decisions_v0_1.md"
SOURCE = ROOT / "coordination/internal_work/blueprint/portfolio_reviews/2026-08-31__forprint__human_intent_portfolio_source_v0_2.md"
PDF = ROOT / "coordination/internal_work/blueprint/portfolio_reviews/2026-08-31__forprint__human_intent_portfolio_v0_2.pdf"
SNAPSHOT = ROOT / "coordination/internal_work/blueprint/portfolio_reviews/2026-08-31__forprint__human_intent_portfolio_v0_2.snapshot.yaml"
RENDERER = ROOT / "scripts/portfolio/render_human_intent_portfolio.py"
INDEX = ROOT / "coordination/human_intent/index.yaml"
PYPROJECT = ROOT / "pyproject.toml"


def _all_intent_ids():
    index = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    ids = []
    for item in index["modules"]:
        ledger = yaml.safe_load(
            (ROOT / "coordination/human_intent" / item["file"]).read_text(
                encoding="utf-8"
            )
        )
        ids.extend(x["intent_id"] for x in ledger["intents"])
    return ids



def test_reportlab_is_declared_as_dev_tooling_dependency():
    text = PYPROJECT.read_text(encoding="utf-8")
    optional = text.split("[project.optional-dependencies]", 1)[1]
    dev_block = optional.split("dev", 1)[1].split("]", 1)[0]
    assert "reportlab>=4,<5" in dev_block


def test_recovered_portfolio_rendering_details_present():
    text = STANDARD.read_text(encoding="utf-8")
    for needle in [
        "top: 11 mm",
        "bottom: 12 mm",
        "Liberation Sans",
        "#2E4F88",
        "#DDE8F7",
        "#D9E4D2",
        "#F2E7BD",
        "#E8C9CC",
        "#E1E1E1",
        "#E9C7C7",
        "status sync needed",
        "render-checked across all pages",
        "PDF SHA-256",
        "generation baseline / source refs",
    ]:
        assert needle in text


def test_explicit_gap_list_preserves_exact_unrecovered_calculator_gap():
    text = GAPS.read_text(encoding="utf-8")
    assert "GAP-6" in text
    assert "Exact Calculator external visual-configurator reference resources/URLs" in text
    assert "Do not invent replacements" in text
    for n in range(1, 10):
        assert f"GAP-{n}" in text


def test_expanded_source_contains_every_intent_as_one_record_heading():
    ids = _all_intent_ids()
    assert len(ids) == 234
    assert len(ids) == len(set(ids))

    text = SOURCE.read_text(encoding="utf-8")
    rendered_ids = re.findall(
        r"^##\s+[^·\n]+\s+·\s+(HI-[A-Z0-9_-]+)\s*$",
        text,
        flags=re.MULTILINE,
    )

    assert len(rendered_ids) == 234
    assert len(rendered_ids) == len(set(rendered_ids))
    assert set(rendered_ids) == set(ids)


def test_pdf_and_snapshot_match():
    assert PDF.is_file()
    assert PDF.stat().st_size > 10000
    assert PDF.read_bytes().startswith(b"%PDF")

    snapshot = yaml.safe_load(SNAPSHOT.read_text(encoding="utf-8"))
    assert snapshot["human_intent_count"] == 234
    assert snapshot["human_intent_coverage"] == "complete"
    assert snapshot["pdf_sha256"] == hashlib.sha256(PDF.read_bytes()).hexdigest()


def test_persistent_renderer_present():
    text = RENDERER.read_text(encoding="utf-8")
    assert "expanded portfolio source coverage failure" in text
    assert "LiberationSans-Regular.ttf" in text
    assert "12 * mm" in text
    assert "11 * mm" in text
