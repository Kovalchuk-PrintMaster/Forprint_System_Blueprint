"""r044 is a design review ONLY: positive inspect cannot release a Worker."""
import ast
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane import cf10_single_owner_pilot_review_v0_1 as r044

ROOT = Path(__file__).resolve().parents[3]


def contract():
    return yaml.safe_load((ROOT / r044.POLICY).read_text(encoding="utf-8"))


def source_fixture():
    return {name: "\n".join(tokens) for name, tokens in r044.SOURCES.items()}


def test_valid_source_is_not_authorization():
    r = r044.inspect(ROOT, source_text=source_fixture(), doc=contract())
    assert r["status"] == "OWNER_SELECTED_DESIGN_RELEASE_BLOCKED"
    assert not r["blockers"]
    assert r["authority_granted"] is False and r["production_cutover"] is False
    assert r["worker_launched"] is False and r["operator_claim_consumed"] is False
    assert "IMPLEMENT_SEPARATE_BOUNDED_PILOT_ADMISSION" in r["next_action"]


@pytest.mark.parametrize("section,key,value", [
    ("scope", "worker_id", "worker-02"),
    ("scope", "attempt", "REUSE_OLD_ATTEMPT"),
    ("scope", "first_live_task_family", "Task80"),
    ("scope", "simultaneous_writable_workers_max", 2),
    ("scope", "simultaneous_writable_workers_max", True),
    ("scope", "broader_modules_allowed", True),
    ("scope", "automatic_next_task", True),
    ("operator_authentication", "method", "NO_PASSWORD"),
    ("operator_authentication", "reusable_signing_lease_required", True),
    ("operator_authentication", "operator_password_stored", True),
    ("operator_authentication", "owner_decision_substitutes_independent_human_signer_for_bounded_pilot_only", False),
    ("historical_conflict", "reconciliation_required", False),
    ("historical_conflict", "legacy_live_release_must_remain_unchanged_until_separate_cutover", False),
    ("live_cutover", "granted_by_this_design", True),
    ("live_cutover", "make_quarantine_must_remain", False),
    ("live_cutover", "systemd_live_cutover_must_remain_disabled", False),
    ("live_cutover", "no_automatic_worker_retry", False),
    ("live_cutover", "no_automatic_acceptance", False),
    ("live_cutover", "no_automatic_publication", False),
])
def test_widening_is_denied(section, key, value):
    doc = contract()
    doc[section][key] = value
    assert r044.validate_contract(doc)
    report = r044.inspect(ROOT, source_text=source_fixture(), doc=doc)
    assert report["authority_granted"] is False
    assert report["status"].startswith("BLOCKED")


def test_missing_technical_proof_blocked():
    doc = contract()
    doc["independent_technical_protections"].remove("durable_pre_and_post_terminal_receipts")
    assert "TECHNICAL_PROOFS_INCOMPLETE" in r044.validate_contract(doc)


def test_duplicate_proof_blocked():
    doc = contract()
    doc["independent_technical_protections"].append("durable_pre_and_post_terminal_receipts")
    assert "TECHNICAL_PROOFS_INCOMPLETE" in r044.validate_contract(doc)


@pytest.mark.parametrize("path", tuple(r044.SOURCES))
def test_each_canonical_source_fence_must_hold(path):
    src = source_fixture()
    src[path] = "replaced unsafe source"
    report = r044.inspect(ROOT, source_text=src, doc=contract())
    assert "CANONICAL_SOURCE_BOUNDARY_CHANGED:" + path in report["blockers"]
    assert report["authority_granted"] is False


def test_document_not_runtime_authority():
    file = ROOT / "scripts/coordination/control_plane/cf10_single_owner_pilot_review_v0_1.py"
    tree = ast.parse(file.read_text())
    call_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            call_names.add(fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else "UNKNOWN")
    assert not ({"launch_once", "append_record", "os.system", "Popen", "create_subprocess_exec", "commit", "push"} & call_names)
    assert "LIVE_CUTOVER_ENABLED=True" not in file.read_text()



def test_real_sources_match_review_contract():
    r = r044.inspect(ROOT)
    assert not r["blockers"], r["blockers"]
    assert r["status"] == "OWNER_SELECTED_DESIGN_RELEASE_BLOCKED"


def test_invalid_policy_rejected():
    assert r044.validate_contract(None) == ["POLICY_NOT_MAPPING"]
    assert r044.validate_contract([]) == ["POLICY_NOT_MAPPING"]


def test_next_milestone_order_pinned():
    doc = contract()
    doc["next_engineering_milestones"].reverse()
    assert "NEXT_STEP_CONTRACT_INVALID" in r044.validate_contract(doc)
