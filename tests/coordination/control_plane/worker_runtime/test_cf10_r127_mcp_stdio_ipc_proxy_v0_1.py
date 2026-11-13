from __future__ import annotations
import io
import json
import os
import socket
import struct
import threading
import pytest

from scripts.coordination.control_plane.worker_runtime import cf10_r127_mcp_stdio_ipc_proxy_v0_1 as m


def frame(method, ident=None, params=None):
    doc = {'jsonrpc':'2.0','method':method}
    if ident is not None: doc['id']=ident;doc['params']=params
    return m.encode(doc)


def transcript():
    return b''.join([
      frame('initialize','0001',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'CopilotCLI','version':'1.0'}}),
      frame('notifications/initialized'),
      frame('tools/list','0002',{}),
      frame('tools/call','0003',{'name':'run_repo_head','arguments':{}}),
    ])


def server_once(sock, report):
    try:
        f = sock.makefile('rb', buffering=0)
        for i in range(4):
            req = m.decode(m.read_frame(f))
            if i == 1:continue
            if i == 0: result={'protocolVersion':'2025-06-18','capabilities':{},'serverInfo':{'name':'ForPrintValidation','version':'0.2.0'}}
            elif i == 2:result={'tools':[{'name':'run_repo_head','inputSchema':{'type':'object'}}, {'name':'run_repo_status','inputSchema':{'type':'object'}}]}
            else:result={'isError':False,'structuredContent':{'return_code':0,'outcome':'completed','timed_out':False,'evidence_digest':'a'*64,'authority':{'release_allowed':False,'commit_allowed':False}}}
            sock.sendall(m.encode({'jsonrpc':'2.0','id':req['id'],'result':result}))
        report.append('PASS')
    except BaseException as exc:
        report.append(type(exc).__name__ + ':' + str(exc))
    finally:sock.close()


def test_full_real_socket_stdio_exchange_and_tool_filter():
    a,b=socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM)
    a.settimeout(3);b.settimeout(3)
    report=[]
    thread=threading.Thread(target=server_once,args=(b,report),daemon=True)
    thread.start()
    src=io.BytesIO(transcript());dest=io.BytesIO()
    try:r=m.run_session(src,dest,a)
    finally:a.close();thread.join(timeout=5)
    assert report == ['PASS']
    assert r == {'frames_forwarded':4,'read_only_calls_forwarded':1,'extra_calls_allowed':False,'authority_granted':False,'worker_launched':False}
    lines=[json.loads(x) for x in dest.getvalue().splitlines()]
    assert [line['id'] for line in lines] == ['0001','0002','0003']
    assert [t['name'] for t in lines[1]['result']['tools']] == ['run_repo_head']
    assert src.tell() == len(transcript())


def test_source_does_not_expose_other_tools():
    seen=set()
    for i,method in enumerate(m.METHODS):
        assert m.CAPABILITY != 'run_validation_suite'
        if i!=3:continue
        valid=m.decode(frame(method,'0003',{'name':'run_repo_head','arguments':{}}))
        assert m.validate_request(valid,i,seen)=='0003'
        for wrong in ('run_validation_suite','run_repo_status','run_repo_diff_check','read_completed_validation_evidence'):
            with pytest.raises(m.IPCProxyHold,match='TOOL_DENIED'):
                m.validate_request(m.decode(frame(method,'0004',{'name':wrong,'arguments':{}})),i,set())


def test_response_rejects_widened_auth():
    r={'jsonrpc':'2.0','id':'0003','result':{'isError':False,'structuredContent':{'return_code':0,'timed_out':False,'outcome':'completed','evidence_digest':'a'*64,'authority':{'release_allowed':True}}}}
    with pytest.raises(m.IPCProxyHold,match='AUTHORITY_WIDENED'):m.validate_response(r,'0003',3)


def test_response_missing_evidence_rejected():
    r={'jsonrpc':'2.0','id':'0003','result':{'isError':False,'structuredContent':{'return_code':0,'timed_out':False,'outcome':'completed','authority':{'release_allowed':False}}}}
    with pytest.raises(m.IPCProxyHold,match='EVIDENCE_DIGEST'):m.validate_response(r,'0003',3)


def test_response_errors_rejected():
    with pytest.raises(m.IPCProxyHold,match='RESPONSE_CORRUPT'):
        m.validate_response({'jsonrpc':'2.0','id':'0002','error':{'code':-1}},'0002',2)


def test_tool_list_must_contain_exactly_one_allowed():
    for tools in ([],[{'name':'run_repo_status'}],[{'name':'run_repo_head'}]*2):
        with pytest.raises(m.IPCProxyHold,match='TOOLS_ALLOWLIST'):
            m.validate_response({'jsonrpc':'2.0','id':'x','result':{'tools':tools}},'x',2)


def test_duplicate_json_keys_rejected():
    with pytest.raises(m.IPCProxyHold,match='JSON_DUPLICATE_KEY'):
        m.decode(b'{"jsonrpc":"2.0","jsonrpc":"2.0"}\n')


def test_oversized_frame_rejected():
    with pytest.raises(m.IPCProxyHold,match='FRAME_OVERSIZE'):
        m.read_frame(io.BytesIO(b'a'*(m.MAX_FRAME+200)+b'\n'))


def test_missing_newline_rejected():
    with pytest.raises(m.IPCProxyHold,match='FRAME_LENGTH'):m.decode(b'{}')


def test_disallowed_params_rejected():
    with pytest.raises(m.IPCProxyHold,match='TOOL_DENIED'):
        m.validate_request(m.decode(frame('tools/call','0004',{'name':'run_repo_head','arguments':{'path':'/etc'}})),3,set())


def test_wrong_method_order_rejected():
    with pytest.raises(m.IPCProxyHold,match='METHOD_ORDER'):
        m.validate_request(m.decode(frame('tools/call','0001',{'name':'run_repo_head','arguments':{}})),0,set())


def test_reused_jsonrpc_id_rejected():
    seen={'0002'}
    with pytest.raises(m.IPCProxyHold,match='REQUEST_ID'):
        m.validate_request(m.decode(frame('tools/list','0002',{})),2,seen)


def test_client_name_can_be_copilot_not_only_fixture():
    seen=set(); req=m.decode(transcript().splitlines(keepends=True)[0])
    assert m.validate_request(req,0,seen)=='0001'


def test_socket_scope_and_attempt_validation():
    valid='/run/forprint-cf10-r125-abcdef0123456789/mcp.sock'
    assert m.validate_identity(socket_path=m.Path(valid),attempt='cf10-a055',epoch='epoch-5',source_head='b'*40,capsule_id=m.CAPSULE)
    for candidate in ('/tmp/mcp.sock','/run/forprint-cf10-r125-../mcp.sock','/run/forprint-cf10-r125-abcdef0123456789/../mcp.sock'):
        with pytest.raises(m.IPCProxyHold,match='SOCKET_PATH'):
            m.validate_identity(socket_path=m.Path(candidate),attempt='cf10-a055',epoch='epoch-5',source_head='b'*40,capsule_id=m.CAPSULE)


def test_no_claim_or_launch_symbols():
    src=m.Path(m.__file__).read_text()
    assert 'subprocess.Popen(' not in src and 'os.execv(' not in src
    assert 'LIVE_CUTOVER' not in src
