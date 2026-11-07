#!/usr/bin/env python3
"""Exercise actual GLB success and adversarial fail cases. Test helper is real
published 2.0.23 GLB parser; synthetic fixture does NOT prove owner asset fixed.
"""
from __future__ import annotations
import hashlib,math,pathlib,struct,tempfile,copy,importlib.util,json,sys
sys.dont_write_bytecode=True
HOME=pathlib.Path(__file__).resolve().parent

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
fix=load(HOME/'fix.py','mudman_fix_v226');glb=load(HOME/'base_glb.py','mudman_base_v223')

def fixture(path,angle,parent_angle=0.,bad_axis="z"):
 arr=bytearray();views=[];access=[]
 def store(data,ctype,type_,count):
  nonlocal arr
  arr+=b'\0'*((-len(arr))%4);start=len(arr);arr+=data
  v=len(views);views.append({'buffer':0,'byteOffset':start,'byteLength':len(data)})
  a=len(access);access.append({'bufferView':v,'byteOffset':0,'componentType':ctype,'type':type_,'count':count})
  return a
 times=store(struct.pack('<5f',0.,.25,.5,.75,1.),5126,'SCALAR',5)
 q_ok=(0,0,0,1)
 sn=math.sin(math.radians(angle)/2);co=math.cos(math.radians(angle)/2)
 q_bad=(sn,0,0,co) if bad_axis=='x' else (0,sn,0,co) if bad_axis=='y' else (0,0,sn,co)
 outputs={}
 for name,q in [('normal',q_ok),('bad',q_bad)]:outputs[name]=store(struct.pack('<20f',*(q*5)),5126,'VEC4',5)
 vertices=[]
 for k in range(10):
  for z in range(4):
   for j in range(10):vertices.append(((j-4.5)*.035,k*.145+.05,(z-1.5)*.02))
 p=store(struct.pack('<'+str(len(vertices)*3)+'f',*(v for vert in vertices for v in vert)),5126,'VEC3',len(vertices))
 j=store(bytes(v for _ in vertices for v in (0,0,0,0)),5121,'VEC4',len(vertices))
 w=store(struct.pack('<'+str(len(vertices)*4)+'f',*(v for _ in vertices for v in (1.,0.,0.,0.))),5126,'VEC4',len(vertices))
 ib=store(struct.pack('<16f',*(float(i%5==0) for i in range(16))),5126,'MAT4',1)
 animations=[]
 for name in sorted(fix.EXPECTED):
  output=outputs['bad' if name=='HitHeadLeft' else 'normal']
  animations.append({'name':name,'samplers':[{'input':times,'output':output,'interpolation':'LINEAR'}],
   'channels':[{'sampler':0,'target':{'node':1,'path':'rotation'}}]})
 doc={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[0,3]}],
      'nodes':[{'name':'Mudman_Ground_Origin','translation':[0.,-.7,0.],'rotation':[math.sin(math.radians(parent_angle)/2),0.,0.,math.cos(math.radians(parent_angle)/2)],'children':[1]},
               {'name':'mixamorig:Hips','translation':[0.,.9,0.],'children':[2]},
               {'name':'mixamorig:Head','translation':[0.,1.,0.]},
               {'name':'geometry_0','mesh':0,'skin':0}],
      'skins':[{'joints':[1],'inverseBindMatrices':ib}],
      'meshes':[{'primitives':[{'attributes':{'POSITION':p,'JOINTS_0':j,'WEIGHTS_0':w},'material':0}]}],
      'materials':[{'name':'actual-clay-placeholder'}],
      'buffers':[{'byteLength':len(arr)}], 'bufferViews':views,'accessors':access,'animations':animations}
 glb.glb_save(doc,bytes(arr),path)
 return fix.digest(path)

