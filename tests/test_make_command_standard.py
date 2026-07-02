from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT / "coordination" / "standards" / "make_command_standard.md"

REQUIRED_TARGETS = (
    "install",
    "lint",
    "lint-fix",
    "test",
    "check",
    "check-report",
    "status-report",
    "report-clean",
    "blueprint-pull",
    "blueprint-check",
    "blueprint-sync-directives",
    "blueprint-instruction-list",
    "blueprint-instruction-check",
    "blueprint-instruction-sync",
    "blueprint-instruction",
    "blueprint-standards-list",
    "blueprint-standards-check",
    "blueprint-standards-sync",
    "blueprint-standards",
    "blueprint-prompts-list",
    "blueprint-prompts-check",
    "blueprint-prompts-sync",
    "blueprint-prompts",
    "blueprint-sync",
    "prompt-read",
    "coordination-check",
    "coordination-fix",
    "module-policy-check",
    "governance-check",
    "completion-packet-validate",
    "completion-packet-apply",
    "completion-packet-check",
    "module-start",
    "module-sync",
    "module-validate",
    "module-finish",
)

REQUIRED_BLOCKS = [
    "00 Environment / constants",
    "01 Help / navigation",
    "02 Operator entrypoints / Blueprint-first workflow",
    "03 Blueprint repository synchronization",
    "04 Blueprint instruction intake",
    "05 Blueprint standards and policies",
    "06 Blueprint outgoing prompts / prompt queue",
    "07 Blueprint document awareness",
    "08 Module coordination metadata",
    "09 Module governance / policy checks",
    "10 Module install / bootstrap",
    "11 Module environment / local configuration",
    "12 Runtime control / process lifecycle",
    "13 Infrastructure / local services",
    "14 Database / storage / migrations",
    "15 Data import / export / fixtures",
    "16 External adapters / sandbox integrations",
    "17 Local previews / operator workflows",
    "18 Observability / diagnostics / logs",
    "19 Syntax / formatting / lint",
    "20 Tests",
    "21 Validation / check reports",
    "22 Status reports / generated reports / cleanup",
    "23 Completion packet / prompt finalization",
    "24 Git / release / commit helpers",
    "90 Module-specific helpers",
]

COMPOSITE_TARGETS = (
    "blueprint-instruction",
    "blueprint-standards",
    "blueprint-prompts",
    "blueprint-sync",
    "module-start",
    "module-sync",
    "module-validate",
    "module-finish",
    "completion-packet-check",
)


def _standard_text() -> str:
    return STANDARD.read_text(encoding="utf-8")


def test_make_command_standard_exists() -> None:
    assert STANDARD.exists()


def test_make_command_standard_has_balanced_code_fences() -> None:
    text = _standard_text()

    assert text.count("```") % 2 == 0


def test_make_command_standard_mentions_required_targets() -> None:
    text = _standard_text()

    for target in REQUIRED_TARGETS:
        assert (
            f"make {target}" in text
            or f"## {target}" in text
            or f"### {target}" in text
        )


def test_make_command_standard_mentions_recommended_blocks() -> None:
    text = _standard_text()

    for block_name in REQUIRED_BLOCKS:
        assert block_name in text


def test_make_command_standard_requires_visual_block_separators() -> None:
    text = _standard_text()

    assert "# =============================================================================" in text
    assert "START" in text
    assert "FINISH" in text
    assert "Purpose:" in text
    assert "Result:" in text


def test_make_command_standard_defines_make_first_workflow() -> None:
    text = _standard_text()

    assert "Make-first workflow rule" in text
    assert "Raw commands are implementation details." in text
    assert "make module-start" in text
    assert "make module-validate" in text
    assert "make module-finish PACKET=" in text


def test_make_command_standard_defines_composite_targets() -> None:
    text = _standard_text()

    assert "Composite target rule" in text
    assert "$(MAKE)" in text

    for target in COMPOSITE_TARGETS:
        assert target in text


def test_make_command_standard_uses_blueprint_root_variable() -> None:
    text = _standard_text()

    assert "$(BLUEPRINT_ROOT)" in text


def test_make_command_standard_allows_optional_colors() -> None:
    text = _standard_text()

    assert "Optional console colors" in text
    assert "COLOR_GREEN" in text
    assert "NO_COLOR" in text
