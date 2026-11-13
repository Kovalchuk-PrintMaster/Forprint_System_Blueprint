"""R013 validated Copilot -p multiline prompt, bounded without global relaxation."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as r013

class R013PromptContract(unittest.TestCase):
    def specimen(self, argv):
        attempt = 'cf10-u180j-a053'
        runtime = '/srv/software_development/forprint-worker-runtime'
        return r013.BoundedInput(
            task_prompt_id='cf10-validation-check-pipeline-profile-and-optimization-v0-1',
            attempt_id=attempt, source_head='a'*40, handoff_sha256='b'*64,
            baseline_sha256='c'*64,
            workspace=f'{runtime}/forprint_system_blueprint/worker-01/{attempt}/workspace/repo',
            runtime_root=runtime, argv=tuple(argv), timeout_seconds=180,
        )

    def test_long_multiline_provider_prompt_passes(self):
        spec = self.specimen(['/usr/bin/env', '-p', 'First line\n' + 'x'*9000,
                              '--additional-mcp-config', '{"mcpServers":{}}'])
        plan = r013.bind_plan(spec)
        self.assertTrue(r013.validate_plan(plan, spec))
        self.assertFalse(plan['flags']['authorizing'])

    def test_newline_elsewhere_still_denied(self):
        spec = self.specimen(['/usr/bin/env', '--model', 'bad\nvalue'])
        with self.assertRaisesRegex(r013.BoundaryBlocked, 'CF10_R013_COMMAND_INVALID'):
            r013.bind_plan(spec)

    def test_nul_and_cr_in_prompt_denied(self):
        for illegal in ('\x00', '\r'):
            with self.subTest(illegal=repr(illegal)):
                spec = self.specimen(['/usr/bin/env', '-p', 'text'+illegal+'suffix'])
                with self.assertRaisesRegex(r013.BoundaryBlocked, 'CF10_R013_COMMAND_INVALID'):
                    r013.bind_plan(spec)

    def test_huge_prompt_denied(self):
        spec = self.specimen(['/usr/bin/env', '-p', 'x'*65537])
        with self.assertRaisesRegex(r013.BoundaryBlocked, 'CF10_R013_COMMAND_INVALID'):
            r013.bind_plan(spec)

    def test_no_unrestricted_nonprompt_arguments(self):
        spec = self.specimen(['/usr/bin/env', '--model', 'x'*2001])
        with self.assertRaisesRegex(r013.BoundaryBlocked, 'CF10_R013_COMMAND_INVALID'):
            r013.bind_plan(spec)

    def test_large_but_bounded_mcp_config(self):
        spec = self.specimen(['/usr/bin/env', '-p', 'prompt\n',
                              '--additional-mcp-config', '{"mcpServers":{"a":"'+ 'x'*3000 + '"}}'])
        self.assertTrue(r013.validate_plan(r013.bind_plan(spec), spec))

    def test_no_global_argv_unbounded_growth(self):
        spec = self.specimen(['/usr/bin/env', '-p', 'x'*65536,
                              '--additional-mcp-config', 'x'*8192,
                              '--model', 'x'*2000] + ['a'*2000]*20)
        with self.assertRaisesRegex(r013.BoundaryBlocked, 'CF10_R013_COMMAND_INVALID'):
            r013.bind_plan(spec)

if __name__ == '__main__':
    unittest.main()
