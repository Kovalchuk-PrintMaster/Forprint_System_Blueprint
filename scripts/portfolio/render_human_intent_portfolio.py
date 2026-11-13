#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "coordination/human_intent/index.yaml"
DEFAULT_SOURCE = ROOT / "coordination/internal_work/blueprint/portfolio_reviews/2026-08-31__forprint__human_intent_portfolio_source_v0_2.md"
DEFAULT_PDF = ROOT / "coordination/internal_work/blueprint/portfolio_reviews/2026-08-31__forprint__human_intent_portfolio_v0_2.pdf"
DEFAULT_SNAPSHOT = ROOT / "coordination/internal_work/blueprint/portfolio_reviews/2026-08-31__forprint__human_intent_portfolio_v0_2.snapshot.yaml"
GAP_FILE = ROOT / "coordination/internal_work/blueprint/evening_reviews/2026-08-31/open_gaps_and_deferred_decisions_v0_1.md"
SPEC = ROOT / "coordination/standards/governance/portfolio_rendering_and_content_specification_v0_1.md"

PALETTE = {
    "main_blue": "#2E4F88",
    "light_blue": "#DDE8F7",
    "AGREED": "#D9E4D2",
    "RECOVERED": "#F2E7BD",
    "PROPOSED": "#E8C9CC",
    "SYNTHETIC": "#E8C9CC",
    "GAP": "#E1E1E1",
    "attention": "#E9C7C7",
}


def load_ledgers():
    index = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    rows = []
    all_ids = []

    for item in index["modules"]:
        module_id = item["module_id"]
        ledger_path = ROOT / "coordination/human_intent" / item["file"]
        ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
        intents = ledger.get("intents", [])
        rows.append((module_id, intents))
        all_ids.extend(x["intent_id"] for x in intents)

    if len(all_ids) != len(set(all_ids)):
        raise RuntimeError("duplicate Human Intent IDs across module ledgers")

    expected_total = sum(int(x["intent_count"]) for x in index["modules"])
    if len(all_ids) != expected_total:
        raise RuntimeError(
            f"Human Intent count mismatch: ledgers={len(all_ids)} index={expected_total}"
        )

    return index, rows, all_ids


def build_markdown(index, rows, all_ids):
    rendered_ids = []
    lines = [
        "# ForPrint Human Intent Ledger + Expanded Portfolio Projection v0.2",
        "",
        "Generated: 2026-08-31",
        "",
        "**Authority note:** This document is a human review projection. Canonical authority",
        "remains in structured Blueprint governance, contracts, roadmaps, Human Intent",
        "ledgers and evidence.",
        "",
        f"**Human Intent coverage:** {len(all_ids)} / {len(all_ids)} indexed intent IDs.",
        "",
        "**Statuses:** AGREED = explicitly agreed/reconfirmed; RECOVERED = recovered from",
        "project/portfolio evidence; PROPOSED/SYNTHETIC = working synthesis; GAP = exact",
        "detail remains unknown/unrecovered.",
        "",
        "## Open GAP projection",
        "",
        "The current explicit GAP list is:",
        "",
        "`coordination/internal_work/blueprint/evening_reviews/2026-08-31/"
        "open_gaps_and_deferred_decisions_v0_1.md`",
        "",
        "Exact Calculator external visual-configurator resources/URLs remain unrecovered;",
        "do not invent replacements.",
        "",
        "## Portfolio dependency principle",
        "",
        "Human Intent entries are grouped by module and retain roadmap/context fields where",
        "present. Runtime/module status that is not proven from current evidence is",
        "represented as **status sync needed** rather than an invented percentage/step.",
        "",
    ]

    for module_id, intents in rows:
        lines += [
            f"# Module — {module_id}",
            "",
            f"Intent count: {len(intents)}",
            "",
        ]

        for entry in intents:
            iid = entry["intent_id"]
            rendered_ids.append(iid)
            status = entry.get("status", "GAP")
            text = str(entry.get("text", "")).strip()
            context = entry.get("context")
            roadmap = entry.get("roadmap")
            evidence = entry.get("evidence")

            lines.append(f"## {status} · {iid}")
            lines.append("")
            lines.append(text or "(no text)")
            lines.append("")

            if context:
                lines.append(f"- Context: {context}")
            if roadmap:
                lines.append(f"- Roadmap: `{roadmap}`")
            if evidence:
                lines.append(f"- Evidence: {evidence}")
            if context or roadmap or evidence:
                lines.append("")

    result = "\n".join(lines).rstrip() + "\n"

    if len(rendered_ids) != len(all_ids):
        raise RuntimeError(
            "expanded portfolio source coverage failure: "
            f"rendered={len(rendered_ids)} expected={len(all_ids)}"
        )

    if len(rendered_ids) != len(set(rendered_ids)):
        raise RuntimeError(
            "expanded portfolio source coverage failure: duplicate rendered intent IDs"
        )

    if set(rendered_ids) != set(all_ids):
        missing = sorted(set(all_ids) - set(rendered_ids))
        unexpected = sorted(set(rendered_ids) - set(all_ids))
        raise RuntimeError(
            "expanded portfolio source coverage failure: "
            f"missing={missing} unexpected={unexpected}"
        )

    return result


