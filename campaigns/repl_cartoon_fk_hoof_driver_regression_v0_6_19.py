#!/usr/bin/env python3
"""Host/mock tests for a complete checkout→policy→blocked / success execution.

All repository and model bytes here are synthetic. These tests only validate
Python entrypoint control flow, immutable destination policy, and publishing.
"""
from pathlib import Path
from unittest import mock
from types import SimpleNamespace
from contextlib import redirect_stdout
import io,hashlib,importlib.util,json,sys,tempfile

ROOT=Path(__file__).resolve().parent
PACKET=ROOT

def mod(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def case(fail_model):
  driver=mod(PACKET/'driver.py','repl0619_driver_mock_'+('failure' if fail_model else 'success'))
  with tempfile.TemporaryDirectory(prefix='repl0619-driver-regression-') as tmp:
    home=Path(tmp)/'home';download=home/'storage'/'downloads';download.mkdir(parents=True)
    repo=Path(tmp)/'repo';(repo/'assets'/'repl').mkdir(parents=True);(repo/'campaigns').mkdir()
    source=b'FAKE_CANONICAL_V0617_GLB_FOR_DRIVER_CONTROL_FLOW_ONLY'
    original_agents=b'# synthetic AGENTS.md fixture\n'
    canon=repo/'assets/repl/Repl.glb';canon.write_bytes(source)
    (repo/'AGENTS.md').write_bytes(original_agents)
    (repo/'README.md').write_text('# fake repository\n')
    (repo/'assets/repl/CANONICAL_MODEL.json').write_text(json.dumps({'active_model':{'sha256':hashlib.sha256(source).hexdigest(),'version':'0.6.17'}}))
    # Source/Git internals are mocked so this does not claim real Git/GLB execution.
    state={'head':'fixture_source_pin','remote':'fixture_source_pin','commit_no':0,'staged':[],'prev_head':None}
    remote='https://github.com/Valar05/parametric-parambulator.git'
    def p(*args,**kw):return SimpleNamespace(stdout='',stderr='',returncode=0)
    def gout(dir,*args):
      if args==('remote','get-url','origin'):return remote
      if args==('rev-parse','HEAD'):return state['head']
      if args==('rev-parse','refs/remotes/origin/main'):return state['remote']
      if args==('rev-parse','--abbrev-ref','HEAD'):return 'main'
      if args==('rev-parse','HEAD^'):return state['prev_head']
      if args==('rev-parse','HEAD:'+driver.CANON):return driver.SRC_BLOB if state['commit_no']<2 else gitblob(canon.read_bytes())
      if args==('ls-remote','origin','refs/heads/main'):return state['remote']+'\trefs/heads/main'
      raise AssertionError('UNHANDLED_FAKE_GIT_QUERY '+repr(args))
    def git(dir,*args):
      if args[:1]==('status',):return p()
      if args[:1]==('add',):state['staged']=list(args[2:]);return p()
      if args[:2]==('diff','--cached'):return SimpleNamespace(stdout='\n'.join(state['staged'])+'\n')
      if 'commit' in args:
        state['prev_head']=state['head'];state['commit_no']+=1
        state['head']='fixture_source_published' if state['commit_no']==1 else 'fixture_model_published'
        return p()
      raise AssertionError('UNHANDLED_FAKE_GIT_MUTATION '+repr(args))
    def push(dir,expect):
      assert expect==state['remote'] if state['commit_no']==1 else expect==state['prev_head']
      state['remote']=state['head']
    def gitblob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    def publish(path,data):
      path=Path(path)
      assert path.parent.is_dir()
      if path.exists():assert path.read_bytes()==data
      else:path.write_bytes(data)
    Core=SimpleNamespace(REMOTE=remote,checkout=lambda work:repo,gout=gout,git=git,
      push=push,one_model=lambda repo:None,publish=publish,gitblob=gitblob,
      make_viewer=lambda *args:b'<html>fixture v0.6.17</html>')
    class Model:
      def evaluate(self,*args):
        if fail_model:raise RuntimeError('PHYSICAL_GAIT_INFEASIBLE_SYNTHETIC')
        return b'REVISED_GLB_SYNTHETIC_SUCCESS_CASE', {'kinematic_details':{},'candidate_profile':'fixture-pass'}, []
    stub=SimpleNamespace()
    original_load=driver.load
    def loaded(path,name):
      if str(path).endswith('git_core.py'):return Core
      if str(path).endswith('model.py'):return Model()
      return stub
    driver.SRC_SHA=hashlib.sha256(source).hexdigest()
    driver.SRC_BLOB=gitblob(source)
    driver.AGENTS_OLD_SHA=hashlib.sha256(original_agents).hexdigest()
    driver.PARENT=state['head']
    oldsys=list(sys.argv)
    capture=io.StringIO()
    try:
      with mock.patch.object(driver,'load',side_effect=loaded), mock.patch.object(driver.Path,'home',return_value=home),redirect_stdout(capture):
        sys.argv=['driver.py','--packet',str(PACKET)]
        ret=driver.main()
    finally:sys.argv=oldsys
    output=capture.getvalue()
    assert (repo/'AGENTS.md').read_bytes()==original_agents.rstrip(b'\n')+b'\n\n'+(ROOT.parent/'AGENTS_ADDENDUM.md').read_bytes()
    assert (repo/'campaigns/repl_cartoon_fk_hoof_driver_v0_6_19.py').is_file()
    assert state['remote']==state['head']
    assert all(x in output for x in ['RESOLVED_REPO=','CANONICAL_SOURCE_SHA=','AGENTS_APPEND_VERIFIED=PASS'])
    if fail_model:
      assert ret==2 and canon.read_bytes()==source
      assert state['commit_no']==1 and state['head']=='fixture_source_published'
      assert 'CAMPAIGN_STATUS=BLOCKED_TWO_JOINT_PHYSICAL_FEASIBILITY' in output
      assert (download/'REPL_CARTOON_FK_HOOF_WALK_v0.6.19_BLOCKED.json').is_file()
    else:
      assert ret==0 and state['commit_no']==2 and canon.read_bytes()!=source
      assert (download/'REPL_CARTOON_FK_HOOF_WALK_v0.6.19_report.json').is_file()
      assert (download/'REPL_CARTOON_FK_HOOF_WALK_v0.6.19_TEXTURED_POSE_LAB.html').is_file()
      assert 'HUMAN_VISUAL_ACCEPTANCE=PENDING' in output
    return output

if __name__=='__main__':
 for fail in (True,False):
  result=case(fail)
  print(('MOCK_BLOCKED_MODEL_PATH=PASS' if fail else 'MOCK_SUCCESS_MODEL_PUBLICATION_PATH=PASS'))
 print('NOTE=MOCK_DRIVER_TESTS_DO_NOT_VERIFY_PRODUCTION_GLB')
