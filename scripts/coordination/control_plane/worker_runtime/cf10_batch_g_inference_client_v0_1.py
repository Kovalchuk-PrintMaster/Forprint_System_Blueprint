"""Disposable sandbox process. Only Unix sockets; no real provider or credentials."""
import hashlib
import json
import os
import re
import socket
import sys
import time
# Exact public fixture protocol. No imports from the project or provider runtime:
# /run/worker.py must be stand-alone under Python -I and systemd isolation.
REQUEST_SCHEMA='cf10_batch_g_disposable_inference_request_v0_1'
RESPONSE_SCHEMA='cf10_batch_g_disposable_inference_response_v0_1'
PAYLOAD_SHA=hashlib.sha256(b'CF10_BATCH_G_PUBLIC_DISPOSABLE_FIXTURE').hexdigest()
MAX_FRAME=1024

def request_id(unit):
    return hashlib.sha256(('cf10-batch-g|'+unit).encode('ascii')).hexdigest()[:24]

def request(unit,route='fixture.inference'):
    return {'schema':REQUEST_SCHEMA,'request_id':request_id(unit),
            'route':route,'payload_sha256':PAYLOAD_SHA}

def reply(unit):
    return {'schema':RESPONSE_SCHEMA,'status':'OK_FIXTURE_ONLY',
            'request_id':request_id(unit),
            'response_sha256':hashlib.sha256(('fixture-response|'+request_id(unit)).encode('ascii')).hexdigest()}

def _line(s,limit=1024):
    b=b''
    while not b.endswith(b'\n'):
        piece=s.recv(256)
        if not piece:return None
        b+=piece
        if len(b)>limit:return None
    try:return json.loads(b.decode('ascii','strict'))
    except (ValueError,UnicodeError):return None

def _send(s,record):
    wire=(json.dumps(record,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
    if len(wire)>MAX_FRAME:return False
    s.sendall(wire);return True

def _deny_family(family):
    try:s=socket.socket(family,socket.SOCK_STREAM)
    except OSError as exc:return {'denied':True,'errno':int(exc.errno or 0)}
    else:s.close();return {'denied':False,'errno':0}

def _deny_private(path):
    try:
        with open(path,'rb') as f:f.read(1)
    except OSError as exc:return {'denied':True,'errno':int(exc.errno or 0)}
    return {'denied':False,'errno':0}

def main(argv):
    if len(argv)!=5:return 71
    peer_sock,control_sock,fake,unit=argv[1:]
    if not re.fullmatch(r'forprint-cf10-batchg-[a-f0-9]{16}\.service',unit):return 72
    folder='/run/'+unit.removesuffix('.service')
    if peer_sock!=folder+'/inference.sock' or control_sock!=folder+'/control.sock' or fake!=folder+'/fake_credential.txt':return 73
    try:
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as bridge:
            bridge.settimeout(14)
            bridge.connect(peer_sock)
            if not _send(bridge,request(unit,'external.unapproved')):return 74
            denial=_line(bridge)
            if denial!={'schema':RESPONSE_SCHEMA,'status':'DENIED_ROUTE','request_id':request_id(unit)}:return 75
            if not _send(bridge,request(unit)):return 76
            ok=_line(bridge)
            if ok!=reply(unit):return 77
        observations={'schema':'cf10_batch_g_client_observations_v0_1',
                      'uid':os.getuid(),'gid':os.getgid(),
                      'ipv4':_deny_family(socket.AF_INET),
                      'ipv6':_deny_family(socket.AF_INET6),
                      'fake_credential':_deny_private(fake),
                      'invalid_route_denied':True,
                      'fixture_response_validated':True,
                      'fixture_response_sha256':reply(unit)['response_sha256']}
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as ctrl:
            ctrl.settimeout(14);ctrl.connect(control_sock)
            if not _send(ctrl,observations):return 78
            if ctrl.recv(8)!=b'RECEIVED':return 79
        while True:time.sleep(1)
    except (OSError,ValueError,TypeError,ValueError):return 80
if __name__=='__main__':raise SystemExit(main(sys.argv))