def find_font(name):
    for root in [Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]:
        if not root.exists():
            continue
        matches = list(root.rglob(name))
        if matches:
            return matches[0]
    return None


def render_pdf(rows, all_ids, output):
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import (
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except Exception as exc:
        raise RuntimeError(
            "reportlab is required for deterministic portfolio PDF rendering"
        ) from exc

    regular = find_font("LiberationSans-Regular.ttf") or find_font("DejaVuSans.ttf")
    bold = find_font("LiberationSans-Bold.ttf") or find_font("DejaVuSans-Bold.ttf")

    if not regular:
        raise RuntimeError("no Unicode-capable Liberation/DejaVu Sans font found")
    if not bold:
        bold = regular

    pdfmetrics.registerFont(TTFont("ForPrintSans", str(regular)))
    pdfmetrics.registerFont(TTFont("ForPrintSansBold", str(bold)))

    main_blue = colors.HexColor(PALETTE["main_blue"])

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "ForPrintTitle",
        parent=styles["Title"],
        fontName="ForPrintSansBold",
        fontSize=18,
        leading=22,
        textColor=main_blue,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    h1 = ParagraphStyle(
        "ForPrintH1",
        parent=styles["Heading1"],
        fontName="ForPrintSansBold",
        fontSize=14,
        leading=17,
        textColor=main_blue,
        spaceBefore=8,
        spaceAfter=6,
    )
    h2 = ParagraphStyle(
        "ForPrintH2",
        parent=styles["Heading2"],
        fontName="ForPrintSansBold",
        fontSize=10,
        leading=13,
        spaceBefore=5,
        spaceAfter=3,
    )
    body = ParagraphStyle(
        "ForPrintBody",
        parent=styles["BodyText"],
        fontName="ForPrintSans",
        fontSize=8.5,
        leading=11,
        spaceAfter=3,
        splitLongWords=True,
    )
    small = ParagraphStyle(
        "ForPrintSmall",
        parent=body,
        fontSize=7,
        leading=9,
    )

    def esc(value):
        return html.escape(str(value)).replace("\n", "<br/>")

    page_counter = {"n": 0}

    def footer(canvas, doc):
        page_counter["n"] += 1
        canvas.saveState()
        canvas.setFont("ForPrintSans", 7)
        canvas.drawCentredString(
            A4[0] / 2,
            6 * mm,
            f"ForPrint expanded human portfolio · page {page_counter['n']}",
        )
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=11 * mm,
        bottomMargin=12 * mm,
        title="ForPrint Human Intent Ledger + Expanded Portfolio Projection v0.2",
        author="ForPrint System Blueprint",
        subject="Human review projection generated from append-only Human Intent ledgers",
    )

    story = [
        Paragraph(
            "ForPrint Human Intent Ledger + Expanded Portfolio Projection v0.2",
            title,
        ),
        Paragraph("Generated 2026-08-31", body),
        Paragraph(
            "Authority note: this PDF is a human review projection; structured Blueprint "
            "governance, roadmaps, contracts, ledgers and evidence remain authority.",
            body,
        ),
        Paragraph(
            f"Human Intent coverage: <b>{len(all_ids)} / {len(all_ids)}</b> indexed IDs.",
            body,
        ),
        Spacer(1, 4),
        Paragraph(
            "Open GAP list: coordination/internal_work/blueprint/evening_reviews/"
            "2026-08-31/open_gaps_and_deferred_decisions_v0_1.md",
            small,
        ),
        Paragraph(
            "Exact Calculator external visual-configurator resources/URLs remain "
            "unrecovered. Do not invent replacements.",
            body,
        ),
        PageBreak(),
    ]

    for module_no, (module_id, intents) in enumerate(rows):
        if module_no:
            story.append(PageBreak())

        story.append(Paragraph(f"Module — {esc(module_id)}", h1))
        story.append(Paragraph(f"Intent count: {len(intents)}", small))

        for entry in intents:
            status = str(entry.get("status", "GAP"))
            iid = entry["intent_id"]
            bg = colors.HexColor(PALETTE.get(status, PALETTE["GAP"]))

            header = Table(
                [[Paragraph(f"<b>{esc(status)} · {esc(iid)}</b>", h2)]],
                colWidths=[172 * mm],
            )
            header.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), bg),
                        ("BOX", (0, 0), (-1, -1), 0.3, colors.grey),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            story.append(header)
            story.append(
                Paragraph(esc(entry.get("text", "") or "(no text)"), body)
            )

            metadata = []
            for label, key in [
                ("Context", "context"),
                ("Roadmap", "roadmap"),
                ("Evidence", "evidence"),
            ]:
                value = entry.get(key)
                if value:
                    metadata.append(f"<b>{label}:</b> {esc(value)}")

            if metadata:
                story.append(Paragraph("<br/>".join(metadata), small))

            story.append(Spacer(1, 3))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    if not output.is_file() or output.stat().st_size < 10000:
        raise RuntimeError("generated PDF missing or unexpectedly small")

    raw = output.read_bytes()
    if not raw.startswith(b"%PDF"):
        raise RuntimeError("generated artifact is not a PDF")

    page_markers = raw.count(b"/Type /Page")
    if page_markers < 2:
        raise RuntimeError("PDF page structure check failed")

    return page_markers


