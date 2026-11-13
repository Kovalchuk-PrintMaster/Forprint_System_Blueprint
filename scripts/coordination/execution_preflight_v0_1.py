from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from prompt_execution_events_v0_1 import (  # noqa: E402
    ACTIVE_QUEUE_STATUSES,
    REGISTRY_REL,
    PromptExecutionEventError,
    _queue_prompt,
    _registry_is_read_only,
    _registry_module,
    _repository_root,
)
from validate_prompt_contract_v0_4 import (  # noqa: E402
    B1_POLICY_SCHEMA,
    load_yaml,
    validate_contract,
)

REPORT_SCHEMA = "blueprint_execution_preflight_v0_1"

READY = {
    "READY_EXACT",
    "READY_FORWARD_COMPATIBLE",
    "READY_CURRENT_REVALIDATED",
}
BLUEPRINT_BLOCKERS = {
    "BLOCKED_BLUEPRINT_MATERIAL_DRIFT",
    "BLOCKED_REQUIRED_INPUT_MISSING",
    "BLOCKED_BREAKING_RELEASE_CHANGE",
    "BLOCKED_PROMPT_SUPERSEDED",
}


class PreflightError(RuntimeError):
    pass


def resolve_coordination_binding(
    *,
    blueprint_root: Path,
    module_root: Path,
    module_id: str,
    prompt_id: str,
) -> dict[str, Any]:
    """Bind contract identity to existing registry and Prompt Queue authority."""

    registry_path = (blueprint_root / REGISTRY_REL).resolve()
    registry = load_yaml(registry_path)

    try:
        module = _registry_module(registry, module_id)
        if not _registry_is_read_only(module):
            raise PreflightError(
                "registered module does not preserve read-only Blueprint boundaries"
            )

        registered_root = _repository_root(module)
        if registered_root != module_root.resolve():
            raise PreflightError(
                "module_root does not match registered repository.local_path "
                f"for module_id={module_id!r}"
            )

        _, prompt, queue_path = _queue_prompt(
            blueprint_root,
            module,
            prompt_id,
        )
    except PromptExecutionEventError as exc:
        raise PreflightError(str(exc)) from exc

    module_execution = prompt.get("module_execution")
    if not isinstance(module_execution, dict):
        raise PreflightError("queue prompt module_execution must be a mapping")

    return {
        "registry_path": registry_path,
        "registered_module_root": registered_root,
        "queue_path": queue_path,
        "queue_status": module_execution.get("status"),
    }


