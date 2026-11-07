#!/usr/bin/env python3
"""Exact-input, minimally invasive GLB repair for an accidental 90 degree
hip/root axis offset in HitHeadLeft. Uses audited v2.0.23 glTF tools.
No general-purpose rotations; accept only a measured, independently corroborated
root-chain axis error, or stop with the forensic receipt.
"""
from __future__ import annotations
import copy,hashlib,json,math,pathlib,struct,sys,bisect,importlib.util,os

V='MUDMAN_HITHEADLEFT_FRAME_v2.0.26'
OLD='19304bf8007670e36a38b354b5f8d2ea0c39982c97e2a247acdac1190fe2b7ef'
EXPECTED={'Cross-Enemy','Run','BackImpact','Death','HitHeadLeft','HitHeadRightBig','Idle-Cross','Jab-Enemy',
          'KnockedBack','ProneBack','ProneBackDamage','ProneBackStandUp','ProneFrontDamage','ProneFront','StandUp',
          'StepBack','StepBackLeft','StepBackRight','StepForward','StepForwardLeft','StepForwardRight','StepLeft','StepRight'}

def require(x,msg):
 if not x:raise RuntimeError(msg)
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as s:
  for b in iter(lambda:s.read(1048576),b''):h.update(b)
 return h.hexdigest()
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def load_tools(path):
 spec=importlib.util.spec_from_file_location('mudman_base_glb_readonly',path);require(spec is not None and spec.loader is not None,'HELPER_MODULE_UNAVAILABLE')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def normalize(q):
 d=math.sqrt(sum(float(x)*x for x in q));require(d>1e-7 and math.isfinite(d),'INVALID_ROTATION_QUATERNION')
 return tuple(float(x)/d for x in q)
def mul(a,b):
 x,y,z,w=normalize(a);u,v,t,s=normalize(b)
 return normalize((w*u+x*s+y*t-z*v,w*v-x*t+y*s+z*u,w*t+x*v-y*u+z*s,w*s-x*u-y*v-z*t))
def inv(q):
 x,y,z,w=normalize(q);return (-x,-y,-z,w)
def degrees(a,b):
 aa,bb=normalize(a),normalize(b)
 c=min(1.,abs(sum(x*y for x,y in zip(aa,bb))))
 return 2*math.degrees(math.acos(c))
def vec3(v):return tuple(float(x) for x in v)
def norm3(v):
 d=math.sqrt(sum(x*x for x in v))
 return tuple(x/d for x in v) if d>1e-7 else (0.,0.,0.)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def pos(m):return (m[12],m[13],m[14])
def sub(a,b):return tuple(x-y for x,y in zip(a,b))

def clip_range(g,data,clip):
 ts=[]
 for s in clip['samplers']:
  rows=g.accessor(data[0],data[1],s['input']);require(rows,'EMPTY_CLIP_TIME')
  ts.append((rows[0][0],rows[-1][0]))
 return min(a for a,b in ts),max(b for a,b in ts)

def rot_channel(g,js,data,clip,node):
 rows=[x for x in clip['channels'] if x['target'].get('node')==node and x['target'].get('path')=='rotation']
 require(len(rows)<2,'DUPLICATE_ROTATION_NODE_CHANNEL_'+str(node))
 return rows[0] if rows else None

def rot_at(g,js,data,clip,node,t):
 channel=rot_channel(g,js,data,clip,node)
 if channel is None:return normalize(js['nodes'][node].get('rotation',(0.,0.,0.,1.)))
 sm=clip['samplers'][channel['sampler']]
 times=[x[0] for x in g.accessor(js,data,sm['input'])]
 values=g.accessor(js,data,sm['output'])
 require(times and len(times)==len(values),'ROTATION_TRACK_TIME_VALUE_MISMATCH')
 if len(times)==1 or t<=times[0]:return normalize(values[0])
 if t>=times[-1]:return normalize(values[-1])
 i=max(0,min(len(times)-2,bisect.bisect_right(times,t)-1))
 if sm.get('interpolation','LINEAR')=='STEP':return normalize(values[i])
 require(sm.get('interpolation','LINEAR')=='LINEAR','NONLINEAR_ROTATION_TRACK_UNSUPPORTED')
 f=(t-times[i])/(times[i+1]-times[i])
 return normalize(g.slerp(values[i],values[i+1],f))

