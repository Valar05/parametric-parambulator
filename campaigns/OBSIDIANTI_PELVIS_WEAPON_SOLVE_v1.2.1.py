#!/usr/bin/env python3
"""Source-locked per-clip Lionheart pelvis pitch and independent weapon-translation correction.

The original canonical GLB is never overwritten until every structural and numerical gate
passes. Original source animations, geometry, skin and all Ares tracks are preserved.

Uses evaluated skinned wedge sole witnesses and donor-world toe contact classifications.
The pelvis adjustment is a small model-space local-X pitch plus bounded vertical placement;
no leg IK, joint hierarchy, cloth, material or weapon rotation mutations.
"""
from __future__ import annotations
import argparse, bisect, copy, hashlib, json, math, os, pathlib, statistics, struct, sys, tempfile
from collections import defaultdict

VERSION='OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1'
EXPECTED_SOURCE_SHA='5fa8773736cf4fd28eae13e13368246642642a1802d76e47ed7e14faf70d04c0'
ANIM_NAMES=['Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp']
WEAPON_NAMES={'mixamorig:LeftWeapon.L','mixamorig:RightWeapon.R'}
GROUND_Y=0.0


def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def unit(q):
 m=math.sqrt(sum(v*v for v in q))
 return [v/m for v in q] if m>1e-12 else [0.,0.,0.,1.]

def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]

def inv(q):return [-q[0],-q[1],-q[2],q[3]]
def qx(t):return [math.sin(t/2),0.,0.,math.cos(t/2)]
def rotate(q,p):
 x,y,z,w=unit(q);vx,vy,vz=p
 tx=2*(y*vz-z*vy);ty=2*(z*vx-x*vz);tz=2*(x*vy-y*vx)
 return [vx+w*tx+y*tz-z*ty, vy+w*ty+z*tx-x*tz, vz+w*tz+x*ty-y*tx]

def slerp(a,b,t):
 a=unit(a);b=unit(b);dot=sum(x*y for x,y in zip(a,b))
 if dot<0:b=[-v for v in b];dot=-dot
 if dot>.9995:return unit([x+(y-x)*t for x,y in zip(a,b)])
 theta=math.acos(max(-1.,min(1.,dot)));ss=math.sin(theta)
 return unit([(x*math.sin((1-t)*theta)+y*math.sin(t*theta))/ss for x,y in zip(a,b)])

def mat_trs(t,q,s):
 x,y,z,w=unit(q);sx,sy,sz=s
 xx=x*x;yy=y*y;zz=z*z;xy=x*y;xz=x*z;yz=y*z;wx=w*x;wy=w*y;wz=w*z
 return [
  (1-2*(yy+zz))*sx,(2*(xy-wz))*sy,(2*(xz+wy))*sz,t[0],
  (2*(xy+wz))*sx,(1-2*(xx+zz))*sy,(2*(yz-wx))*sz,t[1],
  (2*(xz-wy))*sx,(2*(yz+wx))*sy,(1-2*(xx+yy))*sz,t[2],
  0.,0.,0.,1.]

def mm(a,b):
 return [sum(a[4*r+k]*b[4*k+c] for k in range(4)) for r in range(4) for c in range(4)]

def mp(m,p):
 x,y,z=p
 return [m[0]*x+m[1]*y+m[2]*z+m[3],m[4]*x+m[5]*y+m[6]*z+m[7],m[8]*x+m[9]*y+m[10]*z+m[11]]

def clamp(v,a,b):return min(b,max(a,v))
def quantile(values,frac):
 values=sorted(values);return values[min(len(values)-1,max(0,int((len(values)-1)*frac)))]

def load_glb(path):
 d=pathlib.Path(path).read_bytes()
 if len(d)<32 or d[:4]!=b'glTF' or struct.unpack_from('<II',d,4)!=(2,len(d)):
  raise RuntimeError('NOT_VALID_LENGTHED_GLB')
 jn,jtype=struct.unpack_from('<I4s',d,12)
 if jtype!=b'JSON':raise RuntimeError('MISSING_GLB_JSON')
 g=json.loads(d[20:20+jn]);p=20+jn
 bn,btype=struct.unpack_from('<I4s',d,p)
 if btype!=b'BIN\0' or p+8+bn>len(d):raise RuntimeError('MISSING_GLB_BIN')
 b=bytearray(d[p+8:p+8+bn]);
 if len(b)!=g['buffers'][0]['byteLength']:raise RuntimeError('GLB_BIN_LENGTH_WRONG')
 return g,b

