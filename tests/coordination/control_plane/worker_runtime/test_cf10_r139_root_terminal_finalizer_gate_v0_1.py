"""R139: fail-closed root finalizer handoff; all root readbacks are mocked here.

These are contract tests, not kernel or Worker E2E acceptance.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
from unittest import mock

import pytest

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bind
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r138_canonical_terminal_handoff_v0_1 as r138,
    cf10_r139_root_terminal_finalizer_gate_v0_1 as r139,
)

ATT = 'cf10-u180j-a555'
HEAD = 'a'*40
BASE = 'b'*64
HANDOFF = 'c'*64
INV = 'd'*32
UNIT = bind.unit_for(ATT,HEAD)


def pending():
    return {'attempt_id': ATT,'attempt_stage':'STARTED',
            'result_state':'PENDING','validator_outcome':'NOT_RUN'}


def process():
    return {'systemd_unit':UNIT,'systemd_invocation_id':INV,
            'outcome':'completed','return_code':0,'timed_out':False,
            'release_allowed':False,
            'quiescence_observation':r138.KERNEL,
            'worker_result_accepted':False,'automatic_retry':False}


def proof(row=None):
    if row is None:row=pending()
    return {'r035_pre_record_sha256':'1'*64,
            'r035_terminal_record_sha256':'2'*64,
            'r015_last_receipt_sha256':'3'*64,
            'ledger_started_sha256':hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',', ':'),ensure_ascii=False).encode('utf-8')).hexdigest()}


@pytest.fixture
def trust(tmp_path,monkeypatch):
    root = tmp_path / 'blueprint'
    root.mkdir(mode=0o700)
    monkeypatch.setattr(r139,'ROOT',root)
    monkeypatch.setattr(r139.os,'geteuid',lambda:0)
    return root


def call(rootpath,**changes):
    args=dict(root=rootpath,attempt_id=ATT,source_head=HEAD,
              baseline_sha256=BASE,handoff_sha256=HANDOFF,
              started_record=pending(),process_result=process())
    args.update(changes)
    return r139.review_pending_success(**args)


def test_good_strict_review(trust):
    with mock.patch.object(r138,'_trusted_readback',return_value=proof()) as read:
        result=call(trust)
    assert result['state']==r139.READY
    assert result['systemd_invocation_id']==INV
    assert result['r035_terminal_record_sha256']=='2'*64
    assert all(result[k] is False for k in ('terminal_ledger_written','worker_result_accepted',
                                              'release_allowed','automatic_retry','g1_g5_closed',
                                              'independent_worker_result_verified'))
    read.assert_called_once()
    kw=read.call_args.kwargs
    assert kw['unit']==UNIT and kw['invocation']==INV and kw['cancelled'] is False
    assert kw['spec'].source_head==HEAD and kw['spec'].baseline_sha256==BASE
    assert kw['spec'].handoff_sha256==HANDOFF


def test_nonroot_blocked_before_readback(trust,monkeypatch):
    monkeypatch.setattr(r139.os,'geteuid',lambda:1000)
    with mock.patch.object(r138,'_trusted_readback') as read:
        with pytest.raises(r139.RootFinalizerHold,match='ROOT_REQUIRED'):
            call(trust)
    read.assert_not_called()


@pytest.mark.parametrize('change',[
    {'root':Path('/tmp/untrusted')},
    {'attempt_id':'../../etc/passwd'},
    {'attempt_id':'cf10-u180j-a'},
    {'source_head':'f'*39},
    {'source_head':'F'*40},
    {'baseline_sha256':'f'*63},
    {'handoff_sha256':'f'*65},
    {'source_head':None},
    {'started_record':[]},
    {'process_result':[]},
])
def test_invalid_frozen_input(trust,change):
    with mock.patch.object(r138,'_trusted_readback') as read:
        with pytest.raises(r139.RootFinalizerHold):call(trust,**change)
    read.assert_not_called()


@pytest.mark.parametrize('change',[
    {'attempt_id':'cf10-u180j-a999'},
    {'attempt_stage':'FINISHED'},
    {'result_state':'SUCCEEDED'},
    {'validator_outcome':'PASS'},
])
def test_invalid_started_row(trust,change):
    row=pending();row.update(change)
    with mock.patch.object(r138,'_trusted_readback') as read:
        with pytest.raises(r139.RootFinalizerHold,match='STARTED_PENDING'):
            call(trust,started_record=row)
    read.assert_not_called()


@pytest.mark.parametrize('change',[
    {'systemd_unit':'evil.service'},
    {'systemd_invocation_id':'0'*31},
    {'return_code':1},
    {'timed_out':True},
    {'outcome':'failed'},
    {'quiescence_observation':'SYNTHETIC'},
    {'worker_result_accepted':True},
    {'automatic_retry':True},
    {'release_allowed':True},
])
def test_invalid_terminal_process(trust,change):
    p=process();p.update(change)
    with mock.patch.object(r138,'_trusted_readback') as read:
        with pytest.raises(r139.RootFinalizerHold):call(trust,process_result=p)
    read.assert_not_called()


@pytest.mark.parametrize('change',[
    {'r035_terminal_record_sha256':None},
    {'r015_last_receipt_sha256':'0'*63},
    {'ledger_started_sha256':'f'*64},
    {'extra_key':'bad'},
])
def test_untrusted_or_mismatched_root_digest(trust,change):
    result=proof();result.update(change)
    with mock.patch.object(r138,'_trusted_readback',return_value=result):
        with pytest.raises(r139.RootFinalizerHold,match='ROOT_LEDGER_CROSSSTORE'):
            call(trust)


def test_missing_root_readback(trust):
    with mock.patch.object(r138,'_trusted_readback',side_effect=r138.TerminalHandoffHold('missing')):
        with pytest.raises(r139.RootFinalizerHold,match='INDEPENDENT_READBACK'):
            call(trust)


def test_source_gate_is_before_existing_finalizer_and_not_on_terminal_replay():
    path=Path(r139.__file__).parents[1] / 'governed_worker_cycle.py'
    tree=ast.parse(path.read_text())
    func=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='advance_cycle')
    text=ast.get_source_segment(path.read_text(),func)
    assert text.index('root_terminal_gate.review_pending_success(') < text.index('dispatch_intent.finalize_cf10_workspace_result_artifact(')
    guard=text[text.index('if not terminal_already_present:',text.index('R139:')):text.index('# The existing full Handoff freshness')]
    assert 'root_terminal_gate.review_pending_success(' in guard
    assert 'except Exception as exc' in guard
    # The immutable terminal replay branch must remain before the finalizer.
    assert text.index('if terminal_already_present:') < text.index('dispatch_intent.finalize_cf10_workspace_result_artifact(')


def test_no_live_writer_or_worker_api_and_source_entry():
    src=Path(r139.__file__).read_text()
    forbidden=['append_record(', 'systemd-run', 'subprocess.Popen(', 'os.system(',
               'launch_after_owner_claim(', 'stop --', 'force_push']
    assert not any(s in src for s in forbidden)
    with mock.patch('scripts.coordination.control_plane.worker_runtime.cf10_systemd_launcher_v0_1.LIVE_CUTOVER_ENABLED',False):
        assert r139.main(['--mode','source-check'])==0
