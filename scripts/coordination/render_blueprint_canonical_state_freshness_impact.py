#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

SCHEMA_VERSION = "blueprint_canonical_state_freshness_impact_report_v0_1"

CURRENT_RELEASE = Path("coordination/releases/current.yaml")
RELEASE_POLICY = Path("coordination/standards/governance/outgoing_prompt_release_policy_v0_1.yaml")
LOGISTICS_QUEUE = Path("coordination/outgoing_prompts/logistics_service/index.yaml")
HUMAN_INTENT_INDEX = Path("coordination/human_intent/index.yaml")
AGENTS = Path("AGENTS.md")
SNAPSHOT_GATE = Path("coordination/repository_knowledge/snapshot_comparison_gate_v0_1.yaml")
GOVERNANCE_RENDERER = Path("scripts/coordination/render_blueprint_governance_status.py")
FRESHNESS_ASSESSOR = Path("scripts/coordination/assess_repository_knowledge_freshness.py")
CONTEXT_BUILDER = Path("scripts/coordination/build_context_bundle.py")
DEFAULT_CONTRACTS = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-09-06__blueprint__current_state_freshness_surface_contracts_v0_1.yaml"
)

CURRENT_STATE_START = "<!-- FORPRINT_MODULE_INVENTORY_PROGRAM_U111_BEGIN -->"
CURRENT_STATE_END = "<!-- FORPRINT_MODULE_INVENTORY_PROGRAM_U111_END -->"


