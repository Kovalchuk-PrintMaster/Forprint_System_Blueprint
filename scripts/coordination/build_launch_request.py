from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

LAUNCH_REQUEST_SCHEMA = "forprint_launch_request_v0_1"
DEPENDENCY_READINESS_SCHEMA = "forprint_dependency_readiness_snapshot_v0_1"
TASK_CONTEXT_SCHEMA = "forprint_task_context_manifest_v0_1"

STATE_AWAITING_APPROVAL = "AWAITING_OPERATOR_APPROVAL"
STATE_BLOCKED = "BLOCKED"

BLOCKER_CONTEXT_REVALIDATION = "TASK_CONTEXT_REVALIDATION_FAILED"
BLOCKER_CONTEXT_DRIFT = "TASK_CONTEXT_FINGERPRINT_DRIFT"
BLOCKER_BLUEPRINT_BASELINE = "BLUEPRINT_BASELINE_DRIFT"
BLOCKER_MODULE_BASELINE = "MODULE_BASELINE_DRIFT"
BLOCKER_PROMPT_HASH = "PROMPT_HASH_DRIFT"
BLOCKER_CONTRACT_HASH = "PROMPT_CONTRACT_HASH_DRIFT"
BLOCKER_ORACLE_HASH = "ACCEPTANCE_ORACLE_HASH_DRIFT"
BLOCKER_MODULE_FRESHNESS = "MODULE_FRESH_CONTEXT_NOT_PASS"
BLOCKER_MODULE_DIRTY = "MODULE_UNCLASSIFIED_DIRTY_PATHS"
BLOCKER_DEPENDENCY_MISSING = "DEPENDENCY_READINESS_NOT_PROVIDED"
BLOCKER_DEPENDENCY_INVALID = "DEPENDENCY_READINESS_INVALID"
BLOCKER_DEPENDENCY_BLOCKED = "DEPENDENCY_READINESS_NOT_READY"


