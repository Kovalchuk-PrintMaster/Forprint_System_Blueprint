"""A02 entirely synthetic (except fixture G2a evidence bytes); no actual mounted backup written."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from scripts.coordination.evidence_management import backup_v0_1 as b
from scripts.coordination.evidence_management import vault_v0_1 as v
from tests.coordination.evidence_management.test_vault_v0_1 import sample_zip

class A02(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='a02_synthetic_')
        self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name)
        self.restore_parent=self.home/'project-scratch'
        self.restore_parent.mkdir()
        self.restore_target_patch=mock.patch.object(b,'RESTORE_PARENT',self.restore_parent)
        self.restore_target_patch.start()
        self.addCleanup(self.restore_target_patch.stop)
        self.root=self.home/'vault'
        self.target=self.home/'remote-mount'
        self.target.mkdir(mode=0o700)
        self.assertEqual(v.init(self.root,confirmed=True,strict=False),'INITIALIZED_NON_AUTHORIZING')
        self.source=self.home/'proof.zip'
        self.source.write_bytes(sample_zip())
        v.register(self.root,self.source,'cf10-g2a-pilot',confirmed=True,strict=False)
        self.probe={'separate_filesystem_verified':True,'physical_independence_verified':False,'offhost_copy_verified':False,
                    'mountpoint':str(self.target),'source_dev':1,'backup_dev':2}
        self.patch=mock.patch.object(b,'validate_target',return_value=self.probe)
        self.restore_probe=mock.patch.object(b,'validate_backup_mount_only',return_value=self.probe)

    def do_snapshot(self):
        with self.patch:
            return b.snapshot(self.root,self.target,confirm=b.CONFIRM_BACKUP,strict=False,
                              identifier='a02-test-20261028')

    def test_full_snapshot_and_independent_restore(self):
        x=self.do_snapshot()
        self.assertEqual(x['state'],'SEPARATE_FILESYSTEM_SNAPSHOT_VERIFIED_NON_AUTHORIZING')
        self.assertFalse(x['backup_disaster_recovery_proven'])
        self.assertEqual(x['evidence_count'],1)
        y=b.verify_snapshot(self.target/'snapshots'/x['snapshot_id'],x['manifest_sha256'])
        self.assertEqual(y['evidence_count'],1)
        restore=self.restore_parent/'evidence_a02_restore_isolated'
        with self.restore_probe:
            z=b.restore_test(self.root,self.target,x['snapshot_id'],x['manifest_sha256'],restore,
                             confirm=b.CONFIRM_RESTORE,strict=False)
        self.assertEqual(z['state'],'ISOLATED_RESTORE_TEST_PASS_NON_AUTHORIZING')
        self.assertEqual((restore/'vault.json').read_bytes(),(self.root/'vault.json').read_bytes())
        self.assertEqual(v.verify_registered(restore,'cf10-g2a-pilot',strict=False)['state'],
                         'VERIFIED_REGISTERED_NON_AUTHORIZING')

    def test_restore_does_not_need_original_vault(self):
        x=self.do_snapshot()
        self.root.rename(self.home/'lost-original-vault')
        with self.restore_probe:
            z=b.restore_test(self.root,self.target,x['snapshot_id'],x['manifest_sha256'],self.restore_parent/'evidence_a02_restore_after-loss',
                             confirm=b.CONFIRM_RESTORE,strict=False)
        self.assertEqual(z['state'],'ISOLATED_RESTORE_TEST_PASS_NON_AUTHORIZING')

    def test_missing_confirmation_rejected(self):
        with self.assertRaisesRegex(b.BackupBlocked,'EXPLICIT_BACKUP_CONFIRMATION'):
            b.snapshot(self.root,self.target,confirm='',strict=False)
    def test_bad_snapshot_id_rejected(self):
        with self.patch,self.assertRaisesRegex(b.BackupBlocked,'SNAPSHOT_ID_INVALID'):
            b.snapshot(self.root,self.target,confirm=b.CONFIRM_BACKUP,identifier='../escape',strict=False)
    def test_backup_existing_never_overwrites(self):
        self.do_snapshot()
        with self.patch,self.assertRaisesRegex(b.BackupBlocked,'SNAPSHOT_ALREADY_EXISTS'):
            b.snapshot(self.root,self.target,confirm=b.CONFIRM_BACKUP,identifier='a02-test-20261028',strict=False)
    def test_wrong_external_anchor_rejected(self):
        x=self.do_snapshot()
        with self.assertRaisesRegex(b.BackupBlocked,'ANCHOR_MISMATCH'):
            b.verify_snapshot(self.target/'snapshots'/x['snapshot_id'],'0'*64)
    def test_tampered_payload_rejected(self):
        x=self.do_snapshot()
        obj=list((self.target/'snapshots'/x['snapshot_id']/'payload'/'objects').rglob('?'*64))[0]
        obj.chmod(0o600);obj.write_bytes(b'altered')
        with self.assertRaises(b.BackupBlocked):
            b.verify_snapshot(self.target/'snapshots'/x['snapshot_id'],x['manifest_sha256'])
    def test_unexpected_vault_file_rejected(self):
        (self.root/'intake'/'foreign.txt').write_text('untracked')
        with self.assertRaisesRegex(b.BackupBlocked,'EXTRA_OR_MISSING'):
            b.collect(self.root,strict=False)
    def test_unregistered_object_rejected(self):
        (self.root/'objects'/'sha256'/'cd').mkdir(mode=0o700)
        (self.root/'objects'/'sha256'/'cd'/('c'*64)).write_text('orphan')
        with self.assertRaisesRegex(b.BackupBlocked,'EXTRA_OR_MISSING'):
            b.collect(self.root,strict=False)
    def test_multiple_evidence_ids_deduplicate_object(self):
        v.register(self.root,self.source,'cf10-g2a-pilot-two',confirmed=True,strict=False)
        x=self.do_snapshot()
        self.assertEqual(x['evidence_count'],2)
        manifest=json.loads((self.target/'snapshots'/x['snapshot_id']/'snapshot_manifest.json').read_text())
        self.assertEqual(len([a for a in manifest['entries'] if a.startswith('objects/sha256/')]),1)
    def test_restore_existing_path_rejected(self):
        x=self.do_snapshot()
        existing=self.restore_parent/'evidence_a02_restore_already';existing.mkdir()
        with self.restore_probe,self.assertRaisesRegex(b.BackupBlocked,'RESTORE_MUST_CREATE_NEW'):
            b.restore_test(self.root,self.target,x['snapshot_id'],x['manifest_sha256'],existing,
                           confirm=b.CONFIRM_RESTORE,strict=False)
    def test_restore_without_operator_confirmation_rejected(self):
        x=self.do_snapshot()
        with self.assertRaisesRegex(b.BackupBlocked,'EXPLICIT_RESTORE_CONFIRMATION'):
            b.restore_test(self.root,self.target,x['snapshot_id'],x['manifest_sha256'],self.restore_parent/'evidence_a02_restore_out',confirm='',strict=False)
    def test_mount_same_device_fails(self):
        with self.assertRaisesRegex(b.BackupBlocked,'BACKUP_TARGET_IN_PRIMARY_OR_TRANSIENT_TREE|SAME_FILESYSTEM'):
            b.validate_target(self.target,self.root,strict=False)
    def test_paths_symlink_rejected(self):
        link=self.home/'backup-link';link.symlink_to(self.target,target_is_directory=True)
        with self.assertRaisesRegex(b.BackupBlocked,'SYMLINK_PATH'):
            b.validate_target(link,self.root,strict=False)
    def test_backup_into_vault_rejected(self):
        with self.assertRaisesRegex(b.BackupBlocked,'BACKUP_TARGET_IN_PRIMARY'):
            b.validate_target(self.root/'objects',self.root,strict=False)
    def test_snapshot_file_extra_rejected(self):
        x=self.do_snapshot();dir=self.target/'snapshots'/x['snapshot_id']
        (dir/'unexpected').write_text('x')
        with self.assertRaisesRegex(b.BackupBlocked,'FILE_SET_DRIFT'):
            b.verify_snapshot(dir,x['manifest_sha256'])
    def test_corrupted_journal_source_rejected(self):
        p=self.root/'journal'/'events'/'cf10-g2a-pilot.json'
        p.write_text('{}')
        with self.assertRaisesRegex(b.BackupBlocked,'EVIDENCE_VERIFY_FAILED'):
            b.collect(self.root,strict=False)
    def test_manifest_bad_path_rejected(self):
        x=self.do_snapshot()
        snap=self.target/'snapshots'/x['snapshot_id'];mp=snap/'snapshot_manifest.json'
        obj=json.loads(mp.read_text());obj['entries']['../outside']={'sha256':'0'*64,'size_bytes':1}
        mp.write_bytes(v.encode(obj))
        with self.assertRaises(b.BackupBlocked):
            b.verify_snapshot(snap,v.digest(mp.read_bytes()))
    def test_inspect_requires_evidence(self):
        empty=self.home/'empty';v.init(empty,confirmed=True,strict=False)
        with self.assertRaisesRegex(b.BackupBlocked,'NO_REGISTERED_EVIDENCE'):
            b.collect(empty,strict=False)
    def test_no_delete_implementation(self):
        self.assertNotIn('delete',b.main.__code__.co_consts)

if __name__=='__main__':unittest.main()
