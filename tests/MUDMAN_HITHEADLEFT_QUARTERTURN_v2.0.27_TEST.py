#!/usr/bin/env python3
"""Preflight pure-math and failure injection; real GLB full proof runs only on Termux."""
from __future__ import annotations
import importlib.util,json,math,pathlib,sys,tempfile
P=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('quarter',P/'fix.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
assert len(q.EXPECTED)==23
assert q.NORMAL_AXIS==(-1.,0.,0.)
assert q.MEASURED_AXIS[0]<-.95
class F:
 @staticmethod
 def axis_angle(axis,angle):
  d=math.sqrt(sum(x*x for x in axis));return (*[x/d*math.sin(angle/2) for x in axis],math.cos(angle/2))
 @staticmethod
 def degrees(a,b):
  c=abs(sum(x*y for x,y in zip(a,b)));return math.degrees(2*math.acos(min(1,c)))
 @staticmethod
 def mul(a,b):
  x,y,z,w=a;u,v,t,s=b
  return (w*u+x*s+y*t-z*v,w*v-x*t+y*s+z*u,w*t+x*v-y*u+z*s,w*s-x*u-y*v-z*t)
for axis in (q.NORMAL_AXIS,q.MEASURED_AXIS):
 quat=F.axis_angle(axis,math.pi/2)
 assert abs(F.degrees(quat,(0,0,0,1))-90)<1e-9
 a=F.mul(quat,(0,0,0,1));assert abs(F.degrees(a,(0,0,0,1))-90)<1e-9
 # Verify a local X quarter turn changes the up vector, never silently produces 62.38°.
assert abs(F.degrees(F.axis_angle(q.NORMAL_AXIS,math.pi/2),(0,0,0,1))-62.38362)>25
try:q.require(False,'EXPECTED_REJECTION')
except RuntimeError as e:assert 'EXPECTED_REJECTION' in str(e)
else:raise AssertionError('missing rejection')
print('PASS_QUARTER_TURN=90.000000_DEGREES')
print('PASS_X_AND_MEASURED_AXIS_VECTORS')
print('PASS_NOT_REJECTED_62_38_DEGREES')
print('PASS_INVALID_INPUT_REJECTS')

# Exercise the COMPLETE apply_one path with a structurally representative
# 23-clip GLB adapter and injected source/hash and output-collision failures.
import hashlib,copy
class FakeG:
 def glb_load(self,src):
  raw=pathlib.Path(src).read_bytes()
  if raw==b'BASE':
   js={'nodes':[{'name':'mixamorig:Hips'},{'name':'mixamorig:Head'}],
       'animations':[{'name':n,'samplers':[{'input':'times','output':'source'}],
                       'channels':[{'target':{'node':0,'path':'rotation'},'sampler':0}]} if n=='HitHeadLeft'
                     else {'name':n,'samplers':[],'channels':[]} for n in sorted(q.EXPECTED)],
       'accessor_data':{'times':[[i/30.] for i in range(31)],'source':[[0,0,0,1] for _ in range(31)]}}
   return js,b'BASE'
  j=json.loads(raw.decode());return j['js'],bytes.fromhex(j['bin'])
 def accessor(self,js,data,key):return js['accessor_data'][key]
 def clip_bytes(self,js,data,clip):return json.dumps(clip,sort_keys=True).encode()
 def sampled_skinned_bounds(self,js,data,clip,t):return {'witnessVertices':4474,'minY':0.,'maxY':1.6}
 def glb_save(self,js,data,output):pathlib.Path(output).write_text(json.dumps({'js':js,'bin':data.hex()},sort_keys=True))
class FakePrior(F):
 @staticmethod
 def load_tools(path):return FakeG()
 @staticmethod
 def rig_chain(js):return 0,1,[0]
 @staticmethod
 def rot_channel(g,js,data,clip,node):
  r=[ch for ch in clip['channels'] if ch['target'].get('node')==node and ch['target'].get('path')=='rotation']
  return r[0] if r else None
 @staticmethod
 def write_track(g,js,data,clip,node,quat):
  c=FakePrior.rot_channel(g,js,data,clip,node)
  old=clip['samplers'][c['sampler']]['output'];oldvalues=g.accessor(js,data,old)
  js['accessor_data']['rot_new']=[list(F.mul(quat,v)) for v in oldvalues]
  clip['samplers'][c['sampler']]['output']='rot_new'
  return data+b'NEXT',{'newKeyCount':len(oldvalues),'oldAccessor':old,'newAccessor':'rot_new'}
 @staticmethod
 def clip_range(g,data,clip):return (0.,1.)
 @staticmethod
 def body_vector(g,js,data,clip,t,hips,head):return (0.,1.,0.)
 @staticmethod
 def dot(a,b):return sum(x*y for x,y in zip(a,b))
with tempfile.TemporaryDirectory() as temp:
 base=pathlib.Path(temp)/'baseline.glb';base.write_bytes(b'BASE')
 for label,axis in [('x',q.NORMAL_AXIS),('axis',q.MEASURED_AXIS)]:
  output=pathlib.Path(temp)/(label+'.glb')
  proof=q.apply_one(base,output,'unused',FakePrior,axis,label,hashlib.sha256(b'BASE').hexdigest())
  assert proof['rotationDegrees']==90 and proof['other22AnimationsByteIdentical']
  assert proof['rotationKeys']==31 and proof['candidateSHA256']==hashlib.sha256(output.read_bytes()).hexdigest()
  try:q.apply_one(base,output,'unused',FakePrior,axis,label,hashlib.sha256(b'BASE').hexdigest())
  except RuntimeError as e:assert 'OUTPUT_COLLISION' in str(e)
  else:raise AssertionError('output collision accepted')
  try:q.apply_one(base,pathlib.Path(temp)/'badsha.glb','unused',FakePrior,axis,label,'0'*64)
  except RuntimeError as e:assert 'EXACT_ORIGINAL' in str(e)
  else:raise AssertionError('wrong source hash accepted')
print('PASS_COMPLETE_23_CLIP_GLB_APPLY_AND_READBACK_STUB_90X_AND_90FORENSIC_AXIS')
print('PASS_NON_TARGET_22_CLIP_PRESERVATION')
print('PASS_HASH_REJECTION_AND_OUTPUT_COLLISION')
