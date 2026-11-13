from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECON = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-09-23__blueprint__cf10_worker_delta_hardening_reconciliation_v0_1.yaml"
)
FRONT = (
    ROOT
    / "coordination/work_fronts/"
    "cf10_worker_delta_pipeline_completion_v0_1.yaml"
)
OLD_FRONT = (
    ROOT
    / "coordination/work_fronts/"
    "cf10_operator_status_surface_self_hardening_v0_1.yaml"
)

EXPECTED_OLD_FRONT_BLOB = "e2bf19dd967cd81177835eb33ef13fc11e6f9e0e"
EXPECTED_SEQUENCE = [
    "49c49b9569f647be41bd35c1c092505085a0f470",
    "a9042872d9667742dddea718dd2d625de2efaf7c",
    "a4606deaa895ea8953a3cdab676a6f802693fca8",
    "970d459956b8414d88294e3cf6a567c3701a9d47",
]
BASE = "cf4f1889f60951f868c85dec3890716ee9c2f091"

FORBIDDEN_SCOPE = {
    "coordination/repository_knowledge/roadmap_enrichment/source_map.yaml",
    "coordination/human_intent/modules/forprint_system_blueprint.yaml",
}


def _git(*args: str) -> str:
    import subprocess

    cp = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if cp.returncode != 0:
        raise RuntimeError(
            "git command failed: git "
            + " ".join(args)
            + "\n"
            + cp.stdout
        )
    return cp.stdout.strip()


def _load(path: Path) -> dict:
    import yaml

    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"YAML root must be mapping: {path}")
    return value


def main() -> int:
    recon = _load(RECON)
    front = _load(FRONT)

    if recon.get("schema_version") != (
        "forprint_cf10_worker_delta_hardening_reconciliation_v0_1"
    ):
        raise RuntimeError("unexpected reconciliation schema")
    metadata = recon.get("metadata") or {}
    if metadata.get("work_id") != "u180j":
        raise RuntimeError("reconciliation work_id mismatch")
    if metadata.get("step_id") != "CF-10":
        raise RuntimeError("reconciliation step_id mismatch")

    old_front_blob = _git("hash-object", str(OLD_FRONT.relative_to(ROOT)))
    if old_front_blob != EXPECTED_OLD_FRONT_BLOB:
        raise RuntimeError("original operator-status Work Front changed")

    ancestry = _git(
        "rev-list",
        "--reverse",
        f"{BASE}..{EXPECTED_SEQUENCE[-1]}",
    ).splitlines()
    if ancestry != EXPECTED_SEQUENCE:
        raise RuntimeError(
            "published hardening ancestry mismatch: " + repr(ancestry)
        )

    rows = recon.get("published_hardening_sequence", {}).get("commits")
    if not isinstance(rows, list):
        raise RuntimeError("published hardening commit rows missing")
    recorded = [row.get("commit") for row in rows if isinstance(row, dict)]
    if recorded != EXPECTED_SEQUENCE:
        raise RuntimeError("reconciliation commit sequence mismatch")

    decision = recon.get("governance_decision") or {}
    required_false = (
        "historical_implementation_reclassified_as_original_work_front_execution",
        "original_work_front_mutated",
        "retroactive_authority_granted",
        "a003_terminal_history_mutated",
    )
    for key in required_false:
        if decision.get(key) is not False:
            raise RuntimeError(f"retroactive governance widening: {key}")
    if decision.get("historical_implementation_recognized_as_repository_fact") is not True:
        raise RuntimeError("historical repository fact not recognized")
    if decision.get("future_cf10_control_plane_mutation_requires_prospective_front") is not True:
        raise RuntimeError("prospective Work Front requirement missing")

    if front.get("work_front_id") != (
        "wf-cf10-worker-delta-pipeline-completion-v0-1"
    ):
        raise RuntimeError("unexpected prospective Work Front ID")

    authority = front.get("authority") or {}
    required_false_authority = (
        "widening_requested",
        "retroactive_authority",
        "live_worker_dispatch_authorized",
        "lifecycle_mutation_authorized",
        "roadmap_mutation_authorized",
        "release_authorized",
        "merge_authorized",
        "automatic_accept_authorized",
    )
    for key in required_false_authority:
        if authority.get(key) is not False:
            raise RuntimeError(f"prospective Work Front authority widening: {key}")
    if authority.get("prospective_only") is not True:
        raise RuntimeError("prospective_only marker missing")

    scope = front.get("scope")
    if not isinstance(scope, list) or not all(isinstance(item, str) for item in scope):
        raise RuntimeError("prospective Work Front scope invalid")
    forbidden = sorted(FORBIDDEN_SCOPE & set(scope))
    if forbidden:
        raise RuntimeError("shared paths entered CF-10 scope: " + repr(forbidden))

    exclusions = front.get("exclusions")
    if not isinstance(exclusions, list):
        raise RuntimeError("prospective Work Front exclusions missing")
    exclusion_text = "\n".join(str(item) for item in exclusions)
    for forbidden_path in sorted(FORBIDDEN_SCOPE):
        if forbidden_path not in exclusion_text:
            raise RuntimeError(
                "shared path exclusion missing: " + forbidden_path
            )
    if "coordination/internal_work/blueprint/evening_reviews/" not in exclusion_text:
        raise RuntimeError("historical evening review exclusion missing")

    trigger = recon.get("trigger") or {}
    if trigger.get("historical_attempt_id") != "cf10-u180j-a003":
        raise RuntimeError("a003 reconciliation binding missing")
    if trigger.get("historical_terminal_result") != "FAILED":
        raise RuntimeError("a003 terminal result must remain FAILED")
    if trigger.get("rewrite_attempt_history") is not False:
        raise RuntimeError("a003 rewrite prohibition missing")

    boundaries = recon.get("boundaries") or {}
    for key in (
        "lifecycle_mutation_performed",
        "roadmap_mutation_performed",
        "dispatch_performed",
        "worker_launched",
        "attempt_ledger_appended",
        "release_performed",
        "merge_performed",
        "automatic_accept_performed",
        "cross_module_write_performed",
        "historical_files_rewritten",
    ):
        if boundaries.get(key) is not False:
            raise RuntimeError(f"reconciliation boundary widened: {key}")

    print("CF10_WORKER_DELTA_GOVERNANCE_RECONCILIATION_VALIDATION=PASS")
    print("WORK_ID=u180j")
    print("STEP_ID=CF-10")
    print("PUBLISHED_HARDENING_COMMIT_COUNT=4")
    print("ORIGINAL_WORK_FRONT_REWRITTEN=false")
    print("RETROACTIVE_AUTHORITY_GRANTED=false")
    print("A003_TERMINAL_HISTORY_REWRITTEN=false")
    print("PROSPECTIVE_WORK_FRONT=wf-cf10-worker-delta-pipeline-completion-v0-1")
    print("LIVE_WORKER_DISPATCH_AUTHORIZED=false")
    print("SHARED_HISTORICAL_PATHS_IN_SCOPE=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
