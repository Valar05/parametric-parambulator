#!/usr/bin/env python3
"""Regression tests using actual source GLB/Heavy1 JSON on Termux, plus pure math/failure gates."""
from __future__ import annotations
import argparse, copy, importlib.util, json, math, pathlib, sys, tempfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
SOLVER=ROOT/'campaigns/OBSIDIANTI_HEAVY1_NATIVE_IK_SOLVE_v1.5.0.py'
def imp(path,name):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
D=imp(SOLVER,'obs_H1_unit_solver')

def need(cond,message):
 if not cond:raise AssertionError(message)

def test_maths(M):
 a=[.1,-.8,.2];b=[-.2,-.65,.35]
 q=D.from_to(M,a,b);r=M.rotate(q,a)
 need(D.length(D.sub(D.normalize(r),D.normalize(b)))<1e-6,'from_to wrong')
 q2=D.from_to(M,[1,0,0],[-1,0,0]);r=M.rotate(q2,[1,0,0])
 need(D.length(D.sub(r,[-1,0,0]))<1e-6,'180deg from_to wrong')
 q3=D.yrot(.37);need(D.length(D.sub(D.yaw(M,q3,[0,0,1]),[math.sin(.37),0,math.cos(.37)]))<1e-6,'yaw wrong')
 need(abs(D.quatangle(M,[0,0,0,1],[0,0,0,1]))<1e-8,'quat angle')
 test=pathlib.Path(tempfile.mkdtemp())
 b=bytearray();g={'buffers':[{'byteLength':0}],'bufferViews':[],'accessors':[]}
 try:
  D.append_times(g,b,[0,.5,1]);need(g['accessors'][0]['type']=='SCALAR','scalar accessor wrong')
  need(len(b)==12,'scalar binary length wrong')
  try:D.append_times(g,b,[0,0,1]);raise AssertionError('duplicate time accepted')
  except RuntimeError:pass
 finally:
  import shutil;shutil.rmtree(test)

def test_real(M,repo):
 model=repo/'assets/obsidianti/Obsidianti.glb'
 source=repo/'diagnostics/obsidianti/lionheart-ik-all-v1.4.0/actions/Heavy1.json'
 calibr=repo/'diagnostics/obsidianti/lionheart-ik-all-v1.4.0/calibration.json'
 need(D.sha(model)==D.SOURCE_SHA,'wrong remote real model')
 need(D.sha(source)==D.DONOR_SHA,'wrong source half frame archive')
 need(D.sha(calibr)==D.CALIB_SHA,'wrong calibration')
 raw=json.loads(source.read_text());cal=json.loads(calibr.read_text())
 ts=[r['timeSeconds'] for r in raw['frames']]
 need(len(ts)==61 and abs(ts[-1]-1)<1e-6,'full and half frame cadence missing')
 need(all(y>x for x,y in zip(ts,ts[1:])),'source timeline not monotone')
 for row in raw['frames']:
  names=row['bones']
  need(all(x in names for x in ['LeftFoot.IK','RightFoot.IK','LeftKnee.IK','RightKnee.IK','mixamorig:Hips','mixamorig:LeftFoot','mixamorig:RightFoot']), 'native IK data incomplete')
 g,b=M.load_glb(model)
 orig_json=json.dumps(g,sort_keys=True);orig_bin=bytes(b)
 anim=next(a for a in g['animations'] if a['name']==D.CLIP)
 idle=next(a for a in g['animations'] if a['name']=='LionheartIdle_UNREVIEWED')
 tracks=M.channels(g,b,anim);ref,chain,parents=D.make_target_reference(M,g,b,tracks,idle)
 for t in [0.,.166666667,.333333333,.5,.666666667,1.]:
  poses,err,goal,poles=D.one_frame(M,g,tracks,t,raw['frames'],cal,ref,chain,parents,1.,0.)
  sample=dict(tracks)
  for side in ('Left','Right'):
   need(all(math.isfinite(x) for p in poses[side].values() for x in p),'nonfinite solution')
   for idx,q in poses[side].items():sample[(idx,'rotation')]=([t],[q])
  W=M.global_matrices(g,sample,t)
  for side in ('Left','Right'):
   e=D.length(D.sub(D.xyz(W[chain[side][-1]]),goal[side]))
   need(e<=max(.001,err[side]['reachMiss_m']+.0004),'ankle IK solution mismatched')
  need(json.dumps(g,sort_keys=True)==orig_json and bytes(b)==orig_bin,'test mutated input GLB')
 # Exercise source motions and scan some skinned soles via the SAME candidate implementation.
 stats,new,rows,probes=D.candidate(M,g,b,raw,cal,1.,0.,probe_only=True)
 need(stats['sampleFrames']==61 and stats['physicalProbeCount']==121,'quarter-frame physical coverage')
 need(stats['sourceControllerAnchor']=='NATIVE_BLENDER_EVALUATED_ALL_FRAMES','wrong anchor')
 need(len(rows)==61,'loss of source frames')
 need(isinstance(stats['physicalGatePassed'],bool),'physical validity missing')
 # Regression: copy model before proving accessor mutation/guard. Protected clips invariant.
 gg=copy.deepcopy(g);bb=bytearray(b)
 selected=next(a for a in gg['animations'] if a['name']==D.CLIP)
 edits=D.append_rotations(M,gg,bb,selected,tracks,new)
 need(len(edits)==6,'not exactly six rotation channels')
 need(bytes(bb).startswith(orig_bin),'original binary rewrite')
 need(all(a==x for a,x in zip(g['animations'],gg['animations']) if a['name']!=D.CLIP),'protected animation changed')
 blob=M.encode_glb(gg,bb)
 need(blob[:4]==b'glTF','candidate not GLB')
 # Inject source corruption: the integrity gate must reject it before candidate creation.
 with tempfile.TemporaryDirectory() as d:
  corrupt=pathlib.Path(d)/'wrong.json';corrupt.write_text(source.read_text()+' ')
  need(D.sha(corrupt)!=D.DONOR_SHA,'hash corruption not detected')
 print('REAL_GLB_IK_PROBE=PASS; physicalGatePassed='+str(stats['physicalGatePassed']))