def encode_glb(g,b):
 g['buffers'][0]['byteLength']=len(b)
 js=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode()
 js+=b' '*(-len(js)%4)
 binary=bytes(b);binary+=b'\0'*(-len(binary)%4)
 return struct.pack('<4sII',b'glTF',2,28+len(js)+len(binary))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(binary),b'BIN\0')+binary

class Access:
 def __init__(self,g,b):self.g,self.b=g,b;self.cache={}
 def get(self,i):
  if i in self.cache:return self.cache[i]
  a=self.g['accessors'][i];v=self.g['bufferViews'][a['bufferView']]
  if a.get('sparse'):raise RuntimeError('SPARSE_ACCESSOR_UNSUPPORTED')
  dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
  fmt={5126:'f',5123:'H',5121:'B',5125:'I'}[a['componentType']]
  size=struct.calcsize('<'+fmt*dim);stride=v.get('byteStride',size)
  start=v.get('byteOffset',0)+a.get('byteOffset',0)
  if start+(a['count']-1)*stride+size>len(self.b):raise RuntimeError('ACCESSOR_OUT_OF_BIN')
  data=[struct.unpack_from('<'+fmt*dim,self.b,start+k*stride) for k in range(a['count'])]
  self.cache[i]=data;return data

def channels(g,b,anim):
 ac=Access(g,b);result={}
 for ch in anim['channels']:
  target=ch['target'];k=(target['node'],target['path'])
  s=anim['samplers'][ch['sampler']]
  if k in result:raise RuntimeError('DUPLICATE_ANIM_TARGET '+str(k))
  if s.get('interpolation','LINEAR')!='LINEAR':raise RuntimeError('UNSUPPORTED_INTERPOLATION '+anim['name'])
  result[k]=(tuple(v[0] for v in ac.get(s['input'])),ac.get(s['output']))
 return result

def sampled(tvals,vals,time,rotation=False):
 if time<=tvals[0]:return list(vals[0])
 if time>=tvals[-1]:return list(vals[-1])
 i=bisect.bisect_right(tvals,time)-1
 dt=tvals[i+1]-tvals[i]
 if dt<=0:raise RuntimeError('BAD_TIME_SERIES')
 f=(time-tvals[i])/dt
 if rotation:return slerp(vals[i],vals[i+1],f)
 return [a+(b-a)*f for a,b in zip(vals[i],vals[i+1])]

def global_matrices(g,anim_tracks,time):
 nodes=g['nodes'];cache={};parents={c:i for i,node in enumerate(nodes) for c in node.get('children',[])}
 def world(i):
  if i not in cache:
   n=nodes[i];t=n.get('translation',[0,0,0]);q=n.get('rotation',[0,0,0,1]);s=n.get('scale',[1,1,1])
   if (i,'translation') in anim_tracks:tvals,vals=anim_tracks[i,'translation'];t=sampled(tvals,vals,time)
   if (i,'rotation') in anim_tracks:tvals,vals=anim_tracks[i,'rotation'];q=sampled(tvals,vals,time,True)
   if (i,'scale') in anim_tracks:tvals,vals=anim_tracks[i,'scale'];s=sampled(tvals,vals,time)
   m=mat_trs(t,q,s);cache[i]=mm(world(parents[i]),m) if i in parents else m
  return cache[i]
 for i in range(len(nodes)):world(i)
 return cache

