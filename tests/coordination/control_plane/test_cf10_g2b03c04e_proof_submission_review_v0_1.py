"""Synthetic G2b03C04E fail-closed tests; never read /etc or launch a Worker."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

SOURCE=Path(__file__).resolve().parents[3]/'scripts/coordination/control_plane/cf10_g2b03c04e_proof_submission_review_v0_1.py'
spec=importlib.util.spec_from_file_location('cf10_04e',SOURCE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
HEAD='0c6dfc9fe8ce614739b162a118b0802fc573a4bf'
IDS=['COMPLETE_CURRENT_WRITER_ENTRYPOINTS','ALL_WRITER_PROCESSES_ENROLLED','RUNNING_WRITER_RESTART_OR_DRAIN',
'SCHEDULED_MANUAL_REMOTE_WRITERS','CANONICAL_LOCK_AND_LEDGER_EXCLUSIVITY','INDEPENDENT_DYNAMIC_PROOF',
'SIGNED_COVERAGE_APPROVAL','RUNTIME_BINDING_AND_QUARANTINE_ACCEPTANCE']

def prior():return {'source_head':m.FOUR_D_HEAD,'status':'OPERATOR_EVIDENCE_SURVEY_CAPTURED_WITH_GAPS_NON_AUTHORIZING',
                  'authority_granted':False,'independent_dynamic_coverage_verified':False}
def template():return {'requirements':[{'id':s,'required_evidence':'text'} for s in IDS]}
def row(i=0,rel='evidence/p01.json',h='a'*64):return {'requirement_id':IDS[i],'artifact_rel':rel,'sha256':h,'submitter_ref':'external_operator_submission_not_approval'}
def index(sub=None,head=HEAD):return {'schema_version':m.INDEX_SCHEMA,'source_head':head,'frozen_04d_sha256':m.FOUR_D_SHA,'submissions':[] if sub is None else sub}

class Tests(unittest.TestCase):
 def classify(self,prior_doc=None,proof=None,source=True,head=HEAD):
  return m.classify(prior=prior_doc if prior_doc is not None else prior(),template=template(),head=head,
                    self_published=source,submissions=[] if proof is None else proof,submission_state='NOT_PROVIDED')
 def assert_non_authorizing(self,doc):
  for x in ('proofs_attested','dynamic_coverage_verified','signature_cryptographically_verified',
            'runtime_binding_authorized','make_quarantine_removed','launch_allowed','ledger_append_allowed',
            'ledger_mutated','worker_launched','authority_granted'):
   self.assertIn(doc[x],(False,0),x)
 def test_empty_intake_ready_but_unattested(self):
  doc=self.classify();self.assertEqual(doc['status'],'OPERATOR_PROOF_INTAKE_READY_AWAITING_EXTERNAL_SUBMISSIONS_NON_AUTHORIZING')
  self.assertEqual(doc['submission_integrity_count'],0);self.assertEqual(doc['requirement_count'],8)
  self.assertTrue(all(r['intake_state']=='NOT_SUBMITTED' for r in doc['matrix']))
  self.assert_non_authorizing(doc)
 def test_one_hash_only_submission_still_not_attested(self):
  doc=self.classify(proof=[{'requirement_id':IDS[0],'artifact_rel':'evidence/p01.json','evidence_sha256':'a'*64}])
  self.assertEqual(doc['status'],'OPERATOR_PROOF_INTAKE_INTEGRITY_REVIEW_NON_AUTHORIZING')
  self.assertEqual(doc['submission_integrity_count'],1)
  self.assertEqual(doc['matrix'][0]['intake_state'],'HASH_VERIFIED_CONTENT_UNREVIEWED')
  self.assert_non_authorizing(doc)
 def test_eight_hash_only_submissions_never_coverage(self):
  rows=[{'requirement_id':k,'artifact_rel':f'evidence/p{i}.txt','evidence_sha256':'a'*64} for i,k in enumerate(IDS)]
  doc=self.classify(proof=rows);self.assertEqual(doc['submission_integrity_count'],8);self.assert_non_authorizing(doc)
 def test_false_previous_authority_blocks(self):
  p=prior();p['authority_granted']=True
  self.assertIn('FROZEN_04D_PREDECESSOR_NOT_VALID',self.classify(prior_doc=p)['blockers'])
 def test_false_previous_dynamic_blocks(self):
  p=prior();p['independent_dynamic_coverage_verified']=True
  self.assertIn('FROZEN_04D_PREDECESSOR_NOT_VALID',self.classify(prior_doc=p)['blockers'])
 def test_wrong_previous_head_blocks(self):
  p=prior();p['source_head']='b'*40
  self.assertIn('FROZEN_04D_PREDECESSOR_NOT_VALID',self.classify(prior_doc=p)['blockers'])
 def test_wrong_previous_status_blocks(self):
  p=prior();p['status']='ATTESTED'
  self.assertIn('FROZEN_04D_PREDECESSOR_NOT_VALID',self.classify(prior_doc=p)['blockers'])
 def test_unpublished_source_blocks(self):
  self.assertIn('SOURCE_HEAD_NOT_EXACT_PUBLISHED',self.classify(source=False)['blockers'])
 def test_invalid_head_blocks(self):
  self.assertIn('SOURCE_HEAD_NOT_EXACT_PUBLISHED',self.classify(head='not-head')['blockers'])
 def test_duplicate_proofs_block(self):
  r={'requirement_id':IDS[0],'artifact_rel':'a','evidence_sha256':'a'*64}
  self.assertIn('SUBMISSION_SET_INVALID',self.classify(proof=[r,r])['blockers'])
 def test_check_index_valid(self):
  self.assertEqual(len(m.check_index(index([row()]),head=HEAD,known_ids=IDS)),1)
 def test_empty_index_valid(self):
  self.assertEqual(m.check_index(index(),head=HEAD,known_ids=IDS),[])
 def test_wrong_head_index_rejected(self):
  with self.assertRaises(m.IntakeBlocked):m.check_index(index(head='f'*40),head=HEAD,known_ids=IDS)
 def test_unknown_id_rejected(self):
  r=row();r['requirement_id']='SOMETHING_ELSE'
  with self.assertRaises(m.IntakeBlocked):m.check_index(index([r]),head=HEAD,known_ids=IDS)
 def test_duplicate_id_rejected(self):
  with self.assertRaises(m.IntakeBlocked):m.check_index(index([row(),row(0,'evidence/p02.json')]),head=HEAD,known_ids=IDS)
 def test_duplicate_path_rejected(self):
  with self.assertRaises(m.IntakeBlocked):m.check_index(index([row(),row(1)]),head=HEAD,known_ids=IDS)
 def test_forged_attestation_field_rejected(self):
  r=row();r['attested']=True
  with self.assertRaises(m.IntakeBlocked):m.check_index(index([r]),head=HEAD,known_ids=IDS)
 def test_extra_index_field_rejected(self):
  doc=index();doc['authority_granted']=True
  with self.assertRaises(m.IntakeBlocked):m.check_index(doc,head=HEAD,known_ids=IDS)
 def test_invalid_digest_rejected(self):
  with self.assertRaises(m.IntakeBlocked):m.check_index(index([row(h='none')]),head=HEAD,known_ids=IDS)
 def test_invalid_submitter_ref_rejected(self):
  r=row();r['submitter_ref']=''
  with self.assertRaises(m.IntakeBlocked):m.check_index(index([r]),head=HEAD,known_ids=IDS)
 def test_nine_rows_rejected(self):
  with self.assertRaises(m.IntakeBlocked):m.check_index(index([row()]*9),head=HEAD,known_ids=IDS)
 def test_no_external_trust_path(self):
  for path in ('/etc/forprint/signing.json','../../x','evidence/../x','evidence/.hidden/../x','evidence/abc.key','evidence/x\\secret.json'):
   with self.subTest(path=path),self.assertRaises(m.IntakeBlocked):m.safe_relative(path)
 def test_optional_requires_exact_index_path(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   with self.assertRaises(m.IntakeBlocked):m.optional_submission(root,head=HEAD,known_ids=IDS,index_path=root/'other.json',index_sha='a'*64)
 def test_optional_partial_inputs_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   with self.assertRaises(m.IntakeBlocked):m.optional_submission(root,head=HEAD,known_ids=IDS,index_path=root/m.INDEX_REL,index_sha=None)
 def test_no_submission_mode_needs_no_input(self):
  x=m.optional_submission(Path('/nonexistent'),head=HEAD,known_ids=IDS,index_path=None,index_sha=None)
  self.assertEqual(x,([], 'NOT_PROVIDED'))
 def test_optional_private_hash_verification(self):
  if os.getuid()!=0:self.skipTest('test root-owned path on root only')
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);target=root/m.INDEX_ROOT_REL
   (target/'evidence').mkdir(parents=True,mode=0o700)
   target.chmod(0o700);(target/'evidence').chmod(0o700)
   artifact=target/'evidence/p01.json';raw=b'{"proven":false}\n';artifact.write_bytes(raw);artifact.chmod(0o600)
   data=index([row(h=hashlib.sha256(raw).hexdigest())]);enc=(json.dumps(data)+'\n').encode()
   (target/'index.json').write_bytes(enc);(target/'index.json').chmod(0o600)
   checked,state=m.optional_submission(root,head=HEAD,known_ids=IDS,index_path=target/'index.json',index_sha=hashlib.sha256(enc).hexdigest())
   self.assertEqual(len(checked),1);self.assertEqual(checked[0]['integrity'],'SHA256_MATCH_ONLY_NOT_ATTESTED')
   self.assertIn('UNVERIFIED_CONTENT',state)
 def test_wrong_artifact_hash_denied(self):
  if os.getuid()!=0:self.skipTest('test root-owned path on root only')
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);target=root/m.INDEX_ROOT_REL
   (target/'evidence').mkdir(parents=True,mode=0o700)
   target.chmod(0o700);(target/'evidence').chmod(0o700)
   artifact=target/'evidence/p01.json';artifact.write_text('other');artifact.chmod(0o600)
   data=index([row()]);enc=json.dumps(data).encode()
   (target/'index.json').write_bytes(enc);(target/'index.json').chmod(0o600)
   with self.assertRaises(m.IntakeBlocked):m.optional_submission(root,head=HEAD,known_ids=IDS,index_path=target/'index.json',index_sha=hashlib.sha256(enc).hexdigest())
 def test_private_file_symlink_denied(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'p';p.write_text('x');q=Path(t)/'q';q.symlink_to(p)
   with self.assertRaises(m.IntakeBlocked):m.safe_read(q)
 def test_private_file_broad_mode_denied(self):
  if os.getuid()!=0:self.skipTest('requires uid 0')
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);root.chmod(0o700);p=root/'p';p.write_text('x');p.chmod(0o644)
   with self.assertRaises(m.IntakeBlocked):m.safe_read(p)
 def test_private_file_multiple_links_denied(self):
  if os.getuid()!=0:self.skipTest('requires uid 0')
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);root.chmod(0o700);p=root/'p';p.write_text('x');p.chmod(0o600);(root/'q').hardlink_to(p)
   with self.assertRaises(m.IntakeBlocked):m.safe_read(p)
 def test_frozen_report_wrong_path_denied(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with self.assertRaises(m.IntakeBlocked):m.frozen_04d(r,r/'other.json',m.FOUR_D_SHA)
 def test_frozen_report_wrong_sha_denied(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with self.assertRaises(m.IntakeBlocked):m.frozen_04d(r,r/m.FOUR_D_REL,'0'*64)
 def test_save_create_only_and_template(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'tmp').mkdir()
   doc=self.classify()
   out,s=m.save(root,doc)
   self.assertEqual(len(s),64)
   idx=json.loads((out/'submission_index_template.json').read_text())
   self.assertEqual(idx['source_head'],HEAD);self.assertEqual(idx['submissions'],[])
   self.assertEqual((out/'report.json').stat().st_mode&0o777,0o600)
   self.assert_non_authorizing(json.loads((out/'report.json').read_text()))
 def test_save_symlink_tmp_denied(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'real').mkdir();(root/'tmp').symlink_to(root/'real')
   with self.assertRaises(m.IntakeBlocked):m.save(root,self.classify())

if __name__=='__main__':unittest.main()
