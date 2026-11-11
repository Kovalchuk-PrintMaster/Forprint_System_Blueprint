"""V independent terminal evidence: strict, no implied production approval."""
from copy import deepcopy
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_terminal_proof_fence_v0_1 as t

def test_positive_is_disposable_only():
    r=t.coherent_lab(**t.fixture())
    assert r['lab_kernel_terminal_confirmed'] is True
    assert r['live_worker_kernel_terminal_proven'] is False
    assert r['terminal_ledger_written'] is False
    assert r['gates_open']==['G1','G2','G3','G4','G5']
    assert len(r['report_sha256'])==64

@pytest.mark.parametrize('part,key,value',[
  ('context','worker_claim_consumed',True),
  ('context','attachment_sha256','a'*63),
  ('start','main_pid',0),('start','uid',0),('start','gid',0),
  ('start','state','active/exited'),
  ('kernel','samples',['0']),('kernel','samples',['1','1','0']),
  ('kernel','observation','SYSTEMD_STATUS_ONLY'),
  ('kernel','arm_pid',123),
  ('retained','active','inactive'),('retained','substate','dead'),
  ('retained','main_pid',45),('retained','result','exit-code'),
  ('retained','exec_main_status',1),('retained','exit_type','main'),
  ('retained','remain_after_exit',False),
  ('final','active','failed'),('final','main_pid',1),
  ('final','stop_rc',1),('final','result','exit-code'),
])
def test_missing_proof_or_claim_holds(part,key,value):
    data=t.fixture();data[part][key]=value
    with pytest.raises(t.TerminalHold):t.coherent_lab(**data)

@pytest.mark.parametrize('part', ['context','start','kernel','retained','final'])
def test_extra_field_denied(part):
    data=t.fixture();data[part]['token']='bad'
    with pytest.raises(t.TerminalHold):t.coherent_lab(**data)

@pytest.mark.parametrize('part', ['start','kernel','retained','final'])
def test_invocation_mismatch_denied(part):
    data=t.fixture();data[part]['invocation_id']='d'*32
    with pytest.raises(t.TerminalHold):t.coherent_lab(**data)

def test_schema_and_hash_deterministic():
    assert t.coherent_lab(**t.fixture())==t.coherent_lab(**t.fixture())