def foot_witnesses(g,b):
 ac=Access(g,b)
 sk=g['skins'][0];prim=g['meshes'][0]['primitives'][0];att=prim['attributes']
 for k in ('POSITION','JOINTS_0','WEIGHTS_0'):
  if k not in att:raise RuntimeError('FOOT_MESH_ATTRIBUTE_MISSING '+k)
 pos=ac.get(att['POSITION']);joints=ac.get(att['JOINTS_0']);weights=ac.get(att['WEIGHTS_0'])
 sk_names=[g['nodes'][i].get('name','') for i in sk['joints']]
 out={}
 for side in ('Left','Right'):
  valid={i for i,name in enumerate(sk_names) if name in {'mixamorig:'+side+'Foot','mixamorig:'+side+'ToeBase','mixamorig:'+side+'Toe_End'}}
  if len(valid)<2:raise RuntimeError('FOOT_SKIN_JOINTS_MISSING '+side)
  candidates=[]
  for p,js,ws in zip(pos,joints,weights):
   influence=sum(w for j,w in zip(js,ws) if j in valid)
   if influence>.24 and p[1]<.245:
    candidates.append((p,js,ws))
  if len(candidates)<70:raise RuntimeError('INSUFFICIENT_SKINNED_FOOT_VERTICES '+side)
  floor=min(x[0][1] for x in candidates)
  sole=[c for c in candidates if c[0][1]<floor+.035]
  if len(sole)<16:raise RuntimeError('INSUFFICIENT_PHYSICAL_SOLE_VERTICES '+side)
  # Deterministically retain the full shoe contact patch, with bounded work.
  sole.sort(key=lambda x:(round(x[0][2],4),round(x[0][0],4),x[0][1]))
  if len(sole)>96:sole=sole[::math.ceil(len(sole)/96)]
  out[side]=sole
 ibs=ac.get(sk['inverseBindMatrices'])
 # glTF MAT4 column major -> row major
 ibm=[[m[c*4+r] for r in range(4) for c in range(4)] for m in ibs]
 return out,sk,ibm

def skin_foot_points(witnesses,skin,ibm,world):
 result={}
 required={j for side in witnesses for _,js,ws in witnesses[side] for j,w in zip(js,ws) if w>0}
 mats={j:mm(world[skin['joints'][j]],ibm[j]) for j in required}
 for side,verts in witnesses.items():
  pts=[]
  for p,js,ws in verts:
   v=[0.,0.,0.]
   for j,w in zip(js,ws):
    if w<=0:continue
    pt=mp(mats[j],p)
    v[0]+=pt[0]*w;v[1]+=pt[1]*w;v[2]+=pt[2]*w
   pts.append(v)
  result[side]=pts
 return result

def floor_height(pts):return quantile([p[1] for p in pts],.065)

def sample_source_frames(donor,clip):
 rows=donor['actions'][clip]['frames']
 if not rows or len(rows)<2:raise RuntimeError('SOURCE_ACTION_EMPTY '+clip)
 return rows

def source_contacts(donor):
 actions=donor['actions'];baseline=actions['Idle']['frames'][0]['bones']
 if not all(('mixamorig:'+s+'ToeBase') in baseline for s in ('Left','Right')):
  raise RuntimeError('DONOR_BASE_TOE_BONES_MISSING')
 floor=min(baseline['mixamorig:'+s+'ToeBase']['worldPosition'][1] for s in ('Left','Right'))
 if abs(floor)>.35:raise RuntimeError('SOURCE_GROUND_UNEXPECTED '+str(floor))
 return floor

def build_measurements(g,b,donor):
 names={n.get('name'):i for i,n in enumerate(g['nodes'])}
 hip=names['mixamorig:Hips']
 if g['nodes'][hip].get('scale',[1,1,1])[0]<.9:raise RuntimeError('HIP_SCALE_NOT_SUPPORTED')
 rootparent=next((i for i,n in enumerate(g['nodes']) if hip in n.get('children',[])),None)
 if rootparent is None:raise RuntimeError('HIP_PARENT_MISSING')
 parent=g['nodes'][rootparent]
 if any(abs(x)>1e-5 for x in parent.get('translation',[0,0,0])) or any(abs(x-y)>1e-5 for x,y in zip(parent.get('rotation',[0,0,0,1]),[0,0,0,1])):
  raise RuntimeError('HIP_PARENT_NONIDENTITY_NEEDS_EXPLICIT_BASIS')
 ac=Access(g,b);wit,skin,ibm=foot_witnesses(g,b)
 source_floor=source_contacts(donor);result={}
 for aname in ANIM_NAMES:
  clip='Lionheart_'+aname
  anim=next((a for a in g['animations'] if a['name']==clip),None)
  if not anim:raise RuntimeError('REQUIRED_CLIP_NOT_FOUND '+clip)
  tr=channels(g,b,anim)
  if (hip,'rotation') not in tr or (hip,'translation') not in tr:raise RuntimeError('HIP_CHANNEL_MISSING '+clip)
  rows=sample_source_frames(donor,aname)
  measures=[]
  # Source time samples match the explicitly evaluated original Blender sequence.
  for row in rows:
   t=float(row['time']);bones=row['bones'];contacts=[]
   for side in ('Left','Right'):
    bn='mixamorig:'+side+'ToeBase'
    if bn not in bones:raise RuntimeError('TOE_BONE_MISSING_IN_SOURCE '+clip+':'+bn)
    h=bones[bn]['worldPosition'][1]-source_floor
    if -.055<=h<=.068:contacts.append(side)
   if not contacts:continue  # airborne or deliberate lifted phase
   world=global_matrices(g,tr,t)
   shoes=skin_foot_points(wit,skin,ibm,world)
   hp=mp(world[hip],[0,0,0]);tvals,qvals=tr[(hip,'rotation')];q=sampled(tvals,qvals,t,True)
   measures.append({'time':t,'supports':contacts,'shoe':shoes,'pivot':hp,'hipQuat':q,'sourceToe':{side:bones['mixamorig:'+side+'ToeBase']['worldPosition'][1]-source_floor for side in ('Left','Right')}})
  result[aname]={'frames':measures,'sourceFrameCount':len(rows),'contacts':sum(len(m['supports']) for m in measures),'originalFrames':rows[-1]['time']}
 return result,names

