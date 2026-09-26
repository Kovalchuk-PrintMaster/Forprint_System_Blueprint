#!/usr/bin/env python3
"""Control Plane task-context adapter for external prompts and Blueprint internal tasks.

This is a facade, not a second Task Context authority:
- EXTERNAL_PROMPT_QUEUE delegates unchanged to build_context_bundle.py --task-context.
- MANUAL_INTERNAL compiles an authority-neutral Blueprint-native context from the
  accepted Worker Task Envelope plus the canonical continuity source-state fingerprint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.coordination.continuity import build_source_state  # noqa: E402
from scripts.coordination.control_plane.tasking import (  # noqa: E402
    compile_task_envelope,
    validate_task_envelope,
)
from scripts.coordination.control_plane.tasking.sources import (  # noqa: E402
    manual_internal_source,
)

INTERNAL_MODULE_ID = "forprint_system_blueprint"
INTERNAL_TASK_INDEX = Path(
    "coordination/internal_work/blueprint/worker_tasks/index.yaml"
)
EXTERNAL_TASK_CONTEXT_BUILDER = Path(
    "scripts/coordination/build_context_bundle.py"
)
SCHEMA_VERSION = "forprint_blueprint_internal_task_context_v0_1"


class TaskContextAdapterError(RuntimeError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise TaskContextAdapterError(f"required YAML missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TaskContextAdapterError(f"top-level mapping required: {path}")
    return data


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_module_root(root: Path, module_root: str) -> Path:
    candidate = Path(module_root)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def resolve_internal_task(
    root: Path,
    task_id: str,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    index_path = root / INTERNAL_TASK_INDEX
    index = _load_yaml(index_path)
    if index.get("schema_version") != "forprint_blueprint_worker_task_index_v0_1":
        raise TaskContextAdapterError("internal worker task index schema mismatch")
    if index.get("authority") != "none":
        raise TaskContextAdapterError("internal worker task index must be authority=none")

    rows = index.get("tasks")
    if not isinstance(rows, list):
        raise TaskContextAdapterError("internal worker task index tasks[] missing")

    matches = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("task_id") == task_id
    ]
    if len(matches) != 1:
        raise TaskContextAdapterError(
            f"internal task id {task_id!r} must resolve exactly once"
        )

    row = matches[0]
    if row.get("status") != "READY_FOR_CONTEXT":
        raise TaskContextAdapterError(
            f"internal task {task_id!r} is not READY_FOR_CONTEXT"
        )

    file_name = row.get("file")
    if not isinstance(file_name, str) or not file_name.strip():
        raise TaskContextAdapterError("internal task row file is required")
    if "/" in file_name or "\\" in file_name:
        raise TaskContextAdapterError("internal task row file must be a local basename")

    task_path = index_path.parent / file_name
    task = _load_yaml(task_path)
    if task.get("task_id") != task_id:
        raise TaskContextAdapterError("internal task artifact task_id mismatch")
    if task.get("module_id") != INTERNAL_MODULE_ID:
        raise TaskContextAdapterError("internal task module_id mismatch")
    if task.get("status") != "READY_FOR_CONTEXT":
        raise TaskContextAdapterError("internal task artifact is not READY_FOR_CONTEXT")

    row_work_front = row.get("work_front_id")
    task_work = task.get("work")
    if not isinstance(task_work, dict):
        raise TaskContextAdapterError("internal task work mapping missing")
    if task_work.get("work_front_id") != row_work_front:
        raise TaskContextAdapterError("internal task work_front_id index mismatch")
    if task_work.get("work_id") != row.get("work_id"):
        raise TaskContextAdapterError("internal task work_id index mismatch")

    return task_path, task, row


def _nonempty_string_list(value: Any, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise TaskContextAdapterError(f"{label} must be a non-empty string list")
    return [item.strip() for item in value]


def build_internal_task_context(
    root: Path,
    *,
    task_id: str,
    module_root: str,
) -> dict[str, Any]:
    root = root.resolve()
    resolved_module_root = _resolve_module_root(root, module_root)
    if resolved_module_root != root:
        raise TaskContextAdapterError(
            "MANUAL_INTERNAL module_root must resolve to Blueprint repository root"
        )

    task_path, task, _row = resolve_internal_task(root, task_id)

    source = task.get("source")
    if not isinstance(source, dict):
        raise TaskContextAdapterError("internal task source mapping missing")
    if source.get("type") != "MANUAL_INTERNAL":
        raise TaskContextAdapterError("internal task source type mismatch")
    if source.get("generation_mode") != "MANUAL":
        raise TaskContextAdapterError("internal task generation_mode mismatch")
    if source.get("raw_chat_is_authority") is not False:
        raise TaskContextAdapterError("raw chat cannot be task authority")

    work = task.get("work")
    profile = task.get("execution_profile")
    procedure = task.get("procedure")
    authority = task.get("authority")
    if not all(isinstance(value, dict) for value in (work, profile, procedure, authority)):
        raise TaskContextAdapterError(
            "work/profile/procedure/authority mappings are required"
        )

    if authority.get("execution_authority_source") != "WORK_FRONT":
        raise TaskContextAdapterError("Work Front must remain execution authority")
    if authority.get("task_artifact_grants_authority") is not False:
        raise TaskContextAdapterError("task artifact must not grant authority")
    for key in (
        "dispatch_authority",
        "release_authority",
        "push_authority",
        "merge_authority",
        "foreign_write_authority",
        "automatic_accept",
        "widening_requested",
    ):
        if authority.get(key) is not False:
            raise TaskContextAdapterError(f"internal task authority widened: {key}")

    relative_task_path = task_path.relative_to(root).as_posix()
    envelope = compile_task_envelope(
        task_id=task_id,
        module_id=INTERNAL_MODULE_ID,
        source=manual_internal_source(
            artifact_ref=relative_task_path,
            created_by=str(source.get("created_by") or "operator_assistant"),
        ),
        work_id=str(work.get("work_id") or ""),
        work_front_id=str(work.get("work_front_id") or ""),
        objective=str(task.get("objective") or ""),
        instructions=_nonempty_string_list(task.get("instructions"), "instructions"),
        acceptance=_nonempty_string_list(task.get("acceptance"), "acceptance"),
        stop_conditions=_nonempty_string_list(
            task.get("stop_conditions"),
            "stop_conditions",
        ),
        execution_profile_id=str(profile.get("profile_id") or ""),
        execution_profile_revision=str(profile.get("revision") or ""),
        procedure_id=str(procedure.get("procedure_id") or ""),
        procedure_revision=str(procedure.get("revision") or ""),
    )
    errors = validate_task_envelope(envelope)
    if errors:
        raise TaskContextAdapterError("; ".join(errors))

    source_state = build_source_state(root)
    fingerprint = source_state.get("fingerprint_sha256")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise TaskContextAdapterError(
            "canonical continuity source-state fingerprint missing"
        )

    context: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        "module_id": INTERNAL_MODULE_ID,
        "source_type": "MANUAL_INTERNAL",
        "task_artifact": {
            "path": relative_task_path,
            "sha256": _sha256_file(task_path),
        },
        "task_envelope": envelope,
        "source_state": {
            "provider": "scripts.coordination.continuity.build_source_state",
            "schema_version": source_state.get("schema_version"),
            "source_mode": source_state.get("source_mode"),
            "git_head": source_state.get("git_head"),
            "git_branch": source_state.get("git_branch"),
            "fingerprint_sha256": fingerprint,
            "durable_dirty_path_count": len(
                source_state.get("durable_dirty_paths") or []
            ),
        },
        "authority": {
            "context_grants_authority": False,
            "execution_authority_source": "WORK_FRONT",
            "dispatch_authority_conferred": False,
            "release_authority_conferred": False,
            "foreign_write_authority_conferred": False,
        },
    }
    context["task_context_id"] = _sha256_bytes(_canonical_json(context))
    return context


def build_external_argv(
    root: Path,
    *,
    prompt_id: str,
    module_root: str,
    module: str | None,
    no_write: bool,
    output_dir: str | None,
    print_bundle: bool,
) -> list[str]:
    builder = root / EXTERNAL_TASK_CONTEXT_BUILDER
    if not builder.is_file():
        raise TaskContextAdapterError(
            f"external Task Context builder missing: {builder}"
        )
    argv = [
        sys.executable,
        str(builder),
        "--task-context",
        "--prompt-id",
        prompt_id,
        "--module-root",
        module_root,
    ]
    if module:
        argv.extend(["--module", module])
    if no_write:
        argv.append("--no-write")
    if output_dir:
        argv.extend(["--output-dir", output_dir])
    if print_bundle:
        argv.append("--print")
    return argv


def delegate_external(
    root: Path,
    *,
    prompt_id: str,
    module_root: str,
    module: str | None,
    no_write: bool,
    output_dir: str | None,
    print_bundle: bool,
) -> int:
    argv = build_external_argv(
        root,
        prompt_id=prompt_id,
        module_root=module_root,
        module=module,
        no_write=no_write,
        output_dir=output_dir,
        print_bundle=print_bundle,
    )
    cp = subprocess.run(
        argv,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=1800,
    )
    print(cp.stdout, end="" if cp.stdout.endswith("\n") else "\n")
    return cp.returncode


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-context", action="store_true")
    parser.add_argument("--prompt-id", required=True)
    parser.add_argument("--module-root", required=True)
    parser.add_argument("--module")
    parser.add_argument("--output-dir")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--print", dest="print_bundle", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = PROJECT_ROOT.resolve()

    if not args.task_context:
        print("FAILED: --task-context is required")
        return 2

    try:
        if args.module == INTERNAL_MODULE_ID:
            if not args.no_write:
                raise TaskContextAdapterError(
                    "MANUAL_INTERNAL v0.1 supports no-write context compilation only"
                )
            if args.output_dir or args.print_bundle:
                raise TaskContextAdapterError(
                    "MANUAL_INTERNAL v0.1 does not emit task-context archives yet"
                )

            context = build_internal_task_context(
                root,
                task_id=args.prompt_id,
                module_root=args.module_root,
            )
            print("TASK_CONTEXT_COMPILER=PASS")
            print("TASK_CONTEXT_ADAPTER=CONTROL_PLANE")
            print("TASK_CONTEXT_MODE=MANUAL_INTERNAL")
            print(f"TASK_CONTEXT_ID={context['task_context_id']}")
            print(f"TASK_ID={context['task_id']}")
            print(f"MODULE_ID={context['module_id']}")
            print(
                "TASK_ARTIFACT="
                + str(context["task_artifact"]["path"])
            )
            print(
                "SOURCE_STATE_FINGERPRINT="
                + str(context["source_state"]["fingerprint_sha256"])
            )
            print("EXECUTION_AUTHORITY_SOURCE=WORK_FRONT")
            print("DISPATCH_AUTHORITY_CONFERRED=false")
            print("RELEASE_AUTHORITY_CONFERRED=false")
            print("FOREIGN_WRITE_AUTHORITY_CONFERRED=false")
            print("MUTATION_PERFORMED=false")
            return 0

        return delegate_external(
            root,
            prompt_id=args.prompt_id,
            module_root=args.module_root,
            module=args.module,
            no_write=args.no_write,
            output_dir=args.output_dir,
            print_bundle=args.print_bundle,
        )

    except Exception as exc:
        print("TASK_CONTEXT_COMPILER=FAIL")
        print(f"ERROR={type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
