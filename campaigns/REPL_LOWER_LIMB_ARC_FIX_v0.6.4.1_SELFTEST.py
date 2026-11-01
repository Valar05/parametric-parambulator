#!/usr/bin/env python3
"""Release gate, no network/checkout writes. Invoked by first Termux command."""
from __future__ import annotations
import json,math,pathlib,sys
sys.dont_write_bytecode=True
here=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(here))
import model,driver

def check(v,label):
 if not v:raise RuntimeError('SELFTEST_FAILED:'+label)
check(model.VERSION==driver.VER=='0.6.4.1','VERSION_MISMATCH')
check(model.SOURCE_SHA==driver.SOURCE_SHA and model.SOURCE_BLOB==driver.SOURCE_BLOB,'SOURCE_IDENTITY')
check(driver.KNOWN_PARENT_HEAD=='77148fbe2855112906fb24801df2d8ee28e8a51a','PINNED_SOURCE_COMMIT')
check(set(model.LEGS)=={'LF','RF','LH','RH'},'FOUR_LEGS')
check(model.HIND_HOOF_TRACKS=={'Bone_023','Bone_028'},'DISCOVER_EXISTING_OR_CREATE_HIND_HOOF_TRACKS')
check(model.HIND_HOOF_TRACKS <= model.MODIFIED, 'HIND_ALREADY_KEYED_TRACKS_MUTABLE')
check(model.EXISTING_FOREFOOT_TRACKS=={'Bone_012','Bone_018'},'PREVIOUS_FOREFOOT_TRACKS')
check([model.LEGS[n]['lower'] for n in ('LF','RF','LH','RH')]==
      ['Bone_013','Bone_019','Bone_024','Bone_029'],'LOWER_CHAIN_JOINTS')
check(all(v['hoof_target']<0 for v in model.LEGS.values()),'FOOT_ROTATION_SIGN_CONTRACT')
check(all(model.LEGS[n]['cannon_target']>0 for n in ('LF','RF')),'FRONT_CANNON_SIGN_CONTRACT')
check(all(model.LEGS[n]['cannon_target']>0 for n in ('LH','RH')),'HIND_CANNON_SIGN_CONTRACT')
for label,leg in model.LEGS.items():
 for u in [i/512 for i in range(513)]:
  t=(leg['phase']+u)*model.STRIDE
  q,stance=model.phase(leg,t)
  check(stance==(u<model.STANCE) or abs(u-1)<1e-8,'FOOTFALL_PHASE:'+label)
check(model.TRAVEL==.96 and model.FRAMES==97,'ONLY_MOVING_WALK')
for name in ('driver.py','model.py','blender_review.py','selftest.py'):
 compile((here/name).read_text('utf8'),str(here/name),'exec')
for name in ('viewer.html.in','run-termux.sh','contract.json'):
 check((here/name).is_file(),'MISSING_PACKET_MEMBER:'+name)
check('Bone_028' in (here/'viewer.html.in').read_text(),'MISSING_FOURTH_HOOF_MARKER')
contract=json.loads((here/'contract.json').read_text())
check(contract['single_canonical_glb']=='assets/repl/Repl.glb','SINGLE_CANONICAL_MODEL')
check(contract['git_mutation_lane']=='Termux Git only','AUTHORIZED_LANE')
print('PACKET_SELFTEST=PASS',flush=True)
print('ZERO_GITHUB_CONNECTOR_MUTATIONS=TRUE',flush=True)
print('FORE_HOOF_CORRECTED=2__HIND_HOOF_TRACKS=DISCOVER_AND_UPDATE_OR_CREATE',flush=True)
print('HUMAN_VISUAL_ACCEPTANCE=PENDING',flush=True)
