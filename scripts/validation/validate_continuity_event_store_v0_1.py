#!/usr/bin/env python3
"""Validate the ForPrint append-only continuity checkpoint event store v0.1."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.coordination.continuity import (  # noqa: E402
    EVENT_NAME_RE,
    EVENT_SCHEMA,
    build_source_state,
    event_files,
    read_event,
    sha256_file,
)

EVENT_ROOT = ROOT / "coordination/continuity/events"
CONTRACT = ROOT / "coordination/standards/automation/continuity_contract_v0_1.yaml"

REQUIRED_CHECKPOINT_FIELDS = {
    "what_changed",
    "why",
    "evidence",
    "decision_rationale",
    "rejected_alternative_when_material",
    "blockers",
    "unknowns",
    "next_actions",
    "source_state_before",
    "source_state_after",
    "final_applied_artifact_hashes",
    "external_baseline_preserved",
}


def fail(message: str) -> int:
    print(f"CONTINUITY_EVENT_STORE=FAIL {message}")
    return 1


def _validate_state_object(state: object, label: str) -> str | None:
    if not isinstance(state, dict):
        return f"{label}_not_mapping"
    digest = state.get("fingerprint_sha256")
    if not isinstance(digest, str) or not re.fullmatch(
        r"[0-9a-f]{64}",
        digest,
    ):
        return f"{label}_fingerprint"
    required = {
        "git_head",
        "git_branch",
        "durable_dirty_paths",
        "dirty_path_status",
        "dirty_path_content_or_symlink_fingerprint",
        "bounded_final_applied_artifact_hashes",
    }
    if not required.issubset(state):
        return f"{label}_components"
    return None


def validate_store(
    *,
    root: Path,
    event_root: Path,
    require_current_state_match: bool,
) -> tuple[bool, str, dict]:
    files = event_files(event_root)
    if not files:
        return False, "no_events", {}

    seen_ids: set[str] = set()
    previous_id: str | None = None
    previous_sha: str | None = None
    latest_checkpoint: dict | None = None

    for expected_sequence, path in enumerate(files, start=1):
        match = EVENT_NAME_RE.fullmatch(path.name)
        if match is None:
            return False, f"invalid_filename={path.name}", {}

        if int(match.group("sequence")) != expected_sequence:
            return False, f"sequence_gap={path.name}", {}

        actual_sha = sha256_file(path)
        if actual_sha[:12] != match.group("sha"):
            return False, f"content_address_mismatch={path.name}", {}

        try:
            event = read_event(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            return False, f"parse={path.name}:{exc}", {}

        if event.get("schema_version") != EVENT_SCHEMA:
            return False, f"schema={path.name}", {}
        if event.get("sequence") != expected_sequence:
            return False, f"embedded_sequence={path.name}", {}

        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            return False, f"event_id={path.name}", {}
        if event_id != match.group("event_id"):
            return False, f"filename_event_id={path.name}", {}
        if event_id in seen_ids:
            return False, f"duplicate_event_id={event_id}", {}
        seen_ids.add(event_id)

        if event.get("previous_event_id") != previous_id:
            return False, f"previous_event_id={path.name}", {}
        if event.get("previous_event_sha256") != previous_sha:
            return False, f"previous_event_sha256={path.name}", {}

        if event.get("event_type") == "CHECKPOINT_RECORDED":
            checkpoint = event.get("checkpoint")
            if not isinstance(checkpoint, dict):
                return False, f"checkpoint_mapping={path.name}", {}
            missing = REQUIRED_CHECKPOINT_FIELDS - set(checkpoint)
            if missing:
                return (
                    False,
                    f"checkpoint_fields={path.name}:{sorted(missing)}",
                    {},
                )
            actions = checkpoint.get("next_actions")
            if not isinstance(actions, list) or not 5 <= len(actions) <= 10:
                return False, f"next_actions={path.name}", {}
            if checkpoint.get("external_baseline_preserved") is not True:
                return False, f"external_baseline={path.name}", {}

            before_error = _validate_state_object(
                checkpoint.get("source_state_before"),
                "source_state_before",
            )
            if before_error:
                return False, f"{before_error}={path.name}", {}
            after_error = _validate_state_object(
                checkpoint.get("source_state_after"),
                "source_state_after",
            )
            if after_error:
                return False, f"{after_error}={path.name}", {}

            after = checkpoint["source_state_after"]
            if event.get("source_state_ref") != after.get("fingerprint_sha256"):
                return False, f"source_state_ref={path.name}", {}

            hashes = checkpoint.get("final_applied_artifact_hashes")
            if not isinstance(hashes, dict) or not hashes:
                return False, f"final_hashes={path.name}", {}
            for rel, digest in hashes.items():
                if not isinstance(rel, str) or not isinstance(digest, str):
                    return False, f"final_hash_entry={path.name}", {}
                if not re.fullmatch(r"[0-9a-f]{64}", digest):
                    return False, f"final_hash_digest={path.name}", {}

            latest_checkpoint = event

        previous_id = event_id
        previous_sha = actual_sha

    first = read_event(files[0])
    if first.get("event_type") != "CHECKPOINT_RECORDED":
        return False, "genesis_must_be_checkpoint", {}
    if first.get("bootstrap_historical_import") is not True:
        return False, "genesis_historical_import_marker", {}

    current_match = None
    if require_current_state_match:
        if latest_checkpoint is None:
            return False, "no_checkpoint_for_state_match", {}
        checkpoint = latest_checkpoint["checkpoint"]
        bounded = checkpoint["final_applied_artifact_hashes"]
        current = build_source_state(
            root,
            bounded_final_applied_artifact_hashes=bounded,
        )
        expected = checkpoint["source_state_after"]["fingerprint_sha256"]
        current_match = current["fingerprint_sha256"] == expected
        if not current_match:
            return (
                False,
                "current_source_state_mismatch",
                {
                    "expected": expected,
                    "actual": current["fingerprint_sha256"],
                },
            )

    return (
        True,
        "PASS",
        {
            "event_count": len(files),
            "latest_event_id": previous_id,
            "latest_event_sha256": previous_sha,
            "latest_checkpoint_id": (
                latest_checkpoint.get("event_id") if latest_checkpoint is not None else None
            ),
            "current_source_state_match": current_match,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
    )
    parser.add_argument(
        "--event-root",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--require-current-state-match",
        action="store_true",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    event_root = (
        args.event_root.resolve()
        if args.event_root is not None
        else root / "coordination/continuity/events"
    )

    contract_path = root / "coordination/standards/automation/continuity_contract_v0_1.yaml"
    if not contract_path.is_file():
        return fail("continuity_contract_missing")

    ok, reason, details = validate_store(
        root=root,
        event_root=event_root,
        require_current_state_match=args.require_current_state_match,
    )
    if not ok:
        return fail(reason)

    print("CONTINUITY_EVENT_STORE=PASS")
    print(f"EVENT_COUNT={details['event_count']}")
    print(f"LATEST_EVENT_ID={details['latest_event_id']}")
    print(f"LATEST_EVENT_SHA256={details['latest_event_sha256']}")
    print(f"LATEST_CHECKPOINT_ID={details['latest_checkpoint_id']}")
    if args.require_current_state_match:
        print("CURRENT_SOURCE_STATE_MATCH=true")
    print("APPEND_ONLY_CONTENT_ADDRESSING=true")
    print("GENESIS_HISTORICAL_IMPORT=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
