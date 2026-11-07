#!/usr/bin/env python3
"""Regression tests on actual skinned Obsidianti rig, with deliberately synthetic action fixture."""
import copy,importlib.util,json,math,pathlib,sys,tempfile
import bake

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def run(real,kernel):
 src=pathlib.Path(real)
 j,buf=kernel.read_glb(src)
 assert len(j['meshes'])>=4 and len(j['skins'])==1
 fixture=copy.deepcopy(j)
 original=copy.deepcopy(j['animations'][0])
 fixture['animations']=[]
 for n in range(41):
  a=copy.deepcopy(original);a['name']='Synthetic'+str(n);fixture['animations'].append(a)
 # Actual rig and skin, synthetic very short movement sections. Never infer real 41 clip success from this.
 fixture['animations'][0]['name']=bake.SPEAR
 fixture['animations'][1]['name']=bake.ATTACK
 # Full attack original spans roughly .8s in AxeKick donor; sufficient IK geometric exercise.
 with tempfile.TemporaryDirectory(prefix='obs-ik-v233-') as td:
  td=pathlib.Path(td)
  sim=td/'synthetic_41.glb';kernel.glb_save(fixture,buf,sim)
  output=td/'out.glb';report=td/'proof.json'
  data=bake.bake(sim,output,report,kernel,expected_sha=kernel.digest(sim))
  assert data['outputClipCount']==42 and data['maxGripErrorAfterPrepM']<1e-4
  assert data['maxStretchFactor']>=1
  old,oldbin=kernel.read_glb(sim);new,newbin=kernel.read_glb(output)
  assert new['animations'][:41]==old['animations'] and newbin.startswith(oldbin)
  assert new['animations'][41]['name']==bake.VARIANT
  assert new['meshes']==old['meshes'] and new['nodes']==old['nodes']
  assert len(data['frameDiagnostics'])>40 and any(v['phase']=='PREP' for v in data['frameDiagnostics'])
  assert all(v['gripErrorM']<0.0001 for v in data['frameDiagnostics'] if v['phase']=='ATTACK')
  try:bake.bake(sim,output,report,kernel,expected_sha=kernel.digest(sim))
  except ValueError as e:assert 'VERSIONED_OUTPUT_COLLISION' in str(e)
  else:raise AssertionError('OUTPUT_COLLISION_NOT_REJECTED')
  try:bake.bake(sim,td/'wrong.glb',td/'wrong.json',kernel,expected_sha='0'*64)
  except ValueError as e:assert 'SOURCE_41_CLIP_SHA_DRIFT' in str(e)
  else:raise AssertionError('WRONG_SHA_NOT_REJECTED')
  del fixture['animations'][0];bad=td/'missing.glb';kernel.glb_save(fixture,buf,bad)
  try:bake.bake(bad,td/'bad.glb',td/'bad.json',kernel,expected_sha=kernel.digest(bad))
  except ValueError as e:assert 'EXPECTED_EXACT_41_CLIP_SOURCE_LIBRARY' in str(e)
  else:raise AssertionError('MISSING_ANIMATION_NOT_REJECTED')
  print('REAL_RIG_SYNTHETIC_IK_42_CLIP_TEST_PASS max_stretch='+str(data['maxStretchFactor'])+' max_grip_error='+str(data['maxGripErrorAfterPrepM']))

if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('usage: test_bake.py ACTUAL_RIG_GLB PRIOR_COMPOSER_PATH')
 run(sys.argv[1],load(sys.argv[2],'pinned_prior_compose'))
