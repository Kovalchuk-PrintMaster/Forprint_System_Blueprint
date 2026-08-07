#!/usr/bin/env python3
"""Read-only reconciliation of historical module completion acceptance evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

HISTORICAL_ACCEPTANCE = "HISTORICAL_ACCEPTANCE"
HISTORICAL_EVIDENCE_UNRESOLVED = "HISTORICAL_EVIDENCE_UNRESOLVED"
PENDING_OPERATOR_REVIEW = "PENDING_OPERATOR_REVIEW"
NO_COMPLETION_EVIDENCE = "NO_COMPLETION_EVIDENCE"

ACCEPTED_CONTROL_VALUES = {
    "accepted",
    "accepted_by_blueprint",
}
CONTROL_PATHS = (
    "coordination/outgoing_prompts/{module_id}/index.yaml",
    "coordination/roadmaps/{module_id}.yaml",
    "coordination/self_coordination/module_plans/{module_id}.yaml",
)


class ReconciliationError(ValueError):
    """Raised when committed reconciliation evidence cannot be verified."""


@dataclass(frozen=True)
class GitEvidence:
    requested: str
    resolved: str


def _run_git(
    repo: Path,
    *args: str,
    allowed_returncodes: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        check=False,
    )
    if result.returncode not in allowed_returncodes:
        detail = (
            result.stderr.decode("utf-8", errors="replace").strip()
            or result.stdout.decode("utf-8", errors="replace").strip()
        )
        raise ReconciliationError(f"git {' '.join(args)} failed in {repo}: {detail}")
    return result


def _git_text(repo: Path, *args: str) -> str:
    return (
        _run_git(repo, *args)
        .stdout.decode(
            "utf-8",
            errors="replace",
        )
        .strip()
    )


def _resolve_commit(repo: Path, commit: str) -> GitEvidence:
    requested = commit.strip()
    if not requested:
        raise ReconciliationError("empty Git commit identifier")
    resolved = _git_text(
        repo,
        "rev-parse",
        "--verify",
        f"{requested}^{{commit}}",
    )
    return GitEvidence(
        requested=requested,
        resolved=resolved,
    )


def _is_ancestor(
    repo: Path,
    ancestor: str,
    descendant: str,
) -> bool:
    result = _run_git(
        repo,
        "merge-base",
        "--is-ancestor",
        ancestor,
        descendant,
        allowed_returncodes=(0, 1),
    )
    return result.returncode == 0


def _path_exists_at_commit(
    repo: Path,
    commit: str,
    path: str,
) -> bool:
    result = _run_git(
        repo,
        "cat-file",
        "-e",
        f"{commit}:{path}",
        allowed_returncodes=(0, 1, 128),
    )
    return result.returncode == 0


def _show_bytes(
    repo: Path,
    commit: str,
    path: str,
) -> bytes:
    result = _run_git(
        repo,
        "show",
        f"{commit}:{path}",
    )
    return result.stdout


def _load_yaml_bytes(
    data: bytes,
    *,
    label: str,
) -> dict[str, Any]:
    try:
        value = yaml.safe_load(data.decode("utf-8", errors="replace"))
    except yaml.YAMLError as error:
        raise ReconciliationError(f"invalid YAML in {label}: {error}") from error
    if not isinstance(value, dict):
        raise ReconciliationError(f"YAML root must be a mapping: {label}")
    return value


def _load_yaml_at_commit(
    repo: Path,
    commit: str,
    path: str,
) -> dict[str, Any]:
    return _load_yaml_bytes(
        _show_bytes(repo, commit, path),
        label=f"{commit}:{path}",
    )


def _list_paths(
    repo: Path,
    commit: str,
    prefix: str,
) -> list[str]:
    output = _git_text(
        repo,
        "ls-tree",
        "-r",
        "--name-only",
        commit,
        "--",
        prefix,
    )
    return [line for line in output.splitlines() if line]


def _prompt_control_records(
    value: Any,
    prompt_id: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    if isinstance(value, dict):
        direct_strings = {
            key: item
            for key, item in value.items()
            if isinstance(key, str) and isinstance(item, str)
        }
        if prompt_id in direct_strings.values():
            records.append(
                {
                    "direct_strings": direct_strings,
                }
            )

        for item in value.values():
            records.extend(_prompt_control_records(item, prompt_id))
        return records

    if isinstance(value, list):
        for item in value:
            records.extend(_prompt_control_records(item, prompt_id))

    return records


def _control_signals(
    *,
    blueprint_root: Path,
    blueprint_commit: str,
    module_id: str,
    prompt_id: str,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for template in CONTROL_PATHS:
        path = template.format(module_id=module_id)
        if not _path_exists_at_commit(
            blueprint_root,
            blueprint_commit,
            path,
        ):
            continue

        value = _load_yaml_at_commit(
            blueprint_root,
            blueprint_commit,
            path,
        )
        records = _prompt_control_records(value, prompt_id)
        if not records:
            continue

        direct_values = {
            scalar for record in records for scalar in record["direct_strings"].values()
        }
        accepted_values = sorted(direct_values & ACCEPTED_CONTROL_VALUES)
        signals.append(
            {
                "path": path,
                "matched_record_count": len(records),
                "accepted_values": accepted_values,
            }
        )
    return signals


def _packet_index(
    *,
    module_root: Path,
    module_commit: str,
    module_id: str,
) -> dict[str, dict[str, Any]]:
    prefix = "coordination/completion_packets/records"
    result: dict[str, dict[str, Any]] = {}
    for path in _list_paths(module_root, module_commit, prefix):
        if Path(path).suffix not in {".yaml", ".yml"}:
            continue
        data = _load_yaml_at_commit(
            module_root,
            module_commit,
            path,
        )
        if data.get("module_id") != module_id:
            continue
        prompt_id = data.get("prompt_id")
        if not isinstance(prompt_id, str) or not prompt_id.strip():
            continue
        if prompt_id in result:
            raise ReconciliationError(
                f"multiple committed completion packets found for {prompt_id}"
            )
        result[prompt_id] = {
            "path": path,
            "data": data,
        }
    return result


def _review_index(
    *,
    blueprint_root: Path,
    blueprint_commit: str,
    module_id: str,
) -> dict[str, list[dict[str, Any]]]:
    prefix = f"coordination/review_packets/{module_id}/processed"
    result: dict[str, list[dict[str, Any]]] = {}
    for path in _list_paths(
        blueprint_root,
        blueprint_commit,
        prefix,
    ):
        if Path(path).suffix not in {".yaml", ".yml"}:
            continue
        data = _load_yaml_at_commit(
            blueprint_root,
            blueprint_commit,
            path,
        )
        if data.get("module_id") != module_id:
            continue
        prompt_id = data.get("prompt_id")
        if not isinstance(prompt_id, str) or not prompt_id.strip():
            continue
        result.setdefault(prompt_id, []).append(
            {
                "path": path,
                "data": data,
            }
        )
    for reviews in result.values():
        reviews.sort(key=lambda row: row["path"])
    return result


def _verify_accepted_review(
    *,
    module_root: Path,
    module_id: str,
    prompt_id: str,
    review_path: str,
    review: dict[str, Any],
) -> tuple[bool, list[str], dict[str, Any]]:
    reasons: list[str] = []
    proof: dict[str, Any] = {
        "review_path": review_path,
        "review_decision": review.get("decision"),
    }

    if review.get("decision") != "accepted":
        reasons.append("processed review decision is not accepted")
        return False, reasons, proof

    module_evidence = review.get("module_evidence")
    if not isinstance(module_evidence, dict):
        reasons.append("processed review module_evidence is missing")
        return False, reasons, proof

    packet_path = module_evidence.get("packet_path")
    completion_commit = module_evidence.get("completion_commit")
    implementation_commit = module_evidence.get("implementation_commit")
    report_path = module_evidence.get("report_path")

    required = {
        "packet_path": packet_path,
        "completion_commit": completion_commit,
        "implementation_commit": implementation_commit,
        "report_path": report_path,
    }
    for field, value in required.items():
        if not isinstance(value, str) or not value.strip():
            reasons.append(f"processed review {field} is missing")
    if reasons:
        return False, reasons, proof

    try:
        resolved_completion = _resolve_commit(
            module_root,
            completion_commit,
        )
        resolved_review_implementation = _resolve_commit(
            module_root,
            implementation_commit,
        )
    except ReconciliationError as error:
        reasons.append(str(error))
        return False, reasons, proof

    proof["completion_commit"] = {
        "requested": resolved_completion.requested,
        "resolved": resolved_completion.resolved,
    }
    proof["review_implementation_commit"] = {
        "requested": resolved_review_implementation.requested,
        "resolved": resolved_review_implementation.resolved,
    }

    if not _path_exists_at_commit(
        module_root,
        resolved_completion.resolved,
        packet_path,
    ):
        reasons.append("reviewed packet does not exist at completion commit")
        return False, reasons, proof

    if not _path_exists_at_commit(
        module_root,
        resolved_completion.resolved,
        report_path,
    ):
        reasons.append("reviewed completion report does not exist at completion commit")

    packet = _load_yaml_at_commit(
        module_root,
        resolved_completion.resolved,
        packet_path,
    )
    proof["packet_path"] = packet_path
    proof["report_path"] = report_path

    if packet.get("module_id") != module_id:
        reasons.append("packet module_id does not match processed review")
    if packet.get("prompt_id") != prompt_id:
        reasons.append("packet prompt_id does not match processed review")

    packet_implementation = packet.get("implementation_commit")
    if not isinstance(packet_implementation, str):
        reasons.append("packet implementation_commit is missing")
    else:
        try:
            resolved_packet_implementation = _resolve_commit(
                module_root,
                packet_implementation,
            )
        except ReconciliationError as error:
            reasons.append(str(error))
        else:
            proof["packet_implementation_commit"] = {
                "requested": resolved_packet_implementation.requested,
                "resolved": resolved_packet_implementation.resolved,
            }
            if resolved_packet_implementation.resolved != resolved_review_implementation.resolved:
                reasons.append("review and packet implementation commits differ")
            if not _is_ancestor(
                module_root,
                resolved_packet_implementation.resolved,
                resolved_completion.resolved,
            ):
                reasons.append("implementation commit is not an ancestor of completion commit")

    return not reasons, reasons, proof


def reconcile(
    *,
    blueprint_root: Path,
    module_id: str,
    module_root: Path,
    prompt_ids: list[str],
    blueprint_commit: str = "HEAD",
    module_commit: str = "HEAD",
) -> dict[str, Any]:
    """Classify committed completion evidence without repository writes."""

    blueprint_root = blueprint_root.resolve()
    module_root = module_root.resolve()
    if not blueprint_root.is_dir():
        raise ReconciliationError(f"Blueprint root does not exist: {blueprint_root}")
    if not module_root.is_dir():
        raise ReconciliationError(f"module root does not exist: {module_root}")

    blueprint_git = _resolve_commit(
        blueprint_root,
        blueprint_commit,
    )
    module_git = _resolve_commit(
        module_root,
        module_commit,
    )

    packets = _packet_index(
        module_root=module_root,
        module_commit=module_git.resolved,
        module_id=module_id,
    )
    reviews = _review_index(
        blueprint_root=blueprint_root,
        blueprint_commit=blueprint_git.resolved,
        module_id=module_id,
    )

    items: list[dict[str, Any]] = []
    for prompt_id in prompt_ids:
        packet_entry = packets.get(prompt_id)
        prompt_reviews = reviews.get(prompt_id, [])
        signals = _control_signals(
            blueprint_root=blueprint_root,
            blueprint_commit=blueprint_git.resolved,
            module_id=module_id,
            prompt_id=prompt_id,
        )
        accepted_control = any(signal["accepted_values"] for signal in signals)

        item: dict[str, Any] = {
            "module_id": module_id,
            "prompt_id": prompt_id,
            "packet_path": (packet_entry["path"] if packet_entry is not None else None),
            "processed_review_count": len(prompt_reviews),
            "control_signals": signals,
            "classification": None,
            "reasons": [],
            "acceptance_proof": None,
            "operator_decision_performed": False,
        }

        if prompt_reviews:
            accepted_reviews = [
                review for review in prompt_reviews if review["data"].get("decision") == "accepted"
            ]
            if len(prompt_reviews) != 1 or len(accepted_reviews) != 1:
                item["classification"] = HISTORICAL_EVIDENCE_UNRESOLVED
                item["reasons"].append(
                    "processed review records are ambiguous or "
                    "do not contain exactly one accepted decision"
                )
            else:
                review_entry = accepted_reviews[0]
                verified, reasons, proof = _verify_accepted_review(
                    module_root=module_root,
                    module_id=module_id,
                    prompt_id=prompt_id,
                    review_path=review_entry["path"],
                    review=review_entry["data"],
                )
                item["acceptance_proof"] = proof
                if verified:
                    item["classification"] = HISTORICAL_ACCEPTANCE
                else:
                    item["classification"] = HISTORICAL_EVIDENCE_UNRESOLVED
                    item["reasons"].extend(reasons)
        elif accepted_control:
            item["classification"] = HISTORICAL_EVIDENCE_UNRESOLVED
            item["reasons"].append(
                "Blueprint control state contains an acceptance signal "
                "but no processed review record exists"
            )
        elif packet_entry is not None:
            item["classification"] = PENDING_OPERATOR_REVIEW
            item["reasons"].append(
                "module completion packet exists but no processed Blueprint review decision exists"
            )
        else:
            item["classification"] = NO_COMPLETION_EVIDENCE
            item["reasons"].append("no committed completion packet or processed review was found")

        items.append(item)

    counts: dict[str, int] = {}
    for item in items:
        classification = item["classification"]
        counts[classification] = counts.get(classification, 0) + 1

    return {
        "schema_version": ("blueprint_historical_acceptance_reconciliation_v0_1"),
        "metadata": {
            "blueprint_commit": blueprint_git.resolved,
            "module_commit": module_git.resolved,
            "module_id": module_id,
            "read_only": True,
            "committed_objects_only": True,
        },
        "summary": {
            "candidate_count": len(items),
            "classification_counts": counts,
            "processed_review_record_count": sum(len(value) for value in reviews.values()),
        },
        "items": items,
        "boundaries": {
            "module_repository_write": False,
            "completion_packet_write": False,
            "review_decision_write": False,
            "automatic_acceptance": False,
            "automatic_return": False,
        },
        "result": ("BLUEPRINT_HISTORICAL_ACCEPTANCE_RECONCILIATION_READY"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Reconcile historical completion acceptance from committed "
            "Blueprint and module Git evidence."
        )
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--module", required=True)
    parser.add_argument("--module-root", required=True)
    parser.add_argument(
        "--prompt-id",
        action="append",
        dest="prompt_ids",
        required=True,
    )
    parser.add_argument("--blueprint-commit", default="HEAD")
    parser.add_argument("--module-commit", default="HEAD")
    parser.add_argument(
        "--output-format",
        choices=("text", "json", "yaml"),
        default="text",
    )
    args = parser.parse_args()

    try:
        result = reconcile(
            blueprint_root=Path(args.root),
            module_id=args.module,
            module_root=Path(args.module_root),
            prompt_ids=args.prompt_ids,
            blueprint_commit=args.blueprint_commit,
            module_commit=args.module_commit,
        )
    except ReconciliationError as error:
        if args.output_format == "json":
            print(
                json.dumps(
                    {
                        "result": "failed",
                        "error": str(error),
                    },
                    indent=2,
                )
            )
        elif args.output_format == "yaml":
            print(
                yaml.safe_dump(
                    {
                        "result": "failed",
                        "error": str(error),
                    },
                    sort_keys=False,
                ),
                end="",
            )
        else:
            print("FAILED: historical acceptance reconciliation")
            print(f"- {error}")
            print("RESULT: BLUEPRINT_HISTORICAL_ACCEPTANCE_RECONCILIATION_FAILED")
        return 1

    if args.output_format == "json":
        print(json.dumps(result, indent=2))
        return 0
    if args.output_format == "yaml":
        print(
            yaml.safe_dump(
                result,
                sort_keys=False,
                width=120,
            ),
            end="",
        )
        return 0

    print("Historical acceptance reconciliation")
    for item in result["items"]:
        print(f"- {item['prompt_id']}: {item['classification']}")
    print("Automatic acceptance: False")
    print("Automatic return: False")
    print("RESULT: BLUEPRINT_HISTORICAL_ACCEPTANCE_RECONCILIATION_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
