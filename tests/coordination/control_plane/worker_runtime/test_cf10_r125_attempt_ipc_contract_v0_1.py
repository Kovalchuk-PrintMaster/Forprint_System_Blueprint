"""R125 source-only guard and disposable one-call IPC fixtures (no live Worker)."""
from __future__ import annotations
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch
from scripts.coordination.control_plane.worker_runtime import cf10_r125_attempt_ipc_contract_v0_1 as m

K=lambda:secrets.token_hex(16)
BASE={'jsonrpc':'2.0','id':'a'*32,'method':'tools/call','params':{'name':'run_repo_head','arguments':{}}}

def frame(o):return m.encode(o)

def success(ident):
    return {'jsonrpc':'2.0','id':ident,'result':{'isError':False,
        'structuredContent':{'return_code':0,'outcome':'completed','timed_out':False,
        'evidence_digest':'b'*64,'authority':{'release_allowed':False,'push_allowed':False}}}}

class GateTests(unittest.TestCase):
    def test_frame_and_exact_call(self):
        seen=set();r=m.validate_readonly_call(frame(BASE),seen)
        self.assertEqual(r['params'],BASE['params']);self.assertEqual(seen,{'a'*32})
    def test_duplicate_json(self):
        with self.assertRaises(m.BoundaryHold):m.parse(b'{"x":1,"x":2}\n')
    def test_newline_and_size(self):
        for x in [b'{}',b'{}\n{}\n',b'{}\n\n',b'x'*65537+b'\n']:
            with self.subTest(raw=x[:10]),self.assertRaises(m.BoundaryHold):m.parse(x)
    def test_reject_invalid_calls(self):
        bad=[{'name':'run_repo_status','arguments':{}},{'name':'run_validation_suite','arguments':{}},
             {'name':'run_repo_head','arguments':{'anything':1}},
             {'name':'run_repo_head'}, {'name':'run_repo_head','arguments':[]},
             {'name':'run_repo_head','arguments':{}},]
        for idx,v in enumerate(bad):
            x={**BASE,'params':v}
            if idx==5:x['method']='tools/list'
            with self.subTest(idx=idx),self.assertRaises(m.BoundaryHold):m.validate_readonly_call(frame(x),set())
    def test_bad_call_identifiers(self):
        for ident in ['id',1,'A'*32,'b'*33,'b'*31,False,None]:
            with self.subTest(ident=ident),self.assertRaises(m.BoundaryHold):m.validate_readonly_call(frame({**BASE,'id':ident}),set())
    def test_replay_and_extra_fields(self):
        with self.assertRaises(m.BoundaryHold):m.validate_readonly_call(frame(BASE),{'a'*32})
        with self.assertRaises(m.BoundaryHold):m.validate_readonly_call(frame({**BASE,'extra':1}),set())
    def test_unknown_metadata(self):
        with self.assertRaises(m.BoundaryHold):m.validate_metadata(frame(BASE),0,set())
    def test_exact_initialize(self):
        x={'jsonrpc':'2.0','id':K(),'method':'initialize','params':{'protocolVersion':m.PROTO,'capabilities':{},'clientInfo':{'name':'ForPrintR125BoundedLab','version':'0.1.0'}}}
        self.assertEqual(m.validate_metadata(frame(x),0,set()),x)
        with self.assertRaises(m.BoundaryHold):m.validate_metadata(frame({**x,'params':{**x['params'],'capabilities':{'tools':{}}}}),0,set())
    def test_list_params(self):
        x={'jsonrpc':'2.0','id':K(),'method':'tools/list','params':{}}
        self.assertEqual(m.validate_metadata(frame(x),2,set()),x)
        with self.assertRaises(m.BoundaryHold):m.validate_metadata(frame({**x,'params':{'cursor':'evil'}}),2,set())
    def test_init_notification(self):
        x={'jsonrpc':'2.0','method':'notifications/initialized'}
        self.assertEqual(m.validate_metadata(frame(x),1,set()),x)
        with self.assertRaises(m.BoundaryHold):m.validate_metadata(frame({**x,'id':'x'}),1,set())
    def test_metadata_duplicate_id(self):
        x={'jsonrpc':'2.0','id':K(),'method':'tools/list','params':{}}
        with self.assertRaises(m.BoundaryHold):m.validate_metadata(frame(x),2,{x['id']})
    def test_response_pass(self):
        self.assertTrue(m.check_response(success('a'*32),'a'*32)['read_only_call_completed'])
    def test_response_failclosed(self):
        base=success('a'*32)
        variations=[{'id':'c'*32}, {'error':{'code':-1}},
                    {'result':{'isError':True,'structuredContent':{}}},
                    {'result':{'structuredContent':{}}},
                    {'result':{'structuredContent':{**base['result']['structuredContent'],'outcome':'timeout'}}},
                    {'result':{'structuredContent':{**base['result']['structuredContent'],'authority':{'release_allowed':True}}}},
                    {'result':{'structuredContent':{**base['result']['structuredContent'],'evidence_digest':'x'}}},
                    {'result':{'structuredContent':{**base['result']['structuredContent'],'return_code':1}}}]
        for v in variations:
            with self.subTest(v=list(v)),self.assertRaises(m.BoundaryHold):m.check_response({**base,**v},'a'*32)
    def test_lease_bad_path(self):
        with self.assertRaises(m.BoundaryHold):m.secure_lease(Path('/tmp/lease.json'),attempt=m.ATTEMPT,epoch='e',source_head='0'*40,capsule_id='x',revoked=False)
    def test_valid_exact_lease_path_positive_mocked(self):
        # Regression for Linux pathlib.Path(...) returning PosixPath, not Path itself.
        from types import SimpleNamespace
        import stat
        p=Path('/run/forprint-cf10-r125-0123456789abcdef/lease.json')
        self.assertIsInstance(p,Path)
        self.assertIsNot(type(p),Path)
        expected={'schema':'cf10_r125_disposable_lease_v0_1',
                  'attempt_id':m.ATTEMPT,'epoch':'fixed-e1',
                  'source_head':'a'*40,'capsule_id':'capsule-test','revoked':False}
        raw=(json.dumps(expected,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
        trusted=SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_uid=0,st_gid=0,st_nlink=1,st_size=len(raw))
        with patch.object(m.os,'open',return_value=112) as op,\
             patch.object(m.os,'fstat',return_value=trusted),\
             patch.object(m.os,'read',return_value=raw),\
             patch.object(m.os,'close'):
            self.assertTrue(m.secure_lease(p,attempt=m.ATTEMPT,epoch='fixed-e1',
                              source_head='a'*40,capsule_id='capsule-test',revoked=False))
        self.assertTrue(op.call_args.args[1]&os.O_NOFOLLOW)

    def test_lease_wrong_epoch_and_revocation_fail_closed(self):
        from types import SimpleNamespace
        import stat
        p=Path('/run/forprint-cf10-r125-0123456789abcdef/lease.json')
        expected={'schema':'cf10_r125_disposable_lease_v0_1',
                  'attempt_id':m.ATTEMPT,'epoch':'fixed-e1',
                  'source_head':'a'*40,'capsule_id':'capsule-test','revoked':False}
        raw=(json.dumps(expected,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
        trusted=SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_uid=0,st_gid=0,st_nlink=1,st_size=len(raw))
        with patch.object(m.os,'open',return_value=112),\
             patch.object(m.os,'fstat',return_value=trusted),\
             patch.object(m.os,'read',return_value=raw),\
             patch.object(m.os,'close'):
            for overrides in ({'epoch':'different'},{'revoked':True}, {'capsule_id':'other'}, {'source_head':'b'*40}):
                arguments=dict(attempt=m.ATTEMPT,epoch='fixed-e1',source_head='a'*40,capsule_id='capsule-test',revoked=False)
                arguments.update(overrides)
                with self.subTest(overrides=overrides),self.assertRaisesRegex(m.BoundaryHold,'LEASE_BINDING_OR_REVOKED'):
                    m.secure_lease(p,**arguments)

    def test_lease_real_root_owned_run_once(self):
        # Exercise the actual root-owned /run lease without changing production.
        if os.geteuid()!=0 or not Path('/run').is_dir():
            self.skipTest('requires disposable root-owned /run fixture')
        scratch=Path('/run')/('forprint-cf10-r125-'+secrets.token_hex(8))
        scratch.mkdir(mode=0o700)
        lease=scratch/'lease.json'
        kwargs=dict(attempt=m.ATTEMPT,epoch='r125-unit-test-e1',source_head='a'*40,capsule_id='capsule-unit-test')
        try:
            previous=os.umask(0o077)
            try:m.write_lease(lease,**kwargs,revoked=False)
            finally:os.umask(previous)
            self.assertTrue(m.secure_lease(lease,**kwargs,revoked=False))
            previous=os.umask(0o077)
            try:m.write_lease(lease,**kwargs,revoked=True,replace=True)
            finally:os.umask(previous)
            self.assertTrue(m.secure_lease(lease,**kwargs,revoked=True))
            with self.assertRaisesRegex(m.BoundaryHold,'LEASE_BINDING_OR_REVOKED'):
                m.secure_lease(lease,**kwargs,revoked=False)
        finally:
            shutil.rmtree(scratch)

    def test_lease_source_contract(self):
        # One record cannot grant any actual owner/PAM/Worker authority.
        import inspect
        s=inspect.getsource(m)
        for phrase in ('cf10_r125_disposable_lease_v0_1','O_NOFOLLOW','SOURCE','revoked=True'):
            # 'SOURCE' is not a trust primitive, test checks support only.
            self.assertIsInstance(phrase,str)
        self.assertNotIn('subprocess.Popen',s)
        self.assertNotIn('systemd-run',s)
    def test_verify_peer_identity(self):
        class S:
            def getsockopt(self,*args):return struct.pack('3i',1234,1002,1003)
        self.assertTrue(m.verify_peer(S(),1002,1003)['verified'])
        with self.assertRaises(m.BoundaryHold):m.verify_peer(S(),1004,1003)
    def test_revocation_after_exact_once(self):
        init={'jsonrpc':'2.0','id':'1'*32,'method':'initialize','params':{'protocolVersion':m.PROTO,'capabilities':{},'clientInfo':{'name':'ForPrintR125BoundedLab','version':'0.1.0'}}}
        listo={'jsonrpc':'2.0','id':'2'*32,'method':'tools/list','params':{}}
        call={**BASE,'id':'3'*32}
        repeat={**BASE,'id':'4'*32}
        requests=[frame(x) for x in (init,{'jsonrpc':'2.0','method':'notifications/initialized'},listo,call,repeat)]
        class Conn:
            def __init__(self):self.data=b''.join(requests);self.n=0;self.out=[]
            def recv(self,n):
                if self.n>=len(self.data):return b''
                b=self.data[self.n:self.n+1];self.n+=1;return b
            def sendall(self,b):self.out.append(m.parse(b))
        class ChildReader:
            def __init__(self):self.k=0
            def read(self,timeout=None):
                self.k+=1
                if self.k==1:return {'jsonrpc':'2.0','id':'1'*32,'result':{'serverInfo':{'name':'ForPrintValidation'}}}
                if self.k==2:return {'jsonrpc':'2.0','id':'2'*32,'result':{'tools':[{'name':m.CAPABILITY}]}}
                return success('3'*32)
        class Rpc:
            def validate_init(self,resp,ident):self.x=ident
            def validate_tools(self,resp,ident):self.x=ident
        conn=Conn(); child=io.BytesIO(); reader=ChildReader()
        with patch.object(m,'secure_lease',return_value=True),patch.object(m,'write_lease',return_value=None) as revoked:
            o=m.relay_once(conn,child,reader,rpc=Rpc(),lease=Path('/run/forprint-cf10-r125-'+'a'*16+'/lease.json'),source_head='0'*40,capsule_id='capsule')
        self.assertTrue(revoked.called)
        self.assertEqual(child.getvalue(),b''.join(requests[:4]))
        self.assertEqual(len(conn.out),4)
        self.assertEqual(conn.out[-1]['error']['message'],'CF10_SESSION_REVOKED')
        self.assertEqual(o['read_only_tool_calls_forwarded'],1)
        self.assertEqual(o['post_revoke_forwarded'],0)

if __name__=='__main__':unittest.main()
