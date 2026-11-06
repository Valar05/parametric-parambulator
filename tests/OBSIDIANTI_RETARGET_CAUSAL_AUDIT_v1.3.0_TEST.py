#!/usr/bin/env python3
"""Disposable successful-path and failure-injection contract test. NOT real physics proof."""
from __future__ import annotations
import hashlib,importlib.util,json,math,pathlib,tempfile,sys,types
HERE=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('audit_module',HERE/'analyze.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
MOVES=audit.MOVES;SIDES=audit.SIDES
names=[audit.HIP]+[f'mixamorig:{s}{x}' for s in SIDES for x in audit.BONENAMES]

def make_fake_modules(root):
 glb=root/'fake-glb.bin';glb.write_bytes(b'FAKE_TEST_ONLY_NOT_ACTUAL_MODEL')
 donor={'sourceKind':'lionheart','actions':{}}
 for act in ('Idle',*MOVES):
  frames=[]
  for i in range(7):
   t=i/60.;dy=.1*i/6.;bones={}
   for s in SIDES:
    x=-.2 if s=='Left' else .2
    for part,y in (('UpLeg',.9),('Leg',.55),('Foot',.2),('ToeBase',.02)):
     bones[f'mixamorig:{s}{part}']={'worldPosition':[x,y,0],'restWorldQuat':[0,0,0,1],'localDeltaQuat':[0,0,0,1]}
   bones[audit.HIP]={'worldPosition':[0,1.+dy,0],'restWorldQuat':[0,0,0,1],'localDeltaQuat':[0,0,0,1]}
   frames.append({'time':t,'sourceFrame':i/2,'bones':bones})
  donor['actions'][act]={'frames':frames}
 donorpath=root/'donor.json';donorpath.write_text(json.dumps(donor))
 evaluator=root/'evaluator.py'
 evaluator.write_text('''import math
NAMES=['mixamorig:Hips']+[f'mixamorig:{s}{p}' for s in ('Left','Right') for p in ('UpLeg','Leg','Foot','ToeBase')]

def load_glb(path):
 g={'nodes':[{'name':n} for n in NAMES], 'animations':[{'name':'Lionheart_'+x} for x in ('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')],'skins':[{}]}
 return g,bytearray(b'X')
def channels(g,b,a):
 nodes={n['name']:i for i,n in enumerate(g['nodes'])};tt=[0.,.1]
 out={(nodes['mixamorig:Hips'],'translation'):(tt,[[0,1,0],[0,1.1,0]]),(nodes['mixamorig:Hips'],'rotation'):(tt,[[0,0,0,1],[0,0,0,1]])}
 for s in ('Left','Right'):
  for p in ('UpLeg','Leg','Foot'):
   out[nodes[f'mixamorig:{s}{p}'],'rotation']=(tt,[[0,0,0,1],[0,0,.1,math.sqrt(.99)]])
 return out

def sampled(t,v,time,rotation=False):
 if time<=t[0]:return v[0]
 if time>=t[-1]:return v[-1]
 q=(time-t[0])/(t[-1]-t[0]);return [(1-q)*x+q*y for x,y in zip(v[0],v[-1])]
def mat(pos):return [1,0,0,pos[0],0,1,0,pos[1],0,0,1,pos[2],0,0,0,1]
def global_matrices(g,tracks,time):
 names={n['name']:i for i,n in enumerate(g['nodes'])};ret={}
 hip_id=names['mixamorig:Hips'];hp=sampled(*tracks[hip_id,'translation'],time)
 ret[hip_id]=mat(hp)
 for s in ('Left','Right'):
  x=-.2 if s=='Left' else .2
  rotations=[sampled(*tracks[names[f'mixamorig:{s}{part}'],'rotation'],time,True)[2] for part in ('UpLeg','Leg','Foot')]
  dy=3*rotations[0]+2*rotations[1]
  for part,offset in [('UpLeg',-.1),('Leg',-.45),('Foot',-.8),('ToeBase',-.98)]:
   ret[names[f'mixamorig:{s}{part}']]=mat([x,hp[1]+offset+dy,0])
 return ret
def foot_witnesses(g,b):return ({'Left':[(0,0,0)],'Right':[(0,0,0)]},{},[])
def skin_foot_points(witness,skin,ibm,world):return {'Left':[[0,0.01,0],[0,0.02,0]],'Right':[[0,0.013,0],[0,0.03,0]]}
def floor_height(points):return min(x[1] for x in points)
''')
 importer=root/'importer.py'
 importer.write_text('''def approved_idle(g,b):return ({i:[0,0,0,1] for i in range(len(g['nodes']))},{})
def ref_quats(g):return {i:[0,0,0,1] for i in range(len(g['nodes']))}
def rebase_source_pose(source,base,g,rest,approved,frames):return {i:[0,0,0,1] for i in range(len(g['nodes']))}
''')
 return glb,donorpath,evaluator,importer

def run_test():
 with tempfile.TemporaryDirectory(prefix='obs-130-fake-fixtures-') as d:
  root=pathlib.Path(d);glb,donor,evalmod,importer=make_fake_modules(root)
  fake_args=types.SimpleNamespace(model=str(glb),donor=str(donor),expected_model_sha=audit.sha(glb),
    expected_donor_samples_sha=audit.sha(donor),blend_sha='FAKE-DONOR-TEST-ONLY',evaluator=str(evalmod),
    importer=str(importer),output=str(root/'result.json'))
  audit.audit(fake_args)
  result=json.loads((root/'result.json').read_text())
  assert len(result['clips'])==10
  assert result['invariants']['stationarySourcePairContradictions']==[] # fake left/right identical motion
  assert all(c['sampleCount']==7 for c in result['clips'].values())
  assert all(c['legs']['Left']['footVerticalResidual_m']['n']==7 for c in result['clips'].values())
  fake_args.expected_model_sha='wrong'
  try:audit.audit(fake_args)
  except RuntimeError as e:assert 'WRONG_HISTORICAL_MODEL_HASH' in str(e)
  else:raise AssertionError('WRONG_SHA_WAS_ACCEPTED')
  fake_args.expected_model_sha=audit.sha(glb)
  j=json.loads(donor.read_text());del j['actions']['Cast'];donor.write_text(json.dumps(j));fake_args.expected_donor_samples_sha=audit.sha(donor)
  try:audit.audit(fake_args)
  except RuntimeError as e:assert 'WRONG_DONOR_KIND_OR_CLIP_SET' in str(e)
  else:raise AssertionError('MISSING_CLIP_WAS_ACCEPTED')
 print('HOST_FIXTURE_SUCCESS_AND_FAILURE_PATHS_PASS')
if __name__=='__main__':run_test()
