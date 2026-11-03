#!/usr/bin/env python3
"""Packet integrity + pure geometry regression; actual model checks run in Termux."""
import hashlib,importlib.util,json,math,pathlib,sys
sys.dont_write_bytecode=True
root=pathlib.Path(__file__).resolve().parent
manifest=json.loads((root.parent/'manifest.json').read_text('utf8'))
assert manifest['campaign']=='REPL_CARTOON_FK_HOOF_WALK'
assert manifest['version']=='0.6.10'
expected={
 'campaign/regression.py','README.md','campaign/model.py','campaign/driver.py','campaign/viewer.html.in',
 'campaign/blender_review.py','campaign/run-termux.sh','campaign/selftest.py','campaign/contract.json'}
assert set(manifest['sha256'])==expected
for rel,digest in manifest['sha256'].items():
 p=root.parent/rel
 assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,rel
spec=importlib.util.spec_from_file_location('repl0610',root/'model.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.SOURCE_SHA=='eff0c604ca56ba58543c7a477bffc0e22e3c23f1d5da00bdbf1ea62369f27509'
assert m.EDITED=={'Bone_015','Bone_014','Bone_021','Bone_020'}
assert not (m.EDITED & m.PROTECTED_HIND)
assert not (m.EDITED & m.PROTECTED_TOES)
assert m.MID_CLEARANCE>0 and m.EARLY_CLEARANCE<0
assert all(20<=a<=30 and 20<=b<=60 for a,b in m.PROFILES)
for label in m.FRONT:
 vals=[m.pulse(m.phase(label,fr)[0]) for fr in range(m.PERIOD)]
 assert any(v>.9 for v in vals)
 assert all(v==0 for fr,v in enumerate(vals) if m.phase(label,fr)[1])
 assert len([fr for fr in range(m.PERIOD) if not m.phase(label,fr)[1]])>=10
assert m.delta_deg(179,-179)==-2 and m.delta_deg(-179,179)==2

# Algebraic polarity regression, not a claim about the actual 50-joint rig.
class FakeBase:
 def __init__(self,polarity): self.polarity=polarity
 def axisq(self,axis,degrees):
  h=math.radians(degrees)/2
  return (math.sin(h),0.,0.,math.cos(h))
 def qmul(self,a,b):
  x,y,z,w=a;X,Y,Z,W=b
  return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,
          w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
 def world_matrices(self,doc,pose):
  a,b=(2*math.degrees(math.atan2(pose[i][0],pose[i][3])) for i in (0,1))
  upper=self.polarity*a;middle=upper+b
  v0=(0,1.,0)
  v1=(0,1.-.3*math.cos(math.radians(upper)),.3*math.sin(math.radians(upper)))
  v2=(0,v1[1]-.2*math.cos(math.radians(middle)),v1[2]+.2*math.sin(math.radians(middle)))
  def matrix(v):
   x,y,z=v;return (1.,0.,0.,x,0,1.,0.,y,0,0,1.,z,0,0,0,1.)
  return [matrix(x) for x in (v0,v1,v2)]
for polarity in (1,-1):
 base=FakeBase(polarity);pose={0:(0,0,0,1),1:(0,0,0,1)}
 names={'shoulder':0,'middle':1,'distal':2}
 x,_,world=m.drive_joint(base,{},pose,names,'shoulder','shoulder','middle',24.,38.)
 y,_,middle=m.drive_joint(base,{},pose,names,'middle','middle','distal',-35.,88.)
 assert abs(world-24)<.2 and abs(middle+35)<.2,(polarity,world,middle)
 assert x*polarity>0 and y*polarity!=0
print('PACKET_HASHES=PASS')
print('FRONT_ONLY_MUTATION_AND_STANCE_LOCKS=PASS')
print('SIGNED_WORLD_AXIS_SOLVER_BOTH_POLARITIES=PASS')
print('REAL_GLB_SKIN_AND_CLEARANCE_VALIDATION=DEFERRED_TO_PINNED_TERMUX_EXECUTION')

# Full verifier and candidate-generation paths, not just individual math helpers.
from regression import run_regressions
run_regressions(m)
print('FULL_CANDIDATE_AND_MID_SWING_VERIFIER_REGRESSION=PASS')

# Regression canary for the v0.6.9 float-shadow crash. Structural AST check
# complements the full make_candidate/verify path above.
import ast
v = next(n for n in ast.parse((root/'model.py').read_text()).body
         if isinstance(n,ast.FunctionDef) and n.name=='verify')
assert not any(isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store) and n.id=='s'
               for n in ast.walk(v)), 'VERIFIER_REINTRODUCED_COLLIDING_S_VARIABLE'
print('V069_FLOAT_SHADOW_REGRESSION=PASS')
