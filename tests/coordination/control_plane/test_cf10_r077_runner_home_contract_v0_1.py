"""R077 read-only home and exact systemd property scope regressions."""
import importlib.util
from pathlib import Path
import os
import stat
import tempfile
import unittest
import sys
from types import SimpleNamespace
from unittest.mock import patch,Mock

from scripts.coordination.control_plane import cf10_r077_runner_home_contract_v0_1 as mod

class HomeTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='r077-home-test-')
        self.root=Path(self.tmp.name)
        self.home=self.root/'forprint-runner'
        self.home.mkdir(mode=0o700)
        self.uid=self.home.stat().st_uid
        self.gid=self.home.stat().st_gid
    def tearDown(self):self.tmp.cleanup()
    def check(self):return mod.inspect_home(self.home,uid=self.uid,gid=self.gid,account_home=str(self.home))
    def test_missing_cache_is_acceptable_before_state_directory(self):
        x=self.check()
        self.assertIn('MISSING_ALLOWED',x['cache_state'])
        self.assertFalse(x['worker_launched'])
    def test_private_existing_cache_allowed(self):
        (self.home/'.cache').mkdir(mode=0o700)
        self.assertEqual(self.check()['cache_state'],'EXISTS_PRIVATE')
    def test_cache_symlink_rejected(self):
        (self.home/'.cache').symlink_to(self.root)
        with self.assertRaises(mod.HomeBlocked):self.check()
    def test_cache_public_mode_rejected(self):
        (self.home/'.cache').mkdir(mode=0o777)
        (self.home/'.cache').chmod(0o755)
        with self.assertRaises(mod.HomeBlocked):self.check()
    def test_home_wrong_owner_rejected(self):
        with self.assertRaises(mod.HomeBlocked):
            mod.inspect_home(self.home,uid=self.uid+1,gid=self.gid,account_home=str(self.home))
    def test_home_wrong_mode_rejected(self):
        self.home.chmod(0o755)
        with self.assertRaises(mod.HomeBlocked):self.check()
    def test_home_symlink_rejected(self):
        self.home.rmdir()
        self.home.symlink_to(self.root)
        with self.assertRaises(mod.HomeBlocked):self.check()
    def test_missing_home_rejected(self):
        self.home.rmdir()
        with self.assertRaises(mod.HomeBlocked):self.check()
    def test_account_home_mismatch_rejected(self):
        with self.assertRaises(mod.HomeBlocked):
            mod.inspect_home(self.home,uid=self.uid,gid=self.gid,account_home='/another')

class PropertiesTest(unittest.TestCase):
    def setUp(self):
        self.props={'User':'forprint-runner','Group':'forprint-runner',
          'ProtectSystem':'strict','ProtectHome':'yes','PrivateTmp':'yes',
          'StateDirectory':'forprint-runner','StateDirectoryMode':'0700',
          'ReadWritePaths':'/work/repo /work/logs'}
    def test_exact_scope_allowed(self):
        self.assertTrue(mod.assert_systemd_properties(self.props,'/work/repo','/work/logs'))
    def test_missing_state_directory_denied(self):
        self.props.pop('StateDirectory')
        with self.assertRaises(mod.HomeBlocked):mod.assert_systemd_properties(self.props)
    def test_broad_readwrite_denied(self):
        self.props['ReadWritePaths']=' /var/lib /work/repo /work/logs'
        with self.assertRaises(mod.HomeBlocked):mod.assert_systemd_properties(self.props,'/work/repo','/work/logs')
    def test_no_protectsystem_weakening(self):
        self.props['ProtectSystem']='full'
        with self.assertRaises(mod.HomeBlocked):mod.assert_systemd_properties(self.props)
    def test_mode_must_be_private(self):
        self.props['StateDirectoryMode']='0755'
        with self.assertRaises(mod.HomeBlocked):mod.assert_systemd_properties(self.props)
    def test_disposable_probe_never_uses_worker_executable_or_attempt(self):
        fake=Mock(returncode=0,stdout=b'CF10_R077_EFFECTIVE_HOME_CACHE_WRITE=PASS\n',stderr=b'')
        with (patch.dict(sys.modules,{'scripts.coordination.control_plane.cf10_supervisor_binding_candidate_v0_1':SimpleNamespace(EXPECTED_PROPERTIES=self.props)}),
              patch.object(mod,'assert_runner_home',return_value={}),
              patch.object(mod.os,'geteuid',return_value=0),
              patch.object(mod.os,'isatty',return_value=True),
              patch.object(mod.subprocess,'run',return_value=fake) as run):
            x=mod.disposable_sandbox_probe()
        self.assertEqual(x['status'],'PASS_DISPOSABLE_SYSTEMD_HOME_CACHE_WRITE_NON_AUTHORIZING')
        argv=run.call_args.args[0]
        self.assertEqual(argv[0],'/usr/bin/systemd-run')
        self.assertIn('--property=StateDirectory=forprint-runner',argv)
        self.assertIn('--property=StateDirectoryMode=0700',argv)
        self.assertIn('--property=ProtectSystem=strict',argv)
        self.assertNotIn('copilot',argv)
        self.assertFalse(x['worker_launched'])
    def test_disposable_probe_nonzero_denied(self):
        fake=Mock(returncode=1,stdout=b'',stderr=b'')
        with (patch.dict(sys.modules,{'scripts.coordination.control_plane.cf10_supervisor_binding_candidate_v0_1':SimpleNamespace(EXPECTED_PROPERTIES=self.props)}),
              patch.object(mod,'assert_runner_home',return_value={}),
              patch.object(mod.os,'geteuid',return_value=0),
              patch.object(mod.os,'isatty',return_value=True),
              patch.object(mod.subprocess,'run',return_value=fake)):
            with self.assertRaises(mod.HomeBlocked):mod.disposable_sandbox_probe()

    def test_target_readwrite_exact(self):
        self.props['ReadWritePaths']='/work/repo /work/logs /other'
        with self.assertRaises(mod.HomeBlocked):mod.assert_systemd_properties(self.props,'/work/repo','/work/logs')

if __name__=='__main__':unittest.main()