with tempfile.TemporaryDirectory(prefix='mudman-v226-tests-') as d:
 d=pathlib.Path(d)
 src=d/'source.glb';out=d/'candidate.glb';proof=d/'proof.json';expected=fixture(src,90)
 result=fix.repair(src,out,proof,HOME/'base_glb.py',expected)
 assert result['status']=='WORLD_FRAME_REPAIR_CANDIDATE_UNAPPROVED',result
 assert result['chosen']['node']=='mixamorig:Hips',result
 assert result['otherClipsByteEquivalent']==22,result
 original,origbin=glb.glb_load(src);changed,newbin=glb.glb_load(out)
 assert changed['animations'][7 if False else [x['name'] for x in changed['animations']].index('HitHeadLeft')]['name']=='HitHeadLeft'
 assert newbin.startswith(origbin)
 assert fix.digest(out)==result['outputSHA256']
 assert result['chosen']['angleDegrees']>89 and result['chosen']['angleDegrees']<91
 print('PASS: REAL_GLB_PARSER_SYNTHETIC_90DEG_ROOT_REPAIR_22_CLIPS_PRESERVED')
 # Rotated-armature parent should not fool the world-space-to-local correction.
 for axis,parent in [('x',0),('z',35),('x',25)]:
  src2=d/('rotated_'+axis+str(parent)+'.glb');out2=d/('repaired_'+axis+str(parent)+'.glb');proof2=d/('rotated_'+axis+str(parent)+'.json')
  expected2=fixture(src2,90,parent,axis)
  result2=fix.repair(src2,out2,proof2,HOME/'base_glb.py',expected2)
  assert result2['status']=='WORLD_FRAME_REPAIR_CANDIDATE_UNAPPROVED' and out2.exists(),(axis,parent,result2.get('blocker'))
  assert result2['otherClipsUnchanged']
 print('PASS: X_AND_Z_TIPPING_WITH_ROTATED_PARENT_WORLD_FRAME')
 # Yaw turning is not a sideways collapse; it must never trigger this repair.
 yaw=d/'yaw.glb';yawout=d/'yawfixed.glb';yawproof=d/'yaw.json';yawsha=fixture(yaw,90,0,'y')
 try:fix.repair(yaw,yawout,yawproof,HOME/'base_glb.py',yawsha)
 except RuntimeError:pass
 else:raise AssertionError('YAW_ONLY_MISTAKEN_FOR_BODY_TIP')
 assert not yawout.exists()
 print('PASS: YAW_ONLY_NOT_TREATED_AS_90_DEG_SIDEWAYS_TIP')
 # Fail closed for ambiguous/everyday motion. Must not emit a mutated output file.
 for angle in (15,30,150):
  f=d/('incorrect_'+str(angle)+'.glb');p=d/('incorrect_'+str(angle)+'.json');out_bad=d/('bad_'+str(angle)+'.glb')
  expected=fixture(f,angle)
  try:fix.repair(f,out_bad,p,HOME/'base_glb.py',expected)
  except RuntimeError:pass
  else:raise AssertionError('UNSAFE_ROOT_CORRECTION_WAS_PUBLISHED_'+str(angle))
  assert not out_bad.exists() and json.loads(p.read_text())['status']=='BLOCKED_NO_GUESS'
 print('PASS: NEAR_MISS_15_40_145_DEGREES_BLOCKED_NO_MODEL')
 try:fix.repair(src,d/'again.glb',d/'again.json',HOME/'base_glb.py')
 except RuntimeError as err:assert 'EXACT_CURATED_SOURCE_GLB_SHA_INVALID' in str(err)
 else:raise AssertionError('SOURCE_SHA_NOT_ENFORCED')
 print('PASS: WRONG_SOURCE_SHA_BLOCKED')
 same=d/'same.glb';same.write_bytes(b'unrelated');tryreport=d/'same.json'
 try:fix.repair(src,same,tryreport,HOME/'base_glb.py',fix.digest(src))
 except RuntimeError as err:assert 'OUTPUT_PATH_ALREADY_EXISTS' in str(err)
 else:raise AssertionError('OUTPUT_COLLISION_NOT_BLOCKED')
 print('PASS: OUTPUT_COLLISION_NO_OVERWRITE')
print('V226_TESTS_OK')