@dataclass(frozen=True)
class LaunchRequestResult:
    request_id: str
    state: str
    blocker_codes: tuple[str, ...]
    document: dict[str, Any]


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_yaml_mapping(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{label} is missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a YAML mapping: {path}")
    return data


def _load_task_context_manifest(archive_path: Path) -> tuple[dict[str, Any], str]:
    if not archive_path.is_file():
        raise ValueError(f"task-context archive is missing: {archive_path}")
    archive_sha = _sha256_path(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if names.count("TASK_CONTEXT_MANIFEST.yaml") != 1:
            raise ValueError("task-context archive must contain exactly one manifest")
        manifest = yaml.safe_load(
            archive.read("TASK_CONTEXT_MANIFEST.yaml").decode("utf-8")
        )
    if not isinstance(manifest, dict):
        raise ValueError("task-context manifest must be a YAML mapping")
    if manifest.get("schema_version") != TASK_CONTEXT_SCHEMA:
        raise ValueError("task-context manifest schema is unsupported")
    return manifest, archive_sha


def _load_context_compiler(root: Path):
    compiler_path = root / Path("scripts") / "coordination" / "build_context_bundle.py"
    if not compiler_path.is_file():
        raise ValueError(f"task-context compiler is missing: {compiler_path}")
    spec = importlib.util.spec_from_file_location(
        "forprint_task_context_compiler_runtime",
        compiler_path,
    )
    if spec is None or spec.loader is None:
        raise ValueError("task-context compiler import spec could not be created")
    module = importlib.util.module_from_spec(spec)
    # Dataclass processing inside the dynamically loaded compiler resolves its
    # defining module through sys.modules while exec_module() is running.
    # Register it first so live revalidation follows normal import semantics.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def _recompile_current_task_context(
    *,
    root: Path,
    module: str,
    prompt_id: str,
    module_root: Path,
) -> dict[str, Any]:
    compiler = _load_context_compiler(root)
    result = compiler.build_task_context(
        root=root,
        module=module,
        prompt_id=prompt_id,
        module_root=module_root,
    )
    manifest = result.manifest
    if not isinstance(manifest, dict):
        raise ValueError("recompiled task context manifest is invalid")
    return manifest


def _nested(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _dependency_readiness(
    *,
    dependency_readiness_path: Path | None,
    module: str,
    prompt_id: str,
    context_fingerprint: str,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    if dependency_readiness_path is None:
        return (
            {
                "provided": False,
                "status": "NOT_PROVIDED",
                "path": None,
                "sha256": None,
                "blocking_dependencies": [],
                "evidence": [],
            },
            [
                {
                    "code": BLOCKER_DEPENDENCY_MISSING,
                    "detail": "No dependency-readiness snapshot was supplied.",
                }
            ],
        )

    blockers: list[dict[str, str]] = []
    try:
        data = _load_yaml_mapping(
            dependency_readiness_path,
            label="dependency-readiness snapshot",
        )
    except Exception as exc:
        return (
            {
                "provided": True,
                "status": "INVALID",
                "path": str(dependency_readiness_path),
                "sha256": (
                    _sha256_path(dependency_readiness_path)
                    if dependency_readiness_path.is_file()
                    else None
                ),
                "blocking_dependencies": [],
                "evidence": [],
            },
            [
                {
                    "code": BLOCKER_DEPENDENCY_INVALID,
                    "detail": str(exc),
                }
            ],
        )

    if data.get("schema_version") != DEPENDENCY_READINESS_SCHEMA:
        blockers.append(
            {
                "code": BLOCKER_DEPENDENCY_INVALID,
                "detail": "dependency-readiness schema is unsupported",
            }
        )
    if data.get("module_id") != module:
        blockers.append(
            {
                "code": BLOCKER_DEPENDENCY_INVALID,
                "detail": "dependency-readiness module_id mismatch",
            }
        )
    if data.get("prompt_id") != prompt_id:
        blockers.append(
            {
                "code": BLOCKER_DEPENDENCY_INVALID,
                "detail": "dependency-readiness prompt_id mismatch",
            }
        )
    if data.get("context_fingerprint_sha256") != context_fingerprint:
        blockers.append(
            {
                "code": BLOCKER_DEPENDENCY_INVALID,
                "detail": "dependency-readiness context fingerprint mismatch",
            }
        )

    status = data.get("status")
    blocking = data.get("blocking_dependencies")
    evidence = data.get("evidence")
    if not isinstance(blocking, list):
        blockers.append(
            {
                "code": BLOCKER_DEPENDENCY_INVALID,
                "detail": "blocking_dependencies must be a list",
            }
        )
        blocking = []
    if not isinstance(evidence, list):
        blockers.append(
            {
                "code": BLOCKER_DEPENDENCY_INVALID,
                "detail": "evidence must be a list",
            }
        )
        evidence = []

    if not blockers and (status != "READY" or blocking):
        blockers.append(
            {
                "code": BLOCKER_DEPENDENCY_BLOCKED,
                "detail": (
                    f"dependency-readiness status={status!r}, "
                    f"blocking_dependencies={len(blocking)}"
                ),
            }
        )

    return (
        {
            "provided": True,
            "status": status,
            "path": str(dependency_readiness_path),
            "sha256": _sha256_path(dependency_readiness_path),
            "blocking_dependencies": blocking,
            "evidence": evidence,
            "authority": data.get("authority"),
            "generated_at": data.get("generated_at"),
        },
        blockers,
    )


def build_launch_request(
    *,
    root: Path,
    module_root: Path,
    task_context_archive: Path,
    dependency_readiness_path: Path | None = None,
) -> LaunchRequestResult:
    root = root.resolve()
    module_root = module_root.resolve()
    task_context_archive = task_context_archive.resolve()
    if dependency_readiness_path is not None:
        dependency_readiness_path = dependency_readiness_path.resolve()

    archived, archive_sha = _load_task_context_manifest(task_context_archive)
    identity = archived.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("task-context identity mapping is missing")
    module = identity.get("module_id")
    prompt_id = identity.get("prompt_id")
    archived_fingerprint = identity.get("context_fingerprint_sha256")
    if not all(
        isinstance(value, str) and value
        for value in (module, prompt_id, archived_fingerprint)
    ):
        raise ValueError("task-context identity is incomplete")

    blockers: list[dict[str, str]] = []
    current: dict[str, Any] | None = None
    try:
        current = _recompile_current_task_context(
            root=root,
            module=module,
            prompt_id=prompt_id,
            module_root=module_root,
        )
    except Exception as exc:
        blockers.append(
            {
                "code": BLOCKER_CONTEXT_REVALIDATION,
                "detail": str(exc),
            }
        )

    if current is not None:
        current_fingerprint = _nested(
            current,
            "identity",
            "context_fingerprint_sha256",
        )
        if current_fingerprint != archived_fingerprint:
            blockers.append(
                {
                    "code": BLOCKER_CONTEXT_DRIFT,
                    "detail": "task-context fingerprint no longer matches live state",
                }
            )

        comparisons = [
            (
                BLOCKER_BLUEPRINT_BASELINE,
                _nested(archived, "repository_baseline", "blueprint", "head"),
                _nested(current, "repository_baseline", "blueprint", "head"),
            ),
            (
                BLOCKER_MODULE_BASELINE,
                _nested(archived, "repository_baseline", "module", "head"),
                _nested(current, "repository_baseline", "module", "head"),
            ),
            (
                BLOCKER_PROMPT_HASH,
                _nested(archived, "task_prompt", "sha256"),
                _nested(current, "task_prompt", "sha256"),
            ),
            (
                BLOCKER_CONTRACT_HASH,
                _nested(archived, "prompt_contract", "sha256"),
                _nested(current, "prompt_contract", "sha256"),
            ),
            (
                BLOCKER_ORACLE_HASH,
                _nested(archived, "acceptance_oracle", "sha256"),
                _nested(current, "acceptance_oracle", "sha256"),
            ),
        ]
        for code, expected, observed in comparisons:
            if expected != observed:
                blockers.append(
                    {
                        "code": code,
                        "detail": f"archived={expected!r}, live={observed!r}",
                    }
                )

        if _nested(current, "module_self_knowledge", "fresh_context_state") != "PASS":
            blockers.append(
                {
                    "code": BLOCKER_MODULE_FRESHNESS,
                    "detail": "module fresh-context state is not PASS",
                }
            )
        unclassified = _nested(
            current,
            "module_self_knowledge",
            "unclassified_dirty_paths",
        )
        if unclassified != []:
            blockers.append(
                {
                    "code": BLOCKER_MODULE_DIRTY,
                    "detail": f"unclassified_dirty_paths={unclassified!r}",
                }
            )

    dependency, dependency_blockers = _dependency_readiness(
        dependency_readiness_path=dependency_readiness_path,
        module=module,
        prompt_id=prompt_id,
        context_fingerprint=archived_fingerprint,
    )
    blockers.extend(dependency_blockers)

    blocker_codes = tuple(sorted({item["code"] for item in blockers}))
    state = STATE_AWAITING_APPROVAL if not blocker_codes else STATE_BLOCKED

    stable_identity = {
        "module_id": module,
        "prompt_id": prompt_id,
        "task_context_archive_sha256": archive_sha,
        "context_fingerprint_sha256": archived_fingerprint,
        "blueprint_head": _nested(
            archived,
            "repository_baseline",
            "blueprint",
            "head",
        ),
        "module_head": _nested(
            archived,
            "repository_baseline",
            "module",
            "head",
        ),
        "dependency_readiness_sha256": dependency.get("sha256"),
    }
    request_fingerprint = hashlib.sha256(
        json.dumps(
            stable_identity,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    request_id = f"{module}__{prompt_id}__launch__{request_fingerprint[:16]}"

    document: dict[str, Any] = {
        "schema_version": LAUNCH_REQUEST_SCHEMA,
        "request_id": request_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "state": state,
        "identity": {
            "module_id": module,
            "prompt_id": prompt_id,
            "task_context_id": archived.get("task_context_id"),
            "context_fingerprint_sha256": archived_fingerprint,
            "request_fingerprint_sha256": request_fingerprint,
        },
        "task_context": {
            "archive_path": str(task_context_archive),
            "archive_sha256": archive_sha,
            "schema_version": archived.get("schema_version"),
        },
        "repository_revalidation": {
            "performed": True,
            "current_task_context_recompiled": current is not None,
            "blueprint_head": (
                _nested(current, "repository_baseline", "blueprint", "head")
                if current is not None
                else None
            ),
            "module_head": (
                _nested(current, "repository_baseline", "module", "head")
                if current is not None
                else None
            ),
            "fresh_context_state": (
                _nested(current, "module_self_knowledge", "fresh_context_state")
                if current is not None
                else None
            ),
            "unclassified_dirty_paths": (
                _nested(
                    current,
                    "module_self_knowledge",
                    "unclassified_dirty_paths",
                )
                if current is not None
                else None
            ),
        },
        "dependency_readiness": dependency,
        "eligibility": {
            "eligible_for_operator_approval": state == STATE_AWAITING_APPROVAL,
            "blocker_count": len(blocker_codes),
            "blockers": blockers,
        },
        "operator_approval": {
            "required": True,
            "decision": "NOT_DECIDED",
            "approval_artifact": None,
            "approval_gateway_implemented": False,
        },
        "execution_boundaries": {
            "worker_dispatch_allowed": False,
            "prompt_claim_allowed": False,
            "blueprint_accept_allowed": False,
            "next_prompt_release_allowed": False,
            "module_repository_write_allowed": False,
            "telegram_required": False,
        },
        "next_gate": (
            "OPERATOR_APPROVAL_GATEWAY"
            if state == STATE_AWAITING_APPROVAL
            else "RESOLVE_BLOCKERS_AND_REBUILD_REQUEST"
        ),
    }

    return LaunchRequestResult(
        request_id=request_id,
        state=state,
        blocker_codes=blocker_codes,
        document=document,
    )


def write_launch_request(
    *,
    result: LaunchRequestResult,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"{result.request_id}__{timestamp}.yaml"
    if output_path.exists():
        raise ValueError(f"launch-request artifact already exists: {output_path}")
    output_path.write_text(
        yaml.safe_dump(
            result.document,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )
    return output_path


def render_summary(
    result: LaunchRequestResult,
    *,
    output_path: Path | None,
) -> str:
    lines = [
        "LAUNCH_REQUEST_GATE=PASS",
        f"REQUEST_ID={result.request_id}",
        f"STATE={result.state}",
        f"BLOCKER_COUNT={len(result.blocker_codes)}",
        "BLOCKERS=" + ",".join(result.blocker_codes),
        "OPERATOR_APPROVAL_REQUIRED=true",
        "OPERATOR_APPROVAL_DECISION=NOT_DECIDED",
        "WORKER_DISPATCH_ALLOWED=false",
        "PROMPT_CLAIM_ALLOWED=false",
    ]
    if output_path is not None:
        lines.append(f"LAUNCH_REQUEST_PATH={output_path}")
        lines.append(f"LAUNCH_REQUEST_SHA256={_sha256_path(output_path)}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build and revalidate an immutable ForPrint launch request. "
            "This gate never approves or dispatches a worker."
        )
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--module-root", required=True)
    parser.add_argument("--task-context-archive", required=True)
    parser.add_argument("--dependency-readiness", default=None)
    parser.add_argument("--output-dir", default="tmp/control_plane/launch_requests")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--print", action="store_true")
    parser.add_argument("--require-eligible", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    module_root = Path(args.module_root).resolve()
    archive = Path(args.task_context_archive).resolve()
    dependency = (
        Path(args.dependency_readiness).resolve()
        if args.dependency_readiness
        else None
    )

    try:
        result = build_launch_request(
            root=root,
            module_root=module_root,
            task_context_archive=archive,
            dependency_readiness_path=dependency,
        )
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    if args.print:
        print(
            yaml.safe_dump(
                result.document,
                sort_keys=False,
                allow_unicode=True,
                width=112,
            ).rstrip()
        )
    elif args.no_write:
        print(render_summary(result, output_path=None))
    else:
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = root / output_dir
        output_path = write_launch_request(result=result, output_dir=output_dir)
        print(render_summary(result, output_path=output_path))

    if args.require_eligible and result.state != STATE_AWAITING_APPROVAL:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
