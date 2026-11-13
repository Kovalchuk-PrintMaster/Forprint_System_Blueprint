#!/usr/bin/env python3
"""One bounded root-only Copilot endpoint + credential metadata survey.

This tests *unauthenticated* public GitHub _ping, not Worker egress or auth.
No token access, no user request, no direct Worker network, no claims, no
systemd unit, no provider inference, no network policy mutation or fallback URL.
"""
from __future__ import annotations
import argparse
import http.client
import json
import os
from pathlib import Path
import re
import socket
import ssl
import stat
import subprocess
from scripts.coordination.control_plane.worker_runtime import cf10_ai_pre_admission_contract_v0_1 as contract

SCHEMA='cf10_ai_root_copilot_survey_v0_1'
ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
CLI=Path('/usr/local/bin/forprint-copilot-1.0.107')
HANDLE=Path('/var/lib/forprint-cf10/credentials/copilot.pat')
TIMEOUT=7
LIMIT=1024

class SurveyHold(ValueError):pass

def deny(msg):raise SurveyHold('CF10_AI_SURVEY_HOLD_'+msg)

def https_ping(host:str,*,factory=http.client.HTTPSConnection)->dict:
    if type(host) is not str or host not in contract.ENDPOINTS:deny('NONALLOWLISTED_HOST')
    row={'host':host,'path':'/_ping','state':'HOLD_NETWORK','http_status':None,
         'tls_certificate_verified':False,'response_bytes':0}
    connection=None
    try:
        ctx=ssl.create_default_context()
        if ctx.verify_mode!=ssl.CERT_REQUIRED or not ctx.check_hostname:deny('TLS_CERT_MODE')
        connection=factory(host,port=443,timeout=TIMEOUT,context=ctx)
        connection.request('GET','/_ping',body=None,headers={
            'User-Agent':'ForPrint-CF10-Root-Readiness/1.0',
            'Accept':'text/plain','Connection':'close'})
        response=connection.getresponse()
        row['http_status']=response.status
        body=response.read(LIMIT+1)
        row['response_bytes']=min(len(body),LIMIT)
        if len(body)>LIMIT:row['state']='HOLD_RESPONSE_SIZE'
        elif type(response.status) is int and response.status==200:
            row.update(state='PASS_TLS_200',tls_certificate_verified=True)
        else:row['state']='HOLD_HTTP_STATUS'
    except (ssl.SSLError,ssl.CertificateError):row['state']='HOLD_TLS_OR_CERT'
    except (OSError,TimeoutError,ValueError,http.client.HTTPException):row['state']='HOLD_NETWORK'
    finally:
        if connection is not None:
            try:connection.close()
            except OSError:pass
    return row

def offline_cli_help(*, runner=subprocess.run, inspector=None):
    from scripts.coordination.control_plane.worker_runtime import cf10_r115_preclaim_executable_profile_v0_1 as r115
    result={'pinned_sha256':contract.BINARY_SHA,'binary_verified_by_r115':False,
            'help_exit_code':None,'help_flag_matches':{f:False for f in contract.CLI_FLAGS},
            'offline_no_auto_update':True,'credential_env_passed':False,
            'provider_inference':False}
    if CLI!=r115.COPILOT_PILOT_PATH or r115.COPILOT_PILOT_SHA256!=contract.BINARY_SHA:
        return result
    try:(inspector or r115.assert_pinned_binary)()
    except Exception:return result
    result['binary_verified_by_r115']=True
    env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent','XDG_CONFIG_HOME':'/nonexistent',
         'LANG':'C','LC_ALL':'C','GIT_TERMINAL_PROMPT':'0','NO_COLOR':'1',
         'COPILOT_AUTO_UPDATE':'false','COPILOT_OFFLINE':'true','DO_NOT_TRACK':'1'}
    try:
        cp=runner([str(CLI),'--help'],cwd='/',env=env,stdin=subprocess.DEVNULL,
                  stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=12,check=False)
    except (OSError,subprocess.TimeoutExpired,ValueError):return result
    if type(cp.returncode) is not int or len(cp.stdout)>100_000 or len(cp.stderr)>100_000:
        return result
    result['help_exit_code']=cp.returncode
    if cp.returncode!=0:return result
    text=cp.stdout.decode('utf-8','replace')+'\n'+cp.stderr.decode('utf-8','replace')
    # Flag listing alone is feature discovery, not a grant to invoke a model.
    result['help_flag_matches']={flag:(flag in text) for flag in contract.CLI_FLAGS}
    return result

