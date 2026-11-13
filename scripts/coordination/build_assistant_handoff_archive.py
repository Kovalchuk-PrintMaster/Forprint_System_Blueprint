#!/usr/bin/env python3
"""Build deterministic zero-context ForPrint assistant handoff archive v0.1.

The archive is a runtime convenience view, not release/queue/worker authority.
It derives continuity projections in memory from the immutable event ledger and
the current working tree, so an unreconciled current delta is visible rather
than hidden by a durable projection refresh.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.coordination.build_continuity_projections import (  # noqa: E402
    PROJECTION_IDS,
    build_projection_documents,
    render_projection,
)
from scripts.coordination.continuity import (  # noqa: E402
    event_files,
    read_event,
    sha256_file,
)
from scripts.validation.validate_continuity_event_store_v0_1 import (  # noqa: E402
    validate_store,
)

COMPILER_ID = "forprint_assistant_handoff_compiler"
COMPILER_VERSION = "v0_1"
MANIFEST_SCHEMA = "forprint_assistant_handoff_manifest_v0_1"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
MAX_PAYLOAD_FILES = 40
MAX_PAYLOAD_BYTES = 8 * 1024 * 1024

ROADMAP = Path(
    "coordination/roadmaps/details/forprint_system_blueprint/continuity/"
    "2026-09-10__continuity_assistant_handoff_micro_roadmap_v0_1.yaml"
)
DEPENDENCY_REGISTRY = Path("coordination/registry/execution_dependency_registry_v0_1.yaml")
CONTRACT = Path("coordination/standards/automation/continuity_contract_v0_1.yaml")
BOOTSTRAP_START = Path("coordination/bootstrap/START_HERE.md")
BOOTSTRAP_INDEX = Path("coordination/bootstrap/index_v0_1.yaml")
AGENTS = Path("AGENTS.md")
MISSION = Path("coordination/global_policy/forprint_project_doctrine.md")

BOOTSTRAP_LIVING_PROJECT_ONBOARD_SOURCES = (
    Path("coordination/instruction_intake/assistant_reading_order.md"),
    Path("coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_2.yaml"),
    Path("coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"),
    Path("coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md"),
    Path("coordination/repository_knowledge/roadmap_enrichment/README.md"),
    Path("coordination/repository_knowledge/roadmap_enrichment/source_map.yaml"),
)

class HandoffError(RuntimeError):
    pass


class _IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _yaml_bytes(value: Any) -> bytes:
    return yaml.dump(
        value,
        Dumper=_IndentedSafeDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=120,
    ).encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def _require_regular_file(root: Path, rel: Path) -> Path:
    path = root / rel
    if not path.is_file() or path.is_symlink():
        raise HandoffError(f"required regular file missing: {rel.as_posix()}")
    return path


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise HandoffError(f"YAML mapping required: {path}")
    return value


def _mission_source(root: Path) -> Path:
    _require_regular_file(root, MISSION)
    return MISSION


def _latest_checkpoint_path(root: Path) -> Path:
    events = root / "coordination/continuity/events"
    for path in reversed(event_files(events)):
        event = read_event(path)
        if event.get("event_type") == "CHECKPOINT_RECORDED":
            return path
    raise HandoffError("continuity event store has no checkpoint")


def _dependency_slice(registry: dict[str, Any]) -> dict[str, Any]:
    artifacts = []
    for row in registry.get("artifacts", []):
        if not isinstance(row, dict):
            continue
        text = " ".join(str(row.get(key, "")) for key in ("id", "path", "producer")).lower()
        if "continuity" in text or "assistant_handoff" in text:
            artifacts.append(row)

    targets = []
    for row in registry.get("targets", []):
        if not isinstance(row, dict):
            continue
        text = str(row.get("target", "")).lower()
        if "continuity" in text or "assistant-" in text:
            targets.append(row)

    return {
        "schema_version": "forprint_assistant_handoff_dependency_slice_v0_1",
        "authority": "none",
        "source": DEPENDENCY_REGISTRY.as_posix(),
        "artifacts": artifacts,
        "targets": targets,
    }


def _roadmap_slice(roadmap: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "forprint_assistant_handoff_roadmap_slice_v0_1",
        "authority": "none",
        "source": ROADMAP.as_posix(),
        "accepted_foundations": roadmap.get("accepted_foundations", []),
        "steps": roadmap.get("steps", []),
        "next_action": roadmap.get("next_action", {}),
        "deferred_after_continuity_foundation": roadmap.get(
            "deferred_after_continuity_foundation",
            [],
        ),
    }


def _knowledge_health(
    latest_event: dict[str, Any],
    *,
    event_store_details: dict[str, Any],
    delta_material: bool,
) -> dict[str, Any]:
    checkpoint = latest_event.get("checkpoint", {})
    evidence = checkpoint.get("evidence", []) if isinstance(checkpoint, dict) else []
    acceptance = [
        item
        for item in evidence
        if isinstance(item, dict) and item.get("kind") == "current_acceptance_gate"
    ]
    return {
        "schema_version": "forprint_assistant_handoff_knowledge_health_v0_1",
        "authority": "none",
        "source": "latest_immutable_checkpoint_evidence",
        "latest_checkpoint_event_id": latest_event.get("event_id"),
        "event_store_validated": True,
        "event_count": event_store_details.get("event_count"),
        "latest_event_sha256": event_store_details.get("latest_event_sha256"),
        "current_unreconciled_delta_material": delta_material,
        "latest_checkpoint_acceptance_evidence": acceptance,
        "claim_scope": (
            "This handoff compiler does not independently promote repository "
            "knowledge health; it carries accepted checkpoint evidence and "
            "current continuity/source-state derivations."
        ),
    }


def _unknowns(latest_event: dict[str, Any]) -> dict[str, Any]:
    checkpoint = latest_event.get("checkpoint")
    unknowns = []
    if isinstance(checkpoint, dict):
        value = checkpoint.get("unknowns", [])
        if isinstance(value, list):
            unknowns = value
    return {
        "schema_version": "forprint_assistant_handoff_unknowns_v0_1",
        "authority": "none",
        "source_checkpoint_event_id": latest_event.get("event_id"),
        "unresolved_unknown_count": len(unknowns),
        "unknowns": unknowns,
    }


def _read_first(
    *,
    mission_source: Path,
    latest_event: dict[str, Any],
    projections: dict[str, dict[str, Any]],
) -> bytes:
    source_state = projections["SOURCE_STATE"]["payload"]
    delta = projections["UNRECONCILED_CURRENT_DELTA"]["payload"]
    workfront = projections["CURRENT_WORKFRONT"]["payload"]
    blockers = projections["BLOCKERS"]["payload"]
    horizon = projections["NEXT_HORIZON"]["payload"]
    checkpoint = latest_event.get("checkpoint", {})
    unknowns = checkpoint.get("unknowns", []) if isinstance(checkpoint, dict) else []
    action_ids = [
        str(item.get("id")) for item in horizon.get("actions", []) if isinstance(item, dict)
    ]

    action_lines = "\n".join(f"{index}. {value}" for index, value in enumerate(action_ids, start=1))

    text = f"""# ForPrint Assistant Handoff — READ FIRST

