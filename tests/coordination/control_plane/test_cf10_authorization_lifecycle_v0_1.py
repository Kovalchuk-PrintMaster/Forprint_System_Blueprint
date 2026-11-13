import importlib.util
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('cf10_authorization_lifecycle_v0_1.py')
if not SOURCE.is_file():
    SOURCE = Path(__file__).resolve().parents[3] / 'scripts/coordination/control_plane/cf10_authorization_lifecycle_v0_1.py'
spec = importlib.util.spec_from_file_location('cf10_auth_test_module', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

NOW = datetime(2026,10,30,12,0,0,tzinfo=timezone.utc)
HEAD = 'e83afedd54b122017136743bcb3d15a6569bf942'

def decision(start, end, head=HEAD):
    return {'publication_commit': head, 'issued_at':start.isoformat(), 'expires_at':end.isoformat(),
            'signature_base64':'REDACTED'}

class LifecycleTests(unittest.TestCase):
    def test_expired(self):
        d=decision(NOW-timedelta(hours=5),NOW-timedelta(minutes=1))
        a=m.classify_window('writer_activation',d,head=HEAD,now=NOW)
        self.assertEqual(a['state'],'EXPIRED')
    def test_unbounded(self):
        d=decision(NOW-timedelta(days=3),NOW+timedelta(days=3))
        self.assertEqual(m.classify_window('writer_activation',d,head=HEAD,now=NOW)['state'],'INVALID_WINDOW')
    def test_future_issue(self):
        d=decision(NOW+timedelta(hours=1),NOW+timedelta(hours=2))
        self.assertEqual(m.classify_window('writer_activation',d,head=HEAD,now=NOW)['state'],'NOT_YET_VALID')
    def test_release_eight_hour_max(self):
        d=decision(NOW-timedelta(minutes=2),NOW+timedelta(hours=9))
        self.assertEqual(m.classify_window('worker_release',d,head=HEAD,now=NOW)['state'],'INVALID_WINDOW')
    def test_activation_one_day_max(self):
        d=decision(NOW-timedelta(hours=2),NOW+timedelta(hours=21))
        self.assertEqual(m.classify_window('writer_activation',d,head=HEAD,now=NOW)['state'],'WITHIN_WINDOW_NOT_AUTHORIZED')
    def test_naive_timestamp_invalid(self):
        d={'publication_commit':HEAD,'issued_at':'2026-10-30T10:00:00','expires_at':'2026-10-30T17:00:00'}
        self.assertEqual(m.classify_window('writer_activation',d,head=HEAD,now=NOW)['state'],'INVALID_WINDOW')
    def test_head_drift_outweighs_expiry(self):
        a=m.classify_window('writer_activation',decision(NOW-timedelta(hours=10),NOW-timedelta(hours=1),'a'*40),head=HEAD,now=NOW)
        r=m.classify_window('worker_release',None,head=HEAD,now=NOW)
        self.assertEqual(m.decide(a,r,gate={},release_gate={},make_quarantined=True)['state'],'SOURCE_REVIEW_AND_NEW_SIGNED_DECISIONS_REQUIRED')
    def test_expiry_simple_renewal_request(self):
        a=m.classify_window('writer_activation',decision(NOW-timedelta(hours=10),NOW-timedelta(hours=1)),head=HEAD,now=NOW)
        r=m.classify_window('worker_release',None,head=HEAD,now=NOW)
        self.assertEqual(m.decide(a,r,gate={},release_gate={},make_quarantined=True)['state'],'WRITER_ACTIVATION_RENEWAL_REVIEW_REQUIRED')
    def test_release_needs_renewal(self):
        a=m.classify_window('writer_activation',decision(NOW-timedelta(hours=3),NOW+timedelta(hours=3)),head=HEAD,now=NOW)
        r=m.classify_window('worker_release',decision(NOW-timedelta(hours=7),NOW-timedelta(minutes=1)),head=HEAD,now=NOW)
        self.assertEqual(m.decide(a,r,gate={},release_gate={},make_quarantined=True)['state'],'WORKER_RELEASE_RENEWAL_REVIEW_REQUIRED')
    def test_green_clock_not_authority(self):
        a=m.classify_window('writer_activation',decision(NOW-timedelta(hours=3),NOW+timedelta(hours=3)),head=HEAD,now=NOW)
        r=m.classify_window('worker_release',decision(NOW-timedelta(hours=3),NOW+timedelta(hours=3)),head=HEAD,now=NOW)
        x=m.decide(a,r,gate={'status':'PASS'},release_gate={'candidate_preconditions_pass':True},make_quarantined=True)
        self.assertEqual(x['state'],'INDEPENDENT_MAKE_REBIND_REQUIRED')
        self.assertFalse(x['worker_launch_allowed_by_this_tool'])
    def test_unknown_gate_blocked(self):
        a=m.classify_window('writer_activation',decision(NOW-timedelta(hours=1),NOW+timedelta(hours=1)),head=HEAD,now=NOW)
        x=m.decide(a,a,gate={'status':'UNKNOWN'},release_gate={'candidate_preconditions_pass':True},make_quarantined=False)
        self.assertEqual(x['state'],'CANONICAL_GATES_BLOCKED_REVIEW_REQUIRED')
    def test_private_request_idempotent_and_no_signatures(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); report={'source_head':HEAD,'writer_activation_window':m.classify_window('writer_activation',None,head=HEAD,now=NOW),
                                 'worker_release_window':m.classify_window('worker_release',None,head=HEAD,now=NOW),
                                 'next_step':{'state':'WRITER_ACTIVATION_RENEWAL_REVIEW_REQUIRED','operator_next_action':'review'}}
            p=m._store(root,report); before=(p/'request.json').read_bytes();self.assertEqual(p,m._store(root,report))
            self.assertEqual(before,(p/'request.json').read_bytes())
            self.assertNotIn(b'signature_base64',before)
            self.assertNotIn('time_remaining_seconds',str((p/'request.json').read_text()))
            self.assertIn('time_remaining_seconds', report['writer_activation_window']) # not mutated
            self.assertEqual(len(list((root/m.ROOT_REQUEST).glob('request_*'))),1)
    def test_tampered_request_fails(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); d={'source_head':HEAD,'writer_activation_window':m.classify_window('writer_activation',None,head=HEAD,now=NOW),
                 'worker_release_window':m.classify_window('worker_release',None,head=HEAD,now=NOW),
                 'next_step':{'state':'X','operator_next_action':'Y'}}
            folder=m._store(root,d); (folder/'request.json').write_text('bad')
            with self.assertRaises(ValueError):m._store(root,d)
    def test_missing_makefile_is_quarantined(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertTrue(m._make_quarantine(Path(t)))
    def test_canonical_output_redacts_nonprimitive(self):
        v=m._gate_view({'status':'BLOCKED','checks':{'secret':{'a':'b'},'state':'PASS'},'candidate_preconditions_pass':True})
        self.assertEqual(v['checks'],{'state':'PASS'})
        self.assertTrue(v['candidate_preconditions_pass'])
    def test_canonical_release_flag_false_is_not_a_success(self):
        self.assertFalse(m._gate_view({'status':'INSPECTED_NON_AUTHORIZING','candidate_preconditions_pass':1})['candidate_preconditions_pass'])
    def test_everything_green_still_not_launch_permission(self):
        now=NOW
        a=m.classify_window('writer_activation',decision(now-timedelta(minutes=1),now+timedelta(minutes=10)),head=HEAD,now=now)
        r=m.classify_window('worker_release',decision(now-timedelta(minutes=1),now+timedelta(minutes=10)),head=HEAD,now=now)
        x=m.decide(a,r,gate={'status':'PASS'},release_gate={'candidate_preconditions_pass':True},make_quarantined=False)
        self.assertEqual(x['state'],'EXPLICIT_RELEASE_REVIEW_REQUIRED')
        self.assertFalse(x['authority_granted_by_this_tool'])

if __name__ == '__main__': unittest.main()
