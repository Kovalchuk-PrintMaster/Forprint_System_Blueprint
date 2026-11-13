"""S01 single-use candidate: local isolated fixtures only, no /etc, worker or ledger."""
import hashlib
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import stat
from unittest.mock import patch

import pytest

P = Path(__file__).with_name("cf10_s01_single_use_guard_v0_1.py")
if not P.exists():
    P = Path(__file__).resolve().parents[3] / "scripts/coordination/control_plane/cf10_s01_single_use_guard_v0_1.py"
spec = importlib.util.spec_from_file_location("cf10_single_use_fixture", P)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

HEAD = "a" * 40
WORKER = "worker-01"
TASK = "cf10-s01-single-pilot-v0-1"
ATTEMPT = "cf10-u180j-a048"


def binding():
    return {"receipt_sha256": "b" * 64, "publication_commit": HEAD,
            "worker_id": WORKER, "task_prompt_id": TASK, "attempt_id": ATTEMPT}


def predicate():
    return {"status": "PREDICATE_PASS_NON_AUTHORIZING", "predicate_pass": True,
            "blockers": [], "worker_id": WORKER, "task_prompt_id": TASK, "attempt_id": ATTEMPT,
            "checks": {"baseline": "PASS", "pilot_scope": "SIGNED_MATCH",
                       "proof_files_verified": 8, "head_stable": True},
            "launch_allowed": False, "authority_granted": False,
            "single_use_enforced": False, "worker_launched": False, "live_make_wired": False}


@pytest.fixture
def state(tmp_path):
    p = tmp_path / "cf10_s01_single_use_fixture"
    p.mkdir(mode=0o700)
    return p


def claim(state, b=None, pred=None):
    return module.consume_once_fixture(state, binding=b if b is not None else binding(),
                                       predicate=pred if pred is not None else predicate())


def test_valid_fixture_claim_is_non_authorizing_and_durable(state):
    value = claim(state)
    assert value["status"] == "CONSUMED_TEST_FIXTURE_NON_AUTHORIZING"
    assert value["claim_record_written"] is True
    for key in ("authority_granted", "launch_allowed", "worker_launched",
                "single_use_production_enforced", "canonical_ledger_modified", "live_make_wired"):
        assert value[key] is False
    data = json.loads((state/module.CLAIM_NAME).read_bytes())
    assert data["state"] == "CONSUMED_TEST_FIXTURE_ONLY"
    assert data["binding"] == binding()
    assert stat.S_IMODE((state/module.CLAIM_NAME).stat().st_mode) == 0o600


def test_second_claim_rejected_persistently(state):
    assert claim(state)["claim_record_written"] is True
    old = (state/module.CLAIM_NAME).read_bytes()
    assert claim(state)["blockers"] == ["SINGLE_USE_ALREADY_CONSUMED"]
    assert (state/module.CLAIM_NAME).read_bytes() == old


def test_second_different_attempt_cannot_reuse_same_fixture(state):
    assert claim(state)["claim_record_written"]
    b=binding(); b["attempt_id"]="cf10-u180j-a049"
    p=predicate(); p["attempt_id"]="cf10-u180j-a049"
    assert claim(state, b, p)["blockers"] == ["SINGLE_USE_ALREADY_CONSUMED"]


def test_crash_like_partial_marker_fails_closed(state):
    (state / module.CLAIM_NAME).write_bytes(b'{"incomplete":')
    assert claim(state)["blockers"] == ["SINGLE_USE_ALREADY_CONSUMED"]


def test_symlink_claim_file_blocks(state):
    (state / module.CLAIM_NAME).symlink_to(state / "missing")
    assert not claim(state)["claim_record_written"]
    assert (state / module.CLAIM_NAME).is_symlink()


def _claim_child(path, q, event):
    event.wait(timeout=10)
    v = module.consume_once_fixture(Path(path), binding=binding(), predicate=predicate())
    q.put(v["status"])


def test_multiprocess_exactly_one_consumes(state):
    ctx = multiprocessing.get_context("fork")
    q = ctx.Queue()
    go = ctx.Event()
    children = [ctx.Process(target=_claim_child, args=(str(state), q, go)) for _ in range(8)]
    for c in children: c.start()
    go.set()
    outcomes = [q.get(timeout=10) for _ in children]
    for c in children:
        c.join(timeout=10)
        assert c.exitcode == 0
    assert outcomes.count("CONSUMED_TEST_FIXTURE_NON_AUTHORIZING") == 1
    assert outcomes.count("BLOCKED_NON_AUTHORIZING") == 7


