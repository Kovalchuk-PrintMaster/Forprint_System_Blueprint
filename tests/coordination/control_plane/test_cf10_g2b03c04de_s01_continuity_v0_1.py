"""S01-current vs frozen predecessor boundaries; pure synthetic tests, no system effects."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[3]
def load(name):
    path=BASE/'scripts/coordination/control_plane'/name
    spec=importlib.util.spec_from_file_location(name.removesuffix('.py'),path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
D=load('cf10_g2b03c04d_operator_evidence_survey_v0_1.py')
E=load('cf10_g2b03c04e_proof_submission_review_v0_1.py')
HEAD='b8b2b6d6b62378cdc86a113b570f00772c4f7611'
OTHER='e'*40
SHA='f'*64
REQ=(('COMPLETE_CURRENT_WRITER_ENTRYPOINTS','a'),)

def prior04c(head=HEAD):
    return {'schema_version':'cf10_g2b03c04c_evidence_readback_v0_1','source_head':head,
            'status':'INDEPENDENT_EVIDENCE_READBACK_READY_FOR_OPERATOR_PROOFS_NON_AUTHORIZING',
            'blockers':[],'proofs_submitted':0,'proofs_attested':0,'authority_granted':False,
            'independent_dynamic_coverage_verified':False,'launch_allowed':False,
            'operator_proof_intake':[{'id':'COMPLETE_CURRENT_WRITER_ENTRYPOINTS',
                'operator_evidence_required':'a','state':'NOT_SUBMITTED',
                'independent_evidence_id':None,'evidence_sha256':None,'review_authority':'NOT_VERIFIED'}]}

class Continuity(unittest.TestCase):
    def test_d_current_exact_locator(self):
        root=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
        item=root/'tmp/cf10_g2b03c04c_readback_20261030T103001123456Z/report.json'
        self.assertTrue(D.report_locator_allowed(root,item,SHA))
        self.assertFalse(D.report_locator_allowed(root,item,'bad'))
        self.assertFalse(D.report_locator_allowed(root,root/'tmp/other/report.json',SHA))
        self.assertFalse(D.report_locator_allowed(root,root/'tmp/cf10_g2b03c04c_readback_20261030T103001123456Z/extra.json',SHA))
    def test_d_legacy_path_frozen_to_original_sha(self):
        root=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
        self.assertTrue(D.report_locator_allowed(root,root/D.PRIOR_REL,D.PRIOR_SHA))
        self.assertFalse(D.report_locator_allowed(root,root/D.PRIOR_REL,SHA))
    def test_d_rejects_cross_head(self):
        self.assertIn('FROZEN_04C_PREDECESSOR_NOT_VERIFIED',D.validate_prior(prior04c(OTHER),REQ,HEAD))
    def test_d_accepts_current_non_authorizing(self):
        self.assertEqual(D.validate_prior(prior04c(),REQ,HEAD),[])
        schedule={'matches':[],'findings':[],'full_scheduler_scope_proven':False,
                  'remote_or_manual_writers_proven':False,'external_authority_payloads_read':False}
        live={'processes':{'state':'OBSERVED','unreadable_count':0,'absence_of_processes_proven':False},
              'ledger':{'state':'DIRECTORY'},'mount':{'state':'OBSERVED','network_or_fuse_surface':False}}
        r=D.classify(prior=prior04c(),head=HEAD,requirements=REQ,schedule=schedule,live=live,
                     source_ok=True,prior_expected_head=HEAD,prior_report_sha=SHA)
        self.assertEqual(r['status'],'OPERATOR_EVIDENCE_SURVEY_CAPTURED_WITH_GAPS_NON_AUTHORIZING')
        self.assertEqual(r['proof_template']['predecessor_report_sha256'],SHA)
        self.assertFalse(r['authority_granted'])
    def test_e_locator_current_and_legacy(self):
        root=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
        item=root/'tmp/cf10_g2b03c04d_survey_20261030T103001123456Z/report.json'
        self.assertTrue(E.report_locator_allowed(root,item,SHA))
        self.assertFalse(E.report_locator_allowed(root,item,'bad'))
        self.assertTrue(E.report_locator_allowed(root,root/E.FOUR_D_REL,E.FOUR_D_SHA))
        self.assertFalse(E.report_locator_allowed(root,root/E.FOUR_D_REL,SHA))
    def test_e_current_source_head_and_sha(self):
        prior={'source_head':HEAD,'status':'OPERATOR_EVIDENCE_SURVEY_CAPTURED_WITH_GAPS_NON_AUTHORIZING',
               'authority_granted':False,'independent_dynamic_coverage_verified':False}
        template={'requirements':[{'id':str(i),'required_evidence':'x'} for i in range(8)]}
        r=E.classify(prior=prior,template=template,head=HEAD,self_published=True,submissions=[],
                     submission_state='NOT_PROVIDED',predecessor_head=HEAD,predecessor_sha=SHA)
        self.assertEqual(r['status'],'OPERATOR_PROOF_INTAKE_READY_AWAITING_EXTERNAL_SUBMISSIONS_NON_AUTHORIZING')
        self.assertEqual(r['frozen_04d_sha256'],SHA)
        self.assertFalse(r['launch_allowed'])
        prior['source_head']=OTHER
        r=E.classify(prior=prior,template=template,head=HEAD,self_published=True,submissions=[],
                     submission_state='NOT_PROVIDED',predecessor_head=HEAD,predecessor_sha=SHA)
        self.assertIn('FROZEN_04D_PREDECESSOR_NOT_VALID',r['blockers'])
    def test_e_submission_index_binds_actual_04d_sha(self):
        ids=['id']
        data={'schema_version':E.INDEX_SCHEMA,'source_head':HEAD,'frozen_04d_sha256':SHA,'submissions':[]}
        self.assertEqual(E.check_index(data,head=HEAD,known_ids=ids,frozen_sha=SHA),[])
        with self.assertRaises(E.IntakeBlocked):
            E.check_index(data,head=HEAD,known_ids=ids,frozen_sha='d'*64)
    def test_e_zero_submission_does_not_read_evidence(self):
        x=E.optional_submission(Path('/nonexistent'),head=HEAD,known_ids=[],
                                index_path=None,index_sha=None,frozen_sha=SHA)
        self.assertEqual(x,([], 'NOT_PROVIDED'))

if __name__=='__main__': unittest.main()
