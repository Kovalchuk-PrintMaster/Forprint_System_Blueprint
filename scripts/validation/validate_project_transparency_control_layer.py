#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

DEFAULT_RENDERER = Path(
    "scripts/coordination/"
    "render_blueprint_governance_status.py"
)
EXPECTED_SCHEMA = (
    "project_transparency_current_state_manifest_v0_1"
)
EXPECTED_CHECK_ID = (
    "project_transparency_control_layer_validation"
)


def load_renderer(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "blueprint_governance_status_renderer_for_validation",
        path,
    )
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load renderer: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def tracked_status(root: Path) -> str:
    result = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=no",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(
            "Could not inspect tracked repository status: "
            f"{result.stdout}"
        )
    return result.stdout


def validate(
    root: Path,
    renderer_path: Path,
) -> list[str]:
    issues: list[str] = []
    renderer = load_renderer(renderer_path)

    try:
        manifest = renderer.build_manifest(root)
    except Exception as error:
        return [f"manifest build failed closed: {error}"]

    if manifest.get("schema_version") != EXPECTED_SCHEMA:
        issues.append("manifest schema version is invalid")

    projection = manifest.get("projection")
    if not isinstance(projection, dict):
        issues.append("projection section must be a mapping")
    else:
        expected_projection = {
            "role": "current_state_projection",
            "independent_authority": False,
            "historical_evidence_rewritten": False,
            "pilot_authorization_effect": "none",
            "release_policy_effect": "none",
        }
        for key, expected in expected_projection.items():
            if projection.get(key) != expected:
                issues.append(
                    f"projection.{key} must be {expected!r}"
                )

    release = manifest.get("current_release_authority")
    if not isinstance(release, dict):
        issues.append("current_release_authority must be a mapping")
    else:
        expected_release = {
            "source": "coordination/releases/current.yaml",
            "schema_version": "forprint_current_release_projection_v0_1",
            "status": "authoritative_current",
            "base_release": "v0.4",
            "base_release_state": "PROMOTED_CLOSED_SEALED",
            "hardening_release": "v0.4.1",
            "hardening_state": "ACTIVE_CURRENT",
        }
        for key, expected in expected_release.items():
            if release.get(key) != expected:
                issues.append(
                    f"current_release_authority.{key} must be {expected!r}"
                )

        legacy = release.get("legacy_compatibility")
        if not isinstance(legacy, dict):
            issues.append(
                "current_release_authority.legacy_compatibility must be a mapping"
            )
        else:
            if legacy.get("visibility") != "advisory_yellow":
                issues.append(
                    "legacy compatibility visibility must be advisory_yellow"
                )
            if legacy.get("current_gate") != "nonblocking":
                issues.append(
                    "legacy compatibility current gate must be nonblocking"
                )
            if legacy.get("current_runtime_dependency_allowed") is not False:
                issues.append(
                    "current runtime must not depend on legacy compatibility"
                )

    consistency = manifest.get("source_consistency")
    if not isinstance(consistency, dict):
        issues.append("source_consistency must be a mapping")
    elif consistency.get("state") != "agreed":
        issues.append(
            "authoritative sources disagree: "
            f"{consistency.get('disagreements')!r}"
        )

    authorization = manifest.get("authorization_evidence")
    if not isinstance(authorization, dict):
        issues.append("authorization_evidence must be a mapping")
    else:
        expected_authorization = {
            "reference_pilot_authorized": False,
            "external_prompts_released": False,
            "external_rollout": "gated",
            "release_policy_global_enabled": False,
            "authorized_modules": [],
            "release_authorization_evidence": None,
        }
        for key, expected in expected_authorization.items():
            if authorization.get(key) != expected:
                issues.append(
                    f"authorization_evidence.{key} "
                    f"must be {expected!r}"
                )

    boundaries = manifest.get("boundaries")
    if not isinstance(boundaries, dict):
        issues.append("boundaries must be a mapping")
    else:
        required_false = (
            "tracked_writes",
            "git_mutations",
            "pilot_authorized_by_rendering",
            "release_policy_changed_by_rendering",
            "historical_evidence_rewritten",
            "external_rollout_authorized",
        )
        if boundaries.get("read_only_projection") is not True:
            issues.append("read_only_projection must be true")
        for key in required_false:
            if boundaries.get(key) is not False:
                issues.append(f"boundaries.{key} must be false")

    coordination = manifest.get("coordination_control_state")
    if not isinstance(coordination, dict):
        issues.append(
            "coordination_control_state must be a mapping"
        )
    else:
        plan = coordination.get("ten_step_forward_plan")
        if not isinstance(plan, list) or len(plan) != 10:
            issues.append("ten-step forward plan must contain 10 rows")
        else:
            expected_steps = list(range(1, 11))
            if [row.get("step") for row in plan] != expected_steps:
                issues.append(
                    "ten-step forward plan order is invalid"
                )
            if [row.get("status") for row in plan[:4]] != [
                "completed",
                "completed",
                "completed",
                "completed",
            ]:
                issues.append(
                    "control-layer steps 1-4 must be completed"
                )
            if plan[4].get("action") != (
                "define_reference_pilot_authorization_criteria"
            ):
                issues.append(
                    "step 5 must define pilot authorization criteria"
                )
        if coordination.get("authority") != (
            "coordination_proposal"
        ):
            issues.append(
                "coordination control must remain a proposal"
            )
        if coordination.get("authorization_effect") != "none":
            issues.append(
                "coordination control must not authorize pilot"
            )

    checks = manifest.get("canonical_checks")
    if not isinstance(checks, dict):
        issues.append("canonical_checks must be a mapping")
    else:
        count = checks.get("count")
        unique_count = checks.get("unique_count")
        if not isinstance(count, int) or count <= 0:
            issues.append(
                "canonical check count must be positive"
            )
        if unique_count != count:
            issues.append(
                "canonical check IDs must be unique"
            )
        check_ids = checks.get("check_ids")
        if (
            not isinstance(check_ids, list)
            or check_ids.count(EXPECTED_CHECK_ID) != 1
        ):
            issues.append(
                "transparency validator must occur exactly once "
                "in the canonical catalog"
            )
        if checks.get("historical_evidence_immutable") is not True:
            issues.append(
                "historical canonical evidence must remain immutable"
            )

    source_files = manifest.get("source_files")
    if not isinstance(source_files, dict):
        issues.append("source_files must be a mapping")
    else:
        for path, record in source_files.items():
            if not isinstance(path, str) or not isinstance(
                record,
                dict,
            ):
                issues.append("source file record is malformed")
                continue
            digest = record.get("sha256")
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(
                    character not in "0123456789abcdef"
                    for character in digest
                )
            ):
                issues.append(
                    f"source hash is invalid for {path}"
                )

    try:
        rendered = renderer.render_status(manifest)
    except Exception as error:
        issues.append(f"status render failed: {error}")
        rendered = ""

    required_fragments = (
        "ForPrint Blueprint Governance Status",
        "Current release authority",
        "base release: v0.4 PROMOTED_CLOSED_SEALED",
        "hardening release: v0.4.1 ACTIVE_CURRENT",
        "legacy compatibility: advisory / nonblocking",
        "Observed governance decision state",
        "Coordination control state",
        "Authorization boundaries",
        "reference pilot authorized: false",
        "external prompts released: false",
        "external rollout: gated",
        "Canonical checks",
        "Migration dependency chain",
        "Ten-step forward plan",
        "Source consistency",
        "state: agreed",
    )
    for fragment in required_fragments:
        if fragment not in rendered:
            issues.append(
                f"rendered status lacks required fragment: "
                f"{fragment!r}"
            )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the read-only project transparency "
            "control layer."
        )
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--renderer",
        default=DEFAULT_RENDERER.as_posix(),
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    renderer_path = Path(args.renderer)
    if not renderer_path.is_absolute():
        renderer_path = root / renderer_path

    try:
        before = tracked_status(root)
        issues = validate(root, renderer_path)
        after = tracked_status(root)
    except Exception as error:
        print(f"FAILED: {error}")
        print(
            "RESULT: "
            "PROJECT_TRANSPARENCY_CONTROL_LAYER_VALIDATION_FAILED"
        )
        return 1

    if before != after:
        issues.append(
            "validation changed tracked repository state"
        )

    if issues:
        print("Project transparency control-layer validation failed:")
        for item in issues:
            print(f"- {item}")
        print(
            "RESULT: "
            "PROJECT_TRANSPARENCY_CONTROL_LAYER_VALIDATION_FAILED"
        )
        return 1

    print(
        "Project transparency control-layer validation passed."
    )
    print("Canonical check catalog: consistent")
    print("Source consistency: agreed")
    print("Reference pilot authorized: false")
    print("External prompts released: false")
    print("External rollout: gated")
    print("Tracked writes: false")
    print(
        "RESULT: "
        "PROJECT_TRANSPARENCY_CONTROL_LAYER_VALIDATION_READY"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
