"""No root/operator integration; strict mock-free synthetic local vault tests."""
import json
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED
from scripts.coordination.evidence_management import vault_v0_1 as v


def sample_zip(*, state='STABLE_RELEASES_READY_FOR_INDEPENDENT_REBIND_NON_AUTHORIZING',
               authority=False, gate_blob=None, source_head=None, tamper_sums=False):
    doc={
        'schema_version':v.REPORT_SCHEMA,
        'state':state,'authority_granted':authority,
        'root_signed_activation_renewed':False,
        'make_launch_gate_unquarantined':False,
        'worker_launched':False,
        'historical_technical_coverage_evidence_migrated':False,
        'historical_gate_coverage_binding_reauthorized':False,
        'checks':{'canonical':{'status':'PASS','canonical_head':source_head or v.SOURCE_HEAD,
                               'remote_verified':True,'pinned_git_objects_verified':True,'pinned_git_objects_missing':[]},
                  'gate':{'status':'PASS','head':v.PIN['gate'][0],
                          'source_blob_oid':gate_blob or v.PIN['gate'][1]},
                  'writer':{'status':'PASS','head':v.PIN['writer'][0],
                            'source_blob_oid':v.PIN['writer'][1]}}
    }
    payload={'report.json':v.encode(doc),'summary.txt':('CF10_G2A_STATUS='+state+'\n').encode()}
    sums=''.join(v.digest(raw)+'  '+name+'\n' for name,raw in sorted(payload.items()))
    if tamper_sums:sums='x'+sums[1:]
    payload['SHA256SUMS']=sums.encode()
    f=BytesIO()
    with ZipFile(f,'w',ZIP_DEFLATED) as z:
        for name,raw in payload.items():z.writestr(name,raw)
    return f.getvalue()

class EvidenceVaultTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(prefix='forprint_evidence_pilot_')
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)/'vault'
        self.src=Path(self.t.name)/'g2a.zip'
        self.src.write_bytes(sample_zip())
        self.id='cf10-g2a-review-f37abe98-20261028'

    def initialize(self):v.init(self.root,confirmed=True,strict=False)
    def register(self):return v.register(self.root,self.src,self.id,confirmed=True,strict=False)

    def test_realistic_synthetic_proposal(self):
        p=v.propose(self.src)
        self.assertEqual(p['source_head'],v.SOURCE_HEAD)
        self.assertFalse(p['authorizing'])
        self.assertFalse(p['vault_mutated'])
        self.assertFalse(self.root.exists())

    def test_init_is_explicit(self):
        with self.assertRaisesRegex(v.VaultBlocked,'CONFIRMATION'):
            v.init(self.root,strict=False)
        self.assertFalse(self.root.exists())

    def test_initialize_idempotent(self):
        self.initialize()
        self.assertEqual(v.init(self.root,confirmed=True,strict=False),'ALREADY_INITIALIZED_NON_AUTHORIZING')
        self.assertEqual(v.inspect(self.root,strict=False)['registered_manifest_count'],0)

    def test_init_nonempty_unowned_folder_blocks(self):
        self.root.mkdir();(self.root/'other').write_text('unexpected')
        self.root.chmod(0o700)
        with self.assertRaisesRegex(v.VaultBlocked,'UNRECOGNIZED'):
            self.initialize()

    def test_register_explicit_confirmation(self):
        self.initialize()
        with self.assertRaisesRegex(v.VaultBlocked,'CONFIRMATION'):
            self.register_unconfirmed()
        self.assertEqual(v.inspect(self.root,strict=False)['registered_manifest_count'],0)

    def register_unconfirmed(self):return v.register(self.root,self.src,self.id,strict=False)

    def test_round_trip_and_dedup(self):
        self.initialize()
        self.assertEqual(self.register()['state'],'REGISTERED_NON_AUTHORIZING')
        # register() returns a VERIFIED state; no operator ACCEPT anywhere.
        self.assertEqual(v.verify_registered(self.root,self.id,strict=False)['sha256'],v.digest(self.src.read_bytes()))
        self.assertEqual(self.register()['state'],'ALREADY_REGISTERED_NON_AUTHORIZING')
        self.assertEqual(len(list((self.root/'objects'/'sha256').rglob('[0-9a-f]'*64))),1)
        self.assertEqual(v.inspect(self.root,strict=False)['registered_manifest_count'],1)
        dest=Path(self.t.name)/'restored.zip'
        self.assertEqual(v.retrieve(self.root,self.id,dest,confirmed=True,strict=False)['state'],'EXPORTED_NON_AUTHORIZING')
        self.assertEqual(dest.read_bytes(),self.src.read_bytes())
        with self.assertRaisesRegex(v.VaultBlocked,'NOT_NEW_FILE'):
            v.retrieve(self.root,self.id,dest,confirmed=True,strict=False)

    def test_rejects_changed_g2a_summary(self):
        self.src.write_bytes(sample_zip(state='BLOCKED_NON_AUTHORIZING'))
        with self.assertRaisesRegex(v.VaultBlocked,'STATE'):
            v.propose(self.src)

    def test_rejects_authority_true(self):
        self.src.write_bytes(sample_zip(authority=True))
        with self.assertRaisesRegex(v.VaultBlocked,'AUTHORITY'):
            v.propose(self.src)

    def test_rejects_git_head_drift(self):
        self.src.write_bytes(sample_zip(source_head='0'*40))
        with self.assertRaisesRegex(v.VaultBlocked,'CANONICAL_PROVENANCE'):
            v.propose(self.src)

    def test_rejects_blob_drift(self):
        self.src.write_bytes(sample_zip(gate_blob='a'*40))
        with self.assertRaisesRegex(v.VaultBlocked,'PINNED_RELEASE'):
            v.propose(self.src)

    def test_rejects_internal_sha_drift(self):
        self.src.write_bytes(sample_zip(tamper_sums=True))
        with self.assertRaisesRegex(v.VaultBlocked,'SHA256SUMS'):
            v.propose(self.src)

    def test_source_symlink_rejected(self):
        link=Path(self.t.name)/'link.zip';link.symlink_to(self.src)
        with self.assertRaisesRegex(v.VaultBlocked,'SYMLINK'):
            v.propose(link)

    def test_object_tampering_detected(self):
        self.initialize();self.register()
        sha=v.digest(self.src.read_bytes());path=v.object_path(self.root,sha)
        path.chmod(0o600);path.write_bytes(b'x')
        with self.assertRaises(v.VaultBlocked):
            v.verify_registered(self.root,self.id,strict=False)

    def test_journal_tampering_detected(self):
        self.initialize();self.register()
        journal=v.event_path(self.root,self.id)
        event=json.loads(journal.read_text());event['artifact_sha256']='0'*64
        journal.write_bytes(v.encode(event))
        with self.assertRaisesRegex(v.VaultBlocked,'JOURNAL_LINK_DRIFT'):
            v.verify_registered(self.root,self.id,strict=False)

    def test_different_source_cannot_rebind_same_id(self):
        self.initialize();self.register()
        other=sample_zip();self.src.write_bytes(other+b'\n')
        # Same ZIP content + trailing garbage remains readable but has different raw digest.
        with self.assertRaisesRegex(v.VaultBlocked,'OTHER_BYTES'):
            self.register()

    def test_id_traversal_rejected(self):
        self.initialize()
        with self.assertRaisesRegex(v.VaultBlocked,'EVIDENCE_ID_INVALID'):
            v.register(self.root,self.src,'../escape',confirmed=True,strict=False)

    def test_vault_symlink_rejected(self):
        self.root.symlink_to(Path(self.t.name),target_is_directory=True)
        with self.assertRaisesRegex(v.VaultBlocked,'SYMLINK'):
            self.initialize()

    def test_no_retrieval_without_operator(self):
        self.initialize();self.register()
        with self.assertRaisesRegex(v.VaultBlocked,'CONFIRMATION'):
            v.retrieve(self.root,self.id,Path(self.t.name)/'out.zip',strict=False)

    def test_vault_retrieval_to_self_blocked(self):
        self.initialize();self.register()
        with self.assertRaisesRegex(v.VaultBlocked,'DESTINATION_UNSAFE'):
            v.retrieve(self.root,self.id,self.root/'intake'/'x.zip',confirmed=True,strict=False)

    def test_mode_drift_blocked(self):
        self.initialize();self.root.chmod(0o777)
        with self.assertRaisesRegex(v.VaultBlocked,'DIRECTORY_MODE_DRIFT'):
            v.inspect(self.root,strict=False)

    def test_no_cleanup_or_authority_commands(self):
        p=v.build_arg_parser() if hasattr(v,'build_arg_parser') else None
        self.assertFalse(hasattr(v,'delete'))
        self.assertFalse(hasattr(v,'authorize'))
        self.assertFalse(hasattr(v,'launch'))
        self.assertIsNone(p)

if __name__=='__main__':unittest.main()
