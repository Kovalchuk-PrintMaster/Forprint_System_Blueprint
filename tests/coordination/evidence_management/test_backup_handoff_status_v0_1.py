"""Pure/synthetic tests. No s01 mutation or external backup access."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.coordination.evidence_management import backup_handoff_status_v0_1 as status
from scripts.coordination.evidence_management import vault_v0_1 as vault

class BackupHandoffStatusTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name) / 'vault'

    def test_not_initialized_warns_no_backups(self):
        result = status.build_status(self.root, strict=False)
        self.assertEqual(result['primary_vault_state'], 'NOT_INITIALIZED_NON_AUTHORIZING')
        self.assertFalse(result['offhost_backup_verified'])
        self.assertFalse(result['backup_service_connected'])

    def test_initialized_pilot_is_still_pending(self):
        vault.init(self.root, confirmed=True, strict=False)
        result = status.build_status(self.root, strict=False)
        self.assertEqual(result['primary_vault_state'], 'INITIALIZED_NON_AUTHORIZING')
        self.assertEqual(result['state'], 'PENDING_EXTERNAL_INTEGRATION')
        self.assertFalse(result['independent_restore_verified'])
        self.assertFalse(result['authority_granted'])

    def test_does_not_modify_vault(self):
        vault.init(self.root, confirmed=True, strict=False)
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        status.build_status(self.root, strict=False)
        after = sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        self.assertEqual(before, after)

    def test_rejects_corrupt_vault(self):
        vault.init(self.root, confirmed=True, strict=False)
        (self.root / 'vault.json').write_bytes(b'{}')
        with self.assertRaises(vault.VaultBlocked):
            status.build_status(self.root, strict=False)

    def test_text_warning_visible_and_exit_zero(self):
        report = {'state':'PENDING_EXTERNAL_INTEGRATION', 'primary_vault_state':'INITIALIZED_NON_AUTHORIZING'}
        with patch.object(status, 'build_status', return_value=report):
            from contextlib import redirect_stdout
            from io import StringIO
            out = StringIO()
            with redirect_stdout(out):
                self.assertEqual(status.main([]), 0)
            self.assertIn('EVIDENCE_VAULT_BACKUP=PENDING_EXTERNAL_INTEGRATION', out.getvalue())
            self.assertIn('BACKUP_VERIFIED=false', out.getvalue())
            self.assertIn('WARNING:', out.getvalue())

    def test_json_machine_status(self):
        vault.init(self.root, confirmed=True, strict=False)
        with patch.object(status, 'build_status', return_value=status.build_status(self.root, strict=False)):
            from contextlib import redirect_stdout
            from io import StringIO
            out=StringIO()
            with redirect_stdout(out):self.assertEqual(status.main(['--format','json']),0)
            data=json.loads(out.getvalue())
            self.assertEqual(data['state'],'PENDING_EXTERNAL_INTEGRATION')
            self.assertFalse(data['backup_service_connected'])

    def test_fail_closed_on_invalid_source(self):
        with patch.object(status, 'build_status', side_effect=vault.VaultBlocked('INVALID')):
            from contextlib import redirect_stderr
            from io import StringIO
            err=StringIO()
            with redirect_stderr(err):self.assertEqual(status.main([]),2)
            self.assertIn('BLOCKED:',err.getvalue())

if __name__ == '__main__': unittest.main()
