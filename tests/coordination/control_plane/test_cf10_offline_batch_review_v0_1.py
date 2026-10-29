from __future__ import annotations
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

HERE=Path(__file__).resolve().parent
MODULE_FILE=HERE/'cf10_offline_batch_review_v0_1.py'
if not MODULE_FILE.is_file():
    MODULE_FILE=HERE.parents[2]/'scripts/coordination/control_plane/cf10_offline_batch_review_v0_1.py'
spec=importlib.util.spec_from_file_location('cf10_offline',MODULE_FILE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class FormatTests(unittest.TestCase):
    def test_safe_paths(self):
        for name in ('manifest.json','published_head/scripts/a.py','uncommitted_review/file.patch'):
            self.assertTrue(module.canonical_name(name))
        for name in ('/root/file','../abc','scripts/../etc','abc\\evil',''):
            self.assertFalse(module.canonical_name(name))
    def test_categories_cover_all_names(self):
        self.assertGreater(len(module.CATEGORIES),10)
    def test_non_mutating_replace(self):
        r={'path':'scripts/x.py','api':'replace','line':1,'function':'func'}
        self.assertEqual(module.site_category(r,'text.replace("Z", "+00:00")'),'STRING_REPLACE_NOT_FS_WRITE')
    def test_readonly_open(self):
        r={'path':'scripts/x.py','api':'open','line':1,'function':'func'}
        self.assertEqual(module.site_category(r,'os.open(path, os.O_RDONLY | os.O_NOFOLLOW)'),'READ_ONLY_OPEN')
    def test_canonical_core(self):
        r={'path':'scripts/coordination/execution_attempt_ledger_v0_1.py','api':'open','line':373,'function':'append_record'}
        self.assertEqual(module.site_category(r,'with path.open("x") as f:'),'CANONICAL_LEDGER_CORE')
    def test_governed_append(self):
        r={'path':'scripts/coordination/control_plane/governed_worker_cycle.py','api':'append_record','line':2745,'function':'reconcile_result_return'}
        self.assertEqual(module.site_category(r,'ledger.append_record(root, record)'),'CANONICAL_LEDGER_API_CALL')
    def test_closeout_distinguishes_lock_completion(self):
        base='scripts/coordination/work_front_closeout_apply_v0_1.py'
        self.assertEqual(module.site_category({'path':base,'api':'open','line':215,'function':'perform_closeout'},'with lock.open("a+b")'), 'CLOSEOUT_LOCK_HANDLE')
        self.assertEqual(module.site_category({'path':base,'api':'open','line':267,'function':'perform_closeout'},'fd=os.open(target, os.O_CREAT)'), 'CLOSEOUT_COMPLETION_WRITE')
    def test_patch_header_rejects_mismatch(self):
        manifest={'dirty_worktree_file_names_only':['a.txt']}
        with self.assertRaises(module.ReviewError):
            module.assess_dirty_patch('diff --git a/a.txt b/other.txt\n--- a/a.txt\n+++ b/a.txt\n',manifest)
    def test_write_results_fail_closed_existing_dir(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(module.ReviewError):module.write_results({},Path(d))
    def test_proof_contract_has_eight(self):
        self.assertEqual(len(module.REQUIRED_PROOFS),8)

class FullArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value=os.getenv('CF10_BATCH_FIXTURE_ZIP')
        if not value:raise unittest.SkipTest('Optional full source batch fixture not supplied')
        cls.archive=Path(value)
        cls.review=module.review(cls.archive)
    def test_reconcile_113(self):self.assertEqual(len(self.review['candidates']),113)
    def test_reconcile_18(self):self.assertEqual(len(self.review['dirty_patch']),18)
    def test_p01_332(self):
        self.assertEqual(self.review['summary']['p01_files_crosschecked'],332)
        self.assertEqual(self.review['summary']['p01_files_not_exported'],['config/worker_runtime.yaml'])
    def test_proofs_not_attested(self):
        self.assertTrue(all(x['status']=='NOT_ATTESTED' for x in self.review['proof_requirements']))
        self.assertFalse(self.review['summary']['authority_granted'])
    def test_distinct_known_writer_sources(self):
        rows=self.review['candidates'];s=module.Counter(x['category'] for x in rows)
        self.assertEqual(s['CANONICAL_LEDGER_API_CALL'],3)
        self.assertEqual(s['CANONICAL_LEDGER_CORE'],4)
        self.assertEqual(s['STRING_REPLACE_NOT_FS_WRITE'],23)
        self.assertEqual(s['READ_ONLY_OPEN'],6)
        self.assertEqual(sum(s.values()),113)
    def test_indirect_callback_properly_separate(self):
        callback=self.review['summary']['additional_indirect_canonical_append']
        self.assertEqual(callback['line'],2168)
        self.assertFalse(callback['runtime_verified'])
    def test_report_output_sha256(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'review';module.write_results(self.review,out)
            for line in (out/'SHA256SUMS').read_text().splitlines():
                h,f=line.split('  ')
                self.assertEqual(module.sha((out/f).read_bytes()),h)
    def test_manipulated_zip_fails_closed(self):
        with zipfile.ZipFile(self.archive) as z:
            with tempfile.TemporaryDirectory() as d:
                fake=Path(d)/'bad.zip'
                with zipfile.ZipFile(fake,'w',zipfile.ZIP_DEFLATED) as dst:
                    for item in z.infolist():
                        contents=z.read(item.filename)
                        if item.filename=='reports/p07_write_survey.json':contents=contents.replace(b'"authority_granted": false',b'"authority_granted": true',1)
                        dst.writestr(item.filename,contents)
                with self.assertRaises(module.ReviewError):module.read_archive(fake)

if __name__=='__main__':unittest.main()
