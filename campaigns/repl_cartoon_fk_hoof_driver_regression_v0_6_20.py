#!/usr/bin/env python3
"""Real driver control-flow fixtures; Git and mesh bytes are synthetic.

Exercise single-invocation source+AGENTS publish, model rejection, candidate
success, exact commit scopes and remote readback without network side effects.
"""
from pathlib import Path
from unittest import mock
from types import SimpleNamespace
from contextlib import redirect_stdout
import hashlib,io,json,os,sys,tempfile,importlib.util
HERE=Path(__file__).resolve().parent
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def case(fail_model):
 drv=load(HERE/'driver.py','repl20_mock_driver_'+str(fail_model))
 with tempfile.TemporaryDirectory(prefix='repl20-regress-') as td:
  root=Path(td);home=root/'home';down=home/'storage'/'downloads';down.mkdir(parents=True)
  repo=root/'repo';(repo/'assets/repl').mkdir(parents=True);(repo/'campaigns').mkdir()
  source=b'SYNTHETIC_V0617_REPL_ONLY_FOR_DRIVER_CONTROL_TEST'
  current=b'# Mandatory repository boot gate\n# Repl stance and breakover\n# Python shadow import regression\n'
  (repo/'AGENTS.md').write_bytes(current)
  model=repo/'assets/repl/Repl.glb';model.write_bytes(source)
  (repo/'README.md').write_text('# repo\n')
  (repo/'assets/repl/CANONICAL_MODEL.json').write_text(json.dumps({
   'active_model':{'version':'0.6.17','sha256':hashlib.sha256(source).hexdigest()}}))
  state={'head':'fixture_parent','remote':'fixture_parent','commits':0,'staged':[]}
  expected_remote='https://github.com/Valar05/parametric-parambulator.git'
  def gitblob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
  def gout(path,*args):
   if args==('remote','get-url','origin'):return expected_remote
   if args==('rev-parse','HEAD'):return state['head']
   if args==('rev-parse','refs/remotes/origin/main'):return state['remote']
   if args==('rev-parse','HEAD:'+drv.CANON):return gitblob(model.read_bytes())
   if args==('rev-parse','refs/remotes/origin/main:'+drv.CANON):return gitblob(model.read_bytes())
   if args==('ls-remote','origin','refs/heads/main'):return state['remote']+'\trefs/heads/main'
   raise AssertionError('UNEXPECTED_MOCK_GIT_READ:'+repr(args))
  def git(path,*args):
   if args[:1]==('status',):return SimpleNamespace(stdout='',returncode=0)
   if args[:1]==('fetch',):return SimpleNamespace(stdout='',returncode=0)
   if args[:1]==('add',):state['staged']=list(args[2:]);return SimpleNamespace(stdout='',returncode=0)
   if args[:2]==('diff','--cached'):
    return SimpleNamespace(stdout='\n'.join(state['staged'])+'\n',returncode=0)
   if 'commit' in args:
    state['commits']+=1
    state['head']='fixture_commit_'+str(state['commits'])
    return SimpleNamespace(stdout='',returncode=0)
   raise AssertionError('UNEXPECTED_MOCK_GIT_WRITE:'+repr(args))
  def push(path,parent):
   assert state['remote']==parent,'PUSH_PARENT_NOT_PINNED'
   state['remote']=state['head']
  def publish(path,data):
   path=Path(path)
   if path.exists():assert path.read_bytes()==data,'PUBLICATION_OVERWRITE'
   else:path.write_bytes(data)
  Core=SimpleNamespace(REMOTE=expected_remote,checkout=lambda work:repo,gout=gout,git=git,
   push=push,one_model=lambda repo:None,publish=publish,gitblob=gitblob,
   make_viewer=lambda *args:b'<html>synthetic Repl v0.6.17</html>')
  class Solver:
   SOURCE_SHA=hashlib.sha256(source).hexdigest()
   VERSION='0.6.20'
   EDITABLE={'Bone_015','Bone_014','Bone_021','Bone_020'}
   def evaluate(self,*args,**kwargs):
    if fail_model:raise RuntimeError('SYNTHETIC_FAILED_FULL_CYCLE')
    return b'SYNTHETIC_VERIFIED_IMPROVED_GLB',{'kinematics':{},'summary':{},'tested_physical_frames':1164},[
      {'outcome':'VALID_FULL_CYCLE','attempt':3}]
  stub=SimpleNamespace(EXPECTED_JOINTS=50)
  def deps(path,name):
   if str(path).endswith('git_core.py'):return Core
   if str(path).endswith('model.py'):return Solver()
   return stub
  drv.PARENT=state['head'];drv.SRC_SHA=hashlib.sha256(source).hexdigest()
  drv.SRC_BLOB=gitblob(source)
  argv=sys.argv;cwd=os.getcwd();capture=io.StringIO()
  try:
   with mock.patch.object(drv,'module',side_effect=deps),mock.patch.object(drv.Path,'home',return_value=home),redirect_stdout(capture):
    sys.argv=['driver','--packet',str(HERE)];code=drv.main()
  finally:
   sys.argv=argv;os.chdir(cwd)
  out=capture.getvalue()
  assert (repo/'AGENTS.md').read_bytes()==current.rstrip(b'\n')+b'\n\n'+(HERE.parent/'AGENTS_ADDENDUM.md').read_bytes()
  assert (repo/'campaigns/repl_cartoon_fk_hoof_driver_v0_6_20.py').is_file()
  assert state['head']==state['remote']
  if fail_model:
   assert code==2 and state['commits']==1 and model.read_bytes()==source
   assert 'MODEL_UNCHANGED=PASS' in out
  else:
   assert code==0 and state['commits']==2 and model.read_bytes()!=source
   assert (down/'REPL_CARTOON_FK_HOOF_WALK_v0.6.20_report.json').is_file()
   assert (down/'REPL_CARTOON_FK_HOOF_WALK_v0.6.20_TEXTURED_POSE_LAB.html').is_file()
   assert 'HUMAN_VISUAL_ACCEPTANCE=PENDING' in out
  return True
if __name__=='__main__':
 assert case(True) and case(False)
 print('FULL_MOCK_REPOSITORY_DRIVER_BLOCK_AND_SUCCESS_PATHS=PASS')
 print('FULL_MOCK_TESTS_ARE_NOT_PRODUCTION_GLB_VERIFICATION')
