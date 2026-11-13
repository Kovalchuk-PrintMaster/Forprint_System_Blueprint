"""AB: pinned directory+events FD; no systemd units or live Worker required."""
from pathlib import Path
from types import SimpleNamespace
import os
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as kw

UNIT='forprint-cf10-worker-'+'a'*24+'.service'
INV='b'*32

def show_rows(*,pid='4321',inv=INV,group=UNIT):
    return {'Id':UNIT,'LoadState':'loaded','ActiveState':'active','SubState':'running',
      'MainPID':pid,'ControlGroup':'/system.slice/'+group,'InvocationID':inv,
      'RemainAfterExit':'yes','ExitType':'cgroup','User':'forprint-runner',
      'Group':'forprint-runner','KillMode':'control-group','Result':'success',
      'ExecMainStatus':'0'}

def runner(rows):
    def call(args):
        assert args[0]=='/usr/bin/systemctl' and args[-1]==UNIT
        return SimpleNamespace(returncode=0,stdout=('\n'.join(k+'='+v for k,v in rows.items())+'\n').encode())
    return call

@pytest.fixture
def cgroup(tmp_path,monkeypatch):
    root=tmp_path/'system.slice';root.mkdir()
    folder=root/UNIT;folder.mkdir();(folder/'cgroup.events').write_text('populated 1\nfrozen 0\n')
    old_lstat=Path.lstat;old_fstat=os.fstat
    def lstat(self,*args,**kw):
        st=old_lstat(self,*args,**kw)
        if self==folder:
            return SimpleNamespace(st_mode=st.st_mode,st_uid=0,st_dev=st.st_dev,st_ino=st.st_ino)
        return st
    def fstat(fd):
        st=old_fstat(fd)
        return SimpleNamespace(st_mode=st.st_mode,st_uid=0,st_dev=st.st_dev,st_ino=st.st_ino)
    monkeypatch.setattr(Path,'lstat',lstat)
    monkeypatch.setattr(os,'fstat',fstat)
    return root,folder

def test_dir_inode_and_events_pinned(cgroup):
    root,folder=cgroup
    witness=kw.arm(UNIT,runner(show_rows()),kernel_root=root,require_root=False)
    assert witness.anchor_fd is not None
    assert kw.read_fd(witness.fd)=='1'
    assert os.fstat(witness.anchor_fd).st_ino==folder.lstat().st_ino
    (folder/'cgroup.events').write_text('populated 0\nfrozen 0\n')
    result=witness.wait_zero(timeout_seconds=1)
    assert result['transition']=='1_TO_0' and result['samples']==['1','0']
    anchor=witness.anchor_fd;events=witness.fd
    witness.close();witness.close()
    assert witness.closed and witness.anchor_fd is None
    for fd in (anchor,events):
        with pytest.raises(OSError):os.read(fd,1)

def test_anchor_denies_inode_swapped(cgroup,monkeypatch):
    root,_=cgroup
    old_fstat=os.fstat
    calls={'n':0}
    def wrong(fd):
        st=old_fstat(fd);calls['n']+=1
        if calls['n']==1:
            return SimpleNamespace(st_mode=st.st_mode,st_uid=0,st_dev=st.st_dev,st_ino=st.st_ino+1)
        return st
    monkeypatch.setattr(os,'fstat',wrong)
    with pytest.raises(kw.WitnessBlocked,match='GROUP_ANCHOR_INODE_DRIFT'):
        kw.arm(UNIT,runner(show_rows()),kernel_root=root,require_root=False)

def test_initial_empty_cgroup_not_armed(cgroup):
    root,folder=cgroup
    (folder/'cgroup.events').write_text('populated 0\n')
    with pytest.raises(kw.WitnessBlocked,match='NOT_POPULATED_AT_ARM'):
        kw.arm(UNIT,runner(show_rows()),kernel_root=root,require_root=False)

@pytest.mark.parametrize('rows',[show_rows(pid='0'),show_rows(group='other.service'),show_rows(inv='x'),show_rows()|{'ExitType':'main'}])
def test_bad_held_identity_never_arms(cgroup,rows):
    root,_=cgroup
    with pytest.raises(kw.WitnessBlocked):kw.arm(UNIT,runner(rows),kernel_root=root,require_root=False)

def test_missing_events_holds(cgroup):
    root,folder=cgroup
    (folder/'cgroup.events').unlink()
    with pytest.raises(kw.WitnessBlocked):kw.arm(UNIT,runner(show_rows()),kernel_root=root,require_root=False)

def test_no_hidden_live_cutover_from_kernel_module():
    assert kw.UNIT.fullmatch(UNIT)
    assert not kw.UNIT.fullmatch('forprint-cf10-batchab-'+'a'*24+'.service')
    assert 'anchor_fd' in kw.KernelWitness.__dataclass_fields__
