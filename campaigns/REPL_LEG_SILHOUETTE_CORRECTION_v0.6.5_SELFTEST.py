#!/usr/bin/env python3
"""Static packet release gates for owner-corrected v0.6.5."""
import json,math,pathlib,sys
sys.dont_write_bytecode=True
here=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(here))
import model,driver

def must(ok,name):
 if not ok:raise RuntimeError('SELFTEST_FAILED:'+name)
must(model.VERSION==driver.VER=='0.6.5','VERSION_MATCH')
must(model.SOURCE_SHA==driver.SOURCE_SHA and model.SOURCE_BLOB==driver.SOURCE_BLOB,'PINNED_SOURCE')
must(driver.KNOWN_PARENT_HEAD=='bd0528afaf2640dcf3272b61b000f42442c6bc47','PINNED_MAIN_PARENT')
must(set(model.LEGS)=={'LF','RF','LH','RH'},'FOUR_LEGS')
must(model.CHANGED_NAMES=={'Bone_015','Bone_014','Bone_013','Bone_012','Bone_021','Bone_020','Bone_019','Bone_018','Bone_025','Bone_024','Bone_023','Bone_030','Bone_029','Bone_028'},'EXACT_ALLOWLIST')
for side in ('LF','RF'):
 angles=[x[2] for x in model.LEGS[side]['segment_targets']]
 must(angles==[12.,-20.,-23.,145.],'FORE_SEGMENT_DIRECTIONS')
for side in ('LH','RH'):
 must([x[2] for x in model.LEGS[side]['segment_targets']]==[-10.,-16.],'REAR_SEGMENT_DIRECTIONS')
for label in model.LEGS:
 for u in [k/512 for k in range(512)]:
  got,stance=model.phase(label,(model.LEGS[label]['phase']+u)*model.STRIDE)
  must(stance==(u<model.STANCE),'GROUNDED_PHASE_'+label)
for file in ('model.py','driver.py','blender_review.py','selftest.py'):
 compile((here/file).read_text('utf8'),file,'exec')
for file in ('viewer.html.in','run-termux.sh','contract.json'):
 must((here/file).is_file(),'PACKET_MEMBER_'+file)
contract=json.loads((here/'contract.json').read_text('utf8'))
must(contract['single_canonical_glb']=='assets/repl/Repl.glb','SINGLE_MODEL')
must(contract['git_mutation_lane']=='Termux Git only','TERMUX_WRITES')
print('PACKET_SELFTEST=PASS',flush=True)
print('VISIBLE_SILHOUETTE_GUARDS=FRONT_AND_REAR__STANCE_UNCHANGED',flush=True)
print('HUMAN_VISUAL_ACCEPTANCE=PENDING',flush=True)
