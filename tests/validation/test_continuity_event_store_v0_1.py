from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.coordination import continuity
from scripts.indexing import build_blueprint_knowledge_index as knowledge_index

ROOT = Path(__file__).resolve().parents[2]


def _state(label: str) -> dict:
    payload = {
        "schema_version": continuity.STATE_SCHEMA,
        "source_mode": "working_tree",
        "git_head": "a" * 40,
        "git_branch": "test",
        "durable_dirty_paths": [f"{label}.txt"],
        "dirty_path_status": {f"{label}.txt": " M"},
        "dirty_path_content_or_symlink_fingerprint": {
            f"{label}.txt": {
                "kind": "file",
                "sha256": "b" * 64,
                "bytes": 1,
            }
        },
        "rename_or_copy_origins": {},
        "bounded_final_applied_artifact_hashes": {"scripts/example.py": "c" * 64},
        "exclusion_policy": {
            "runtime_top_level": [],
            "runtime_exact": [],
            "runtime_recursive_parts": [],
            "non_source_prefixes": [],
            "reports_implicitly_excluded": False,
        },
    }
    payload["fingerprint_sha256"] = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return payload


def _spec(path: Path, event_id: str) -> Path:
    value = {
        "schema_version": continuity.SPEC_SCHEMA,
        "event_id": event_id,
        "work_id": "u-test",
        "occurred_at": "2026-09-10T12:00:00Z",
        "actor": "test",
        "summary": "Test checkpoint",
        "bootstrap_historical_import": True,
        "what_changed": ["test change"],
        "why": "test append-only semantics",
        "evidence": [{"kind": "test", "result": "PASS"}],
        "decision_rationale": "content addressed events are deterministic",
        "rejected_alternative_when_material": "in-place mutable state",
        "blockers": [],
        "unknowns": [],
        "next_actions": [
            {"order": 1, "id": "a"},
            {"order": 2, "id": "b"},
            {"order": 3, "id": "c"},
            {"order": 4, "id": "d"},
            {"order": 5, "id": "e"},
        ],
        "source_state_before": _state("before"),
        "source_state_after": _state("after"),
        "final_applied_artifact_hashes": {"scripts/example.py": "c" * 64},
        "external_baseline_preserved": True,
    }
    path.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_source_fingerprint_exclusions_are_explicit_and_reports_remain() -> None:
    assert continuity.excluded_from_source_fingerprint(Path("tmp.py"))
    assert continuity.excluded_from_source_fingerprint(Path("tmp/session/evidence.json"))
    assert continuity.excluded_from_source_fingerprint(Path("scripts/__pycache__/x.pyc"))
    assert continuity.excluded_from_source_fingerprint(Path("indexes/references.json"))
    assert continuity.excluded_from_source_fingerprint(
        Path("coordination/continuity/events/000001__x__abc.yaml")
    )
    assert not continuity.excluded_from_source_fingerprint(Path("reports/current_validation.yaml"))
    assert not continuity.excluded_from_source_fingerprint(
        Path("scripts/coordination/continuity.py")
    )


def test_checkpoint_append_is_content_addressed_and_duplicate_safe(
    tmp_path: Path,
) -> None:
    event_root = tmp_path / "events"
    spec = _spec(tmp_path / "spec.yaml", "evt-test-checkpoint")

    first = continuity.append_checkpoint(
        root=ROOT,
        spec_path=spec,
        event_root=event_root,
    )
    assert first.exists()
    assert first.name.startswith("000001__evt-test-checkpoint__")
    assert first.name.endswith(f"__{continuity.sha256_file(first)[:12]}.yaml")

    with pytest.raises(continuity.ContinuityError, match="duplicate event_id"):
        continuity.append_checkpoint(
            root=ROOT,
            spec_path=spec,
            event_root=event_root,
        )

    assert len(continuity.event_files(event_root)) == 1


def test_second_checkpoint_chains_to_first(tmp_path: Path) -> None:
    event_root = tmp_path / "events"
    first = continuity.append_checkpoint(
        root=ROOT,
        spec_path=_spec(tmp_path / "one.yaml", "evt-test-one"),
        event_root=event_root,
    )
    second = continuity.append_checkpoint(
        root=ROOT,
        spec_path=_spec(tmp_path / "two.yaml", "evt-test-two"),
        event_root=event_root,
    )

    event = continuity.read_event(second)
    assert event["sequence"] == 2
    assert event["previous_event_id"] == "evt-test-one"
    assert event["previous_event_sha256"] == continuity.sha256_file(first)


def test_checkpoint_requires_five_to_ten_next_actions(tmp_path: Path) -> None:
    spec = yaml.safe_load(
        _spec(tmp_path / "spec.yaml", "evt-test-bounds").read_text(encoding="utf-8")
    )
    spec["next_actions"] = [{"order": 1, "id": "only"}]
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(spec), encoding="utf-8")

    with pytest.raises(
        continuity.ContinuityError,
        match="between 5 and 10",
    ):
        continuity.append_checkpoint(
            root=ROOT,
            spec_path=path,
            event_root=tmp_path / "events",
        )


def test_event_store_validator_accepts_content_addressed_temp_store(
    tmp_path: Path,
) -> None:
    event_root = tmp_path / "events"
    continuity.append_checkpoint(
        root=ROOT,
        spec_path=_spec(tmp_path / "spec.yaml", "evt-test-validate"),
        event_root=event_root,
    )

    cp = subprocess.run(
        [
            sys.executable,
            "scripts/validation/validate_continuity_event_store_v0_1.py",
            "--root",
            str(ROOT),
            "--event-root",
            str(event_root),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "CONTINUITY_EVENT_STORE=PASS" in cp.stdout


def test_knowledge_builder_excludes_managed_continuity_roots() -> None:
    assert knowledge_index._is_skipped_source_path(
        Path("coordination/continuity/events/000001__evt__abc.yaml")
    )
    assert knowledge_index._is_skipped_source_path(
        Path("coordination/continuity/projections/CURRENT_WORKFRONT.yaml")
    )
    assert not knowledge_index._is_skipped_source_path(Path("coordination/continuity/README.md"))
