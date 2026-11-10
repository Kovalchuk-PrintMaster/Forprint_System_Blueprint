"""R133 isolation suite: no real systemd, no root receipts, no Worker."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r133_post_release_quarantine_v0_1 as q,
    cf10_systemd_kernel_witness_v0_1 as kernel,
)

UNIT = 'forprint-cf10-worker-' + 'a'*24 + '.service'
INVOCATION = 'b'*32
ATTEMPT = 'cf10-r133case-a133'
HEAD = 'c'*40
ROOT = Path(__file__).resolve().parents[4]


def witness(monkeypatch, state=None):
    obj = kernel.KernelWitness(UNIT, INVOCATION, -1)
    monkeypatch.setattr(kernel.KernelWitness, 'close', lambda self: setattr(self, 'closed', True))
    if state is None:
        state = {'transition': '1_TO_0', 'unit': UNIT,
                 'invocation_id': INVOCATION, 'kernel_observation': 'PINNED_FD_READ'}
    monkeypatch.setattr(kernel.KernelWitness, 'wait_zero', lambda self, *, timeout_seconds: state)
    return obj


def setup_quarantine(monkeypatch, *, rc=0, state=None):
    monkeypatch.setattr(q.os, 'geteuid', lambda: 0)
    w = witness(monkeypatch, state)
    events = []
    monkeypatch.setattr(q.receipts, 'append_observation', lambda **k: events.append(k['event']))
    calls = []
    def runner(argv):
        calls.append(argv)
        if argv[1] == 'show':
            rows = dict.fromkeys(kernel.PROPS, '')
            rows.update(Id=UNIT, InvocationID=INVOCATION, LoadState='loaded',
                ControlGroup='/system.slice/'+UNIT, User='forprint-runner',
                Group='forprint-runner', KillMode='control-group')
            return SimpleNamespace(returncode=0,stdout=('\n'.join(k+'='+v for k,v in rows.items())+'\n').encode())
        return SimpleNamespace(returncode=rc)
    return w, events, calls, runner


def call_q(w, runner):
    return q.quarantine(attempt_id=ATTEMPT, source_head=HEAD, unit=UNIT,
                        pinned_witness=w, timeout_seconds=30, runner=runner)


def test_cancelled_cgroup_is_only_review_not_worker_terminal(monkeypatch):
    w, events, calls, runner = setup_quarantine(monkeypatch)
    out = call_q(w, runner)
    assert calls[-1] == [q.SYSTEMCTL,'kill','--signal=SIGKILL','--',UNIT]
    assert calls[0][:3] == [q.SYSTEMCTL,'show','--no-pager']
    assert events == ['QUIESCENCE_OBSERVED_CANDIDATE', 'REVIEW_REQUIRED']
    assert out['state'] == 'CANCELLED_KERNEL_ZERO_REVIEW_REQUIRED'
    assert out['terminal_success'] is out['worker_result_accepted'] is False
    assert out['automatic_retry'] is out['release_allowed'] is False


def test_kill_error_is_hold_and_receipt_marks_unproven(monkeypatch):
    w, events, calls, runner = setup_quarantine(monkeypatch, rc=1)
    with pytest.raises(q.QuarantineHold, match='KILL_NOT_PROVEN'):
        call_q(w, runner)
    assert events == ['QUIESCENCE_UNPROVEN','REVIEW_REQUIRED']


@pytest.mark.parametrize('state', [
    {'transition': '1_TO_0', 'unit': UNIT, 'invocation_id': '0'*32,
     'kernel_observation': 'PINNED_FD_READ'},
    {'transition': '1_TO_0', 'unit': UNIT, 'invocation_id': INVOCATION,
     'kernel_observation': 'SYNTHETIC'},
    {'transition': 'MISSING', 'unit': UNIT, 'invocation_id': INVOCATION,
     'kernel_observation': 'PINNED_FD_READ'},
])
def test_kernel_evidence_forgery_cannot_pass(monkeypatch,state):
    w, events, _, runner = setup_quarantine(monkeypatch, state=state)
    with pytest.raises(q.QuarantineHold, match='KERNEL_ZERO_NOT_PROVEN'):
        call_q(w, runner)
    assert events == ['QUIESCENCE_UNPROVEN','REVIEW_REQUIRED']


def test_untrusted_unit_refused_before_systemd(monkeypatch):
    w, events, calls, runner = setup_quarantine(monkeypatch)
    with pytest.raises(q.QuarantineHold, match='PINNED_WITNESS_REQUIRED'):
        q.quarantine(attempt_id=ATTEMPT,source_head=HEAD,
                     unit='forprint-cf10-worker-'+'e'*24+'.service',
                     pinned_witness=w,timeout_seconds=30,runner=runner)
    assert calls == events == []


def test_root_only_before_kill(monkeypatch):
    w, events, calls, runner = setup_quarantine(monkeypatch)
    monkeypatch.setattr(q.os,'geteuid',lambda:996)
    with pytest.raises(q.QuarantineHold,match='ROOT_REQUIRED'):
        call_q(w,runner)
    assert calls == events == []


def test_bogus_witness_or_closed_fd_refused(monkeypatch):
    w, events, calls, runner = setup_quarantine(monkeypatch)
    with pytest.raises(q.QuarantineHold,match='PINNED_WITNESS_REQUIRED'):
        q.quarantine(attempt_id=ATTEMPT,source_head=HEAD,unit=UNIT,
                     pinned_witness=object(),timeout_seconds=30,runner=runner)
    w.closed=True
    with pytest.raises(q.QuarantineHold,match='PINNED_WITNESS_REQUIRED'):
        call_q(w,runner)
    assert calls == events == []


def test_root_receipt_failed_never_reports_success(monkeypatch):
    w, _, _, runner = setup_quarantine(monkeypatch)
    def reject(**kw):raise q.receipts.ReceiptBlocked('fixture')
    monkeypatch.setattr(q.receipts,'append_observation',reject)
    with pytest.raises(q.QuarantineHold, match='REVIEW_NOT_DURABLE'):
        call_q(w,runner)


def _extract_r030(monkeypatch, *, terminal_error=False, pre_error=False, callback_error=False, cancel_error=False, post_error=False, retire_error=False):
    """Exec the ACTUAL R030 run_once AST with only named fake dependencies."""
    src=(ROOT/'scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py').read_text('utf8')
    tree=ast.parse(src)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_once')
    calls=[]
    w=witness(monkeypatch)
    class Cutover(RuntimeError):pass
    def denied(reason):raise Cutover(reason)
    spec=SimpleNamespace(attempt_id=ATTEMPT,source_head=HEAD,timeout_seconds=30)
    plan={'identity':{'unit':UNIT}}
    def arm(unit, runner):
        calls.append('arm');assert unit==UNIT
        return w
    def pre(**kw):
        calls.append('durable-pre')
        if pre_error:raise RuntimeError('pre-error')
    def post(**kw):
        calls.append('durable-terminal')
        if post_error:raise RuntimeError('post-error')
    def launch(**kw):
        calls.append('held')
        kw['started_callback']({'pid':123,'unit':UNIT})
        calls.append('release')
        return {'state':'SYSTEMD_RELEASED_OBSERVE_WORKER','unit':UNIT,'process_started':True}
    def observed(**kw):
        calls.append('terminal-readback')
        if terminal_error:raise RuntimeError('terminal-error')
        return {'return_code':0,'worker_result_accepted':False}
    def cancel(**kw):
        calls.append('quarantine')
        if cancel_error:raise q.QuarantineHold('failure')
        return {'state':'CANCELLED_KERNEL_ZERO_REVIEW_REQUIRED'}
    monkeypatch.setattr(q,'quarantine',cancel)
    env={
        'assert_cutover_ready':lambda:None,
        'os':SimpleNamespace(geteuid=lambda:0),
        'deny':denied,'CanonicalCutoverBlocked':Cutover,
        'bind_contract':lambda **kwargs:(spec,plan),
        'backend':SimpleNamespace(launch_after_owner_claim=launch,RUNTIME=Path('/srv/fixture')),
        'witness':SimpleNamespace(arm=arm),
        'durable':SimpleNamespace(record_pre=pre,record_terminal=post),
        'terminal':SimpleNamespace(witnessed_terminal=observed),
        'handoff':SimpleNamespace(
            TerminalHandoffHold=type('HandoffHold',(RuntimeError,),{}),
            review_success=lambda **k: calls.append('review-terminal'),
            review_cancelled=lambda **k: calls.append('review-cancelled')),
        '_trusted_runner':lambda argv:None,
        '_retire_after_durable_terminal':lambda u:(calls.append('retire'), (_ for _ in ()).throw(RuntimeError('retire-error')) if retire_error else None),
    }
    exec(compile(ast.Module(body=[function],type_ignores=[]),str(ROOT/'scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py'),'exec'),env)
    def callback(rec):
        calls.append('ledger-started')
        if callback_error:raise RuntimeError('started-error')
    def run():
        return env['run_once'](root=None,runtime_root=None,task_prompt_id='task',
                               attempt_id=ATTEMPT,source_head=HEAD,
                               baseline_sha256='d'*64,handoff_sha256='e'*64,
                               launch_values={},started_callback=callback)
    return run,calls,w,Cutover


def test_real_r030_function_orders_pre_ledger_release_terminal(monkeypatch):
    run,calls,w,_=_extract_r030(monkeypatch)
    assert run()['return_code']==0
    assert calls==['held','arm','durable-pre','ledger-started','release',
                   'terminal-readback','durable-terminal','review-terminal','retire']
    assert w.closed is True


def test_real_r030_post_release_failure_routes_quarantine(monkeypatch):
    run,calls,w,_=_extract_r030(monkeypatch,terminal_error=True)
    with pytest.raises(RuntimeError,match='terminal-error'):
        run()
    assert calls[-3:]==['terminal-readback','quarantine','review-cancelled']
    assert 'durable-terminal' not in calls and 'retire' not in calls
    assert w.closed is True


def test_real_r030_quarantine_failure_stays_blocked(monkeypatch):
    run,calls,w,Cutover=_extract_r030(monkeypatch,terminal_error=True,cancel_error=True)
    with pytest.raises(Cutover,match='POST_RELEASE_RECONCILE_REQUIRED'):
        run()
    assert 'quarantine' in calls and w.closed


def test_real_r030_pre_release_failure_never_kills(monkeypatch):
    run,calls,w,_=_extract_r030(monkeypatch,pre_error=True)
    with pytest.raises(RuntimeError,match='pre-error'):
        run()
    assert calls == ['held','arm','durable-pre']
    assert w.closed


def test_real_r030_started_callback_failure_never_kills(monkeypatch):
    run,calls,w,_=_extract_r030(monkeypatch,callback_error=True)
    with pytest.raises(RuntimeError,match='started-error'):
        run()
    assert calls == ['held','arm','durable-pre','ledger-started']
    assert w.closed


def test_no_live_admission_source_change():
    s=(ROOT/'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py').read_text()
    assert 'LIVE_CUTOVER_ENABLED=False' in s
    assert '/tmp/' not in (ROOT/'scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py').read_text()


def test_real_r030_durable_terminal_failure_routes_quarantine(monkeypatch):
    run,calls,w,_=_extract_r030(monkeypatch,post_error=True)
    with pytest.raises(RuntimeError,match='post-error'):
        run()
    assert calls[-4:] == ['terminal-readback','durable-terminal','quarantine','review-cancelled']
    assert 'retire' not in calls and w.closed


def test_real_r030_retire_failure_does_not_reclassify_success_as_kill(monkeypatch):
    run,calls,w,_=_extract_r030(monkeypatch,retire_error=True)
    with pytest.raises(RuntimeError,match='retire-error'):
        run()
    assert calls[-3:] == ['durable-terminal','review-terminal','retire']
    assert 'quarantine' not in calls and w.closed


def test_kill_command_oserror_fails_closed(monkeypatch):
    w,events,_,runner=setup_quarantine(monkeypatch)
    def bad(argv):
        if argv[1]=='show':return runner(argv)
        raise OSError('unavailable')
    with pytest.raises(q.QuarantineHold,match='KILL_NOT_PROVEN'):
        call_q(w,bad)
    assert events == ['QUIESCENCE_UNPROVEN','REVIEW_REQUIRED']


def test_quarantine_rejects_invalid_attempt_before_kill(monkeypatch):
    w,events,calls,runner=setup_quarantine(monkeypatch)
    with pytest.raises(q.QuarantineHold, match='CANONICAL_IDENTITY'):
        q.quarantine(attempt_id='../bad',source_head=HEAD,unit=UNIT,
                     pinned_witness=w,timeout_seconds=30,runner=runner)
    assert calls == events == []


def test_recycled_systemd_invocation_refused_before_kill(monkeypatch):
    w,events,calls,runner=setup_quarantine(monkeypatch)
    def recycled(argv):
        cp=runner(argv)
        if argv[1]=='show':
            cp.stdout=cp.stdout.replace(INVOCATION.encode(),('f'*32).encode())
        return cp
    with pytest.raises(q.QuarantineHold,match='RETAINED_UNIT_IDENTITY_DRIFT'):
        call_q(w,recycled)
    assert len(calls)==1 and calls[0][1]=='show'
    assert events==[]


def test_unreadable_systemd_readback_refused_before_kill(monkeypatch):
    w,events,calls,runner=setup_quarantine(monkeypatch)
    def failed_show(argv):
        return SimpleNamespace(returncode=1,stdout=b'')
    with pytest.raises(q.QuarantineHold,match='RETAINED_UNIT_READBACK_UNAVAILABLE'):
        call_q(w,failed_show)
    assert events==[]
