#!/usr/bin/env python3
"""Offline packet and regression guards; main driver reruns on real canonical GLB."""
import importlib.util,hashlib,json,pathlib,sys,math
root=pathlib.Path(__file__).resolve().parent
man=json.loads((root.parent/'manifest.json').read_text())
assert man['campaign']=='REPL_CARTOON_FK_HOOF_WALK' and man['version']=='0.6.8'
for rel,expected in man['sha256'].items():
 p=root.parent/rel
 assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==expected, ('PACKET_HASH',rel)
assert len(man['sha256'])==8 and set(man['sha256'])=={'README.md','campaign/model.py','campaign/driver.py','campaign/viewer.html.in','campaign/blender_review.py','campaign/run-termux.sh','campaign/selftest.py','campaign/contract.json'}

spec=importlib.util.spec_from_file_location('model_selftest',root/'model.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.SOURCE_SHA=='c3209b404b5c50842591cfa654142d2f0d84d27eb1acf7779b8d4d504d4508af'
assert m.CANON=='assets/repl/Repl.glb' and len(m.LEGS)==4
assert set(m.MODIFIED)=={'Bone_013','Bone_019','Bone_024','Bone_025','Bone_026','Bone_029','Bone_030','Bone_031','Bone_012','Bone_018','Bone_023','Bone_028'}
assert set(m.FRONT_MIDDLE).isdisjoint(m.MODIFIED)
assert set(m.FIXED)=={'Bone_012','Bone_018','Bone_023','Bone_028'}
for label in m.LEGS:
 s=[i/100 for i in range(101)];peak=max(m.pulse(u) for u in s)
 assert 0.95<peak<=1.01
 assert all(abs(m.pulse(u))<1e-9 for u in s if u<m.STANCE)
print('PACKET_SELFTEST=PASS',flush=True)
print('CARTOON_LEG_DRIVERS_AND_FK_LOCKS=PASS',flush=True)
print('HOOF_DEFORMATION_BRANCHES=GUARDED_ON_REAL_MODEL',flush=True)

# v0.6.8 selftest: sign cannot be discarded by absolute quaternion distance.
class QB:
 @staticmethod
 def qmul(a,b):
  x,y,z,w=a;X,Y,Z,W=b
  return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,
          w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
origin=(0.,0.,0.,1.)
for degrees in (-48.,-19.,19.,48.):
 rad=math.radians(degrees)/2
 q=(math.sin(rad),0.,0.,math.cos(rad))
 assert abs(m.signed_local_x_delta(origin,q,QB)-degrees)<1e-7
assert m.stance_frames('LF')[0]==8 and max(m.stance_frames('RF'))>31
assert set(m.FIXED)=={'Bone_012','Bone_018','Bone_023','Bone_028'}
print('SIGNED_BEND_DIRECTION_AND_WRAPPED_STANCE_SELFTEST=PASS',flush=True)
