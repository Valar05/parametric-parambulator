#!/usr/bin/env python3
"""Real skinned fixture tests, source-history validation, solver math and failure gates.

Tests are off-device design evidence; production driver replays full preflight on the
REAL pinned v1.2.2 canonical GLB before any write/push.
"""
from __future__ import annotations
import copy, hashlib, importlib.util, json, math, os, pathlib, shutil, struct, sys, tempfile, types


def load(path):
 sys.dont_write_bytecode=True
 spec=importlib.util.spec_from_file_location('sample_solver',path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.M=m.read_tool();return m

def fixture(model,solver):
 m=solver.M
 g,b=m.load_glb(model)
 scene=copy.deepcopy(g)
 oldg=copy.deepcopy(g);oldb=bytearray(b)
 idle=next(a for a in oldg['animations'] if a['name']=='LionheartIdle_UNREVIEWED')
 names={n.get('name'):i for i,n in enumerate(oldg['nodes'])}
 times=[i/30. for i in range(21)]
 def add_acc(vals,typ):
  dim={'SCALAR':1,'VEC3':3,'VEC4':4}[typ]
  while len(oldb)%4:oldb.append(0)
  start=len(oldb);flat=[float(x) for row in vals for x in (row if isinstance(row,(tuple,list)) else (row,))]
  raw=struct.pack('<'+'f'*len(flat),*flat);oldb.extend(raw)
  view=len(oldg['bufferViews']);oldg['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(raw)})
  acc=len(oldg['accessors']);oldg['accessors'].append({'bufferView':view,'componentType':5126,'count':len(vals),'type':typ})
  return acc
 timeacc=add_acc(times,'SCALAR')
 wt=m.channels(oldg,oldb,idle)
 for name in ['ObsidiantiIdle']+['Lionheart_'+x for x in solver.ACTIONS]+['Ares_'+x for x in ['StepForward','StepBack','StepLeft','StepRight','StepForwardLeft','StepForwardRight','StepBackLeft','StepBackRight','AxeKick']]:
  clip={'name':name,'channels':[],'samplers':[]}
  for (node,path),(time,v) in wt.items():
   v0=list(v[0]);out=add_acc([v0 for i in times],{'rotation':'VEC4','translation':'VEC3'}[path]);s=len(clip['samplers'])
   clip['samplers'].append({'input':timeacc,'output':out,'interpolation':'LINEAR'});clip['channels'].append({'sampler':s,'target':{'node':node,'path':path}})
  if name.startswith('Lionheart_'):
   for weapon in ('mixamorig:LeftWeapon.L','mixamorig:RightWeapon.R'):
    node=names[weapon];a=add_acc([[0.01*i/20,0.,0.] for i in range(21)],'VEC3');s=len(clip['samplers'])
    clip['samplers'].append({'input':timeacc,'output':a,'interpolation':'LINEAR'});clip['channels'].append({'sampler':s,'target':{'node':node,'path':'translation'}})
  oldg['animations'].append(clip)
 assert len(oldg['animations'])==23
 historical=pathlib.Path(tempfile.mkstemp(suffix='.glb')[1]);historical.write_bytes(m.encode_glb(oldg,oldb))
 currentg=copy.deepcopy(oldg);currentb=bytearray(oldb)
 for a in currentg['animations']:
  if not a['name'].startswith('Lionheart_') or a['name']=='LionheartIdle_UNREVIEWED':continue
  a['channels']=[c for c in a['channels'] if not(c['target']['path']=='translation' and currentg['nodes'][c['target']['node']].get('name') in solver.WEAPONS)]
  ch,s=solver.find_track(a,currentg,names['mixamorig:Hips'],'rotation')
  src=list(m.Access(currentg,currentb).get(s['output']))
  rotated=[m.mul(list(q),m.qx(math.radians(9))) for q in src]
  s['output']=m.append_accessor(currentg,currentb,rotated,'VEC4')
 current=pathlib.Path(tempfile.mkstemp(suffix='.glb')[1]);current.write_bytes(m.encode_glb(currentg,currentb))
 idletoes={'mixamorig:LeftToeBase':{'worldPosition':[0.,.006,0.]},'mixamorig:RightToeBase':{'worldPosition':[0.,.006,0.]}}
 donor={'sourceKind':'lionheart','actionCount':11,'actions':{'Idle':{'frames':[{'time':0,'bones':idletoes}]}}}
 for name in solver.ACTIONS:
  frames=[]
  for i,t in enumerate(times):
   leftheight=.36 if name=='Kick' and 6<=i<=15 else .006
   backwards=-.004*i if name=='Heavy1' else 0.
   frames.append({'time':t,'bones':{'mixamorig:LeftToeBase':{'worldPosition':[.08,leftheight,.02]},'mixamorig:RightToeBase':{'worldPosition':[-.08,.006,.02+backwards]}}})
  donor['actions'][name]={'frames':frames}
 src=pathlib.Path(tempfile.mkstemp(suffix='.json')[1]);src.write_text(json.dumps(donor))
 return historical,current,src

def main():
 here=pathlib.Path(__file__).resolve().parents[1]
 modelpath=os.environ.get('OBSIDIANTI_TEST_SOURCE_GLB')
 if not modelpath or not pathlib.Path(modelpath).is_file():raise RuntimeError('EXPLICIT_3_CLIP_FIXTURE_GLB_REQUIRED: set OBSIDIANTI_TEST_SOURCE_GLB')
 solver=load(here/'campaigns/OBSIDIANTI_CONTACT_IK_SOLVE_v1.3.0.py');m=solver.M
 g,b=m.load_glb(modelpath);wit,skin,ibm=m.foot_witnesses(g,b)
 idle=next(x for x in g['animations'] if x['name']=='LionheartIdle_UNREVIEWED')
 tr=m.channels(g,b,idle)
 chains,parents=solver.joint_names(g)
 world=m.global_matrices(g,tr,0)
 for side,chain in chains.items():
  ankle=solver.matpos(world[chain[2]])
  q,report=solver.solve_two_bone(world,chain,parents,ankle)
  assert q is not None,(side,report)
  original=[m.sampled(*tr[(j,'rotation')],0,True) for j in chain]
  assert max(solver.quatang(a,b) for a,b in zip(q,original))<.03,(side,q,original)
  # No vertical correction to a perfectly matched ankle may introduce side travel.
  desired=solver.vadd(ankle,[0,.012,0]);q,info=solver.solve_two_bone(world,chain,parents,desired)
  assert q is not None,(side,info)
  newtr=solver.make_modified_track(tr,chain,q,0)
  ww=m.global_matrices(g,newtr,0);result=solver.matpos(ww[chain[2]])
  assert solver.norm(solver.vsub(result,desired))<.003,(side,result,desired)
  rr0=solver.matrix_rot(world[chain[2]]);rr1=solver.matrix_rot(ww[chain[2]])
  assert solver.quatang(rr0,rr1)<.1,(side,solver.quatang(rr0,rr1))
 print('TWO_LINK_IK_ON_REAL_SKINNED_MESH=PASS',flush=True)
 historical,current,src=fixture(modelpath,solver)
 try:
  solver.CURRENT_SHA=solver.sha(current);solver.ORIGINAL_SHA=solver.sha(historical)
  with tempfile.TemporaryDirectory() as tmp:
   out=pathlib.Path(tmp)/'report.json'
   info=solver.solve_model(current,historical,src,out,True)
   assert solver.sha(current)==solver.CURRENT_SHA
   assert len(info['perClip'])==10
   print('DRY_RUN_CANONICAL_BYTE_IDENTICAL=PASS',flush=True)
   info=solver.solve_model(current,historical,src,out,False)
   assert solver.sha(current)==info['candidateByteSha256']
   newg,newb=m.load_glb(current);oldg,oldb=m.load_glb(historical)
   assert len(newg['animations'])==23
   for a,ab in zip(newg['animations'],oldg['animations']):
    if a['name'].startswith('Ares_') or a['name'] in ('Running','Walking','ObsidiantiIdle','LionheartIdle_UNREVIEWED'):assert a==ab,a['name']
   for a in newg['animations']:
    if not a['name'].startswith('Lionheart_') or a['name']=='LionheartIdle_UNREVIEWED':continue
    assert all(not(c['target']['path']=='translation' and newg['nodes'][c['target']['node']].get('name') in solver.WEAPONS) for c in a['channels'])
   kick=next(x for x in newg['animations'] if x['name']=='Lionheart_Kick')
   oldkick=next(x for x in oldg['animations'] if x['name']=='Lionheart_Kick')
   names={n.get('name'):i for i,n in enumerate(newg['nodes'])}
   left=names['mixamorig:LeftUpLeg']
   orig=m.channels(oldg,oldb,oldkick)[left,'rotation'][1][10]
   got=m.channels(newg,newb,kick)[left,'rotation'][1][10]
   assert solver.quatang(orig,got)<.02,('SOURCE_AIRBORNE_LEG_WAS_GROUNDED',orig,got)
   print('SOURCE_AIRBORNE_FOOT_PRESERVED=PASS',flush=True)
   print('ALL_23_ANIMATION_INVARIANTS=PASS',flush=True)
   try:solver.solve_model(current,historical,src,out,False)
   except RuntimeError as e:assert 'CANONICAL_UNEXPECTED_SHA' in str(e)
   else:raise AssertionError('Wrong SHA silently accepted')
   print('UNEXPECTED_CANONICAL_HASH_REJECTED=PASS',flush=True)
 finally:
  historical.unlink(missing_ok=True);current.unlink(missing_ok=True);src.unlink(missing_ok=True)
 print('TEST_SUITE=PASS')
if __name__=='__main__':main()
