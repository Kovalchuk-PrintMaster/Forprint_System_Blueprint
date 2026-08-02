from __future__ import annotations

import json
import shutil
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.coordination.modules._shared.external_input import (
    create_input_file,
    mark_consumed,
    validate_provided_input,
)
from scripts.coordination.modules._shared.io import (
    WorkflowError,
    read_yaml_mapping,
    relative_or_absolute,
    sha256_file,
    write_json,
    write_yaml,
)
from scripts.coordination.modules._shared.reporting import (
    artifact_paths,
    build_metric_rows,
    render_dashboard,
    render_full_markdown,
)
from scripts.coordination.modules._shared.repository_scan import scan_repository

MODULE_ID = "forprint_system_blueprint"
WORKFLOW_ID = "blueprint_self_audit"
WORKFLOW_INDEX = (
    "coordination/modules/forprint_system_blueprint/workflows/"
    "workflow_index.yaml"
)
INPUT_RELATIVE = "operator_input/forprint_system_blueprint/bsa.yaml"
WORKSPACE_RELATIVE = "tmp/module_workflows/forprint_system_blueprint"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _runtime_path(root: Path) -> Path:
    return artifact_paths(root)["runtime"]


def _evidence_paths(
    root: Path,
    *,
    scan_path: Path,
    report_path: Path,
    instructions_path: Path,
) -> list[Path]:
    paths = [
        scan_path,
        report_path,
        instructions_path,
        root / "coordination/modules/module_workflow_registry.yaml",
        root
        / "coordination/modules/forprint_system_blueprint/"
        "module_workflow_manifest.yaml",
        root / WORKFLOW_INDEX,
        root / "Makefile",
    ]

    for relative_dir in (
        "coordination/repository_knowledge/inventory",
        "coordination/repository_knowledge/flows",
        "coordination/repository_knowledge/direction/blueprint_coordination",
        "coordination/repository_knowledge/direction/system_portfolio",
    ):
        directory = root / relative_dir
        if directory.is_dir():
            candidates = sorted(directory.glob("*.yaml"))
            if candidates:
                paths.append(candidates[-1])

    return [path for path in paths if path.is_file()]


def _build_bundle_manifest(
    root: Path,
    *,
    evidence_paths: list[Path],
) -> dict[str, Any]:
    files = [
        {
            "path": relative_or_absolute(path, root),
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
        for path in sorted(evidence_paths)
    ]
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True).encode("utf-8")
    import hashlib

    content_sha256 = hashlib.sha256(canonical).hexdigest()
    return {
        "schema_version": "blueprint_self_audit_bundle_manifest_v0_1",
        "module_id": MODULE_ID,
        "workflow_id": WORKFLOW_ID,
        "content_sha256": content_sha256,
        "files": files,
    }


def _build_bundle(
    root: Path,
    *,
    run_dir: Path,
    evidence_paths: list[Path],
    template_path: Path,
    manifest_path: Path,
) -> Path:
    bundle_path = run_dir / "analysis_bundle.tar.gz"
    with tarfile.open(bundle_path, "w:gz") as archive:
        for path in [*evidence_paths, template_path, manifest_path]:
            archive.add(
                path,
                arcname=relative_or_absolute(path, root),
                recursive=False,
            )
    return bundle_path


def _write_reports(
    root: Path,
    *,
    scan: dict[str, Any],
    runtime: dict[str, Any],
    external_input_status: str,
    external_analysis: dict[str, Any] | None,
    use_color: bool,
) -> str:
    paths = artifact_paths(root)
    rows = build_metric_rows(scan, external_input_status=external_input_status)
    payload = {
        "schema_version": "blueprint_self_knowledge_summary_v0_1",
        "module_id": MODULE_ID,
        "workflow_id": WORKFLOW_ID,
        "generated_at": scan["generated_at"],
        "runtime": runtime,
        "metrics": rows,
        "scan": scan,
        "external_analysis": external_analysis,
    }
    write_json(paths["summary"], payload)
    paths["full"].parent.mkdir(parents=True, exist_ok=True)
    paths["full"].write_text(
        render_full_markdown(
            scan=scan,
            rows=rows,
            runtime=runtime,
            external_analysis=external_analysis,
        ),
        encoding="utf-8",
    )
    write_yaml(paths["runtime"], runtime)
    return render_dashboard(rows, use_color=use_color)


