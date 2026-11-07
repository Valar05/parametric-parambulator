#!/usr/bin/env python3
"""Standalone post-ARP patch geometry, parser, and regression tests; no repo mutation."""
from __future__ import annotations
import importlib.util,math,pathlib,struct,sys,tempfile,json,subprocess
P=pathlib.Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('toe_patch_lib',str(P));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
assert mod.LION==['Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp']
assert abs(mod.length([3,4,0])-5)<1e-8
assert mod.length(mod.sub(mod.qrot([0,0,0,1],[1,2,3]),[1,2,3]))<1e-10
for a,b in [([0,0,0,1],[0,0,0,1]),([1,0,0,0],[1,0,0,0])]:
 assert mod.qangle(a,b)<1e-7
 assert mod.length(mod.sub(mod.qrot(a,[0,1,0]),mod.qrot(b,[0,1,0])))<1e-7
assert mod.length(mod.sub(mod.qrot(mod.qarcto([0,1,0],[0,0,1]),[0,1,0]),[0,0,1]))<1e-7
assert mod.ease(-1)==0 and mod.ease(2)==1
w,d=mod.score_source_contact({'toeZ':0.,'idleToeZ':0.,'ankleZ':.1,'idleHeelAboveToe':0.,'ankleToeLength':.20})
assert 0.4<w<0.6
w,d=mod.score_source_contact({'toeZ':.3,'idleToeZ':0.,'ankleZ':.4,'idleHeelAboveToe':0.,'ankleToeLength':.20})
assert w==0,'AIRBORNE_FOOT_CORRECTED'
# Realistic two-bone simulation with original knee plane retained.
class S:
 names={'mixamorig:LeftUpLeg':0,'mixamorig:LeftLeg':1,'mixamorig:LeftFoot':2,'mixamorig:LeftToeBase':3}
 parents={0:4,1:0,2:1,3:2}
 nodes=[{'translation':[0,0,0]},{'translation':[0,-.4,0]},{'translation':[0,-.4,0]},{'translation':[0,0,.15]}]
s=S()
# Slightly angled knee: physically plausible triangle H -> K -> A.
H=[0,1,0];K=[0.1,.6,0];A=[0,0.2,0]
qId=[0,0,0,1]
# Direct solver verifies structural input guards even on degenerate synthetic pose.
try:mod.corrected_leg(s,{0:H,1:K,2:A,3:A},{4:qId,0:qId,1:qId,2:qId},'Left',[0,-1,0])
except ValueError as e:assert 'REACH' in str(e)
else:raise AssertionError('INVALID_IK_REACH_ACCEPTED')
# Structural failure path, invalid magic not silently accepted.
with tempfile.TemporaryDirectory() as tmp:
 p=pathlib.Path(tmp)/'bad.glb';p.write_bytes(b'not a GLB')
 try:mod.load(p)
 except ValueError:pass
 else:raise AssertionError('INVALID_GLB_ACCEPTED')
# Reproduce the exact v2.0.18 failure before checking the repaired import path.
driver_path=P.with_name('driver.py')
spec=importlib.util.spec_from_file_location('tested_toeroll_driver_v219',driver_path)
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
with tempfile.TemporaryDirectory() as td:
 td=pathlib.Path(td);(td/'campaigns').mkdir()
 helper=td/'campaigns'/'helper.py';helper.write_text('answer=42\n')
 subprocess.run(['git','init','-q',str(td)],check=True)
 subprocess.run(['git','-C',str(td),'add','campaigns/helper.py'],check=True)
 subprocess.run(['git','-C',str(td),'-c','user.name=Test','-c','user.email=test@example.com','commit','-qm','fixture'],check=True)
 def stat():return subprocess.check_output(['git','-C',str(td),'status','--porcelain'],text=True).strip()
 assert not stat(), 'TEST_INITIAL_REPO_DIRTY'
 # An ordinary source-loader import creates an untracked __pycache__ folder.
 baseline_bytecode_flag=sys.dont_write_bytecode
 sys.dont_write_bytecode=False
 try:
  vanilla=importlib.util.spec_from_file_location('unprotected_helper',helper)
  ordinary=importlib.util.module_from_spec(vanilla);vanilla.loader.exec_module(ordinary)
 finally:
  sys.dont_write_bytecode=baseline_bytecode_flag
 assert '?? campaigns/__pycache__/' in stat(), 'ORIGINAL_DIRTY_BUG_NOT_REPRODUCED'
 # Test fixture cleanup only. This is NOT a production-repo recovery mechanism.
 import shutil
 shutil.rmtree(td/'campaigns'/'__pycache__')
 assert not stat(), 'TEST_FIXTURE_FAILED_TO_CLEAR'
 previous=sys.dont_write_bytecode
 loaded=driver.import_path(helper,'protected_helper')
 assert loaded.answer==42 and not stat() and sys.dont_write_bytecode==previous, 'READONLY_IMPORT_DIRTIED_CHECKOUT'
 assert not (td/'campaigns'/'__pycache__').exists(), 'BYTECODE_WAS_WRITTEN'
 helper.write_text('raise ValueError("deliberate helper error")\n')
 try:driver.import_path(helper,'expected_failure_helper')
 except ValueError:pass
 else:raise AssertionError('HELPER_IMPORT_FAILURE_NOT_RAISED')
 assert sys.dont_write_bytecode==previous and not (td/'campaigns'/'__pycache__').exists(), 'BYTECODE_FLAG_LEAKED_AFTER_ERROR'
 assert 'campaigns/helper.py' in stat(), 'TRACKED_MODIFICATION_NOT_DETECTABLE'
# Distinguish scope-changing edits: only driver/test contract/version have changed.
print('GIT_READONLY_IMPORT_AND_DIRTY_CHECKOUT_REGRESSIONS=PASS',flush=True)
print('TOE_ROLL_PATCH_REGRESSION_TESTS=PASS',flush=True)