def write_snapshot(source, pdf, all_ids, page_markers):
    payload = {
        "schema_version": "forprint_human_intent_portfolio_snapshot_v0_1",
        "generated_at": "2026-08-31",
        "status": "human_review_projection",
        "authority": "non_authoritative_projection",
        "source": source.relative_to(ROOT).as_posix(),
        "pdf": pdf.relative_to(ROOT).as_posix(),
        "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "human_intent_count": len(all_ids),
        "human_intent_coverage": "complete",
        "pdf_page_structure_markers": page_markers,
        "generation_baseline": {
            "human_intent_index": INDEX.relative_to(ROOT).as_posix(),
            "gap_list": GAP_FILE.relative_to(ROOT).as_posix(),
            "rendering_specification": SPEC.relative_to(ROOT).as_posix(),
            "renderer": Path(__file__).relative_to(ROOT).as_posix(),
            "preferred_margins_mm": {
                "left": 12,
                "right": 12,
                "top": 11,
                "bottom": 12,
            },
            "font_baseline": "Liberation Sans or metrically safe Unicode-capable equivalent",
        },
    }

    DEFAULT_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_SNAPSHOT.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    args = parser.parse_args()

    index, rows, all_ids = load_ledgers()

    source = args.source
    pdf = args.pdf
    source.parent.mkdir(parents=True, exist_ok=True)
    pdf.parent.mkdir(parents=True, exist_ok=True)

    markdown = build_markdown(index, rows, all_ids)
    source.write_text(markdown, encoding="utf-8")

    page_markers = render_pdf(rows, all_ids, pdf)
    write_snapshot(source, pdf, all_ids, page_markers)

    print(f"HUMAN_INTENT_TOTAL={len(all_ids)}")
    print(f"HUMAN_INTENT_SOURCE_COVERAGE={len(all_ids)}/{len(all_ids)}")
    print(f"PORTFOLIO_SOURCE={source}")
    print(f"PORTFOLIO_PDF={pdf}")
    print(f"PORTFOLIO_PDF_SHA256={hashlib.sha256(pdf.read_bytes()).hexdigest()}")
    print(f"PORTFOLIO_PDF_PAGE_MARKERS={page_markers}")
    print("PORTFOLIO_RENDER=PASS")


if __name__ == "__main__":
    main()
