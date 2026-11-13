"""Isolated tests: no live /etc or s01 access and no worker invocation."""
from __future__ import annotations
import json
from pathlib import Path
import os
import stat
import subprocess
import pytest
from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_2 as m


def fake_review():
    matches = {r: {"exact_writer_release_sha256_match": True} for r in m.inventory.TRACKED_WRITERS}
    matches[m.inventory.TRACKED_WRITERS[0]]["exact_writer_release_sha256_match"] = False
    matches[m.inventory.TRACKED_WRITERS[1]]["exact_writer_release_sha256_match"] = False
    return {"host":"s01", "deployment_checkout":str(m.inventory.DEPLOYMENT_PATH),
        "deployment_git_head":"bfeb799098c94fedcfc3d6b6a34af9323aeeb4f9",
        "coverage_evidence_sha256":"c5ad50d0db6b7062bc1de03d58715a964524db0a10047407f7cfad38f6598f0c",
        "canonical_ledger":{"status":{"state":"DIRECTORY","uid":0,"gid":0,
            "group_writable":False,"other_writable":False},
            "mount":{"state":"OBSERVED","network_or_fuse_surface":False}},
        "current_writer_process_observation":{"state":"OBSERVED","unreadable_count":0,"observed":[]},
        "findings_requiring_operator_action":[m.ALLOWED_LEGACY_FINDING],
        "operator_declared_boundary":{"other_hosts_onboarded":False},
        "writer_source_comparison":matches}


def decision_for(doc, hashes=None):
    hashes = hashes or {k:"a"*64 for k in m.RUNTIME_SOURCE_SET}
    return {m.SIGNED_EXTENSION_KEY:{
        "schema_version":m.SIGNED_EXTENSION_SCHEMA,
        "decision":m.OPERATOR_DECISION,
        "host":"s01",
        "deployment_root":str(m.inventory.DEPLOYMENT_PATH),
        "canonical_ledger":m.inventory.CANONICAL_REL,
        "deployment_git_head":doc["deployment_git_head"],
        "gate_publication_commit":m.inventory.GATE_COMMIT,
        "writer_publication_commit":m.inventory.WRITER_COMMIT,
        "technical_coverage_evidence_sha256":doc["coverage_evidence_sha256"],
        "runtime_source_sha256":hashes,
        "independent_operator_review_ref":"op-review:s01:2026-10-15"}}


def eval_ok(doc=None, decision=None, sources=None, verified=True):
    doc = fake_review() if doc is None else doc
    sources = {k:"a"*64 for k in m.RUNTIME_SOURCE_SET} if sources is None else sources
    decision = decision_for(doc,sources) if decision is None else decision
    return m.launch_preflight_v0_2(doc,decision,sources,independently_verified=verified)


def test_signed_authority_alone_without_readback_blocked():
    out=eval_ok(verified=False)
    assert out['status']=='BLOCKED' and out['launch_allowed'] is False
    assert 'INDEPENDENT_GATE_READBACK_NOT_VERIFIED' in out['blockers']


def test_non_authorizing_old_scan_not_enough():
    d=fake_review()
    out=m.launch_preflight_v0_2(d,None,None,independently_verified=False)
    assert not out['launch_allowed']


def test_true_authorized_case_requires_all_constraints():
    out=eval_ok()
    assert out['status']=='READY_FOR_OPERATOR_MAKE'
    assert out['launch_allowed'] is True
    assert out['worker_launch_performed'] is False


def test_dirty_active_dispatch_cycle_accepted_only_if_signed():
    d=fake_review()
    assert eval_ok(d)['launch_allowed']
    x=decision_for(d)
    x[m.SIGNED_EXTENSION_KEY]['runtime_source_sha256'][m.inventory.TRACKED_WRITERS[0]]='b'*64
    out=m.launch_preflight_v0_2(d,x,{k:'a'*64 for k in m.RUNTIME_SOURCE_SET},independently_verified=True)
    assert out['status']=='BLOCKED' and 'SIGNED_RUNTIME_BINDING_DRIFT:runtime_source_sha256' in out['blockers']


def test_unsigned_extension_missing_blocks():
    assert 'SIGNED_RUNTIME_EXTENSION_MISSING' in eval_ok(decision={})['blockers']


def test_signed_approval_review_ref_is_required():
    d=fake_review(); x=decision_for(d)
    x[m.SIGNED_EXTENSION_KEY]['independent_operator_review_ref']=''
    assert 'SIGNED_RUNTIME_REVIEW_REFERENCE_MISSING' in eval_ok(d,decision=x)['blockers']


def test_missing_coverage_sha_binding_fails():
    d=fake_review(); x=decision_for(d)
    x[m.SIGNED_EXTENSION_KEY]['technical_coverage_evidence_sha256']='0'*64
    assert 'SIGNED_RUNTIME_BINDING_DRIFT:technical_coverage_evidence_sha256' in eval_ok(d,x)['blockers']


def test_wrong_host_blocks():
    d=fake_review();d['host']='other'
    assert 'DEPLOYMENT_IDENTITY_NOT_S01' in eval_ok(d)['blockers']


def test_root_owned_ledger_is_required():
    d=fake_review();d['canonical_ledger']['status']['uid']=1000
    assert 'CANONICAL_LEDGER_DAC_NOT_SAFE' in eval_ok(d)['blockers']


