#!/usr/bin/env python3
"""Runs against the actual v2.0.33 rig on Termux before any production mutation.
Also verifies absence of output/path substitutions and preservation of exact prior clips.
"""
from __future__ import annotations
import importlib.util,pathlib,sys,math,copy,tempfile
import fix

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_adaptive_grid():
 import struct
 f32=fix.f32_time
 end=f32(1.13)
 # Genuine float32 accessor keys plus conceptual decimal anchors, at the exact
 # failure seam from the previous release.
 first=[f32(end*i/100) for i in range(101)]
 one=fix.adaptive_key_grid(first,end)
 assert all(b>a+1e-6 for a,b in zip(one,one[1:]))
 assert all(a in one for a in (f32(0),f32(.175),f32(.23),end))
 assert one==fix.adaptive_key_grid(one,end),'NORMALIZATION_NOT_IDEMPOTENT'
 refine=[a+(b-a)*r for a,b in zip(one,one[1:]) for r in (.25,.5,.75) if b>fix.LEAD]
 two=fix.adaptive_key_grid([*one,*refine,f32(.23),.23,.175,f32(.175)],end)
 assert len(two)>len(one),'SECOND_ATTEMPT_DID_NOT_REFINE'
 assert all(b>a+1e-6 for a,b in zip(two,two[1:])), 'SECOND_ATTEMPT_NONMONOTONE'
 assert two==fix.adaptive_key_grid(two,end),'SECOND_ATTEMPT_NOT_IDEMPOTENT'
 assert all(f32(t)==t for t in two),'SECOND_ATTEMPT_NOT_GLTF_REPRESENTABLE'
 for corrupted in ([float('nan')],[float('inf')],[-.01],[end+.01]):
  try:fix.adaptive_key_grid(corrupted,end)
  except ValueError:pass
  else:raise AssertionError('BAD_GRID_INPUT_ACCEPTED_'+str(corrupted))
 try:fix.adaptive_key_grid([0.,.5],.23)
 except ValueError:pass
 else:raise AssertionError('INVALID_DURATION_NOT_REJECTED')
 print('V236_ADAPTIVE_FLOAT32_TWO_PASS_AND_NEGATIVE_TESTS_PASS first='+str(len(one))+' second='+str(len(two)))

def run(src,core):
 test_adaptive_grid()
 js,buf=core.read_glb(src);acts=js['animations'];names=[a['name'] for a in acts]
 assert len(names)==42 and names[-1]==fix.PREVIOUS and len(set(names))==42,'REAL_42_SOURCE_INVENTORY_DRIFT'
 assert len(js['meshes'])>=4 and len(js['skins'])==1,'ACTUAL_RIG_OR_SKIN_MISSING'
 ids=core.name_ids(js);pa=core.parents(js)
 assert all(n in ids for n in fix.LEFT+fix.RIGHT+fix.CENTER+(fix.WEAPON,)),'ARM_CHAIN_INCOMPLETE'
 clip=acts[-1];start,end=core.range_times(js,buf,clip)
 assert .5<=end<=2.0 and abs(start)<1e-3,'EXPECTED_ATTACK_DURATION_DRIFT'
 first=fix.snapshot(js,buf,clip,0.,core)
 palm,details=fix.palm_local_offset(first,ids,pa,core)
 assert details['knuckleCount']>=2 and details['palmOffsetM']>.004
 # Exercise world-frame shoulder/forearm/wrist solve on real skinned rig at
 # meaningful attack times (not an invented dummy skeleton).
 measured=[]
 for t in (fix.LEAD+.015,fix.LEAD+.08,fix.LEAD+.18,end-.1,end):
  pose=fix.snapshot(js,buf,clip,t,core)
  beforeq=fix.world(ids[fix.WEAPON],pose,pa,core)[1]
  right=fix.fix_right(pose,ids,pa,core)
  left=fix.fix_left(pose,ids,pa,core,palm)
  afterq=fix.world(ids[fix.WEAPON],pose,pa,core)[1]
  assert core.qdeg(beforeq,afterq)<.03,'RIGHT_ARM_ROTATED_LANCE_IN_TEST'
  assert left['palmErrorM']<.00012,'PALM_MISALIGNED_IN_TEST'
  assert right['newPenetration']<=right['oldPenetration']+1e-8,'ARM_PROXY_COLLISION_REGRESSION_IN_TEST'
  measured.append((right['beforeClearanceM'],right['afterClearanceM'],left['palmErrorM']))
 try:fix.run(src,pathlib.Path(tempfile.gettempdir())/'__unused_probe_glb__',pathlib.Path(tempfile.gettempdir())/'__unused_probe_proof__',core,None,expected_sha='0'*64)
 except ValueError as e:assert 'EXACT_V233_INPUT_SHA_INVALID' in str(e)
 else:raise AssertionError('BAD_INPUT_SHA_NOT_REJECTED')
 # Test exact source has an animation and enough time samples for the full move.
 assert details['knuckleCount']>=2 and len(measured)==5
 print('V236_REAL_42_CLIP_IK_PREFLIGHT_PASS palmLocalM='+str(details['palmOffsetM'])+
  ' samples='+str(len(measured))+' rightClearances='+str([(round(x,4),round(y,4)) for x,y,_ in measured]))

if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('usage: test.py REAL_V233_GLB V231_COMPOSER')
 run(pathlib.Path(sys.argv[1]),load(sys.argv[2],'v234_core'))
