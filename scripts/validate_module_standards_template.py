#!/usr/bin/env python3
from __future__ import annotations

import argparse
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

TEMPLATE_DIR = Path("tools/module_standards_template")
REQUIRED_FILES = [
    "README.md",
    "Makefile.fragment",
    "read_blueprint_standards.py",
    "check_blueprint_standards.py",
    "sync_blueprint_standards_snapshot.py",
]
REQUIRED_TARGETS = [
    "blueprint-standards-list",
    "blueprint-standards-check",
    "blueprint-standards-sync",
]
FORBIDDEN_MODULE_ID = "forprint_" + "calculator_engine"


def _issue(path: Path, message: str) -> str:
    return f"{path}: {message}"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _validate_required_files(root: Path) -> list[str]:
    issues: list[str] = []
    for relative_path in REQUIRED_FILES:
        path = root / TEMPLATE_DIR / relative_path
        if not path.is_file():
            issues.append(_issue(path, "required template file is missing"))
    return issues


def _validate_no_forbidden_tokens(root: Path) -> list[str]:
    issues: list[str] = []
    for path in (root / TEMPLATE_DIR).glob("*"):
        if path.is_file() and path.suffix in {".py", ".md", ".fragment"}:
            if FORBIDDEN_MODULE_ID in _read_text(path):
                issues.append(_issue(path, f"forbidden token `{FORBIDDEN_MODULE_ID}`"))
    return issues


def _validate_makefile_fragment(root: Path) -> list[str]:
    path = root / TEMPLATE_DIR / "Makefile.fragment"
    if not path.exists():
        return [_issue(path, "Makefile fragment is missing")]
    text = _read_text(path)
    issues: list[str] = []
    for target in REQUIRED_TARGETS:
        if f"{target}:" not in text:
            issues.append(_issue(path, f"missing target `{target}`"))
    for expected in (
        "$(MAKE) blueprint-check",
        "scripts/read_blueprint_standards.py",
        "scripts/check_blueprint_standards.py",
        "scripts/sync_blueprint_standards_snapshot.py",
    ):
        if expected not in text:
            issues.append(_issue(path, f"missing expected text `{expected}`"))
    return issues


def _validate_readme(root: Path) -> list[str]:
    path = root / TEMPLATE_DIR / "README.md"
    if not path.exists():
        return [_issue(path, "README is missing")]
    text = _read_text(path).lower()
    issues: list[str] = []
    for expected in ("advisory", "gradual", "not automatically equivalent to active prompts"):
        if expected not in text:
            issues.append(_issue(path, f"README must mention `{expected}`"))
    return issues


def _validate_python_compiles(root: Path) -> list[str]:
    issues: list[str] = []
    for file_name in (
        "read_blueprint_standards.py",
        "check_blueprint_standards.py",
        "sync_blueprint_standards_snapshot.py",
    ):
        path = root / TEMPLATE_DIR / file_name
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            issues.append(_issue(path, f"Python compile failed: {exc.msg}"))
    return issues


def _write_fake_blueprint(root: Path) -> Path:
    blueprint_dir = root / "forprint_system_blueprint"
    standards_dir = blueprint_dir / "coordination" / "standards"
    standards_dir.mkdir(parents=True, exist_ok=True)
    (standards_dir / "example_standard.md").write_text(
        "# Example standard\\n\\nStatus: active standard / gradual adoption\\n",
        encoding="utf-8",
    )
    index: dict[str, Any] = {
        "standards_index_version": "v0_1",
        "status": "active",
        "default_semantics": "advisory_guidance_gradual_alignment",
        "policy": {
            "continuous_read_required": True,
            "advisory_by_default": True,
            "not_active_prompt": True,
            "gradual_alignment_required": True,
            "hard_enforcement_requires_prompt_or_directive": True,
        },
        "standards": [
            {
                "standard_id": "example_standard",
                "file": "example_standard.md",
                "title": "Example standard",
                "status": "active_standard",
                "adoption_mode": "gradual_alignment",
            }
        ],
    }
    (standards_dir / "index.yaml").write_text(yaml.safe_dump(index, sort_keys=False), encoding="utf-8")
    return blueprint_dir


def _run_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def _validate_template_runtime(root: Path) -> list[str]:
    issues: list[str] = []
    with tempfile.TemporaryDirectory() as temp_dir_string:
        temp_dir = Path(temp_dir_string)
        blueprint_dir = _write_fake_blueprint(temp_dir)
        module_root = temp_dir / "module"
        module_root.mkdir(parents=True, exist_ok=True)
        read_script = root / TEMPLATE_DIR / "read_blueprint_standards.py"
        check_script = root / TEMPLATE_DIR / "check_blueprint_standards.py"
        sync_script = root / TEMPLATE_DIR / "sync_blueprint_standards_snapshot.py"

        read_result = _run_script(read_script, "--blueprint-dir", str(blueprint_dir), "--list")
        if read_result.returncode != 0:
            issues.append(_issue(read_script, f"list runtime failed:\\n{read_result.stdout}"))

        check_result = _run_script(check_script, "--blueprint-dir", str(blueprint_dir), "--module-root", str(module_root))
        if check_result.returncode != 0:
            issues.append(_issue(check_script, f"check runtime failed:\\n{check_result.stdout}"))

        sync_result = _run_script(sync_script, "--blueprint-dir", str(blueprint_dir), "--module-root", str(module_root))
        if sync_result.returncode != 0:
            issues.append(_issue(sync_script, f"sync runtime failed:\\n{sync_result.stdout}"))

        snapshot_path = module_root / "coordination" / "standards" / "blueprint_standards_snapshot.yaml"
        if not snapshot_path.is_file():
            issues.append(_issue(snapshot_path, "snapshot file was not created"))
        else:
            snapshot = yaml.safe_load(snapshot_path.read_text(encoding="utf-8"))
            if not isinstance(snapshot, dict):
                issues.append(_issue(snapshot_path, "snapshot root must be a mapping"))
            elif snapshot.get("standards_count") != 1:
                issues.append(_issue(snapshot_path, "snapshot standards_count must be 1"))
    return issues


def validate_template(root: Path) -> list[str]:
    issues: list[str] = []
    issues.extend(_validate_required_files(root))
    issues.extend(_validate_no_forbidden_tokens(root))
    issues.extend(_validate_makefile_fragment(root))
    issues.extend(_validate_readme(root))
    issues.extend(_validate_python_compiles(root))
    if not issues:
        issues.extend(_validate_template_runtime(root))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate module standards visibility template.")
    parser.add_argument("--root", default=".", help="Blueprint repository root.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    issues = validate_template(root)
    if issues:
        print("❌ Module standards template validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print("✅ Module standards template validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
