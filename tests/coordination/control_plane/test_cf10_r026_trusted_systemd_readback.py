"""Adversarial tests for root-side real systemd / kernel observations."""
from pathlib import Path
import os
import subprocess
import pytest
from scripts.coordination.control_plane import cf10_r026_trusted_systemd_readback_v0_1 as m
from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as old

ID=old.identity_from_source(attempt_id='cf10-r026fixture-abcdef123456-a026',
    head='3734cb3c60b57d284264d05082e756c05481ea5e',handoff_sha256='f'*64)

def show(*,load='not-found',active='inactive',pid=0,group='',user='',group_user='',kill='',uid=None):
    d={'Id':ID.unit if uid is None else uid,'LoadState':load,'ActiveState':active,
       'MainPID':str(pid),'ControlGroup':group,'User':user,'Group':group_user,'KillMode':kill}
    return ('\n'.join(f'{p}={d[p]}' for p in m.PROPS)+'\n').encode()

def run(raw, *, rc=0):
    return lambda args: subprocess.CompletedProcess(args,rc,raw,b'')

def sample(tmp_path,raw, *, rc=0):
    return m._collect(ID,runner=run(raw,rc=rc),kernel_root=tmp_path)

def test_absent_unit_is_non_authorizing(tmp_path):
    out=sample(tmp_path,show())
    assert out['systemctl']['load_state']=='not-found'
    assert out['kernel']['cgroup_state']=='UNKNOWN_NO_CONTROL_GROUP'
    assert not out['release_allowed'] and not out['production_quiescence_proven']

def test_argv_uses_only_bound_unit(tmp_path):
    called=[]
    def runner(args):
        called.append(args)
        return subprocess.CompletedProcess(args,0,show(),b'')
    m._collect(ID,runner=runner,kernel_root=tmp_path)
    assert called[0][:3]==['/usr/bin/systemctl','show','--no-pager']
    assert called[0][-2:]==['--',ID.unit]
    assert all(x.startswith('--property=') for x in called[0][3:-2])

@pytest.mark.parametrize('bad',[
    b'',b'junk',b'Id=x\n',b'Id=a\nId=b\n',b'\0',b'\xff',b'Id=x'*4000,
    show(uid='forprint-other.service'),show().replace(b'User=',b'User=root\nUser='),
    show().replace(b'ActiveState=inactive',b'ActiveState=unknown'),
    show().replace(b'MainPID=0',b'MainPID=NaN'),
    show().replace(b'LoadState=not-found',b'LoadState=loaded\nBadField=x'),
])
def test_invalid_show_rejected(tmp_path,bad):
    with pytest.raises((m.ReadbackBlocked,old.RecoveryBlocked)):
        sample(tmp_path,bad)

def test_bad_systemctl_return_code(tmp_path):
    with pytest.raises(m.ReadbackBlocked,match='SYSTEMCTL_RETURN_CODE'):
        sample(tmp_path,show(),rc=1)

def test_kernel_no_cgroup_not_proof(tmp_path):
    out=sample(tmp_path,show(load='loaded',active='inactive',
                            group='/system.slice/'+ID.unit,
                            user='forprint-runner',group_user='forprint-runner',kill='control-group'))
    assert out['kernel']['cgroup_state']=='REMOVED_NOT_PROOF'

def make_cgroup(root,events=b'populated 0\nfrozen 0\n'):
    d=root/ID.unit;d.mkdir()
    (d/'cgroup.events').write_bytes(events)
    return d

def test_inactive_cgroup_empty_sample(tmp_path):
    make_cgroup(tmp_path)
    out=sample(tmp_path,show(load='loaded',active='inactive',
                  group='/system.slice/'+ID.unit,user='forprint-runner',group_user='forprint-runner',kill='control-group'))
    assert out['kernel']['cgroup_state']=='EMPTY_AT_SAMPLE'
    assert out['production_quiescence_proven'] is False

def test_inactive_cgroup_still_populated(tmp_path):
    make_cgroup(tmp_path,b'populated 1\n')
    out=sample(tmp_path,show(load='loaded',active='inactive',
                  group='/system.slice/'+ID.unit,user='forprint-runner',group_user='forprint-runner',kill='control-group'))
    assert out['kernel']['cgroup_state']=='INACTIVE_BUT_POPULATED'

def test_active_cgroup_populated(tmp_path):
    make_cgroup(tmp_path,b'populated 1\n')
    out=sample(tmp_path,show(load='loaded',active='active',pid=1234,
                  group='/system.slice/'+ID.unit,user='forprint-runner',group_user='forprint-runner',kill='control-group'))
    assert out['kernel']['cgroup_state']=='POPULATED'

def test_active_cgroup_absent_fails_closed(tmp_path):
    with pytest.raises(m.ReadbackBlocked,match='ACTIVE_UNIT_WITHOUT_POPULATED_CGROUP'):
        sample(tmp_path,show(load='loaded',active='active',pid=1234,
                  group='/system.slice/'+ID.unit,user='forprint-runner',group_user='forprint-runner',kill='control-group'))

@pytest.mark.parametrize('events',[b'',b'frozen 0\n',b'populated 2\n',b'populated 0\npopulated 1\n',b'populated XX\n',b'populated 0 1\n'])
def test_malformed_cgroup_fails_closed(tmp_path,events):
    make_cgroup(tmp_path,events)
    with pytest.raises(m.ReadbackBlocked):
        sample(tmp_path,show(load='loaded',active='inactive',group='/system.slice/'+ID.unit),)

def test_symlink_cgroup_rejected(tmp_path):
    (tmp_path/ID.unit).symlink_to(tmp_path)
    with pytest.raises(m.ReadbackBlocked):
        sample(tmp_path,show(load='loaded',active='inactive',group='/system.slice/'+ID.unit))

def test_symlink_cgroup_event_rejected(tmp_path):
    d=tmp_path/ID.unit;d.mkdir()
    (d/'cgroup.events').symlink_to('/etc/passwd')
    with pytest.raises(OSError):
        sample(tmp_path,show(load='loaded',active='inactive',group='/system.slice/'+ID.unit))

def test_helper_can_join_non_authorizing(monkeypatch,tmp_path):
    data=sample(tmp_path,show())
    monkeypatch.setattr(m,'collect',lambda identity:data)
    report=m.reconcile_without_side_effects(identity=ID,receipt_summary=None,ledger_rows=[],claim_path_occupied=False)
    assert report['automatic_retry'] is False
    assert report['recovery']['launch_allowed'] is False
    assert report['recovery']['release_allowed'] is False

def test_root_required(monkeypatch):
    monkeypatch.setattr(m.os,'geteuid',lambda:1000)
    with pytest.raises(m.ReadbackBlocked,match='ROOT_REQUIRED'):
        m.collect(ID)