def rig_chain(js):
 children={}
 for i,n in enumerate(js['nodes']):
  for ch in n.get('children',[]):
   require(ch not in children,'MULTIPLE_PARENTS_IN_RIG')
   children[ch]=i
 hips=[i for i,n in enumerate(js['nodes']) if n.get('name','').lower() in ('mixamorig:hips','mixamorig_hips')]
 heads=[i for i,n in enumerate(js['nodes']) if n.get('name','').lower() in ('mixamorig:head','mixamorig_head')]
 require(len(hips)==1 and len(heads)==1,'EXPECTED_SINGLE_MIXAMO_HIPS_AND_HEAD')
 c=[];node=hips[0]
 while True:
  c.append(node)
  if node not in children:break
  node=children[node]
 return hips[0],heads[0],c

def axis_of_quat(q):
 x,y,z,w=normalize(q)
 if w<0:x,y,z,w=-x,-y,-z,-w
 d=math.sqrt(max(0.,1-w*w))
 return tuple(round(v/d,5) for v in (x,y,z)) if d>1e-5 else (0.,0.,0.)

def skinned_geo(g,js,data,clip,t):
 result=g.sampled_skinned_bounds(js,data,clip,t)
 require(result['witnessVertices']>=200,'SKINNED_GEOMETRY_EVIDENCE_TOO_WEAK')
 return result

def body_vector(g,js,data,clip,t,hip,head):
 world=g.pose(js,data,clip,t)
 return norm3(sub(pos(world[head]),pos(world[hip])))

