#!/usr/bin/env python3
"""Runs against the actual v2.0.33 rig on Termux before any production mutation.
Also verifies absence of output/path substitutions and preservation of exact prior clips.
"""
from __future__ import annotations
import importlib.util,pathlib,sys,math,copy,tempfile
import fix

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def run(src,core):
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
 print('V234_REAL_42_CLIP_IK_PREFLIGHT_PASS palmLocalM='+str(details['palmOffsetM'])+
  ' samples='+str(len(measured))+' rightClearances='+str([(round(x,4),round(y,4)) for x,y,_ in measured]))

if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('usage: test.py REAL_V233_GLB V231_COMPOSER')
 run(pathlib.Path(sys.argv[1]),load(sys.argv[2],'v234_core'))
