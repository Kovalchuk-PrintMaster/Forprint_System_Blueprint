#!/usr/bin/env python3
# Build a committed-source MODULE_BOOTSTRAP_COMMISSION archive.

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

import yaml

SCRIPT_ID = "forprint_module_bootstrap_commission_builder_v0_1"
REQUEST_SCHEMA = "forprint_module_bootstrap_commission_request_v0_1"
PACKAGE_CLASS = "MODULE_BOOTSTRAP_COMMISSION"

CLASSIFICATIONS = {
    "EXISTING_REGISTERED_MODULE",
    "NEW_TOP_LEVEL_MODULE_CANDIDATE",
    "EXPERIMENTAL_CAPABILITY_INSIDE_EXISTING_MODULE",
    "HELPER_OR_LAB_NOT_YET_A_MODULE",
}

BLUEPRINT_REFERENCE_PATHS = [
    "coordination/instruction_intake/assistant_reading_order.md",
    "coordination/instruction_intake/instruction_sources.yaml",
    "coordination/global_policy/forprint_project_doctrine.md",
    "coordination/global_policy/clean_tree_first_working_policy_v0_1.md",
    "coordination/standards/index.yaml",
    "coordination/standards/governance/clean_repository_root_policy_v0_1.yaml",
    "coordination/standards/governance/new_module_bootstrap_protocol_v0_1.md",
    "coordination/standards/governance/module_bootstrap_commission_contract_v0_1.yaml",
    "coordination/instruction_intake/bootstrap/forprint_roadmap_operating_contract_v0_1.yaml",
    "coordination/standards/module_assistant_start_protocol.md",
    "coordination/standards/project_structure_standard.md",
    "coordination/standards/repository_structure_baseline.md",
    "coordination/standards/make_command_standard.md",
    "coordination/standards/module_make_target_contract.md",
    "coordination/standards/module_pre_commit_protocol.md",
    "coordination/standards/governance/folder_architecture_policy.md",
    "coordination/standards/governance/documentation_and_recovery_gate.md",
    "coordination/standards/modular_topology_and_resilience/module_global_context_policy.md",
    "coordination/standards/modular_topology_and_resilience/data_ownership_and_storage_policy.md",
]

TEMPLATE_PATHS = [
    "coordination/templates/module_makefile_standard.template.mk",
    "coordination/templates/module_bootstrap/AGENTS.md.template",
    "coordination/templates/module_bootstrap/START_HERE.template.md",
    "coordination/templates/module_bootstrap/module_bootstrap_manifest.template.yaml",
    "coordination/templates/module_bootstrap/new_module_assistant_commissioning_prompt_v0_1.md",
]

TOOL_PATHS = [
    "tools/module_bootstrap/module_assistant_context.py",
]

PORTFOLIO_PATHS = [
    "machine/modules.yaml",
    "machine/ownership.yaml",
    "coordination/roadmaps/details/forprint_system_blueprint/portfolio_module_roadmap_approval_matrix_v0_1.yaml",
]


class CommissionError(RuntimeError):
    pass


