#!/usr/bin/env python3
"""Exact-input, minimally invasive GLB repair for an accidental 90 degree
hip/root axis offset in HitHeadLeft. Uses audited v2.0.23 glTF tools.
No general-purpose rotations; accept only a measured, independently corroborated
root-chain axis error, or stop with the forensic receipt.
"""
from __future__ import annotations
import copy,hashlib,json,math,pathlib,struct,sys,bisect,importlib.util,os

V='MUDMAN_HITHEADLEFT_AXIS_v2.0.25'
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

def repair(src,dst,report,base_tools,expected=OLD):
 src,dst,report=map(pathlib.Path,(src,dst,report));require(src.is_file() and digest(src)==expected,'EXACT_CURATED_SOURCE_GLB_SHA_INVALID')
 require(not dst.exists() and not report.exists(),'OUTPUT_PATH_ALREADY_EXISTS')
 g=load_tools(base_tools);js,data=g.glb_load(src)
 names=[a.get('name') for a in js['animations']]
 require(len(names)==23 and len(set(names))==23 and set(names)==EXPECTED,'GODOT_23_CLIP_LIBRARY_CHANGED')
 clips={a['name']:a for a in js['animations']}
 target=clips['HitHeadLeft'];idle=clips['Idle-Cross'];opposite=clips['HitHeadRightBig']
 hips,head,chain=rig_chain(js)
 a0,a1=clip_range(g,(js,data),target)
 # Sample first exact animated time. Screenshot at approximately t=0.02.
 t0=a0
 reference_names=('Idle-Cross','HitHeadRightBig')
 u_idle=body_vector(g,js,data,idle,clip_range(g,(js,data),idle)[0],hips,head)
 u_right=body_vector(g,js,data,opposite,clip_range(g,(js,data),opposite)[0],hips,head)
 u_target=body_vector(g,js,data,target,t0,hips,head)
 reference_agreement=dot(u_idle,u_right)
 diag={'schema':V,'sourceSHA256':digest(src),'target':'HitHeadLeft','animatedNodeChain':[{'index':i,'name':js['nodes'][i].get('name','')} for i in chain],
       'references':list(reference_names),'initialUprightVector':list(u_target),'idleUprightVector':list(u_idle),
       'oppositeHitUprightVector':list(u_right),'referenceBodyDirectionDot':reference_agreement,
       'candidates':[],'chosen':None,'ownerVisualAcceptance':'PENDING','scope':'ONE_ANIMATION_ONE_ROOT_CHAIN_ROTATION_SAMPLER_ONLY'}
 def checkpoint():
  report.parent.mkdir(parents=True,exist_ok=True)
  report.write_text(json.dumps(diag,indent=2,sort_keys=True)+'\n')
 # Keep forensic findings on failure rather than silently guessing.
 try:
  require(reference_agreement>0.78,'CONTROL_CLIPS_DISAGREE_ON_UPRIGHT_DIRECTION')
  require(dot(u_target,u_idle)<0.80,'HITHEADLEFT_BODY_ORIENTATION_NOT_ANOMALOUS_ENOUGH_TO_CORRECT')
  for i in chain:
   n=js['nodes'][i].get('name','')
   ch=rot_channel(g,js,data,target,i)
   if ch is None:continue
   ri=rot_at(g,js,data,idle,i,clip_range(g,(js,data),idle)[0]);rr=rot_at(g,js,data,opposite,i,clip_range(g,(js,data),opposite)[0]);rt=rot_at(g,js,data,target,i,t0)
   agreement=degrees(ri,rr);badangle=degrees(rt,ri);q=mul(ri,inv(rt));axis=axis_of_quat(q)
   candidate={'nodeIndex':i,'node':n,'referenceRotationsAgreeDegrees':round(agreement,5),'offAxisDegrees':round(badangle,5),
              'correctionAxis':axis,'correctionQuaternion':list(q),'qualifies':False}
   diag['candidates'].append(candidate)
   if not (agreement<=28 and 65<=badangle<=115):continue
   testjs=copy.deepcopy(js)
   testdata,tdata=write_track(g,testjs,data,testjs['animations'][names.index('HitHeadLeft')],i,q)
   new_u=body_vector(g,testjs,testdata,testjs['animations'][names.index('HitHeadLeft')],t0,hips,head)
   pre=dot(u_target,u_idle);post=dot(new_u,u_idle)
   candidate.update({'bodyBeforeDot':round(pre,6),'bodyAfterDot':round(post,6),'bodyDirectionAfter':list(new_u)})
   if post<=0.82 or post-pre<0.25:continue
   # Compare physical posed skinned character, not just local quaternions.
   b_before=skinned_geo(g,js,data,target,t0)
   b_after=skinned_geo(g,testjs,testdata,testjs['animations'][names.index('HitHeadLeft')],t0)
   b_idle=skinned_geo(g,js,data,idle,clip_range(g,(js,data),idle)[0])
   ht_before=b_before['maxY']-b_before['minY'];ht_after=b_after['maxY']-b_after['minY'];ht_idle=b_idle['maxY']-b_idle['minY']
   candidate.update({'heightBefore':ht_before,'heightAfter':ht_after,'referenceIdleHeight':ht_idle})
   if not (ht_after>=ht_before*1.15 and ht_after>=ht_idle*0.64):continue
   # Require target pose to become physically upright and plausible without changing timing.
   candidate['qualifies']=True
  accepted=[x for x in diag['candidates'] if x['qualifies']]
  require(len(accepted)==1,'CANNOT_ISOLATE_UNIQUE_90_DEG_ROOT_CHANNEL_'+str(len(accepted)))
  chosen=accepted[0];node=chosen['nodeIndex']
  finaljs=copy.deepcopy(js)
  outdata,mutation=write_track(g,finaljs,data,finaljs['animations'][names.index('HitHeadLeft')],node,chosen['correctionQuaternion'])
  for old,new in zip(js['animations'],finaljs['animations']):
   if old['name']!='HitHeadLeft':require(old==new,'UNRELATED_ANIMATION_JSON_CHANGED_'+old['name'])
  require(outdata[:len(data)]==data,'ORIGINAL_GLB_BIN_BYTES_CHANGED')
  require(finaljs['nodes']==js['nodes'] and finaljs['meshes']==js['meshes'] and finaljs['materials']==js['materials']
          and finaljs['skins']==js['skins'] and finaljs.get('textures')==js.get('textures') and finaljs.get('images')==js.get('images'),
          'RIG_OR_TEXTURE_OR_GEOMETRY_MUTATED')
  pre_hashes={x['name']:g.clip_bytes(js,data,x) for x in js['animations']}
  dest_bytes=g.glb_save(finaljs,outdata,dst)
  checkjs,checkdata=g.glb_load(dst)
  require(len(checkjs['animations'])==23 and set(a['name'] for a in checkjs['animations'])==EXPECTED,'OUTPUT_CLIP_LIBRARY_INVALID')
  require(checkdata[:len(data)]==data,'GLB_SOURCE_BIN_DATA_CHANGED_AFTER_SAVE')
  for x in checkjs['animations']:
   if x['name']!='HitHeadLeft':require(g.clip_bytes(checkjs,checkdata,x)==pre_hashes[x['name']],'UNRELATED_SAMPLER_BYTES_CHANGED_'+x['name'])
  check_u=body_vector(g,checkjs,checkdata,checkjs['animations'][names.index('HitHeadLeft')],t0,hips,head)
  require(dot(check_u,u_idle)>0.82,'NEW_GLB_ROOT_FIX_NOT_OBSERVED')
  # Sample the whole reaction: corrective delta is constant and all non-root keyframes are retained.
  spans=[]
  for f in (0,0.25,0.5,0.75,1):
   t=a0+(a1-a0)*f
   raw=body_vector(g,js,data,target,t,hips,head)
   corrected=body_vector(g,checkjs,checkdata,checkjs['animations'][names.index('HitHeadLeft')],t,hips,head)
   spans.append({'time':t,'preRefDot':dot(raw,u_idle),'afterRefDot':dot(corrected,u_idle)})
  diag.update({'chosen':chosen,'mutatedTrack':mutation,'outputSHA256':digest(dst),'outputBytes':dest_bytes,
               'otherClipsByteEquivalent':22,'otherClipsUnchanged':True,'allModelGeometryAndTexturePreserved':True,
               'samplingAcrossFullReaction':spans,'status':'EXACT_ROOT_AXIS_REPAIR_CANDIDATE_UNAPPROVED'})
  checkpoint()
  return diag
 except BaseException as e:
  diag.update({'status':'BLOCKED_NO_GUESS','blocker':type(e).__name__+':'+str(e)})
  checkpoint()
  # No candidate should escape the diagnostic stage after failure.
  if dst.exists():dst.unlink()
  raise

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--dest',required=True);ap.add_argument('--report',required=True);ap.add_argument('--tools',required=True)
 a=ap.parse_args();print(json.dumps(repair(a.source,a.dest,a.report,a.tools),indent=2))
