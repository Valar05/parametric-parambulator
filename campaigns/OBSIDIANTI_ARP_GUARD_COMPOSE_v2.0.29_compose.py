#!/usr/bin/env python3
"""Recover exact v1.1 original guard + authored idle and compose eight lower-ARP guard steps.
Only appends new glTF animations/buffer data; old clips, skin, mesh and material bytes stay immutable.
"""
from __future__ import annotations
import argparse,bisect,copy,hashlib,json,math,pathlib,struct,sys

VERSION='OBSIDIANTI_ARP_GUARD_COMPOSE_v2.0.29'
CANON_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
ARP_SHA='e7f60fea731fd9537380868adbb52fee63df34fdf1b6d7694bc39925b440fa1d'
STEPS=('StepForward','StepForwardLeft','StepLeft','StepBackLeft','StepBack','StepBackRight','StepRight','StepForwardRight')
GUARD='LionheartIdle_UNREVIEWED'
AUTHORED='ObsidiantiIdle'
HIPS='mixamorig:Hips'
SPINE='mixamorig:Spine'


def require(x,msg):
 if not x:raise ValueError(msg)
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def read_glb(path):
 b=pathlib.Path(path).read_bytes()
 require(len(b)>=28 and b[:4]==b'glTF','INVALID_GLB_MAGIC')
 _,version,total=struct.unpack_from('<4sII',b,0)
 require(version==2 and total==len(b),'INVALID_GLB_VERSION_OR_LENGTH')
 jn,jtyp=struct.unpack_from('<I4s',b,12)
 require(jtyp==b'JSON' and 0<jn<30000000,'INVALID_JSON_CHUNK')
 js=json.loads(b[20:20+jn]);p=20+jn
 bn,btyp=struct.unpack_from('<I4s',b,p)
 require(btyp==b'BIN\0' and p+8+bn==len(b),'INVALID_BIN_CHUNK')
 data=b[p+8:]
 require(len(js.get('buffers',[]))==1 and js['buffers'][0]['byteLength']<=len(data),'INVALID_BUFFERS')
 require(js.get('animations') and js.get('skins') and js.get('meshes'),'MISSING_RIG_MESH_OR_ANIMATIONS')
 return js,data

def glb_save(js,data,path):
 doc=copy.deepcopy(js)
 doc['buffers'][0]['byteLength']=len(data)
 j=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*(-len(j)%4)
 binary=data+b'\0'*(-len(data)%4)
 blob=struct.pack('<4sII',b'glTF',2,28+len(j)+len(binary))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(binary),b'BIN\0')+binary
 pathlib.Path(path).write_bytes(blob)
 return len(blob)

def name_ids(js):
 result={}
 for i,n in enumerate(js['nodes']):
  name=n.get('name')
  if name:
   require(name not in result,'DUPLICATE_BONE_NAME_'+name);result[name]=i
 return result

def parents(js):
 out={}
 for i,n in enumerate(js['nodes']):
  for c in n.get('children',[]):
   require(c not in out,'MULTIPARENT_RIG');out[c]=i
 return out

def descendants(js,root):
 found=set();stack=[root]
 while stack:
  node=stack.pop()
  if node in found:continue
  found.add(node);stack.extend(js['nodes'][node].get('children',[]))
 return found

def normq(q):
 d=math.sqrt(sum(float(x)**2 for x in q));require(math.isfinite(d) and d>1e-10,'BAD_QUATERNION')
 return tuple(float(x)/d for x in q)
def qm(a,b):
 x,y,z,w=normq(a);u,v,t,s=normq(b)
 return normq((w*u+x*s+y*t-z*v,w*v-x*t+y*s+z*u,w*t+x*v-y*u+z*s,w*s-x*u-y*v-z*t))
def qi(q):
 x,y,z,w=normq(q);return (-x,-y,-z,w)
def qdeg(a,b):
 d=abs(sum(x*y for x,y in zip(normq(a),normq(b))))
 return 2*math.degrees(math.acos(min(1.,max(-1.,d))))
def qslerp(a,b,f):
 a=normq(a);b=normq(b);d=sum(x*y for x,y in zip(a,b))
 if d<0:b=tuple(-v for v in b);d=-d
 if d>.9995:return normq(tuple(x*(1-f)+y*f for x,y in zip(a,b)))
 angle=math.acos(max(-1.,min(1.,d)));s=math.sin(angle)
 return normq(tuple((x*math.sin((1-f)*angle)+y*math.sin(f*angle))/s for x,y in zip(a,b)))

