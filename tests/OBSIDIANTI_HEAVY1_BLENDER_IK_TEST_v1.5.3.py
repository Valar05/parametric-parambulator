#!/usr/bin/env python3
"""Source and runner tests. Green tests never replace actual Blender/skinned preflight."""
from __future__ import annotations
import argparse, ast, hashlib, importlib.util, json, pathlib, subprocess, sys, tempfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
RUN=ROOT/'campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.3.py'
EVAL=ROOT/'campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_v1.5.3.py'
APPLY=ROOT/'campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_APPLY_v1.5.3.py'

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
R=load(RUN,'h151runner')
P=load(APPLY,'h151apply')

def must(v,msg):
 if not v:raise AssertionError(msg)
def cmd(*args):
 p=subprocess.run(args,capture_output=True,text=True)
 if p.returncode:raise AssertionError('git fixture: '+p.stderr[-600:])
 return p.stdout.strip()

def test_ast():
 for path in (RUN,EVAL,APPLY):
  ast.parse(path.read_text())
 s=EVAL.read_text();a=APPLY.read_text();r=RUN.read_text()
 must("constraints.new('IK')" in s and 'ik.chain_count=2' in s, 'real Blender IK chain not created')
 must("constraints.new('COPY_ROTATION')" in s,'native foot-roll copy rotation omitted')
 must('pole_target=controls' in s,'real pole target omitted')
 must('base_idle_under_hip' in s and 'badHeavy1FKUsedToInitializeIK' in r,'wrong target baseline')
 must('pole_local=target_local+align@poleLever*scale' in s,'pole lever arm not preserved')
 must("clip['name']" not in s or 'Lionheart_Heavy1' in s,'unexpected authoring mode')
 must('M.skin_foot_points' in a and 'physicalProbeCount' in a, 'skinned witnesses missing')
 must('set(edits)!=allowed' in r,'six-track allowlist missing')
 must('worldDelta=v3(controller' in s and "worldDelta+residual" in s,'source controller not driven by world displacement')
 must('sourceControllerNetDisplacement_m' in a and 'sum(length(vec(y,x))' in a,'cyclic motion measured as zero')
 must('SOURCE_WORLD_FOOT_CONTROLLER_DELTA_NO_DONOR_PELVIS_COMPENSATION' in s,'trajectory provenance missing')
 must('no force' not in r.lower() or 'PUSH_REFUSED_REMOTE_ADVANCED' in r,'remote push guard missing')

def test_local_git_publication_and_rejection():
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d);bare=p/'remote.git';repo=p/'repo';other=p/'other'
  cmd('git','init','--bare',str(bare));cmd('git','init','-b','main',str(repo))
  cmd('git','-C',str(repo),'config','user.name','test')
  cmd('git','-C',str(repo),'config','user.email','test@example.invalid')
  (repo/'test.txt').write_text('first')
  head=R.commit(repo,['test.txt'],'fixture origin')
  cmd('git','-C',str(repo),'remote','add','origin',str(bare))
  must(R.push(repo,head)==head,'readback push failed')
  cmd('git','-C',str(bare),'symbolic-ref','HEAD','refs/heads/main')
  cmd('git','clone',str(bare),str(other))
  cmd('git','-C',str(other),'config','user.name','rival')
  cmd('git','-C',str(other),'config','user.email','rival@example.invalid')
  (other/'other.txt').write_text('advanced')
  cmd('git','-C',str(other),'add','other.txt');cmd('git','-C',str(other),'commit','-m','remote advanced')
  cmd('git','-C',str(other),'push','origin','main')
  (repo/'test.txt').write_text('stale')
  stale=R.commit(repo,['test.txt'],'should reject')
  try:R.push(repo,stale)
  except RuntimeError as err:
   must('PUSH_REFUSED_REMOTE_ADVANCED' in str(err),'wrong nonforce push rejection')
  else:raise AssertionError('stale Git push unexpectedly succeeded')

