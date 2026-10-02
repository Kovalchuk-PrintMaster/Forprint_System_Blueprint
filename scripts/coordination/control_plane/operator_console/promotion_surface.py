from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.control_plane import candidate_promotion as promotion
from scripts.coordination.control_plane.operator_console.sealed_result import (
    SEALED_RESULT_SCHEMA,
)

PREVIEW_SCHEMA = "forprint_oc01_promotion_preview_v0_1"
CONTROL_RESULT_SCHEMA = "forprint_oc01_promotion_control_result_v0_1"
EXPLICIT_APPLY_TOKEN = "APPLY_EXACT_OC01_PROMOTION"


class PromotionSurfaceError(RuntimeError):
    pass


def _load_yaml(path: Path | str, label: str) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    if resolved.is_symlink():
        raise PromotionSurfaceError(f"{label} cannot be a symlink")
    if not resolved.is_file():
        raise PromotionSurfaceError(f"{label} missing: {resolved}")
    value = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PromotionSurfaceError(f"{label} must be a mapping")
    return value


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_immutable_yaml(path: Path | str, payload: Mapping[str, Any]) -> Path:
    resolved = Path(path).expanduser().resolve()
    if resolved.exists() or resolved.is_symlink():
        raise PromotionSurfaceError(f"refusing to overwrite evidence: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        yaml.safe_dump(
            dict(payload),
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )
    return resolved


def _assert_outside_canonical(
    *,
    root: Path | str,
    path: Path | str,
    label: str,
) -> None:
    canonical = Path(root).expanduser().resolve()
    resolved = Path(path).expanduser().resolve()
    if resolved == canonical or canonical in resolved.parents:
        raise PromotionSurfaceError(
            f"{label} must remain outside the canonical repository"
        )


