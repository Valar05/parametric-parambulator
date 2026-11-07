#!/usr/bin/env python3
"""Curation-only glTF patch: exact original Meshy baseColor texture, foot-ground model root, Godot-named action subset.
All source glTF mesh, skin, inverse bind, and retained sampler/accessor bytes are immutable.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,math,os,pathlib,struct,sys,zipfile,bisect
V='MUDMAN_GODOT_CURATED_v2.0.23'
OLD_GLB='396e9cf024846ba9e8c5159a9b8660b21a296a73a6e656d4c347dc86780079d6'
OWNER_ZIP='fbcb592ac941dbc34ecade66b044b551f5bd55bf5855be50d8af5caba0514f79'
OWNER_PNG='f1a6089742844a6a3b0a4b7c93ce6ca80faf126adf92ec135bb7aa26a478e886'
# Source animation names verified against v2.0.22 ACTION_RESULTS.json;
# labels and gameplay roles verified against SecurityTitan.tscn/security_titan.json.
# The original Ares blend has no action named Idle-Cross: alias from moving Idle OBCross is explicitly documented.
MAP={
'Mudman_Idle__OBCross':'Idle-Cross',
'Mudman_Run':'Run',
'Mudman_StepForward':'StepForward',
'Mudman_StepBack':'StepBack',
'Mudman_StepLeft':'StepLeft',
'Mudman_StepRight':'StepRight',
'Mudman_StepForwardLeft':'StepForwardLeft',
'Mudman_StepForwardRight':'StepForwardRight',
'Mudman_StepBackLeft':'StepBackLeft',
'Mudman_StepBackRight':'StepBackRight',
'Mudman_Jab-Enemy__OBCross':'Jab-Enemy',
'Mudman_Cross-Enemy':'Cross-Enemy',
'Mudman_HitHeadLeft':'HitHeadLeft',
'Mudman_HitHeadRightBig':'HitHeadRightBig',
'Mudman_BackImpact__OBHitHeadLeft':'BackImpact',
'Mudman_KnockedBack':'KnockedBack',
'Mudman_ProneBack':'ProneBack',
'Mudman_ProneBackDamage':'ProneBackDamage',
'Mudman_ProneBackStandUp':'ProneBackStandUp',
'Mudman_ProneFront__OBHitHeadLeft':'ProneFront',
'Mudman_ProneFrontDamage__OBHitHeadLeft':'ProneFrontDamage',
'Mudman_StandUp__OBHitHeadLeft':'StandUp',
'Mudman_Death':'Death',
}
assert len(MAP)==23 and len(set(MAP.values()))==23

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as stream:
  for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def require(cond,msg):
 if not cond:raise RuntimeError(msg)

def glb_load(path):
 b=pathlib.Path(path).read_bytes();require(len(b)>=32 and b[:4]==b'glTF','SOURCE_NOT_GLB')
 magic,version,total=struct.unpack_from('<4sII',b,0)
 require(magic==b'glTF' and version==2 and total==len(b),'GLB_HEADER_INVALID')
 jlen,jtyp=struct.unpack_from('<I4s',b,12);require(jtyp==b'JSON' and jlen>0,'GLB_JSON_CHUNK_INVALID')
 js=json.loads(b[20:20+jlen]);off=20+jlen
 blen,btyp=struct.unpack_from('<I4s',b,off)
 require(btyp==b'BIN\x00' and off+8+blen==len(b),'GLB_BIN_CHUNK_INVALID')
 data=b[off+8:];require(len(js.get('buffers',[]))==1,'ONE_GLB_BUFFER_REQUIRED')
 return js,data

def glb_save(js,data,path):
 bjson=json.dumps(js,ensure_ascii=False,separators=(',',':')).encode('utf-8')
 bjson+=b' '*((-len(bjson))%4);data+=b'\0'*((-len(data))%4)
 js['buffers'][0]['byteLength']=len(data)
 bjson=json.dumps(js,ensure_ascii=False,separators=(',',':')).encode('utf-8')
 bjson+=b' '*((-len(bjson))%4)
 raw=struct.pack('<4sII',b'glTF',2,12+8+len(bjson)+8+len(data))
 raw+=struct.pack('<I4s',len(bjson),b'JSON')+bjson+struct.pack('<I4s',len(data),b'BIN\0')+data
 p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 require(not p.exists(),'OUTPUT_COLLISION_'+str(p))
 p.write_bytes(raw)
 return len(raw)

FORMATS={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}
WIDTH={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def accessor(js,data,index):
 a=js['accessors'][index];require('sparse' not in a and 'bufferView' in a,'SPARSE_OR_UNBUFFERED_ACCESSOR_UNSUPPORTED')
 v=js['bufferViews'][a['bufferView']];require(v.get('buffer',0)==0,'NONZERO_BUFFER')
 code,size=FORMATS[a['componentType']];width=WIDTH[a['type']]
 unit=size*width;stride=v.get('byteStride',unit)
 offset=v.get('byteOffset',0)+a.get('byteOffset',0)
 count=a['count'];require(stride>=unit and offset+(count-1)*stride+unit<=len(data),'ACCESSOR_OVERRUN')
 unpack=struct.Struct('<'+code*width)
 out=[unpack.unpack_from(data,offset+i*stride) for i in range(count)]
 if a.get('normalized'):
  if a['componentType']==5121:out=[tuple(x/255 for x in row) for row in out]
  elif a['componentType']==5123:out=[tuple(x/65535 for x in row) for row in out]
  else:raise RuntimeError('UNSUPPORTED_NORMALIZED_FORMAT')
 return out

# Column-major 4x4, glTF (TRS transforms, skins and inverse bind).
I=(1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.)
def mul(a,b):return tuple(sum(a[4*k+r]*b[4*c+k] for k in range(4)) for c in range(4) for r in range(4))
def pt(m,v):
 x,y,z=v[:3]
 return (m[0]*x+m[4]*y+m[8]*z+m[12],m[1]*x+m[5]*y+m[9]*z+m[13],m[2]*x+m[6]*y+m[10]*z+m[14])
def qnorm(q):
 d=math.sqrt(sum(x*x for x in q));require(d>0 and math.isfinite(d),'QUATERNION_INVALID')
 return [x/d for x in q]
def mtrs(t,q,s):
 x,y,z,w=qnorm(q);sx,sy,sz=s
 return ((1-2*(y*y+z*z))*sx,2*(x*y+z*w)*sx,2*(x*z-y*w)*sx,0.,
   2*(x*y-z*w)*sy,(1-2*(x*x+z*z))*sy,2*(y*z+x*w)*sy,0.,
   2*(x*z+y*w)*sz,2*(y*z-x*w)*sz,(1-2*(x*x+y*y))*sz,0.,
   float(t[0]),float(t[1]),float(t[2]),1.)
def slerp(a,b,t):
 d=sum(x*y for x,y in zip(a,b))
 if d<0:b=tuple(-x for x in b);d=-d
 if d>.9995:return qnorm([(1-t)*x+t*y for x,y in zip(a,b)])
 d=max(-1.,min(1.,d));ang=math.acos(d);sn=math.sin(ang)
 return [(math.sin((1-t)*ang)*x+math.sin(t*ang)*y)/sn for x,y in zip(a,b)]

def pose(js,data,animation,timepoint):
 overrides={}
 for ch in animation['channels']:
  target=ch['target'];idx=target['node'];path=target['path']
  if path not in ('translation','rotation','scale'):continue
  sample=animation['samplers'][ch['sampler']]
  times=[row[0] for row in accessor(js,data,sample['input'])]
  values=accessor(js,data,sample['output'])
  require(len(times)>=1 and len(times)==len(values),'BAD_ANIMATION_SAMPLER')
  i=max(0,min(len(times)-2,bisect.bisect_right(times,timepoint)-1)) if len(times)>1 else 0
  alpha=(timepoint-times[i])/(times[i+1]-times[i]) if len(times)>1 and times[i+1]>times[i] else 0.
  alpha=max(0.,min(1.,alpha))
  interp=sample.get('interpolation','LINEAR')
  require(interp in ('LINEAR','STEP'),'UNSUPPORTED_INTERPOLATION_'+interp)
  if len(times)==1 or timepoint<=times[0]:val=values[0]
  elif timepoint>=times[-1]:val=values[-1]
  elif interp=='STEP':val=values[i]
  elif path=='rotation':val=slerp(values[i],values[i+1],alpha)
  else:val=[a*(1-alpha)+b*alpha for a,b in zip(values[i],values[i+1])]
  overrides.setdefault(idx,{})[path]=val
 nodes=js['nodes'];parents={}
 for i,n in enumerate(nodes):
  for ch in n.get('children',[]):require(ch not in parents,'MULTIPLE_NODE_PARENTS');parents[ch]=i
 local=[]
 for i,n in enumerate(nodes):
  custom=overrides.get(i,{})
  if 'matrix' in n:
   require(not custom,'ANIMATED_NODE_WITH_MATRIX_UNSUPPORTED')
   local.append(n['matrix'])
  else:local.append(mtrs(custom.get('translation',n.get('translation',(0,0,0))),custom.get('rotation',n.get('rotation',(0,0,0,1))),custom.get('scale',n.get('scale',(1,1,1)))))
 world={}
 def calc(i):
  if i in world:return world[i]
  world[i]=mul(calc(parents[i]),local[i]) if i in parents else local[i]
  return world[i]
 for i in range(len(nodes)):calc(i)
 return world

def sampled_skinned_bounds(js,data,action,t,cap=100000):
 world=pose(js,data,action,t)
 ymin=math.inf;ymax=-math.inf;witness=0;details=[]
 for ni,node in enumerate(js['nodes']):
  if 'mesh' not in node or 'skin' not in node:continue
  skin=js['skins'][node['skin']]
  ib=accessor(js,data,skin['inverseBindMatrices']) if 'inverseBindMatrices' in skin else [I]*len(skin['joints'])
  require(len(ib)==len(skin['joints']),'INVALID_SKIN_IBM')
  boneworld=[mul(world[j],ib[k]) for k,j in enumerate(skin['joints'])]
  for prim in js['meshes'][node['mesh']]['primitives']:
   attr=prim['attributes']
   require('POSITION' in attr and 'JOINTS_0' in attr and 'WEIGHTS_0' in attr,'SKINNED_MESH_WITHOUT_JOINTS_OR_WEIGHTS')
   positions=accessor(js,data,attr['POSITION']);joints=accessor(js,data,attr['JOINTS_0']);weights=accessor(js,data,attr['WEIGHTS_0'])
   require(len(positions)==len(joints)==len(weights),'SKIN_VERTEX_STREAM_LENGTH_MISMATCH')
   # Deterministic bounded witness sampling. Include first, last, and stride samples.
   step=max(1,len(positions)//cap);samples=list(range(0,len(positions),step))
   if len(positions)-1 not in samples:samples.append(len(positions)-1)
   for v in samples:
    ys=0.;ws=0.
    for j,w in zip(joints[v],weights[v]):
     if w<0.0000001:continue
     require(0<=int(j)<len(boneworld),'INVALID_SKIN_JOINT')
     yy=pt(boneworld[int(j)],positions[v])[1];ys+=float(w)*yy;ws+=float(w)
    if ws<0.5:continue
    y=ys/ws
    require(math.isfinite(y),'NONFINITE_SKINNED_VERTEX')
    ymin=min(ymin,y);ymax=max(ymax,y);witness+=1
   details.append({'mesh':js['meshes'][node['mesh']].get('name',str(node['mesh'])),'sampledVertices':len(samples),'totalVertices':len(positions),'maxSampleStride':step})
 require(witness>=50 and math.isfinite(ymin) and ymax>ymin,'SKINNED_GROUND_MEASUREMENT_MISSING')
 return {'minY':ymin,'maxY':ymax,'witnessVertices':witness,'meshDetails':details}

def clip_bytes(js,data,an):
 hashes=[]
 for sampler in an['samplers']:
  for key in ('input','output'):
   access=js['accessors'][sampler[key]];bv=js['bufferViews'][access['bufferView']]
   start=bv.get('byteOffset',0);end=start+bv['byteLength'];require(end<=len(data),'CLIP_BUFFER_OVERRUN')
   hashes.append(sha_bytes(data[start:end]))
 return hashes

def apply(src,zipfile_path,dest,report):
 require(sha(src)==OLD_GLB,'BASE_REVIEW_GLB_SHA_CHANGED')
 require(sha(zipfile_path)==OWNER_ZIP,'OWNER_MESHY_ZIP_SHA_CHANGED')
 with zipfile.ZipFile(zipfile_path) as z:
  filenames=[p for p in z.namelist() if p.lower().endswith('.png') and not p.startswith('__MACOSX')]
  require(len(filenames)==1,'ORIGINAL_MESHY_PNG_NOT_UNIQUE')
  texture=z.read(filenames[0])
 require(sha_bytes(texture)==OWNER_PNG and texture.startswith(b'\x89PNG\r\n\x1a\n'),'ORIGINAL_MESHY_PNG_SHA_OR_SIGNATURE_INVALID')
 width,height=struct.unpack_from('>II',texture,16);require((width,height)==(2048,2048),'MESHY_UV_ATLAS_DIMENSIONS_CHANGED')
 js,data=glb_load(src)
 require(len(js.get('animations',[]))==77,'BASE_77_ACTION_INVENTORY_CHANGED')
 before=copy.deepcopy(js)
 names=[a['name'] for a in js['animations']]
 require(len(names)==len(set(names)) and all(n in names for n in MAP),'REQUIRED_GODOT_ACTION_MISSING')
 original_animation_lookup={a['name']:a for a in js['animations']}
 idle=original_animation_lookup['Mudman_Idle__OBCross']
 t0=min(row[0][0] for row in (accessor(js,data,s['input']) for s in idle['samplers']) if row)
 ground=sampled_skinned_bounds(js,data,idle,t0)
 delta=-ground['minY'];model_h=ground['maxY']-ground['minY']
 require(model_h>0.1 and abs(delta)<(model_h*7),'GROUND_CORRECTION_OUTSIDE_MODEL_SCALE')
 # Preserve every animated bone, root channel, skin, and keyframe. Add a single
 # unanimated scene parent correcting the MODEL'S world vertical placement.
 scene_idx=js.get('scene',0);scene=js['scenes'][scene_idx]
 roots=list(scene['nodes']);require(roots,'SCENE_ROOTS_MISSING')
 wrapper_idx=len(js['nodes'])
 js['nodes'].append({'name':'Mudman_Ground_Origin','translation':[0.,round(delta,8),0.],'children':roots})
 scene['nodes']=[wrapper_idx]
 selected=[];relabels=[];dropped=[];sampler_hashes={}
 for a in js['animations']:
  old=a['name'];
  if old not in MAP:dropped.append(old);continue
  sampler_hashes[MAP[old]]=clip_bytes(js,data,a)
  changed=copy.deepcopy(a);changed['name']=MAP[old]
  selected.append(changed);relabels.append({'from':old,'to':MAP[old],'source':'Original Ares -> Godot SecurityTitan scene','reason':'SOURCE_DATA' if old.endswith(MAP[old]) else 'EXPLICIT_ALIAS'})
 js['animations']=selected
 require(len(js['animations'])==23 and len(set(a['name'] for a in selected))==23,'CURATION_COUNT_INVALID')
 # Append and bind the exact original Meshy RGB texture atlas in the GLB BIN.
 original_data_len=len(data);pad=(-len(data))%4;offset=len(data)+pad
 data=data+b'\0'*pad+texture
 if len(data)%4:data+=b'\0'*((-len(data))%4)
 vid=len(js.setdefault('bufferViews',[]))
 js['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(texture)})
 image_idx=len(js.setdefault('images',[]))
 js['images'].append({'name':'Mudman_Meshy_Original_Diffuse_2048','mimeType':'image/png','bufferView':vid})
 tex_idx=len(js.setdefault('textures',[]))
 js['textures'].append({'name':'Mudman_Meshy_Original_Diffuse','source':image_idx})
 js.setdefault('materials',[])
 changed_materials=set();textured_primitives=0
 for mesh in js['meshes']:
  for prim in mesh['primitives']:
   require('TEXCOORD_0' in prim.get('attributes',{}),'MESH_WITHOUT_UV0_CANNOT_APPLY_MESHY_ATLAS')
   if 'material' not in prim:
    prim['material']=len(js['materials']);js['materials'].append({'name':'Mudman_Clay_Meshy'})
   m=prim['material'];require(0<=m<len(js['materials']),'MESH_MATERIAL_INDEX_INVALID')
   material=js['materials'][m]
   pbr=material.setdefault('pbrMetallicRoughness',{})
   pbr['baseColorTexture']={'index':tex_idx,'texCoord':0}
   pbr['baseColorFactor']=[1.,1.,1.,1.]
   # Preserve original normal/emissive/occlusion maps and other material parameters.
   if 'KHR_materials_pbrSpecularGlossiness' in material.get('extensions',{}):
    material['extensions'].pop('KHR_materials_pbrSpecularGlossiness')
   changed_materials.add(m);textured_primitives+=1
 require(textured_primitives>=1,'NO_TEXTURED_PRIMITIVES')
 # Avoid dangling material extension reference if previous asset had an unsupported legacy shader.
 if not any('KHR_materials_pbrSpecularGlossiness' in m.get('extensions',{}) for m in js['materials']):
  js['extensionsUsed']=[x for x in js.get('extensionsUsed',[]) if x!='KHR_materials_pbrSpecularGlossiness']
  js['extensionsRequired']=[x for x in js.get('extensionsRequired',[]) if x!='KHR_materials_pbrSpecularGlossiness']
 js.setdefault('asset',{}).setdefault('extras',{})['mudmanReview']={'schema':V,'originalReviewSHA256':OLD_GLB,'textureSHA256':OWNER_PNG,'reference':'Valar05/gravity-fist/scenes/SecurityTitan.tscn','groundOffsetMeters':round(delta,8),'note':'Exact retained pose/skin/keyframes, only added stationary ground wrapper; active clips curated.'}
 result_bytes=glb_save(js,data,dest)
 check,check_data=glb_load(dest)
 require(check_data[:original_data_len]==glb_load(src)[1],'ANIMATION_OR_GEOMETRY_SOURCE_BIN_MUTATED')
 require(len(check['animations'])==23 and [a['name'] for a in check['animations']]==[a['name'] for a in selected],'EXPORTED_GODOT_ACTIONS_CHANGED')
 require([s for s in check['skins']]==before['skins'] and [a for a in check['accessors']]==before['accessors'],'RIG_SKIN_ACCESSORS_CHANGED')
 require(len(check['meshes'])==len(before['meshes']),'GEOMETRY_MESH_COUNT_CHANGED')
 require(all(clip_bytes(check,check_data,a)==sampler_hashes[a['name']] for a in check['animations']),'RETAINED_ANIMATION_SAMPLERS_CHANGED')
 require(all(check['materials'][p['material']]['pbrMetallicRoughness']['baseColorTexture']['index']==tex_idx for m in check['meshes'] for p in m['primitives']),'MATERIAL_TEXTURE_NOT_APPLIED_TO_ALL_PRIMITIVES')
 after_ground=sampled_skinned_bounds(check,check_data,next(a for a in check['animations'] if a['name']=='Idle-Cross'),t0)
 # Re-measure the identical Idle action after the static parent translation.
 require(abs(after_ground['minY'])<0.002,'MODEL_NOT_GROUNDED_AFTER_WRAPPER_'+str(after_ground['minY']))
 report_object={'schema':V,'status':'CURATED_MUDMAN_REVIEW_PENDING','sourceGLBSHA256':OLD_GLB,'outputGLBSHA256':sha(dest),'outputBytes':result_bytes,
  'animationsBefore':77,'animationsAfter':len(selected),'animationMap':relabels,'excludedAnimationNames':dropped,'sourceBinPrefixUnchanged':True,
  'skinnedOriginalGround':ground,'skinnedGroundAfter':after_ground,'groundOffsetMeters':delta,'groundingMethod':'UNANIMATED_PARENT_TRANSLATION_FROM_ACTUAL_SKINNED_IDLE_VERTEX_MINIMUM',
  'textureOriginalSHA256':OWNER_PNG,'textureEmbeddedSHA256':sha_bytes(texture),'textureDimensions':[width,height],'texturedMeshPrimitives':textured_primitives,
  'texturedMaterialIndices':sorted(changed_materials),'originalAnimationCurvesAndSkinUnchanged':True,'ownerVisualAcceptance':'PENDING',
  'godotEvidence':{'SecurityTitanSceneBlobSHA':'4f07c8c2af40038c1f672750b8a155f53f123b6d','TitanAttackDataBlobSHA':'f2a1036f75cc7c4b7821e700ffa61a6bed7980fc','source':'Valar05/gravity-fist','retainedStaticHoldStates':['ProneBack','ProneFront'],'missingGodotSpecificSource':['HitHeadRight','Idle-Cross exact named Ares source action']}}
 pathlib.Path(report).write_text(json.dumps(report_object,indent=2,sort_keys=True)+'\n')
 return report_object

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--mesh-zip',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True)
 a=p.parse_args();r=apply(a.source,a.mesh_zip,a.output,a.report)
 print('CURATED_GLB='+a.output,'SHA256='+r['outputGLBSHA256'],'CLIPS='+str(r['animationsAfter']),'GROUND_OFFSET='+str(round(r['groundOffsetMeters'],6)),flush=True)
if __name__=='__main__':main()
