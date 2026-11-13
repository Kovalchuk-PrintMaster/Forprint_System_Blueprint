import hashlib
import json
import subprocess
from pathlib import Path
import pytest
from scripts.coordination import work_front_closeout_publication_v0_1 as pub

def cmd(root,*args):
    p=subprocess.run(['git','-C',str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    return p.stdout.decode().strip()

@pytest.fixture
def remote_checkout(tmp_path):
    remote=tmp_path/'remote.git'; work=tmp_path/'work'; remote.mkdir();work.mkdir()
    cmd(remote,'init','--bare','-q')
    cmd(work,'init','-q');cmd(work,'config','user.email','test@example.org');cmd(work,'config','user.name','Test')
    (work/'a.py').write_text('data=1\n');cmd(work,'add','a.py');cmd(work,'commit','-qm','one')
    commit=cmd(work,'rev-parse','HEAD');cmd(work,'remote','add','origin',str(remote));cmd(work,'push','-q','origin','HEAD:refs/heads/main')
    digest=hashlib.sha256((work/'a.py').read_bytes()).hexdigest()
    manifest={'schema_version':'forprint_closeout_publication_manifest_v0_1','commit':commit,'implementation_sha256':{'a.py':digest},'frozen_prepublication_file_sha256':{'a.py':digest}}
    msha=hashlib.sha256((json.dumps(manifest,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()).hexdigest()
    policy={'publication_remote':'origin','publication_ref':'refs/heads/main','publication_remote_url':str(remote)}
    decision={'publication_commit':commit,'publication_remote':'origin','publication_ref':'refs/heads/main','publication_manifest_sha256':msha}
    return work,remote,policy,decision,manifest

def test_real_remote_commit_and_exact_blob(remote_checkout):
    w,r,p,d,m=remote_checkout
    assert pub.verify_publication(w,{},d,p,m)['blob_count']==1

def test_remote_head_mismatch_blocks(remote_checkout):
    w,r,p,d,m=remote_checkout
    (w/'a.py').write_text('data=2\n');cmd(w,'add','a.py');cmd(w,'commit','-qm','two');cmd(w,'push','-q','origin','HEAD:refs/heads/main')
    with pytest.raises(pub.PublicationError,match='REMOTE_REF_COMMIT_DRIFT'):
        pub.verify_publication(w,{},d,p,m)

def test_published_blob_mismatch_blocks(remote_checkout):
    w,r,p,d,m=remote_checkout
    m['implementation_sha256']['a.py']='f'*64;m['frozen_prepublication_file_sha256']['a.py']='f'*64
    d['publication_manifest_sha256']=hashlib.sha256((json.dumps(m,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()).hexdigest()
    with pytest.raises(pub.PublicationError,match='PUBLISHED_BLOB_MISMATCH'):
        pub.verify_publication(w,{},d,p,m)

def test_local_head_without_observed_remote_is_not_publication(remote_checkout):
    w,r,p,d,m=remote_checkout
    d['publication_remote']='elsewhere';p['publication_remote']='elsewhere'
    with pytest.raises(pub.PublicationError,match='GIT_VERIFICATION_FAILED'):
        pub.verify_publication(w,{},d,p,m)

def test_different_branch_policy_blocks(remote_checkout):
    w,r,p,d,m=remote_checkout
    d['publication_ref']='refs/heads/rogue'
    with pytest.raises(pub.PublicationError,match='PUBLICATION_POLICY_MISMATCH'):
        pub.verify_publication(w,{},d,p,m)

def test_path_traversal_rejected(remote_checkout):
    w,r,p,d,m=remote_checkout
    m['implementation_sha256']={'../oops': 'f'*64};m['frozen_prepublication_file_sha256']=dict(m['implementation_sha256'])
    d['publication_manifest_sha256']=hashlib.sha256((json.dumps(m,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()).hexdigest()
    with pytest.raises(pub.PublicationError,match='IMPLEMENTATION_PATH_OR_SHA_INVALID'):
        pub.verify_publication(w,{},d,p,m)
