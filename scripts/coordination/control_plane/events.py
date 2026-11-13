from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

Q5_REQUIRED_FIELDS = frozenset(
    {
        "event_id",
        "event_type",
        "occurred_at",
        "producer",
        "target",
        "module_id",
        "prompt_id",
        "roadmap_step_id",
        "correlation_id",
        "causation_id",
        "severity",
        "blocking",
        "schema_version",
        "payload",
        "evidence_refs",
        "idempotency_key",
    }
)
Q5_ALLOWED_FAMILIES = frozenset(
    {
        "claim_status",
        "clarification",
        "answer_resolution",
        "execution_blocker",
        "unable_to_execute",
        "operator_attention",
        "operator_decision",
        "completion_publication",
    }
)


@dataclass(frozen=True)
class EventScanResult:
    cursor: dict[str, Any]
    observations: tuple[dict[str, Any], ...]
    invalid_files: tuple[str, ...]


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(path: Path) -> dict[str, Any] | None:
    try:
        data = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.suffix.lower() == ".json"
            else yaml.safe_load(path.read_text(encoding="utf-8"))
        )
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def validate_q5_event_envelope(event: dict[str, Any]) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    actual = set(event)
    if actual != Q5_REQUIRED_FIELDS:
        if Q5_REQUIRED_FIELDS - actual:
            errors.append("missing_fields")
        if actual - Q5_REQUIRED_FIELDS:
            errors.append("unknown_fields")
    event_type = event.get("event_type")
    if not isinstance(event_type, str) or "." not in event_type:
        errors.append("event_type_invalid")
    else:
        family, action = event_type.split(".", 1)
        if family not in Q5_ALLOWED_FAMILIES:
            errors.append("event_family_not_in_q5_v0_1")
        if not family or not action:
            errors.append("event_type_format_invalid")
    if not isinstance(event.get("blocking"), bool):
        errors.append("blocking_not_boolean")
    if not isinstance(event.get("payload"), dict):
        errors.append("payload_not_mapping")
    if not isinstance(event.get("evidence_refs"), list):
        errors.append("evidence_refs_not_list")
    return not errors, tuple(sorted(set(errors)))


def scan_event_roots(*, event_roots: list[Path], cursor_id: str) -> EventScanResult:
    observations: list[dict[str, Any]] = []
    invalid: list[str] = []
    fingerprints: dict[str, str] = {}
    candidates: list[Path] = []
    for root in event_roots:
        root = root.resolve()
        if not root.exists():
            continue
        if root.is_file():
            candidates.append(root)
        else:
            candidates.extend(
                p
                for p in root.rglob("*")
                if p.is_file() and p.suffix.lower() in {".yaml", ".yml", ".json"}
            )
    for path in sorted(set(candidates), key=str):
        data = _load(path)
        fingerprints[str(path)] = _sha(path)
        if data is None:
            invalid.append(str(path))
            continue
        if set(data) != Q5_REQUIRED_FIELDS:
            continue
        valid, _ = validate_q5_event_envelope(data)
        if not valid:
            invalid.append(str(path))
            continue
        observations.append(
            {
                "event_id": data["event_id"],
                "event_type": data["event_type"],
                "idempotency_key": data["idempotency_key"],
                "module_id": data["module_id"],
                "prompt_id": data["prompt_id"],
                "blocking": data["blocking"],
                "source_path": str(path),
                "source_sha256": fingerprints[str(path)],
            }
        )
    material = {
        "cursor_id": cursor_id,
        "source_fingerprints": fingerprints,
        "event_keys": sorted(o["idempotency_key"] for o in observations),
    }
    fp = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    cursor = {
        "schema_version": "forprint_control_plane_event_cursor_v0_1",
        "cursor_id": cursor_id,
        "cursor_fingerprint_sha256": fp,
        "source_fingerprints": fingerprints,
        "observed_event_count": len(observations),
        "invalid_event_file_count": len(invalid),
        "ordering_authority": "IDENTITY_AND_PREDECESSOR_NOT_FILESYSTEM_TIMESTAMP",
        "q5_unknown_event_family_emission_allowed": False,
    }
    return EventScanResult(cursor, tuple(observations), tuple(sorted(invalid)))