def prepare(root: Path, *, use_color: bool) -> int:
    scan = scan_repository(root, workflow_index_path=WORKFLOW_INDEX)
    run_id = f"bsa-{_timestamp()}"
    request_id = run_id
    run_dir = root / WORKSPACE_RELATIVE / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    scan_path = run_dir / "repository_scan.json"
    write_json(scan_path, scan)

    provisional_runtime = {
        "schema_version": "module_workflow_runtime_v0_1",
        "module_id": MODULE_ID,
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "request_id": request_id,
        "stage": "preparing_external_input",
        "run_dir": relative_or_absolute(run_dir, root),
        "bundle_path": None,
        "bundle_sha256": None,
        "bundle_content_sha256": None,
    }
    provisional_rows = build_metric_rows(
        scan,
        external_input_status="preparing",
    )
    provisional_report = run_dir / "self_knowledge_report.md"
    provisional_report.write_text(
        render_full_markdown(
            scan=scan,
            rows=provisional_rows,
            runtime=provisional_runtime,
            external_analysis=None,
        ),
        encoding="utf-8",
    )

    instructions_path = run_dir / "analysis_instructions.md"
    instructions_path.write_text(
        """# Blueprint Self Audit — External Analysis

Analyze the attached current scan and repository-knowledge evidence.

Return exactly one YAML document using `response.template.yaml`.

Required assessment:

1. Summarize how deeply Blueprint currently understands itself.
2. Identify the highest-value knowledge gaps.
3. Prioritize the next practical automation or documentation steps.
4. Preserve unknowns and conflicts.
5. Do not declare files dead without proof.
6. Do not propose cross-repository writes.
7. Keep module id, workflow id, request id and source content checksum unchanged.
8. Set `status: provided`.
""",
        encoding="utf-8",
    )

    evidence_paths = _evidence_paths(
        root,
        scan_path=scan_path,
        report_path=provisional_report,
        instructions_path=instructions_path,
    )
    bundle_manifest = _build_bundle_manifest(
        root,
        evidence_paths=evidence_paths,
    )
    manifest_path = run_dir / "bundle_manifest.json"
    write_json(manifest_path, bundle_manifest)

    template_path = run_dir / "response.template.yaml"
    input_path = root / INPUT_RELATIVE
    template = create_input_file(
        input_path,
        request_id=request_id,
        bundle_path=relative_or_absolute(
            run_dir / "analysis_bundle.tar.gz",
            root,
        ),
        bundle_sha256=bundle_manifest["content_sha256"],
    )
    write_yaml(template_path, template)

    bundle_path = _build_bundle(
        root,
        run_dir=run_dir,
        evidence_paths=evidence_paths,
        template_path=template_path,
        manifest_path=manifest_path,
    )
    archive_sha256 = sha256_file(bundle_path)

    runtime = {
        "schema_version": "module_workflow_runtime_v0_1",
        "module_id": MODULE_ID,
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "request_id": request_id,
        "stage": "awaiting_external_input",
        "run_dir": relative_or_absolute(run_dir, root),
        "bundle_path": relative_or_absolute(bundle_path, root),
        "bundle_sha256": archive_sha256,
        "bundle_content_sha256": bundle_manifest["content_sha256"],
        "input_path": INPUT_RELATIVE,
    }
    dashboard = _write_reports(
        root,
        scan=scan,
        runtime=runtime,
        external_input_status="awaiting_input",
        external_analysis=None,
        use_color=use_color,
    )
    shutil.copy2(artifact_paths(root)["full"], run_dir / "self_knowledge_report.md")

    print(dashboard)
    print()
    print("External input required")
    print(f"Module: {MODULE_ID}")
    print("Workflow: Blueprint Self Audit")
    print("Completed stage: repository scan and local coverage report")
    print(f"Analysis bundle: {runtime['bundle_path']}")
    print(f"Archive SHA256: {runtime['bundle_sha256']}")
    print(f"Content checksum: {runtime['bundle_content_sha256']}")
    print(f"Expected response file: {INPUT_RELATIVE}")
    print()
    print("Required action:")
    print("1. Send the analysis bundle to the analysis assistant.")
    print("2. Ask for the exact YAML structure included as response.template.yaml.")
    print("3. Keep module_id, workflow_id, request_id and content checksum unchanged.")
    print("4. Fill analysis.summary, confidence and the structured list fields.")
    print("5. Set status: provided.")
    print("6. Save the result as operator_input/forprint_system_blueprint/bsa.yaml.")
    print("7. Run: make blueprint-self-audit-resume")
    print()
    print("Expected result after resume:")
    print("Validated external assessment is archived and merged into the full report.")
    print("RESULT: AWAITING_EXTERNAL_INPUT")
    return 0


