"""Independent negative tests for non-authorizing S01 integration review."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
MOD = ROOT / 'cf10_s01_launch_integration_review_v0_1.py'
if not MOD.exists():
    MOD = Path(__file__).resolve().parents[3] / 'scripts/coordination/control_plane/cf10_s01_launch_integration_review_v0_1.py'
spec = importlib.util.spec_from_file_location('cf10_review_candidate', MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

WORKER = '''
def require_bounded_s01_launch_authority():
    raise RuntimeError('QUARANTINED')
def launch_authorized_worker_cycle():
    require_bounded_s01_launch_authority()
    print('NEVER')
def launch_cycle():
    """doc"""
    require_bounded_s01_launch_authority()
    print('NEVER')
'''
MAKE = 'cf10-s01-runtime-launch-preflight:\n\t@echo CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND; exit 2\n'


def git(repo, *args):
    subprocess.run(['git', *args], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class ReviewTests(unittest.TestCase):
    def test_quarantine_guard_detected(self):
        b = m.inspect_barriers(WORKER, MAKE)
        self.assertTrue(b['direct_python_hard_blocked'])
        self.assertTrue(b['make_quarantine_present'])
        self.assertEqual(set(b['python_entrypoints'].values()), {'FIRST_ACTION_GUARD'})
        self.assertFalse(b['live_launch_allowed'])

    def test_missing_guards_blocked(self):
        b = m.inspect_barriers(WORKER.replace('    require_bounded_s01_launch_authority()\n    print', '    print'), MAKE)
        self.assertIn('FIRST_ACTION_NOT_PROVEN_GUARDED', b['python_entrypoints'].values())

    def test_make_marker_removed_never_authority(self):
        b = m.inspect_barriers(WORKER, 'cf10-s01-runtime-launch-preflight:\n\t@true\n')
        self.assertFalse(b['make_quarantine_present'])
        self.assertFalse(b['live_launch_allowed'])

    def test_syntax_fail_closed(self):
        with self.assertRaises(SyntaxError):
            m.inspect_barriers('not python ???', MAKE)

    def test_normalized_error_no_secret(self):
        s = m.status_only({'status': 'BLOCKED', 'blockers': ['BAD /etc/secret key']}, 'activation')
        self.assertEqual(s['blockers'], ['CANONICAL_CHECK_BLOCKED'])

    def test_untrusted_canonical_result_never_authorizes(self):
        b = m.inspect_barriers(WORKER, MAKE)
        inv = {'critical_source_drift': []}
        checks = [m.status_only({'status':'PASS','candidate_preconditions_pass': True,
                                 'predicate_pass': True}, name)
                  for name in ('activation','release','rebind','corridor')]
        p = m.plan(barrier=b,inventory=inv,checks=checks,exact_scope=True)
        self.assertEqual(p['status'], 'BLOCKED_NON_AUTHORIZING')
        self.assertFalse(p['authority_granted'])
        self.assertIn('DIRECT_PYTHON_LAUNCH_QUARANTINED_BY_DESIGN', p['blockers'])

    def test_source_drift_priority(self):
        b = m.inspect_barriers(WORKER, MAKE)
        p = m.plan(barrier=b, inventory={'critical_source_drift':['Makefile']},checks=[],exact_scope=False)
        self.assertEqual(p['next_action'], 'RESTORE_OR_INDEPENDENTLY_REVIEW_CRITICAL_SOURCE_DRIFT_BEFORE_INTEGRATION')

    def test_canonical_failure_classified_without_secret(self):
        with patch('importlib.import_module', side_effect=RuntimeError('private_token')):
            out=m.canonical_reviews(Path('.'),worker='worker-01',task='task',attempt='cf10-test')
        self.assertEqual(len(out),4)
        self.assertEqual({o['status'] for o in out},{'UNAVAILABLE'})
        self.assertNotIn('private_token',str(out))

    def test_exact_scope_restricted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            git(root,'init','-q')
            git(root,'config','user.name','Review')
            git(root,'config','user.email','review@example.invalid')
            for rel in m.SOURCE_FILES:
                p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(WORKER if rel.endswith('governed_worker_cycle.py') else MAKE if rel == 'Makefile' else 'pass\n')
            git(root,'add','.')
            git(root,'commit','-qm','baseline')
            loader=lambda name: {'status':'PASS', 'candidate_preconditions_pass':True, 'predicate_pass':True, 'blockers':[]}
            report=m.evaluate(root,worker='worker-01',task='cf10-task85',attempt='cf10-unit-a001',loader=loader)
            self.assertFalse(report['outcome']['launch_allowed'])
            self.assertTrue(report['barriers']['direct_python_hard_blocked'])
            before=m.sha((root/'Makefile').read_bytes())
            target=m.write_report(root,report)
            self.assertTrue(target.exists())
            self.assertEqual(before,m.sha((root/'Makefile').read_bytes()))
            self.assertEqual(target,m.write_report(root,report))
            self.assertEqual(m.main(['launch-preflight','--root',str(root)]),2)

    def test_drift_and_sha_binding(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            git(root,'init','-q');git(root,'config','user.name','Review');git(root,'config','user.email','review@example.invalid')
            for rel in m.SOURCE_FILES:
                p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(WORKER if rel.endswith('governed_worker_cycle.py') else MAKE if rel=='Makefile' else 'pass\n')
            git(root,'add','.');git(root,'commit','-qm','baseline')
            report=m.source_inventory(root)
            self.assertEqual(report['critical_source_drift'],[])
            (root/'Makefile').write_text('modified')
            report=m.source_inventory(root)
            self.assertIn('Makefile',report['critical_source_drift'])
            (root/'Makefile').unlink();(root/'Makefile').symlink_to(root/'README')
            with self.assertRaises(ValueError):m.source_inventory(root)

    def test_no_dangerous_runtime_calls_in_new_module(self):
        src=MOD.read_text()
        for forbidden in ('consume_once_fd(', 'launch_authorized_worker_cycle(',
                          'subprocess.Popen(', 'git push', 'git commit', 'signature_base64 ='):
            self.assertNotIn(forbidden,src)

if __name__ == '__main__':
    unittest.main()
