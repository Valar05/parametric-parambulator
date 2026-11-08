#!/usr/bin/env python3
"""v2.0.39 real 43-clip wrist/shield preflight; negative and provenance gates."""
import pathlib,sys,importlib.util,math,tempfile
import fix

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def run(path,core):
 for bad in ([float('nan')],[float('inf')],[-.02],[2.0]):
  try:fix.adaptive_key_grid(bad,0.86)
  except ValueError:pass
  else:raise AssertionError('INVALID_KEY_GRID_ACCEPTED')
 j,buf=core.read_glb(path)
 assert len(j['animations'])==43 and j['animations'][-1]['name']==fix.PREVIOUS
 act=j['animations'][-1];begin,end=core.range_times(j,buf,act)
 assert abs(begin)<.001 and .5<end<2.
 ids=core.name_ids(j);pa=core.parents(j)
 pose0=fix.snapshot(j,buf,act,0.,core)
 palm,_=fix.palm_local_offset(pose0,ids,pa,core)
 knuckle=fix.knuckle_axis_local(pose0,ids,pa,core)
 shield,reason=fix.identify_shield(j,buf,act,core,end)
 assert reason['strategy']=='verified_skin_weight_joint' and reason['purity']>=.98
 times=fix.adaptive_key_grid([end*i/240 for i in range(241)],end)
 scales,meta=fix.shield_scale_track(j,buf,act,shield,core,times,end,reason)
 assert len(scales)==len(times) and meta['newEndSeconds']>meta['onsetSeconds'] and meta['targetRatio']<0.4
 assert all(scales[i+1][k]<=scales[i][k]+1e-7 for i in range(len(scales)-1) for k in range(3))
 for t in (.24,.30,.42,.58,end-.05):
  pose=fix.snapshot(j,buf,act,t,core)
  right={i:{p:pose[ids[i]][p] for p in ('rotation','translation','scale')} for i in fix.RIGHT}
  desired=fix.corrected_wrist_world(pose,ids,pa,core,knuckle,t)
  result=fix.solve_left_wrist(pose,ids,pa,core,palm,desired)
  assert result['errorM']<=.0005
  for name,snapshot in right.items():
   assert pose[ids[name]]==snapshot,'RIGHT_ARM_PRETEST_REGRESSION'
 # Reject a mismatched binary before generating anything.
 try:fix.run(path,pathlib.Path(tempfile.gettempdir())/'nonexistent-output.glb',pathlib.Path(tempfile.gettempdir())/'nonexistent-report.json',core,expected_sha='0'*64)
 except ValueError as exc:assert 'EXACT_V236_SOURCE_SHA_INVALID' in str(exc)
 else:raise AssertionError('SOURCE_HASH_NEGATIVE_TEST_FAILED')
 print('V239_REAL_43_CLIP_WRIST_SHIELD_PREFLIGHT_PASS shieldNode='+str(shield)+' samples=5')


def shield_unlabelled_regression():
 class Core:
  @staticmethod
  def name_ids(j):return {n['name']:i for i,n in enumerate(j['nodes']) if 'name' in n}
  @staticmethod
  def raw_accessor(j,b,a):return b[a]
 js={'nodes':[{'name':'mixamorig:LeftWeapon.L'}, {'mesh':0,'skin':0}, {'mesh':1,'skin':0}],
     'skins':[{'joints':[0,3]}],
     'meshes':[{'primitives':[{'attributes':{'JOINTS_0':0,'WEIGHTS_0':1}}]},
               {'primitives':[{'attributes':{'JOINTS_0':2,'WEIGHTS_0':3}}]}]}
 js['nodes'].append({'name':'OtherBone'})
 buffers={0:[(0,0,0,0)]*10,1:[(1.,0.,0.,0.)]*10,
          2:[(1,1,1,1)]*10,3:[(.25,0.,0.,0.)]*10}
 act={'channels':[{'target':{'node':i,'path':'scale'}} for i in range(4)]}
 bone,proof=fix.identify_shield(js,buffers,act,Core,.86)
 assert bone==0 and proof['strategy']=='verified_skin_weight_joint' and proof['purity']==1
 # An unrelated surface influenced by the same bone MUST fail closed.
 buffers[2]=[(0,1,1,1)]*10
 buffers[3]=[(.25,0.,0.,0.)]*10
 try:fix.identify_shield(js,buffers,act,Core,.86)
 except ValueError as exc:assert 'SPILLS_ON_OTHER_MESHES' in str(exc)
 else:raise AssertionError('SHIELD_SPILL_NEGATIVE_TEST_FAILED')

if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('usage test.py REAL_43_GLTF CORE_SCRIPT')
 run(pathlib.Path(sys.argv[1]),load(pathlib.Path(sys.argv[2]),'v239_core'))
