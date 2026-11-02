"""Bounded immutable root-only receipt primitives for CF-10 (candidate).

Never authorizes Worker, ACK, result acceptance, commit or release. Parent store
must be independently configured by trusted root-side operator governance.
The consumed-claim state cannot be cleared by this module; interrupted writes
fail closed and need a separate human-reviewed reconciliation.
"""
from __future__ import annotations
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat

class ReceiptBlocked(RuntimeError): pass
ATTEMPT=re.compile(r"cf10-[a-zA-Z0-9_-]{3,80}-a[0-9]{3,5}\Z")
HEAD=re.compile(r"[a-f0-9]{40}\Z")
HASH=re.compile(r"[a-f0-9]{64}\Z")
EVENTS=('CLAIM_CONSUMED','LAUNCH_REQUESTED','SERVICE_OBSERVED','STOP_REQUESTED',
        'QUIESCENCE_UNPROVEN','QUIESCENCE_OBSERVED_CANDIDATE','REVIEW_REQUIRED')

def _deny(reason): raise ReceiptBlocked('CF10_R015_RECEIPT_'+reason)
def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def _check_private_root_dir(p: Path):
    if not p.is_absolute() or p.is_symlink(): _deny('PATH')
    st=p.lstat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=0o700:
        _deny('PARENT_NOT_PRIVATE_ROOT')

def _new_json(directory: Path, filename: str, row: dict):
    if not re.fullmatch(r'[a-zA-Z0-9._-]{1,128}',filename):_deny('NAME')
    flags=os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_CLOEXEC|os.O_NOFOLLOW
    data=(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode()
    fd=os.open(str(directory/filename),flags,0o600)
    try:
        os.write(fd,data)
        os.fsync(fd)
    finally: os.close(fd)
    dir_fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:os.fsync(dir_fd)
    finally:os.close(dir_fd)

def _read_json(p: Path)->dict:
    if p.is_symlink():_deny('SYMLINK')
    st=p.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=0o600 or st.st_size>65536:
        _deny('FILE_UNSAFE')
    obj=json.loads(p.read_text('utf8'))
    if not isinstance(obj,dict): _deny('CONTENT')
    body=dict(obj);digest=body.pop('receipt_sha256',None)
    if digest!=_digest(body): _deny('TAMPER')
    return obj

def _seal(body:dict)->dict:
    value=dict(body);value['receipt_sha256']=_digest(body);return value

def claim(*, private_store:Path, attempt_id:str, head:str, handoff_sha256:str)->dict:
    """Consume attempt before spawn; O_EXCL mkdir means no automatic retry."""
    if os.geteuid()!=0:_deny('ROOT_REQUIRED')
    if not isinstance(attempt_id,str) or not ATTEMPT.fullmatch(attempt_id):_deny('ATTEMPT')
    if not isinstance(head,str) or not HEAD.fullmatch(head):_deny('HEAD')
    if not isinstance(handoff_sha256,str) or not HASH.fullmatch(handoff_sha256):_deny('HANDOFF')
    store=Path(private_store)
    _check_private_root_dir(store)
    attempt=store/attempt_id
    try:os.mkdir(attempt,0o700)
    except FileExistsError:_deny('ALREADY_CONSUMED_NO_RETRY')
    _check_private_root_dir(attempt)
    obj=_seal({'schema_version':'cf10_root_lifecycle_receipt_v0_1',
               'attempt_id':attempt_id,'source_head':head,
               'handoff_sha256':handoff_sha256,'state':'CLAIM_CONSUMED',
               'worker_launched':False,'automatic_retry':False})
    # Crash between mkdir and write leaves an irreversible occupied directory.
    _new_json(attempt,'0000_claim.json',obj)
    return obj

def observe(*, private_store:Path, attempt_id:str, expected_head:str)->dict:
    if os.geteuid()!=0:_deny('ROOT_REQUIRED')
    if not isinstance(attempt_id,str) or not ATTEMPT.fullmatch(attempt_id):_deny('ATTEMPT')
    store=Path(private_store);_check_private_root_dir(store)
    attempt=store/attempt_id;_check_private_root_dir(attempt)
    claim_data=_read_json(attempt/'0000_claim.json')
    if claim_data['attempt_id']!=attempt_id or claim_data['source_head']!=expected_head:
        _deny('BINDING')
    rows=[claim_data]
    event_paths=sorted(attempt.glob('event_*.json'))
    for i,path in enumerate(event_paths,1):
        if path.name!=f'event_{i:04d}.json':_deny('EVENT_GAP')
        row=_read_json(path)
        if row.get('attempt_id')!=attempt_id or row.get('source_head')!=expected_head:
            _deny('EVENT_BINDING')
        if row.get('sequence')!=i or row.get('previous_sha256')!=rows[-1]['receipt_sha256']:
            _deny('EVENT_CHAIN')
        if row.get('event') not in EVENTS:_deny('EVENT_TYPE')
        rows.append(row)
    return {'attempt_id':attempt_id,'source_head':expected_head,
            'claim_consumed':True,'event_count':len(rows)-1,
            'last_digest':rows[-1]['receipt_sha256'],
            'worker_result_accepted':False,'automatic_retry':False,
            'root_receipt_chain_verified':True}

def append_observation(*,private_store:Path,attempt_id:str,expected_head:str,event:str)->dict:
    """Record single non-authorizing event, with kernel flock and fsync."""
    if event not in EVENTS or event=='CLAIM_CONSUMED':_deny('EVENT_TYPE')
    store=Path(private_store);_check_private_root_dir(store)
    attempt=store/attempt_id;_check_private_root_dir(attempt)
    lock_path=attempt/'observation.lock'
    # Lock file itself is not an authority token; no pre-existing unsafe inode.
    fd=os.open(lock_path,os.O_CREAT|os.O_RDWR|os.O_CLOEXEC|os.O_NOFOLLOW,0o600)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=0o600:_deny('LOCK_UNSAFE')
        fcntl.flock(fd,fcntl.LOCK_EX)
        state=observe(private_store=store,attempt_id=attempt_id,expected_head=expected_head)
        n=state['event_count']+1
        if n>9999:_deny('LIMIT')
        body={'schema_version':'cf10_root_lifecycle_event_v0_1','attempt_id':attempt_id,
              'source_head':expected_head,'sequence':n,'event':event,
              'previous_sha256':state['last_digest'],
              'worker_result_accepted':False,'automatic_retry':False}
        row=_seal(body)
        _new_json(attempt,f'event_{n:04d}.json',row)
        return row
    finally:
        fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)
