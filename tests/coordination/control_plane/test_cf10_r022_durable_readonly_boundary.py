import unittest
from pathlib import Path
from scripts.coordination.control_plane import cf10_durable_readonly_boundary_v0_1 as m

A='cf10-u180j-a051'
HEAD='a'*40; HANDOFF='b'*64
R='/srv/software_development/forprint-worker-runtime'
W=R+'/forprint_system_blueprint/worker-01/'+A+'/workspace/repo'
S=R+'/forprint_system_blueprint/control_plane/root_receipts'

def good():return dict(attempt_id=A,source_head=HEAD,handoff_sha256=HANDOFF,runtime_root=R,workspace_repo=W,receipt_store=S)

class DurableOnly(unittest.TestCase):
 def test_01_valid_fixed_paths_non_authorizing(self):
  a=m.validate_durable_scope(**good());self.assertEqual(a['status'],'PASS_NON_AUTHORIZING_DURABLE_SCOPE');self.assertFalse(a['worker_launched'])
 def test_02_no_tmp_runtime(self):
  with self.assertRaises(m.DurableBoundaryBlocked):m.validate_durable_scope(**{**good(),'runtime_root':'/tmp/x'})
 def test_03_no_project_tmp_workspace(self):
  with self.assertRaises(m.DurableBoundaryBlocked):m.validate_durable_scope(**{**good(),'workspace_repo':'/srv/software_development/forprint-project/forprint_system_blueprint/tmp/x'})
 def test_04_no_tmp_receipt(self):
  with self.assertRaises(m.DurableBoundaryBlocked):m.validate_durable_scope(**{**good(),'receipt_store':'/tmp/receipts'})
 def test_05_no_alternate_runtime_root(self):
  with self.assertRaises(m.DurableBoundaryBlocked):m.validate_durable_scope(**{**good(),'runtime_root':'/srv/software_development/alternative-runtime'})
 def test_06_no_other_attempt_workspace(self):
  with self.assertRaises(m.DurableBoundaryBlocked):m.validate_durable_scope(**{**good(),'workspace_repo':W.replace('a051','a049')})
 def test_07_no_bad_receipt_path(self):
  with self.assertRaises(m.DurableBoundaryBlocked):m.validate_durable_scope(**{**good(),'receipt_store':R+'/forprint_system_blueprint/worker-01/'+A+'/workspace/repo/receipts'})
 def test_08_no_path_traversal(self):
  with self.assertRaises(m.DurableBoundaryBlocked):m.validate_durable_scope(**{**good(),'workspace_repo':W+'/../input'})
 def test_09_no_invalid_head(self):
  with self.assertRaises(m.DurableBoundaryBlocked):m.validate_durable_scope(**{**good(),'source_head':'invalid'})
 def test_10_no_replay_scope(self):
  a=m.validate_durable_scope(**good());a['release_allowed']=True
  with self.assertRaises(m.DurableBoundaryBlocked):m.review_ledger_only(scope=a,receipt=None,ledger_rows=[])
 def test_11_join_never_authorizes(self):
  a=m.validate_durable_scope(**good());r=m.review_ledger_only(scope=a,receipt=None,ledger_rows=[])
  for k in ('release_allowed','worker_launched','production_cutover_completed','resume_allowed'):
   self.assertFalse(r[k])
 def test_12_import_not_from_zip(self):
  file=Path(m.__file__).resolve()
  self.assertEqual(file.parent, file.parents[3]/'scripts/coordination/control_plane')
  self.assertNotIn('.zip/',file.as_posix())
 def test_13_no_ledger_mutation_or_process_spawn(self):
  import inspect
  t=inspect.getsource(m)
  for bad in ('subprocess.Popen(', 'systemd-run', 'os.system(', 'append_record(', 'sudo -v'):
   self.assertNotIn(bad,t)
 def test_14_wrong_type(self):
  with self.assertRaises(m.DurableBoundaryBlocked):m.validate_durable_scope(**{**good(),'attempt_id':None})
 def test_15_bad_receipt_symlink_or_alias(self):
  with self.assertRaises(m.DurableBoundaryBlocked):m.validate_durable_scope(**{**good(),'receipt_store':S+'/..'})

if __name__=='__main__': unittest.main()
