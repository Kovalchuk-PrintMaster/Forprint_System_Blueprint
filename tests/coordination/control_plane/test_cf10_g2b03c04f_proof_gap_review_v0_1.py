"""04F boundary regression: never promote metadata integrity into authority."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from scripts.coordination.control_plane import cf10_g2b03c04f_proof_gap_review_v0_1 as m

HEAD='e83afedd54b122017136743bcb3d15a6569bf942'
D_SHA='91db326d15c8e199ed7a41b0d3664d3abc7b5a23e8353c2f05d78112ff7d1134'
E_SHA='6123ff691ba9ac776216e534fea4d11070beaa0165ae63de96695f2012f3b455'
SOURCES={m.FOUR_E_SOURCE:'a'*64,m.FOUR_B_SOURCE:'b'*64}

def fixtures(submitted=0):
    d={'schema_version':m.FOUR_D_SCHEMA,'source_head':HEAD,
       'status':'OPERATOR_EVIDENCE_SURVEY_CAPTURED_WITH_GAPS_NON_AUTHORIZING',
       'proof_rows':8,'proofs_attested':0,'proofs_submitted':0,'blockers':[],
       'authority_granted':False,'independent_dynamic_coverage_verified':False,'launch_allowed':False}
    rows=[]
    for i,(ident,_) in enumerate(m.PROOFS):
        has=i<submitted
        rows.append({'id':ident,'intake_state':'HASH_VERIFIED_CONTENT_UNREVIEWED' if has else 'NOT_SUBMITTED',
                     'evidence_sha256':'c'*64 if has else None,
                     'evidence_reference':f'evidence/{ident}.json' if has else None,
                     'independent_verifier':'NOT_VERIFIED','attested':False})
    e={'schema_version':m.FOUR_E_SCHEMA,'source_head':HEAD,'frozen_04d_sha256':D_SHA,
       'frozen_04d_head':HEAD,
       'status':('OPERATOR_PROOF_INTAKE_INTEGRITY_REVIEW_NON_AUTHORIZING' if submitted
                 else 'OPERATOR_PROOF_INTAKE_READY_AWAITING_EXTERNAL_SUBMISSIONS_NON_AUTHORIZING'),
       'proofs_attested':0,'blockers':[],'authority_granted':False,'launch_allowed':False,
       'dynamic_coverage_verified':False,'content_and_authenticity_independently_verified':False,
       'signed_operator_decision_verified':False,'signature_cryptographically_verified':False,
       'worker_launched':False,'make_quarantine_removed':False,
       'matrix':rows,'requirement_count':8,'submission_integrity_count':submitted}
    return d,e

def evaluated(d,e):
    return m.classify(d,e,head=HEAD,d_pin=D_SHA,e_pin=E_SHA,exact_sources=SOURCES)

class BoundaryTests(unittest.TestCase):
    def test_clean_zero_submissions_is_not_authority(self):
        d,e=fixtures();out=evaluated(d,e)
        self.assertEqual(out['proof_requirements'],8)
        self.assertEqual(out['evidence_integrity_submitted'],0)
        for key in ('authority_granted','worker_launched','launch_allowed','dynamic_coverage_verified',
                    'content_authenticity_independently_attested','make_quarantine_removed'):
            self.assertIs(out[key],False)
        self.assertEqual(out['proofs_attested'],0)
        self.assertTrue(all(x['operator_next_action']=='SUBMIT_INDEPENDENT_EVIDENCE' for x in out['proof_matrix']))

    def test_all_hash_verified_still_not_attested(self):
        d,e=fixtures(8);out=evaluated(d,e)
        self.assertEqual(out['evidence_integrity_submitted'],8)
        self.assertEqual(out['proofs_attested'],0)
        self.assertIs(out['launch_allowed'],False)
        self.assertTrue(all(x['operator_next_action']=='INDEPENDENT_CONTENT_AND_AUTHENTICITY_REVIEW' for x in out['proof_matrix']))

    def test_partial_submission_distinction(self):
        d,e=fixtures(3);out=evaluated(d,e)
        self.assertEqual(out['evidence_integrity_submitted'],3)
        self.assertEqual([x['integrity_state'] for x in out['proof_matrix']].count('NOT_SUBMITTED'),5)

    def test_bad_source_head_fails(self):
        d,e=fixtures();e['source_head']='f'*40
        with self.assertRaises(m.ReviewBlocked):evaluated(d,e)

    def test_foreign_04d_pin_fails(self):
        d,e=fixtures();e['frozen_04d_sha256']='e'*64
        with self.assertRaises(m.ReviewBlocked):evaluated(d,e)

    def test_wrong_04e_status_fails(self):
        d,e=fixtures();e['status']='SUCCEEDED'
        with self.assertRaises(m.ReviewBlocked):evaluated(d,e)

    def test_04d_attested_claim_fails(self):
        d,e=fixtures();d['proofs_attested']=8
        with self.assertRaises(m.ReviewBlocked):evaluated(d,e)

    def test_04e_authority_claim_fails(self):
        d,e=fixtures();e['authority_granted']=True
        with self.assertRaises(m.ReviewBlocked):evaluated(d,e)

    def test_04e_launch_claim_fails(self):
        d,e=fixtures();e['launch_allowed']=True
        with self.assertRaises(m.ReviewBlocked):evaluated(d,e)

    def test_04e_matrix_reordered_fails(self):
        d,e=fixtures();e['matrix'].reverse()
        with self.assertRaises(m.ReviewBlocked):evaluated(d,e)

    def test_04e_count_mismatch_fails(self):
        d,e=fixtures(2);e['submission_integrity_count']=1
        with self.assertRaises(m.ReviewBlocked):evaluated(d,e)

    def test_fake_attested_row_fails(self):
        d,e=fixtures(1);e['matrix'][0]['attested']=True
        with self.assertRaises(m.ReviewBlocked):evaluated(d,e)

    def test_missing_source_pin_fails(self):
        d,e=fixtures()
        with self.assertRaises(m.ReviewBlocked):
            m.classify(d,e,head=HEAD,d_pin=D_SHA,e_pin=E_SHA,exact_sources={m.FOUR_E_SOURCE:'a'*64})

    def test_unknown_intake_state_fails(self):
        d,e=fixtures(1);e['matrix'][0]['intake_state']='ATTESTED'
        with self.assertRaises(m.ReviewBlocked):evaluated(d,e)

    @unittest.skipUnless(os.geteuid()==0,'requires root for private artifact metadata')
    def test_strict_manifest_and_file_permissions(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=root/'tmp'/'cf10_g2b03c04e_intake_20261030T120000000000Z'
            p.mkdir(parents=True,mode=0o700);os.chmod(p,0o700)
            contents={'report.json':b'{}\n','summary.txt':b'summary\n','submission_index_template.json':b'{}\n'}
            for name,blob in contents.items():
                x=p/name;x.write_bytes(blob);os.chmod(x,0o600)
            sha=lambda x:hashlib.sha256(x).hexdigest()
            manifest=''.join(sha(blob)+'  '+name+'\n' for name,blob in sorted(contents.items()))
            (p/'SHA256SUMS').write_text(manifest);os.chmod(p/'SHA256SUMS',0o600)
            out=m.verify_artifacts(root,'04E',p/'report.json',sha(contents['report.json']))
            self.assertEqual(out['report.json'],{})
            os.chmod(p/'report.json',0o644)
            with self.assertRaises(m.ReviewBlocked):m.verify_artifacts(root,'04E',p/'report.json',sha(contents['report.json']))

    def test_stale_historical_evidence_not_promoted(self):
        d,e=fixtures()
        out=m.classify(d,e,head='d'*40,predecessor_head=HEAD,d_pin=D_SHA,e_pin=E_SHA,exact_sources=SOURCES)
        self.assertFalse(out['source_freshness_reconciled'])
        self.assertEqual(out['frozen_predecessor_head'],HEAD)
        self.assertIn('CURRENT_HEAD_DIFFERS_FROM_FROZEN_EVIDENCE_HEAD',out['blockers'])
        self.assertFalse(out['launch_allowed'])

    @unittest.skipUnless(os.geteuid()==0,'requires root for private artifact metadata')
    def test_missing_manifest_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=root/'tmp'/'cf10_g2b03c04e_intake_20261030T120000000000Z'
            p.mkdir(parents=True,mode=0o700);os.chmod(p,0o700)
            contents={'report.json':b'{}\n','summary.txt':b'summary\n','submission_index_template.json':b'{}\n'}
            sha=lambda x:hashlib.sha256(x).hexdigest()
            for name,blob in contents.items():
                if name=='submission_index_template.json':continue
                x=p/name;x.write_bytes(blob);os.chmod(x,0o600)
            manifest=''.join(sha(blob)+'  '+name+'\n' for name,blob in sorted(contents.items()))
            (p/'SHA256SUMS').write_text(manifest);os.chmod(p/'SHA256SUMS',0o600)
            with self.assertRaises((m.ReviewBlocked,FileNotFoundError)):
                m.verify_artifacts(root,'04E',p/'report.json',sha(contents['report.json']))

    def test_invalid_head_is_rejected(self):
        d,e=fixtures()
        with self.assertRaises(m.ReviewBlocked):
            m.classify(d,e,head='xyz',d_pin=D_SHA,e_pin=E_SHA,exact_sources=SOURCES)

if __name__=='__main__':unittest.main()