def write_track(g,js,data,clip,node,correction):
 ch=rot_channel(g,js,data,clip,node)
 require(ch is not None,'CORRECTED_NODE_HAS_NO_ANIMATED_ROTATION')
 sm=clip['samplers'][ch['sampler']]
 old_accessor=sm['output']
 a=js['accessors'][old_accessor]
 require(a['type']=='VEC4' and a['componentType']==5126 and 'sparse' not in a,'UNSUPPORTED_ROOT_ROTATION_FORMAT')
 values=g.accessor(js,data,old_accessor)
 require(len(values)>=2,'ROTATION_NEEDS_MORE_THAN_ONE_KEY')
 newvalues=[mul(correction,v) for v in values]
 # Preserve the original keyframe times and original untouched animation bytes.
 pad=(-len(data))%4;offset=len(data)+pad
 payload=b''.join(struct.pack('<4f',*v) for v in newvalues)
 next_data=data+b'\0'*pad+payload
 require(offset%4==0 and len(payload)==len(values)*16,'INVALID_PACKED_QUATERNION')
 bv=len(js['bufferViews']);js['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(payload)})
 access=len(js['accessors']);js['accessors'].append({'bufferView':bv,'byteOffset':0,'componentType':5126,'count':len(newvalues),'type':'VEC4'})
 sm['output']=access
 return next_data, {'oldAccessor':old_accessor,'newAccessor':access,'newBufferView':bv,'newKeyCount':len(newvalues),
  'firstBefore':list(values[0]),'firstAfter':list(newvalues[0]),'lastBefore':list(values[-1]),'lastAfter':list(newvalues[-1]),
  'newSamplerBytesSHA256':sha_bytes(payload)}

def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def length(v):return math.sqrt(dot(v,v))
def rotate_vec(q,v):
 x,y,z,w=normalize(q)
 v0=(x,y,z)
 a=cross(v0,v)
 b=cross(v0,a)
 return tuple(v[i]+2*(w*a[i]+b[i]) for i in range(3))
def from_to(a,b):
 a=norm3(a);b=norm3(b);d=max(-1.,min(1.,dot(a,b)))
 if d>0.999999:return (0.,0.,0.,1.)
 if d<-0.999999:
  axis=cross(a,(1.,0.,0.))
  if length(axis)<1e-5:axis=cross(a,(0.,1.,0.))
  return (*norm3(axis),0.)
 c=cross(a,b)
 return normalize((c[0],c[1],c[2],1.+d))
def axis_angle(axis,rad):
 a=norm3(axis);sn=math.sin(rad/2)
 return normalize((a[0]*sn,a[1]*sn,a[2]*sn,math.cos(rad/2)))
def projection(v,n):
 return sub(v,tuple(dot(v,n)*a for a in n))
def full_frame(js,world,hip,head):
 u=norm3(sub(pos(world[head]),pos(world[hip])))
 ls=next((i for i,node in enumerate(js['nodes']) if node.get('name','').lower() in ('mixamorig:leftshoulder','mixamorig_leftshoulder')),None)
 rs=next((i for i,node in enumerate(js['nodes']) if node.get('name','').lower() in ('mixamorig:rightshoulder','mixamorig_rightshoulder')),None)
 right=norm3(sub(pos(world[rs]),pos(world[ls]))) if ls is not None and rs is not None else None
 right=norm3(projection(right,u)) if right is not None else None
 if right is not None and length(right)<1e-4:right=None
 return {'up':u,'right':right}
def align_frame(target,reference,use_shoulder):
 q=from_to(target['up'],reference['up'])
 if use_shoulder and target['right'] is not None and reference['right'] is not None:
  a=norm3(projection(rotate_vec(q,target['right']),reference['up']))
  b=norm3(projection(reference['right'],reference['up']))
  if length(a)>.01 and length(b)>.01:
   theta=math.atan2(dot(reference['up'],cross(a,b)),dot(a,b))
   q=mul(axis_angle(reference['up'],theta),q)
 return q
def matrix_quat(world):
 # Extract the parent orientation from glTF column-major transform (positive scales).
 x=norm3((world[0],world[1],world[2]));y=norm3((world[4],world[5],world[6]));z=norm3(cross(x,y))
 y=norm3(cross(z,x));require(dot(cross(x,y),z)>.95,'NEGATIVE_OR_SHEARED_PARENT_ROTATION')
 m00,m01,m02=x[0],y[0],z[0];m10,m11,m12=x[1],y[1],z[1];m20,m21,m22=x[2],y[2],z[2]
 trace=m00+m11+m22
 if trace>0:
  s=math.sqrt(trace+1.)*2;w=.25*s;xq=(m21-m12)/s;yq=(m02-m20)/s;zq=(m10-m01)/s
 elif m00>m11 and m00>m22:
  s=math.sqrt(1.+m00-m11-m22)*2;w=(m21-m12)/s;xq=.25*s;yq=(m01+m10)/s;zq=(m02+m20)/s
 elif m11>m22:
  s=math.sqrt(1.+m11-m00-m22)*2;w=(m02-m20)/s;xq=(m01+m10)/s;yq=.25*s;zq=(m12+m21)/s
 else:
  s=math.sqrt(1.+m22-m00-m11)*2;w=(m10-m01)/s;xq=(m02+m20)/s;yq=(m12+m21)/s;zq=.25*s
 return normalize((xq,yq,zq,w))
def evaluate(g,js,data,target,reference,other,hip,head,times,node,delta):
 trial=copy.deepcopy(js)
 modified,info=write_track(g,trial,data,trial['animations'][[a['name'] for a in trial['animations']].index('HitHeadLeft')],node,delta)
 newclip=next(a for a in trial['animations'] if a['name']=='HitHeadLeft')
 vectors=[]
 for t in times:
  ref=body_vector(g,js,data,reference,clip_range(g,(js,data),reference)[0],hip,head)
  before=body_vector(g,js,data,target,t,hip,head)
  after=body_vector(g,trial,modified,newclip,t,hip,head)
  vectors.append({'t':round(t,6),'before':round(dot(before,ref),6),'after':round(dot(after,ref),6)})
 pre=sum(x['before'] for x in vectors[:3])/min(3,len(vectors))
 post=sum(x['after'] for x in vectors[:3])/min(3,len(vectors))
 try:
  geo_before=skinned_geo(g,js,data,target,times[0]);geo_after=skinned_geo(g,trial,modified,newclip,times[0]);idle=skinned_geo(g,js,data,reference,clip_range(g,(js,data),reference)[0])
  old_h=geo_before['maxY']-geo_before['minY'];new_h=geo_after['maxY']-geo_after['minY'];idle_h=idle['maxY']-idle['minY']
 except RuntimeError:
  raise
 angle=degrees(delta,(0,0,0,1))
 # Test for genuinely tipped torso, and an alignment that restores upright
 # without forcing every hit reaction into the identical idle pose.
 first=vectors[0];improvement=post-pre
 qualifies=(first['before']<.81 and first['after']>.82 and first['after']-first['before']>.20
            and post>.66 and improvement>.16 and 45<=angle<=135
            and new_h>old_h*.97 and new_h>idle_h*.56
            and geo_after['minY']>-.35*idle_h)
 score=3*improvement+2*(first['after']-first['before'])+.25*post+.15*(new_h/idle_h)-.002*abs(angle-90)
 return {'qualifies':bool(qualifies),'score':round(score,6),'sampleDots':vectors,
         'angleDegrees':round(angle,5),'geometryBefore':geo_before,'geometryAfter':geo_after,
         'originalHeight':old_h,'correctedHeight':new_h,'idleHeight':idle_h,'mutation':info}

def repair(src,dst,report,base_tools,expected=OLD):
 src,dst,report=map(pathlib.Path,(src,dst,report));require(src.is_file() and digest(src)==expected,'EXACT_CURATED_SOURCE_GLB_SHA_INVALID')
 require(not dst.exists() and not report.exists(),'OUTPUT_PATH_ALREADY_EXISTS')
 g=load_tools(base_tools);js,data=g.glb_load(src)
 names=[a.get('name') for a in js['animations']]
 require(len(names)==23 and len(set(names))==23 and set(names)==EXPECTED,'GODOT_23_CLIP_LIBRARY_CHANGED')
 clips={a['name']:a for a in js['animations']}
 target=clips['HitHeadLeft'];idle=clips['Idle-Cross'];opposite=clips['HitHeadRightBig']
 hips,head,chain=rig_chain(js);a0,a1=clip_range(g,(js,data),target)
 t_idle=clip_range(g,(js,data),idle)[0];t_right=clip_range(g,(js,data),opposite)[0]
 w_bad=g.pose(js,data,target,a0);w_idle=g.pose(js,data,idle,t_idle);w_right=g.pose(js,data,opposite,t_right)
 badframe=full_frame(js,w_bad,hips,head);idleframe=full_frame(js,w_idle,hips,head);rightframe=full_frame(js,w_right,hips,head)
 baseline=dot(badframe['up'],idleframe['up']);ref_agree=dot(idleframe['up'],rightframe['up'])
 parents={c:i for i,n in enumerate(js['nodes']) for c in n.get('children',[])}
 times=[a0+(a1-a0)*frac for frac in (0,.07,.18,.32,.50,.75,1.)]
 diag={'schema':V,'sourceSHA256':digest(src),'target':'HitHeadLeft','parentChain':
       [{'index':i,'name':js['nodes'][i].get('name','')} for i in chain],
       'sourceOriginalSummary':{'firstTime':a0,'lastTime':a1,'bodyDotIdle':baseline,'referenceDot':ref_agree,
          'badFrame':badframe,'idleFrame':idleframe,'oppositeFrame':rightframe},
       'candidates':[],'chosen':None,'scope':'ONE_TARGET_CLIP_ROTATION_TRACK_ONLY','ownerVisualAcceptance':'PENDING'}
 def save():
  report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(diag,indent=2,sort_keys=True)+'\n')
 try:
  require(ref_agree>.72,'REFERENCE_CLIPS_NOT_UPRIGHT_ALIGNED')
  require(baseline<.81,'HITHEADLEFT_NOT_GEOMETRICALLY_TIPPED_AT_START')
  q_up=align_frame(badframe,idleframe,False)
  q_frame=align_frame(badframe,idleframe,True)
  # Local-reference deltas and parent-coordinate world-frame alignment differ.
  # Evaluate each physically; no assumptions about the local key being 90 degrees.
  for i in chain:
   if not rot_channel(g,js,data,target,i):continue
   n=js['nodes'][i].get('name','');ri=rot_at(g,js,data,idle,i,t_idle);rt=rot_at(g,js,data,target,i,a0)
   q_ref=mul(ri,inv(rt))
   parent=parents.get(i)
   qp=matrix_quat(w_bad[parent]) if parent is not None else (0.,0.,0.,1.)
   proposals=[('LOCAL_REFERENCE_DELTA',q_ref),('WORLD_BODY_UP',mul(mul(inv(qp),q_up),qp)),
              ('WORLD_TORSO_FRAME',mul(mul(inv(qp),q_frame),qp))]
   for method,correction in proposals:
    c={'node':n,'nodeIndex':i,'method':method,'deltaQuaternion':list(correction),
       'axis':axis_of_quat(correction),'sourceLocalAngleToIdle':degrees(rt,ri),'qualifies':False}
    try:
     result=evaluate(g,js,data,target,idle,opposite,hips,head,times,i,correction)
     c.update(result)
    except Exception as exc:c['candidateError']=type(exc).__name__+':'+str(exc)[:250]
    diag['candidates'].append(c)
  accepted=sorted([x for x in diag['candidates'] if x.get('qualifies')],key=lambda x:(-x['score'],x['node']!='mixamorig:Hips',x['method']!='WORLD_TORSO_FRAME'))
  diag['acceptedCount']=len(accepted)
  require(accepted,'NO_PHYSICALLY_SAFE_WORLD_FRAME_CORRECTION')
  # Multiple methods on the SAME parent node are normal. Prefer the highest
  # independently scored spatial correction; print all candidates for review.
  best=accepted[0]
  # If a materially different second result scores similarly, do not silently
  # choose an ambiguous fix. Instead retain full scored evidence for inspection.
  for other in accepted[1:]:
   if other['nodeIndex']!=best['nodeIndex'] and other['score']>best['score']-.20:
    # Ancestor and hip tracks can be visually equivalent; favour the hips when
    # the best physical score difference is minor.
    if best['node']!='mixamorig:Hips' and other['node']=='mixamorig:Hips':best=other
  chosen=best;diag['chosen']=chosen
  final=copy.deepcopy(js)
  outdata,mutation=write_track(g,final,data,final['animations'][names.index('HitHeadLeft')],chosen['nodeIndex'],chosen['deltaQuaternion'])
  for a,b in zip(js['animations'],final['animations']):
   if a['name']!='HitHeadLeft':require(a==b,'UNRELATED_ANIMATION_JSON_CHANGED_'+a['name'])
  require(outdata[:len(data)]==data,'ORIGINAL_BUFFER_CHANGED')
  for key in ('nodes','meshes','materials','skins','textures','images','scenes'):
   require(final.get(key)==js.get(key),'MODEL_STRUCTURE_OR_MATERIAL_CHANGED_'+key)
  baselines={x['name']:g.clip_bytes(js,data,x) for x in js['animations']}
  g.glb_save(final,outdata,dst)
  reread,binary=g.glb_load(dst)
  require(binary.startswith(data),'RESULT_SOURCE_BUFFER_PREFIX_CHANGED')
  for clip in reread['animations']:
   if clip['name']!='HitHeadLeft':require(g.clip_bytes(reread,binary,clip)==baselines[clip['name']],'NON_TARGET_CLIP_CHANGED_'+clip['name'])
  require(len(reread['animations'])==23 and {a['name'] for a in reread['animations']}==EXPECTED,'RESULT_ANIMATION_NAMES_CHANGED')
  first_before=diag['sourceOriginalSummary']['bodyDotIdle'];first_after=body_vector(g,reread,binary,reread['animations'][names.index('HitHeadLeft')],a0,hips,head)
  require(dot(first_after,idleframe['up'])>.82 and dot(first_after,idleframe['up'])>first_before+.20,'FINAL_VIEWER_MODEL_ROOT_NOT_CORRECTED')
  diag.update({'status':'WORLD_FRAME_REPAIR_CANDIDATE_UNAPPROVED','outputSHA256':digest(dst),'outputBytes':dst.stat().st_size,
               'otherClipsByteEquivalent':22,'otherClipsUnchanged':True,'allModelGeometryAndTexturePreserved':True,'mutatedTrack':mutation})
  save();return diag
 except BaseException as exc:
  diag.update({'status':'BLOCKED_NO_GUESS','blocker':type(exc).__name__+':'+str(exc)})
  save()
  if dst.exists():dst.unlink()
  raise

if __name__=="__main__":
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument("--source",required=True);ap.add_argument("--dest",required=True);ap.add_argument("--report",required=True);ap.add_argument("--tools",required=True)
 a=ap.parse_args();print(json.dumps(repair(a.source,a.dest,a.report,a.tools),indent=2))
