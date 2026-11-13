from pathlib import Path
import sys
import tempfile
import unittest
PAYLOAD=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PAYLOAD))
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as supervisor
from scripts.coordination.control_plane import cf10_trusted_baseline_binding_v0_1 as binding
from scripts.coordination.control_plane.workspace import cf10_untrusted_worktree_delta_v0_1 as delta

HEAD='16a296463333416e9e6b26a41bf193e0970ae38d'
A='cf10-u180j-a050'
R='/srv/software_development/forprint-worker-runtime'
W=R+'/forprint_system_blueprint/worker-01/'+A+'/workspace/repo'
HANDOFF='e'*64
TASK='cf10-project-change-impact-and-freshness-control-v0-1'

class CrossBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='r013-combined-')
        self.repo=Path(self.temp.name)
        (self.repo/'.git').mkdir()
        (self.repo/'a.txt').write_text('before')
    def tearDown(self):self.temp.cleanup()
    def issue(self, snapshot, attempt=A):
        b=binding.assemble_binding(attempt_id=attempt,task_prompt_id=TASK,
            source_head=HEAD,handoff_sha256=HANDOFF,baseline_sha256=snapshot['content_sha256'])
        s=supervisor.BoundedInput(TASK,attempt,HEAD,HANDOFF,snapshot['content_sha256'],
           W.replace(A,attempt),R,('/usr/bin/python3','-V'),60)
        return b,s,supervisor.bind_plan(s)
    def test_01_baseline_and_handoff_binding(self):
        before=delta.snapshot_tree(self.repo);b,s,p=self.issue(before)
        self.assertTrue(binding.match_binding(b,attempt_id=A,task_prompt_id=TASK,
          source_head=HEAD,handoff_sha256=HANDOFF,baseline_sha256=before['content_sha256']))
        self.assertTrue(supervisor.validate_plan(p,s))
    def test_02_independent_delta_never_authorized(self):
        before=delta.snapshot_tree(self.repo); b,s,p=self.issue(before)
        (self.repo/'a.txt').write_text('after')
        diff=delta.compare_snapshots(before,delta.snapshot_tree(self.repo),process_quiescence_proven=True)
        self.assertEqual(diff['changed_paths'],['a.txt'])
        self.assertFalse(diff['promotion_allowed'])
        self.assertFalse(p['flags']['authorizing'])
    def test_03_snapshot_digest_replay_blocked(self):
        before=delta.snapshot_tree(self.repo);b,s,p=self.issue(before)
        (self.repo/'a.txt').write_text('after')
        new=delta.snapshot_tree(self.repo)
        with self.assertRaises(binding.BindingBlocked):binding.match_binding(b,attempt_id=A,
            task_prompt_id=TASK,source_head=HEAD,handoff_sha256=HANDOFF,baseline_sha256=new['content_sha256'])
    def test_04_different_attempt_not_reusable(self):
        before=delta.snapshot_tree(self.repo);b,s,p=self.issue(before)
        new_s=supervisor.BoundedInput(TASK,'cf10-u180j-a051',HEAD,HANDOFF,before['content_sha256'],W.replace(A,'cf10-u180j-a051'),R,('/usr/bin/python3','-V'),60)
        with self.assertRaises(supervisor.BoundaryBlocked):supervisor.validate_plan(p,new_s)
    def test_05_git_metadata_not_trusted(self):
        before=delta.snapshot_tree(self.repo)
        (self.repo/'.git').rename(self.repo/'.git-old')
        with self.assertRaises(delta.UntrustedTreeBlocked):delta.snapshot_tree(self.repo)
    def test_06_observed_quiescence_is_not_production_receipt(self):
        before=delta.snapshot_tree(self.repo);b,s,p=self.issue(before)
        unit=p['identity']['unit'];group='/system.slice/'+unit
        present={'Id':unit,'User':'forprint-runner','Group':'forprint-runner',
          'KillMode':'control-group','Delegate':'no','NoNewPrivileges':'yes',
          'ProtectControlGroups':'yes','ControlGroup':group,'MainPID':'31234','ActiveState':'active'}
        final={'Id':unit,'MainPID':'0','ActiveState':'inactive'}
        sample=({'uid':996,'gid':992,'cgroup':group,'alive_after_stop':False},)
        observed=supervisor.assess_observation(plan=p,spec=s,before=present,after=final,
                           sampled_pids=sample,cgroup_populated='0',stop_rc=0)
        self.assertTrue(observed['status'].startswith('PASS'))
        self.assertFalse(observed['production_quiescence_proven'])
        with self.assertRaises(delta.UntrustedTreeBlocked):
            delta.compare_snapshots(before,before,process_quiescence_proven=observed['production_quiescence_proven'])

if __name__=='__main__':unittest.main()
