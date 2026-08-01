#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.completion_intake_check import (
    CompletionIntakeCheckError,
    CompletionIntakeCheckResult,
    check_completion_intake,
)
from scripts.coordination.module_roadmap import (
    load_yaml_file,
    resolve_roadmap_path,
    validate_roadmap_document,
)
from scripts.reporting.coordination_result_tables import (
    render_completion_intake_summary,
)

REVIEW_SCHEMA_VERSION = "blueprint_completion_review_packet_v0_1"
ALLOWED_DECISIONS = {"accepted", "returned_for_fix"}
OK_CHECK_VALUES = {"ok", "passed", "pass", "green", True}


class CompletionIntakeError(ValueError):
    """Raised when module completion evidence cannot be accepted safely."""


@dataclass(frozen=True)
class CompletionEvidence:
    module_id: str
    prompt_id: str
    phase: str
    packet_path: Path
    packet_relative_path: str
    report_path: str
    report_absolute_path: Path
    created_at: str
    branch: str | None
    implementation_commit: str
    completion_commit: str
    push_status: str | None
    checks: dict[str, Any]
    boundary_confirmation: dict[str, Any]


@dataclass(frozen=True)
class IntakePlan:
    module_id: str
    prompt_id: str
    decision: str
    reviewed_at: str
    queue_path: Path
    roadmap_path: Path
    review_path: Path
    queue_data: dict[str, Any]
    roadmap_data: dict[str, Any]
    review_data: dict[str, Any]
    changed_paths: tuple[Path, ...]
    warnings: tuple[str, ...]


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CompletionIntakeError(f"file does not exist: {path}") from exc
    except yaml.YAMLError as exc:
        raise CompletionIntakeError(f"invalid YAML in {path}: {exc}") from exc

    if not isinstance(loaded, dict):
        raise CompletionIntakeError(f"YAML root must be a mapping: {path}")

    return loaded


def _required_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CompletionIntakeError(f"completion packet field `{field}` must be a non-empty string")
    return value.strip()


def _safe_under(root: Path, candidate: Path, *, label: str) -> Path:
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve()
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise CompletionIntakeError(f"{label} escapes module root: {candidate}") from exc
    return candidate_resolved


def _run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise CompletionIntakeError(f"git {' '.join(args)} failed in {repo}: {detail}")
    return completed.stdout.strip()


def _verify_commit(repo: Path, commit: str) -> str:
    return _run_git(repo, "rev-parse", "--verify", f"{commit}^{{commit}}")


def _remote_contains(repo: Path, commit: str) -> bool:
    output = _run_git(repo, "branch", "-r", "--contains", commit)
    return bool(output.strip())


def _date_part(value: str) -> str:
    token = value.strip()
    if len(token) < 10:
        raise CompletionIntakeError(f"invalid date/timestamp: {value!r}")
    candidate = token[:10]
    try:
        date.fromisoformat(candidate)
    except ValueError as exc:
        raise CompletionIntakeError(f"invalid ISO date/timestamp: {value!r}") from exc
    return candidate


