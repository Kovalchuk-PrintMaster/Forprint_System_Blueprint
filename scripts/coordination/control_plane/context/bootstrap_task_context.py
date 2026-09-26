from __future__ import annotations

import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.control_plane.worker_runtime.bootstrap_profile import (
    BootstrapRuntimeError,
    resolve_bootstrap_runtime,
)

SCHEMA = "forprint_bootstrap_task_context_envelope_v0_1"
EXECUTION_CLASS = "MODULE_BOOTSTRAP"
STATE_READY = "BOOTSTRAP_READY"
STATE_BLOCKED = "BLOCKED"

DEBT_LOCAL_WORKTREE_DIRTY = "LOCAL_WORKTREE_DIRTY"
DEBT_FRESH_CONTEXT_MISSING = "FRESH_CONTEXT_MISSING"
DEBT_FRESH_CONTEXT_STALE = "FRESH_CONTEXT_STALE"
DEBT_MODULE_MEMORY_INCOMPLETE = "MODULE_MEMORY_INCOMPLETE"
DEBT_RUNTIME_PROFILE_MISSING = "MODULE_RUNTIME_PROFILE_MISSING"

MODULE_MEMORY_ROOT = ("coordination", "module_memory")
DEFAULT_MODULE_MEMORY = tuple(
    Path(*MODULE_MEMORY_ROOT, name).as_posix()
    for name in (
        "module_memory.yaml",
        "inventory_index.yaml",
        "implementation_lineage.yaml",
        "document_authority.yaml",
        "roadmap_state.yaml",
    )
)
FRESH_CONTEXT = Path(
    *MODULE_MEMORY_ROOT,
    "fresh_context_manifest.yaml",
).as_posix()
RUNTIME_PROFILE = Path("config", "worker_runtime.yaml").as_posix()


