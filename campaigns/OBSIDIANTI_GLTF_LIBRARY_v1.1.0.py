#!/usr/bin/env python3
"""Append all sampled motion to ONE existing canonical Obsidianti GLB, retaining original binary payload.

No model copies or alternative model paths are emitted. Parent orchestration writes to an
atomic temporary byte-stream in the SAME canonical path and commits its replacement.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, os, struct, tempfile
from pathlib import Path

VERSION='OBSIDIANTI_GLTF_LIBRARY_v1.1.0'
SOURCE_MODEL_SHA='27f943ddf1ba1f72169026a2cb4750662f00b053f78e4346f43b3888c744e95b'
ANIM_LABELS=('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
STEP_LABELS=('StepForward','StepBack','StepLeft','StepRight','StepForwardLeft','StepForwardRight','StepBackLeft','StepBackRight')


def sha(path):
 h=hashlib.sha256();
 with open(path,'rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def qmul(a,b):
 ax,ay,az,aw=a;bx,by,bz,bw=b
 return [aw*bx+ax*bw+ay*bz-az*by,aw*by+ay*bw+az*bx-ax*bz,aw*bz+az*bw+ax*by-ay*bx,aw*bw-ax*bx-ay*by-az*bz]
def qnorm(q):
 n=math.sqrt(sum(v*v for v in q));return [v/n for v in q] if n>1e-12 else [0,0,0,1]
def qinv(q):return [-q[0],-q[1],-q[2],q[3]]
def qslerp(a,b,t):
 a=qnorm(a);b=qnorm(b);dot=sum(x*y for x,y in zip(a,b))
 if dot<0:b=[-v for v in b];dot=-dot
 if dot>.9995:return qnorm([x*(1-t)+y*t for x,y in zip(a,b)])
 theta=math.acos(max(-1,min(1,dot)));s=math.sin(theta)
 return qnorm([x*math.sin((1-t)*theta)/s+y*math.sin(t*theta)/s for x,y in zip(a,b)])

def qaxis(angle,axis):
 m=math.sin(angle/2);return [axis[0]*m,axis[1]*m,axis[2]*m,math.cos(angle/2)]

def glb_load(path):
 data=Path(path).read_bytes();assert data[:4]==b'glTF' and struct.unpack_from('<II',data,4)==(2,len(data))
 jslen,jstype=struct.unpack_from('<I4s',data,12);assert jstype==b'JSON';g=json.loads(data[20:20+jslen]);p=20+jslen
 n,typ=struct.unpack_from('<I4s',data,p);assert typ==b'BIN\0';b=bytearray(data[p+8:p+8+n]);assert len(b)==g['buffers'][0]['byteLength']
 return g,b

def glb_bytes(g,b):
 g['buffers'][0]['byteLength']=len(b)
 j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*(-len(j)%4)
 binary=bytes(b);binary+=b'\0'*(-len(binary)%4)
 return struct.pack('<4sII',b'glTF',2,28+len(j)+len(binary))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(binary),b'BIN\0')+binary

def read_accessor(g,b,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
 typ={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
 fmt={5126:'f',5123:'H',5121:'B'}[a['componentType']];stride=v.get('byteStride',struct.calcsize('<'+fmt*typ));start=v.get('byteOffset',0)+a.get('byteOffset',0)
 return [list(struct.unpack_from('<'+fmt*typ,b,start+k*stride)) for k in range(a['count'])]

class Writer:
 def __init__(self,g,b):self.g,self.b=g,b
 def alloc(self,raw):
  while len(self.b)%4:self.b.append(0)
  off=len(self.b);self.b.extend(raw);i=len(self.g['bufferViews']);self.g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(raw)});return i
 def acc(self,frames,typ):
  dim={'SCALAR':1,'VEC3':3,'VEC4':4}[typ];values=[float(n) for f in frames for n in (f if isinstance(f,(tuple,list)) else [f])];assert len(values)==len(frames)*dim
  if not all(math.isfinite(n) for n in values):raise ValueError('NONFINITE_ANIM_VALUE')
  view=self.alloc(struct.pack('<'+'f'*len(values),*values));a={'bufferView':view,'componentType':5126,'count':len(frames),'type':typ};
  if typ=='SCALAR':a.update(min=[min(values)],max=[max(values)])
  self.g['accessors'].append(a);return len(self.g['accessors'])-1
 def animation(self,name,times,rots,poss):
  if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('NONMONOTONIC_TIME '+name)
  ix=self.acc(times,'SCALAR');anim={'name':name,'samplers':[],'channels':[]}
  for j,data in sorted(rots.items()):
   if len(data)!=len(times):raise ValueError('TRACK_LENGTH '+name)
   oi=self.acc([qnorm(q) for q in data],'VEC4');k=len(anim['samplers']);anim['samplers'].append({'input':ix,'output':oi,'interpolation':'LINEAR'});anim['channels'].append({'sampler':k,'target':{'node':j,'path':'rotation'}})
  for j,data in sorted(poss.items()):
   if len(data)!=len(times):raise ValueError('TRACK_LENGTH '+name)
   oi=self.acc(data,'VEC3');k=len(anim['samplers']);anim['samplers'].append({'input':ix,'output':oi,'interpolation':'LINEAR'});anim['channels'].append({'sampler':k,'target':{'node':j,'path':'translation'}})
  self.g['animations'].append(anim);return len(anim['channels'])

def ref_quats(g):
 parents={child:i for i,n in enumerate(g['nodes']) for child in n.get('children',[])}
 cache={}
 def world(j):
  if j not in cache:
   local=qnorm(g['nodes'][j].get('rotation',[0,0,0,1]));cache[j]=qmul(world(parents[j]),local) if j in parents else local
  return cache[j]
 return {i:qnorm(world(i)) for i in range(len(g['nodes']))}

def approved_idle(g,b):
 a=next((a for a in g['animations'] if a['name']=='LionheartIdle_UNREVIEWED'),None)
 if not a:raise ValueError('APPROVED_PREVIEW_IDLE_MISSING')
 result={};positions={}
 for ch in a['channels']:
  sp=a['samplers'][ch['sampler']];vals=read_accessor(g,b,sp['output']);node=ch['target']['node'];p=ch['target']['path']
  if p=='rotation':result[node]=qnorm(vals[0])
  if p=='translation':positions[node]=vals[0]
 return result,positions

def nmap(g):return {n.get('name'):i for i,n in enumerate(g['nodes']) if n.get('name')}
def map_bone(s,names):
 if s=='Weapon.L':return names.get('mixamorig:LeftWeapon.L')
 if s=='Weapon.R':return names.get('mixamorig:RightWeapon.R')
 return names.get(s)

def rebase_source_pose(source,base_source,g,rest_world,approved,frames,only_lower=False):
 names=nmap(g)
 keys=set(base_source['bones']);out={};locs={}
 for bone in keys:
  j=map_bone(bone,names)
  if j is None:continue
  if only_lower and not (bone=='mixamorig:Hips' or 'Leg' in bone or 'Foot' in bone or 'Toe' in bone):continue
  if bone not in source['bones']:continue
  # Convert sampled source pose delta from source bone space to destination target bone space.
  def mapped(sourcebone):
   src_rest=sourcebone['restWorldQuat'];pose=sourcebone['localDeltaQuat'];target_rest=rest_world[j]
   rebased=qmul(qmul(qmul(qinv(target_rest),src_rest),pose),qmul(qinv(src_rest),target_rest))
   return qnorm(qmul(g['nodes'][j].get('rotation',[0,0,0,1]),rebased))
  qbase=mapped(base_source['bones'][bone]);qnow=mapped(source['bones'][bone]);
  # Source Idle -> approved target Idle ensures every clip uses the SAME user-liked combat stance.
  approved_q=approved.get(j,g['nodes'][j].get('rotation',[0,0,0,1]));offset=qmul(approved_q,qinv(qbase));out[j]=qnorm(qmul(offset,qnow))
 return out

def interp_head(s,amp):
 return qaxis(math.sin(2*math.pi*s)*amp,[0,0,1])

def parse_samples(blob,keys):
 if not isinstance(blob,dict):raise ValueError('MISSING_SOURCE_SAMPLES')
 actions=blob.get('actions',{})
 missing=[x for x in keys if x not in actions]
 if missing:raise ValueError('SOURCE_ACTIONS_MISSING '+','.join(missing))
 for name in keys:
  rows=actions[name]['frames'];
  if len(rows)<2:raise ValueError('SOURCE_ACTION_NOT_ANIMATED '+name)
  if rows[-1]['time']<=rows[0]['time']:raise ValueError('SOURCE_DURATION_INVALID '+name)
  if not all('mixamorig:Hips' in f['bones'] for f in rows):raise ValueError('SOURCE_HIPS_MISSING '+name)
 return actions

def make_library(model,lionheart,ares,report_path,ground_delta=-.012):
 if sha(model)!=SOURCE_MODEL_SHA:raise ValueError('CANONICAL_SHA_CHANGED: refuse to overwrite unrecognized model')
 g,b=glb_load(model);original_binary=bytes(b);original_anims=copy.deepcopy(g['animations']);original_jointskin=copy.deepcopy(g['skins']);original_meshes=copy.deepcopy(g['meshes']);original_nodes=copy.deepcopy(g['nodes']);
 if g['scenes'][0]['nodes']!=[77]:raise ValueError('UNUSED_CLOTH_SCENE_REGRESSION')
 names=nmap(g);rest_world=ref_quats(g);approved,baseline_pos=approved_idle(g,b)
 hip=names['mixamorig:Hips'];assert hip in baseline_pos
 if not (-.05<=ground_delta<=.01):raise ValueError('GROUND_DELTA_OUT_OF_BOUNDS')
 # Keep approved bone angles EXACT, change only hip Y by small declared visual correction.
 baseline_pos[hip]=[baseline_pos[hip][0],baseline_pos[hip][1]+ground_delta,baseline_pos[hip][2]]
 w=Writer(g,b);evidence=[]
 # Real 3-second looping idle, visibly different frames, with source Idle as central pose.
 # This is authored secondary breathing/weight motion; native Lionheart Idle itself is STATIC.
 idle_t=[i/30 for i in range(91)]
 idle_rots={j:[] for j in approved};idle_pos={hip:[]}
 # small torso expansion, weight loading, head counter-motion, subtle shield/weapon sway.
 breath_targets={names.get('mixamorig:Spine1'):.010,names.get('mixamorig:Spine2'):.014,names.get('mixamorig:Neck'):-.003}
 breath_targets={k:v for k,v in breath_targets.items() if k in approved}
 for t in idle_t:
  phase=2*math.pi*t/3;inhale=math.sin(phase);sway=math.sin(phase)
  for j,q in approved.items():
   amp=breath_targets.get(j,0.0)
   add=qaxis(amp*inhale,[1,0,0])
   if j==names.get('mixamorig:Hips'):add=qmul(add,qaxis(.004*sway,[0,0,1]))
   idle_rots[j].append(qnorm(qmul(q,add)))
  idle_pos[hip].append([baseline_pos[hip][0]+.002*sway,baseline_pos[hip][1]+.002*(1-math.cos(phase)),baseline_pos[hip][2]])
 idlen=w.animation('ObsidiantiIdle',idle_t,idle_rots,idle_pos);evidence.append({'clip':'ObsidiantiIdle','duration':3.0,'channels':idlen,'status':'REVIEW_CANDIDATE_NOT_SOURCE_AUTHORED','note':'3-second gentle animated loop centered on exact owner-approved Lionheart static pose'})
 # Per-move sampled Blender-evaluated source, including constrained IK feet and weapon locs.
 la=parse_samples(lionheart,ANIM_LABELS)
 base=lionheart['actions']['Idle']['frames'][0] if 'Idle' in lionheart['actions'] else lionheart['idlePose']
 if 'mixamorig:Hips' not in base['bones']:raise ValueError('LIONHEART_IDLE_BASE_MISSING')
 for name in ANIM_LABELS:
  frames=la[name]['frames'];times=[float(f['time'])-float(frames[0]['time']) for f in frames]
  rots={};poss={}
  for f in frames:
   mapped=rebase_source_pose(f,base,g,rest_world,approved,frames)
   for j in approved:rots.setdefault(j,[]).append(mapped.get(j,approved[j]))
   hp0=base['bones']['mixamorig:Hips']['worldPosition'];hp1=f['bones']['mixamorig:Hips']['worldPosition'];delta=[hp1[k]-hp0[k] for k in range(3)]
   for k in range(3):
    if abs(delta[k])>2:raise ValueError('ROOT_TRANSLATION_EXCESSIVE '+name)
   poss.setdefault(hip,[]).append([baseline_pos[hip][k]+delta[k] for k in range(3)])
   # Bone-local weapon motion from source (independent left and right controls).
   for wb in ['Weapon.L','Weapon.R']:
    j=map_bone(wb,names)
    if j is None or wb not in f['bones'] or wb not in base['bones']:continue
    d=[f['bones'][wb]['localDeltaPosition'][k]-base['bones'][wb]['localDeltaPosition'][k] for k in range(3)]
    if max(abs(k) for k in d)>1:raise ValueError('WEAPON_TRANSLATION_EXCESSIVE '+name)
    origin=g['nodes'][j].get('translation',[0,0,0]);poss.setdefault(j,[]).append([origin[k]+d[k] for k in range(3)])
   # Fill weapon tracks for frames where no key is supplied, to keep lengths stable.
   for wb in ['Weapon.L','Weapon.R']:
    j=map_bone(wb,names)
    if j not in poss or len(poss[j])==len(poss[hip]):continue
    while len(poss[j])<len(poss[hip]):poss[j].append(list(g['nodes'][j].get('translation',[0,0,0])))
  cn=w.animation('Lionheart_'+name,times,rots,poss)
  evidence.append({'clip':'Lionheart_'+name,'duration':times[-1],'channels':cn,'sampleFrames':len(times),'status':'REVIEW_CANDIDATE_SOURCE_EVALUATED'})
 # Ares lower-body stepping and full-body AxeKick, using Ares Idle-Cross as donor baseline.
 aa=parse_samples(ares,(*STEP_LABELS,'AxeKick'))
 ab=ares['actions'].get('Idle-Cross',{}).get('frames')
 if not ab:raise ValueError('ARES_IDLE_CROSS_REQUIRED_FOR_RECONCILIATION')
 donor=ab[0]
 for name in (*STEP_LABELS,'AxeKick'):
  lower=name in STEP_LABELS;frames=aa[name]['frames'];times=[f['time']-frames[0]['time'] for f in frames];rots={};poss={}
  scale=float(ares.get('targetScale',1.0));
  if not .4<=scale<=2.5:raise ValueError('ARES_SCALE_OUT_OF_BOUNDS')
  for f in frames:
   mapped=rebase_source_pose(f,donor,g,rest_world,approved,frames,only_lower=lower)
   for j in approved:rots.setdefault(j,[]).append(mapped.get(j,approved[j]))
   # Preserve Lionheart's idle guard world-facing orientation during footwork.
   # Hip motion may yaw the pelvis, so counter-rotate the direct Spine child locally.
   if lower and 'mixamorig:Spine' in names and names['mixamorig:Spine'] in approved:
    sj=names['mixamorig:Spine'];hq=rots[hip][-1]
    rots[sj][-1]=qnorm(qmul(qmul(qinv(hq),approved[hip]),approved[sj]))
   hp0=donor['bones']['mixamorig:Hips']['worldPosition'];hp1=f['bones']['mixamorig:Hips']['worldPosition']
   delta=[(hp1[k]-hp0[k])*scale for k in range(3)]
   if max(abs(x) for x in delta)>2.5:raise ValueError('ARES_ROOT_DISPLACEMENT_EXCESSIVE '+name)
   poss.setdefault(hip,[]).append([baseline_pos[hip][k]+delta[k] for k in range(3)])
  cn=w.animation('Ares_'+name+('_Lower' if lower else '_Full'),times,rots,poss)
  evidence.append({'clip':'Ares_'+name,'duration':times[-1],'channels':cn,'sampleFrames':len(times),'status':'REVIEW_CANDIDATE_LOWER_ONLY' if lower else 'REVIEW_CANDIDATE_FULL_BODY'})
 new=glb_bytes(g,b)
 # Verify JSON changes never remove/rewrite original GLB geometry/skin or bin payload.
 g2,b2=glb_load_bytes(new)
 if bytes(b2[:len(original_binary)])!=original_binary:raise ValueError('ORIGINAL_BIN_MUTATED')
 if g2['skins']!=original_jointskin or g2['meshes']!=original_meshes or g2['nodes']!=original_nodes:raise ValueError('ORIGINAL_RIG_MUTATED')
 if g2['animations'][:len(original_anims)]!=original_anims:raise ValueError('EXISTING_CLIPS_MUTATED')
 if len(g2['animations'])!=len(original_anims)+1+len(ANIM_LABELS)+len(STEP_LABELS)+1:raise ValueError('ANIMATION_COUNT_MISMATCH')
 # No new GLB pathname: atomically replace exact canonical model in-place only when all checks pass.
 fd,tmp=tempfile.mkstemp(dir=str(Path(model).parent),prefix='.obsidianti-atomic-',suffix='.tmp')
 try:
  with os.fdopen(fd,'wb') as f:f.write(new);f.flush();os.fsync(f.fileno())
  os.replace(tmp,model)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 result={'schema':'obsidianti-full-animation-campaign-v1.1.0','status':'QUARANTINED_FULL_LIBRARY','oldSha256':SOURCE_MODEL_SHA,'newSha256':sha(model),'clipCount':len(g2['animations']),'appended':evidence,'groundDelta':ground_delta,'groundingVerdict':'USER_REVIEW_PENDING','originalClipsPreserved':[a['name'] for a in original_anims],'canonical':'assets/obsidianti/Obsidianti.glb','fullIdleProvenance':'authored secondary-motion layer atop unchanged approved source static pose','allSourceAnimationDataEvaluated':True,'garmentsExcluded':True}
 Path(report_path).parent.mkdir(parents=True,exist_ok=True);Path(report_path).write_text(json.dumps(result,indent=2)+'\n');return result

def glb_load_bytes(data):
 assert data[:4]==b'glTF';n,typ=struct.unpack_from('<I4s',data,12);g=json.loads(data[20:20+n]);pos=20+n;nb,tp=struct.unpack_from('<I4s',data,pos);return g,bytearray(data[pos+8:pos+8+nb])

def cli():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--lionheart',required=True);p.add_argument('--ares',required=True);p.add_argument('--report',required=True);p.add_argument('--ground-delta',type=float,default=-.012)
 a=p.parse_args();r=make_library(a.model,json.load(open(a.lionheart)),json.load(open(a.ares)),a.report,a.ground_delta);print(json.dumps(r,indent=2))
if __name__=='__main__':cli()