def _normalize_check_value(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in OK_CHECK_VALUES
    return value in OK_CHECK_VALUES


def _validate_checks(checks: Any) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(checks, dict):
        raise CompletionIntakeError("completion packet `checks` must be a mapping")

    warnings: list[str] = []
    for required in ("check_report", "tests", "governance_check"):
        if required not in checks:
            raise CompletionIntakeError(f"completion packet `checks.{required}` is required")
        if not _normalize_check_value(checks[required]):
            raise CompletionIntakeError(
                f"completion packet `checks.{required}` is not successful: {checks[required]!r}"
            )

    warning_count = checks.get("check_report_warnings")
    if isinstance(warning_count, int) and warning_count > 0:
        warnings.append(f"module check report contains {warning_count} warning(s)")

    failed_count = checks.get("check_report_failed")
    if isinstance(failed_count, int) and failed_count > 0:
        raise CompletionIntakeError(
            f"module check report contains {failed_count} failed check(s)"
        )

    return dict(checks), warnings


def _validate_boundary(boundary: Any) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(boundary, dict) or not boundary:
        raise CompletionIntakeError(
            "completion packet `boundary_confirmation` must be a non-empty mapping"
        )

    warnings: list[str] = []
    unsafe: list[str] = []

    for key, value in boundary.items():
        if key.startswith("no_"):
            if value is not True:
                unsafe.append(f"{key} must be true")
        elif key.endswith(("_added", "_committed", "_written_directly")):
            if value is not False:
                unsafe.append(f"{key} must be false")
        elif isinstance(value, bool):
            warnings.append(f"unrecognized boundary flag semantics: {key}={value}")

    if unsafe:
        raise CompletionIntakeError(
            "unsafe boundary confirmation:\n- " + "\n- ".join(unsafe)
        )

    return dict(boundary), warnings


def collect_completion_evidence(
    *,
    module_id: str,
    module_root: Path,
    packet: Path,
    completion_commit: str | None,
    verify_git: bool,
) -> tuple[CompletionEvidence, list[str]]:
    module_root = module_root.resolve()
    packet_path = packet if packet.is_absolute() else module_root / packet
    packet_path = _safe_under(module_root, packet_path, label="completion packet")
    data = _load_yaml_mapping(packet_path)

    packet_module = _required_string(data, "module_id")
    if packet_module != module_id:
        raise CompletionIntakeError(
            f"packet module_id `{packet_module}` does not match requested module `{module_id}`"
        )

    prompt_id = _required_string(data, "prompt_id")
    phase = _required_string(data, "phase")
    report_path = _required_string(data, "report_path")
    report_absolute = _safe_under(
        module_root,
        module_root / report_path,
        label="completion report",
    )
    if not report_absolute.is_file():
        raise CompletionIntakeError(f"completion report does not exist: {report_absolute}")

    created_at = _required_string(data, "created_at")
    implementation_commit = _required_string(data, "implementation_commit")
    checks, warnings = _validate_checks(data.get("checks"))
    boundary, boundary_warnings = _validate_boundary(data.get("boundary_confirmation"))
    warnings.extend(boundary_warnings)

    branch = data.get("branch")
    if branch is not None and (not isinstance(branch, str) or not branch.strip()):
        raise CompletionIntakeError("completion packet `branch` must be a non-empty string when present")

    push_status = data.get("push_status")
    if push_status is not None and not isinstance(push_status, str):
        raise CompletionIntakeError("completion packet `push_status` must be a string when present")

    resolved_completion_commit = completion_commit
    if not resolved_completion_commit:
        if verify_git:
            resolved_completion_commit = _run_git(module_root, "rev-parse", "HEAD")
        else:
            resolved_completion_commit = implementation_commit

    if verify_git:
        implementation_commit = _verify_commit(module_root, implementation_commit)
        resolved_completion_commit = _verify_commit(module_root, resolved_completion_commit)

        if push_status not in {"pushed", "synced", "remote"}:
            warnings.append(
                "packet push_status is not explicitly pushed/synced; remote containment was checked"
            )
        if not _remote_contains(module_root, resolved_completion_commit):
            raise CompletionIntakeError(
                f"completion commit is not contained in a remote branch: {resolved_completion_commit}"
            )

    packet_relative = packet_path.relative_to(module_root).as_posix()

    return (
        CompletionEvidence(
            module_id=module_id,
            prompt_id=prompt_id,
            phase=phase,
            packet_path=packet_path,
            packet_relative_path=packet_relative,
            report_path=report_path,
            report_absolute_path=report_absolute,
            created_at=created_at,
            branch=branch.strip() if isinstance(branch, str) else None,
            implementation_commit=implementation_commit,
            completion_commit=resolved_completion_commit,
            push_status=push_status,
            checks=checks,
            boundary_confirmation=boundary,
        ),
        warnings,
    )


def _find_prompt(queue_data: dict[str, Any], prompt_id: str) -> dict[str, Any]:
    queue = queue_data.get("prompt_queue")
    if not isinstance(queue, list):
        raise CompletionIntakeError("prompt queue `prompt_queue` must be a list")

    matches = [
        item
        for item in queue
        if isinstance(item, dict) and item.get("prompt_id") == prompt_id
    ]
    if len(matches) != 1:
        raise CompletionIntakeError(
            f"expected exactly one prompt queue record for `{prompt_id}`, found {len(matches)}"
        )
    return matches[0]


def _find_roadmap_step(roadmap_data: dict[str, Any], prompt_id: str) -> dict[str, Any]:
    roadmap = roadmap_data.get("roadmap")
    if not isinstance(roadmap, list):
        raise CompletionIntakeError("roadmap `roadmap` must be a list")

    matches = [
        item
        for item in roadmap
        if isinstance(item, dict) and item.get("step_id") == prompt_id
    ]
    if len(matches) != 1:
        raise CompletionIntakeError(
            f"expected exactly one roadmap step for `{prompt_id}`, found {len(matches)}"
        )
    return matches[0]


def _test_summary(checks: dict[str, Any]) -> str:
    parts: list[str] = []
    test_count = checks.get("test_count")
    if isinstance(test_count, int):
        parts.append(f"{test_count} tests")

    passed = checks.get("check_report_passed")
    warnings = checks.get("check_report_warnings")
    failed = checks.get("check_report_failed")
    if all(isinstance(value, int) for value in (passed, warnings, failed)):
        parts.append(f"check report {passed} passed / {warnings} warnings / {failed} failed")

    return "; ".join(parts) or "module completion checks reported successful"


def _detect_check_report(module_root: Path, module_id: str) -> str | None:
    candidates = (
        Path("reports") / f"{module_id}_check_report.md",
        Path("reports") / "logistics_service_check_report.md",
        Path("reports") / "blueprint_check_report.md",
    )
    for candidate in candidates:
        if (module_root / candidate).is_file():
            return candidate.as_posix()
    return None


def _review_path(
    *,
    root: Path,
    module_id: str,
    prompt_id: str,
    reviewed_at: str,
    decision: str,
) -> Path:
    return (
        root
        / "coordination"
        / "review_packets"
        / module_id
        / "processed"
        / f"{reviewed_at}__{prompt_id}__{decision}.yaml"
    )


def build_intake_plan(
    *,
    root: Path,
    module_id: str,
    module_root: Path,
    packet: Path,
    decision: str,
    review_notes: str,
    completion_commit: str | None = None,
    reviewed_at: str | None = None,
    verify_git: bool = True,
    intake_check: CompletionIntakeCheckResult | None = None,
) -> IntakePlan:
    if decision not in ALLOWED_DECISIONS:
        raise CompletionIntakeError(
            f"unsupported decision `{decision}`; allowed: {', '.join(sorted(ALLOWED_DECISIONS))}"
        )

    root = root.resolve()
    module_root = module_root.resolve()
    queue_path = root / "coordination" / "outgoing_prompts" / module_id / "index.yaml"
    roadmap_path = resolve_roadmap_path(root=root, module=module_id)

    evidence, warnings = collect_completion_evidence(
        module_id=module_id,
        module_root=module_root,
        packet=packet,
        completion_commit=completion_commit,
        verify_git=verify_git,
    )

    if decision == "accepted":
        if intake_check is None:
            intake_check_data = {"status": "not_run"}
        else:
            expected_check_values = {
                "module_id": evidence.module_id,
                "prompt_id": evidence.prompt_id,
                "phase": evidence.phase,
                "packet_path": evidence.packet_relative_path,
                "report_path": evidence.report_path,
                "implementation_commit": evidence.implementation_commit,
                "completion_commit": evidence.completion_commit,
            }
            actual_check_values = {
                "module_id": intake_check.module_id,
                "prompt_id": intake_check.prompt_id,
                "phase": intake_check.phase,
                "packet_path": intake_check.packet_path,
                "report_path": intake_check.report_path,
                "implementation_commit": intake_check.implementation_commit,
                "completion_commit": intake_check.completion_commit,
            }
            if actual_check_values != expected_check_values:
                raise CompletionIntakeError(
                    "completion-intake-check result does not match "
                    "the intake plan evidence"
                )
            intake_check_data = {
                "status": "passed",
                "module_id": intake_check.module_id,
                "prompt_id": intake_check.prompt_id,
                "phase": intake_check.phase,
                "packet_path": intake_check.packet_path,
                "report_path": intake_check.report_path,
                "implementation_commit": intake_check.implementation_commit,
                "completion_commit": intake_check.completion_commit,
                "remote": intake_check.remote,
                "branch": intake_check.branch,
                "remote_commit": intake_check.remote_commit,
                "warnings": list(intake_check.warnings),
            }
    else:
        intake_check_data = {
            "status": "not_required_for_return",
        }

    queue_original = _load_yaml_mapping(queue_path)
    roadmap_original = load_yaml_file(roadmap_path)
    roadmap_validation = validate_roadmap_document(roadmap_original, path=roadmap_path)
    if roadmap_validation.errors:
        raise CompletionIntakeError(
            "roadmap is invalid before intake:\n- "
            + "\n- ".join(roadmap_validation.errors)
        )
    warnings.extend(roadmap_validation.warnings)

    queue_data = copy.deepcopy(queue_original)
    roadmap_data = copy.deepcopy(roadmap_original)

    prompt = _find_prompt(queue_data, evidence.prompt_id)
    step = _find_roadmap_step(roadmap_data, evidence.prompt_id)

    existing_review = prompt.get("blueprint_review")
    if not isinstance(existing_review, dict):
        existing_review = {}

    effective_reviewed_at = reviewed_at
    if not effective_reviewed_at:
        existing_date = existing_review.get("accepted_at")
        if decision == "accepted" and isinstance(existing_date, str) and existing_date:
            effective_reviewed_at = existing_date
        else:
            effective_reviewed_at = date.today().isoformat()
    effective_reviewed_at = _date_part(effective_reviewed_at)

    completed_at = _date_part(evidence.created_at)

    prompt["module_execution"] = {
        "status": (
            "completed_by_module"
            if decision == "accepted"
            else "returned_for_fix"
        ),
        "completion_commit": evidence.completion_commit,
        "completion_report": evidence.report_path,
        "completed_at": completed_at,
    }

    if decision == "accepted":
        prompt["blueprint_review"] = {
            "status": "accepted_by_blueprint",
            "acceptance_commit": existing_review.get("acceptance_commit"),
            "accepted_at": effective_reviewed_at,
            "review_notes": review_notes or (
                "Accepted from validated module completion packet, successful checks, "
                "verified commits and preserved boundary confirmations."
            ),
        }
        step["status"] = "accepted"
    else:
        prompt["blueprint_review"] = {
            "status": "returned_for_fix",
            "acceptance_commit": None,
            "accepted_at": None,
            "review_notes": review_notes or "Returned for correction by Blueprint review.",
        }
        step["status"] = "active"

    evidence_block = step.get("evidence")
    if not isinstance(evidence_block, dict):
        evidence_block = {}
    evidence_block.update(
        {
            "implementation_commit": evidence.implementation_commit,
            "completion_commit": evidence.completion_commit,
            "completion_report": evidence.report_path,
            "completion_packet": evidence.packet_relative_path,
            "test_summary": _test_summary(evidence.checks),
            "blueprint_review_status": prompt["blueprint_review"]["status"],
        }
    )
    check_report = _detect_check_report(module_root, module_id)
    if check_report:
        evidence_block["check_report"] = check_report
    if decision == "returned_for_fix":
        evidence_block["review_notes"] = prompt["blueprint_review"]["review_notes"]
    step["evidence"] = evidence_block

    metadata = roadmap_data.get("metadata")
    if isinstance(metadata, dict):
        metadata["updated_at"] = effective_reviewed_at

    review_path = _review_path(
        root=root,
        module_id=module_id,
        prompt_id=evidence.prompt_id,
        reviewed_at=effective_reviewed_at,
        decision=decision,
    )
    review_data = {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "review_id": f"{effective_reviewed_at}__{module_id}__{evidence.prompt_id}__{decision}",
        "module_id": module_id,
        "prompt_id": evidence.prompt_id,
        "phase": evidence.phase,
        "decision": decision,
        "reviewed_at": effective_reviewed_at,
        "review_notes": prompt["blueprint_review"]["review_notes"],
        "module_evidence": {
            "module_root": str(module_root),
            "packet_path": evidence.packet_relative_path,
            "report_path": evidence.report_path,
            "branch": evidence.branch,
            "implementation_commit": evidence.implementation_commit,
            "completion_commit": evidence.completion_commit,
            "push_status": evidence.push_status,
            "checks": evidence.checks,
            "boundary_confirmation": evidence.boundary_confirmation,
        },
        "blueprint_intake_check": intake_check_data,
        "blueprint_updates": {
            "prompt_queue": queue_path.relative_to(root).as_posix(),
            "roadmap": roadmap_path.relative_to(root).as_posix(),
            "roadmap_step_status": step["status"],
            "prompt_execution_status": prompt["module_execution"]["status"],
            "blueprint_review_status": prompt["blueprint_review"]["status"],
        },
    }

    changed_paths: list[Path] = []
    if queue_data != queue_original:
        changed_paths.append(queue_path)
    if roadmap_data != roadmap_original:
        changed_paths.append(roadmap_path)

    existing_review_data = None
    if review_path.exists():
        existing_review_data = _load_yaml_mapping(review_path)
    if review_data != existing_review_data:
        changed_paths.append(review_path)

    return IntakePlan(
        module_id=module_id,
        prompt_id=evidence.prompt_id,
        decision=decision,
        reviewed_at=effective_reviewed_at,
        queue_path=queue_path,
        roadmap_path=roadmap_path,
        review_path=review_path,
        queue_data=queue_data,
        roadmap_data=roadmap_data,
        review_data=review_data,
        changed_paths=tuple(changed_paths),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _yaml_text(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        handle.write(text)
        temporary_name = handle.name
    os.replace(temporary_name, path)


def apply_intake_plan(plan: IntakePlan) -> tuple[Path, ...]:
    if plan.decision == "accepted":
        intake_check = plan.review_data.get(
            "blueprint_intake_check"
        )
        if (
            not isinstance(intake_check, dict)
            or intake_check.get("status") != "passed"
        ):
            raise CompletionIntakeError(
                "completion-accept requires a successful "
                "completion-intake-check before Blueprint writes"
            )

    payloads = {
        plan.queue_path: _yaml_text(plan.queue_data),
        plan.roadmap_path: _yaml_text(plan.roadmap_data),
        plan.review_path: _yaml_text(plan.review_data),
    }

    originals: dict[Path, str | None] = {
        path: path.read_text(encoding="utf-8") if path.exists() else None
        for path in payloads
    }

    changed: list[Path] = []
    try:
        for path, text in payloads.items():
            if originals[path] == text:
                continue
            _atomic_write(path, text)
            changed.append(path)
    except Exception:
        for path, original in originals.items():
            if original is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_write(path, original)
        raise

    return tuple(changed)


def _render_plan(
    plan: IntakePlan,
    *,
    root: Path,
    write: bool,
    use_color: bool = True,
) -> str:
    signal = "GREEN" if not plan.warnings else "YELLOW"
    changed_files: list[str] = []
    for path in plan.changed_paths:
        try:
            changed_files.append(path.relative_to(root).as_posix())
        except ValueError:
            changed_files.append(str(path))

    next_actions = (
        f"python scripts/coordination/validate_prompt_queue.py --root {root}",
        (
            "python scripts/coordination/validate_module_roadmap.py "
            f"--root {root} --module {plan.module_id}"
        ),
        f"make next-work-suggestion MODULE={plan.module_id}",
    )
    return render_completion_intake_summary(
        result=signal,
        mode="WRITE" if write else "PREVIEW",
        module=plan.module_id,
        prompt_id=plan.prompt_id,
        decision=plan.decision,
        reviewed_at=plan.reviewed_at,
        changed_files=changed_files,
        warnings=plan.warnings,
        next_actions=next_actions,
        use_color=use_color,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or apply Blueprint-side module completion intake."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--module", required=True)
    parser.add_argument("--module-root", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument(
        "--decision",
        choices=sorted(ALLOWED_DECISIONS),
        default="accepted",
    )
    parser.add_argument("--review-notes", default="")
    parser.add_argument("--completion-commit")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch")
    parser.add_argument("--reviewed-at")
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--no-git-verify",
        action="store_true",
        help="Skip module Git commit and remote containment verification.",
    )
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        intake_check = None
        completion_commit = args.completion_commit

        if args.decision == "accepted":
            if args.no_git_verify:
                raise CompletionIntakeError(
                    "`--no-git-verify` cannot bypass "
                    "completion-intake-check for acceptance"
                )
            if not completion_commit:
                raise CompletionIntakeError(
                    "completion-accept and completion-intake-preview "
                    "require --completion-commit"
                )
            try:
                intake_check = check_completion_intake(
                    blueprint_root=args.root,
                    module_id=args.module,
                    module_root=args.module_root,
                    packet=args.packet,
                    completion_commit=completion_commit,
                    remote=args.remote,
                    branch=args.branch,
                )
            except CompletionIntakeCheckError as error:
                raise CompletionIntakeError(
                    f"completion-intake-check failed: {error}"
                ) from error
            completion_commit = intake_check.completion_commit

        plan = build_intake_plan(
            root=args.root,
            module_id=args.module,
            module_root=args.module_root,
            packet=args.packet,
            decision=args.decision,
            review_notes=args.review_notes,
            completion_commit=completion_commit,
            reviewed_at=args.reviewed_at,
            verify_git=False,
            intake_check=intake_check,
        )
        changed = apply_intake_plan(plan) if args.write else ()
    except CompletionIntakeError as exc:
        print(f"RESULT: RED\nERROR: {exc}")
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "result": "YELLOW" if plan.warnings else "GREEN",
                    "mode": "write" if args.write else "preview",
                    "module": plan.module_id,
                    "prompt_id": plan.prompt_id,
                    "decision": plan.decision,
                    "reviewed_at": plan.reviewed_at,
                    "changed_files": [
                        str(path.relative_to(args.root.resolve()))
                        for path in (changed if args.write else plan.changed_paths)
                    ],
                    "warnings": list(plan.warnings),
                    "blueprint_intake_check": (
                        plan.review_data.get(
                            "blueprint_intake_check"
                        )
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        check_data = plan.review_data.get(
            "blueprint_intake_check"
        )
        if (
            isinstance(check_data, dict)
            and check_data.get("status") == "passed"
        ):
            print("Completion intake check: PASSED")
            print(
                "Publication: "
                f"{check_data['remote']}/{check_data['branch']} "
                f"@ {check_data['remote_commit']}"
            )
        elif plan.decision == "returned_for_fix":
            print(
                "Completion intake check: "
                "NOT REQUIRED FOR RETURN"
            )

        print(
            _render_plan(
                plan,
                root=args.root.resolve(),
                write=args.write,
                use_color=not args.no_color and "NO_COLOR" not in os.environ,
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