@pytest.mark.parametrize("bad, code", [
    ({"receipt_sha256":"z"*64},"RECEIPT_DIGEST_INVALID"),
    ({"publication_commit":"0"*39},"PUBLICATION_COMMIT_INVALID"),
    ({"worker_id":"worker-02"},"WORKER_NOT_SUPPORTED"),
    ({"attempt_id":"bad"},"ATTEMPT_ID_INVALID"),
    ({"task_prompt_id":"../oops"},"TASK_ID_INVALID"),
])
def test_bad_binding_blocks_without_state_write(state, bad, code):
    b=binding(); b.update(bad)
    assert code in module.binding_blockers(b, predicate())
    assert claim(state, b)["claim_record_written"] is False
    assert not (state / module.CLAIM_NAME).exists()


def test_unknown_binding_field_rejected(state):
    b = binding(); b["additional_authority"] = True
    assert claim(state,b)["blockers"] == ["EXACT_BINDING_REQUIRED"]


@pytest.mark.parametrize("key, value, error", [
    ("predicate_pass",False,"PREDICATE_NOT_VERIFIED"),
    ("status","PASS","PREDICATE_NOT_VERIFIED"),
    ("blockers",["fake"],"PREDICATE_HAS_BLOCKERS"),
    ("worker_id","worker-02","PREDICATE_BINDING_MISMATCH:worker_id"),
    ("task_prompt_id","wrong","PREDICATE_BINDING_MISMATCH:task_prompt_id"),
    ("attempt_id","cf10-u180j-a099","PREDICATE_BINDING_MISMATCH:attempt_id"),
    ("launch_allowed",True,"PREDICATE_PRETENDS_AUTHORITY:launch_allowed"),
    ("authority_granted",True,"PREDICATE_PRETENDS_AUTHORITY:authority_granted"),
    ("single_use_enforced",True,"PREDICATE_PRETENDS_AUTHORITY:single_use_enforced"),
    ("worker_launched",True,"PREDICATE_PRETENDS_AUTHORITY:worker_launched"),
    ("live_make_wired",True,"PREDICATE_PRETENDS_AUTHORITY:live_make_wired"),
])
def test_predicate_mutations_refused(state, key, value, error):
    p=predicate();p[key]=value
    assert error in module.binding_blockers(binding(), p)
    assert not claim(state, pred=p)["claim_record_written"]


@pytest.mark.parametrize("key,value", [
    ("baseline","BLOCKED"),("pilot_scope","NO"),
    ("proof_files_verified",7),("proof_files_verified",True),
    ("head_stable",False),
])
def test_missing_or_wrong_evidence_blocks(state,key,value):
    p=predicate();p["checks"][key]=value
    assert claim(state,pred=p)["blockers"] == ["PREDICATE_CHECKS_INCOMPLETE"]


def test_missing_predicate_blocks(state):
    assert claim(state,pred={})["claim_record_written"] is False


def test_refuse_public_or_group_visible_fixture(state):
    state.chmod(0o750)
    assert claim(state)["blockers"] == ["FIXTURE_DIRECTORY_NOT_SAFE"]


def test_refuse_ordinary_tmp_without_reserved_prefix(tmp_path):
    assert claim(tmp_path)["blockers"] == ["FIXTURE_DIRECTORY_NOT_SAFE"]


def test_refuse_symlink_fixture_root(state):
    alias=state.parent / "cf10_s01_single_use_alias"
    alias.symlink_to(state)
    assert claim(alias)["blockers"] == ["FIXTURE_DIRECTORY_NOT_SAFE"]


def test_refuse_nonexistent_directory(state):
    assert claim(state.parent / "cf10_s01_single_use_nope")["blockers"] == ["FIXTURE_DIRECTORY_NOT_SAFE"]


def test_indeterminate_write_retains_claim_for_safety(state,monkeypatch):
    def broke(*args, **kwargs):
        raise OSError("fixture IO failure")
    monkeypatch.setattr(module.os, "write", broke)
    result = claim(state)
    assert result["blockers"] == ["CLAIM_WRITE_INDETERMINATE_NO_RETRY"]
    assert (state / module.CLAIM_NAME).exists()
    monkeypatch.undo()
    assert claim(state)["blockers"] == ["SINGLE_USE_ALREADY_CONSUMED"]


def test_inspect_never_claims(state):
    assert module.inspect()["blockers"] == ["SINGLE_USE_NOT_LIVE_WIRED"]
    assert module.main(["inspect"]) == 0
    assert module.main(["launch-preflight"]) == 2
    assert list(state.iterdir()) == []


def test_no_live_or_external_paths_in_candidate_source():
    src = P.read_text()
    for forbidden in ("/etc/forprint", "/run/forprint", "launch_authorized_worker_cycle(",
                      "subprocess.Popen(", "ledger.append_record(", "git push", "git commit"):
        assert forbidden not in src