def run(root: Path, *args: str, allow_fail: bool = False) -> tuple[int, str]:
    cp = subprocess.run(
        list(args),
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if cp.returncode and not allow_fail:
        raise CommissionError(f"COMMAND_FAILED={' '.join(args)}\n{cp.stdout}")
    return cp.returncode, cp.stdout.rstrip("\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_yaml(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=140),
        encoding="utf-8",
    )


def git_blob(root: Path, head: str, rel: str) -> bytes:
    cp = subprocess.run(
        ["git", "show", f"{head}:{rel}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if cp.returncode:
        raise CommissionError(
            f"COMMITTED_SOURCE_MISSING={rel}|"
            + cp.stderr.decode("utf-8", errors="replace")
        )
    return cp.stdout


def git_blob_optional(root: Path, head: str, rel: str) -> bytes | None:
    cp = subprocess.run(
        ["git", "show", f"{head}:{rel}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return cp.stdout if cp.returncode == 0 else None


def safe_rel_source(raw: str) -> str:
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts or raw.startswith(".git/"):
        raise CommissionError(f"UNSAFE_ADDITIONAL_SOURCE={raw}")
    return p.as_posix()


def load_request(path: Path) -> dict:
    if not path.is_file():
        raise CommissionError(f"REQUEST_MISSING={path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CommissionError("REQUEST_NOT_MAPPING")
    if data.get("schema_version") != REQUEST_SCHEMA:
        raise CommissionError(
            f"REQUEST_SCHEMA_MISMATCH={data.get('schema_version')}"
        )
    if data.get("package_class") != PACKAGE_CLASS:
        raise CommissionError(
            f"PACKAGE_CLASS_MISMATCH={data.get('package_class')}"
        )

    target = data.get("target") or {}
    classification = target.get("classification")
    if classification not in CLASSIFICATIONS:
        raise CommissionError(f"INVALID_CLASSIFICATION={classification}")

    module_id = str(target.get("module_id") or "").strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_\-]{1,79}", module_id):
        raise CommissionError(f"INVALID_MODULE_ID={module_id}")

    if not str(target.get("module_name") or "").strip():
        raise CommissionError("MODULE_NAME_REQUIRED")
    if not str(target.get("purpose") or "").strip():
        raise CommissionError("PURPOSE_REQUIRED")
    if not isinstance(target.get("must_not_own"), list) or not target["must_not_own"]:
        raise CommissionError("MUST_NOT_OWN_REQUIRED")

    authority = data.get("authority") or {}
    if not str(authority.get("operator_task_ref") or "").strip():
        raise CommissionError("OPERATOR_TASK_REF_REQUIRED")
    if authority.get("allowed_scope") != "bootstrap_only":
        raise CommissionError("ALLOWED_SCOPE_MUST_BE_BOOTSTRAP_ONLY")
    if authority.get("may_enter_module_specific_implementation") is not False:
        raise CommissionError("MODULE_SPECIFIC_IMPLEMENTATION_MUST_BE_FALSE")

    bootstrap = data.get("bootstrap") or {}
    manifest = bootstrap.get(
        "canonical_manifest_path",
        "coordination/module/manifest.yaml",
    )
    if manifest != "coordination/module/manifest.yaml":
        exceptions = bootstrap.get("hard_root_path_exceptions") or []
        if not exceptions:
            raise CommissionError(
                "NONDEFAULT_MANIFEST_REQUIRES_HARD_EXCEPTION"
            )

    return data


def repo_state(root: Path) -> dict:
    branch = run(root, "git", "branch", "--show-current")[1]
    head = run(root, "git", "rev-parse", "HEAD")[1]
    upstream_head = run(root, "git", "rev-parse", "@{u}")[1]
    upstream_ref = run(
        root,
        "git",
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{u}",
    )[1]
    if head != upstream_head:
        raise CommissionError(
            f"BLUEPRINT_NOT_REMOTE_SYNCED={head}|{upstream_head}"
        )
    status = run(
        root,
        "git",
        "status",
        "--short",
        "--untracked-files=all",
    )[1].splitlines()
    return {
        "branch": branch,
        "head": head,
        "upstream_head": upstream_head,
        "upstream_ref": upstream_ref,
        "head_equals_upstream": True,
        "worktree_status_observed": status,
        "canonical_package_source": "HEAD_COMMITTED_BLOBS_ONLY",
    }


def source_catalog(root: Path, head: str, request: dict):
    module_id = request["target"]["module_id"]
    required = list(BLUEPRINT_REFERENCE_PATHS) + list(PORTFOLIO_PATHS)
    module_specific = [
        f"coordination/module_policy/{module_id}/module_policy.md",
        f"coordination/human_intent/modules/{module_id}.yaml",
        f"coordination/roadmaps/{module_id}.yaml",
        f"coordination/roadmaps/details/forprint_system_blueprint/portfolio_rebuild_seeds/{module_id}.yaml",
    ]

    optional = request.get("optional_committed_blueprint_sources") or {}
    authority_source = optional.get("authority_source_path")
    if authority_source:
        module_specific.append(safe_rel_source(authority_source))
    for raw in optional.get("additional_source_paths") or []:
        module_specific.append(safe_rel_source(str(raw)))

    seen = set()
    selected = []

    for rel in required:
        if rel in seen:
            continue
        seen.add(rel)
        blob = git_blob(root, head, rel)
        selected.append(("BLUEPRINT_COMMITTED_REFERENCE", rel, blob, True))

    for rel in module_specific:
        if rel in seen:
            continue
        seen.add(rel)
        blob = git_blob_optional(root, head, rel)
        if blob is not None:
            selected.append(("BLUEPRINT_COMMITTED_REFERENCE", rel, blob, False))

    for rel in TEMPLATE_PATHS:
        blob = git_blob(root, head, rel)
        selected.append(("TEMPLATES", Path(rel).name, blob, True))

    for rel in TOOL_PATHS:
        blob = git_blob(root, head, rel)
        selected.append(("TOOLS_REFERENCE", Path(rel).name, blob, True))

    return selected


def package_manifest(request: dict, state: dict, entries: list[dict]) -> dict:
    return {
        "schema_version": "forprint_module_bootstrap_commission_package_manifest_v0_1",
        "script_id": SCRIPT_ID,
        "package_class": PACKAGE_CLASS,
        "target": request["target"],
        "source_blueprint": {
            "branch": state["branch"],
            "head": state["head"],
            "upstream_ref": state["upstream_ref"],
            "upstream_head": state["upstream_head"],
            "head_equals_upstream": True,
            "source_mode": "committed_HEAD_blobs_only",
        },
        "authority": {
            "execution": False,
            "acceptance": False,
            "release": False,
            "blueprint_write": False,
            "cross_repository_write": False,
            "production": False,
        },
        "selection": {
            "file_count": len(entries),
            "files": entries,
        },
        "freshness": {
            "before_first_canonical_module_write":
                "reconcile_live_Blueprint_and_target_Git_state",
            "package_snapshot_never_outranks_live_authority": True,
        },
    }


def make_readme(request: dict, state: dict) -> str:
    t = request["target"]
    return (
        "# ForPrint MODULE_BOOTSTRAP_COMMISSION\n\n"
        f"Target module: `{t['module_id']}`\n"
        f"Display name: `{t['module_name']}`\n"
        f"Classification: `{t['classification']}`\n"
        f"Blueprint HEAD: `{state['head']}`\n\n"
        "## Purpose\n\n"
        f"{t['purpose']}\n\n"
        "## Authority boundary\n\n"
        "This archive is commissioning/navigation evidence only.\n\n"
        "It does **not** grant execution, acceptance, release, production, "
        "Blueprint-write, cross-repository-write, commit, push or merge authority.\n\n"
        "The only allowed scope recorded by the request is `bootstrap_only`.\n\n"
        "## Required operating sequence\n\n"
        "1. Read `bootstrap_commission.yaml`.\n"
        "2. Classify/confirm the target boundary before repository creation.\n"
        "3. Inspect live filesystem/Git/remote state with short terminal commands.\n"
        "4. Reconcile this pinned package with live committed Blueprint authority.\n"
        "5. Apply `REUSE -> EXTEND -> ADAPT -> REPLACE -> NEW`.\n"
        "6. Keep repository root maximally clean.\n"
        "7. Use one canonical module manifest at `coordination/module/manifest.yaml` "
        "unless a documented unavoidable technical exception exists.\n"
        "8. Reach `FOUNDATION_REMOTE_CONTAINED`.\n"
        "9. Commission module-owned continuity.\n"
        "10. Prove `MODULE_ONBOARD` and `MODULE_CONTEXT`.\n"
        "11. Pass cold-start/no-chat-history acceptance.\n"
        "12. Enter module-specific implementation only under separate authority.\n"
    )


def root_surface_acceptance() -> dict:
    return {
        "schema_version": "forprint_bootstrap_root_surface_review_v0_1",
        "status": "OPERATOR_OR_ASSISTANT_TO_COMPLETE",
        "policy": "MAXIMALLY_CLEAN_ROOT",
        "typical_allowed_canonical_root": [
            ".gitignore",
            "README.md",
            "AGENTS.md",
            "Makefile",
            "pyproject.toml",
        ],
        "canonical_manifest_default": "coordination/module/manifest.yaml",
        "duplicate_root_manifest_for_compatibility": "FORBIDDEN",
        "entries": [],
        "allowed_decisions": [
            "KEEP_ROOT",
            "MOVE_DEEPER",
            "LOCAL_IGNORED",
            "REMOVE_GENERATED",
            "BLOCKED_NEEDS_DECISION",
        ],
        "closeout_question":
            "Is the repository root still the smallest practical operator/tooling surface?",
    }


def cold_start_acceptance() -> dict:
    return {
        "schema_version": "forprint_module_cold_start_acceptance_v0_1",
        "status": "NOT_RUN",
        "scenario":
            "Fresh assistant receives no prior chat memory and uses live module + read-only Blueprint.",
        "required": [
            "assistant-handoff-check PASS",
            "assistant-pack produces MODULE_ONBOARD",
            "assistant-context-pack produces MODULE_CONTEXT for bounded topic",
            "authority flags remain false",
            "no Blueprint/Git/runtime mutation during continuity package generation",
            "routine clarification questions = 0 when answers are discoverable",
            "unjustified canonical root entries = 0",
            "duplicate canonical manifests = 0",
        ],
        "completion_state": "SELF_ONBOARD_VERIFIED",
    }


def evidence_index(request: dict, state: dict) -> dict:
    return {
        "schema_version": "forprint_module_bootstrap_commission_evidence_index_v0_1",
        "claims": [
            {
                "id": "BOOT-EV-001",
                "claim": "Repository root is maximally clean for new ForPrint modules.",
                "source": "coordination/standards/governance/clean_repository_root_policy_v0_1.yaml",
                "source_head": state["head"],
            },
            {
                "id": "BOOT-EV-002",
                "claim":
                    "Pre-module commission archive is distinct from MODULE_ONBOARD and MODULE_CONTEXT.",
                "source":
                    "coordination/standards/governance/module_bootstrap_commission_contract_v0_1.yaml",
                "source_head": state["head"],
            },
            {
                "id": "BOOT-EV-003",
                "claim":
                    "Module continuity targets are assistant-handoff-check, assistant-pack and assistant-context-pack.",
                "source": "coordination/standards/make_command_standard.md",
                "source_head": state["head"],
            },
        ],
        "target_module_id": request["target"]["module_id"],
    }


def precedent_files() -> dict[str, str]:
    return {
        "prepress_zero_state.md": (
            "# Prepress empirical zero-state precedent\n\n"
            "Useful precedent:\n"
            "- short parent-level reconnaissance before project-local tooling exists;\n"
            "- explicit Git/remote discovery;\n"
            "- dedicated module venv;\n"
            "- strong ignore policy;\n"
            "- exact-path staging;\n"
            "- first durable pushed foundation checkpoint.\n\n"
            "Do not copy Prepress product ownership or commit hashes as global constants.\n"
            "The clean-root manifest direction is now governed by the global owner policy.\n"
        ),
        "logistics_coordination_precedent.md": (
            "# Logistics coordination precedent\n\n"
            "Use Logistics as historical precedent for:\n"
            "- module-local prompt intake/status/report organization;\n"
            "- bounded coordination workflows;\n"
            "- safe provider/runtime boundary patterns when analogous.\n\n"
            "Do not use Logistics as the normative assistant-continuity implementation.\n"
            "Current continuity authority is the System Blueprint helper/template/standards.\n"
        ),
    }


def build(root: Path, request_path: Path, output_dir: Path | None):
    request = load_request(request_path)
    state = repo_state(root)
    selected = source_catalog(root, state["head"], request)

    module_id = request["target"]["module_id"]
    base = (
        output_dir.resolve()
        if output_dir
        else (
            root
            / "tmp"
            / "module_bootstrap_commission"
            / module_id
            / state["head"][:12]
        )
    )
    package_dir = base / "package"
    archive = base / (
        f"forprint_{module_id}__module_bootstrap_commission__{state['head'][:12]}.tar.gz"
    )

    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for group, rel, blob, required in selected:
        dst = package_dir / group / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(blob)
        entries.append({
            "group": group,
            "path": rel,
            "required": required,
            "size_bytes": len(blob),
            "sha256": sha256_bytes(blob),
        })

    normalized_request = json.loads(json.dumps(request))
    normalized_request["generated_package"] = {
        "package_class": PACKAGE_CLASS,
        "source_blueprint_head": state["head"],
        "source_mode": "committed_HEAD_blobs_only",
    }

    write_yaml(package_dir / "bootstrap_commission.yaml", normalized_request)
    write_yaml(
        package_dir / "PACKAGE_MANIFEST.yaml",
        package_manifest(request, state, entries),
    )
    write_yaml(
        package_dir / "evidence_index.yaml",
        evidence_index(request, state),
    )
    write_yaml(
        package_dir / "acceptance" / "root_surface_review.yaml",
        root_surface_acceptance(),
    )
    write_yaml(
        package_dir / "acceptance" / "cold_start_acceptance.yaml",
        cold_start_acceptance(),
    )
    (package_dir / "00_READ_FIRST.md").write_text(
        make_readme(request, state),
        encoding="utf-8",
    )
    for name, content in precedent_files().items():
        p = package_dir / "PRECEDENT_SUMMARIES" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    if archive.exists():
        archive.unlink()
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(package_dir, arcname=f"{module_id}_bootstrap_commission")

    result = {
        "script_id": SCRIPT_ID,
        "package_class": PACKAGE_CLASS,
        "module_id": module_id,
        "blueprint_head": state["head"],
        "package_dir": str(package_dir.relative_to(root))
            if package_dir.is_relative_to(root)
            else str(package_dir),
        "archive": str(archive.relative_to(root))
            if archive.is_relative_to(root)
            else str(archive),
        "archive_sha256": sha256_bytes(archive.read_bytes()),
        "selected_committed_source_count": len(entries),
        "status": "PASS",
        "authority_created": False,
    }
    write_yaml(base / "result.yaml", result)
    return result


def check_only(root: Path, request_path: Path):
    request = load_request(request_path)
    state = repo_state(root)
    selected = source_catalog(root, state["head"], request)
    return {
        "module_id": request["target"]["module_id"],
        "classification": request["target"]["classification"],
        "blueprint_head": state["head"],
        "blueprint_upstream_head": state["upstream_head"],
        "selected_committed_source_count": len(selected),
        "status": "PASS",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--request", required=True)
    ap.add_argument("--output-dir")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("build")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    request_path = Path(args.request)
    if not request_path.is_absolute():
        request_path = (root / request_path).resolve()
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else None
    )

    if root.name != "forprint_system_blueprint" or not (root / ".git").exists():
        print("MODULE_BOOTSTRAP_COMMISSION=FAIL")
        print(f"ERROR=RUN_FROM_BLUEPRINT_ROOT|ROOT={root}")
        return 2

    try:
        if args.command == "check":
            result = check_only(root, request_path)
            print("MODULE_BOOTSTRAP_COMMISSION_CHECK=PASS")
            print(f"MODULE_ID={result['module_id']}")
            print(f"CLASSIFICATION={result['classification']}")
            print(f"BLUEPRINT_HEAD={result['blueprint_head']}")
            print(
                "SELECTED_COMMITTED_SOURCE_COUNT="
                + str(result["selected_committed_source_count"])
            )
            print("MUTATION_SCOPE=none")
            print("AUTHORITY_CREATED=false")
            return 0

        result = build(root, request_path, output_dir)
        print("MODULE_BOOTSTRAP_COMMISSION_BUILD=PASS")
        print(f"PACKAGE_CLASS={result['package_class']}")
        print(f"MODULE_ID={result['module_id']}")
        print(f"BLUEPRINT_HEAD={result['blueprint_head']}")
        print(f"ARCHIVE={result['archive']}")
        print(f"ARCHIVE_SHA256={result['archive_sha256']}")
        print(
            "SELECTED_COMMITTED_SOURCE_COUNT="
            + str(result["selected_committed_source_count"])
        )
        print("CANONICAL_MUTATION_PERFORMED=false")
        print("AUTHORITY_CREATED=false")
        return 0
    except CommissionError as exc:
        print("MODULE_BOOTSTRAP_COMMISSION=FAIL")
        print(f"ERROR={exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
