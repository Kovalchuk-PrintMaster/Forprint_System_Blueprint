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


def load(path: Path) -> dict:
    import yaml

    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def git(*args: str) -> str:
    import subprocess

    cp = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    return cp.stdout.strip()


def test_reconciliation_preserves_original_work_front_and_a003_history() -> None:
    recon = load(RECON)
    assert git("hash-object", str(OLD_FRONT.relative_to(ROOT))) == (
        "e2bf19dd967cd81177835eb33ef13fc11e6f9e0e"
    )
    assert recon["original_work_front"]["rewritten_by_this_reconciliation"] is False
    assert recon["trigger"]["historical_attempt_id"] == "cf10-u180j-a003"
    assert recon["trigger"]["historical_terminal_result"] == "FAILED"
    assert recon["trigger"]["rewrite_attempt_history"] is False


def test_published_hardening_sequence_is_exact_git_ancestry() -> None:
    expected = [
        "49c49b9569f647be41bd35c1c092505085a0f470",
        "a9042872d9667742dddea718dd2d625de2efaf7c",
        "a4606deaa895ea8953a3cdab676a6f802693fca8",
        "970d459956b8414d88294e3cf6a567c3701a9d47",
    ]
    actual = git(
        "rev-list",
        "--reverse",
        "cf4f1889f60951f868c85dec3890716ee9c2f091.."
        "970d459956b8414d88294e3cf6a567c3701a9d47",
    ).splitlines()
    assert actual == expected

    recon = load(RECON)
    recorded = [
        row["commit"]
        for row in recon["published_hardening_sequence"]["commits"]
    ]
    assert recorded == expected


def test_reconciliation_never_claims_retroactive_authority() -> None:
    decision = load(RECON)["governance_decision"]
    assert (
        decision[
            "historical_implementation_recognized_as_repository_fact"
        ]
        is True
    )
    assert (
        decision[
            "historical_implementation_reclassified_as_original_work_front_execution"
        ]
        is False
    )
    assert decision["retroactive_authority_granted"] is False
    assert decision["original_work_front_mutated"] is False


def test_prospective_front_is_bounded_and_excludes_parallel_historical_work() -> None:
    front = load(FRONT)
    authority = front["authority"]
    assert authority["prospective_only"] is True
    assert authority["retroactive_authority"] is False
    assert authority["live_worker_dispatch_authorized"] is False
    assert authority["lifecycle_mutation_authorized"] is False
    assert authority["roadmap_mutation_authorized"] is False
    assert authority["automatic_accept_authorized"] is False

    scope = set(front["scope"])
    assert (
        "coordination/repository_knowledge/roadmap_enrichment/source_map.yaml"
        not in scope
    )
    assert (
        "coordination/human_intent/modules/forprint_system_blueprint.yaml"
        not in scope
    )

    exclusions = "\n".join(front["exclusions"])
    assert "coordination/internal_work/blueprint/evening_reviews/" in exclusions
    assert (
        "coordination/repository_knowledge/roadmap_enrichment/source_map.yaml"
        in exclusions
    )
    assert (
        "coordination/human_intent/modules/forprint_system_blueprint.yaml"
        in exclusions
    )


def test_reconciliation_slice_has_no_live_authority_mutation() -> None:
    boundaries = load(RECON)["boundaries"]
    assert all(value is False for value in boundaries.values())
