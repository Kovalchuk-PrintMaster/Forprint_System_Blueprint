"""Project-native synthetic tests for non-authorizing Make command surface."""
import unittest
from scripts.validation import validate_make_surface_no_scratch_v0_1 as policy

class SurfaceTests(unittest.TestCase):
    @staticmethod
    def fixture():
        lines=[x for x in policy.REQUIRED if x!='CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND']
        lines.extend([
          'cf10-s01-runtime-binding-inspect:',
          'CF10_PRELAUNCH_REPORT_PARENT ?= generated/cf10_prelaunch_audits',
          'CF10_GATE_WRITER_AUDIT_REPORT_PARENT ?= generated/cf10_gate_writer_release_audits',
          'cf10-s01-runtime-launch-preflight:\n\t@echo "CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND"; exit 2',
          'cf10-s01-runtime-binding-inspect:\n\t@echo "CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND"; exit 2',
        ])
        return '\n'.join(x for x in lines if x not in ['cf10-s01-runtime-launch-preflight:','cf10-s01-runtime-binding-inspect:'])+'\n'

    def test_valid_source_is_not_authority(self):
        d=policy.inspect(self.fixture())
        self.assertEqual(d['status'],'PASS_NON_AUTHORIZING')
        self.assertFalse(d['worker_launch_allowed'])
        self.assertTrue(d['release_rebind_required'])

    def test_scratch_token_rejected(self):
        d=policy.inspect(self.fixture()+'\nLEGACY_DIR ?= /tmp/unsafe\n')
        self.assertEqual(d['status'],'BLOCKED')

    def test_launch_quarantine_mandatory(self):
        d=policy.inspect(self.fixture().replace('exit 2','exit 0'))
        self.assertEqual(d['status'],'BLOCKED')

    def test_release_dependency_required(self):
        d=policy.inspect(self.fixture().replace('governed-worker-cycle-launch: cf10-s01-runtime-launch-preflight','governed-worker-cycle-launch:'))
        self.assertEqual(d['status'],'BLOCKED')
if __name__=='__main__':unittest.main()
