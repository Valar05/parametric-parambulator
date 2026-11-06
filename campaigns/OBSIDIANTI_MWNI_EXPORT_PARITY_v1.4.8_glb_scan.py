#!/usr/bin/env python3
"""Independently inspect the *values* of animation keyframes in a GLB, not merely channel names."""
from __future__ import annotations
import argparse,hashlib,json,math,pathlib,struct
PARTS=('LeftUpLeg','LeftLeg','LeftFoot','RightUpLeg','RightLeg','RightFoot','LeftArm','LeftForeArm','RightArm','RightForeArm','Spine2')
DTYPE={5126:('f',4),5123:('H',2),5121:('B',1),5125:('I',4),5122:('h',2)}
COMP={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def hash_file(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse_glb(path):
 p=pathlib.Path(path);f=p.open('rb');n=p.stat().st_size
 if n<28 or n>512*1024*1024:raise RuntimeError('GLB_SIZE_OUT_OF_RANGE')
 with f:
  header=f.read(12)
  if len(header)!=12 or header[:4]!=b'glTF' or struct.unpack_from('<II',header,4)!=(2,n):raise RuntimeError('GLB_HEADER_INVALID')
  jsz,jstype=struct.unpack('<I4s',f.read(8))
  if jstype!=b'JSON' or jsz>32*1024*1024:raise RuntimeError('GLB_JSON_INVALID')
  data=json.loads(f.read(jsz).decode('utf8'))
  bsize,btype=struct.unpack('<I4s',f.read(8))
  if btype!=b'BIN\x00' or bsize>500*1024*1024:raise RuntimeError('GLB_BIN_INVALID')
  binpart=f.read(bsize)
  if len(binpart)!=bsize:raise RuntimeError('GLB_BIN_TRUNCATED')
 return data,binpart

def accessor_values(g,binpart,index,limit=12000):
 a=g['accessors'][index];ct=a['componentType'];typ=a['type'];count=a['count']
 if 'sparse' in a:raise RuntimeError('SPARSE_ACCESSOR_UNSUPPORTED')
 if ct not in DTYPE or typ not in COMP or count>limit:raise RuntimeError('ACCESSOR_FORMAT_UNSUPPORTED')
 fmt,width=DTYPE[ct];component_count=COMP[typ];v=g['bufferViews'][a['bufferView']]
 if v.get('buffer',0)!=0:raise RuntimeError('EXTERNAL_BIN_BUFFER_UNSUPPORTED')
 stride=v.get('byteStride',component_count*width);start=v.get('byteOffset',0)+a.get('byteOffset',0)
 if stride<width*component_count or start+(count-1)*stride+component_count*width>len(binpart):raise RuntimeError('ACCESSOR_RANGE_INVALID')
 ans=[];packer='<'+fmt*component_count
 for i in range(count):
  raw=struct.unpack_from(packer,binpart,start+i*stride)
  if a.get('normalized'):
   div={5123:65535,5121:255,5125:4294967295,5122:32767}.get(ct)
   if div is None:raise RuntimeError('NORMALIZED_COMPONENT_UNSUPPORTED')
   raw=tuple(max(-1.0,x/div) for x in raw)
  ans.append(raw)
 return ans

def excursion(g,binpart,ch,smpl):
 values=accessor_values(g,binpart,smpl['output'])
 if smpl.get('interpolation')=='CUBICSPLINE':
  if len(values)%3:raise RuntimeError('CUBICSPLINE_VALUE_COUNT_INVALID')
  values=values[1::3]  # each key is IN_TANGENT, VALUE, OUT_TANGENT
 elif smpl.get('interpolation','LINEAR') not in ('LINEAR','STEP'):
  raise RuntimeError('UNKNOWN_GLTF_INTERPOLATION')
 if len(values)<2:return 0.0
 path=ch['target']['path'];first=values[0]
 if path=='rotation':
  def quat(v):
   n=math.sqrt(sum(x*x for x in v))
   if n<1e-9 or not math.isfinite(n):raise RuntimeError('NONNORMALIZABLE_ROTATION_QUATERNION')
   return tuple(x/n for x in v)
  q0=quat(first)
  return round(max(math.degrees(2*math.acos(min(1.,abs(sum(a*b for a,b in zip(q0,quat(q))))))) for q in values),4)
 if path=='translation':return round(max(math.dist(first,v) for v in values),5)
 return round(max(math.dist(first,v) for v in values),5)

def scan(path,clip):
 g,raw=parse_glb(path);nodes=g['nodes'];rows=[]
 skin_joints={i for skin in g.get('skins',[]) for i in skin.get('joints',[])}
 if not skin_joints:raise RuntimeError('GLB_NO_SKINNED_BONES')
 for a in g.get('animations',[]):
  for ch in a.get('channels',[]):
   name=nodes[ch['target']['node']].get('name','')
   smp=a['samplers'][ch['sampler']]
   try:val=excursion(g,raw,ch,smp)
   except Exception as e:raise RuntimeError('VALUE_DECODE_FAILED '+name+' '+ch['target']['path']+' '+str(e))
   rows.append({'bone':name,'path':ch['target']['path'],'valueRange':val,'count':g['accessors'][smp['output']]['count'], 'isSkinnedJoint':ch['target']['node'] in skin_joints})
 focus={p:max((v['valueRange'] for v in rows if v['path']=='rotation' and v['isSkinnedJoint'] and v['bone'].endswith('mixamorig:'+p)),default=0) for p in PARTS}
 moving={p:v for p,v in focus.items() if v>5.0}
 ok=all(sum(focus.get(p,0)>5 for p in opts)>=1 for opts in (('LeftUpLeg','LeftLeg'),('RightUpLeg','RightLeg'),('LeftArm','RightArm','Spine2')))
 out={'clip':clip,'sha256':hash_file(path),'bytes':pathlib.Path(path).stat().st_size,'animationNames':[x.get('name') for x in g.get('animations',[])],
  'channels':len(rows),'rotatingBonesDegrees':focus,'movingBodyParts':moving,'movingBodyPartCount':len(moving),'animatedLimbs':ok,
  'movingJointCount':sum(v>5 for v in focus.values()),'channelDetails':rows,
  'meshes':len(g.get('meshes',[])),'skins':len(g.get('skins',[])),'skinnedJointCount':len(skin_joints)}
 return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--glb',required=True);ap.add_argument('--clip',required=True);ap.add_argument('--out',required=True)
 args=ap.parse_args();obj=scan(args.glb,args.clip);pathlib.Path(args.out).write_text(json.dumps(obj,indent=2)+'\n');print('GLB_SCAN='+json.dumps({k:obj[k] for k in ('clip','sha256','movingBodyPartCount','animatedLimbs')},sort_keys=True),flush=True)
