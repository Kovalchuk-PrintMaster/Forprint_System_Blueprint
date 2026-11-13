"""Isolated, synthetic tests for G2b03C03A. No external state or signing."""
from pathlib import Path
import importlib.util
import tempfile
import unittest

S=Path(__file__).resolve().parents[3]/'scripts/coordination/control_plane/cf10_g2b03c03a_writer_delta_v0_1.py'
spec=importlib.util.spec_from_file_location('delta',S)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
HEAD='2e9583d2c95bbd6da5a4761cb4a2010acf1768c4'
OLD=''.join('context_line_%d\n'%i for i in range(150))
BLOCK1='\n'.join(['# CF10_B3_P2_INDEPENDENT_PRELAUNCH_READBACK_V0_1_START',
   'def _resolve_b3_trusted_readback(',
   '    training.readback.verify_frozen_selection(',
   *('    example_line_%d'%i for i in range(50)),
   '# CF10_B3_P2_INDEPENDENT_PRELAUNCH_READBACK_V0_1_END',''])+'\n'
BLOCK2=('    trusted_readback_selection = _resolve_b3_trusted_readback(\n'+
        '        prepared_execution=prepared_execution,\n'+
        '        root=canonical,\n'+
        '        expected_attempt_id=attempt_id,\n'+
        '        expected_task_prompt_id=task_prompt_id,\n'+
        '        explicit_dispatch_decision=decision,\n'+
        '    )\n')
BLOCK3='    "validation_readback_selection": trusted_readback_selection,\n'

def pair():
    lines=OLD.splitlines(keepends=True)
    lines[20:20]=BLOCK1.splitlines(keepends=True)
    lines[80:80]=BLOCK2.splitlines(keepends=True)
    lines[125:125]=[BLOCK3]
    return ''.join(lines).encode(),OLD.encode()


def live():
    return {'status':'LIVE_OBSERVATION_REVIEW_REQUIRED_NON_AUTHORIZING', 'blockers':[],
            'source_head':HEAD,'authority_granted':False,'dynamic_coverage_verified':False,
            'observed_s01_runtime':{'tracked_writers':[m.REL,'ledger.py'],
                  'writer_source_comparison':{m.REL:False,'ledger.py':True}}}

