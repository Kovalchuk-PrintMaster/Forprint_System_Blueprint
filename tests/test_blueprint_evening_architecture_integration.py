import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_evening_architecture_front_door_and_matrix():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "BOOTSTRAP_WITHOUT_TASK" in agents
    assert "BOOTSTRAP_FOR_TASK" in agents
    matrix = yaml.safe_load(
        (
            ROOT
            / "coordination/roadmaps/details/forprint_system_blueprint/"
            "forprint_evening_architecture_action_matrix_v0_1.yaml"
        ).read_text(encoding="utf-8")
    )
    candidate = matrix["new_module_candidates"][0]
    assert candidate["module_id_candidate"] == "forprint_semantic_retrieval_service"
    assert candidate["status"] == "PROPOSED"


def test_process_revision_and_execution_lock_language_present():
    text = (
        ROOT
        / "coordination/standards/governance/"
        "assistant_bootstrap_governance_and_process_contract_direction_v0_1.md"
    ).read_text(encoding="utf-8")
    for token in ["ACTIVE", "SUPPORTED_LEGACY", "DEPRECATED", "BLOCKED", "REVOKED"]:
        assert token in text

    order = (
        ROOT
        / "coordination/roadmaps/details/forprint_system_blueprint/"
        "order_execution_job_ticket_stop_work_training_direction_v0_1.md"
    ).read_text(encoding="utf-8")
    assert "Hard execution lock" in order
    assert "QR" in order


def test_blueprint_indexes_are_fresh():
    py = ROOT / ".venv_blueprint/bin/python"
    for script in [
        "scripts/indexing/build_blueprint_index.py",
        "scripts/indexing/build_blueprint_knowledge_index.py",
        "scripts/indexing/build_blueprint_specialized_indexes.py",
    ]:
        cp = subprocess.run(
            [str(py), script, "--check"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert cp.returncode == 0, cp.stdout
