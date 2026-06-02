from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_SOURCES_FILE = (
    PROJECT_ROOT / "coordination" / "module_sources" / "module_git_sources.yaml"
)
OUTPUT_DIR = PROJECT_ROOT / "reports" / "module_coordination"


@dataclass(frozen=True)
class GitPullResult:
    attempted: bool
    ok: bool
    returncode: int | None
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ModuleCoordinationSnapshot:
    module_id: str
    module_name: str
    generated_at: str
    local_path: str | None
    repo_url: str | None
    branch: str
    repo_status: str
    pull: GitPullResult
    coordination_ready: bool
    missing_files: list[str]
    loaded_files: list[str]
    current_status: dict[str, Any] | None
    prompt_index: dict[str, Any] | None
    report_index: dict[str, Any] | None
    notes: str | None


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_module_sources(path: Path = MODULE_SOURCES_FILE) -> list[dict[str, Any]]:
    data = load_yaml(path)
    return list(data["module_git_sources"]["modules"])


def find_module(module_id: str, modules: list[dict[str, Any]]) -> dict[str, Any]:
    for module in modules:
        if module["module_id"] == module_id:
            return module
    known_modules = ", ".join(sorted(item["module_id"] for item in modules))
    raise ValueError(f"Unknown module_id: {module_id}. Known modules: {known_modules}")


def run_git_pull(local_path: Path, enabled: bool) -> GitPullResult:
    if not enabled:
        return GitPullResult(
            attempted=False,
            ok=True,
            returncode=None,
            stdout="",
            stderr="",
        )

    result = subprocess.run(
        ["git", "-C", str(local_path), "pull", "--ff-only"],
        check=False,
        capture_output=True,
        text=True,
    )

    return GitPullResult(
        attempted=True,
        ok=result.returncode == 0,
        returncode=result.returncode,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
    )


def try_load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_yaml(path)


def build_snapshot(module: dict[str, Any], pull: bool) -> ModuleCoordinationSnapshot:
    local_path_value = module.get("local_path")
    local_path = Path(local_path_value) if local_path_value else None

    missing_files: list[str] = []
    loaded_files: list[str] = []

    if local_path is None or not local_path.exists():
        pull_result = GitPullResult(
            attempted=False,
            ok=False,
            returncode=None,
            stdout="",
            stderr="local_path is missing or does not exist",
        )

        return ModuleCoordinationSnapshot(
            module_id=module["module_id"],
            module_name=module["module_name"],
            generated_at=datetime.now(UTC).isoformat(),
            local_path=local_path_value,
            repo_url=module.get("repo_url"),
            branch=module.get("branch", "main"),
            repo_status=module.get("repo_status", "unknown"),
            pull=pull_result,
            coordination_ready=False,
            missing_files=[
                module.get("status_file", "coordination/status/current_status.yaml"),
                module.get("prompt_index", "coordination/prompts/index.yaml"),
                module.get("report_index", "coordination/reports/index.yaml"),
            ],
            loaded_files=[],
            current_status=None,
            prompt_index=None,
            report_index=None,
            notes=module.get("notes"),
        )

    pull_result = run_git_pull(local_path=local_path, enabled=pull)

    status_path = local_path / module["status_file"]
    prompt_index_path = local_path / module["prompt_index"]
    report_index_path = local_path / module["report_index"]

    current_status = try_load_yaml(status_path)
    prompt_index = try_load_yaml(prompt_index_path)
    report_index = try_load_yaml(report_index_path)

    for path in (status_path, prompt_index_path, report_index_path):
        relative = str(path.relative_to(local_path))
        if path.exists():
            loaded_files.append(relative)
        else:
            missing_files.append(relative)

    coordination_ready = not missing_files and pull_result.ok

    return ModuleCoordinationSnapshot(
        module_id=module["module_id"],
        module_name=module["module_name"],
        generated_at=datetime.now(UTC).isoformat(),
        local_path=str(local_path),
        repo_url=module.get("repo_url"),
        branch=module.get("branch", "main"),
        repo_status=module.get("repo_status", "unknown"),
        pull=pull_result,
        coordination_ready=coordination_ready,
        missing_files=missing_files,
        loaded_files=loaded_files,
        current_status=current_status,
        prompt_index=prompt_index,
        report_index=report_index,
        notes=module.get("notes"),
    )


def render_markdown(snapshot: ModuleCoordinationSnapshot) -> str:
    pull_status = "OK" if snapshot.pull.ok else "FAILED"
    readiness = "READY" if snapshot.coordination_ready else "NOT_READY"

    lines = [
        f"# Module Coordination Snapshot — {snapshot.module_id}",
        "",
        f"- Generated at: `{snapshot.generated_at}`",
        f"- Module name: `{snapshot.module_name}`",
        f"- Local path: `{snapshot.local_path}`",
        f"- Repository: `{snapshot.repo_url}`",
        f"- Branch: `{snapshot.branch}`",
        f"- Repo status: `{snapshot.repo_status}`",
        f"- Coordination readiness: `{readiness}`",
        f"- Git pull attempted: `{snapshot.pull.attempted}`",
        f"- Git pull status: `{pull_status}`",
        "",
    ]

    if snapshot.pull.stdout:
        lines.extend(
            [
                "## Git pull stdout",
                "",
                "```text",
                snapshot.pull.stdout,
                "```",
                "",
            ]
        )

    if snapshot.pull.stderr:
        lines.extend(
            [
                "## Git pull stderr",
                "",
                "```text",
                snapshot.pull.stderr,
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Loaded files",
            "",
        ]
    )

    if snapshot.loaded_files:
        lines.extend(f"- `{item}`" for item in snapshot.loaded_files)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Missing files",
            "",
        ]
    )

    if snapshot.missing_files:
        lines.extend(f"- `{item}`" for item in snapshot.missing_files)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Current status summary",
            "",
        ]
    )

    if snapshot.current_status:
        status = snapshot.current_status
        lines.extend(
            [
                f"- module_status: `{status.get('module_status', 'unknown')}`",
                f"- priority: `{status.get('priority', 'unknown')}`",
                f"- current_phase: `{status.get('current_phase', 'unknown')}`",
                f"- last_completed_step: `{status.get('last_completed_step', 'unknown')}`",
                f"- recommended_next_step: `{status.get('recommended_next_step', [])}`",
            ]
        )
    else:
        lines.append("- current_status.yaml not loaded")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            snapshot.notes or "No notes.",
            "",
        ]
    )

    return "\n".join(lines)


def write_snapshot(snapshot: ModuleCoordinationSnapshot) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / f"{snapshot.module_id}_coordination_snapshot.json"
    markdown_path = OUTPUT_DIR / f"{snapshot.module_id}_coordination_snapshot.md"

    json_path.write_text(
        json.dumps(asdict(snapshot), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(snapshot), encoding="utf-8")

    print(f"📄 JSON snapshot: {json_path}")
    print(f"📄 Markdown snapshot: {markdown_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect coordination status from a ForPrint module repository."
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Module ID from coordination/module_sources/module_git_sources.yaml.",
    )
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Run git pull --ff-only in the module local path before reading files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    modules = load_module_sources()
    module = find_module(args.module, modules)

    snapshot = build_snapshot(module=module, pull=args.pull)
    write_snapshot(snapshot)

    if snapshot.coordination_ready:
        print(f"✅ Module coordination ready: {snapshot.module_id}")
    else:
        print(f"⚠️ Module coordination not ready: {snapshot.module_id}")
        if snapshot.missing_files:
            print("Missing files:")
            for item in snapshot.missing_files:
                print(f"  - {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
