"""R083 security regression: post-R082 freezes cannot be silently downgraded."""
from __future__ import annotations
from pathlib import Path
import copy
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_r083_frozen_epoch_gate_v0_1 as m

HEAD = 'a' * 40
BASE_FINGERPRINT = 'b' * 64
TASK = 'cf10-u180j-a998'
WORKER = 'worker-01'


def docs(*, new=True):
    prepared = {'attempt_id': TASK, 'worker_id': WORKER}
    binding = {'attempt_id': TASK, 'worker_id': WORKER,
               'runtime_provider':'github_copilot_cli','runtime_model':'auto'}
    if new:
        prepared[m.frozen.KEY] = {'schema_version':m.frozen.SCHEMA}
        binding['cf10_frozen_provider_assignment_sha256'] = 'c'*64
    return {'git_head':HEAD, 'fingerprint_sha256':BASE_FINGERPRINT}, prepared, {'binding':binding}


def run(tmp_path, d):
    return m.assert_launch_epoch(root=tmp_path,source_state=d[0],
          prepared=d[1],decision=d[2],attempt_id=TASK,worker_id=WORKER)


def test_required_epoch_checks_both_markers(monkeypatch, tmp_path):
    monkeypatch.setattr(m,'source_epoch',lambda *a:m.source_epoch.__name__ if False else 'FROZEN_REQUIRED_AFTER_R082')
    monkeypatch.setattr(m.frozen,'verify_decision',lambda **kw:{'new_assignment_verified':True,'legacy_copilot_only':False})
    d=docs(new=True)
    assert run(tmp_path,d)['frozen_verified'] is True
    for prop in ('prepared','decision','both'):
        x=copy.deepcopy(d)
        if prop in ('prepared','both'):x[1].pop(m.frozen.KEY)
        if prop in ('decision','both'):x[2]['binding'].pop('cf10_frozen_provider_assignment_sha256')
        with pytest.raises(m.EpochGateBlocked,match='DOWNGRADE_BLOCKED'):
            run(tmp_path,x)


def test_new_epoch_cannot_just_have_matching_markers_without_real_verify(monkeypatch,tmp_path):
    monkeypatch.setattr(m,'source_epoch',lambda *a:'FROZEN_REQUIRED_AFTER_R082')
    def no(_):pass
    monkeypatch.setattr(m.frozen,'verify_decision',lambda **kw:{'new_assignment_verified':False,'legacy_copilot_only':True})
    with pytest.raises(m.EpochGateBlocked,match='NEW_FROZEN_ASSIGNMENT_NOT_VERIFIED'):
        run(tmp_path, docs(new=True))


def test_real_r082_verifier_exception_propagates(monkeypatch,tmp_path):
    monkeypatch.setattr(m,'source_epoch',lambda *a:'FROZEN_REQUIRED_AFTER_R082')
    def fail(**kw):raise m.frozen.FrozenAssignmentBlocked('CF10_R082_DRIFT')
    monkeypatch.setattr(m.frozen,'verify_decision',fail)
    with pytest.raises(m.frozen.FrozenAssignmentBlocked):
        run(tmp_path,docs(new=True))


def test_legacy_history_requires_both_markers_absent_and_copilot(monkeypatch,tmp_path):
    monkeypatch.setattr(m,'source_epoch',lambda *a:'LEGACY_ANCESTOR_BEFORE_R082')
    monkeypatch.setattr(m.frozen,'verify_decision',lambda **kw:{'new_assignment_verified':False,'legacy_copilot_only':True})
    assert run(tmp_path,docs(new=False))['frozen_verified'] is False
    with pytest.raises(m.EpochGateBlocked,match='HISTORICAL_ATTEMPT_MIXED'):
        run(tmp_path,docs(new=True))
    monkeypatch.setattr(m.frozen,'verify_decision',lambda **kw:{'new_assignment_verified':False,'legacy_copilot_only':False})
    with pytest.raises(m.EpochGateBlocked,match='LEGACY_PROVIDER_NOT_ALLOWED'):
        run(tmp_path,docs(new=False))


@pytest.mark.parametrize('field', ['attempt_in_prepared','worker_in_prepared','attempt_in_decision','worker_in_decision','fingerprint','mapping'])
def test_malformed_identity_rejected_before_git(monkeypatch,tmp_path,field):
    monkeypatch.setattr(m,'source_epoch',lambda *a:pytest.fail('no git on identity drift'))
    x=docs(new=True)
    if field=='attempt_in_prepared': x[1]['attempt_id']='wrong'
    elif field=='worker_in_prepared': x[1]['worker_id']='wrong'
    elif field=='attempt_in_decision': x[2]['binding']['attempt_id']='wrong'
    elif field=='worker_in_decision': x[2]['binding']['worker_id']='wrong'
    elif field=='fingerprint':x[0]['fingerprint_sha256']='invalid'
    elif field=='mapping':x=(None,x[1],x[2])
    with pytest.raises(m.EpochGateBlocked):run(tmp_path,x)


def test_epoch_rejects_invalid_head_without_git(tmp_path):
    with pytest.raises(m.EpochGateBlocked,match='SOURCE_HEAD_INVALID'):
        m.source_epoch(tmp_path,'bad')


def test_source_epoch_git_history_real_fixture(tmp_path,monkeypatch):
    import subprocess
    def git(*args):return subprocess.run(['git',*args],cwd=tmp_path,capture_output=True,check=True,env={**__import__('os').environ,'GIT_CONFIG_GLOBAL':'/dev/null'})
    git('init','-q')
    git('config','user.email','cf10@example.invalid')
    git('config','user.name','CF10 Fixture')
    (tmp_path/'p').write_text('a')
    git('add','p');git('commit','-qm','base')
    base=git('rev-parse','HEAD').stdout.decode().strip()
    (tmp_path/'p').write_text('b')
    git('add','p');git('commit','-qm','next')
    nexthead=git('rev-parse','HEAD').stdout.decode().strip()
    monkeypatch.setattr(m,'R082_BASE',base)
    assert m.source_epoch(tmp_path,base)=='FROZEN_REQUIRED_AFTER_R082'
    assert m.source_epoch(tmp_path,nexthead)=='FROZEN_REQUIRED_AFTER_R082'
    monkeypatch.setattr(m,'R082_BASE',nexthead)
    assert m.source_epoch(tmp_path,base)=='LEGACY_ANCESTOR_BEFORE_R082'
    with pytest.raises(m.EpochGateBlocked,match='SOURCE_COMMIT_NOT_IN_REPO'):
        m.source_epoch(tmp_path,'f'*40)


def test_no_authority_markers(monkeypatch,tmp_path):
    monkeypatch.setattr(m,'source_epoch',lambda *a:'FROZEN_REQUIRED_AFTER_R082')
    monkeypatch.setattr(m.frozen,'verify_decision',lambda **kw:{'new_assignment_verified':True,'legacy_copilot_only':False})
    result=run(tmp_path,docs(new=True))
    assert all(result[k] is False for k in ['launch_authorized','owner_claim_consumed','worker_launched','result_accepted','automatic_fallback','automatic_retry'])
