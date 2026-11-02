import sys
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as m

HEAD='16a296463333416e9e6b26a41bf193e0970ae38d'
SHA='e'*64
A='cf10-u180j-a050'
R='/srv/software_development/forprint-worker-runtime'
W=R+'/forprint_system_blueprint/worker-01/'+A+'/workspace/repo'

def spec():
    return m.BoundedInput('cf10-project-change-impact-and-freshness-control-v0-1',A,HEAD,
                          SHA,SHA,W,R,('/usr/local/bin/codex','exec','--sandbox','workspace-write'),600)


def observations(plan):
    unit=plan['identity']['unit']
    b={'Id':unit,'User':'forprint-runner','Group':'forprint-runner',
       'KillMode':'control-group','Delegate':'no','NoNewPrivileges':'yes',
       'ProtectControlGroups':'yes','ControlGroup':'/system.slice/'+unit,
       'MainPID':'20011','ActiveState':'active'}
    a={'Id':unit,'MainPID':'0','ActiveState':'inactive'}
    ps=({'pid':20011,'uid':996,'gid':992,'cgroup':'/system.slice/'+unit,'alive_after_stop':False},)
    return b,a,ps

class SupervisorCandidateTests(unittest.TestCase):
    def test_01_plan_shape_no_authority(self):
        p=m.bind_plan(spec());self.assertFalse(p['flags']['authorizing']);self.assertFalse(p['flags']['claim_issued'])
    def test_02_deterministic(self):
        self.assertEqual(m.bind_plan(spec()),m.bind_plan(spec()))
    def test_03_head_binding(self):
        self.assertNotEqual(m.bind_plan(spec())['identity']['unit'], m.bind_plan(replace(spec(),source_head='a'*40))['identity']['unit'])
    def test_04_reject_unknown_attempt(self):
        with self.assertRaises(m.BoundaryBlocked):m.bind_plan(replace(spec(),attempt_id='a049'))
    def test_05_reject_path_traversal(self):
        with self.assertRaises(m.BoundaryBlocked):m.bind_plan(replace(spec(),workspace=W+'/../input'))
    def test_06_reject_wrong_workspace(self):
        with self.assertRaises(m.BoundaryBlocked):m.bind_plan(replace(spec(),workspace=W.replace('a050','a049')))
    def test_07_reject_unbounded_runtime(self):
        with self.assertRaises(m.BoundaryBlocked):m.bind_plan(replace(spec(),runtime_root='relative'))
    def test_08_reject_bad_handoff(self):
        with self.assertRaises(m.BoundaryBlocked):m.bind_plan(replace(spec(),handoff_sha256='-'))
    def test_09_reject_executable_relative(self):
        with self.assertRaises(m.BoundaryBlocked):m.bind_plan(replace(spec(),argv=('codex','exec')))
    def test_10_reject_executable_outside_allowlist(self):
        with self.assertRaises(m.BoundaryBlocked):m.bind_plan(replace(spec(),argv=('/tmp/launcher','exec')))
    def test_11_reject_embedded_newline(self):
        with self.assertRaises(m.BoundaryBlocked):m.bind_plan(replace(spec(),argv=('/usr/bin/python3','abc\ndef')))
    def test_12_reject_timeout_bool(self):
        with self.assertRaises(m.BoundaryBlocked):m.bind_plan(replace(spec(),timeout_seconds=True))
    def test_13_reject_timeout_oversize(self):
        with self.assertRaises(m.BoundaryBlocked):m.bind_plan(replace(spec(),timeout_seconds=100000))
    def test_14_plan_tamper(self):
        p=m.bind_plan(spec());p['flags']['authorizing']=True
        with self.assertRaises(m.BoundaryBlocked):m.validate_plan(p,spec())
    def test_15_unit_tamper(self):
        p=m.bind_plan(spec());p['identity']['unit']='x.service'
        with self.assertRaises(m.BoundaryBlocked):m.validate_plan(p,spec())
    def test_16_plan_replay_other_attempt(self):
        with self.assertRaises(m.BoundaryBlocked):m.validate_plan(m.bind_plan(spec()),replace(spec(),attempt_id='cf10-u180j-a051',workspace=W.replace('a050','a051')))
    def test_17_systemd_argv_no_shell(self):
        p=m.bind_plan(spec());cmd=m.candidate_systemd_argv(p,spec())
        self.assertEqual(cmd[0],'/usr/bin/systemd-run');self.assertEqual(cmd[-4:],list(spec().argv));self.assertIn('--property=KillMode=control-group',cmd)
    def test_18_runner_has_no_root_identity(self):
        self.assertEqual(m.UID,996);self.assertEqual(m.GID,992)
    def test_19_precondition_required(self):
        p=m.bind_plan(spec());b,a,ps=observations(p)
        r=m.assess_observation(plan=p,spec=spec(),before=b,after=a,sampled_pids=ps,cgroup_populated='0',stop_rc=0)
        self.assertEqual(r['status'],'PASS_OBSERVATION_CANDIDATE_ONLY');self.assertFalse(r['promotion_allowed'])
    def test_20_unbound_unit(self):
        p=m.bind_plan(spec());b,a,ps=observations(p);b['Id']='else.service'
        r=m.assess_observation(plan=p,spec=spec(),before=b,after=a,sampled_pids=ps,cgroup_populated='0',stop_rc=0)
        self.assertTrue(r['status'].startswith('BLOCKED'))
    def test_21_wrong_uid(self):
        p=m.bind_plan(spec());b,a,ps=observations(p);ps=({**ps[0],'uid':0},)
        r=m.assess_observation(plan=p,spec=spec(),before=b,after=a,sampled_pids=ps,cgroup_populated='0',stop_rc=0)
        self.assertTrue(r['status'].startswith('BLOCKED'))
    def test_22_child_survives(self):
        p=m.bind_plan(spec());b,a,ps=observations(p);ps=({**ps[0],'alive_after_stop':True},)
        r=m.assess_observation(plan=p,spec=spec(),before=b,after=a,sampled_pids=ps,cgroup_populated='0',stop_rc=0)
        self.assertFalse(r['checks']['sampled_processes_gone'])
    def test_23_populated(self):
        p=m.bind_plan(spec());b,a,ps=observations(p)
        r=m.assess_observation(plan=p,spec=spec(),before=b,after=a,sampled_pids=ps,cgroup_populated='1',stop_rc=0)
        self.assertTrue(r['status'].startswith('BLOCKED'))
    def test_24_still_active(self):
        p=m.bind_plan(spec());b,a,ps=observations(p);a['ActiveState']='active'
        r=m.assess_observation(plan=p,spec=spec(),before=b,after=a,sampled_pids=ps,cgroup_populated='0',stop_rc=0)
        self.assertTrue(r['status'].startswith('BLOCKED'))
    def test_25_stop_failed(self):
        p=m.bind_plan(spec());b,a,ps=observations(p)
        r=m.assess_observation(plan=p,spec=spec(),before=b,after=a,sampled_pids=ps,cgroup_populated='0',stop_rc=1)
        self.assertTrue(r['status'].startswith('BLOCKED'))
    def test_26_empty_sample_not_proof(self):
        p=m.bind_plan(spec());b,a,ps=observations(p)
        r=m.assess_observation(plan=p,spec=spec(),before=b,after=a,sampled_pids=(),cgroup_populated='0',stop_rc=0)
        self.assertTrue(r['status'].startswith('BLOCKED'))
    def test_27_never_authorizing(self):
        p=m.bind_plan(spec());b,a,ps=observations(p)
        r=m.assess_observation(plan=p,spec=spec(),before=b,after=a,sampled_pids=ps,cgroup_populated='0',stop_rc=0)
        self.assertFalse(r['authorization_granted']);self.assertFalse(r['production_quiescence_proven']);self.assertFalse(r['worker_result_accepted'])
    def test_28_show_malformed(self):
        with self.assertRaises(m.BoundaryBlocked):m.parse_systemd_show('ActiveState=active\nActiveState=inactive')
    def test_29_show_good(self):
        self.assertEqual(m.parse_systemd_show('ActiveState=inactive\nMainPID=0')['MainPID'],'0')
    def test_30_no_subprocess_code(self):
        import inspect
        s=inspect.getsource(m)
        self.assertNotIn('subprocess.',s);self.assertNotIn('os.system(',s)

if __name__=='__main__':unittest.main()