def raw_accessor(js,data,i):
 a=js['accessors'][i];require('sparse' not in a and 'bufferView' in a,'UNSUPPORTED_SPARSE_ACCESSOR')
 v=js['bufferViews'][a['bufferView']]
 require(v.get('buffer',0)==0,'MULTI_BUFFER_ACCESSOR_UNSUPPORTED')
 typ=a['type'];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}.get(typ)
 fmt={5126:'f',5125:'I',5123:'H',5121:'B'}.get(a['componentType'])
 require(n is not None and fmt is not None,'UNSUPPORTED_ACCESSOR_TYPE')
 sz=struct.calcsize('<'+fmt*n);stride=v.get('byteStride',sz)
 require(stride>=sz,'BAD_ACCESSOR_STRIDE')
 off=v.get('byteOffset',0)+a.get('byteOffset',0)
 require(off>=0 and (off+(a['count']-1)*stride+sz)<=len(data),'ACCESSOR_OUTSIDE_BUFFER')
 return [struct.unpack_from('<'+fmt*n,data,off+j*stride) for j in range(a['count'])]

def get_channel(clip,node,path):
 ch=[x for x in clip['channels'] if x['target'].get('node')==node and x['target'].get('path')==path]
 require(len(ch)<=1,'MULTIPLE_SAME_CHANNEL_'+str((node,path)))
 return ch[0] if ch else None

def at_time(js,data,clip,node,path,t):
 ch=get_channel(clip,node,path)
 if ch is None:return js['nodes'][node].get(path,(0.,0.,0.,1.) if path=='rotation' else ((1.,1.,1.) if path=='scale' else (0.,0.,0.)))
 samp=clip['samplers'][ch['sampler']]
 ts=[x[0] for x in raw_accessor(js,data,samp['input'])]
 vals=raw_accessor(js,data,samp['output'])
 require(len(ts)>=1 and len(ts)==len(vals),'CHANNEL_TIME_VALUE_MISMATCH')
 if t<=ts[0]:return vals[0]
 if t>=ts[-1]:return vals[-1]
 i=bisect.bisect_right(ts,t)-1
 require(ts[i+1]>ts[i],'NON_INCREASING_TIMES')
 f=(t-ts[i])/(ts[i+1]-ts[i]);interp=samp.get('interpolation','LINEAR')
 if interp=='STEP':return vals[i]
 require(interp=='LINEAR','UNSUPPORTED_INTERPOLATION_'+interp)
 if path=='rotation':return qslerp(vals[i],vals[i+1],f)
 return tuple(x+(y-x)*f for x,y in zip(vals[i],vals[i+1]))

def range_times(js,data,clip):
 ends=[]
 for sm in clip['samplers']:
  ts=raw_accessor(js,data,sm['input']);require(ts and ts[0][0]>=-.00001,'INVALID_TIME_RANGE')
  ends.append((ts[0][0],ts[-1][0]))
 return min(a for a,b in ends),max(b for a,b in ends)

