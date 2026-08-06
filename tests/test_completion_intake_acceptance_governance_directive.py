from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DIRECTIVE_ID = "2026-08-06__global__directive__completion-intake-and-acceptance-governance-v0-1"
DIRECTIVE = ROOT / "coordination/directives/global/planned/" / f"{DIRECTIVE_ID}.md"
INDEX = ROOT / "coordination/directives/global/index.yaml"
EVIDENCE = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    / "2026-08-06__blueprint__completion-intake-protocol-findings-v0-1.yaml"
)


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_completion_intake_directive_is_planned_not_released() -> None:
    index = load_yaml(INDEX)
    global_directives = index["global_directives"]
    planned = [row for row in global_directives["planned"] if row["directive_id"] == DIRECTIVE_ID]
    active = [row for row in global_directives["active"] if row["directive_id"] == DIRECTIVE_ID]
    assert len(planned) == 1
    assert active == []
    assert planned[0]["status"] == "planned"
    assert planned[0]["requires_acknowledgement"] is False
    assert planned[0]["activation_requires_separate_decision"] is True
    assert planned[0]["file"] == DIRECTIVE.relative_to(ROOT).as_posix()
    assert DIRECTIVE.is_file()


def test_completion_intake_directive_preserves_module_autonomy() -> None:
    content = DIRECTIVE.read_text(encoding="utf-8")
    required_fragments = (
        "Blueprint must not repair, rewrite or commit module-owned",
        "READY_FOR_OPERATOR_REVIEW",
        "HISTORICAL_EVIDENCE_UNRESOLVED",
        "supersedes_completion_id",
        "git rev-parse",
        "Blueprint must not perform the correction itself.",
        "external_rollout: gated",
    )
    for fragment in required_fragments:
        assert fragment in content


def test_completion_intake_findings_remain_rollout_gated() -> None:
    evidence = load_yaml(EVIDENCE)
    assert evidence["metadata"]["status"] == "documented_rollout_gated"
    assert evidence["observed_state"]["ready_for_operator_review"] == 0
    assert evidence["observed_state"]["processed_acceptance_records_found"] == 2
    assert evidence["governance_decisions"]["automatic_acceptance"] is False
    assert evidence["governance_decisions"]["automatic_return"] is False
    assert evidence["governance_decisions"]["directive_activation_authorized"] is False
    assert evidence["boundaries"]["module_repository_writes"] is False
    assert evidence["boundaries"]["external_prompts_released"] is False
