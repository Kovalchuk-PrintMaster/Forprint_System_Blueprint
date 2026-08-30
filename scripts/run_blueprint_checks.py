#!/usr/bin/env python3
"""Run Blueprint checks through a structured compact/full reporting pipeline.

Architecture and operations:
- docs/architecture/blueprint_check_reporting_architecture.md
- docs/operations/blueprint_check_reporting_runbook.md
- docs/operations/blueprint_check_reporting_recovery.md
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from scripts.reporting.artifact_writer import (
    render_markdown_report as render_structured_markdown_report,
)
from scripts.reporting.artifact_writer import (
    write_report_artifacts,
)
from scripts.reporting.console_summary import render_compact_report
from scripts.reporting.models import CheckDefinition, CheckResult
from scripts.reporting.statuses import (
    STATUS_FAILED,
    STATUS_OK,
    STATUS_WARNING,
    colorize,
    detect_status,
    has_warning_signal,
    status_token,
)
from scripts.reporting.statuses import (
    summarize_results as summarize_report_results,
)
from scripts.reporting.table_renderer import TableRow, render_boxed_table

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Backward-compatible public API
#
# Existing Blueprint tests and local tools imported these names directly from
# scripts.run_blueprint_checks. Keep the facade stable while the implementation
# is split into scripts.reporting components.


def format_duration(seconds: float) -> str:
    """Format duration using the legacy public helper."""

    return f"{seconds:.2f}s"


def color_status(status: str, use_color: bool) -> str:
    """Render a status using semantic tokens and the legacy helper name."""

    return colorize(status, status_token(status), use_color=use_color)


def summarize_results(results: list[CheckResult]) -> dict[str, int]:
    """Return the legacy status-count mapping."""

    summary = summarize_report_results(results)
    return {
        STATUS_OK: summary.passed,
        STATUS_WARNING: summary.warnings,
        STATUS_FAILED: summary.failed,
    }


def render_text_table(
    results: list[CheckResult],
    use_color: bool = True,
) -> str:
    """Render the original single-table public view for compatible callers."""

    rows = tuple(
        TableRow(
            values=(
                result.title,
                result.expected_result,
                result.status,
                format_duration(result.duration_seconds),
            ),
            token=status_token(result.status),
        )
        for result in results
    )

    table = render_boxed_table(
        headers=("Перевірка", "Очікуваний результат", "Статус", "Час"),
        widths=(30, 54, 9, 8),
        rows=rows,
        use_color=use_color,
    )
    return "\n".join(
        [
            "ForPrint System Blueprint — check report",
            table,
        ]
    )


def render_markdown_report(results: list[CheckResult]) -> str:
    """Render the legacy Markdown helper through the structured implementation."""

    summary = summarize_report_results(results)
    return render_structured_markdown_report(
        results,
        summary,
        generated_at=datetime.now(UTC).isoformat(),
    )


def write_reports(results: list[CheckResult]) -> None:
    """Write the legacy default JSON/Markdown report artifacts."""

    summary = summarize_report_results(results)
    write_report_artifacts(
        project_root=PROJECT_ROOT,
        results=results,
        summary=summary,
        include_full_log=summary.failed > 0 or summary.warnings > 0,
    )


def build_checks() -> list[CheckDefinition]:
    """Return the authoritative Blueprint check catalog."""

    python = sys.executable
    return [
        CheckDefinition(
            check_id="ruff_lint",
            title="Ruff lint",
            expected_result="No lint errors in scripts/tests/tools",
            command=(python, "-m", "ruff", "check", "scripts", "tests", "tools"),
            group="core_quality",
        ),
        CheckDefinition(
            check_id="pytest",
            title="Pytest",
            expected_result="All tests pass",
            command=(python, "-m", "pytest", "-q"),
            group="core_quality",
        ),
        CheckDefinition(
            check_id="current_release_projection_validation",
            title="Current release projection",
            expected_result=(
                "Authoritative current coordination release is valid and "
                "legacy compatibility is non-blocking"
            ),
            command=(
                python,
                "scripts/coordination/current_release_projection_v0_1.py",
                "--root",
                ".",
            ),
            group="core_quality",
        ),
        CheckDefinition(
            check_id="blueprint_validation",
            title="Blueprint validation",
            expected_result="Architecture metadata is valid",
            command=(python, "scripts/validate_blueprint.py"),
            group="core_quality",
        ),
        CheckDefinition(
            check_id="module_manifest_validation",
            title="Module manifest",
            expected_result="Example module manifest is valid",
            command=(
                python,
                "scripts/validate_module_manifest.py",
                "module_manifests/examples/calculator_engine.forprint_module_manifest.example.yaml",
            ),
            group="core_quality",
        ),
        CheckDefinition(
            check_id="semantic_structure_validation",
            title="Semantic structure",
            expected_result="Current, derived and historical Blueprint surfaces are separated",
            command=(python, "scripts/indexing/validate_semantic_structure.py"),
            group="coordination",
        ),
        CheckDefinition(
            check_id="outgoing_prompts_validation",
            title="Outgoing prompts",
            expected_result="Prompt indexes and files are valid",
            command=(python, "scripts/validate_outgoing_prompts.py"),
            group="coordination",
        ),
        CheckDefinition(
            check_id="prompt_queue_validation",
            title="Prompt queue",
            expected_result="Prompt Queue v0.2 indexes are valid",
            command=(python, "scripts/coordination/validate_prompt_queue.py"),
            group="coordination",
        ),
        CheckDefinition(
            check_id="document_manifest_validation",
            title="Document manifest",
            expected_result="Coordination manifest builds read-only",
            command=(
                python,
                "scripts/coordination/build_document_manifest.py",
                "--no-write",
            ),
            group="coordination",
        ),
        CheckDefinition(
            check_id="document_awareness_dashboard",
            title="Awareness dashboard",
            expected_result="Library awareness dashboard renders",
            command=(
                python,
                "scripts/coordination/render_document_awareness_dashboard.py",
                "--module",
                "forprint_library",
                "--no-color",
                "--limit",
                "20",
            ),
            group="coordination",
        ),
        CheckDefinition(
            check_id="context_bundle_validation",
            title="Context bundle",
            expected_result="Bootstrap context bundle builds read-only",
            command=(
                python,
                "scripts/coordination/build_context_bundle.py",
                "--module",
                "forprint_library",
                "--scope",
                "bootstrap",
                "--limit",
                "10",
                "--no-write",
            ),
            group="coordination",
        ),
        CheckDefinition(
            check_id="module_roadmap_validation",
            title="Roadmap validation",
            expected_result="Library roadmap is valid",
            command=(
                python,
                "scripts/coordination/validate_module_roadmap.py",
                "--module",
                "forprint_library",
            ),
            group="coordination",
        ),
        CheckDefinition(
            check_id="module_roadmap_dashboard",
            title="Roadmap dashboard",
            expected_result="Library roadmap dashboard renders",
            command=(
                python,
                "scripts/coordination/render_module_roadmap_dashboard.py",
                "--module",
                "forprint_library",
                "--before-current",
                "2",
                "--after-current",
                "5",
                "--no-color",
            ),
            group="coordination",
        ),
        CheckDefinition(
            check_id="module_roadmap_summary",
            title="Roadmap summary",
            expected_result="Configured roadmap summary renders",
            command=(
                python,
                "scripts/coordination/render_module_roadmap_dashboard.py",
                "--modules",
                "forprint_library",
                "--no-color",
            ),
            group="coordination",
        ),
        CheckDefinition(
            check_id="completion_finalization_tests",
            title="Completion workflow",
            expected_result="Completion intake/finalization tests pass",
            command=(
                python,
                "-m",
                "pytest",
                "-q",
                "tests/coordination/test_module_completion_finalization.py",
            ),
            group="coordination",
        ),
        CheckDefinition(
            check_id="completion_intake_check_tests",
            title="Completion discovery/intake v0.4",
            expected_result="Promoted v0.4 completion discovery/intake and review boundary are read-only",
            command=(
                python,
                "-m",
                "pytest",
                "-q",
                "tests/validation/test_v0_4_completion_discovery_and_intake.py",
                "tests/validation/test_v0_4_completion_packet.py",
                "tests/validation/test_v0_4_completion_outbox.py",
                "tests/validation/test_v0_4_review_transaction_module_schema_plan.py",
            ),
            group="coordination",
        ),
        CheckDefinition(
            check_id="module_governance_audit",
            title="Module governance audit",
            expected_result="Governance audit is clean and read-only",
            command=(python, "scripts/audit_module_governance.py", "--no-write"),
            group="coordination",
        ),
        CheckDefinition(
            check_id="completion_packet_template_validation",
            title="Completion packet template validation",
            expected_result="Completion packet contract is valid",
            command=(python, "scripts/validate_completion_packet_template.py"),
            group="coordination",
        ),
        CheckDefinition(
            check_id="module_workflow_validation",
            title="Module workflows",
            expected_result="Workflow registry and control files are valid",
            command=(
                python,
                "-m",
                "scripts.coordination.modules.module_workflow_cli",
                "--root",
                ".",
                "check",
            ),
            group="coordination",
        ),
        CheckDefinition(
            check_id="mermaid_generation",
            title="Mermaid generation",
            expected_result="Architecture diagrams generate",
            command=(python, "scripts/generate_mermaid.py"),
            group="documentation",
        ),
        CheckDefinition(
            check_id="diagrams_index_validation",
            title="Diagrams index",
            expected_result="Generated diagrams are indexed",
            command=(python, "scripts/validation/validate_diagrams_index.py"),
            group="documentation",
        ),
        CheckDefinition(
            check_id="module_guides_generation",
            title="Module guides",
            expected_result="Module guides generate",
            command=(python, "scripts/generate_module_guides.py"),
            group="documentation",
        ),
        CheckDefinition(
            check_id="markdown_fence_validation",
            title="Markdown fences",
            expected_result="No new Markdown fence defects beyond baseline",
            command=(
                python,
                "scripts/validation/validate_markdown_fences.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="standards_index_validation",
            title="Standards index",
            expected_result="Standards index is valid",
            command=(python, "scripts/validate_standards_index.py"),
            group="documentation",
        ),
        CheckDefinition(
            check_id="module_workflow_adoption_matrix_validation",
            title="Workflow adoption matrix",
            expected_result="Command adoption matrix semantics are valid",
            command=(
                python,
                "scripts/validation/validate_module_workflow_adoption_matrix.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="mutation_builder_contract_validation",
            title="Mutation builder contract",
            expected_result=("Mutation builders follow predictable preflight and rollback rules"),
            command=(
                python,
                "scripts/validation/validate_mutation_builder_contract.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="b2_persistence_boundary_validation",
            title="B2 persistence boundary",
            expected_result=(
                "Source-of-truth, migration, retention and disabled-runtime boundaries are valid"
            ),
            command=(
                python,
                "scripts/validation/validate_b2_persistence_boundary.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="q1_clarification_question_lifecycle_validation",
            title="Q1 clarification lifecycle",
            expected_result=(
                "Question lifecycle, identity, prompt-coupling and deferred-boundary "
                "semantics are valid"
            ),
            command=(
                python,
                "scripts/validation/validate_q1_clarification_question_lifecycle.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="q2_bounded_clarification_and_escalation_validation",
            title="Q2 bounded clarification",
            expected_result=(
                "Five unresolved rounds are bounded per question thread and "
                "round-five escalation is deterministic/evidence-complete"
            ),
            command=(
                python,
                "scripts/validation/validate_q2_bounded_clarification_and_escalation.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="q3_execution_blocker_taxonomy_validation",
            title="Q3 execution blocker taxonomy",
            expected_result=(
                "Execution blocker reasons, scope blocking and separation from "
                "unable-to-execute/RETURN/HOLD are valid"
            ),
            command=(
                python,
                "scripts/validation/validate_q3_execution_blocker_taxonomy.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="q4_immutable_prompt_adjustment_and_decision_validation",
            title="Q4 immutable prompt decisions",
            expected_result=(
                "Released prompts stay immutable while correlated decisions/adjustments "
                "preserve explicit execution and acceptance effects"
            ),
            command=(
                python,
                "scripts/validation/validate_q4_immutable_prompt_adjustment_and_decision.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="q5_common_coordination_event_envelope_validation",
            title="Q5 coordination event envelope",
            expected_result=(
                "Common immutable coordination event envelope, correlation/causation "
                "and idempotency semantics are valid"
            ),
            command=(
                python,
                "scripts/validation/validate_q5_common_coordination_event_envelope.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="q6_operator_attention_semantics_validation",
            title="Q6 operator attention semantics",
            expected_result=("Operator-attention reasons, lifecycle and transport-independent semantics are valid"),
            command=(python, "scripts/validation/validate_q6_operator_attention_semantics.py"),
            group="documentation",
        ),
        CheckDefinition(
            check_id="q7_cross_module_question_routing_validation",
            title="Q7 cross-module question routing",
            expected_result=(
                "Cross-module question routing preserves Q1/Q2 identity and round semantics, "
                "requires evidence-backed answers and forbids cross-repository writes"
            ),
            command=(
                python,
                "scripts/validation/validate_q7_cross_module_question_routing_contract.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="q8_logistics_clarification_reference_validation",
            title="Q8 Logistics clarification reference",
            expected_result=(
                "Accepted Logistics reference proves the composed Q1-Q7 clarification, blocker, "
                "decision, attention and routing semantics while Q->H10 remains manual"
            ),
            command=(
                python,
                "scripts/validation/validate_q8_logistics_clarification_reference_validation.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="phase_boundary_progression_gate_validation",
            title="Phase-boundary progression gate",
            expected_result=(
                "Manual progress approval is phase-boundary-only while same-phase "
                "progression remains deterministic and fail-closed"
            ),
            command=(
                python,
                "scripts/validation/validate_phase_boundary_progression_gate_policy.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="blueprint_command_applicability_validation",
            title="Blueprint command applicability",
            expected_result=("Blueprint command applicability and readiness blockers are valid"),
            command=(
                python,
                "scripts/validation/validate_blueprint_command_applicability.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="project_transparency_control_layer_validation",
            title="Project transparency control layer",
            expected_result=("Current governance sources agree and status rendering is read-only"),
            command=(
                python,
                "scripts/validation/validate_project_transparency_control_layer.py",
            ),
            group="documentation",
        ),
        CheckDefinition(
            check_id="module_standards_template_validation",
            title="Standards template",
            expected_result="Module standards template is valid",
            command=(python, "scripts/validate_module_standards_template.py"),
            group="documentation",
        ),
        CheckDefinition(
            check_id="instruction_intake_validation",
            title="Instruction intake",
            expected_result="Instruction intake protocol is valid",
            command=(python, "scripts/validate_instruction_intake.py"),
            group="documentation",
        ),
    ]


def tail_text(text: str, max_lines: int = 12) -> str:
    """Return a bounded tail for routine warning/failure evidence."""

    lines = text.strip().splitlines()
    if not lines:
        return ""
    return "\n".join(lines[-max_lines:])


def run_one_check(check: CheckDefinition) -> CheckResult:
    """Execute one isolated check and capture complete evidence."""

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
        command=check.command,
        group=check.group,
        status=status,
        return_code=process.returncode,
        duration_seconds=duration,
        stdout=process.stdout,
        stderr=process.stderr,
        stdout_tail=tail_text(process.stdout),
        stderr_tail=tail_text(process.stderr),
    )


def run_checks(*, stop_on_fail: bool) -> list[CheckResult]:
    """Run the authoritative check catalog in deterministic order."""

    results: list[CheckResult] = []
    for check in build_checks():
        result = run_one_check(check)
        results.append(result)
        if stop_on_fail and result.status == STATUS_FAILED:
            break
    return results


def build_cli() -> argparse.ArgumentParser:
    """Build the stable Blueprint check-report CLI."""

    parser = argparse.ArgumentParser(
        description="Run Blueprint checks and render compact/file-first reports.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors. NO_COLOR=1 is also supported.",
    )
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="Stop after the first failed check.",
    )
    parser.add_argument(
        "--full-log",
        action="store_true",
        help="Write complete stdout/stderr to reports/diagnostics/.",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Write artifacts without printing the compact terminal tables.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run checks, write artifacts and print a compact decision report."""

    args = build_cli().parse_args(argv)
    use_color = not args.no_color and "NO_COLOR" not in os.environ

    results = run_checks(stop_on_fail=args.stop_on_fail)
    summary = summarize_report_results(results)
    include_full_log = args.full_log or summary.failed > 0 or summary.warnings > 0

    paths = write_report_artifacts(
        project_root=PROJECT_ROOT,
        results=results,
        summary=summary,
        include_full_log=include_full_log,
    )

    if not args.json_only:
        print(
            render_compact_report(
                results,
                summary,
                artifact_paths=paths,
                use_color=use_color,
            )
        )

    return 1 if summary.failed else 0


__all__ = [
    "build_checks",
    "build_cli",
    "detect_status",
    "has_warning_signal",
    "main",
    "run_checks",
    "run_one_check",
    "tail_text",
]


if __name__ == "__main__":
    raise SystemExit(main())
