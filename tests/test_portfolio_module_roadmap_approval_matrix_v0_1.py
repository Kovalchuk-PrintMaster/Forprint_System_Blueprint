import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

def load(rel):
    with (ROOT / rel).open(encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_validator_passes():
    p = subprocess.run(
        [sys.executable, "scripts/validation/validate_portfolio_module_roadmap_approval_matrix_v0_1.py"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    assert p.returncode == 0, p.stdout

def test_distribution_is_closed():
    m = load("coordination/roadmaps/details/forprint_system_blueprint/portfolio_module_roadmap_approval_matrix_v0_1.yaml")
    assert m["distribution_gate"]["state"] == "CLOSED"
    assert m["distribution_gate"]["assistant_task_distribution_allowed"] is False

def test_every_canonical_module_matches_target_horizon():
    m = load("coordination/roadmaps/details/forprint_system_blueprint/portfolio_module_roadmap_approval_matrix_v0_1.yaml")
    t = load("coordination/roadmaps/details/forprint_system_blueprint/portfolio_full_horizon_target_states_v0_1.yaml")
    i = load("machine/module_identity_registry.yaml")

    assert set(m["modules"]) == set(i["canonical_module_ids"])
    assert set(t["modules"]) == set(i["canonical_module_ids"])

    for module_id in i["canonical_module_ids"]:
        steps = m["modules"][module_id]["steps"]
        target_steps = t["modules"][module_id]["full_horizon_steps"]

        assert len(steps) == len(target_steps)
        assert [x["sequence"] for x in steps] == list(
            range(1, len(steps) + 1)
        )
        assert [x["title"] for x in steps] == target_steps

def test_semantic_retrieval_is_review_only():
    m = load("coordination/roadmaps/details/forprint_system_blueprint/portfolio_module_roadmap_approval_matrix_v0_1.yaml")
    s = m["proposed_noncanonical_modules"]["forprint_semantic_retrieval_service"]
    assert s["identity_state"] == "PROPOSED_NONCANONICAL_REVIEW_ONLY"
    assert all(x["execution_authority"] is False for x in s["steps"])