def ease(w):return w*w*(3-2*w)

def envelope(t,duration,start_close,end_close):
 # Retain the accepted Idle pose at transitions if the authored movement starts/ends there.
 start=min(1.,t/.14) if start_close else 1.
 end=min(1.,(duration-t)/.14) if end_close else 1.
 return ease(clamp(min(start,end),0.,1.))

def root_rotation_closeness(animtracks,hip,initial_or_final,approved):
 tvals,qvals=animtracks[hip,'rotation'];q=unit(qvals[0 if initial_or_final=='start' else -1])
 dot=min(1.,abs(sum(a*b for a,b in zip(q,approved))))
 return math.degrees(2*math.acos(dot))

def prepare_measures(measures,start_close,end_close):
 # For rotation around local hip X, one scan of each physical sole vertex gives
 # exact Rodrigues coefficients. We can evaluate thousands of pitch candidates
 # without repeatedly skinning or rotating every 3D point.
 duration=measures['originalFrames']
 result=[]
 for m in measures['frames']:
  axis=rotate(m['hipQuat'],[1,0,0]);pivot=m['pivot']
  left_right={}
  for side,pts in m['shoe'].items():
   coeff=[]
   for p in pts:
    r=[p[k]-pivot[k] for k in range(3)]
    dot=sum(axis[k]*r[k] for k in range(3))
    a=r[1]-axis[1]*dot
    bv=axis[2]*r[0]-axis[0]*r[2]
    coeff.append((p[1],a,bv))
   left_right[side]=coeff
  result.append({'supports':m['supports'],'time':m['time'],
   'weight':envelope(m['time'],duration,start_close,end_close),'coeff':left_right})
 return result

def raw_heights(prepared,angle):
 results=[]
 for m in prepared:
  theta=math.radians(angle*m['weight']);dc=math.cos(theta)-1.;ds=math.sin(theta)
  for side in m['supports']:
   vals=[y+dc*a+ds*bb for y,a,bb in m['coeff'][side]]
   results.append((quantile(vals,.065),m['weight']))
 return results

def metric_from_heights(heights,angle,drop):
 errors=[h+drop*w for h,w in heights]
 if len(errors)<3:return {'score':1e9,'rms':1e9,'maxPenetration':1e9,'maxHover':1e9,'count':len(errors)}
 rms=math.sqrt(sum(e*e for e in errors)/len(errors))
 penetration=max(0.,-min(errors));hover=max(0.,max(errors))
 score=sum((2.5 if e<-.015 else 1.)*e*e for e in errors)/len(errors)
 score+=.00002*(angle/15.)**2+.00002*(drop/.04)**2
 return {'score':score,'rms':rms,'maxPenetration':penetration,'maxHover':hover,'count':len(errors)}

