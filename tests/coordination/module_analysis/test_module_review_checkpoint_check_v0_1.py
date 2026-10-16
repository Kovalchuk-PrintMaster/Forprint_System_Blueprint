from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / 'scripts/coordination/module_analysis/module_review_checkpoint_check_v0_1.py'
spec = importlib.util.spec_from_file_location('module_review_checker', SCRIPT)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class ReviewCheckpointTests(unittest.TestCase):
    def test_current_package_documents(self):
        self.assertEqual(m.validate(ROOT), [])
    def test_missing_root_is_failing(self):
        self.assertTrue(m.validate(Path('/nonexistent/project/module-review')))
    def test_no_implementation_promotion(self):
        t = (ROOT/m.CHECKPOINT/'01_TELEGRAM_EVIDENCE_CHECKPOINT.yaml').read_text()
        self.assertIn('implementation_approved: false', t)
        self.assertIn('canonical_roadmap_mutated: false', t)
if __name__ == '__main__': unittest.main()
