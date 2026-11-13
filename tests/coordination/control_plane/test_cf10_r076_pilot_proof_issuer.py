"""R076 historical-proof replay controls; no live issue or claim in test suite."""
from __future__ import annotations
from unittest import TestCase, main
from unittest.mock import patch
from pathlib import Path
from types import ModuleType
import hashlib
import io
import json
import os
import sys
import zipfile

from scripts.coordination.control_plane import cf10_r076_historical_evidence_v0_1 as ev
from scripts.coordination.control_plane import cf10_r076_pilot_proof_issuer_v0_1 as issuer


def doc_bytes(obj):
    return (json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()


def zip_bytes(items):
    file=io.BytesIO()
    with zipfile.ZipFile(file,'w',compression=zipfile.ZIP_STORED) as z:
        for name,content in items:z.writestr(name,content)
    return file.getvalue()


class HistoricalVerifierTests(TestCase):
    def test_historical_scope_exact_and_not_fresh(self):
        self.assertEqual(ev.ATT,'cf10-u180j-a053')
        self.assertEqual(ev.HEAD,'e790ed596758c9ebfe101c6d5892d64901a95134')
        self.assertEqual(len(ev.SRC),4)
        self.assertTrue(all(len(v)==64 for v in ev.SRC.values()))

    def test_strict_json_duplicate_keys_rejected(self):
        with self.assertRaises(ev.EvidenceBlocked):ev.strict_json(b'{"x":1,"x":2}')

    def test_zip_duplicate_rejected(self):
        z=io.BytesIO()
        with zipfile.ZipFile(z,'w') as f:
            with __import__('warnings').catch_warnings():
                __import__('warnings').simplefilter('ignore',UserWarning)
                f.writestr('x',b'a');f.writestr('x',b'b')
        with self.assertRaises(ev.EvidenceBlocked):ev.unzip(z.getvalue())

    def test_zip_path_traversal_rejected(self):
        for bad in ('../secret','/etc/shadow','x\\y','.hidden'):
            with self.subTest(bad=bad),self.assertRaises(ev.EvidenceBlocked):
                ev.unzip(zip_bytes([(bad,b'x')]))

    def test_zip_tamper_fails_crc(self):
        raw=zip_bytes([('x.txt',b'original-bytes-strong-check')])
        changed=raw.replace(b'original-bytes-strong-check',b'altered!-bytes-strong-check')
        self.assertNotEqual(raw,changed)
        with self.assertRaises((ValueError,ev.EvidenceBlocked,zipfile.BadZipFile)):
            ev.unzip(changed)

    def test_exact_sha_manifest_required(self):
        files={'SHA256SUMS':b'0'*64+b'  a\n','a':b'data'}
        with self.assertRaises(ev.EvidenceBlocked):ev.verify_shas(files,'SHA256SUMS')

    def test_wrong_root_archive_sha_never_accepted(self):
        self.assertNotEqual(ev.sha(b'synthetic-archive'),ev.SRC['R072C_ORIGINAL.zip'])


class IssuerContractTests(TestCase):
    def setUp(self):
        self.ctx=issuer.Context(attempt='cf10-u180j-a054',head='b'*40)

    def test_pilot_identity_is_not_history(self):
        self.assertNotEqual(self.ctx.attempt,issuer.HISTORICAL_ATTEMPT)
        self.assertEqual(self.ctx.task,ev.TASK)
        self.assertNotEqual(self.ctx.head,ev.HEAD)

    def test_exact_all_observations_false_fails(self):
        facts={'canonical_cycle_ready':True,'source_guard_verified':True,
               'frozen_input_current':True,'writer_protocol_enforced':True,
               'root_one_shot_claim_unconsumed':False,'canonical_ledger_unstarted':True,
               'systemd_worker_quiescent':True}
        observations=issuer.all_observations({'gates':facts})
        self.assertFalse(observations['SOURCE_AND_WRITER_BOUNDARY']['one_shot_claim_unconsumed'])
        self.assertEqual(len(observations),4)

    def test_canonical_record_contract_if_available(self):
        try:
            from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as r046
            from scripts.coordination.control_plane import cf10_r047_pilot_proof_lineage_v0_1 as r047
        except ImportError:
            self.skipTest('canonical project R046/R047 available on s01')
        facts={x:True for x in ('canonical_cycle_ready','source_guard_verified','frozen_input_current',
                                 'writer_protocol_enforced','root_one_shot_claim_unconsumed',
                                 'canonical_ledger_unstarted','systemd_worker_quiescent')}
        host={'gates':facts}
        dossier={'schema': 'cf10_r073_disposable_evidence_byte_review_v0_1'}
        records, release_name=issuer.build_records(dossier,host,'2026-11-04T00:00:00+00:00',self.ctx)
        self.assertEqual(len(records),11)
        self.assertEqual(len([n for n in records if n.startswith('raw_source_')]),4)
        self.assertEqual(len([n for n in records if n.startswith('proof_')]),4)
        release=json.loads(records[release_name]);self.assertEqual(release['attempt_id'],self.ctx.attempt)
        self.assertEqual(set(release['proofs']),set(r046.PROOF_TYPES))
        self.assertEqual(r047.REQUIRED_OBSERVATIONS,
                         {k:frozenset(v) for k,v in ev.FIELDS.items()})
        for name,blob in records.items():
            self.assertLess(len(blob),32768)
            self.assertEqual(blob,doc_bytes(json.loads(blob)))
        review=json.loads(next(v for k,v in records.items() if k.startswith('r076_operator_review_')))
        self.assertTrue(review['historical_evidence_not_fresh_for_new_head'])
        self.assertFalse(review['external_producer_cryptographically_authenticated'])
        self.assertEqual(review['historical_original_evidence_attempt'],ev.ATT)
        self.assertTrue(review['r075_actual_frozen_manifest_preclaim_reverified'])

    def test_history_mode_never_issues(self):
        def fake(p):return {'schema':'cf10_r073_disposable_evidence_byte_review_v0_1','attempt_id':ev.ATT}
        with patch.object(issuer,'ROOT',Path.cwd()),patch.object(issuer,'historical_folder',return_value=Path.cwd()),\
             patch.object(issuer.evidence,'proof_evidence',side_effect=fake),\
             patch.object(issuer.os,'geteuid',return_value=0),patch.object(issuer,'issue_records') as issue:
            self.assertEqual(issuer.main(['--mode','history']),0)
            issue.assert_not_called()

    def test_historical_attempt_reissue_denied(self):
        with patch.object(issuer,'ROOT',Path.cwd()),patch.object(issuer,'historical_folder',return_value=Path.cwd()),\
             patch.object(issuer.evidence,'proof_evidence',return_value={
                 'schema':'cf10_r073_disposable_evidence_byte_review_v0_1','attempt_id':ev.ATT}),\
             patch.object(issuer.os,'geteuid',return_value=0),patch.object(issuer,'issue_records') as issue:
            self.assertEqual(issuer.main(['--mode','inspect','--attempt',ev.ATT]),2)
            issue.assert_not_called()

    def test_exact_operator_confirmation_not_data_authentication(self):
        self.assertIn('NONCRYPTO',issuer.CONFIRM)
        self.assertIn('NO_WORKER',issuer.CONFIRM)
        self.assertIn('HISTORICAL',issuer.CONFIRM)

    def test_no_programmatic_launch_targets(self):
        import inspect
        source=inspect.getsource(issuer)
        self.assertNotIn('systemd-run',source)
        self.assertNotIn('launch_once(',source)
        self.assertNotIn('os.system(',source)
        self.assertNotIn('subprocess.Popen(',source)
        self.assertIn('os.O_EXCL',source)
        self.assertIn('console.decision(',source)
        self.assertIn('pilot.assert_owner_preclaim_runtime(',source)

if __name__=='__main__':main()