def fit_pitch(measures,start_close,end_close):
 prepared=prepare_measures(measures,start_close,end_close)
 original=metric_from_heights(raw_heights(prepared,0.),0.,0.)
 best=None
 # Owner commissioned rotation ONLY. No pelvis translation correction is applied.
 def evaluate(angle):
  samples=raw_heights(prepared,angle)
  measures=metric_from_heights(samples,angle,0.)
  return {'angle':angle,'drop':0.,**measures}
 for angle in range(-25,26):
  a=evaluate(float(angle))
  if best is None or a['score']<best['score']:best=a
 coarse=best['angle']
 for j in range(-4,5):
  a=evaluate(coarse+j*.25)
  if a['score']<best['score']:best=a
 return original,best

def append_accessor(g,b,data,typ):
 dim={'VEC3':3,'VEC4':4}[typ];values=[float(v) for row in data for v in row]
 if not all(math.isfinite(v) for v in values):raise RuntimeError('NONFINITE_OUTPUT')
 while len(b)%4:b.append(0)
 off=len(b);b.extend(struct.pack('<'+'f'*len(values),*values));k=len(g['bufferViews'])
 g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(values)*4})
 idx=len(g['accessors']);g['accessors'].append({'bufferView':k,'componentType':5126,'count':len(data),'type':typ});return idx