def test_manifest_and_archive():
 with tempfile.TemporaryDirectory() as d:
  root=pathlib.Path(d);file=root/'a';file.write_text('hello')
  dest=root/'record.zip';digest=R.write_evidence_zip(dest,{'a':file})
  must(digest==R.sha(dest),'evidence ZIP hash wrong')
  try:R.write_evidence_zip(dest,{'a':file})
  except RuntimeError:pass
  else:raise AssertionError('duplicate ZIP overwrote existing')
  spec=root/'package';spec.mkdir();(spec/'manifest.json').write_text('{}')
  try:R.verify_packet(spec)
  except RuntimeError:pass
  else:raise AssertionError('malformed manifest passed')

def test_current_canonical(repo):
 must(R.sha(repo/R.MODEL)==R.MODEL_SHA,'actual current canonical GLB wrong')
 must(R.sha(repo/R.DONOR)==R.DONOR_SHA,'original source IK archive has changed')
 must(R.sha(repo/R.CALIB)==R.CALIB_SHA,'calibration source changed')
 must(R.sha(repo/R.MATH)==R.MATH_SHA,'pinned skinning/glTF helper changed')
 sp=importlib.util.spec_from_file_location('h151mat',repo/R.MATH)
 M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)
 g,b=M.load_glb(repo/R.MODEL)
 names=[a['name'] for a in g['animations']]
 must('Lionheart_Heavy1' in names and 'LionheartIdle_UNREVIEWED' in names,'source target clips missing')
 must('Lionheart_Heavy2' in names and 'Ares_StepForward_Lower' in names,'protected source clips missing')
 must(len(g['skins'])==1 and len(g['animations'])>=23,'source skin or actions missing')
 w,skin,ibm=M.foot_witnesses(g,b)
 must(len(w['Left'])>=16 and len(w['Right'])>=16,'no physical wedge sole witnesses')
 idle=M.global_matrices(g,M.channels(g,b,next(a for a in g['animations'] if a['name']=='LionheartIdle_UNREVIEWED')),0)
 must(all('mixamorig:'+s+'Foot' in [n.get('name') for n in g['nodes']] for s in ('Left','Right')),'foot bone missing')
 source=json.loads((repo/R.DONOR).read_text())
 must(source['action']=='Heavy1' and len(source['frames'])==61,'native source frame count incorrect')
 p=source['frames'][0]['bones']
 for side in ('Left','Right'):
  pole=P.length(P.vec(p[side+'Knee.IK']['worldPosition'],p['mixamorig:'+side+'Leg']['worldPosition']))
  must(pole>.25,'pole accidentally coincident with physical knee')
 # Inject a wrong model into independent application and prove it stops before mutation.
 with tempfile.TemporaryDirectory() as tmp:
  wrong=pathlib.Path(tmp)/'wrong.glb';wrong.write_bytes(b'not the model')
  command=[sys.executable,str(APPLY),'--model',str(wrong),'--math-helper',str(repo/R.MATH),
         '--native-ik-samples',str(wrong),'--source',str(repo/R.DONOR),
         '--report',str(pathlib.Path(tmp)/'report.json'),'--out',str(pathlib.Path(tmp)/'candidate.glb')]
  cp=subprocess.run(command,capture_output=True,text=True)
  must(cp.returncode!=0 and 'MODEL_CHANGED_FROM_PINNED_BYTES' in cp.stderr,'tampered model not rejected')
  must(wrong.read_bytes()==b'not the model','tampered model test wrote input')
 print('VERIFIED_REAL_SOURCE_AND_SKINNED_WEDGE_WITNESSES=YES')

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo');args=p.parse_args()
 test_ast();test_manifest_and_archive();test_local_git_publication_and_rejection()
 if args.repo:test_current_canonical(pathlib.Path(args.repo))
 print('ALL_TESTS_PASSED=SOFTWARE_SOURCE_STRUCTURE_AND_GIT_GUARDS')
 print('NATIVE_BLENDER_AND_FULL_SKINNED_VALIDITY=SEPARATE_RUNTIME_GATES')
if __name__=='__main__':main()
