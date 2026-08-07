from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/coordination/historical_acceptance_reconciliation.py"


def load_reconciler():
    spec = importlib.util.spec_from_file_location(
        "historical_acceptance_reconciliation",
        SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            value,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    git(path, "init")
    git(path, "config", "user.email", "tests@example.invalid")
    git(path, "config", "user.name", "Blueprint Tests")


def commit_all(repo: Path, message: str) -> str:
    git(repo, "add", ".")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def packet(
    *,
    prompt_id: str,
    implementation_commit: str,
    report_path: str,
) -> dict:
    return {
        "completion_id": f"{prompt_id}_completion",
        "module_id": "logistics_service",
        "module_name": "Logistics Service",
        "phase": prompt_id.removeprefix("logistics_service_"),
        "prompt_id": prompt_id,
        "report_id": f"{prompt_id}_report",
        "report_path": report_path,
        "created_at": "2026-07-14",
        "summary": "Fixture completion.",
        "implementation_commit": implementation_commit,
        "implemented": ["fixture"],
        "instruction_sources_reviewed": ["fixture"],
        "standards_reviewed": ["fixture"],
        "standards_alignment_notes": ["fixture"],
        "current_outputs": ["fixture"],
        "next_recommended_steps": ["fixture"],
        "checks": {
            "check_report": "ok",
            "tests": "ok",
            "governance_check": "ok",
        },
    }


def build_fixture(tmp_path: Path):
    reconciler = load_reconciler()
    blueprint = tmp_path / "blueprint"
    module = tmp_path / "module"
    init_repo(blueprint)
    init_repo(module)

    (module / "src").mkdir()
    (module / "src/example.txt").write_text(
        "implementation\n",
        encoding="utf-8",
    )
    implementation_commit = commit_all(
        module,
        "implementation",
    )

    accepted_prompt = "logistics_service_test_address_book_v0_1"
    unresolved_prompt = "logistics_service_boundary_and_local_model_v0_1"
    pending_prompt = "logistics_service_tracking_events_v0_1"

    for prompt_id in (
        accepted_prompt,
        unresolved_prompt,
        pending_prompt,
    ):
        report_path = f"coordination/reports/completion/{prompt_id}_completion.md"
        packet_path = f"coordination/completion_packets/records/{prompt_id}_completion.yaml"
        report = module / report_path
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            f"# {prompt_id}\n",
            encoding="utf-8",
        )
        write_yaml(
            module / packet_path,
            packet(
                prompt_id=prompt_id,
                implementation_commit=implementation_commit,
                report_path=report_path,
            ),
        )

    completion_commit = commit_all(module, "completion evidence")

    review_path = (
        blueprint / "coordination/review_packets/logistics_service/processed/accepted.yaml"
    )
    write_yaml(
        review_path,
        {
            "schema_version": "blueprint_completion_review_packet_v0_1",
            "review_id": "accepted",
            "module_id": "logistics_service",
            "prompt_id": accepted_prompt,
            "phase": "test_address_book_v0_1",
            "decision": "accepted",
            "reviewed_at": "2026-07-14",
            "review_notes": "fixture",
            "module_evidence": {
                "packet_path": (
                    f"coordination/completion_packets/records/{accepted_prompt}_completion.yaml"
                ),
                "report_path": (f"coordination/reports/completion/{accepted_prompt}_completion.md"),
                "implementation_commit": implementation_commit,
                "completion_commit": completion_commit[:8],
            },
        },
    )

    write_yaml(
        blueprint / "coordination/outgoing_prompts/logistics_service/index.yaml",
        {
            "prompts": [
                {
                    "prompt_id": unresolved_prompt,
                    "blueprint_review_status": "accepted_by_blueprint",
                },
                {
                    "prompt_id": pending_prompt,
                    "blueprint_review_status": "not_started",
                },
            ]
        },
    )
    write_yaml(
        blueprint / "coordination/roadmaps/logistics_service.yaml",
        {
            "steps": [
                {
                    "prompt_id": unresolved_prompt,
                    "status": "accepted",
                },
                {
                    "prompt_id": pending_prompt,
                    "status": "ready",
                },
            ]
        },
    )
    blueprint_commit = commit_all(blueprint, "blueprint evidence")

    return {
        "reconciler": reconciler,
        "blueprint": blueprint,
        "module": module,
        "blueprint_commit": blueprint_commit,
        "module_commit": completion_commit,
        "accepted_prompt": accepted_prompt,
        "unresolved_prompt": unresolved_prompt,
        "pending_prompt": pending_prompt,
    }


def test_classifies_three_governance_states(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path)
    reconciler = fixture["reconciler"]

    result = reconciler.reconcile(
        blueprint_root=fixture["blueprint"],
        module_id="logistics_service",
        module_root=fixture["module"],
        prompt_ids=[
            fixture["accepted_prompt"],
            fixture["unresolved_prompt"],
            fixture["pending_prompt"],
        ],
        blueprint_commit=fixture["blueprint_commit"],
        module_commit=fixture["module_commit"],
    )

    by_prompt = {item["prompt_id"]: item for item in result["items"]}
    assert (
        by_prompt[fixture["accepted_prompt"]]["classification"] == reconciler.HISTORICAL_ACCEPTANCE
    )
    assert (
        by_prompt[fixture["unresolved_prompt"]]["classification"]
        == reconciler.HISTORICAL_EVIDENCE_UNRESOLVED
    )
    assert (
        by_prompt[fixture["pending_prompt"]]["classification"] == reconciler.PENDING_OPERATOR_REVIEW
    )


def test_acceptance_resolves_short_review_sha(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path)
    reconciler = fixture["reconciler"]

    result = reconciler.reconcile(
        blueprint_root=fixture["blueprint"],
        module_id="logistics_service",
        module_root=fixture["module"],
        prompt_ids=[fixture["accepted_prompt"]],
        blueprint_commit=fixture["blueprint_commit"],
        module_commit=fixture["module_commit"],
    )

    item = result["items"][0]
    assert item["classification"] == reconciler.HISTORICAL_ACCEPTANCE
    proof = item["acceptance_proof"]
    assert proof["completion_commit"]["resolved"] == fixture["module_commit"]


def test_reconciliation_is_read_only(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path)
    reconciler = fixture["reconciler"]

    blueprint_before = git(
        fixture["blueprint"],
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    module_before = git(
        fixture["module"],
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )

    reconciler.reconcile(
        blueprint_root=fixture["blueprint"],
        module_id="logistics_service",
        module_root=fixture["module"],
        prompt_ids=[
            fixture["accepted_prompt"],
            fixture["unresolved_prompt"],
            fixture["pending_prompt"],
        ],
        blueprint_commit=fixture["blueprint_commit"],
        module_commit=fixture["module_commit"],
    )

    assert (
        git(
            fixture["blueprint"],
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        )
        == blueprint_before
    )
    assert (
        git(
            fixture["module"],
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        )
        == module_before
    )