def apply(g,b,donor,report,out):
 src_anims=copy.deepcopy(g['animations']);src_nodes=copy.deepcopy(g['nodes']);src_meshes=copy.deepcopy(g['meshes']);src_skins=copy.deepcopy(g['skins']);src_bin=bytes(b)
 if len(g['animations'])!=23 or g['scenes'][0]['nodes']!=[77]:raise RuntimeError('WRONG_CANONICAL_SOURCE_LAYOUT')
 measure,names=build_measurements(g,b,donor);hip=names['mixamorig:Hips']
 idle=next(a for a in g['animations'] if a['name']=='LionheartIdle_UNREVIEWED')
 idle_track=channels(g,b,idle);idle_q=idle_track[hip,'rotation'][1][0]
 rows=[];updates=0;removed=0
 for aname in ANIM_NAMES:
  clip='Lionheart_'+aname
  anim=next(a for a in g['animations'] if a['name']==clip)
  track=channels(g,b,anim);M=measure[aname];duration=track[hip,'rotation'][0][-1]
  start_close=root_rotation_closeness(track,hip,'start',idle_q)<4.0
  end_close=root_rotation_closeness(track,hip,'end',idle_q)<4.0
  original,fit=fit_pitch(M,start_close,end_close)
  # If no valid correction to supporting feet, keep this clip untouched.
  enough=fit['score'] < original['score']*.84
  materially_wrong=original['rms']>.018
  safer=fit['maxPenetration']<=max(original['maxPenetration']+.004,.02)
  apply_pitch=bool(materially_wrong and enough and safer and abs(fit['angle'])<=25 and len(M['frames'])>=3)
  if apply_pitch:
   qt,qv=track[hip,'rotation']
   nq=[]
   for t,q in zip(qt,qv):
    w=envelope(t,duration,start_close,end_close)
    nq.append(unit(mul(q,qx(math.radians(fit['angle']*w)))))
   for channel in anim['channels']:
    k=(channel['target']['node'],channel['target']['path'])
    if k==(hip,'rotation'):anim['samplers'][channel['sampler']]['output']=append_accessor(g,b,nq,'VEC4')
   updates+=1
  # User explicitly wants NONE of the Lionheart weapon-bone animated positional drift.
  old=len(anim['channels'])
  anim['channels']=[c for c in anim['channels'] if not (c['target']['path']=='translation' and g['nodes'][c['target']['node']].get('name') in WEAPON_NAMES)]
  removed+=old-len(anim['channels'])
  rows.append({'clip':clip,'contactSamples':original['count'],'sourceFrames':M['sourceFrameCount'],
   'sourceContactFrames':len(M['frames']),'rmsBefore_m':round(original['rms'],6),
   'rmsCandidate_m':round(fit['rms'],6),'penetrationBefore_m':round(original['maxPenetration'],6),
   'penetrationCandidate_m':round(fit['maxPenetration'],6),'pitchCandidate_deg':round(fit['angle'],3),
   'rootYCandidate_m':round(fit['drop'],6),'pitchApplied':apply_pitch,'beginFromIdle':start_close,
   'endAtIdle':end_close,'weaponTranslationChannelsRemoved':old-len(anim['channels'])})
 if removed<3:raise RuntimeError('NO_LIONHEART_WEAPON_TRANSLATION_TRACKS_FOUND')
 # Removing malformed weapon translations is independently authorized even if no
 # pelvis angle can be proven to improve every target contact.
 # glTF nonrotational data and all preexisting non-Lionheart clips preserved exactly.
 if g['nodes']!=src_nodes or g['skins']!=src_skins or g['meshes']!=src_meshes:raise RuntimeError('RIG_MESH_CHANGED')
 for before,after in zip(src_anims,g['animations']):
  if not before['name'].startswith('Lionheart_') or before['name']=='LionheartIdle_UNREVIEWED':
   if before!=after:raise RuntimeError('PROTECTED_ANIMATION_CHANGED '+before['name'])
  elif before['name'].startswith('Lionheart_'):
   allowed={'mixamorig:Hips','mixamorig:LeftWeapon.L','mixamorig:RightWeapon.R'}
   a0={(c['target']['node'],c['target']['path']):before['samplers'][c['sampler']]['output'] for c in before['channels']}
   a1={(c['target']['node'],c['target']['path']):after['samplers'][c['sampler']]['output'] for c in after['channels']}
   for k,v in a1.items():
    n=g['nodes'][k[0]].get('name','')
    if k not in a0:raise RuntimeError('ANIM_CHANNEL_ADDED '+before['name'])
    if v!=a0[k] and n not in allowed:raise RuntimeError('UNAUTHORIZED_CHANNEL_MUTATED '+before['name']+' '+n)
 outbytes=encode_glb(g,b)
 newg,newbin=load_glb_bytes(outbytes)
 if bytes(newbin[:len(src_bin)])!=src_bin:raise RuntimeError('ORIGINAL_GLB_BINARY_MUTATED')
 if len(newg['animations'])!=23:raise RuntimeError('CLIP_COUNT_CHANGED')
 # Main canonical path MUST be updated atomically, never a new model filename.
 p=pathlib.Path(out);fd,tmp=tempfile.mkstemp(prefix='.obsidianti-v1.2.1-',suffix='.tmp',dir=str(p.parent))
 try:
  with os.fdopen(fd,'wb') as f:f.write(outbytes);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 result={'campaign':VERSION,'status':'PHONE_VISUAL_REVIEW_REQUIRED','canonical':'assets/obsidianti/Obsidianti.glb',
  'beforeSha256':EXPECTED_SOURCE_SHA,'afterSha256':sha(p),'clipCount':len(newg['animations']),
  'pelvisPitchClipsApplied':updates,'weaponTranslationChannelsRemoved':removed,'perClip':rows,
  'unchangedAnimations':[a['name'] for a in newg['animations'] if not a['name'].startswith('Lionheart_') or a['name']=='LionheartIdle_UNREVIEWED'],
  'contract':'ONLY Lionheart moving action Hips pitch and weapon location channels; no Hips translation, Ares, or Idle edits',
  'visualApproved':False}
 pathlib.Path(report).parent.mkdir(parents=True,exist_ok=True)
 pathlib.Path(report).write_text(json.dumps(result,indent=2)+'\n')
 return result

def load_glb_bytes(data):
 n,typ=struct.unpack_from('<I4s',data,12);g=json.loads(data[20:20+n]);p=20+n;bn,btype=struct.unpack_from('<I4s',data,p);return g,bytearray(data[p+8:p+8+bn])

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--source',required=True);p.add_argument('--report',required=True);p.add_argument('--expect-sha',default=EXPECTED_SOURCE_SHA);args=p.parse_args()
 if args.expect_sha!=EXPECTED_SOURCE_SHA or sha(args.model)!=EXPECTED_SOURCE_SHA:raise RuntimeError('UNRECOGNIZED_CANONICAL_SOURCE')
 donor=json.loads(pathlib.Path(args.source).read_text())
 if donor.get('sourceKind')!='lionheart' or len(donor.get('actions',{}))<11:raise RuntimeError('SOURCE_NOT_VERIFIED_LIONHEART')
 g,b=load_glb(args.model)
 out=apply(g,b,donor,args.report,args.model)
 print(json.dumps(out,indent=2))

if __name__=='__main__':main()
