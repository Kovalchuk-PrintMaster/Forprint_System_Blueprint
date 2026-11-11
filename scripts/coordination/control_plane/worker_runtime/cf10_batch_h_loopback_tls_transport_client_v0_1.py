"""Batch H disposable sandbox client: loopback CONNECT -> UDS -> synthetic TLS.

Stand-alone Python -I; no provider requests, real credentials, or external DNS.
The temporary TLS CA is *public test material* supplied from the guarded lab.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import select
import socket
import ssl
import sys
import threading
import time
import urllib.request

HOST='fixture.forprint.invalid'
ALLOW=HOST+':443'
REJECT='unauthorized.invalid:443'
BODY=b'CF10_BATCH_H_PUBLIC_TLS_CONNECT_FIXTURE_V1\n'
SCHEMA='cf10_batch_h_connect_v0_1'
MAX_HEAD=4096
MAX_TUNNEL=65536

def request_id(unit):
    return hashlib.sha256(('cf10-batch-h|'+unit).encode('ascii')).hexdigest()[:24]

def request(unit,target):
    return {'schema':SCHEMA,'request_id':request_id(unit),'target':target,
            'attempt_mode':'DISPOSABLE_TLS_FIXTURE_ONLY'}

def _readline(sock,cap=1024):
    data=b''
    while not data.endswith(b'\n'):
        part=sock.recv(1)
        if not part or len(data)>=cap:raise ValueError('LINE')
        data+=part
    obj=json.loads(data.decode('ascii','strict'))
    if type(obj) is not dict:raise ValueError('FRAME')
    return obj

def _http_head(sock):
    data=b''
    while not data.endswith(b'\r\n\r\n'):
        chunk=sock.recv(1)
        if not chunk or len(data)>=MAX_HEAD:raise ValueError('HTTP_HEAD')
        data+=chunk
    return data

def _relay(client,broker):
    """Opaque bytes after CONNECT; no TLS termination or credential handling."""
    peers={client:broker,broker:client};active={client,broker};total=0
    while active:
        ready,_,_=select.select(list(active),[],[],9)
        if not ready:raise TimeoutError('TUNNEL_IDLE')
        for s in ready:
            data=s.recv(8192)
            if not data:
                active.remove(s)
                try:peers[s].shutdown(socket.SHUT_WR)
                except OSError:pass
                continue
            total+=len(data)
            if total>MAX_TUNNEL:raise ValueError('TUNNEL_BYTES')
            peers[s].sendall(data)

def _serve_one(listener,unit,broker_path):
    client,_=listener.accept()
    with client:
        client.settimeout(10)
        line=_http_head(client).decode('ascii','strict').split('\r\n')[0]
        parts=line.split(' ')
        if len(parts)!=3 or parts[0]!='CONNECT' or parts[2] not in ('HTTP/1.0','HTTP/1.1'):
            client.sendall(b'HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n');return
        target=parts[1]
        if target not in (ALLOW,REJECT):
            client.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n');return
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as upstream:
            upstream.settimeout(10)
            upstream.connect(broker_path)
            payload=(json.dumps(request(unit,target),sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
            upstream.sendall(payload)
            decision=_readline(upstream)
            want={'status':'DENY_CONNECT' if target==REJECT else 'ALLOW_FIXTURE_TLS',
                  'request_id':request_id(unit)}
            if decision!=want:raise ValueError('ROOT_DECISION')
            if target==REJECT:
                client.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
                return
            client.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            _relay(client,upstream)

def _serve(listener,unit,broker_path,errors):
    try:
        for _ in range(2):_serve_one(listener,unit,broker_path)
    except BaseException as exc:
        errors.append(type(exc).__name__)

def _denied_direct(family,address):
    try:
        with socket.socket(family,socket.SOCK_STREAM) as sock:
            sock.settimeout(1.2)
            sock.connect((address,443))
    except OSError as exc:
        return {'denied':True,'errno':int(exc.errno or 110)}
    return {'denied':False,'errno':0}

def _denied_file(path):
    try:
        with open(path,'rb') as f:f.read(1)
    except OSError as exc:return {'denied':True,'errno':int(exc.errno or 0)}
    return {'denied':False,'errno':0}

def _send_control(path,record):
    data=(json.dumps(record,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
    if len(data)>2048:raise ValueError('OBS_SIZE')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(8);s.connect(path);s.sendall(data)
        if s.recv(8)!=b'RECEIVED':raise ValueError('OBS_ACK')

def main(argv):
    if len(argv)!=6:return 71
    broker,control,cert,fake,unit=argv[1:]
    if not re.fullmatch(r'forprint-cf10-batchh-[0-9a-f]{16}\.service',unit):return 72
    d='/run/'+unit.removesuffix('.service')
    if (broker!=d+'/tunnel.sock' or control!=d+'/control.sock' or
        cert!=d+'/tls_cert.pem' or fake!=d+'/fake_credential.txt'):
        return 73
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            server.bind(('127.0.0.1',0));server.listen(2);server.settimeout(14)
            port=server.getsockname()[1]
            errors=[]
            t=threading.Thread(target=_serve,args=(server,unit,broker,errors),daemon=True)
            t.start()
            with socket.create_connection(('127.0.0.1',port),timeout=8) as s:
                s.settimeout(8)
                s.sendall((f'CONNECT {REJECT} HTTP/1.1\r\nHost: {REJECT}\r\n\r\n').encode('ascii'))
                negative=_http_head(s)
                if not negative.startswith(b'HTTP/1.1 403 Forbidden\r\n'):return 74
            # Actual Python HTTPS-client behavior: HTTPS_PROXY-style HTTP CONNECT,
            # TLS trust+hostname verification and encrypted HTTP over opaque bridge.
            # A manager-level NO_PROXY must not bypass our explicitly pinned proxy.
            os.environ['NO_PROXY']=''
            os.environ['no_proxy']=''
            ctx=ssl.create_default_context(cafile=cert)
            opener=urllib.request.build_opener(
                urllib.request.ProxyHandler({'https':f'http://127.0.0.1:{port}'}),
                urllib.request.HTTPSHandler(context=ctx))
            with opener.open('https://'+HOST+'/ready',timeout=10) as resp:
                body=resp.read(512)
                if resp.status!=200 or body!=BODY:return 75
            t.join(5)
            if t.is_alive() or errors:return 76
            evidence={'schema':'cf10_batch_h_tls_client_observations_v0_1',
                      'uid':os.getuid(),'gid':os.getgid(),
                      'tls_verified':True,'fixture_body_sha256':hashlib.sha256(body).hexdigest(),
                      'unauthorized_connect_denied':True,
                      'proxy_loopback_only':True,
                      'direct_external_ipv4':_denied_direct(socket.AF_INET,'192.0.2.1'),
                      'direct_external_ipv6':_denied_direct(socket.AF_INET6,'2001:db8::1'),
                      'fake_credential':_denied_file(fake)}
            _send_control(control,evidence)
            while True:time.sleep(1)
    except (OSError,ValueError,UnicodeError,TimeoutError,ssl.SSLError):return 80
if __name__=='__main__':raise SystemExit(main(sys.argv))