This archive is a deterministic, non-authoritative continuity handoff.
It is not release authority, queue authority, operator approval, or worker-dispatch authority.

## Project and mission

Mission source inside this pack: `project_mission.md`
Repository source: `{mission_source.as_posix()}`

## Binding interaction and mutation rules

Read `AGENTS.md` before proposing mutation.
Read `coordination/bootstrap/START_HERE.md` and `coordination/bootstrap/index_v0_1.yaml`.
Chat transcript is not project source of truth.
Dirty working-tree state is valid and must not be erased with reset/stash/rebase.
Accepted continuity events are append-only; generated projections are not authority.

## Latest accepted checkpoint

Event: `{latest_event.get("event_id")}`
Work: `{latest_event.get("work_id")}`
Summary: `{latest_event.get("summary")}`

## Present state

Current source matches latest checkpoint: `{str(bool(source_state.get("current_matches_latest_checkpoint"))).lower()}`
Unreconciled current delta material: `{str(bool(delta.get("material"))).lower()}`
Open work items represented by current event stream: `{workfront.get("active_work_count", 0)}`
Unresolved blockers: `{blockers.get("unresolved_blocker_count", 0)}`
Unresolved unknowns in latest checkpoint: `{len(unknowns)}`

If `UNRECONCILED_CURRENT_DELTA.yaml` says `material: true`, treat it as visible active state.
Do not silently fold it into the last checkpoint.

## Next horizon

Next-horizon action ids (see NEXT_HORIZON.yaml derivation metadata):
{action_lines}

## Reading order