class ResolverError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ResolverError(f"required YAML missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ResolverError(f"YAML root must be a mapping: {path}")
    return data


def load_module(path: Path, name: str) -> ModuleType:
    if not path.is_file():
        raise ResolverError(f"required Python primitive missing: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ResolverError(f"could not load Python primitive: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise ResolverError("git " + " ".join(args) + " failed: " + result.stdout.strip())
    return result.stdout.strip()


def changed_paths(root: Path) -> list[str]:
    output = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    paths: set[str] = set()
    for line in output.splitlines():
        if len(line) < 4:
            continue
        raw = line[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        if raw:
            paths.add(raw)
    return sorted(paths)


def find_prompt_record(queue: dict[str, Any], prompt_id: str) -> dict[str, Any]:
    rows = queue.get("prompt_queue")
    if not isinstance(rows, list):
        raise ResolverError("logistics prompt queue must contain prompt_queue list")
    matches = [row for row in rows if isinstance(row, dict) and row.get("prompt_id") == prompt_id]
    if len(matches) != 1:
        raise ResolverError(f"expected exactly one queue row for {prompt_id}, found {len(matches)}")
    return matches[0]


def queue_execution_status(record: dict[str, Any]) -> str | None:
    execution = record.get("module_execution")
    if isinstance(execution, dict):
        value = execution.get("status")
        return value if isinstance(value, str) else None
    value = record.get("execution_status")
    return value if isinstance(value, str) else None


def human_intent_total(index: dict[str, Any]) -> int:
    modules = index.get("modules")
    if not isinstance(modules, list):
        raise ResolverError("Human Intent index modules must be a list")
    total = 0
    for item in modules:
        if not isinstance(item, dict):
            continue
        value = item.get("intent_count")
        if not isinstance(value, int):
            raise ResolverError("Human Intent module intent_count must be integer")
        total += value
    return total


def release_policy_state(policy: dict[str, Any]) -> dict[str, Any]:
    release = policy.get("release")
    if not isinstance(release, dict):
        raise ResolverError("release policy release section must be a mapping")
    authorized = release.get("authorized_modules")
    fail_closed = (
        release.get("global_enabled") is False
        and authorized == []
        and release.get("authorization_evidence") is None
    )
    return {
        "global_enabled": release.get("global_enabled"),
        "authorized_modules": authorized,
        "authorization_evidence": release.get("authorization_evidence"),
        "fail_closed_without_evidence": release.get("fail_closed_without_evidence"),
        "state": "FAIL_CLOSED" if fail_closed else "NOT_FAIL_CLOSED",
    }


def extract_agents_current_state(text: str) -> str:
    if CURRENT_STATE_START not in text or CURRENT_STATE_END not in text:
        return ""
    return text.split(CURRENT_STATE_START, 1)[1].split(CURRENT_STATE_END, 1)[0]


def expected_agents_fragments(state: dict[str, Any]) -> list[str]:
    return [
        (f"release: `{state['hardening_release']}`, hardening state `{state['hardening_state']}`"),
        (
            f"external reference pilot: `{state['pilot_module']}`; "
            "the bounded Blueprint internal zero-stage pilot comes first"
        ),
        f"Logistics bootstrap prompt: `{state['logistics_prompt_id']}`",
        f"queue state: `{state['logistics_queue_status']}`",
        (f"Human Intent portfolio: `{state['human_intent_total']}` captured intents"),
    ]


def evaluate_agents_current_state_text(
    text: str,
    canonical_state: dict[str, Any],
) -> dict[str, Any]:
    block = extract_agents_current_state(text)
    if not block:
        return {
            "state": "STALE",
            "refresh_required": True,
            "reason": "current-state projection markers are missing",
            "missing_expected_fragments": expected_agents_fragments(canonical_state),
        }

    missing = [
        fragment for fragment in expected_agents_fragments(canonical_state) if fragment not in block
    ]
    if canonical_state["release_policy_state"] == "FAIL_CLOSED":
        if "release policy: fail-closed" not in block:
            missing.append("release policy: fail-closed")
    if canonical_state["automatic_accept"] is False:
        if "automatic Blueprint ACCEPT: disabled" not in block:
            missing.append("automatic Blueprint ACCEPT: disabled")
    if canonical_state["automatic_release_next_prompt"] is False:
        if "automatic next-prompt release: disabled" not in block:
            missing.append("automatic next-prompt release: disabled")

    return {
        "state": "FRESH" if not missing else "STALE",
        "refresh_required": bool(missing),
        "reason": (
            "projection agrees with current authority"
            if not missing
            else "projection does not contain all current authority claims"
        ),
        "missing_expected_fragments": missing,
    }


def path_matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-3])
    if pattern.endswith("/*"):
        prefix = pattern[:-1]
        remainder = path[len(prefix) :].strip("/")
        return path.startswith(prefix) and "/" not in remainder
    return path == pattern


def impacted_surfaces(
    contracts: dict[str, Any],
    changed: list[str],
    *,
    agents_evaluation: dict[str, Any],
) -> list[dict[str, Any]]:
    surfaces = contracts.get("surfaces")
    if not isinstance(surfaces, list):
        raise ResolverError("freshness contract surfaces must be a list")

    rows: list[dict[str, Any]] = []
    for surface in surfaces:
        if not isinstance(surface, dict):
            continue
        surface_id = surface.get("surface_id")
        patterns = surface.get("depends_on_patterns")
        if not isinstance(surface_id, str) or not isinstance(patterns, list):
            raise ResolverError("freshness surface contract is malformed")
        matched = sorted(
            {
                path
                for path in changed
                for pattern in patterns
                if isinstance(pattern, str) and path_matches(path, pattern)
            }
        )
        evaluator = surface.get("evaluator")
        if evaluator == "agents_current_state":
            state = agents_evaluation["state"]
            refresh_required = agents_evaluation["refresh_required"]
            reason = agents_evaluation["reason"]
        elif matched:
            state = "AFFECTED_CHECK_REQUIRED"
            refresh_required = False
            reason = (
                "dependency changed; v0.1 identifies impact but does not "
                "claim stale without a surface-specific coherence evaluator"
            )
        else:
            state = "NOT_AFFECTED"
            refresh_required = False
            reason = "no configured dependency path changed in the working tree"

        rows.append(
            {
                "surface_id": surface_id,
                "path": surface.get("path"),
                "role": surface.get("role"),
                "staleness_policy": surface.get("staleness_policy"),
                "state": state,
                "refresh_required": refresh_required,
                "matched_changed_paths": matched,
                "reason": reason,
            }
        )
    return rows


def build_canonical_state(root: Path) -> dict[str, Any]:
    release_doc = load_yaml(root / CURRENT_RELEASE)
    release = release_doc.get("release")
    controls = release_doc.get("coordination_controls")
    module_scope = release_doc.get("module_scope")
    progression = release_doc.get("progression_gate_policy")
    if not all(isinstance(item, dict) for item in (release, controls, module_scope, progression)):
        raise ResolverError("current release authority sections are incomplete")

    policy = release_policy_state(load_yaml(root / RELEASE_POLICY))
    hi_total = human_intent_total(load_yaml(root / HUMAN_INTENT_INDEX))

    prompt_id = "logistics_service_authority_lineage_and_module_bootstrap_v0_1"
    record = find_prompt_record(load_yaml(root / LOGISTICS_QUEUE), prompt_id)
    queue_status = queue_execution_status(record)

    return {
        "authority_source": CURRENT_RELEASE.as_posix(),
        "base_release": release.get("base_release"),
        "base_release_state": release.get("base_release_state"),
        "hardening_release": release.get("hardening_release"),
        "hardening_state": release.get("hardening_state"),
        "current_slice": release.get("current_slice"),
        "current_phase": progression.get("current_phase"),
        "pilot_module": module_scope.get("pilot_module"),
        "automatic_accept": controls.get("automatic_accept"),
        "automatic_release_next_prompt": controls.get("automatic_release_next_prompt"),
        "current_execution_mode": progression.get("current_execution_mode"),
        "logistics_prompt_id": prompt_id,
        "logistics_queue_status": queue_status,
        "release_policy_state": policy["state"],
        "release_policy": policy,
        "human_intent_total": hi_total,
    }


def foundation_status(root: Path) -> dict[str, Any]:
    governance = load_module(
        root / GOVERNANCE_RENDERER,
        "forprint_blueprint_governance_renderer_for_canonical_state",
    )
    freshness = load_module(
        root / FRESHNESS_ASSESSOR,
        "forprint_blueprint_repository_freshness_for_canonical_state",
    )

    governance_manifest = governance.build_manifest(root)
    freshness_report = freshness.assess(root / SNAPSHOT_GATE, repo=root)

    governance_consistency = governance_manifest.get("source_consistency")
    freshness_metadata = freshness_report.get("metadata")
    freshness_summary = freshness_report.get("summary")

    return {
        "governance_projection": {
            "source": GOVERNANCE_RENDERER.as_posix(),
            "schema_version": governance_manifest.get("schema_version"),
            "source_consistency_state": (
                governance_consistency.get("state")
                if isinstance(governance_consistency, dict)
                else None
            ),
        },
        "repository_knowledge_freshness": {
            "source": FRESHNESS_ASSESSOR.as_posix(),
            "schema_version": freshness_report.get("schema_version"),
            "result": (
                freshness_metadata.get("result") if isinstance(freshness_metadata, dict) else None
            ),
            "release_decision": (
                freshness_summary.get("release_decision")
                if isinstance(freshness_summary, dict)
                else None
            ),
            "bounded_refresh_snapshot_count": (
                freshness_summary.get("bounded_refresh_snapshot_count")
                if isinstance(freshness_summary, dict)
                else None
            ),
        },
        "task_context_primitive": {
            "source": CONTEXT_BUILDER.as_posix(),
            "available": (root / CONTEXT_BUILDER).is_file(),
            "role": "existing_context_primitive_to_evolve_not_replace",
        },
    }


def build_report(
    root: Path,
    *,
    contracts_path: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    contracts_file = contracts_path or root / DEFAULT_CONTRACTS
    if not contracts_file.is_absolute():
        contracts_file = root / contracts_file
    contracts = load_yaml(contracts_file)

    canonical = build_canonical_state(root)
    agents_text = (root / AGENTS).read_text(encoding="utf-8")
    agents_eval = evaluate_agents_current_state_text(agents_text, canonical)
    changed = changed_paths(root)
    impacts = impacted_surfaces(
        contracts,
        changed,
        agents_evaluation=agents_eval,
    )
    foundations = foundation_status(root)

    consistency_issues: list[str] = []
    if canonical["release_policy_state"] != "FAIL_CLOSED":
        consistency_issues.append("release policy is not fail-closed")
    if canonical["logistics_queue_status"] != "ready_for_module_pull":
        consistency_issues.append("Logistics bootstrap prompt is not ready_for_module_pull")
    if canonical["automatic_accept"] is not False:
        consistency_issues.append("automatic_accept is not false")
    if canonical["automatic_release_next_prompt"] is not False:
        consistency_issues.append("automatic_release_next_prompt is not false")
    if agents_eval["state"] != "FRESH":
        consistency_issues.append("AGENTS current-state projection is stale")
    if foundations["governance_projection"]["source_consistency_state"] != "agreed":
        consistency_issues.append("existing governance transparency sources are not agreed")
    if foundations["repository_knowledge_freshness"]["result"] != "PASSED":
        consistency_issues.append("existing repository knowledge freshness assessment did not pass")

    return {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "result": "PASS" if not consistency_issues else "ATTENTION_REQUIRED",
            "repository_head": git(root, "rev-parse", "HEAD"),
            "read_only": True,
            "independent_authority": False,
        },
        "canonical_state": canonical,
        "source_consistency": {
            "state": "AGREED" if not consistency_issues else "DISAGREED",
            "issues": consistency_issues,
        },
        "freshness": {
            "agents_current_state_projection": agents_eval,
            "existing_foundations": foundations,
        },
        "working_tree_impact": {
            "changed_path_count": len(changed),
            "changed_paths": changed,
            "surface_count": len(impacts),
            "surfaces": impacts,
            "refresh_required_surfaces": [
                item["surface_id"] for item in impacts if item["refresh_required"]
            ],
            "affected_check_required_surfaces": [
                item["surface_id"] for item in impacts if item["state"] == "AFFECTED_CHECK_REQUIRED"
            ],
        },
        "boundaries": {
            "writes_performed": False,
            "authority_rewritten": False,
            "release_transition_performed": False,
            "prompt_transition_performed": False,
            "module_start_performed": False,
            "commit_push_performed": False,
        },
    }


def render_text(report: dict[str, Any]) -> str:
    state = report["canonical_state"]
    consistency = report["source_consistency"]
    freshness = report["freshness"]["agents_current_state_projection"]
    impact = report["working_tree_impact"]
    lines = [
        "ForPrint Blueprint Canonical State + Freshness/Impact",
        "",
        f"result: {report['metadata']['result']}",
        f"release: {state['hardening_release']} {state['hardening_state']}",
        f"phase: {state['current_phase']}",
        f"pilot: {state['pilot_module']}",
        f"logistics prompt: {state['logistics_prompt_id']}",
        f"queue: {state['logistics_queue_status']}",
        f"release policy: {state['release_policy_state']}",
        f"human intent total: {state['human_intent_total']}",
        f"source consistency: {consistency['state']}",
        f"AGENTS projection: {freshness['state']}",
        f"changed paths: {impact['changed_path_count']}",
        "refresh required: "
        + (
            ", ".join(impact["refresh_required_surfaces"])
            if impact["refresh_required_surfaces"]
            else "none"
        ),
        "affected / check required: "
        + (
            ", ".join(impact["affected_check_required_surfaces"])
            if impact["affected_check_required_surfaces"]
            else "none"
        ),
        "",
        "read-only: true",
        "independent authority: false",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--contracts")
    parser.add_argument(
        "--format",
        choices=("yaml", "json", "text"),
        default="text",
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    contracts = Path(args.contracts) if args.contracts else None
    report = build_report(root, contracts_path=contracts)

    if args.format == "yaml":
        rendered = yaml.safe_dump(
            report,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        )
    elif args.format == "json":
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    else:
        rendered = render_text(report)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 0 if report["metadata"]["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
