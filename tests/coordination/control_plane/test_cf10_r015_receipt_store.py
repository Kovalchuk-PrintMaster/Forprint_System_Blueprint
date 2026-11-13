import os,tempfile,unittest,json
from pathlib import Path
from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as store
A='cf10-u180j-a051';H='a'*40;S='b'*64
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.dir=Path(self.tmp.name)/'store';self.dir.mkdir(mode=0o700)
  self.kw={'private_store':self.dir,'attempt_id':A,'head':H,'handoff_sha256':S}
 def tearDown(self):self.tmp.cleanup()
 def c(self):return store.claim(**self.kw)
 def test_01_claim(self):
  self.assertTrue(self.c()['state']=='CLAIM_CONSUMED')
 def test_02_no_retry(self):
  self.c()
  with self.assertRaises(store.ReceiptBlocked):self.c()
 def test_03_events(self):
  self.c();store.append_observation(private_store=self.dir,attempt_id=A,expected_head=H,event='LAUNCH_REQUESTED');r=store.observe(private_store=self.dir,attempt_id=A,expected_head=H);self.assertEqual(r['event_count'],1)
 def test_04_chain_tamper(self):
  self.c();row=store.append_observation(private_store=self.dir,attempt_id=A,expected_head=H,event='STOP_REQUESTED')
  p=self.dir/A/'event_0001.json';data=json.loads(p.read_text());data['event']='REVIEW_REQUIRED';p.write_text(json.dumps(data))
  with self.assertRaises(store.ReceiptBlocked):store.observe(private_store=self.dir,attempt_id=A,expected_head=H)
 def test_05_wrong_head(self):
  self.c()
  with self.assertRaises(store.ReceiptBlocked):store.observe(private_store=self.dir,attempt_id=A,expected_head='c'*40)
 def test_06_wrong_root_mode(self):
  self.dir.chmod(0o755)
  with self.assertRaises(store.ReceiptBlocked):self.c()
 def test_07_no_parent_overwrite(self):
  self.c();self.assertTrue((self.dir/A/'0000_claim.json').exists())
 def test_08_event_gap(self):
  self.c();store.append_observation(private_store=self.dir,attempt_id=A,expected_head=H,event='SERVICE_OBSERVED')
  (self.dir/A/'event_0001.json').rename(self.dir/A/'event_0002.json')
  with self.assertRaises(store.ReceiptBlocked):store.observe(private_store=self.dir,attempt_id=A,expected_head=H)
 def test_09_non_authorizing(self):
  self.c();r=store.observe(private_store=self.dir,attempt_id=A,expected_head=H);self.assertFalse(r['worker_result_accepted'])
 def test_10_duplicate_chain_event(self):
  self.c();store.append_observation(private_store=self.dir,attempt_id=A,expected_head=H,event='SERVICE_OBSERVED')
  store.append_observation(private_store=self.dir,attempt_id=A,expected_head=H,event='REVIEW_REQUIRED')
  self.assertEqual(store.observe(private_store=self.dir,attempt_id=A,expected_head=H)['event_count'],2)
 def test_11_no_unclaimed_event(self):
  with self.assertRaises(Exception):store.append_observation(private_store=self.dir,attempt_id=A,expected_head=H,event='STOP_REQUESTED')
 def test_12_invalid_attempt(self):
  with self.assertRaises(store.ReceiptBlocked):store.claim(**{**self.kw,'attempt_id':'../../etc'})
 def test_13_symlink_parent(self):
  link=Path(self.tmp.name)/'link';link.symlink_to(self.dir,target_is_directory=True)
  with self.assertRaises(store.ReceiptBlocked):store.claim(**{**self.kw,'private_store':link})
 def test_14_lock_permissions(self):
  self.c();p=self.dir/A/'observation.lock';p.write_text('bad');p.chmod(0o644)
  with self.assertRaises(store.ReceiptBlocked):store.append_observation(private_store=self.dir,attempt_id=A,expected_head=H,event='STOP_REQUESTED')
if __name__=='__main__':unittest.main()
