import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from scripts.coordination.control_plane import cf10_prelaunch_audit_v0_2 as audit


class OfflineTests(unittest.TestCase):
    def test_status_is_not_authority_even_all_pass(self):
        state, counts = audit.summarize([audit.result('a','PASS')])
        self.assertEqual(state, 'EVIDENCE_COLLECTED_NON_AUTHORIZING')
        self.assertEqual(counts['PASS'], 1)

    def test_blocked_takes_precedence(self):
        checks = [audit.result('a', 'PASS'), audit.result('b','BLOCKED'), audit.result('c','REVIEW')]
        self.assertEqual(audit.summarize(checks)[0], 'BLOCKED_NON_AUTHORIZING')

    def test_pending_stays_non_authorizing(self):
        self.assertEqual(audit.summarize([audit.result('a', 'NOT_YET_TESTABLE')])[0],
                         'REVIEW_REQUIRED_NON_AUTHORIZING')

    def test_review_stays_non_authorizing(self):
        self.assertEqual(audit.summarize([audit.result('a', 'REVIEW')])[0],
                         'REVIEW_REQUIRED_NON_AUTHORIZING')

    def test_no_unknown_states(self):
        with self.assertRaises(AssertionError):audit.result('a','AUTHORIZED')

    def temp_root(self):
        context = tempfile.TemporaryDirectory()
        self.addCleanup(context.cleanup)
        root = Path(context.name)/'repo'
        (root/'generated').mkdir(parents=True)
        return root

    def report(self):
        return {'expected_head':'a'*40,'attempt_id':'cf10-u180j-a049','schema_version':audit.SCHEMA}

    def test_report_zip_has_only_sanitized_sections(self):
        root=self.temp_root()
        checks=[audit.result('a','PASS')]
        zip_path, summary = audit.save(root,Path('generated/audits'),self.report(),checks)
        self.assertIn('AUTHORITY_GRANTED=false',summary)
        with ZipFile(zip_path) as z:
            self.assertEqual(sorted(z.namelist()),['SHA256SUMS','checks.json','report.json','summary.txt'])
            self.assertFalse(z.testzip())
            report=json.loads(z.read('report.json'))
            self.assertEqual(report['attempt_id'],'cf10-u180j-a049')
        self.assertEqual(zip_path.stat().st_mode & 0o777, 0o600)

    def test_no_output_escape(self):
        root=self.temp_root()
        with self.assertRaises(RuntimeError):
            audit.save(root,Path('../outside'),self.report(),[])

    def test_no_output_symlink(self):
        root=self.temp_root()
        (root/'generated'/'out').symlink_to(root/'generated',target_is_directory=True)
        with self.assertRaises(RuntimeError):
            audit.save(root,Path('generated/out'),self.report(),[])

    def test_prior_verifier_exception_does_not_create_authority(self):
        self.assertEqual(audit.result('prior_accept','BLOCKED', 'invalid')['status'],'BLOCKED')

    def test_sha256_known_value(self):
        self.assertEqual(audit.digest(b''),'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

    def test_missing_command_is_nonzero(self):
        root=self.temp_root()
        rc, out,err = audit.cmd(['no-such-cf10-executable-x8'],root)
        self.assertNotEqual(rc,0)

    def test_no_external_renewal_script_execution(self):
        import inspect
        src = inspect.getsource(audit.inspect)
        self.assertNotIn('r007_tool', src)
        self.assertIn("add('operator_renewal', 'REVIEW'", src)

    def test_legacy_tmp_dependencies_are_review_not_authority(self):
        import inspect
        src = inspect.getsource(audit.inspect)
        self.assertIn("'legacy_tmp_tooling', 'REVIEW'", src)
        self.assertNotIn('automatic_approval', src)

if __name__ == '__main__':unittest.main()