def prompt_superseded_from_queue_status(queue_status: Any) -> bool:
    """Fail closed for terminal or unknown non-executable queue states."""

    if queue_status == "superseded":
        return True
    if queue_status not in ACTIVE_QUEUE_STATUSES:
        raise PreflightError(
            f"prompt queue status is not execution-eligible: {queue_status!r}"
        )
    return False


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run_git(root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and proc.returncode:
        raise PreflightError(
            f"git {' '.join(args)} failed in {root}: {proc.stdout.strip()}"
        )
    return proc.stdout.strip()


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode == 0


def safe_path(root: Path, raw: str) -> Path:
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts:
        raise PreflightError(f"unsafe repository-relative path: {raw}")
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise PreflightError(f"path escapes repository root: {raw}") from exc
    return target


def repository_state(root: Path) -> dict[str, Any]:
    head = run_git(root, "rev-parse", "HEAD")
    branch = run_git(root, "branch", "--show-current")
    dirty = bool(run_git(root, "status", "--porcelain=v1", "-uall"))

    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "@{upstream}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    upstream = proc.stdout.strip() if proc.returncode == 0 else None

    divergence: list[int] | None = None
    if upstream:
        counts = run_git(
            root,
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...@{upstream}",
        ).split()
        if len(counts) == 2:
            divergence = [int(counts[0]), int(counts[1])]

    return {
        "head": head,
        "branch": branch,
        "dirty": dirty,
        "upstream": upstream,
        "divergence": divergence,
    }


def classify_module(
    *,
    current: dict[str, Any],
    baseline_commit: str,
    baseline_branch: str,
    forward_allowed: bool,
    clean_required: bool,
    synced_required: bool,
    ancestor_ok: bool,
) -> str:
    if clean_required and current["dirty"]:
        return "BLOCKED_MODULE_DIRTY"
    if current["branch"] != baseline_branch:
        return "BLOCKED_MODULE_BRANCH_MISMATCH"
    if synced_required and (
        current["upstream"] is None or current["divergence"] != [0, 0]
    ):
        return "BLOCKED_MODULE_DIVERGED"
    if current["head"] == baseline_commit:
        return "MODULE_EXACT"
    if forward_allowed and ancestor_ok:
        return "MODULE_FORWARD_COMPATIBLE"
    return "BLOCKED_MODULE_DIVERGED"


def classify_blueprint(
    *,
    current_head: str,
    baseline_commit: str,
    forward_allowed: bool,
    ancestor_ok: bool,
    release_compatible: bool,
    missing_required_input: bool,
    material_drift: bool,
    prompt_superseded: bool = False,
) -> str:
    if prompt_superseded:
        return "BLOCKED_PROMPT_SUPERSEDED"
    if missing_required_input:
        return "BLOCKED_REQUIRED_INPUT_MISSING"
    if not release_compatible:
        return "BLOCKED_BREAKING_RELEASE_CHANGE"
    if material_drift:
        return "BLOCKED_BLUEPRINT_MATERIAL_DRIFT"
    if current_head == baseline_commit:
        return "READY_EXACT"
    if forward_allowed and ancestor_ok:
        return "READY_FORWARD_COMPATIBLE"
    return "BLOCKED_BREAKING_RELEASE_CHANGE"


def combine_status(
    *,
    blueprint_status: str,
    module_status: str,
    previous_fingerprint: str | None,
    current_fingerprint: str,
) -> str:
    if blueprint_status in BLUEPRINT_BLOCKERS:
        return blueprint_status
    if module_status.startswith("BLOCKED_"):
        return module_status
    if (
        previous_fingerprint
        and previous_fingerprint != current_fingerprint
        and blueprint_status in READY
    ):
        return "READY_CURRENT_REVALIDATED"
    if (
        blueprint_status == "READY_EXACT"
        and module_status == "MODULE_EXACT"
    ):
        return "READY_EXACT"
    return "READY_FORWARD_COMPATIBLE"



def _valid_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def release_authority_material_drift(
    *,
    authority_exists: bool,
    expected_sha256: str,
    current_sha256: str | None,
) -> bool:
    return bool(
        authority_exists
        and current_sha256 != expected_sha256
    )


def validate_previous_preflight_report(
    previous: dict[str, Any],
    *,
    contract_id: str,
    module_id: str,
    prompt_id: str,
    contract_path: Path,
    release_baseline: dict[str, Any],
) -> str:
    # Fail closed unless a previous report belongs to the same B1 identity.
    if previous.get("schema_version") != REPORT_SCHEMA:
        raise PreflightError("previous preflight report schema mismatch")

    previous_contract = previous.get("contract")
    if not isinstance(previous_contract, dict):
        raise PreflightError("previous preflight report contract must be a mapping")

    expected_identity = {
        "contract_id": contract_id,
        "module_id": module_id,
        "prompt_id": prompt_id,
        "path": str(contract_path),
    }
    for key, expected in expected_identity.items():
        if previous_contract.get(key) != expected:
            raise PreflightError(
                f"previous preflight report contract {key} mismatch"
            )

    if previous.get("release_baseline") != release_baseline:
        raise PreflightError("previous preflight report release_baseline mismatch")

    fingerprint = previous.get("preflight_fingerprint_sha256")
    if not _valid_sha256(fingerprint):
        raise PreflightError(
            "previous preflight report fingerprint must be a lowercase sha256"
        )

    execution_identity = previous.get("execution_identity")
    if not isinstance(execution_identity, dict):
        raise PreflightError(
            "previous preflight report execution_identity must be a mapping"
        )
    if execution_identity.get("execution_epoch_id") != fingerprint:
        raise PreflightError(
            "previous preflight report execution_epoch_id/fingerprint mismatch"
        )

    revalidation = previous.get("revalidation")
    if not isinstance(revalidation, dict):
        raise PreflightError(
            "previous preflight report revalidation must be a mapping"
        )
    if revalidation.get("current_preflight_fingerprint_sha256") != fingerprint:
        raise PreflightError(
            "previous preflight report revalidation fingerprint mismatch"
        )

    return fingerprint


def evaluate(
    *,
    blueprint_root: Path,
    module_root: Path,
    contract_path: Path,
    previous_report: Path | None = None,
) -> dict[str, Any]:
    blueprint_root = blueprint_root.resolve()
    module_root = module_root.resolve()
    contract_path = contract_path.resolve()

    contract_report = validate_contract(blueprint_root, contract_path)
    if contract_report["result"] != "PASSED":
        raise PreflightError(
            "prompt contract validation failed: "
            + "; ".join(contract_report["errors"])
        )

    contract = load_yaml(contract_path)
    policy = contract.get("execution_baseline_policy")
    if not isinstance(policy, dict):
        raise PreflightError(
            "prompt contract has no execution_baseline_policy; "
            "historical v0.4 contracts remain valid but are not B1-executable"
        )
    if policy.get("schema_version") != B1_POLICY_SCHEMA:
        raise PreflightError("unsupported execution_baseline_policy schema")

    metadata = contract["metadata"]
    release = policy["release_baseline"]
    compatibility = policy["compatibility"]

    binding = resolve_coordination_binding(
        blueprint_root=blueprint_root,
        module_root=module_root,
        module_id=metadata["module_id"],
        prompt_id=metadata["prompt_id"],
    )
    prompt_superseded = prompt_superseded_from_queue_status(
        binding["queue_status"]
    )

    blueprint_state = repository_state(blueprint_root)
    module_state = repository_state(module_root)

    authority = release["release_authority"]
    authority_path = safe_path(blueprint_root, authority["path"])
    authority_exists = authority_path.is_file()
    current_authority_sha = sha256_file(authority_path) if authority_exists else None
    authority_material_drift = release_authority_material_drift(
        authority_exists=authority_exists,
        expected_sha256=authority["sha256"],
        current_sha256=current_authority_sha,
    )
    authority_matches_release_baseline = (
        authority_exists and not authority_material_drift
    )
    current_authority = load_yaml(authority_path) if authority_exists else {}
    current_hardening_release = (
        current_authority.get("release", {}).get("hardening_release")
        if isinstance(current_authority, dict)
        else None
    )
    release_compatible = (
        current_hardening_release == authority["hardening_release"]
    )

    missing_required = False
    material_drift = False
    input_observations: list[dict[str, Any]] = []

    for item in policy["required_inputs"]:
        repo_root = (
            blueprint_root
            if item["repository"] == "blueprint"
            else module_root
        )
        path = safe_path(repo_root, item["path"])
        exists = path.is_file()
        current_sha = sha256_file(path) if exists else None
        matches = exists and current_sha == item["sha256"]

        if not exists:
            missing_required = True
        elif item["material"] is True and not matches:
            material_drift = True

        input_observations.append(
            {
                "input_id": item["input_id"],
                "repository": item["repository"],
                "path": item["path"],
                "expected_sha256": item["sha256"],
                "current_sha256": current_sha,
                "exists": exists,
                "matches_release_baseline": matches,
                "material": True,
            }
        )

    blueprint_ancestor = is_ancestor(
        blueprint_root,
        release["blueprint_commit"],
        blueprint_state["head"],
    )
    module_ancestor = is_ancestor(
        module_root,
        release["module_commit"],
        module_state["head"],
    )

    module_status = classify_module(
        current=module_state,
        baseline_commit=release["module_commit"],
        baseline_branch=release["module_branch"],
        forward_allowed=compatibility["allow_module_forward_descendant"],
        clean_required=compatibility["require_clean_module_worktree"],
        synced_required=compatibility["require_module_upstream_synced"],
        ancestor_ok=module_ancestor,
    )

    blueprint_status = classify_blueprint(
        current_head=blueprint_state["head"],
        baseline_commit=release["blueprint_commit"],
        forward_allowed=compatibility["allow_blueprint_forward_descendant"],
        ancestor_ok=blueprint_ancestor,
        release_compatible=release_compatible,
        missing_required_input=missing_required or not authority_exists,
        material_drift=material_drift or authority_material_drift,
        prompt_superseded=prompt_superseded,
    )

    fingerprint_payload = {
        "contract_id": metadata["contract_id"],
        "module_id": metadata["module_id"],
        "prompt_id": metadata["prompt_id"],
        "release_baseline": release,
        "blueprint_state": blueprint_state,
        "module_state": module_state,
        "release_authority": {
            "expected_sha256": authority["sha256"],
            "current_sha256": current_authority_sha,
            "matches_release_baseline": authority_matches_release_baseline,
            "hardening_release": current_hardening_release,
        },
        "required_inputs": input_observations,
        "coordination_binding": {
            "registry_path": str(binding["registry_path"]),
            "registered_module_root": str(binding["registered_module_root"]),
            "queue_path": str(binding["queue_path"]),
            "queue_status": binding["queue_status"],
        },
    }
    fingerprint = canonical_sha256(fingerprint_payload)

    previous_fingerprint = None
    if previous_report is not None:
        previous = load_yaml(previous_report.resolve())
        previous_fingerprint = validate_previous_preflight_report(
            previous,
            contract_id=metadata["contract_id"],
            module_id=metadata["module_id"],
            prompt_id=metadata["prompt_id"],
            contract_path=contract_path,
            release_baseline=release,
        )

    status = combine_status(
        blueprint_status=blueprint_status,
        module_status=module_status,
        previous_fingerprint=previous_fingerprint,
        current_fingerprint=fingerprint,
    )

    return {
        "schema_version": REPORT_SCHEMA,
        "result": "READY" if status in READY else "BLOCKED",
        "status": status,
        "contract": {
            "contract_id": metadata["contract_id"],
            "module_id": metadata["module_id"],
            "prompt_id": metadata["prompt_id"],
            "path": str(contract_path),
        },
        "release_baseline": release,
        "execution_baseline": {
            "blueprint": blueprint_state,
            "module": module_state,
            "release_authority_expected_sha256": authority["sha256"],
            "release_authority_current_sha256": current_authority_sha,
            "release_authority_matches_release_baseline": (
                authority_matches_release_baseline
            ),
            "current_hardening_release": current_hardening_release,
            "required_inputs": input_observations,
            "coordination_binding": {
                "registry_path": str(binding["registry_path"]),
                "registered_module_root": str(binding["registered_module_root"]),
                "queue_path": str(binding["queue_path"]),
                "queue_status": binding["queue_status"],
            },
        },
        "blueprint_status": blueprint_status,
        "module_status": module_status,
        "revalidation": {
            "previous_preflight_fingerprint_sha256": previous_fingerprint,
            "current_preflight_fingerprint_sha256": fingerprint,
            "revalidation_performed": previous_report is not None,
        },
        "execution_identity": {
            "execution_epoch_id": fingerprint,
            "claim_must_bind_preflight_fingerprint": True,
            "head_chasing_after_claim_allowed": False,
        },
        "preflight_fingerprint_sha256": fingerprint,
        "boundaries": {
            "blueprint_repository_writes": False,
            "module_repository_writes": False,
            "operator_decision_created": False,
            "automatic_acceptance": False,
            "automatic_return": False,
            "automatic_hold": False,
            "automatic_commit": False,
            "automatic_push": False,
        },
    }


def render_text(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "ForPrint B1 execution preflight v0.1",
            f"result: {report['result']}",
            f"status: {report['status']}",
            f"blueprint_status: {report['blueprint_status']}",
            f"module_status: {report['module_status']}",
            "execution_epoch_id: "
            + report["execution_identity"]["execution_epoch_id"],
            "preflight_fingerprint_sha256: "
            + report["preflight_fingerprint_sha256"],
            "module_repository_writes: false",
            "blueprint_repository_writes: false",
            "automatic_acceptance: false",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--module-root", required=True)
    parser.add_argument("--previous-report")
    parser.add_argument(
        "--output-format",
        choices=("text", "yaml"),
        default="text",
    )
    args = parser.parse_args()

    try:
        report = evaluate(
            blueprint_root=Path(args.root),
            module_root=Path(args.module_root),
            contract_path=Path(args.contract),
            previous_report=(
                Path(args.previous_report)
                if args.previous_report
                else None
            ),
        )
    except (PreflightError, OSError, ValueError, yaml.YAMLError) as exc:
        print(f"FAILED: {exc}")
        return 2

    if args.output_format == "yaml":
        print(
            yaml.safe_dump(
                report,
                sort_keys=False,
                allow_unicode=True,
            ).rstrip()
        )
    else:
        print(render_text(report))

    return 0 if report["result"] == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
