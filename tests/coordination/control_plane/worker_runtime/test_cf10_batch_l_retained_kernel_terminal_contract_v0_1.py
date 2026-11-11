from __future__ import annotations
import copy
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_batch_l_retained_kernel_terminal_contract_v0_1 as m
UNIT='forprint-cf10-batchl-0123456789abcdef.service'
INV='a'*32

def running():
    d={'Id':UNIT,'LoadState':'loaded','ActiveState':'active','SubState':'running',
       'MainPID':'1234','ControlGroup':'/system.slice/'+UNIT,'InvocationID':INV,
       'Result':'success','ExecMainStatus':'0'}
    d.update(m.PROPERTIES)
    d['ReadWritePaths']='/run/'+UNIT.removesuffix('.service')+'/home'
    return d

def retained():
    d=running();d.update(SubState='exited',MainPID='0')
    return d

def sources():
    h=m.inspect_running(unit=UNIT,rows=running(),peer_pid=1234,peer_uid=996,peer_gid=992)
    t=m.inspect_retained(unit=UNIT,rows=retained(),invocation_id=INV)
    k={'unit':UNIT,'invocation_id':INV,'kernel_observation':'PINNED_FD_READ','transition':'1_TO_0','samples':['1','0']}
    p={'stop_rc':0,'active_state':'inactive','main_pid':'0'}
    return h,t,k,p

def test_positive_terminal():
    h,t,k,p=sources();r=m.attest(unit=UNIT,held=h,terminal=t,kernel=k,post=p)
    assert r['status']=='PASS_RETAINED_LAB_KERNEL_TRANSITION_ONLY'
    assert r['gates_open']==['G1','G2','G3','G4','G5']
    assert all(r[key] is False for key in ['production_kernel_terminal_proven','production_ledger_written','worker_claim_consumed','live_copilot_inference_executed','worker_admission_authorized'])

def test_source_check(): assert m.source_check()['source'].startswith('PASS')

@pytest.mark.parametrize('key,value',[
 ('Id','other.service'),('MainPID','2'),('ControlGroup','/a'),('ActiveState','inactive'),
 ('SubState','exited'),('LoadState','not-found'),('User','root'),('Group','root'),
 ('ExitType','main'),('RemainAfterExit','no'),('KillMode','process'),('PrivateNetwork','no'),
 ('NoNewPrivileges','no'),('ProtectHome','no'),('ProtectSystem','off'),
 ('RestrictAddressFamilies','AF_INET AF_UNIX'),('ReadWritePaths','/run/evil'),('InvocationID','x'),
])
def test_running_drift_denied(key,value):
    d=running();d[key]=value
    with pytest.raises(m.TerminalHold):m.inspect_running(unit=UNIT,rows=d,peer_pid=1234,peer_uid=996,peer_gid=992)

@pytest.mark.parametrize('key,value',[
 ('Id','other.service'),('MainPID','1234'),('SubState','running'),('ActiveState','inactive'),
 ('ExitType','main'),('RemainAfterExit','no'),('Result','exit-code'),
 ('ExecMainStatus','1'),('InvocationID','b'*32),('KillMode','mixed'),
])
def test_retained_drift_denied(key,value):
    d=retained();d[key]=value
    with pytest.raises(m.TerminalHold):m.inspect_retained(unit=UNIT,rows=d,invocation_id=INV)

@pytest.mark.parametrize('key,value',[
 ('kernel_observation','SYSTEMCTL_ONLY'),('transition','0_TO_0'),('samples',['1']),
 ('samples',['0']),('samples',['1','1','0']),('samples',['1','0','1','0']),('invocation_id','b'*32),
])
def test_kernel_drift_denied(key,value):
    h,t,k,p=sources();k[key]=value
    with pytest.raises(m.TerminalHold):m.attest(unit=UNIT,held=h,terminal=t,kernel=k,post=p)

@pytest.mark.parametrize('key,value',[('stop_rc',1),('active_state','active'),('main_pid','112')])
def test_post_stop_drift_denied(key,value):
    h,t,k,p=sources();p[key]=value
    with pytest.raises(m.TerminalHold):m.attest(unit=UNIT,held=h,terminal=t,kernel=k,post=p)

@pytest.mark.parametrize('uid,gid,pid',[(0,992,1234),(996,0,1234),(996,992,1)])
def test_peer_drift_denied(uid,gid,pid):
    with pytest.raises(m.TerminalHold):m.inspect_running(unit=UNIT,rows=running(),peer_pid=pid,peer_uid=uid,peer_gid=gid)

def test_occupied_new_key_denied():
    d=running();d['surprise']='true'
    with pytest.raises(m.TerminalHold):m.inspect_running(unit=UNIT,rows=d,peer_pid=1234,peer_uid=996,peer_gid=992)

def test_unit_scope_denied():
    for name in ('forprint-cf10-worker-'+'a'*24+'.service','forprint-cf10-batchl-012.service','forprint-cf10-batchl-0123456789abcdee.service;rm'):
        with pytest.raises(m.TerminalHold):m.check_unit(name)