1. `AGENTS.md`
2. `coordination/instruction_intake/assistant_reading_order.md`
3. `project_mission.md`
4. `latest_checkpoint.yaml`
5. `SOURCE_STATE.yaml`
6. `UNRECONCILED_CURRENT_DELTA.yaml`
7. `CURRENT_WORKFRONT.yaml`
8. `BLOCKERS.yaml` and `UNKNOWNS.yaml`
9. `NEXT_HORIZON.yaml`
10. `RECENT_ACTIVITY.yaml` and `DECISIONS.yaml`
10. `roadmap_slice.yaml`, `execution_dependency_slice.yaml`, `knowledge_health.yaml`

The later zero-context acceptance step will test whether a fresh assistant can answer
the project/mission, rules, completed work, current work, blockers/unknowns, and next
5-10 actions using this archive alone.
"""
    return text.encode("utf-8")


def build_payload(
    root: Path = ROOT,
    *,
    projection_documents: dict[str, dict[str, Any]] | None = None,
    project_onboard_sources: tuple[Path, ...] = (),
) -> tuple[dict[str, bytes], dict[str, Any]]:
    root = root.resolve()

    event_root = root / "coordination/continuity/events"
    ok, reason, event_details = validate_store(
        root=root,
        event_root=event_root,
        require_current_state_match=False,
    )
    if not ok:
        raise HandoffError(f"continuity event store invalid: {reason}")

    projections = (
        projection_documents
        if projection_documents is not None
        else build_projection_documents(root)
    )
    if tuple(projections) != PROJECTION_IDS:
        raise HandoffError("projection id/order mismatch")

    latest_checkpoint_path = _latest_checkpoint_path(root)
    latest_event = read_event(latest_checkpoint_path)
    roadmap = _load_yaml(_require_regular_file(root, ROADMAP))
    dependency_registry = _load_yaml(_require_regular_file(root, DEPENDENCY_REGISTRY))
    contract = _load_yaml(_require_regular_file(root, CONTRACT))
    mission_rel = _mission_source(root)

    payload: dict[str, bytes] = {
        "AGENTS.md": _require_regular_file(root, AGENTS).read_bytes(),
        "coordination/bootstrap/START_HERE.md": _require_regular_file(
            root, BOOTSTRAP_START
        ).read_bytes(),
        "coordination/bootstrap/index_v0_1.yaml": _require_regular_file(
            root, BOOTSTRAP_INDEX
        ).read_bytes(),
        "project_mission.md": _require_regular_file(root, mission_rel).read_bytes(),
        "latest_checkpoint.yaml": latest_checkpoint_path.read_bytes(),
        "roadmap_slice.yaml": _yaml_bytes(_roadmap_slice(roadmap)),
        "execution_dependency_slice.yaml": _yaml_bytes(_dependency_slice(dependency_registry)),
        "UNKNOWNS.yaml": _yaml_bytes(_unknowns(latest_event)),
        "compiler/build_assistant_handoff_archive.py": Path(__file__).read_bytes(),
    }

    # Optional PROJECT_ONBOARD enrichment is explicit. Portable mode supplies none;
    # Blueprint-specific operator surfaces inject their canonical strategic sources.
    # CURRENT_WORKFRONT and SOURCE_STATE remain live in-memory projections below.
    effective_project_onboard_sources = project_onboard_sources

    if project_onboard_sources:
        effective_project_onboard_sources = tuple(
            dict.fromkeys(
                (
                    *project_onboard_sources,
                    *BOOTSTRAP_LIVING_PROJECT_ONBOARD_SOURCES,
                )
            )
        )

    for rel in effective_project_onboard_sources:
        payload[rel.as_posix()] = _require_regular_file(root, rel).read_bytes()

    for projection_id in PROJECTION_IDS:
        payload[f"{projection_id}.yaml"] = render_projection(projections[projection_id]).encode(
            "utf-8"
        )

    delta_material = bool(projections["UNRECONCILED_CURRENT_DELTA"]["payload"].get("material"))
    payload["knowledge_health.yaml"] = _yaml_bytes(
        _knowledge_health(
            latest_event,
            event_store_details=event_details,
            delta_material=delta_material,
        )
    )
    payload["00_READ_FIRST.md"] = _read_first(
        mission_source=mission_rel,
        latest_event=latest_event,
        projections=projections,
    )

    if len(payload) > MAX_PAYLOAD_FILES:
        raise HandoffError(f"payload file count exceeds {MAX_PAYLOAD_FILES}: {len(payload)}")
    total_bytes = sum(len(value) for value in payload.values())
    if total_bytes > MAX_PAYLOAD_BYTES:
        raise HandoffError(f"payload bytes exceed {MAX_PAYLOAD_BYTES}: {total_bytes}")

    for name in payload:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise HandoffError(f"unsafe archive entry: {name}")
        lowered = name.lower()
        if "chat" in lowered or "transcript" in lowered:
            raise HandoffError(f"chat/transcript entry forbidden: {name}")

    source_fingerprint = projections["SOURCE_STATE"]["payload"].get("current_fingerprint")
    if not isinstance(source_fingerprint, str):
        raise HandoffError("current source-state fingerprint missing")

    latest_event_sha256 = event_details.get("latest_event_sha256")
    if not isinstance(latest_event_sha256, str):
        raise HandoffError("latest event sha256 missing")

    included_hashes = {name: _sha256_bytes(payload[name]) for name in sorted(payload)}
    compiler_sha = sha256_file(Path(__file__))

    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "compiler_identity": COMPILER_ID,
        "compiler_version": COMPILER_VERSION,
        "compiler_sha256": compiler_sha,
        "continuity_contract_version": contract.get("schema_version"),
        "source_state_fingerprint": source_fingerprint,
        "latest_event_id": event_details.get("latest_event_id"),
        "latest_event_sha256": latest_event_sha256,
        "latest_checkpoint_id": event_details.get("latest_checkpoint_id"),
        "projection_basis_mode": "immutable_events_plus_current_working_tree",
        "unreconciled_current_delta_material": delta_material,
        "mission_source_path": mission_rel.as_posix(),
        "manifest_self_hash_excluded": True,
        "included_path_sha256": included_hashes,
        "payload_file_count_excluding_manifest": len(payload),
        "payload_bytes_excluding_manifest": total_bytes,
        "archive_determinism": {
            "entry_order": "lexicographic",
            "zip_compression": "stored",
            "zip_timestamp": "1980-01-01T00:00:00",
            "entry_mode": "0644",
        },
        "authority": "none",
        "chat_transcript_included": False,
    }
    payload["manifest.json"] = _json_bytes(manifest)
    return payload, manifest


def archive_bytes(payload: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer,
        "w",
        compression=zipfile.ZIP_STORED,
        strict_timestamps=True,
    ) as archive:
        for name in sorted(payload):
            info = zipfile.ZipInfo(name, FIXED_ZIP_DATE)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload[name])
    return buffer.getvalue()


def expected_archive(
    root: Path = ROOT,
    *,
    projection_documents: dict[str, dict[str, Any]] | None = None,
    project_onboard_sources: tuple[Path, ...] = (),
) -> tuple[bytes, dict[str, Any], str]:
    payload, manifest = build_payload(
        root,
        projection_documents=projection_documents,
        project_onboard_sources=project_onboard_sources,
    )
    blob = archive_bytes(payload)
    identity = (
        manifest["source_state_fingerprint"][:12] + "__" + manifest["latest_event_sha256"][:12]
    )
    name = f"forprint_assistant_handoff_v0_1__{identity}.zip"
    return blob, manifest, name


def validate_payload(
    payload: dict[str, bytes],
    manifest: dict[str, Any],
) -> None:
    required = {
        "00_READ_FIRST.md",
        "manifest.json",
        "AGENTS.md",
        "coordination/bootstrap/START_HERE.md",
        "coordination/bootstrap/index_v0_1.yaml",
        "project_mission.md",
        "latest_checkpoint.yaml",
        "CURRENT_WORKFRONT.yaml",
        "RECENT_ACTIVITY.yaml",
        "DECISIONS.yaml",
        "BLOCKERS.yaml",
        "NEXT_HORIZON.yaml",
        "SOURCE_STATE.yaml",
        "WORKER_PORTFOLIO.yaml",
        "UNRECONCILED_CURRENT_DELTA.yaml",
        "UNKNOWNS.yaml",
        "roadmap_slice.yaml",
        "execution_dependency_slice.yaml",
        "knowledge_health.yaml",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise HandoffError("handoff payload missing: " + ",".join(missing))

    expected_hashes = manifest.get("included_path_sha256")
    if not isinstance(expected_hashes, dict):
        raise HandoffError("manifest included_path_sha256 missing")
    actual_hashes = {
        name: _sha256_bytes(value) for name, value in payload.items() if name != "manifest.json"
    }
    if expected_hashes != dict(sorted(actual_hashes.items())):
        raise HandoffError("manifest included-path hashes mismatch")

    if manifest.get("chat_transcript_included") is not False:
        raise HandoffError("chat transcript inclusion boundary widened")
    if manifest.get("authority") != "none":
        raise HandoffError("handoff authority widened")


def verify_archive(
    path: Path,
    root: Path = ROOT,
    *,
    projection_documents: dict[str, dict[str, Any]] | None = None,
    project_onboard_sources: tuple[Path, ...] = (),
) -> None:
    expected_blob, expected_manifest, expected_name = expected_archive(
        root,
        projection_documents=projection_documents,
        project_onboard_sources=project_onboard_sources,
    )
    actual = path.read_bytes()
    if actual != expected_blob:
        raise HandoffError("archive bytes do not match current deterministic handoff")
    if path.name != expected_name:
        raise HandoffError(f"archive filename mismatch expected={expected_name}")

    with zipfile.ZipFile(io.BytesIO(actual), "r") as archive:
        names = archive.namelist()
        if names != sorted(names):
            raise HandoffError("archive entries are not lexicographic")
        payload = {name: archive.read(name) for name in names}
        manifest = json.loads(payload["manifest.json"])
        if manifest != expected_manifest:
            raise HandoffError("manifest mismatch")
        validate_payload(payload, manifest)


def _output_dir(root: Path) -> Path:
    return root.resolve() / "tmp/assistant_handoff"


def write_archive(
    root: Path = ROOT,
    *,
    projection_documents: dict[str, dict[str, Any]] | None = None,
    project_onboard_sources: tuple[Path, ...] = (),
) -> Path:
    root = root.resolve()
    blob, manifest, name = expected_archive(
        root,
        projection_documents=projection_documents,
        project_onboard_sources=project_onboard_sources,
    )
    payload, _manifest_again = build_payload(
        root,
        projection_documents=projection_documents,
        project_onboard_sources=project_onboard_sources,
    )
    validate_payload(payload, manifest)

    output_dir = _output_dir(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / name
    temporary = output_dir / f".{name}.{os.getpid()}.tmp"
    try:
        temporary.write_bytes(blob)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()

    verify_archive(
        target,
        root,
        projection_documents=projection_documents,
        project_onboard_sources=project_onboard_sources,
    )
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--verify-archive", type=Path, default=None)
    args = parser.parse_args()

    try:
        root = args.root.resolve()
        if args.verify_archive is not None:
            verify_archive(args.verify_archive.resolve(), root)
            print("ASSISTANT_HANDOFF_ARCHIVE_VERIFY=PASS")
            print(f"ARCHIVE={args.verify_archive.resolve()}")
            return 0

        payload, manifest = build_payload(root)
        validate_payload(
            {**payload, "manifest.json": _json_bytes(manifest)},
            manifest,
        )
        first = archive_bytes({**payload, "manifest.json": _json_bytes(manifest)})
        second = archive_bytes({**payload, "manifest.json": _json_bytes(manifest)})
        if first != second:
            raise HandoffError("archive rendering is non-deterministic")

        if args.validate_only:
            print("ASSISTANT_HANDOFF_COMPILER=PASS")
            print("VALIDATE_ONLY=true")
            print("MUTATION_PERFORMED=false")
            print("SOURCE_STATE_FINGERPRINT=" + manifest["source_state_fingerprint"])
            print(
                "UNRECONCILED_CURRENT_DELTA="
                + str(manifest["unreconciled_current_delta_material"]).lower()
            )
            print("PAYLOAD_FILE_COUNT=" + str(len(payload) + 1))
            return 0

        target = write_archive(root)
        print("ASSISTANT_HANDOFF_PACK=PASS")
        print(f"ARCHIVE={target}")
        print(f"ARCHIVE_SHA256={sha256_file(target)}")
        print("SOURCE_STATE_FINGERPRINT=" + manifest["source_state_fingerprint"])
        print(
            "UNRECONCILED_CURRENT_DELTA="
            + str(manifest["unreconciled_current_delta_material"]).lower()
        )
        print("PROJECT_SOURCE_MUTATION=false")
        print("AUTHORITY=none")
        return 0
    except (
        HandoffError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        yaml.YAMLError,
        zipfile.BadZipFile,
    ) as exc:
        print(f"ASSISTANT_HANDOFF_COMPILER=FAIL {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
