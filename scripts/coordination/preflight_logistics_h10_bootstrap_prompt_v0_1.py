#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

PROMPT_ID = "logistics_service_authority_lineage_and_module_bootstrap_v0_1"
APPROVED_PROMPT = Path(
    "coordination/outgoing_prompts/logistics_service/approved/"
    "2026-09-05__logistics_service_authority_lineage_and_module_bootstrap_v0_1.md"
)
QUEUE = Path("coordination/outgoing_prompts/logistics_service/index.yaml")
RELEASE = Path("coordination/releases/current.yaml")
RELEASE_POLICY = Path(
    "coordination/standards/governance/outgoing_prompt_release_policy_v0_1.yaml"
)
CONTRACT = Path(
    "coordination/prompt_contracts/logistics_service/"
    "logistics_service_authority_lineage_and_module_bootstrap_v0_1/"
    "logistics_service_authority_lineage_and_module_bootstrap_v0_1__contract_v0_4_h10_inventory_v0_1.yaml"
)
ORACLE = Path(
    "coordination/acceptance_oracles/logistics_service/"
    "logistics_service_authority_lineage_and_module_bootstrap_v0_1__acceptance_oracle_v0_1.yaml"
)


class PreflightError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PreflightError(f"required file missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PreflightError(f"YAML root must be a mapping: {path}")
    return data


def git(repo: Path, *args: str, allow_failure: bool = False) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0 and not allow_failure:
        raise PreflightError(
            f"git {' '.join(args)} failed in {repo}: {result.stdout.strip()}"
        )
    return result.returncode, result.stdout.strip()


def front_matter(text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        raise PreflightError("approved prompt has no YAML front matter")
    _, rest = text.split("---\n", 1)
    header_text, _, _ = rest.partition("\n---\n")
    data = yaml.safe_load(header_text)
    if not isinstance(data, dict):
        raise PreflightError("approved prompt front matter is invalid")
    return data


def machine_prompt(text: str) -> dict[str, Any]:
    marker = "# ForPrint machine prompt"
    if marker not in text:
        raise PreflightError("machine prompt marker missing")
    after = text.split(marker, 1)[1]
    if "```yaml" not in after:
        raise PreflightError("machine prompt YAML fence missing")
    payload = after.split("```yaml", 1)[1].split("```", 1)[0]
    data = yaml.safe_load(payload)
    if not isinstance(data, dict):
        raise PreflightError("machine prompt YAML is invalid")
    return data


def check(checks: list[dict[str, Any]], check_id: str, ok: bool, detail: Any) -> None:
    checks.append(
        {
            "check_id": check_id,
            "state": "PASS" if ok else "HOLD",
            "detail": detail,
        }
    )


def find_queue_row(queue: dict[str, Any]) -> dict[str, Any]:
    rows = queue.get("prompt_queue")
    if not isinstance(rows, list):
        raise PreflightError("prompt_queue must be a list")
    matches = [
        row for row in rows
        if isinstance(row, dict) and row.get("prompt_id") == PROMPT_ID
    ]
    if len(matches) != 1:
        raise PreflightError(
            f"expected exactly one queue row for {PROMPT_ID}, found {len(matches)}"
        )
    return matches[0]


def module_repo_checks(
    checks: list[dict[str, Any]],
    module_repo: Path,
    baseline: dict[str, Any],
) -> dict[str, Any]:
    observed: dict[str, Any] = {"path": str(module_repo)}
    if not module_repo.is_dir():
        check(checks, "module_repo_available", False, str(module_repo))
        observed["available"] = False
        return observed

    observed["available"] = True
    check(checks, "module_repo_available", True, str(module_repo))

    _, branch = git(module_repo, "branch", "--show-current")
    _, head = git(module_repo, "rev-parse", "HEAD")
    _, status = git(module_repo, "status", "--porcelain=v1", "--untracked-files=all")
    expected_branch = baseline.get("module_branch")
    baseline_commit = baseline.get("module_commit")

    observed.update(
        {
            "branch": branch,
            "head": head,
            "working_tree_clean": status == "",
            "baseline_commit": baseline_commit,
            "expected_branch": expected_branch,
        }
    )
    check(checks, "module_branch", branch == expected_branch, {
        "expected": expected_branch,
        "observed": branch,
    })
    check(checks, "module_worktree_clean", status == "", {
        "dirty_entry_count": len(status.splitlines()) if status else 0,
    })

    ancestor_rc, _ = git(
        module_repo,
        "merge-base",
        "--is-ancestor",
        str(baseline_commit),
        "HEAD",
        allow_failure=True,
    )
    check(checks, "module_baseline_is_ancestor", ancestor_rc == 0, {
        "baseline": baseline_commit,
        "head": head,
    })

    upstream_rc, upstream = git(
        module_repo,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{u}",
        allow_failure=True,
    )
    if upstream_rc != 0:
        observed["upstream"] = None
        check(checks, "module_upstream_configured", False, upstream or "no upstream")
        return observed

    observed["upstream"] = upstream
    check(checks, "module_upstream_configured", True, upstream)
    counts_rc, counts = git(
        module_repo,
        "rev-list",
        "--left-right",
        "--count",
        "HEAD...@{u}",
        allow_failure=True,
    )
    if counts_rc != 0:
        check(checks, "module_upstream_synced", False, counts)
        return observed

    parts = counts.split()
    ahead = int(parts[0]) if len(parts) >= 1 else -1
    behind = int(parts[1]) if len(parts) >= 2 else -1
    observed["ahead"] = ahead
    observed["behind"] = behind
    check(checks, "module_upstream_synced", ahead == 0 and behind == 0, {
        "ahead": ahead,
        "behind": behind,
        "upstream": upstream,
    })
    return observed


def build_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    checks: list[dict[str, Any]] = []
    advisories: list[dict[str, Any]] = []

    release_doc = load_yaml(root / RELEASE)
    current_release = release_doc.get("release")
    progression = release_doc.get("progression_gate_policy")
    if not isinstance(current_release, dict) or not isinstance(progression, dict):
        raise PreflightError("current release authority is incomplete")
    check(
        checks,
        "release_h10_v0_4_1",
        current_release.get("hardening_release") == "v0.4.1"
        and current_release.get("hardening_state") == "ACTIVE_CURRENT"
        and progression.get("current_phase") == "H10",
        {
            "hardening_release": current_release.get("hardening_release"),
            "hardening_state": current_release.get("hardening_state"),
            "current_phase": progression.get("current_phase"),
        },
    )

    policy = load_yaml(root / RELEASE_POLICY).get("release")
    if not isinstance(policy, dict):
        raise PreflightError("release policy release section is invalid")
    fail_closed = (
        policy.get("global_enabled") is False
        and policy.get("authorized_modules") == []
        and policy.get("authorization_evidence") is None
    )
    check(checks, "release_policy_fail_closed", fail_closed, {
        "global_enabled": policy.get("global_enabled"),
        "authorized_modules": policy.get("authorized_modules"),
        "authorization_evidence": policy.get("authorization_evidence"),
    })

    queue_row = find_queue_row(load_yaml(root / QUEUE))
    execution = queue_row.get("module_execution")
    queue_status = execution.get("status") if isinstance(execution, dict) else None
    check(checks, "queue_ready_for_module_pull", queue_status == "ready_for_module_pull", {
        "sequence": queue_row.get("sequence"),
        "status": queue_status,
    })

    approved_text = (root / APPROVED_PROMPT).read_text(encoding="utf-8")
    approved_header = front_matter(approved_text)
    approved_machine_prompt = machine_prompt(approved_text)
    check(
        checks,
        "approved_prompt_released",
        approved_header.get("prompt_id") == PROMPT_ID
        and approved_header.get("lifecycle_state") == "released",
        {
            "prompt_id": approved_header.get("prompt_id"),
            "lifecycle_state": approved_header.get("lifecycle_state"),
        },
    )

    contract = load_yaml(root / CONTRACT)
    source_prompt = contract.get("source_prompt")
    baseline_policy = contract.get("execution_baseline_policy")
    if not isinstance(source_prompt, dict) or not isinstance(baseline_policy, dict):
        raise PreflightError("prompt contract baseline/source sections are invalid")

    snapshot_path = root / str(source_prompt.get("path"))
    snapshot_hash = sha256_file(snapshot_path) if snapshot_path.is_file() else None
    check(
        checks,
        "contract_source_prompt_snapshot_hash",
        snapshot_hash == source_prompt.get("sha256"),
        {
            "path": source_prompt.get("path"),
            "expected_sha256": source_prompt.get("sha256"),
            "observed_sha256": snapshot_hash,
        },
    )

    if snapshot_path.is_file():
        source_machine_prompt = machine_prompt(snapshot_path.read_text(encoding="utf-8"))
        check(
            checks,
            "released_machine_prompt_semantics_match_contract_source",
            approved_machine_prompt == source_machine_prompt,
            "canonical parsed machine_prompt mapping comparison",
        )

    required_inputs = baseline_policy.get("required_inputs")
    if not isinstance(required_inputs, list):
        raise PreflightError("contract required_inputs must be a list")
    pinned_results = []
    for item in required_inputs:
        if not isinstance(item, dict):
            continue
        input_path = root / str(item.get("path"))
        observed_hash = sha256_file(input_path) if input_path.is_file() else None
        expected_hash = item.get("sha256")
        ok = observed_hash == expected_hash
        check(
            checks,
            f"pinned_input_{item.get('input_id')}",
            ok,
            {
                "path": item.get("path"),
                "material": item.get("material"),
                "expected_sha256": expected_hash,
                "observed_sha256": observed_hash,
            },
        )
        pinned_results.append({
            "input_id": item.get("input_id"),
            "path": item.get("path"),
            "material": item.get("material"),
            "expected_sha256": expected_hash,
            "observed_sha256": observed_hash,
            "state": "PASS" if ok else "HOLD",
        })

    oracle = load_yaml(root / ORACLE)
    oracle_contract = oracle.get("source_prompt_contract")
    actual_contract_hash = sha256_file(root / CONTRACT)
    if not isinstance(oracle_contract, dict):
        raise PreflightError("oracle source_prompt_contract must be a mapping")
    check(
        checks,
        "oracle_contract_hash_chain",
        oracle_contract.get("path") == CONTRACT.as_posix()
        and oracle_contract.get("sha256") == actual_contract_hash,
        {
            "oracle_path": oracle_contract.get("path"),
            "oracle_expected_sha256": oracle_contract.get("sha256"),
            "observed_contract_sha256": actual_contract_hash,
        },
    )

    prompt_acceptance = approved_machine_prompt.get("acceptance_handoff")
    check(
        checks,
        "approved_prompt_acceptance_paths",
        isinstance(prompt_acceptance, dict)
        and prompt_acceptance.get("prompt_contract_path") == CONTRACT.as_posix()
        and prompt_acceptance.get("acceptance_oracle_path") == ORACLE.as_posix(),
        prompt_acceptance,
    )

    release_baseline = baseline_policy.get("release_baseline")
    if not isinstance(release_baseline, dict):
        raise PreflightError("contract release_baseline must be a mapping")

    blueprint_baseline = release_baseline.get("blueprint_commit")
    _, blueprint_head = git(root, "rev-parse", "HEAD")
    ancestor_rc, _ = git(
        root,
        "merge-base",
        "--is-ancestor",
        str(blueprint_baseline),
        "HEAD",
        allow_failure=True,
    )
    check(checks, "blueprint_baseline_is_ancestor", ancestor_rc == 0, {
        "baseline": blueprint_baseline,
        "head": blueprint_head,
    })

    blueprint_status_rc, blueprint_status = git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        allow_failure=True,
    )
    advisories.append({
        "advisory_id": "blueprint_worktree_observation",
        "state": "OBSERVED",
        "detail": {
            "status_command_rc": blueprint_status_rc,
            "dirty_entry_count": len(blueprint_status.splitlines()) if blueprint_status else 0,
            "blocking": False,
            "reason": "contract requires clean module worktree, not clean Blueprint worktree; material Blueprint inputs are hash-pinned separately",
        },
    })

    inventory_path = next(
        (
            root / str(item.get("path"))
            for item in required_inputs
            if isinstance(item, dict)
            and item.get("input_id") == "logistics_inventory_completion_evidence_v0_1"
        ),
        None,
    )
    if inventory_path is None:
        raise PreflightError("Logistics inventory completion evidence is not pinned")
    inventory = load_yaml(inventory_path)
    repository = inventory.get("repository")
    if not isinstance(repository, dict) or not isinstance(repository.get("path"), str):
        raise PreflightError("Logistics inventory evidence has no repository.path")

    module_observation = module_repo_checks(
        checks,
        Path(repository["path"]),
        release_baseline,
    )

    promotion = contract.get("promotion")
    semantic_fidelity = contract.get("semantic_fidelity")
    advisories.append({
        "advisory_id": "prompt_contract_review_state",
        "state": "MANUAL_REVIEW_REQUIRED_BEFORE_BLUEPRINT_ACCEPTANCE"
        if isinstance(promotion, dict)
        and promotion.get("normal_acceptance_allowed") is False
        else "OBSERVED",
        "detail": {
            "promotion_state": promotion.get("state") if isinstance(promotion, dict) else None,
            "normal_acceptance_allowed": promotion.get("normal_acceptance_allowed") if isinstance(promotion, dict) else None,
            "semantic_review_state": semantic_fidelity.get("review_state") if isinstance(semantic_fidelity, dict) else None,
            "blocks_module_start": False,
            "blocks_automatic_blueprint_acceptance": True,
        },
    })

    blockers = [item for item in checks if item["state"] == "HOLD"]
    result = (
        "READY_FOR_MANUAL_MODULE_START"
        if not blockers
        else "HOLD_BEFORE_MODULE_START"
    )

    return {
        "schema_version": "logistics_h10_bootstrap_preflight_report_v0_1",
        "metadata": {
            "prompt_id": PROMPT_ID,
            "result": result,
            "read_only": True,
            "module_start_performed": False,
            "prompt_pull_performed": False,
            "release_transition_performed": False,
            "commit_push_performed": False,
            "control_mode": "L0_FULL_MANUAL_PROMPT_GATE",
        },
        "blocking_checks": checks,
        "blocker_ids": [item["check_id"] for item in blockers],
        "pinned_inputs": pinned_results,
        "module_repository_observation": module_observation,
        "advisories": advisories,
        "next_action": (
            "operator may separately authorize the first manual module-start"
            if result == "READY_FOR_MANUAL_MODULE_START"
            else "resolve blocker_ids and rerun this preflight before module-start"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    parser.add_argument("--output")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    try:
        report = build_report(root)
    except Exception as error:
        print(f"PREFLIGHT_ERROR={type(error).__name__}:{error}")
        return 1

    if args.format == "json":
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    else:
        rendered = yaml.safe_dump(
            report,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        )

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 0 if report["metadata"]["result"] == "READY_FOR_MANUAL_MODULE_START" else 2


if __name__ == "__main__":
    raise SystemExit(main())