class Appender:
 def __init__(self,js,data):self.js=js;self.bin=bytearray(data)
 def alloc_bytes(self,b):
  self.bin.extend(b'\0'*(-len(self.bin)%4))
  off=len(self.bin);self.bin.extend(b)
  ix=len(self.js['bufferViews']);self.js['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(b)})
  return ix
 def floats(self,rows,typ):
  width={'SCALAR':1,'VEC3':3,'VEC4':4}[typ]
  require(all(len(row)==width for row in rows),'INVALID_FLOAT_ROW_WIDTH')
  flat=[float(v) for row in rows for v in row]
  require(flat and all(math.isfinite(v) for v in flat),'NAN_OR_EMPTY_FLOAT_TRACK')
  raw=struct.pack('<'+'f'*len(flat),*flat)
  view=self.alloc_bytes(raw)
  acc={'bufferView':view,'byteOffset':0,'componentType':5126,'count':len(rows),'type':typ}
  if typ=='SCALAR':acc.update(min=[min(flat)],max=[max(flat)])
  self.js['accessors'].append(acc);return len(self.js['accessors'])-1
 def copy_accessor(self,source_js,source_bin,i,cache):
  if i in cache:return cache[i]
  a=copy.deepcopy(source_js['accessors'][i]);require('sparse' not in a and 'bufferView' in a,'CANNOT_COPY_SPARSE_ACCESSOR')
  v=source_js['bufferViews'][a['bufferView']];require(v.get('buffer',0)==0,'MULTIBUFFER_GUARD')
  lo=v.get('byteOffset',0);hi=lo+v['byteLength'];require(0<=lo<hi<=len(source_bin),'COPY_ACCESSOR_OVERRUN')
  bv=self.alloc_bytes(source_bin[lo:hi]);a['bufferView']=bv
  idx=len(self.js['accessors']);self.js['accessors'].append(a);cache[i]=idx;return idx
 def copy_clip(self,source_js,source_bin,clip,name,node_ids):
  cache={};result={'name':name,'samplers':[],'channels':[]}
  for samp in clip['samplers']:
   sm=copy.deepcopy(samp)
   for key in ('input','output'):sm[key]=self.copy_accessor(source_js,source_bin,sm[key],cache)
   result['samplers'].append(sm)
  for ch in clip['channels']:
   target=ch['target'];bone=source_js['nodes'][target['node']].get('name')
   require(bone in node_ids,'GUARD_ACTION_TARGET_BONE_MISSING_'+str(bone))
   new=copy.deepcopy(ch);new['target']['node']=node_ids[bone];result['channels'].append(new)
  self.js['animations'].append(result)
  return result
 def add(self,clip,node,path,times,vals):
  require(len(times)==len(vals) and len(times)>=2,'BAD_OUTPUT_TRACK')
  require(all(b>a for a,b in zip(times,times[1:])),'NONMONOTONIC_NEW_TIMES')
  ix=self.floats([(t,) for t in times],'SCALAR')
  oi=self.floats(vals,'VEC4' if path=='rotation' else 'VEC3')
  s=len(clip['samplers']);clip['samplers'].append({'input':ix,'output':oi,'interpolation':'LINEAR'})
  clip['channels'].append({'sampler':s,'target':{'node':node,'path':path}})


def compatibility(src,tgt):
 a,b=name_ids(src),name_ids(tgt)
 pa,pb=parents(src),parents(tgt)
 required=('mixamorig:Hips','mixamorig:Spine','mixamorig:Spine1','mixamorig:Spine2','mixamorig:LeftArm','mixamorig:RightArm','mixamorig:LeftWeapon.L','mixamorig:RightWeapon.R','mixamorig:LeftUpLeg','mixamorig:RightUpLeg','mixamorig:LeftFoot','mixamorig:RightFoot')
 for n in required:require(n in a and n in b,'GUARD_TARGET_BONE_INCOMPATIBLE_'+n)
 for n in a.keys() & b.keys():
  if n.startswith('mixamorig:'):
   sidx=a[n];tidx=b[n]
   san=src['nodes'][pa[sidx]].get('name') if sidx in pa else None
   tan=tgt['nodes'][pb[tidx]].get('name') if tidx in pb else None
   require(san==tan,'HIERARCHY_INCOMPATIBLE_'+n)
 warnings=[]
 for n in required:
  v=src['nodes'][a[n]];w=tgt['nodes'][b[n]]
  for path,ident in (('rotation',(0.,0.,0.,1.)),('translation',(0.,0.,0.)),('scale',(1.,1.,1.))):
   x=v.get(path,ident);y=w.get(path,ident)
   diff=qdeg(x,y) if path=='rotation' else math.dist(x,y)
   warnings.append({'bone':n,'path':path,'difference':round(diff,7)})
   require(diff<(.025 if path=='rotation' else .015),'REST_POSE_INCOMPATIBLE_'+n+'_'+path+'_'+str(round(diff,5)))
 return {'requiredBones':len(required),'matchedNamedBones':len(a.keys() & b.keys()),'maxRestRotationDeg':max(x['difference'] for x in warnings if x['path']=='rotation'),'maxRestPositionM':max(x['difference'] for x in warnings if x['path']=='translation')}

def world_rot(js,clip,dat,names,ps,node,t):
 cache={}
 def visit(i):
  if i not in cache:
   local=at_time(js,dat,clip,i,'rotation',t)
   cache[i]=qm(visit(ps[i]),local) if i in ps else normq(local)
  return cache[i]
 return visit(names[node])

def compose(source,target,output,report,expected_source=CANON_SHA,expected_target=ARP_SHA):
 source,target,output,report=map(pathlib.Path,(source,target,output,report))
 require(source.is_file() and digest(source)==expected_source,'ORIGINAL_CANONICAL_IDLE_BINARY_SHA_MISMATCH')
 require(target.is_file() and digest(target)==expected_target,'V216_ARP_LIBRARY_BINARY_SHA_MISMATCH')
 require(not output.exists() and not report.exists(),'OUTPUT_COLLISION_NOT_ALLOWED')
 sg,sb=read_glb(source);tg,tb=read_glb(target)
 original=copy.deepcopy(tg);originalnames=[a['name'] for a in tg['animations']]
 require(len(originalnames)==23 and len(set(originalnames))==23,'ARP_SOURCE_NOT_EXACT_23_CLIP_LIBRARY')
 for n in STEPS:require('Ares_'+n in originalnames,'MISSING_MOVING_ARP_STEP_'+n)
 sn=name_ids(sg);tn=name_ids(tg)
 compatibles=compatibility(sg,tg)
 scl={a['name']:a for a in sg['animations']}
 require(GUARD in scl and AUTHORED in scl,'AUTHORED_OBSIDIANTI_IDLE_OR_LIONHEART_GUARD_NOT_FOUND')
 guard=scl[GUARD];author=scl[AUTHORED]
 gt0,_=range_times(sg,sb,guard); at0,at1=range_times(sg,sb,author)
 require(2.9<=at1-at0<=3.1,'AUTHORED_IDLE_NOT_3_SECOND_LOOP')
 # Original authored motion was built around exactly the Lionheart guard at t=0.
 head_bones=['mixamorig:Spine','mixamorig:Spine1','mixamorig:Spine2','mixamorig:LeftArm','mixamorig:RightArm','mixamorig:LeftWeapon.L','mixamorig:RightWeapon.R']
 idle_errors={n:qdeg(at_time(sg,sb,guard,sn[n],'rotation',gt0),at_time(sg,sb,author,sn[n],'rotation',at0)) for n in head_bones}
 require(max(idle_errors.values())<2.,'AUTHORED_IDLE_NOT_BASED_ON_LIONHEART_GUARD')
 app=Appender(copy.deepcopy(tg),tb)
 recovered_guard=app.copy_clip(sg,sb,guard,GUARD,tn)
 recovered_idle=app.copy_clip(sg,sb,author,AUTHORED,tn)
 # Ensure recovered idle's source values were transplanted exactly, before limb work.
 upper=descendants(tg,tn[SPINE]);ps=parents(tg)
 assert tn[SPINE] in upper and tn[HIPS] not in upper
 def guard_value(node,path):
  name=tg['nodes'][node].get('name');require(name in sn,'MISSING_GUARD_BONE_'+str(name))
  result=at_time(sg,sb,guard,sn[name],path,gt0)
  return normq(result) if path=='rotation' else tuple(result)
 gh=guard_value(tn[HIPS],'rotation');gs=guard_value(tn[SPINE],'rotation')
 samples=[]
 for step in STEPS:
  orig=next(a for a in original['animations'] if a['name']=='Ares_'+step)
  start,end=range_times(tg,tb,orig);require(.25<end-start<5,'INVALID_REAL_STEP_DURATION_'+step)
  hip_ch=get_channel(orig,tn[HIPS],'rotation')
  require(hip_ch is not None,'MISSING_ARP_HIP_ROTATION_'+step)
  sm=orig['samplers'][hip_ch['sampler']]
  hip_times=[x[0] for x in raw_accessor(tg,tb,sm['input'])]
  hip_rot=raw_accessor(tg,tb,sm['output'])
  require(len(hip_times)>=10 and len(hip_times)==len(hip_rot),'ARP_STEP_NOT_REAL_MOTION_'+step)
  # Preserve original Ares step channels except upper hierarchy. New independent clip.
  new=copy.deepcopy(orig);new['name']='Combat'+step
  oldchannels=len(new['channels'])
  new['channels']=[ch for ch in new['channels'] if ch['target']['node'] not in upper]
  kept=copy.deepcopy(new['channels'])
  # Sample at key and intermediate times, compensating Hips rotation so the Spine
  # world-frame matches the original Lionheart guard, as in the successful v1.1 pass.
  rate=120
  count=math.ceil((end-start)*rate)
  times=sorted(set([round(t,8) for t in hip_times]+[round(start+(end-start)*k/count,8) for k in range(count+1)]))
  times=[t for i,t in enumerate(times) if i==0 or t>times[i-1]+1e-8]
  require(len(times)>=10,'NOT_ENOUGH_COMPENSATION_SAMPLES')
  vals=[]
  for t in times:
   h=at_time(tg,tb,orig,tn[HIPS],'rotation',t)
   vals.append(qm(qm(qi(h),gh),gs))
  app.add(new,tn[SPINE],'rotation',times,vals)
  # Recreate all guard upper-bone rotation, position, and scale. In v2.0.16
  # the ARP importer explicitly animated those, even when we intended lower-only.
  for node in sorted(upper):
   for path in ('rotation','translation','scale'):
    if node==tn[SPINE] and path=='rotation':continue
    base=guard_value(node,path)
    app.add(new,node,path,[start,end],[base,base])
  # Only lower/hip channels from ARP must remain byte-for-byte reused.
  require(all(ch in new['channels'] for ch in kept),'LOWER_CHANNEL_MODIFIED')
  require(len([ch for ch in new['channels'] if ch['target']['node'] in upper])==len(upper)*3,'UPPER_CHANNEL_COVERAGE_INCOMPLETE')
  # Validate world orientation of shoulder/arm/weapon guard across full clip and midframes.
  tmp=app.js.copy(); tmp['animations']=[new]
  maxerr=0.;worst=None
  check_times=sorted(set(times+[start+(end-start)*i/80 for i in range(81)]))
  for t in check_times:
   for bone in head_bones:
    expected=world_rot(sg,guard,sb,sn,parents(sg),bone,gt0)
    actual=world_rot(app.js,new,app.bin,tn,ps,bone,t)
    err=qdeg(expected,actual)
    if err>maxerr:maxerr=err;worst=(bone,t)
  require(maxerr<0.45,'GUARD_WORLD_FRAME_MISMATCH_'+step+'_'+repr((maxerr,worst)))
  app.js['animations'].append(new)
  samples.append({'source':'Ares_'+step,'composed':new['name'],'hipKeys':len(hip_times),'upperBoneCount':len(upper),
                  'upperTracksReplaced':oldchannels-len(kept),'newTracks':len(upper)*3,
                  'duration':round(end-start,6),'maxGuardWorldRotationErrorDegrees':round(maxerr,7),
                  'worstWitness':repr(worst),'lowerChannelsOriginal':len(kept), 'compensationFrames':len(times)})
 # No original clip, skeleton, mesh, skin or original source byte may change.
 require(app.js['animations'][:23]==original['animations'],'EXISTING_ARP_CLIPS_JSON_MODIFIED')
 for key in ('nodes','meshes','skins','materials','textures','images','scenes'):
  require(app.js.get(key)==original.get(key),'TARGET_RIG_OR_MATERIAL_MODIFIED_'+key)
 require(bytes(app.bin[:len(tb)])==tb,'TARGET_ORIGINAL_GLB_BUFFER_MODIFIED')
 names=[a['name'] for a in app.js['animations']]
 require(len(names)==33 and len(set(names))==33,'COMPOSED_LIBRARY_COUNT_OR_DUPLICATE')
 output.parent.mkdir(parents=True,exist_ok=True)
 glb_save(app.js,bytes(app.bin),output)
 result,binary=read_glb(output)
 require(len(result['animations'])==33 and result['animations'][:23]==original['animations'],'REOPENED_GLB_ORIGINAL_CLIPS_CHANGED')
 require(binary.startswith(tb),'REOPENED_GLB_OLD_BIN_BYTES_CHANGED')
 for key in ('nodes','meshes','skins','materials','textures','images','scenes'):
  require(result.get(key)==original.get(key),'REOPENED_MODEL_STRUCTURE_CHANGED_'+key)
 # Explicit source provenance for all 10 new actions.
 evidence={'schema':VERSION,'status':'GUARD_COMPOSED_REVIEW_UNAPPROVED','sourceCanonicalSHA256':digest(source),
     'sourceARPv216SHA256':digest(target),'resultSHA256':digest(output),'resultBytes':output.stat().st_size,
     'newActionNames':[a['name'] for a in result['animations'][23:]],'existingAnimationsPreserved':23,
     'sourceAuthoredIdleDuration':round(at1-at0,5),'authoredIdleRecoveredFromOriginalSamplerData':True,
     'sourceGuardClip':GUARD,'staticGuardRecoveredFromOriginalSamplerData':True,
     'guardVsAuthoredIdleFirstFrameRotationDegrees':{n:round(v,7) for n,v in idle_errors.items()},
     'compatibleSkeleton':compatibles,'steps':samples,'all22OtherExistingAnimationsPreserved':True,
     'originalAnimationDataPreserved':True,'originalModelAndMaterialsPreserved':True,
     'method':'MOTION_FROM_ARP_V216_HIPS_LEGS_FEET; STATIC_LIONHEART_GUARD_UPPER; V110_HIP_COUNTER_ROTATION',
     'runtime':'Three.js AnimationMixer (Godot runtime not involved)','canonicalModified':False,
     'ownerVisualAcceptance':'PENDING'}
 report.parent.mkdir(parents=True,exist_ok=True)
 report.write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
 return evidence

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--canonical',required=True);p.add_argument('--arp',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True)
 args=p.parse_args();print(json.dumps(compose(args.canonical,args.arp,args.output,args.report),indent=2))