def credential_metadata(*, path:Path|None=None, inspector=None):
    if path is None:path=HANDLE
    if path!=HANDLE:deny('CREDENTIAL_PATH_SCOPE')
    from scripts.coordination.control_plane.worker_runtime import cf10_first_worker_secure_metadata_v0_1 as meta
    empty=meta.empty_record()
    if not path.exists() and not path.is_symlink():
        return dict(empty,metadata_status='UNCONFIGURED')
    # The metadata inspector opens parent directories only, NEVER reads tokens.
    try:row=(inspector or meta.inspect_credential_metadata)(path,project_root=ROOT)
    except (OSError,ValueError,RuntimeError,TypeError,AttributeError):
        return dict(empty,metadata_status='HOLD_PATH_OR_OWNERSHIP')
    if (not isinstance(row,dict) or row.get('root_owns_material') is not True or
            row.get('source')!='ROOT_EXTERNAL_HANDLE_REVIEW_ONLY' or
            any(row.get(k) is not False for k in ('group_or_world_access','material_read',
                'passed_to_cli_env','passed_to_child_tools','credential_exchange_attested'))):
        return dict(empty,metadata_status='HOLD_PATH_OR_OWNERSHIP')
    # Explicit allowlist prevents path, size or token-shaped fields reaching evidence.
    names=set(empty)
    return dict({k:row[k] for k in names},metadata_status='ROOT_METADATA_ONLY')

def get_head(*,runner=subprocess.run):
    cp=runner(['/usr/bin/git','-C',str(ROOT),'rev-parse','HEAD'],
              cwd=str(ROOT),env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','GIT_TERMINAL_PROMPT':'0'},
              stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=12,check=False)
    if cp.returncode!=0:deny('HEAD_READ')
    text=cp.stdout.decode('ascii','strict').strip()
    if not re.fullmatch(r'[0-9a-f]{40}',text):deny('HEAD_FORMAT')
    return text

def run_survey(*,probe=https_ping,help_probe=offline_cli_help,metadata=credential_metadata,source_head=None):
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    if ROOT.is_symlink() or not ROOT.is_dir():deny('PROJECT_ROOT')
    if launcher.LIVE_CUTOVER_ENABLED is not False:deny('PRODUCTION_SWITCH_OPEN')
    data={host:probe(host) for host in contract.ENDPOINTS}
    policy=dict.fromkeys(('live_cutover_enabled','canonical_claim_consumed','production_ledger_written',
                          'independent_owner_ack','production_dispatcher_authorized'),False)
    result=contract.plan(source_head=source_head or get_head(),network=data,cli=help_probe(),
                         credential=metadata(),canonical=policy)
    return result

def source_check():
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    if launcher.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_CUTOVER')
    return contract.source_check()

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('source-check','root-survey'),required=True)
    args=p.parse_args(argv)
    try:row=source_check() if args.mode=='source-check' else run_survey()
    except BaseException as exc:
        row={'schema':contract.SCHEMA,'status':'CF10_AI_SURVEY_HOLD_'+type(exc).__name__,
             'gates_open':list(contract.GATES), 'provider_inference_executed':False,
             'production_claim_consumed':False,'worker_launched':False,'automatic_retry':False}
    print(json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=True))
    return 0 if row['status']=='PASS_COMPLETED_OBSERVATIONAL_PRE_ADMISSION_ONLY' else 3
if __name__=='__main__':raise SystemExit(main())