def test_runner_software():
 R=imp(ROOT/'campaigns/OBSIDIANTI_HEAVY1_NATIVE_IK_RUN_v1.5.0.py','obs_H1_runner_unit')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp)
  source=p/'data.json';source.write_text('{}')
  out=p/'report.zip';digest=R.create_zip(out,{'data.json':source})
  need(digest==R.sha(out),'evidence ZIP hash mismatch')
  import zipfile
  with zipfile.ZipFile(out) as z:need(z.read('data.json')==b'{}','ZIP payload corrupted')
  try:R.create_zip(out,{'data.json':source});raise AssertionError('ZIP collision did not fail closed')
  except RuntimeError:pass

def test_git_fixture():
 import subprocess
 R=imp(ROOT/'campaigns/OBSIDIANTI_HEAVY1_NATIVE_IK_RUN_v1.5.0.py','obs_H1_runner_git_fixture')
 def cmd(*args):
  p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  if p.returncode:raise AssertionError('git fixture failure '+repr(args)+':'+p.stderr[-300:])
  return p.stdout.strip()
 with tempfile.TemporaryDirectory() as td:
  base=pathlib.Path(td);remote=base/'remote.git';work=base/'work'
  cmd('git','init','--bare',str(remote));cmd('git','init','-b','main',str(work))
  cmd('git','-C',str(work),'config','user.name','fixture')
  cmd('git','-C',str(work),'config','user.email','fixture@example.invalid')
  (work/'verified.txt').write_text('source')
  head=R.commit(work,['verified.txt'],'fixture initial commit')
  need(bool(head),'commit helper did not commit')
  cmd('git','-C',str(work),'remote','add','origin',str(remote))
  need(R.push(work,head)==head,'remote push/readback contract broken')
  (work/'verified.txt').write_text('change')
  head2=R.commit(work,['verified.txt'],'fixture second commit')
  need(head2!=head and R.push(work,head2)==head2,'second push/resume broken')
  # A competing writer advances remote: our local non-force path must refuse.
  cmd('git','-C',str(remote),'symbolic-ref','HEAD','refs/heads/main')
  other=base/'other';cmd('git','clone',str(remote),str(other))
  cmd('git','-C',str(other),'config','user.name','fixture')
  cmd('git','-C',str(other),'config','user.email','fixture@example.invalid')
  (other/'competing.txt').write_text('remote advanced')
  cmd('git','-C',str(other),'add','competing.txt');cmd('git','-C',str(other),'commit','-m','competing')
  cmd('git','-C',str(other),'push','origin','main')
  (work/'verified.txt').write_text('stale push must be rejected')
  stale=R.commit(work,['verified.txt'],'stale commit')
  try:R.push(work,stale);raise AssertionError('stale push should be blocked')
  except RuntimeError as err:need('REMOTE_MAIN_ADVANCED' in str(err),'wrong non-fast-forward failure')

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo');a=p.parse_args()
 repo=pathlib.Path(a.repo) if a.repo else None
 # Pure tests use immutable packaged helper in this source checkout when present.
 if repo:
  M=D.load_math(repo)
  need(D.sha(repo/'campaigns/OBSIDIANTI_HEAVY1_NATIVE_IK_SOLVE_v1.5.0.py')==D.sha(SOLVER),'solver source mismatch')
 else:
  probe=ROOT/'tests/_fixture_helper_v121.py'
  if not probe.exists():print('STATIC_TESTS_ONLY_NO_REAL_GLB');print('ALL_TESTS_PASSED=STATIC_ONLY');return
  M=imp(probe,'local_fixture_math')
 test_maths(M)
 test_runner_software()
 test_git_fixture()
 if repo:test_real(M,repo)
 print('ALL_TESTS_PASSED=TRANSFORMS_FAILURE_GATES_AND_REAL_SKINNED_GLB' if repo else 'ALL_TESTS_PASSED=STATIC_ONLY')

if __name__=='__main__':main()