class BootstrapContextError(ValueError):
    pass


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_yaml_mapping(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise BootstrapContextError(f"{label} missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BootstrapContextError(f"{label} must be a YAML mapping: {path}")
    return data


def _git(repo: Path, *args: str, allow_failure: bool = False) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode and not allow_failure:
        raise BootstrapContextError(
            f"git {' '.join(args)} failed in {repo}: {result.stdout.strip()}"
        )
    return result.returncode, result.stdout.strip()


def _porcelain(repo: Path) -> list[str]:
    _, output = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    return [line for line in output.splitlines() if line]


def _nested(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _fresh_context_head(module_root: Path) -> tuple[str | None, str]:
    path = module_root / FRESH_CONTEXT
    if not path.is_file():
        return None, DEBT_FRESH_CONTEXT_MISSING
    try:
        data = load_yaml_mapping(path, label="module fresh-context manifest")
    except BootstrapContextError:
        return None, DEBT_FRESH_CONTEXT_STALE
    head = _nested(data, "repository", "head")
    if not isinstance(head, str) or not head:
        return None, DEBT_FRESH_CONTEXT_STALE
    return head, ""


def build_bootstrap_task_context(
    *,
    blueprint_root: Path,
    module_root: Path,
    module_id: str,
    prompt_id: str,
    prompt_path: Path,
    prompt_contract_path: Path,
    release_authorization_path: Path,
    acceptance_oracle_path: Path,
    stage_0_policy_path: Path,
) -> dict[str, Any]:
    blueprint_root = blueprint_root.resolve()
    module_root = module_root.resolve()
    prompt_path = prompt_path.resolve()
    prompt_contract_path = prompt_contract_path.resolve()
    release_authorization_path = release_authorization_path.resolve()
    acceptance_oracle_path = acceptance_oracle_path.resolve()
    stage_0_policy_path = stage_0_policy_path.resolve()

    if not module_root.is_dir():
        raise BootstrapContextError("module repository is not reachable")
    _, module_head = _git(module_root, "rev-parse", "HEAD")
    _, module_branch = _git(module_root, "branch", "--show-current")
    if not module_branch:
        raise BootstrapContextError("detached module HEAD is not bootstrap-ready")

    rc, module_upstream = _git(
        module_root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{u}",
        allow_failure=True,
    )
    if rc:
        module_upstream = ""

    _, blueprint_head = _git(blueprint_root, "rev-parse", "HEAD")

    load_yaml_mapping(
        prompt_contract_path,
        label="prompt contract",
    )
    release_authorization = load_yaml_mapping(
        release_authorization_path,
        label="release authorization",
    )
    policy = load_yaml_mapping(stage_0_policy_path, label="bootstrap execution policy")

    # Fail closed on identity/authority. Bootstrap mode relaxes freshness, not authority.
    authorization = release_authorization.get("authorization")
    if not isinstance(authorization, dict):
        raise BootstrapContextError("release authorization payload missing")
    if authorization.get("module") != module_id:
        raise BootstrapContextError("release authorization module mismatch")
    if authorization.get("prompt_id") != prompt_id:
        raise BootstrapContextError("release authorization prompt mismatch")
    if authorization.get("explicit_user_execution_required") is not True:
        raise BootstrapContextError("explicit user execution requirement missing")

    authority_basis = release_authorization.get("authority_basis")
    if not isinstance(authority_basis, dict):
        raise BootstrapContextError("release authority basis missing")

    contract_rel = prompt_contract_path.relative_to(blueprint_root).as_posix()
    oracle_rel = acceptance_oracle_path.relative_to(blueprint_root).as_posix()
    if authority_basis.get("prompt_contract") != contract_rel:
        raise BootstrapContextError("release authorization contract path mismatch")
    if authority_basis.get("prompt_contract_sha256") != sha256_path(prompt_contract_path):
        raise BootstrapContextError("release authorization contract SHA mismatch")
    if authority_basis.get("acceptance_oracle") != oracle_rel:
        raise BootstrapContextError("release authorization oracle path mismatch")
    if authority_basis.get("acceptance_oracle_sha256") != sha256_path(acceptance_oracle_path):
        raise BootstrapContextError("release authorization oracle SHA mismatch")

    execution_classes = policy.get("execution_classes")
    if not isinstance(execution_classes, dict):
        raise BootstrapContextError("bootstrap policy execution classes missing")
    bootstrap_policy = execution_classes.get(EXECUTION_CLASS)
    if not isinstance(bootstrap_policy, dict):
        raise BootstrapContextError("MODULE_BOOTSTRAP policy missing")
    if bootstrap_policy.get("requires_stage_0_local_hygiene") is not True:
        raise BootstrapContextError("Stage 0 local hygiene is not required by policy")

    debt: list[dict[str, Any]] = []
    dirty = _porcelain(module_root)
    if dirty:
        debt.append(
            {
                "code": DEBT_LOCAL_WORKTREE_DIRTY,
                "blocking_for_bootstrap": False,
                "blocking_for_development": True,
                "detail": {"porcelain_entries": dirty},
                "required_resolution": "MODULE_ASSISTANT_STAGE_0_LOCAL_HYGIENE",
            }
        )

    observed_fresh_head, fresh_error = _fresh_context_head(module_root)
    if fresh_error:
        debt.append(
            {
                "code": fresh_error,
                "blocking_for_bootstrap": False,
                "blocking_for_development": True,
                "detail": {"expected_module_head": module_head},
                "required_resolution": "MODULE_ASSISTANT_REFRESH_GENERATED_FRESHNESS",
            }
        )
    elif observed_fresh_head != module_head:
        debt.append(
            {
                "code": DEBT_FRESH_CONTEXT_STALE,
                "blocking_for_bootstrap": False,
                "blocking_for_development": True,
                "detail": {
                    "observed_fresh_context_head": observed_fresh_head,
                    "expected_module_head": module_head,
                },
                "required_resolution": "MODULE_ASSISTANT_REFRESH_GENERATED_FRESHNESS",
            }
        )

    missing_memory = [rel for rel in DEFAULT_MODULE_MEMORY if not (module_root / rel).is_file()]
    if missing_memory:
        debt.append(
            {
                "code": DEBT_MODULE_MEMORY_INCOMPLETE,
                "blocking_for_bootstrap": False,
                "blocking_for_development": True,
                "detail": {"missing_paths": missing_memory},
                "required_resolution": "BOOTSTRAP_PROMPT_SELF_KNOWLEDGE_RECONCILIATION",
            }
        )

    try:
        bootstrap_runtime = resolve_bootstrap_runtime(
            blueprint_root=blueprint_root,
            module_root=module_root,
            execution_class=EXECUTION_CLASS,
        )
    except BootstrapRuntimeError as exc:
        bootstrap_runtime = {
            "source": "UNRESOLVED",
            "error": str(exc),
            "worker_process_started": False,
        }
        debt.append(
            {
                "code": DEBT_RUNTIME_PROFILE_MISSING,
                "blocking_for_bootstrap": False,
                "blocking_for_development": True,
                "detail": {
                    "expected_module_path": RUNTIME_PROFILE,
                    "blueprint_bootstrap_fallback": "unavailable",
                    "reason": str(exc),
                },
                "required_resolution": "RESTORE_BLUEPRINT_BOOTSTRAP_RUNTIME_OR_CREATE_MODULE_PROFILE",
            }
        )

    stage_0 = policy.get("stage_0_module_local_hygiene")
    if not isinstance(stage_0, dict):
        raise BootstrapContextError("Stage 0 policy missing")

    evidence = []
    for kind, path in (
        ("approved_prompt", prompt_path),
        ("prompt_contract", prompt_contract_path),
        ("release_authorization", release_authorization_path),
        ("acceptance_oracle", acceptance_oracle_path),
        ("bootstrap_execution_policy", stage_0_policy_path),
    ):
        if not path.is_file():
            raise BootstrapContextError(f"{kind} missing: {path}")
        evidence.append(
            {
                "kind": kind,
                "path": path.relative_to(blueprint_root).as_posix(),
                "sha256": sha256_path(path),
            }
        )

    module_agents = module_root / "AGENTS.md"
    if module_agents.is_file():
        evidence.append(
            {
                "kind": "module_agents",
                "path": "AGENTS.md",
                "sha256": sha256_path(module_agents),
                "repository": module_id,
            }
        )

    envelope = {
        "schema_version": SCHEMA,
        "execution_class": EXECUTION_CLASS,
        "state": STATE_READY,
        "module_id": module_id,
        "prompt_id": prompt_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "authority": {
            "release_authorization_required": True,
            "release_authorization_validated": True,
            "prompt_contract_is_execution_authority": False,
            "bootstrap_policy": stage_0_policy_path.relative_to(blueprint_root).as_posix(),
        },
        "repository_baseline": {
            "blueprint": {"head": blueprint_head},
            "module": {
                "head": module_head,
                "branch": module_branch,
                "upstream": module_upstream or None,
            },
        },
        "bootstrap_runtime": bootstrap_runtime,
        "bootstrap_debt": debt,
        "bootstrap_debt_count": len(debt),
        "strict_development_context_ready": len(debt) == 0,
        "stage_0": {
            "required": True,
            "owner": stage_0.get("owner"),
            "steps": stage_0.get("steps", []),
            "module_local_commit_allowed": stage_0.get("module_local_commit_allowed") is True,
            "module_local_push_allowed": stage_0.get("module_local_push_allowed") is True,
            "forbidden": stage_0.get("forbidden", []),
            "must_rebuild_strict_task_context_after_stage_0": True,
        },
        "execution_boundaries": {
            "roadmap_development_allowed_before_stage_0": False,
            "production_provider_writes_allowed": False,
            "cross_repository_writes_allowed": False,
            "automatic_blueprint_accept": False,
            "automatic_next_prompt_release": False,
        },
        "canonical_task_context_compiler": {
            "primitive": "scripts/coordination/build_context_bundle.py",
            "strict_mode_preserved": True,
            "bootstrap_envelope_does_not_replace_strict_task_context": True,
            "strict_task_context_required_after_stage_0": True,
        },
        "evidence": evidence,
    }

    # Content fingerprint excludes generated_at.
    fingerprint_source = yaml.safe_dump(
        {k: v for k, v in envelope.items() if k != "generated_at"},
        sort_keys=True,
        allow_unicode=True,
    ).encode("utf-8")
    envelope["bootstrap_context_fingerprint_sha256"] = hashlib.sha256(
        fingerprint_source
    ).hexdigest()
    return envelope


def write_bootstrap_task_context(
    *,
    envelope: dict[str, Any],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    fingerprint = envelope["bootstrap_context_fingerprint_sha256"]
    path = output_dir / (
        f"{envelope['module_id']}__{envelope['prompt_id']}"
        f"__bootstrap_context__{fingerprint[:16]}.yaml"
    )
    payload = yaml.safe_dump(
        envelope,
        sort_keys=False,
        allow_unicode=True,
        width=112,
    )
    if path.exists() and path.read_text(encoding="utf-8") != payload:
        raise BootstrapContextError(f"bootstrap context identity conflict: {path}")
    if not path.exists():
        path.write_text(payload, encoding="utf-8")
    return path
