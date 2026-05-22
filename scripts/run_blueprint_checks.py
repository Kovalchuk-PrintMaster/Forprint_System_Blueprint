# python scripts/run_blueprint_checks.py
"""
📄 Назва: run_blueprint_checks.py

🧠 Призначення:
Запускає основні перевірки ForPrint System Blueprint і виводить
людинозрозумілий табличний звіт у термінал.

Головний результат:
- кольорова таблиця в терміналі;
- JSON-звіт: reports/blueprint_check_report.json;
- Markdown-звіт: reports/blueprint_check_report.md.

🔗 Залежності:
Залежить від:
- ruff;
- pytest;
- scripts/validate_blueprint.py;
- scripts/generate_mermaid.py;
- scripts/generate_module_guides.py;
- scripts/validate_module_manifest.py;
- module_manifests/examples/calculator_engine.forprint_module_manifest.example.yaml.

Від цього скрипта залежать:
- ручний архітектурний контроль;
- майбутній Project Inspector;
- швидкий огляд стану Blueprint перед комітом.

🗂 Шляхи / налаштування:
- reports/blueprint_check_report.json
- reports/blueprint_check_report.md
- module_manifests/examples/calculator_engine.forprint_module_manifest.example.yaml

🔍 Аудит і рекомендації:
Це не заміна `make check`, а більш зручна людиноорієнтована оболонка
над тими самими перевірками.

✅ Актуальність:
Працює без зовнішніх UI-бібліотек. Кольори реалізовані через ANSI-коди,
щоб не тягнути додаткову залежність на Rich.

📦 Пропозиції на майбутнє:
- додати режим `--json-only`;
- додати профілі перевірок;
- додати окрему секцію warnings;
- підключити цей звіт до майбутнього ForPrint Project Inspector.

▶️ Приклади запуску:
  - python scripts/run_blueprint_checks.py
  - python scripts/run_blueprint_checks.py --no-color
  - python scripts/run_blueprint_checks.py --stop-on-fail
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
JSON_REPORT_PATH = REPORTS_DIR / "blueprint_check_report.json"
MARKDOWN_REPORT_PATH = REPORTS_DIR / "blueprint_check_report.md"

STATUS_OK = "OK"
STATUS_WARNING = "WARNING"
STATUS_FAILED = "FAILED"

COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"


@dataclass(frozen=True)
class CheckDefinition:
    """Опис однієї перевірки, яку треба виконати."""

    check_id: str
    title: str
    expected_result: str
    command: list[str]


@dataclass(frozen=True)
class CheckResult:
    """Результат виконання однієї перевірки."""

    check_id: str
    title: str
    expected_result: str
    status: str
    return_code: int
    duration_sec: float
    command: list[str]
    stdout_tail: str
    stderr_tail: str


def build_checks() -> list[CheckDefinition]:
    """Повертає список перевірок Blueprint.

    Побічні ефекти: немає.
    """

    python = sys.executable
    return [
        CheckDefinition(
            check_id="ruff_lint",
            title="Ruff lint",
            expected_result="Немає lint-помилок у scripts/tests",
            command=[python, "-m", "ruff", "check", "scripts", "tests"],
        ),
        CheckDefinition(
            check_id="pytest",
            title="Pytest",
            expected_result="Усі тести проходять",
            command=[python, "-m", "pytest", "-q"],
        ),
        CheckDefinition(
            check_id="blueprint_validation",
            title="Blueprint validation",
            expected_result="YAML-архітектура валідна",
            command=[python, "scripts/validate_blueprint.py"],
        ),
        CheckDefinition(
            check_id="mermaid_generation",
            title="Mermaid generation",
            expected_result="Діаграми згенеровано без помилок",
            command=[python, "scripts/generate_mermaid.py"],
        ),
        CheckDefinition(
            check_id="module_guides_generation",
            title="Module guides generation",
            expected_result="Module guides згенеровано",
            command=[python, "scripts/generate_module_guides.py"],
        ),
        CheckDefinition(
            check_id="module_manifest_validation",
            title="Module manifest validation",
            expected_result="Example manifest відповідає Blueprint",
            command=[
                python,
                "scripts/validate_module_manifest.py",
                "module_manifests/examples/calculator_engine.forprint_module_manifest.example.yaml",
            ],
        ),
    ]


def detect_status(return_code: int, combined_output: str) -> str:
    """Визначає статус перевірки за кодом повернення і текстом виводу."""

    if return_code != 0:
        return STATUS_FAILED

    lowered = combined_output.lower()
    if "warning" in lowered or "⚠" in combined_output:
        return STATUS_WARNING

    return STATUS_OK


def tail_text(text: str, max_lines: int = 8) -> str:
    """Повертає останні рядки тексту для компактного звіту."""

    lines = text.strip().splitlines()
    if not lines:
        return ""
    return "\n".join(lines[-max_lines:])


def run_one_check(check: CheckDefinition) -> CheckResult:
    """Запускає одну перевірку і повертає структурований результат."""

    started = time.perf_counter()

    process = subprocess.run(
        check.command,
        cwd=PROJECT_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )

    duration = time.perf_counter() - started
    combined_output = f"{process.stdout}\n{process.stderr}"
    status = detect_status(process.returncode, combined_output)

    return CheckResult(
        check_id=check.check_id,
        title=check.title,
        expected_result=check.expected_result,
        status=status,
        return_code=process.returncode,
        duration_sec=duration,
        command=check.command,
        stdout_tail=tail_text(process.stdout),
        stderr_tail=tail_text(process.stderr),
    )


def color_status(status: str, use_color: bool) -> str:
    """Повертає кольорове представлення статусу."""

    if not use_color:
        return status

    if status == STATUS_OK:
        return f"{COLOR_GREEN}{status}{COLOR_RESET}"
    if status == STATUS_WARNING:
        return f"{COLOR_YELLOW}{status}{COLOR_RESET}"
    if status == STATUS_FAILED:
        return f"{COLOR_RED}{status}{COLOR_RESET}"

    return status


def format_duration(seconds: float) -> str:
    """Форматує тривалість у секундах."""

    return f"{seconds:.2f}s"


def render_text_table(results: list[CheckResult], use_color: bool = True) -> str:
    """Формує табличний terminal-звіт без зовнішніх бібліотек."""

    headers = ["Перевірка", "Очікуваний результат", "Статус", "Час"]
    rows = [
        [
            result.title,
            result.expected_result,
            color_status(result.status, use_color),
            format_duration(result.duration_sec),
        ]
        for result in results
    ]

    raw_rows = [
        [result.title, result.expected_result, result.status, format_duration(result.duration_sec)]
        for result in results
    ]

    widths = [
        max(len(headers[column]), *(len(row[column]) for row in raw_rows))
        for column in range(len(headers))
    ]

    def separator(left: str, middle: str, right: str) -> str:
        parts = ["─" * (width + 2) for width in widths]
        return left + middle.join(parts) + right

    def row(values: list[str]) -> str:
        # Окремий цикл потрібен, бо colored status має ANSI-коди і реальна довжина відрізняється.
        final_cells: list[str] = []
        
        for index, value in enumerate(values):
            raw_value = value
            if index == 2:
                raw_value = value.replace(COLOR_GREEN, "").replace(COLOR_YELLOW, "")
                raw_value = raw_value.replace(COLOR_RED, "").replace(COLOR_RESET, "")
            final_cells.append(f" {value}{' ' * (widths[index] - len(raw_value))} ")
        return "│" + "│".join(final_cells) + "│"

    title = "ForPrint System Blueprint — check report"
    lines = [
        f"{COLOR_BOLD}{title}{COLOR_RESET}" if use_color else title,
        separator("┌", "┬", "┐"),
        row(headers),
        separator("├", "┼", "┤"),
    ]

    lines.extend(row(values) for values in rows)
    lines.append(separator("└", "┴", "┘"))

    return "\n".join(lines)


def summarize_results(results: list[CheckResult]) -> dict[str, int]:
    """Підраховує кількість OK/WARNING/FAILED."""

    return {
        STATUS_OK: sum(1 for result in results if result.status == STATUS_OK),
        STATUS_WARNING: sum(1 for result in results if result.status == STATUS_WARNING),
        STATUS_FAILED: sum(1 for result in results if result.status == STATUS_FAILED),
    }


def render_markdown_report(results: list[CheckResult]) -> str:
    """Формує Markdown-звіт для reports/."""

    summary = summarize_results(results)
    generated_at = datetime.now(UTC).isoformat()

    lines = [
        "# ForPrint System Blueprint — Check Report",
        "",
        f"Generated at: `{generated_at}`",
        "",
        "## Summary",
        "",
        f"- OK: `{summary[STATUS_OK]}`",
        f"- WARNING: `{summary[STATUS_WARNING]}`",
        f"- FAILED: `{summary[STATUS_FAILED]}`",
        "",
        "## Checks",
        "",
        "| Check | Expected result | Status | Duration | Return code |",
        "|---|---|---:|---:|---:|",
    ]

    for result in results:
        lines.append(
            "| "
            f"{result.title} | "
            f"{result.expected_result} | "
            f"{result.status} | "
            f"{format_duration(result.duration_sec)} | "
            f"{result.return_code} |"
        )

    failed = [result for result in results if result.status == STATUS_FAILED]
    warnings = [result for result in results if result.status == STATUS_WARNING]

    if warnings:
        lines.extend(["", "## Warnings", ""])
        for result in warnings:
            lines.extend(
                [
                    f"### {result.title}",
                    "",
                    "```text",
                    result.stdout_tail or result.stderr_tail or "No warning details captured.",
                    "```",
                    "",
                ]
            )

    if failed:
        lines.extend(["", "## Failures", ""])
        for result in failed:
            lines.extend(
                [
                    f"### {result.title}",
                    "",
                    "Command:",
                    "",
                    "```bash",
                    " ".join(result.command),
                    "```",
                    "",
                    "STDOUT tail:",
                    "",
                    "```text",
                    result.stdout_tail or "<empty>",
                    "```",
                    "",
                    "STDERR tail:",
                    "",
                    "```text",
                    result.stderr_tail or "<empty>",
                    "```",
                    "",
                ]
            )

    return "\n".join(lines) + "\n"


def write_reports(results: list[CheckResult]) -> None:
    """Записує JSON і Markdown-звіт у reports/.

    Побічні ефекти:
    - створює reports/ за потреби;
    - оновлює blueprint_check_report.json;
    - оновлює blueprint_check_report.md.
    """

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "summary": summarize_results(results),
        "results": [asdict(result) for result in results],
    }

    JSON_REPORT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    MARKDOWN_REPORT_PATH.write_text(render_markdown_report(results), encoding="utf-8")


def build_cli() -> argparse.ArgumentParser:
    """Створює CLI-парсер."""

    parser = argparse.ArgumentParser(
        description="Run ForPrint System Blueprint checks and print a readable report."
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors in terminal output.",
    )
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="Stop after first failed check.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Основна точка входу."""

    args = build_cli().parse_args(argv)
    use_color = not args.no_color

    print("🔎 Running ForPrint System Blueprint checks...")

    results: list[CheckResult] = []
    for check in build_checks():
        result = run_one_check(check)
        results.append(result)

        status_text = color_status(result.status, use_color)
        print(f"  - {check.title}: {status_text} ({format_duration(result.duration_sec)})")

        if args.stop_on_fail and result.status == STATUS_FAILED:
            break

    write_reports(results)

    print()
    print(render_text_table(results, use_color=use_color))
    print()
    print(f"📄 JSON report: {JSON_REPORT_PATH}")
    print(f"📄 Markdown report: {MARKDOWN_REPORT_PATH}")

    summary = summarize_results(results)
    if summary[STATUS_FAILED] > 0:
        print("❌ Check report completed with failures.")
        return 1

    if summary[STATUS_WARNING] > 0:
        print("⚠️ Check report completed with warnings.")
        return 0

    print("✅ Check report completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())