def resume(root: Path, *, use_color: bool) -> int:
    runtime = read_yaml_mapping(_runtime_path(root))
    if runtime.get("stage") != "awaiting_external_input":
        raise WorkflowError(
            "current Blueprint Self Audit is not awaiting external input"
        )

    input_path = root / INPUT_RELATIVE
    provided = validate_provided_input(
        input_path,
        expected_request_id=str(runtime["request_id"]),
        expected_bundle_sha256=str(runtime["bundle_content_sha256"]),
    )
    summary_path = artifact_paths(root)["summary"]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    scan = summary["scan"]

    run_dir = root / str(runtime["run_dir"])
    archived_input = run_dir / "bsa.provided.yaml"
    shutil.copy2(input_path, archived_input)
    runtime["stage"] = "completed"
    runtime["completed_at"] = datetime.now(UTC).isoformat()
    runtime["input_sha256"] = provided["input_sha256"]
    runtime["archived_input"] = relative_or_absolute(archived_input, root)

    dashboard = _write_reports(
        root,
        scan=scan,
        runtime=runtime,
        external_input_status="provided",
        external_analysis=provided,
        use_color=use_color,
    )
    history_dir = (
        root / "reports/modules/forprint_system_blueprint/history"
    )
    history_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        artifact_paths(root)["full"],
        history_dir / f"{runtime['run_id']}__self_knowledge_report.md",
    )
    shutil.copy2(
        artifact_paths(root)["summary"],
        history_dir / f"{runtime['run_id']}__self_knowledge_summary.json",
    )
    mark_consumed(input_path, provided)

    print(dashboard)
    print()
    print("Blueprint Self Audit external analysis accepted")
    print(f"Request: {runtime['request_id']}")
    print(f"Archived input: {runtime['archived_input']}")
    print(
        "Detailed report: "
        "reports/modules/forprint_system_blueprint/current/"
        "self_knowledge_report.md"
    )
    print("RESULT: COMPLETED")
    return 0


def status(root: Path, *, use_color: bool) -> int:
    summary_path = artifact_paths(root)["summary"]
    if not summary_path.is_file():
        print(
            "Blueprint Self Audit is configured and "
            "ready to initialize."
        )
        print("Workflow: blueprint_self_audit [active_v0_1]")
        print("Next command: make blueprint-self-audit")
        print("RESULT: READY_TO_INITIALIZE")
        return 0
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = summary["metrics"]
    print(render_dashboard(rows, use_color=use_color))
    runtime = summary.get("runtime", {})
    print()
    print(f"Stage: {runtime.get('stage', 'unknown')}")
    print(
        "Detailed report: "
        "reports/modules/forprint_system_blueprint/current/"
        "self_knowledge_report.md"
    )
    print("RESULT: READY")
    return 0


def print_full_report(root: Path) -> int:
    report = artifact_paths(root)["full"]
    if not report.is_file():
        print("Blueprint Self Audit has no full report.")
        print("Next command: make blueprint-self-audit")
        return 1
    print(report.read_text(encoding="utf-8"), end="")
    return 0