class ReviewTests(unittest.TestCase):
    def test_positive_only_review(self):
        new,old=pair();d=m.compare_published_sources(new,old)
        self.assertEqual(d['classification'],'B3_INSERTION_ONLY_COMPATIBILITY_REVIEW_REQUIRED')
        x=m.classify(live(),d,head=HEAD,current_sha=m.digest(new),pinned_sha=m.digest(old))
        self.assertEqual(x['status'],'WRITER_DELTA_COMPATIBILITY_REVIEW_REQUIRED_NON_AUTHORIZING')
        for flag in ('authority_granted','worker_launched','current_runtime_coverage_verified',
                     'independent_attestation_verified','writer_gate_unquarantined',
                     'b3_behavior_independently_verified','successor_versioned_binding_implemented'):
            self.assertIs(x[flag],False)
        self.assertEqual(len(d['hunks']),3)
        self.assertFalse(any('text' in x for x in d['hunks']))
    def test_missing_block(self):
        new,old=pair()
        result=m.compare_published_sources(new.replace(b'# CF10_B3_P2_INDEPENDENT_PRELAUNCH_READBACK_V0_1_END',b'NO_END'),old)
        self.assertEqual(result['classification'],'UNEXPECTED_WRITER_DELTA_BLOCKED')
    def test_changed_old_code_blocks(self):
        new,old=pair()
        self.assertEqual(m.compare_published_sources(new.replace(b'context_line_50',b'context_line_BAD'),old)['classification'],
                         'UNEXPECTED_WRITER_DELTA_BLOCKED')
    def test_extra_insertion_blocks(self):
        new,old=pair()
        self.assertEqual(m.compare_published_sources(new+b'EXTRA\n',old)['classification'],'UNEXPECTED_WRITER_DELTA_BLOCKED')
    def test_identical_pinned_not_reviewed(self):
        self.assertEqual(m.compare_published_sources(OLD.encode(),OLD.encode())['classification'],'EXACT_PINNED_BYTES')
    def test_replacement_not_allowed(self):
        new,old=pair()
        d=m.compare_published_sources(new.replace(b'context_line_5\n',b''),old)
        self.assertFalse(d['recognized_b3_augmentation'])
    def test_bad_utf8(self):
        with self.assertRaises(m.DeltaBlocked):m.compare_published_sources(b'\xff',OLD.encode())
    def test_missing_scope(self):
        new,old=pair();l=live();l['observed_s01_runtime']['writer_source_comparison']['ledger.py']=False
        d=m.compare_published_sources(new,old)
        self.assertIn('WRITER_DIFF_SCOPE_NOT_EXACTLY_GOVERNED_CYCLE',m.classify(l,d,head=HEAD,current_sha=m.digest(new),pinned_sha=m.digest(old))['blockers'])
    def test_unreadable_writer(self):
        new,old=pair();l=live();l['observed_s01_runtime']['writer_source_comparison']['ledger.py']=None
        d=m.compare_published_sources(new,old)
        self.assertEqual(m.classify(l,d,head=HEAD,current_sha=m.digest(new),pinned_sha=m.digest(old))['status'],'BLOCKED_NON_AUTHORIZING')
    def test_unrelated_source_head(self):
        new,old=pair();l=live();l['source_head']='0'*40
        self.assertIn('CURRENT_HEAD_NOT_VERIFIED',m.classify(l,m.compare_published_sources(new,old),head=HEAD,current_sha=m.digest(new),pinned_sha=m.digest(old))['blockers'])
    def test_provenance_auth_widened(self):
        new,old=pair();l=live();l['authority_granted']=True
        self.assertIn('PRIOR_FALSE_AUTHORITY_CLAIM',m.classify(l,m.compare_published_sources(new,old),head=HEAD,current_sha=m.digest(new),pinned_sha=m.digest(old))['blockers'])
    def test_report_safe_create(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'tmp').mkdir()
            new,old=pair();doc=m.classify(live(),m.compare_published_sources(new,old),head=HEAD,current_sha=m.digest(new),pinned_sha=m.digest(old))
            out,sha=m.write_report(p,doc)
            self.assertEqual(len(sha),64)
            self.assertEqual((out/'report.json').stat().st_mode & 0o777,0o600)
            self.assertTrue((out/'SHA256SUMS').exists())
    def test_report_symlink_blocked(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'real').mkdir();(root/'tmp').symlink_to(root/'real')
            with self.assertRaises(m.DeltaBlocked):m.write_report(root,{})


    def test_s01_new_profile_needs_exact_source_and_lock_provenance(self):
        d={'classification':m.S01_PROFILE,'recognized_s01_hardening':True,
           'recognized_b3_augmentation':True,'hunks':[{} for _ in range(6)]}
        l=live()
        l['observed_s01_runtime']['tracked_writers'].append(m.LOCK_REL)
        l['observed_s01_runtime']['writer_source_comparison'][m.LOCK_REL]=False
        x=m.classify(l,d,head=HEAD,current_sha=m.S01_GWC_SHA256,
                     pinned_sha=m.PINNED_GWC_SHA256,
                     writer_lock_review={'status':m.S01_LOCK_STATUS,
                       'current_sha256':m.S01_LOCK_SHA256,'pinned_sha256':m.PINNED_LOCK_SHA256})
        self.assertEqual(x['status'],'S01_WRITER_HARDENING_COMPATIBILITY_REVIEW_REQUIRED_NON_AUTHORIZING')
        self.assertEqual(len(x['findings']),3)
        for flag in ('authority_granted','worker_launched','current_runtime_coverage_verified',
                     'independent_attestation_verified','writer_gate_unquarantined'):
            self.assertIs(x[flag],False)
    def test_s01_requires_lock_release_readback(self):
        d={'classification':m.S01_PROFILE,'recognized_s01_hardening':True,
           'recognized_b3_augmentation':True,'hunks':[{} for _ in range(6)]}
        l=live()
        l['observed_s01_runtime']['tracked_writers'].append(m.LOCK_REL)
        l['observed_s01_runtime']['writer_source_comparison'][m.LOCK_REL]=False
        x=m.classify(l,d,head=HEAD,current_sha=m.S01_GWC_SHA256,
                     pinned_sha=m.PINNED_GWC_SHA256)
        self.assertIn('S01_STRICT_WRITER_LOCK_SOURCE_NOT_VERIFIED',x['blockers'])
    def test_s01_extra_modified_writer_is_blocked(self):
        d={'classification':m.S01_PROFILE,'recognized_s01_hardening':True,
           'recognized_b3_augmentation':True,'hunks':[{} for _ in range(6)]}
        l=live()
        l['observed_s01_runtime']['tracked_writers'] += [m.LOCK_REL]
        l['observed_s01_runtime']['writer_source_comparison'].update({m.LOCK_REL:False,'ledger.py':False})
        x=m.classify(l,d,head=HEAD,current_sha=m.S01_GWC_SHA256,
                     pinned_sha=m.PINNED_GWC_SHA256)
        self.assertIn('WRITER_DIFF_SCOPE_NOT_EXACTLY_S01_HARDENING',x['blockers'])
    def test_s01_wrong_current_sha_denied(self):
        d={'classification':m.S01_PROFILE,'recognized_s01_hardening':True,
           'recognized_b3_augmentation':True,'hunks':[{} for _ in range(6)]}
        l=live(); l['observed_s01_runtime']['tracked_writers'].append(m.LOCK_REL)
        l['observed_s01_runtime']['writer_source_comparison'][m.LOCK_REL]=False
        x=m.classify(l,d,head=HEAD,current_sha='0'*64,pinned_sha=m.PINNED_GWC_SHA256)
        self.assertIn('S01_GOVERNED_SOURCE_PROFILE_NOT_VERIFIED',x['blockers'])
    def test_s01_unknown_source_insertions_remain_blocked(self):
        new,old=pair()
        d=m.compare_published_sources(new+b'dangerous_unreviewed_edit\n',old)
        self.assertEqual(d['classification'],'UNEXPECTED_WRITER_DELTA_BLOCKED')

if __name__=='__main__':unittest.main()