def _validate_sealed_result(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema_version") != SEALED_RESULT_SCHEMA:
        raise PromotionSurfaceError("sealed result schema mismatch")
    if value.get("state") != "SEALED":
        raise PromotionSurfaceError("sealed result state is not SEALED")

    expected_hash = value.get("package_sha256")
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise PromotionSurfaceError("sealed result package_sha256 missing")

    core = dict(value)
    core.pop("package_sha256", None)
    if _canonical_sha256(core) != expected_hash:
        raise PromotionSurfaceError("sealed result package hash mismatch")

    attempt_id = value.get("attempt_id")
    if not isinstance(attempt_id, str) or not attempt_id:
        raise PromotionSurfaceError("sealed result attempt_id missing")

    source_head = value.get("base_head")
    if not isinstance(source_head, str) or len(source_head) != 40:
        raise PromotionSurfaceError("sealed result base_head invalid")

    try:
        changed_paths = promotion.normalize_changed_paths(
            value.get("changed_paths") or []
        )
        recommended = promotion.normalize_changed_paths(
            value.get("recommended_canonical_write_set") or []
        )
    except promotion.CandidatePromotionError as exc:
        raise PromotionSurfaceError(str(exc)) from exc

    if changed_paths != recommended:
        raise PromotionSurfaceError(
            "sealed result changed paths do not equal recommended canonical write-set"
        )

    authority = value.get("authority")
    if not isinstance(authority, dict):
        raise PromotionSurfaceError("sealed result authority missing")
    for key in (
        "canonical_write_authority",
        "promotion_authority",
        "remote_push_authority",
        "merge_authority",
        "release_authority",
    ):
        if authority.get(key) is not False:
            raise PromotionSurfaceError(
                f"sealed result authority widened: {key}"
            )

    actions = value.get("actions_performed")
    if not isinstance(actions, dict):
        raise PromotionSurfaceError("sealed result actions_performed missing")
    for key in (
        "canonical_write",
        "promotion",
        "remote_push",
        "merge",
        "release",
    ):
        if actions.get(key) is not False:
            raise PromotionSurfaceError(
                f"sealed result already performed forbidden action: {key}"
            )

    result = dict(value)
    result["changed_paths"] = changed_paths
    result["recommended_canonical_write_set"] = recommended
    return result


def _validate_roots(
    *,
    root: Path | str,
    candidate_root: Path | str,
) -> tuple[Path, Path]:
    canonical = Path(root).expanduser().resolve()
    candidate = Path(candidate_root).expanduser().resolve()
    if not canonical.is_dir():
        raise PromotionSurfaceError("canonical repository is missing")
    if not candidate.is_dir():
        raise PromotionSurfaceError("candidate root is missing")
    if candidate == canonical:
        raise PromotionSurfaceError("candidate root cannot equal canonical repository")
    return canonical, candidate


def _build_shared_plan(
    *,
    root: Path | str,
    candidate_root: Path | str,
    sealed_result: dict[str, Any],
    work_front: dict[str, Any],
    origin_handoff_manifest: dict[str, Any],
    handoff_result: dict[str, Any],
    expected_profile_ref: str,
    expected_procedure_id: str,
    operator_review: bool,
) -> dict[str, Any]:
    canonical, candidate = _validate_roots(
        root=root,
        candidate_root=candidate_root,
    )

    if handoff_result.get("attempt_id") != sealed_result["attempt_id"]:
        raise PromotionSurfaceError(
            "sealed result and Handoff result attempt_id mismatch"
        )

    try:
        handoff_paths = promotion.normalize_changed_paths(
            handoff_result.get("changed_paths") or []
        )
    except promotion.CandidatePromotionError as exc:
        raise PromotionSurfaceError(str(exc)) from exc

    if handoff_paths != sealed_result["changed_paths"]:
        raise PromotionSurfaceError(
            "sealed result and Handoff result changed_paths mismatch"
        )

    try:
        return promotion.build_candidate_promotion_plan(
            root=canonical,
            candidate_root=candidate,
            source_head=sealed_result["base_head"],
            attempt_id=sealed_result["attempt_id"],
            changed_paths=sealed_result["changed_paths"],
            work_front=work_front,
            origin_handoff_manifest=origin_handoff_manifest,
            handoff_result=handoff_result,
            expected_profile_ref=expected_profile_ref,
            expected_procedure_id=expected_procedure_id,
            operator_review=operator_review,
        )
    except promotion.CandidatePromotionError as exc:
        raise PromotionSurfaceError(str(exc)) from exc


def build_promotion_preview(
    *,
    root: Path | str,
    candidate_root: Path | str,
    sealed_result_path: Path | str,
    work_front_path: Path | str,
    origin_handoff_manifest_path: Path | str,
    handoff_result_path: Path | str,
    expected_profile_ref: str,
    expected_procedure_id: str,
    operator_review: bool,
) -> dict[str, Any]:
    canonical, candidate = _validate_roots(
        root=root,
        candidate_root=candidate_root,
    )
    sealed_path = Path(sealed_result_path).expanduser().resolve()
    work_front_resolved = Path(work_front_path).expanduser().resolve()
    origin_resolved = Path(origin_handoff_manifest_path).expanduser().resolve()
    handoff_resolved = Path(handoff_result_path).expanduser().resolve()

    sealed = _validate_sealed_result(
        _load_yaml(sealed_path, "sealed result")
    )
    work_front = _load_yaml(work_front_resolved, "Work Front")
    origin = _load_yaml(origin_resolved, "origin Handoff manifest")
    handoff = _load_yaml(handoff_resolved, "Handoff result")

    plan = _build_shared_plan(
        root=canonical,
        candidate_root=candidate,
        sealed_result=sealed,
        work_front=work_front,
        origin_handoff_manifest=origin,
        handoff_result=handoff,
        expected_profile_ref=expected_profile_ref,
        expected_procedure_id=expected_procedure_id,
        operator_review=operator_review,
    )
    plan_sha = _canonical_sha256(plan)

    preview: dict[str, Any] = {
        "schema_version": PREVIEW_SCHEMA,
        "state": "PREVIEW_READY",
        "canonical_root": str(canonical),
        "candidate_root": str(candidate),
        "attempt_id": sealed["attempt_id"],
        "source_head": sealed["base_head"],
        "changed_paths": sealed["changed_paths"],
        "sealed_result": {
            "path": str(sealed_path),
            "package_sha256": sealed["package_sha256"],
        },
        "source_inputs": {
            "work_front_path": str(work_front_resolved),
            "origin_handoff_manifest_path": str(origin_resolved),
            "handoff_result_path": str(handoff_resolved),
            "expected_profile_ref": expected_profile_ref,
            "expected_procedure_id": expected_procedure_id,
        },
        "shared_promotion_plan": plan,
        "shared_promotion_plan_sha256": plan_sha,
        "authorization": {
            "apply_requires_explicit_authorization": True,
            "apply_token_literal": EXPLICIT_APPLY_TOKEN,
            "exact_preview_sha256_required": True,
        },
        "authority": {
            "console_is_state_authority": False,
            "promotion_authority": "OPERATOR_CONTROLLED_CF10",
            "commit_authority": False,
            "push_authority": False,
            "merge_authority": False,
            "release_authority": False,
        },
        "actions_performed": {
            "canonical_write": False,
            "staging": False,
            "commit": False,
            "push": False,
            "merge": False,
            "release": False,
        },
    }
    preview["preview_sha256"] = _canonical_sha256(preview)
    return preview


def write_promotion_preview(
    *,
    output_path: Path | str,
    **kwargs: Any,
) -> dict[str, Any]:
    root = kwargs.get("root")
    if root is None:
        raise PromotionSurfaceError("root is required")
    _assert_outside_canonical(
        root=root,
        path=output_path,
        label="promotion preview",
    )
    preview = build_promotion_preview(**kwargs)
    resolved = _write_immutable_yaml(output_path, preview)
    result = dict(preview)
    result["preview_path"] = str(resolved)
    return result


def _validate_preview(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema_version") != PREVIEW_SCHEMA:
        raise PromotionSurfaceError("promotion preview schema mismatch")
    if value.get("state") != "PREVIEW_READY":
        raise PromotionSurfaceError("promotion preview state is not PREVIEW_READY")

    expected = value.get("preview_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise PromotionSurfaceError("promotion preview sha256 missing")
    core = dict(value)
    core.pop("preview_sha256", None)
    if _canonical_sha256(core) != expected:
        raise PromotionSurfaceError("promotion preview hash mismatch")
    return value


def apply_promotion_from_preview(
    *,
    preview_path: Path | str,
    root: Path | str,
    candidate_root: Path | str,
    recovery_root: Path | str,
    evidence_path: Path | str,
    explicit_authorization: str,
    expected_preview_sha256: str,
    post_apply_validator: Callable[
        [list[str]], bool | dict[str, Any]
    ] | None = None,
) -> dict[str, Any]:
    preview_resolved = Path(preview_path).expanduser().resolve()
    preview = _validate_preview(
        _load_yaml(preview_resolved, "promotion preview")
    )

    if explicit_authorization != EXPLICIT_APPLY_TOKEN:
        raise PromotionSurfaceError("explicit promotion authorization token mismatch")
    if expected_preview_sha256 != preview["preview_sha256"]:
        raise PromotionSurfaceError("expected preview sha256 mismatch")

    canonical, candidate = _validate_roots(
        root=root,
        candidate_root=candidate_root,
    )
    if str(canonical) != preview.get("canonical_root"):
        raise PromotionSurfaceError("canonical root differs from promotion preview")
    if str(candidate) != preview.get("candidate_root"):
        raise PromotionSurfaceError("candidate root differs from promotion preview")

    _assert_outside_canonical(
        root=canonical,
        path=recovery_root,
        label="promotion recovery root",
    )
    _assert_outside_canonical(
        root=canonical,
        path=evidence_path,
        label="promotion evidence",
    )

    sources = preview.get("source_inputs")
    if not isinstance(sources, dict):
        raise PromotionSurfaceError("promotion preview source_inputs missing")

    sealed = _validate_sealed_result(
        _load_yaml(
            preview["sealed_result"]["path"],
            "sealed result",
        )
    )
    work_front = _load_yaml(
        sources["work_front_path"],
        "Work Front",
    )
    origin = _load_yaml(
        sources["origin_handoff_manifest_path"],
        "origin Handoff manifest",
    )
    handoff = _load_yaml(
        sources["handoff_result_path"],
        "Handoff result",
    )

    fresh_plan = _build_shared_plan(
        root=canonical,
        candidate_root=candidate,
        sealed_result=sealed,
        work_front=work_front,
        origin_handoff_manifest=origin,
        handoff_result=handoff,
        expected_profile_ref=str(sources["expected_profile_ref"]),
        expected_procedure_id=str(sources["expected_procedure_id"]),
        operator_review=True,
    )
    fresh_sha = _canonical_sha256(fresh_plan)

    if fresh_sha != preview.get("shared_promotion_plan_sha256"):
        raise PromotionSurfaceError(
            "shared promotion plan changed since preview; rebuild preview"
        )
    if fresh_plan != preview.get("shared_promotion_plan"):
        raise PromotionSurfaceError(
            "shared promotion plan payload changed since preview"
        )

    try:
        shared_result = promotion.apply_candidate_promotion(
            plan=fresh_plan,
            root=canonical,
            candidate_root=candidate,
            recovery_root=recovery_root,
            evidence_path=evidence_path,
            post_apply_validator=post_apply_validator,
        )
    except promotion.CandidatePromotionError as exc:
        raise PromotionSurfaceError(str(exc)) from exc

    return {
        "schema_version": CONTROL_RESULT_SCHEMA,
        "state": "PROMOTION_APPLIED_BY_SHARED_CF10_ENGINE",
        "preview_path": str(preview_resolved),
        "preview_sha256": preview["preview_sha256"],
        "explicit_authorization_accepted": True,
        "shared_result": shared_result,
        "authority": {
            "console_is_state_authority": False,
            "promotion_authority": "OPERATOR_CONTROLLED_CF10",
            "commit_authority": False,
            "push_authority": False,
            "merge_authority": False,
            "release_authority": False,
        },
        "actions_performed_by_surface": {
            "planning_engine_reimplemented": False,
            "promotion_engine_reimplemented": False,
            "staging": False,
            "commit": False,
            "push": False,
            "merge": False,
            "release": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OC-01 MINI-5 sandbox-to-canonical promotion surface"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    preview = sub.add_parser("preview")
    preview.add_argument("--root", required=True)
    preview.add_argument("--candidate-root", required=True)
    preview.add_argument("--sealed-result", required=True)
    preview.add_argument("--work-front", required=True)
    preview.add_argument("--origin-handoff-manifest", required=True)
    preview.add_argument("--handoff-result", required=True)
    preview.add_argument("--expected-profile-ref", required=True)
    preview.add_argument("--expected-procedure-id", required=True)
    preview.add_argument("--output", required=True)
    preview.add_argument("--operator-review", action="store_true")

    apply_cmd = sub.add_parser("apply")
    apply_cmd.add_argument("--preview", required=True)
    apply_cmd.add_argument("--root", required=True)
    apply_cmd.add_argument("--candidate-root", required=True)
    apply_cmd.add_argument("--recovery-root", required=True)
    apply_cmd.add_argument("--evidence", required=True)
    apply_cmd.add_argument("--authorization", required=True)
    apply_cmd.add_argument("--expected-preview-sha256", required=True)

    args = parser.parse_args()

    if args.command == "preview":
        result = write_promotion_preview(
            output_path=args.output,
            root=args.root,
            candidate_root=args.candidate_root,
            sealed_result_path=args.sealed_result,
            work_front_path=args.work_front,
            origin_handoff_manifest_path=args.origin_handoff_manifest,
            handoff_result_path=args.handoff_result,
            expected_profile_ref=args.expected_profile_ref,
            expected_procedure_id=args.expected_procedure_id,
            operator_review=args.operator_review,
        )
    else:
        result = apply_promotion_from_preview(
            preview_path=args.preview,
            root=args.root,
            candidate_root=args.candidate_root,
            recovery_root=args.recovery_root,
            evidence_path=args.evidence,
            explicit_authorization=args.authorization,
            expected_preview_sha256=args.expected_preview_sha256,
        )

    print(
        yaml.safe_dump(
            result,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ).rstrip()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
