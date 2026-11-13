import importlib.util
import json
from pathlib import Path
import socket
import unittest
from unittest import mock
import pytest
from scripts.coordination.control_plane.worker_runtime import (
    cf10_batch_g_inference_bridge_contract_v0_1 as g,
    cf10_batch_g_inference_client_v0_1 as child,
)
U='forprint-cf10-batchg-'+'a'*16+'.service'
D='/run/'+U.removesuffix('.service')

class TestBatchG:
    def test_source_check_not_authorizing(self):
        out=g.source_check()
        assert out['authority'] is False and len(out['open_gates'])==5
        assert out['local_fixture_only'] is True
    def test_expected_shape(self):
        p=g.plan(unit=U,lab_dir=D,private_file=D+'/fake_credential.txt')
        assert p['status']==g.STATUS
        assert p['live_admission'] is False
        assert p['g1_g5_closed'] is False
        assert p['copilot_executed'] is False
        assert p['provider_credentials_used'] is False
        assert p['kernel_terminal_proven'] is False
        assert len(p['open_gates'])==5
    def test_props_retain_f_hardening(self):
        p=g.plan(unit=U,lab_dir=D,private_file=D+'/fake_credential.txt')['properties']
        for k,v in {'User':'forprint-runner','Group':'forprint-runner','NoNewPrivileges':'yes',
                    'ProtectSystem':'strict','PrivateNetwork':'yes',
                    'RestrictAddressFamilies':'AF_UNIX','IPAddressDeny':'any',
                    'Restart':'no','RuntimeMaxSec':'60s','KillMode':'control-group',
                    'PrivateDevices':'yes','ProtectHome':'yes','Delegate':'no'}.items():assert p[k]==v
        assert 'StateDirectory' not in p and 'StateDirectoryMode' not in p
        assert p['InaccessiblePaths']=='/var/lib/forprint-runner '+D+'/fake_credential.txt'
    @pytest.mark.parametrize('unit',[
        'forprint-cf10-batchf-'+'a'*16+'.service',
        'forprint-cf10-batchg-'+'g'*16+'.service',
        'forprint-cf10-batchg-'+'a'*15+'.service',
        'forprint-cf10-batchg-'+'a'*16+'.service/../service',
        'foo.service', None, 27])
    def test_unit_reject(self,unit):
        with pytest.raises(g.BridgeHold):g.request_id(unit)
    def test_path_escape_reject(self):
        with pytest.raises(g.BridgeHold):g.plan(unit=U,lab_dir=D+'/..',private_file=D+'/fake_credential.txt')
        with pytest.raises(g.BridgeHold):g.plan(unit=U,lab_dir=D,private_file='/tmp/fake_credential.txt')
    def test_allowed_fixture_roundtrip(self):
        q=g.fixture_request(U)
        assert g.broker_decide(q,U)==g.fixture_reply(U)
        assert g.validate_positive_reply(g.fixture_reply(U),U) is True
    def test_denied_unapproved_route(self):
        out=g.broker_decide(g.fixture_request(U,'external.anywhere'),U)
        assert out=={'schema':g.RESPONSE_SCHEMA,'status':'DENIED_ROUTE','request_id':g.request_id(U)}
    def test_invalid_fields(self):
        q=g.fixture_request(U);q['unexpected']=1
        with pytest.raises(g.BridgeHold):g.broker_decide(q,U)
    def test_invalid_request_id(self):
        q=g.fixture_request(U);q['request_id']='0'*24
        with pytest.raises(g.BridgeHold):g.broker_decide(q,U)
    def test_invalid_sha(self):
        q=g.fixture_request(U);q['payload_sha256']='0'*64
        with pytest.raises(g.BridgeHold):g.broker_decide(q,U)
    def test_invalid_schema(self):
        q=g.fixture_request(U);q['schema']='untrusted'
        with pytest.raises(g.BridgeHold):g.broker_decide(q,U)
    def test_type_confusion(self):
        q=g.fixture_request(U);q['route']=['fixture.inference']
        with pytest.raises(g.BridgeHold):g.broker_decide(q,U)
    def test_denied_wrong_response(self):
        out=g.fixture_reply(U);out['response_sha256']='0'*64
        with pytest.raises(g.BridgeHold):g.validate_positive_reply(out,U)
    def test_other_attempt_replay_reject(self):
        u2='forprint-cf10-batchg-'+'b'*16+'.service'
        with pytest.raises(g.BridgeHold):g.broker_decide(g.fixture_request(U),u2)
        with pytest.raises(g.BridgeHold):g.validate_positive_reply(g.fixture_reply(U),u2)
    def test_source_check_closes_on_gate_on(self):
        from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
        with mock.patch.object(launcher,'LIVE_CUTOVER_ENABLED',True):
            with pytest.raises(g.BridgeHold):g.source_check()
        assert launcher.LIVE_CUTOVER_ENABLED is False
    def test_client_protocol_matches_broker(self):
        assert child.request(U)==g.fixture_request(U)
        assert child.request(U,'external.unapproved')==g.fixture_request(U,'external.unapproved')
        assert child.reply(U)==g.fixture_reply(U)
    def test_client_frame_roundtrip_socketpair(self):
        a,b=socket.socketpair()
        with a,b:
            assert child._send(a,child.request(U)) is True
            assert child._line(b)==g.fixture_request(U)
    def test_child_only_unix_connect(self):
        source=Path(child.__file__).read_text()
        assert 'socket.AF_UNIX' in source
        assert 'socket.AF_INET' in source
        assert 'socket.AF_INET6' in source
        assert 'subprocess.' not in source
        assert 'urllib.' not in source
        assert 'requests.' not in source
        assert 'https://' not in source
    def test_child_not_working_without_path_binding(self):
        assert child.main(['x',D+'/bad',D+'/control.sock',D+'/fake_credential.txt',U])==73
        assert child.main(['x',D+'/inference.sock',D+'/control.sock','/tmp/fake',U])==73
    def test_child_invalid_unit_denied(self):
        assert child.main(['x','bad','bad','bad','bad'])==72
    def test_profile_sha_deterministic(self):
        p=g.plan(unit=U,lab_dir=D,private_file=D+'/fake_credential.txt')
        assert p['profile_sha256']==g.digest(p['properties'])