def test_broad_dac_access_blocks():
    d=fake_review();d['canonical_ledger']['status']['group_writable']=True
    assert 'CANONICAL_LEDGER_DAC_NOT_SAFE' in eval_ok(d)['blockers']


def test_network_mount_blocks():
    d=fake_review();d['canonical_ledger']['mount']['network_or_fuse_surface']=True
    assert 'CANONICAL_MOUNT_UNVERIFIED' in eval_ok(d)['blockers']


def test_unknown_mount_blocks():
    d=fake_review();d['canonical_ledger']['mount']['state']='UNKNOWN_MOUNTINFO'
    assert 'CANONICAL_MOUNT_UNVERIFIED' in eval_ok(d)['blockers']


def test_unreadable_process_inventory_blocks():
    d=fake_review();d['current_writer_process_observation']['unreadable_count']=1
    assert 'PROCESS_INVENTORY_UNRELIABLE' in eval_ok(d)['blockers']


def test_extra_operator_finding_blocks():
    d=fake_review();d['findings_requiring_operator_action'].append('UNKNOWN_WRITER')
    assert 'UNREVIEWED_OPERATOR_FINDINGS' in eval_ok(d)['blockers']


def test_changed_ledger_or_lock_disallowed_even_signed():
    for rel in m.inventory.TRACKED_WRITERS[-2:]:
        d=fake_review();d['writer_source_comparison'][rel]['exact_writer_release_sha256_match']=False
        assert 'CANONICAL_LEDGER_OR_LOCK_SOURCE_DRIFT:'+rel in eval_ok(d)['blockers']


def test_signing_remote_host_onboarding_cannot_expand_s01():
    d=fake_review();d['operator_declared_boundary']['other_hosts_onboarded']=True
    assert 'REMOTE_HOSTS_SCOPE_CHANGED' in eval_ok(d)['blockers']


def test_missing_source_and_symlink_block(tmp_path):
    with pytest.raises(m.PreflightBlocked,match='RUNTIME_SOURCE_MISSING'):
        m.signed_source_digests(tmp_path)
    f=tmp_path/m.RUNTIME_SOURCE_SET[0];f.parent.mkdir(parents=True);f.symlink_to(tmp_path/'outside')
    with pytest.raises(m.PreflightBlocked,match='RUNTIME_SOURCE_UNSAFE'):
        m.signed_source_digests(tmp_path)


def test_source_sha_detects_uncommitted_change(tmp_path):
    for rel in m.RUNTIME_SOURCE_SET:
        file=tmp_path/rel;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(rel,encoding='utf-8')
    before=m.signed_source_digests(tmp_path)
    f=tmp_path/m.RUNTIME_SOURCE_SET[0];f.write_text('CHANGED')
    after=m.signed_source_digests(tmp_path)
    assert before[m.RUNTIME_SOURCE_SET[0]]!=after[m.RUNTIME_SOURCE_SET[0]]


def test_external_verifier_return_code_must_pass(monkeypatch,tmp_path):
    class Result:
        returncode=2; stdout='{"status":"BLOCKED"}'
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**kw: Result())
    with pytest.raises(m.PreflightBlocked,match='INDEPENDENT_GATE_BLOCKED'):
        m._verified_process(root=tmp_path,module='test.fake',argv=('verify',),expected_stage='verify',allowed_status='PASS')


def test_external_activation_must_report_complete_checks(monkeypatch,tmp_path):
    class Result:
        returncode=0; stdout=json.dumps({'stage':'verify','status':'PASS','blockers':[],
            'checks':{'external_approval':'SIGNED_PASS'}})
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**kw:Result())
    with pytest.raises(m.PreflightBlocked,match='ACTIVATION_GATE_CHECKS_INCOMPLETE'):
        m._verified_process(root=tmp_path,module='scripts.coordination.execution_attempt_writer_activation_v0_1',argv=('verify',),expected_stage='verify',allowed_status='PASS')


def test_unsigned_or_partially_authenticated_coverage_not_success(monkeypatch,tmp_path):
    class Result:
        returncode=0; stdout=json.dumps({'stage':'verify','status':'INDEPENDENTLY_ATTESTED_NON_AUTHORIZING','blockers':[],'activation_authorized':True})
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**kw:Result())
    with pytest.raises(m.PreflightBlocked,match='COVERAGE_CLAIMS_ACTIVATION'):
        m._verified_process(root=tmp_path,module='scripts.coordination.execution_attempt_writer_coverage_v0_1',argv=('verify',),expected_stage='verify',allowed_status='INDEPENDENTLY_ATTESTED_NON_AUTHORIZING')


def test_trusted_decision_not_self_generated(tmp_path):
    with pytest.raises(m.PreflightBlocked):
        m.trusted_decision_snapshot(tmp_path/'missing'/'signed_decision.json')


def test_never_advertises_mutation():
    out=eval_ok()
    for field in ('worker_launch_performed','external_provisioning_performed','canonical_ledger_mutation_performed','git_commit_push_performed'):
        assert out[field] is False


def test_approval_required_no_fallback_to_main_git_head():
    d=fake_review();x=decision_for(d)
    x[m.SIGNED_EXTENSION_KEY]['deployment_git_head']='0'*40
    assert 'SIGNED_RUNTIME_BINDING_DRIFT:deployment_git_head' in eval_ok(d,x)['blockers']
