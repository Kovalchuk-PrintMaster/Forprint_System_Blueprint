#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from scripts.coordination.modules._shared.io import WorkflowError, read_yaml_mapping
from scripts.coordination.modules.forprint_system_blueprint.workflows import self_audit

REGISTRY = Path("coordination/modules/module_workflow_registry.yaml")
SUPPORTED_MODULE = "forprint_system_blueprint"


def _root(value: str) -> Path:
    root = Path(value).resolve()
    if not (root / "Makefile").is_file():
        raise WorkflowError(f"Blueprint repository root is invalid: {root}")
    return root


def _validate_control_files(root: Path) -> list[str]:
    registry = read_yaml_mapping(root / REGISTRY)
    if registry.get("schema_version") != "module_workflow_registry_v0_1":
        raise WorkflowError("unsupported module workflow registry schema")
    makefile = root / "Makefile"
    make_targets = set(
        re.findall(
            r"^([A-Za-z0-9_.-]+):(?:\s|$)",
            makefile.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
    )
    issues: list[str] = []
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            issues.append("registry module entry must be a mapping")
            continue
        manifest_path = module.get("manifest")
        if not isinstance(manifest_path, str):
            issues.append("registry module manifest path is missing")
            continue
        manifest = read_yaml_mapping(root / manifest_path)
        module_id = module.get("module_id")
        if manifest.get("module_id") != module_id:
            issues.append(f"manifest module id mismatch: {module_id}")
        workflows = manifest.get("workflows")
        index_path = workflows.get("index") if isinstance(workflows, dict) else None
        if not isinstance(index_path, str):
            issues.append(f"workflow index missing: {module_id}")
            continue
        index = read_yaml_mapping(root / index_path)
        for workflow in index.get("workflows", []):
            if not isinstance(workflow, dict):
                issues.append(f"invalid workflow record: {module_id}")
                continue
            target_map = workflow.get("make_targets")
            if isinstance(target_map, dict):
                for values in target_map.values():
                    if not isinstance(values, list):
                        continue
                    for target in values:
                        if isinstance(target, str) and target not in make_targets:
                            issues.append(
                                f"{module_id}/{workflow.get('workflow_id')}: "
                                f"missing Make target {target}"
                            )
            for key in ("documentation", "script", "recovery"):
                value = workflow.get(key)
                if not isinstance(value, str) or not (root / value).is_file():
                    issues.append(
                        f"{module_id}/{workflow.get('workflow_id')}: "
                        f"missing {key} {value!r}"
                    )
    return issues


def _list(root: Path) -> int:
    registry = read_yaml_mapping(root / REGISTRY)
    print("ForPrint module workflows")
    for module in registry.get("modules", []):
        manifest = read_yaml_mapping(root / module["manifest"])
        index = read_yaml_mapping(root / manifest["workflows"]["index"])
        for workflow in index.get("workflows", []):
            print(
                f"{module['module_id']}: "
                f"{workflow['workflow_id']} [{workflow['status']}]"
            )
    print("RESULT: READY")
    return 0


def _check(root: Path) -> int:
    issues = _validate_control_files(root)
    if issues:
        print("Module workflow validation failed")
        for issue in issues:
            print(f"- {issue}")
        print("RESULT: FAILED")
        return 1
    print("Module workflow validation")
    print("Registry: OK")
    print("Manifests: OK")
    print("Workflow indexes: OK")
    print("Documentation/scripts/recovery: OK")
    print("RESULT: OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ForPrint module-scoped workflow control."
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--module", default=SUPPORTED_MODULE)
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument(
        "command",
        choices=(
            "list",
            "check",
            "self-audit",
            "self-audit-resume",
            "self-status",
            "self-report-full",
            "modules-status",
        ),
    )
    args = parser.parse_args()

    try:
        root = _root(args.root)
        if args.command == "list":
            return _list(root)
        if args.command == "check":
            return _check(root)
        if args.command == "modules-status":
            return self_audit.status(root, use_color=not args.no_color)
        if args.module != SUPPORTED_MODULE:
            raise WorkflowError(
                f"module {args.module!r} is not implemented in workflow engine v0.1"
            )
        if args.command == "self-audit":
            return self_audit.prepare(root, use_color=not args.no_color)
        if args.command == "self-audit-resume":
            return self_audit.resume(root, use_color=not args.no_color)
        if args.command == "self-status":
            return self_audit.status(root, use_color=not args.no_color)
        if args.command == "self-report-full":
            return self_audit.print_full_report(root)
        raise WorkflowError(f"unsupported command: {args.command}")
    except WorkflowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("RESULT: FAILED", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
