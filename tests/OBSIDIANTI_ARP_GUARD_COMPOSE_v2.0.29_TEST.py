#!/usr/bin/env python3
"""Physical-schema fixture from a genuine owner-provided v2.0.14 GLB, plus fault injection.
Not evidence that v2.0.16 or canonical were processed. Source execution occurs on Termux.
"""
import argparse,copy,hashlib,json,pathlib,struct,tempfile
import compose as c

def fixture(real,root):
 js,data=c.read_glb(real);js=copy.deepcopy(js); a={x['name']:x for x in js['animations']}
 # The real 2-key v2.0.14 step exports were defective; for a structural composition
 # fixture use a real multi-key keyed retarget from the same source rig.
 parent=a['Lionheart_Heavy1']; require_multi=c.get_channel(parent,c.name_ids(js)[c.HIPS],'rotation')
 assert len(c.raw_accessor(js,data,parent['samplers'][require_multi['sampler']]['input']))>=10
 for step in c.STEPS:
  idx=next(i for i,x in enumerate(js['animations']) if x['name']=='Ares_'+step)
  js['animations'][idx]=copy.deepcopy(parent);js['animations'][idx]['name']='Ares_'+step
 # Three neutral named untouched actions to reach 23 (the production v2.0.16 is already 23).
 for k in range(23-len(js['animations'])):
  act=copy.deepcopy(parent);act['name']='FIXTURE_OTHER_'+str(k);js['animations'].append(act)
 assert len(js['animations'])==23
 src=copy.deepcopy(js)
 app=c.Appender(src,data)
 nids=c.name_ids(js);up=c.descendants(js,nids[c.SPINE]);hip=nids[c.HIPS]
 t0=0.;t1=3.
 guard={'name':c.GUARD,'channels':[],'samplers':[]}
 for i in range(len(js['nodes'])):
  name=js['nodes'][i].get('name')
  if not name:continue
  for path in ('translation','rotation','scale'):
   val=c.at_time(js,data,parent,i,path,0.)
   val=c.normq(val) if path=='rotation' else tuple(val)
   app.add(guard,i,path,[0.,.03],[val,val])
 app.js['animations'].append(guard)
 idle={'name':c.AUTHORED,'channels':[],'samplers':[]}
 for i in range(len(js['nodes'])):
  if not js['nodes'][i].get('name'):continue
  for path in ('translation','rotation','scale'):
   val=c.at_time(js,data,parent,i,path,0.)
   val=c.normq(val) if path=='rotation' else tuple(val)
   app.add(idle,i,path,[t0,t1],[val,val])
 app.js['animations'].append(idle)
 original=root/'source.glb';target=root/'arp.glb'
 c.glb_save(app.js,bytes(app.bin),original);c.glb_save(js,data,target)
 return original,target

def main():
 p=argparse.ArgumentParser();p.add_argument('--real',required=True);a=p.parse_args()
 f=pathlib.Path(a.real);assert f.exists()
 with tempfile.TemporaryDirectory(prefix='obs-guard-tests-') as d:
  root=pathlib.Path(d);source,target=fixture(f,root)
  o=root/'output.glb';proof=root/'proof.json'
  r=c.compose(source,target,o,proof,expected_source=c.digest(source),expected_target=c.digest(target))
  assert len(r['steps'])==8 and len(r['newActionNames'])==10
  assert r['existingAnimationsPreserved']==23 and r['originalModelAndMaterialsPreserved']
  assert max(x['maxGuardWorldRotationErrorDegrees'] for x in r['steps'])<.45
  js,_=c.read_glb(o);assert len(js['animations'])==33
  print('PASS: actual 78-node owner GLB topology, eight keyed limb-motion steps, guard correction, 33 clips, immutable geometry')
  # Unsupported source binary changes fail closed.
  try:c.compose(source,target,root/'fail.glb',root/'fail.json',expected_source='0'*64,expected_target=c.digest(target))
  except ValueError as exc:assert 'SHA_MISMATCH' in str(exc)
  else:raise AssertionError('hash corruption did not block')
  print('PASS: source hash mismatch blocked')
  try:c.compose(source,target,o,root/'collision.json',expected_source=c.digest(source),expected_target=c.digest(target))
  except ValueError as exc:assert 'OUTPUT_COLLISION' in str(exc)
  else:raise AssertionError('collision not blocked')
  print('PASS: output collision protected')
  # Remove the original authored idle and verify no invented replacement.
  source_js,bb=c.read_glb(source);source_js['animations']=[an for an in source_js['animations'] if an['name']!=c.AUTHORED]
  missing=root/'no_idle.glb';c.glb_save(source_js,bb,missing)
  try:c.compose(missing,target,root/'missing_result.glb',root/'missing_proof.json',expected_source=c.digest(missing),expected_target=c.digest(target))
  except ValueError as exc:assert 'GUARD_NOT_FOUND' in str(exc) or 'IDLE_OR_LIONHEART_GUARD_NOT_FOUND' in str(exc)
  else:raise AssertionError('missing idle not blocked')
  print('PASS: missing historical idle blocked')
 print('V229_COMPOSE_TESTS_OK')
if __name__=='__main__':main()
