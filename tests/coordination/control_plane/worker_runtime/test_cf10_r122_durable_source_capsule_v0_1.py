"""R122 exact Git source-only durable capsule negative and fixture regressions."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest import mock

SRC=Path(__file__).resolve().parents[4]/'scripts/coordination/control_plane/worker_runtime/cf10_r122_durable_source_capsule_v0_1.py'
spec=importlib.util.spec_from_file_location('r122_capsule', SRC)
r122=importlib.util.module_from_spec(spec);spec.loader.exec_module(r122)

class DurableCapsuleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='r122-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.store=self.root/'store';self.store.mkdir(mode=0o755);self.store.chmod(0o750)
        self.uid=os.geteuid();self.gid=os.getegid()
        os.chown(self.store,self.uid,self.gid)
        self.filebytes={
            'scripts/coordination/control_plane/worker_runtime/worker_validation_mcp.py': b'from __future__ import annotations\n',
            'scripts/validation/run_validation_suite_v0_1.py': b'"""frozen"""\n',
            'scripts/__init__.py': b'',
            'scripts/validation/__init__.py': b'',
            'coordination/registry/demo.yaml': b'suite: 1\n',
        }
        self.records=sorted((k,r122.git_blob(v)) for k,v in self.filebytes.items())
        self.obj={r122.git_blob(v):v for v in self.filebytes.values()}
    def fetch(self,oid):return self.obj[oid]
    def publish(self):return r122.publish(store=self.store,owner=self.uid,group=self.gid,records=self.records,fetch=self.fetch)
    def fullpath(self):return self.store/self.publish()['capsule_id']

    def test_publish_readback_and_runtime_filename(self):
        a=self.publish()
        self.assertEqual(a['action'],'PUBLISHED_NEW')
        self.assertEqual(a['source_files'],5)
        self.assertFalse(a['worker_authorized'])
        self.assertFalse(a['runner_writable'])
        self.assertEqual((self.store/a['capsule_id']/'source'/r122.MCP).read_bytes(),self.filebytes[r122.MCP])
        self.assertEqual(r122.verify_capsule(self.store/a['capsule_id'],store=self.store,owner=self.uid,group=self.gid)['source_files'],5)
    def test_idempotent_reuse_verified(self):
        one=self.publish();two=self.publish()
        self.assertEqual(one['capsule_id'],two['capsule_id'])
        self.assertEqual(two['action'],'REUSED_VERIFIED')
    def test_pinned_git_not_mutable_worktree(self):
        self.filebytes[r122.SUITE]=b'WORKTREE MUTATION\n'
        self.assertEqual((self.store/self.publish()['capsule_id']/'source'/r122.SUITE).read_bytes(),b'"""frozen"""\n')
    def test_mutated_content_denied(self):
        directory=self.fullpath();f=directory/'source'/r122.MCP
        f.chmod(0o640);f.write_text('evil',encoding='utf8')
        with self.assertRaisesRegex(r122.Hold,'CAPSULE_DIGEST'):r122.verify_capsule(directory,store=self.store,owner=self.uid,group=self.gid)
    def test_changed_manifest_denied(self):
        path=self.fullpath()/'MANIFEST.json'
        raw=json.loads(path.read_text());raw['state']='ACTIVATED'
        path.write_bytes(r122.canonical(raw))
        with self.assertRaisesRegex(r122.Hold,'MANIFEST_IDENTITY'):r122.verify_capsule(path.parent,store=self.store,owner=self.uid,group=self.gid)
    def test_extra_file_denied(self):
        directory=self.fullpath();p=directory/'source'/'extra.py';p.write_text('x');os.chown(p,self.uid,self.gid);p.chmod(0o640)
        with self.assertRaisesRegex(r122.Hold,'CAPSULE_FILESET'):r122.verify_capsule(directory,store=self.store,owner=self.uid,group=self.gid)
    def test_symlink_file_denied(self):
        directory=self.fullpath();path=directory/'source'/r122.SUITE;path.unlink();path.symlink_to('/etc/hosts')
        with self.assertRaisesRegex(r122.Hold,'PATH_OWNER_MODE'):r122.verify_capsule(directory,store=self.store,owner=self.uid,group=self.gid)
    def test_symlink_directory_denied(self):
        directory=self.fullpath();a=directory/'source'/'scripts'/'validation'; target=self.root/'external';target.mkdir();
        import shutil;shutil.rmtree(a);a.symlink_to(target)
        with self.assertRaisesRegex(r122.Hold,'PATH_OWNER_MODE'):r122.verify_capsule(directory,store=self.store,owner=self.uid,group=self.gid)
    def test_group_writable_capsule_denied(self):
        directory=self.fullpath();directory.chmod(0o775)
        with self.assertRaisesRegex(r122.Hold,'PATH_OWNER_MODE'):r122.verify_capsule(directory,store=self.store,owner=self.uid,group=self.gid)
    def test_group_writable_file_denied(self):
        directory=self.fullpath();(directory/'source'/r122.MCP).chmod(0o660)
        with self.assertRaisesRegex(r122.Hold,'PATH_OWNER_MODE'):r122.verify_capsule(directory,store=self.store,owner=self.uid,group=self.gid)
    def test_corrupted_existing_capsule_never_overwritten(self):
        directory=self.fullpath();(directory/'source'/r122.MCP).write_bytes(b'change')
        with self.assertRaises(r122.Hold):self.publish()
        self.assertEqual((directory/'source'/r122.MCP).read_bytes(),b'change')
    def test_wrong_store_scope(self):
        directory=self.fullpath()
        with self.assertRaisesRegex(r122.Hold,'VERIFY_SCOPE'):
            r122.verify_capsule(directory,store=self.root/'other',owner=self.uid,group=self.gid)
    def test_wrong_owner_denied(self):
        directory=self.fullpath()
        with self.assertRaisesRegex(r122.Hold,'PATH_OWNER_MODE'):
            r122.verify_capsule(directory,store=self.store,owner=self.uid+1,group=self.gid)
    def test_traversal_and_private_names_denied(self):
        for rel in ('../escape.py','scripts/../escape.py','scripts//bad.py','scripts/.env','tmp/script.py','scripts/💙.py','coordination/config/secret.json','secrets/key.json'):
            self.assertFalse(r122.approved_source(rel),rel)
    def test_missing_required(self):
        with self.assertRaisesRegex(r122.Hold,'SOURCE_SET_INCOMPLETE'):
            r122.parse_tree(b'100644 blob '+b'a'*40+b'\tscripts/__init__.py\0')
    def test_unicode_unrelated_tree_is_ignored(self):
        raw=b'100644 blob '+b'a'*40+b'\tcoordination/\xd0\x90.mhtml\0'
        raw+=b''.join(('100644 blob '+oid+'\t'+name+'\0').encode('ascii') for name,oid in self.records)
        self.assertEqual(r122.parse_tree(raw),self.records)
    def test_malformed_unrelated_git_header_fails(self):
        with self.assertRaisesRegex(r122.Hold,'GIT_TREE_RECORD'):
            r122.parse_tree(b'INVALID blob '+b'a'*40+b'\tcoordination/\xd0\x90.mhtml\0')
    def test_symlink_source_git_mode_denied(self):
        raw=b''.join((('120000' if name==r122.MCP else '100644')+' blob '+oid+'\t'+name+'\0').encode('ascii') for name,oid in self.records)
        with self.assertRaisesRegex(r122.Hold,'SOURCE_NOT_REGULAR_BLOB'):r122.parse_tree(raw)
    def test_git_oid_mismatch_denied(self):
        with self.assertRaisesRegex(r122.Hold,'SOURCE_BLOB_MISMATCH'):
            r122.compile_manifest(self.records,lambda _:b'tampered')
    def test_duplicate_source_denied(self):
        dup=self.records+[self.records[0]]
        with self.assertRaisesRegex(r122.Hold,'SOURCE_ORDER_DUPLICATE'):
            r122.compile_manifest(dup,self.fetch)
    def test_manifest_deterministic(self):
        a=r122.compile_manifest(self.records,self.fetch);b=r122.compile_manifest(self.records,self.fetch)
        self.assertEqual(r122.manifest_id(a),r122.manifest_id(b))
        self.assertEqual(hashlib.sha256(r122.canonical(a)).hexdigest(),r122.manifest_id(a)[len(r122.PREFIX):])
    def test_authority_explicitly_denied(self):
        doc=r122.compile_manifest(self.records,self.fetch)
        self.assertFalse(any(doc['authority'].values()))
        self.assertEqual(doc['state'],'PUBLISHED_SOURCE_ONLY_NOT_ACTIVATED')
    def test_no_tmp_runtime_contract(self):
        self.assertNotIn('/tmp',str(r122.STORE))
        self.assertNotIn('tmp/',str(r122.STORE))
    def test_canonical_paths_are_stable(self):
        self.assertEqual(r122.PROJECT.as_posix(),'/srv/software_development/forprint-project/forprint_system_blueprint')
        self.assertEqual(r122.PINNED_HEAD,'12c668e0cc309bd1162154ae12f7281603cf7bfa')
    def test_stable_tree_intermediate_modes(self):
        folder=self.fullpath()
        self.assertEqual(stat.S_IMODE((folder/'source'/'scripts').stat().st_mode),0o750)
        self.assertEqual(stat.S_IMODE((folder/'source'/r122.MCP).stat().st_mode),0o640)
    def test_manifest_unknown_key_has_identity_mismatch(self):
        folder=self.fullpath();mf=folder/'MANIFEST.json';a=json.loads(mf.read_text());a['extra']=1;mf.write_bytes(r122.canonical(a))
        with self.assertRaises(r122.Hold):r122.verify_capsule(folder,store=self.store,owner=self.uid,group=self.gid)
    def test_unauthorized_new_executable_denied(self):
        folder=self.fullpath();p=folder/'script.sh';p.write_text('echo hi');p.chmod(0o755)
        with self.assertRaises(r122.Hold):r122.verify_capsule(folder,store=self.store,owner=self.uid,group=self.gid)
    def test_missing_file_denied(self):
        folder=self.fullpath();(folder/'source'/r122.SUITE).unlink()
        with self.assertRaises((FileNotFoundError,r122.Hold)):r122.verify_capsule(folder,store=self.store,owner=self.uid,group=self.gid)
    def test_source_from_git_fixture_commit(self):
        repo=self.root/'repo';repo.mkdir()
        subprocess.run(['/usr/bin/git','-C',str(repo),'init','-q'],check=True)
        for name,data in self.filebytes.items():
            p=repo/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(data)
        bad=repo/'coordination'/'Примітка.mhtml';bad.write_text('outside allowlist')
        subprocess.run(['/usr/bin/git','-C',str(repo),'add','.'],check=True)
        env={**os.environ,'GIT_AUTHOR_NAME':'ForPrint Test','GIT_AUTHOR_EMAIL':'example@example.invalid',
             'GIT_COMMITTER_NAME':'ForPrint Test','GIT_COMMITTER_EMAIL':'example@example.invalid'}
        subprocess.run(['/usr/bin/git','-C',str(repo),'commit','-qm','r122 fixture'],check=True,env=env)
        tree=subprocess.check_output(['/usr/bin/git','-C',str(repo),'ls-tree','-r','-z','HEAD','--','scripts','coordination'])
        self.assertEqual(r122.parse_tree(tree),self.records)
        self.filebytes[r122.SUITE]=b'LOCAL CHANGED'
        from_git=lambda oid:subprocess.check_output(['/usr/bin/git','-C',str(repo),'cat-file','blob',oid])
        result=r122.publish(store=self.store,owner=self.uid,group=self.gid,records=self.records,fetch=from_git)
        self.assertEqual((self.store/result['capsule_id']/'source'/r122.SUITE).read_bytes(),b'"""frozen"""\n')
    def test_failed_blob_cleanups_staging(self):
        with self.assertRaisesRegex(r122.Hold,'SOURCE_BLOB_MISMATCH'):
            r122.publish(store=self.store,owner=self.uid,group=self.gid,records=self.records,fetch=lambda _:b'mismatch')
        self.assertEqual([p.name for p in self.store.iterdir()],['.r122-publish.lock'])

if __name__=='__main__':unittest.main()
